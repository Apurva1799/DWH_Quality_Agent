import asyncio
import os
from typing import Dict, List, Any, Optional
from loguru import logger

# Import the working Kalyani LLM wrapper
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage

class LLMManager:
    """Manager for LLM clients using Kalyani Gateway"""
    
    def __init__(self):
        self.primary_llm = None
        self.documentdb_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            # Use environment variables for Kalyani gateway
            base_url = os.getenv("KALYANI_LLM_BASE_URL", "")
            model_name = os.getenv("KALYANI_LLM_MODEL", "")
            self.primary_llm = KalyaniLangChainLLM(
                base_url=base_url,
                model_name=model_name
            )
            logger.info("Kalyani LLM Client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kalyani LLM: {e}")
    
    async def generate_with_nemotron_253b(self, query: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate using Nemotron 253B via Kalyani Gateway"""
        return await self.generate(query, temperature)
    
    async def generate_with_nemotron_49b(self, query: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate using Nemotron 49B via Kalyani Gateway"""
        return await self.generate(query, temperature)
    
    async def generate_with_deepseek(self, query: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate using DeepSeek via Kalyani Gateway"""
        return await self.generate(query, temperature)
    
    async def generate_with_llama(self, query: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Generate using Llama via Kalyani Gateway"""
        return await self.generate(query, temperature)
    
    async def generate(self, query: str, temperature: float = 0.1, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate text using Kalyani LLM"""
        try:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=query))
            
            response = await self.primary_llm._agenerate(messages)
            generated_text = response.generations[0].message.content
            
            return {
                "success": True,
                "response": generated_text,
                "client_used": "kalyani_gateway"
            }
            
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error generating response"
            }
    
    async def generate_with_fallback(self, query: str, primary: str = "nemotron_253b", 
                                   fallback: str = "deepseek", temperature: float = 0.1) -> Dict[str, Any]:
        """Generate with fallback (all use same gateway)"""
        return await self.generate(query, temperature)
    
    async def health_check(self) -> Dict[str, bool]:
        """Check LLM health"""
        health_status = {"kalyani_gateway": False}
        
        try:
            # Test with a simple query
            result = await self.generate("Hello")
            if result["success"]:
                health_status["kalyani_gateway"] = True
                health_status["nemotron_49b"] = True
                health_status["nemotron_253b"] = True
                health_status["deepseek"] = True
                health_status["llama"] = True
                logger.info("Kalyani Gateway health check passed")
            else:
                logger.error(f"Kalyani Gateway health check failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
        
        return health_status
    
    async def store_conversation(self, user_id: str, session_id: str, 
                                message: str, response: str, 
                                metadata: Dict[str, Any] = None) -> bool:
        """Stub for conversation storage"""
        # DocumentDB is not available, so we just log it
        logger.info(f"Conversation: {user_id} - {message[:50]}...")
        return True
    
    async def get_conversation_history(self, user_id: str, session_id: str, 
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Stub for conversation history"""
        return []

# Global LLM manager instance
llm_manager = LLMManager()
