"""
Query Executor Agent
Executes SQL queries and handles results/errors
"""

import time
import pandas as pd
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState
from app.database import SQLExecutor


class QueryExecutorAgent(BaseAgent):
    """
    Executes SQL queries against the database.
    Returns results as pandas DataFrame.
    """
    
    def __init__(self):
        super().__init__("QueryExecutor", max_retries=1)
        self.executor = SQLExecutor()
    
    async def process(self, state: AgentState) -> AgentState:
        """Execute SQL query with timing"""
        sql = state.generated_sql
        
        if not sql or not state.sql_valid:
            state.execution_success = False
            state.execution_error = "No valid SQL to execute"
            state.add_trace(self.name, "No valid SQL, skipping execution")
            return state
        
        start_time = time.time()
        
        try:
            logger.info(f"[{self.name}] Executing: {sql[:100]}...")
            
            result = await self.executor.execute_query(sql)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            state.execution_time = execution_time
            
            if result.get('success'):
                data = result.get('data', [])
                columns = result.get('columns', [])
                
                if data:
                    df = pd.DataFrame(data, columns=columns)
                    state.query_results = df
                    state.row_count = len(df)
                    state.execution_success = True
                    state.execution_error = None
                    state.add_trace(self.name, f"Success: {len(df)} rows in {execution_time:.2f}s")
                    logger.info(f"[{self.name}] Success: {len(df)} rows in {execution_time:.2f}s")
                else:
                    # Empty result is still success
                    state.query_results = pd.DataFrame(columns=columns)
                    state.row_count = 0
                    state.execution_success = True
                    state.execution_error = None
                    state.add_trace(self.name, f"Success: 0 rows in {execution_time:.2f}s")
                    logger.info(f"[{self.name}] Success: 0 rows in {execution_time:.2f}s")
            else:
                state.execution_success = False
                state.execution_error = result.get('error', 'Unknown execution error')
                state.query_results = None
                state.row_count = 0
                state.add_trace(self.name, f"Error after {execution_time:.2f}s: {state.execution_error}")
                logger.error(f"[{self.name}] Error after {execution_time:.2f}s: {state.execution_error}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            state.execution_time = execution_time
            logger.error(f"[{self.name}] Exception after {execution_time:.2f}s: {e}")
            state.execution_success = False
            state.execution_error = str(e)
            state.query_results = None
            state.row_count = 0
            state.add_trace(self.name, f"Exception after {execution_time:.2f}s: {str(e)}")
        
        return state
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Handle execution errors"""
        state.execution_success = False
        state.execution_error = f"Execution failed: {str(error)}"
        state.query_results = None
        state.row_count = 0
        state.add_trace(self.name, f"Handled error: {str(error)}")
        return state
