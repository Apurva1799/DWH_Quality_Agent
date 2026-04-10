import json
import ssl
import asyncio
import aiohttp
from typing import Any, List, Optional, AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessageChunk, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.prompts import ChatPromptTemplate


class KalyaniLangChainLLM(BaseChatModel):
    """
    Custom LangChain-compatible async LLM wrapper
    for Kalyani gateway microservice.
    """

    base_url: str = "http://10.7.30.1:8000"
    model_name: str = "/raid/hf/models/nvidia__Llama-3_1-Nemotron-Ultra-253B-v1"
    ssl_context: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Disable SSL verification (change if needed)
        self.ssl_context = False

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:

        # Format messages for gateway
        # Handle both string messages and BaseMessage objects
        formatted_msgs = []
        for m in messages:
            if isinstance(m, str):
                # Plain string message - treat as user message
                formatted_msgs.append({
                    "role": "user",
                    "content": m,
                })
            else:
                # BaseMessage object
                formatted_msgs.append({
                    "role": "user" if m.type == "human" else "assistant",
                    "content": m.content,
                })

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                # STEP 1: Submit job
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={"model": self.model_name, "messages": formatted_msgs},
                ) as resp:
                    if resp.status != 202:
                        error_text = await resp.text()
                        error_msg = (
                            f"Error: Submit Failed (Status: {resp.status}). "
                            f"Response: {error_text[:200]}"
                        )
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=error_msg)
                        )
                        return

                    data = await resp.json()
                    stream_url = data.get("stream_url")

                # STEP 2: Poll + stream
                url = f"{self.base_url}{stream_url}"

                while True:
                    async with session.get(url) as s_resp:
                        if s_resp.status == 202:
                            await asyncio.sleep(0.3)
                            continue

                        async for raw in s_resp.content:
                            line = raw.decode("utf-8").strip()

                            if not line or not line.startswith("data:"):
                                continue

                            payload = line.removeprefix("data:").strip()

                            if payload == "[DONE]":
                                break

                            try:
                                token = json.loads(payload).get("content", "")
                                if token:
                                    yield ChatGenerationChunk(
                                        message=AIMessageChunk(content=token)
                                    )
                            except Exception:
                                continue
                        break

            except aiohttp.ClientConnectorSSLError as e:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=f"SSL Error: {str(e)}. Try using HTTP instead of HTTPS."
                    )
                )
                return

            except Exception as e:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=f"Connection Error: {str(e)}")
                )
                return

    @property
    def _llm_type(self) -> str:
        return "kalyani_gateway"

    async def _agenerate(self, messages, stop=None, **kwargs) -> ChatResult:
        full_content = ""
        async for chunk in self._astream(messages, stop=stop, **kwargs):
            full_content += chunk.message.content

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=full_content))]
        )

    def _generate(self, messages, stop=None, **kwargs):
        """Synchronous generate method that calls async _agenerate"""
        import asyncio
        result = asyncio.run(self._agenerate(messages, stop=stop, **kwargs))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=result.generations[0].message.content))])

    async def list_models(self):
        """List available models from gateway"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(f"{self.base_url}/v1/models") as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {
                        "error": f"Status {resp.status}: {await resp.text()}"
                    }
            except Exception as e:
                return {"error": str(e)}


# -------------------------
# Example Usage
# -------------------------

async def main():
    prompt = ChatPromptTemplate.from_template(
        "Analyze the following legal clause for risks: {clause}"
    )

    llm = KalyaniLangChainLLM()
    chain = prompt | llm

    async for chunk in chain.astream(
        {"clause": "The vendor shall not be liable for any indirect damages..."}
    ):
        print(chunk.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
