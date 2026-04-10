"""
Database Health Check Agent
Checks database connectivity at the start of the chain
"""

from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState
from app.database import SQLExecutor


class DatabaseHealthAgent(BaseAgent):
    """
    Checks if the database is accessible before attempting SQL operations.
    Runs at the very beginning of the agent chain.
    """
    
    def __init__(self):
        super().__init__("DatabaseHealth", max_retries=1)
        self.executor = SQLExecutor()
        self._health_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 30  # Cache health status for 30 seconds
    
    async def process(self, state: AgentState) -> AgentState:
        """Check database health"""
        import time
        
        current_time = time.time()
        
        # Use cached result if available and fresh
        if self._health_cache is not None and (current_time - self._cache_timestamp) < self._cache_ttl:
            is_healthy = self._health_cache
            state.add_trace(self.name, f"Using cached health status: {is_healthy}")
        else:
            # Perform health check
            is_healthy = await self._check_health()
            self._health_cache = is_healthy
            self._cache_timestamp = current_time
            state.add_trace(self.name, f"Health check: {is_healthy}")
        
        # Store in state for other agents to use
        state.response_data['db_healthy'] = is_healthy
        
        if not is_healthy:
            logger.warning(f"[{self.name}] Database is unavailable - will skip SQL execution")
        else:
            logger.info(f"[{self.name}] Database is healthy")
        
        return state
    
    async def _check_health(self) -> bool:
        """Perform actual health check"""
        try:
            # Try a simple query
            result = await self.executor.execute_query("SELECT 1 AS health_check;")
            return result.get('success', False)
        except Exception as e:
            logger.error(f"[{self.name}] Health check failed: {e}")
            return False
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, mark DB as unhealthy"""
        state.response_data['db_healthy'] = False
        state.add_trace(self.name, f"Health check error: {str(error)}")
        return state
