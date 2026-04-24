"""
SQL Query Corrector Agent
Analyzes SQL errors and suggests corrections
"""

import re
import json
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


class SQLQueryCorrectorAgent(BaseAgent):
    """
    Analyzes SQL execution errors and attempts to correct the query.
    Handles:
    - Syntax errors
    - Missing table/column errors
    - Connection errors
    - Permission errors
    - Query optimization issues
    """
    
    def __init__(self):
        super().__init__("SQLQueryCorrector", max_retries=1)
        self.llm = KalyaniLangChainLLM()
        self.max_correction_attempts = 2
    
    async def process(self, state: AgentState) -> AgentState:
        """Analyze error and attempt correction"""
        error = state.execution_error
        sql = state.generated_sql
        
        if not error:
            state.add_trace(self.name, "No error to correct")
            return state
        
        # Don't attempt correction for connection errors (infrastructure issue)
        if self._is_connection_error(error):
            state.add_trace(self.name, "Connection error - no correction possible")
            logger.info(f"[{self.name}] Connection error, skipping correction")
            return state
        
        # Analyze error type
        error_type = self._classify_error(error)
        state.add_trace(self.name, f"Error type: {error_type}")
        
        # Get relevant schema for correction
        schema_info = self._get_relevant_schema(state)
        
        # Attempt correction
        for attempt in range(self.max_correction_attempts):
            try:
                corrected_sql = await self._attempt_correction(sql, error, error_type, schema_info, attempt)
                
                if corrected_sql and corrected_sql != sql:
                    state.generated_sql = corrected_sql
                    state.sql_valid = True  # Mark as potentially valid
                    state.add_trace(self.name, f"Attempt {attempt + 1}: Generated corrected SQL")
                    logger.info(f"[{self.name}] Correction attempt {attempt + 1} complete")
                    
                    # Clear previous error to allow re-execution
                    state.execution_error = None
                    state.execution_success = False
                    
                    return state
                else:
                    state.add_trace(self.name, f"Attempt {attempt + 1}: No changes made")
                    
            except Exception as e:
                logger.error(f"[{self.name}] Correction error: {e}")
                state.add_trace(self.name, f"Attempt {attempt + 1} failed: {str(e)}")
        
        # If we reach here, correction failed
        state.add_trace(self.name, "All correction attempts exhausted")
        return state
    
    def _is_connection_error(self, error: str) -> bool:
        """Check if error is a connection/infrastructure issue"""
        connection_patterns = [
            r'unable to connect',
            r'server is unavailable',
            r'does not exist',
            r'connection refused',
            r'timeout',
            r'network',
            r'20009',  # pymssql connection error code
            r'adaptive server',
            r'db server',
            r'sql server'
        ]
        error_lower = error.lower()
        return any(re.search(pattern, error_lower) for pattern in connection_patterns)
    
    def _classify_error(self, error: str) -> str:
        """Classify the SQL error type"""
        error_lower = error.lower()
        
        if 'syntax' in error_lower or 'incorrect' in error_lower:
            return 'SYNTAX_ERROR'
        elif 'invalid object' in error_lower or 'does not exist' in error_lower:
            return 'MISSING_OBJECT'
        elif 'column' in error_lower and ('not found' in error_lower or 'invalid' in error_lower):
            return 'MISSING_COLUMN'
        elif 'permission' in error_lower or 'denied' in error_lower:
            return 'PERMISSION'
        elif 'timeout' in error_lower:
            return 'TIMEOUT'
        elif 'data type' in error_lower or 'conversion' in error_lower:
            return 'DATA_TYPE'
        elif 'deadlock' in error_lower:
            return 'DEADLOCK'
        else:
            return 'UNKNOWN'
    
    def _get_relevant_schema(self, state: AgentState) -> str:
        """Get schema info for selected tables"""
        if not state.selected_tables:
            return "No tables selected"
        
        schema_parts = []
        for table in state.selected_tables[:5]:
            desc = state.table_descriptions.get(table, "")
            schema_parts.append(f"Table: {table}\n{desc[:400]}")
        
        return "\n\n".join(schema_parts)
    
    async def _attempt_correction(self, sql: str, error: str, error_type: str, 
                                  schema_info: str, attempt: int) -> str:
        """Use LLM to correct the SQL"""
        
        system_prompt = f"""You are a SQL expert. Fix the following SQL query that has an error.

Original SQL:
```sql
{sql}
```

Error Message:
{error}

Error Type: {error_type}

Available Schema:
{schema_info}

Instructions:
1. Analyze the error and identify the root cause
2. Fix the SQL query
3. Ensure proper T-SQL syntax
4. Use correct table and column names from the schema
5. Handle date filters correctly using DATEADD/DATEDIFF
6. Avoid SELECT * - use specific columns

This is correction attempt #{attempt + 1}.

Respond ONLY with a JSON object:
{{
    "corrected_sql": "the fixed SQL query",
    "changes_made": "description of what was fixed",
    "confidence": 0.0-1.0
}}"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Fix the SQL query.")
            ]
            
            result = await self.llm._agenerate(messages)
            raw_response = result.generations[0].message.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{{.*?\}}', raw_response, re.DOTALL)
            if json_match:
                correction = json.loads(json_match.group(0))
                corrected_sql = correction.get("corrected_sql", "")
                
                # Clean the SQL
                corrected_sql = self._clean_sql(corrected_sql)
                
                if corrected_sql and corrected_sql != sql:
                    confidence = correction.get("confidence", 0.5)
                    changes = correction.get("changes_made", "Unknown changes")
                    logger.info(f"[{self.name}] Correction: {changes} (confidence: {confidence})")
                    return corrected_sql
                else:
                    return ""
            else:
                logger.warning(f"[{self.name}] No JSON found in correction response")
                return ""
                
        except Exception as e:
            logger.error(f"[{self.name}] Correction attempt failed: {e}")
            return ""
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL from LLM response"""
        # Remove code blocks
        sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove thinking content
        sql = re.sub(r'<thinking>.*?</thinking>', '', sql, flags=re.DOTALL)
        
        # Find SQL starting with keywords
        sql_match = re.search(r'(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|EXEC).*?(;|$)', 
                              sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(0)
        
        # Clean up
        sql = sql.strip()
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On correction failure, keep original error"""
        state.add_trace(self.name, f"Corrector failed: {str(error)}")
        return state
