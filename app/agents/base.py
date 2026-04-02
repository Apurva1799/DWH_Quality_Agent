from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from loguru import logger
import time

class AgentRequest(BaseModel):
    """Base model for agent requests"""
    query: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Base model for agent responses"""
    success: bool
    response: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_name: str
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(agent=name)
    
    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process the request and return response"""
        pass
    
    async def validate_request(self, request: AgentRequest) -> bool:
        """Validate the request before processing"""
        if not request.query:
            return False
        return True
    
    async def log_execution(self, request: AgentRequest, response: AgentResponse):
        """Log execution details"""
        self.logger.info(
            f"Request processed: {request.query[:100]}... "
            f"Success: {response.success} "
            f"Time: {response.execution_time}s"
        )
    
    async def execute_with_timing(self, request: AgentRequest) -> AgentResponse:
        """Execute process with timing and logging"""
        start_time = time.time()
        
        try:
            # Validate request
            if not await self.validate_request(request):
                return AgentResponse(
                    success=False,
                    response="Invalid request",
                    error="Request validation failed",
                    agent_name=self.name,
                    execution_time=time.time() - start_time
                )
            
            # Process the request
            response = await self.process(request)
            response.execution_time = time.time() - start_time
            
            # Log execution
            await self.log_execution(request, response)
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Agent execution failed: {str(e)}")
            
            return AgentResponse(
                success=False,
                response="Agent execution failed",
                error=str(e),
                agent_name=self.name,
                execution_time=execution_time
            )
