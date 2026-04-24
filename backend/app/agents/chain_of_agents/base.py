"""
Base Agent class for Chain of Agents architecture
"""

from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import time
from loguru import logger

from app.agents.chain_of_agents.state import AgentState


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the chain.
    Each agent must implement the process method.
    """
    
    def __init__(self, name: str, max_retries: int = 2):
        self.name = name
        self.max_retries = max_retries
        logger.info(f"Initialized agent: {name}")
    
    async def run(self, state: AgentState) -> AgentState:
        """
        Execute the agent with retry logic.
        This method should be called by the orchestrator.
        """
        state.add_trace(self.name, "Starting execution")
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt + 1}/{self.max_retries + 1}")
                state = await self.process(state)
                state.add_trace(self.name, f"Completed successfully (attempt {attempt + 1})")
                break
            except Exception as e:
                logger.error(f"[{self.name}] Error on attempt {attempt + 1}: {e}")
                state.add_trace(self.name, f"Error: {str(e)}")
                
                if attempt == self.max_retries:
                    logger.error(f"[{self.name}] All retries exhausted")
                    state = await self.handle_error(state, e)
                else:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        elapsed = (time.time() - start_time) * 1000
        state.processing_time_ms += elapsed
        logger.info(f"[{self.name}] Execution completed in {elapsed:.2f}ms")
        
        return state
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Main processing logic for the agent.
        Must be implemented by each agent.
        
        Args:
            state: Current AgentState
            
        Returns:
            Updated AgentState
        """
        pass
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """
        Handle errors after all retries exhausted.
        Can be overridden by specific agents.
        
        Args:
            state: Current AgentState
            error: The exception that occurred
            
        Returns:
            Updated AgentState with error information
        """
        logger.error(f"[{self.name}] Handling error: {error}")
        state.add_trace(self.name, f"Error handling: {str(error)}")
        return state
