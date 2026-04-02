import asyncio
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from app.config import settings, get_llm_config

# Import existing LLM clients
from clients import SequentialLLMClient, LLM_3B_Client, DocumentDBClient

class LLMManager:
    """Manager for multiple LLM clients with your comprehensive configuration"""
    
    def __init__(self):
        self.nemotron_49b_client = None
        self.nemotron_253b_client = None
        self.deepseek_client = None
        self.llama_client = None
        self.documentdb_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all available LLM clients"""
        # Initialize Nemotron 49B
        try:
            nemotron_49b_config = get_llm_config("nemotron")
            self.nemotron_49b_client = SequentialLLMClient(
                base_url=nemotron_49b_config["base_url"],
                verify_ssl=nemotron_49b_config["verify_ssl"]
            )
            logger.info("Nemotron 49B Client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Nemotron 49B Client: {e}")
        
        # Initialize Nemotron 253B
        try:
            nemotron_253b_config = get_llm_config("nemotron_253b")
            self.nemotron_253b_client = SequentialLLMClient(
                base_url=nemotron_253b_config["base_url"],
                verify_ssl=nemotron_253b_config["verify_ssl"]
            )
            logger.info("Nemotron 253B Client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Nemotron 253B Client: {e}")
        
        # Initialize DeepSeek
        try:
            deepseek_config = get_llm_config("deepseek")
            self.deepseek_client = SequentialLLMClient(
                base_url=deepseek_config["base_url"],
                verify_ssl=deepseek_config["verify_ssl"]
            )
            logger.info("DeepSeek Client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek Client: {e}")
        
        # Initialize Llama (using DGX 3B client pattern)
        try:
            llama_config = get_llm_config("llama")
            self.llama_client = LLM_3B_Client(
                base_url=llama_config["base_url"],
                verify_ssl=llama_config["verify_ssl"]
            )
            logger.info("Llama Client initialized via DGX 3B")
        except Exception as e:
            logger.error(f"Failed to initialize Llama Client: {e}")
        
        # Initialize DocumentDB Client
        try:
            self.documentdb_client = DocumentDBClient(
                base_url=settings.documentdb_base_url,
                load_env=True,
                ssl_verify=settings.documentdb_ssl_verify
            )
            # Auto-login if credentials are available
            if settings.documentdb_username and settings.documentdb_password:
                self.documentdb_client.login(
                    settings.documentdb_username,
                    settings.documentdb_password
                )
            logger.info("DocumentDB Client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DocumentDB Client: {e}")
    
    async def generate_with_nemotron_49b(
        self, 
        query: str, 
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Nemotron 49B"""
        if not self.nemotron_49b_client:
            return {
                "success": False,
                "error": "Nemotron 49B Client not available",
                "client_used": "nemotron_49b"
            }
        
        try:
            # Run the synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.nemotron_49b_client.generate_text,
                settings.llm_nemotron_49b,
                query,
                42,  # seed
                temperature,
                20,  # top_k
                0.9,  # top_p
                "30m"  # keep_alive
            )
            
            return {
                "success": True,
                "response": response,
                "client_used": "nemotron_49b"
            }
            
        except Exception as e:
            logger.error(f"Nemotron 49B Client error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "client_used": "nemotron_49b"
            }
    
    async def generate_with_nemotron_253b(
        self, 
        query: str, 
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Nemotron 253B"""
        if not self.nemotron_253b_client:
            return {
                "success": False,
                "error": "Nemotron 253B Client not available",
                "client_used": "nemotron_253b"
            }
        
        try:
            # Run the synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.nemotron_253b_client.generate_text,
                settings.llm_nemotron_253b,
                query,
                42,  # seed
                temperature,
                20,  # top_k
                0.9,  # top_p
                "30m"  # keep_alive
            )
            
            return {
                "success": True,
                "response": response,
                "client_used": "nemotron_253b"
            }
            
        except Exception as e:
            logger.error(f"Nemotron 253B Client error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "client_used": "nemotron_253b"
            }
    
    async def generate_with_deepseek(
        self, 
        query: str, 
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using DeepSeek"""
        if not self.deepseek_client:
            return {
                "success": False,
                "error": "DeepSeek Client not available",
                "client_used": "deepseek"
            }
        
        try:
            # Run the synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.deepseek_client.generate_text,
                settings.llm_deepseek_r1_70b,
                query,
                42,  # seed
                temperature,
                20,  # top_k
                0.9,  # top_p
                "30m"  # keep_alive
            )
            
            return {
                "success": True,
                "response": response,
                "client_used": "deepseek"
            }
            
        except Exception as e:
            logger.error(f"DeepSeek Client error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "client_used": "deepseek"
            }
    
    async def generate_with_llama(
        self, 
        query: str, 
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using Llama via DGX 3B"""
        if not self.llama_client:
            return {
                "success": False,
                "error": "Llama Client not available",
                "client_used": "llama"
            }
        
        try:
            # Run the synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.llama_client.generate,
                query,
                settings.llm_llama_70b_instruct,
                False,  # stream
                50,  # rate
                None,  # group_id
                120.0,  # overall_retrieve_timeout_seconds
                0.5,  # poll_interval_seconds
                30.0   # api_retrieve_buffer_timeout
            )
            
            return {
                "success": True,
                "response": response,
                "client_used": "llama",
                "stream": False
            }
            
        except Exception as e:
            logger.error(f"Llama Client error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "client_used": "llama"
            }
    
    async def generate_with_fallback(
        self, 
        query: str, 
        primary: str = "nemotron_253b",
        fallback: str = "nemotron_49b",
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with fallback between clients"""
        
        # Try primary client first
        if primary == "nemotron_49b":
            result = await self.generate_with_nemotron_49b(query, temperature, **kwargs)
            if result["success"]:
                return result
        elif primary == "nemotron_253b":
            result = await self.generate_with_nemotron_253b(query, temperature, **kwargs)
            if result["success"]:
                return result
        elif primary == "deepseek":
            result = await self.generate_with_deepseek(query, temperature, **kwargs)
            if result["success"]:
                return result
        elif primary == "llama":
            result = await self.generate_with_llama(query, temperature, **kwargs)
            if result["success"]:
                return result
        
        # Try fallback client
        logger.warning(f"Primary client {primary} failed, trying fallback {fallback}")
        if fallback == "nemotron_49b":
            result = await self.generate_with_nemotron_49b(query, temperature, **kwargs)
            if result["success"]:
                result["fallback_used"] = True
                return result
        elif fallback == "nemotron_253b":
            result = await self.generate_with_nemotron_253b(query, temperature, **kwargs)
            if result["success"]:
                result["fallback_used"] = True
                return result
        elif fallback == "deepseek":
            result = await self.generate_with_deepseek(query, temperature, **kwargs)
            if result["success"]:
                result["fallback_used"] = True
                return result
        elif fallback == "llama":
            result = await self.generate_with_llama(query, temperature, **kwargs)
            if result["success"]:
                result["fallback_used"] = True
                return result
        
        return {
            "success": False,
            "error": f"All clients failed. Primary: {primary}, Fallback: {fallback}",
            "client_used": None
        }
    
    async def store_conversation(
        self, 
        user_id: str, 
        session_id: str, 
        message: str, 
        response: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store conversation in DocumentDB"""
        if not self.documentdb_client:
            logger.warning("DocumentDB Client not available for conversation storage")
            return False
        
        try:
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
                "response": response,
                "timestamp": asyncio.get_event_loop().time(),
                "metadata": metadata or {}
            }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.documentdb_client.create_document,
                settings.learning_documentdb_name,
                settings.learning_documentdb_collection,
                conversation_data
            )
            
            logger.info(f"Conversation stored for user {user_id}, session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {str(e)}")
            return False
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history from DocumentDB"""
        if not self.documentdb_client:
            logger.warning("DocumentDB Client not available for conversation history")
            return []
        
        try:
            query = {
                "user_id": user_id,
                "session_id": session_id
            }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.documentdb_client.find_documents,
                settings.learning_documentdb_name,
                settings.learning_documentdb_collection,
                query,
                "get_conversation_history"
            )
            
            return result[-limit:] if result else []
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all LLM clients"""
        health_status = {
            "nemotron_49b": False,
            "nemotron_253b": False,
            "deepseek": False,
            "llama": False,
            "documentdb": False
        }
        
        # Check Nemotron 49B
        if self.nemotron_49b_client:
            try:
                loop = asyncio.get_event_loop()
                ping_result = await loop.run_in_executor(
                    None, self.nemotron_49b_client.ping
                )
                health_status["nemotron_49b"] = ping_result
            except Exception as e:
                logger.error(f"Nemotron 49B health check failed: {e}")
        
        # Check Nemotron 253B
        if self.nemotron_253b_client:
            try:
                loop = asyncio.get_event_loop()
                ping_result = await loop.run_in_executor(
                    None, self.nemotron_253b_client.ping
                )
                health_status["nemotron_253b"] = ping_result
            except Exception as e:
                logger.error(f"Nemotron 253B health check failed: {e}")
        
        # Check DeepSeek
        if self.deepseek_client:
            try:
                loop = asyncio.get_event_loop()
                ping_result = await loop.run_in_executor(
                    None, self.deepseek_client.ping
                )
                health_status["deepseek"] = ping_result
            except Exception as e:
                logger.error(f"DeepSeek health check failed: {e}")
        
        # Check Llama
        if self.llama_client:
            try:
                loop = asyncio.get_event_loop()
                health_result = await loop.run_in_executor(
                    None, self.llama_client.health_check
                )
                health_status["llama"] = health_result
            except Exception as e:
                logger.error(f"Llama health check failed: {e}")
        
        # Check DocumentDB
        if self.documentdb_client:
            try:
                loop = asyncio.get_event_loop()
                # Simple check - try to list databases
                await loop.run_in_executor(
                    None, self.documentdb_client.list_databases
                )
                health_status["documentdb"] = True
            except Exception as e:
                logger.error(f"DocumentDB health check failed: {e}")
        
        return health_status

# Global LLM manager instance
llm_manager = LLMManager()
