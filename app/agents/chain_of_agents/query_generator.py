"""
Query Generator Agent
Generates optimized SQL based on selected tables and user query
"""

import re
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


class QueryGeneratorAgent(BaseAgent):
    """
    Generates MSSQL queries based on:
    - User's natural language query
    - Selected relevant tables
    - Table descriptions/columns
    """
    
    def __init__(self):
        super().__init__("QueryGenerator", max_retries=2)
        self.llm = KalyaniLangChainLLM()
    
    async def process(self, state: AgentState) -> AgentState:
        """Generate SQL query"""
        query = state.user_query
        selected_tables = state.selected_tables
        table_descriptions = state.table_descriptions
        
        # Build table info for prompt
        table_info = "\n\n".join([
            f"Table: {table}\n{table_descriptions.get(table, 'No description')[:300]}"
            for table in selected_tables[:5]  # Limit to top 5
        ])
        
        system_prompt = f"""You are an expert MSSQL T-SQL query generator.

User Query: {query}

Selected Tables:
{table_info}

Generate a valid MSSQL T-SQL query following these rules:

1. Use exact table names from the selected tables
2. Use proper T-SQL syntax
3. Always use explicit column names (avoid SELECT * when possible)
4. For date filtering:
   - "last month": DATEADD(month, -1, GETDATE())
   - "this month": DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
   - "last week": DATEADD(week, -1, GETDATE())
   - "this year": DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)
5. End with semicolon
6. NO markdown code blocks in output
7. NO explanations - ONLY the SQL query
8. If aggregating, include GROUP BY
9. Use TOP N for limiting results (e.g., TOP 10)
10. Use meaningful aliases for readability

Output ONLY the SQL query, nothing else:"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate SQL for: {query}")
            ]
            
            result = await self.llm._agenerate(messages)
            raw_sql = result.generations[0].message.content.strip()
            
            # Clean and extract SQL
            sql = self._clean_sql(raw_sql)
            
            # Validate SQL
            is_valid, error_msg = self._validate_sql(sql)
            
            state.generated_sql = sql
            state.sql_valid = is_valid
            state.sql_error = error_msg if not is_valid else None
            
            state.add_trace(self.name, f"Generated SQL (valid={is_valid})")
            logger.info(f"[{self.name}] Generated: {sql[:100]}...")
            
        except Exception as e:
            logger.error(f"[{self.name}] Generation error: {e}")
            state.generated_sql = ""
            state.sql_valid = False
            state.sql_error = str(e)
            state.add_trace(self.name, f"Error: {str(e)}")
        
        return state
    
    def _clean_sql(self, raw: str) -> str:
        """Clean SQL from LLM response"""
        # Remove code blocks
        sql = re.sub(r'```sql\s*', '', raw, flags=re.IGNORECASE)
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
    
    def _validate_sql(self, sql: str) -> tuple:
        """Basic SQL validation"""
        if not sql or sql == ';':
            return False, "Empty SQL generated"
        
        # Check for required keywords
        if not re.search(r'SELECT|WITH|INSERT|UPDATE|DELETE', sql, re.IGNORECASE):
            return False, "No SQL statement found"
        
        # Check for dangerous operations (optional - can be removed if needed)
        dangerous = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM', 'UPDATE.*SET.*=']
        for pattern in dangerous:
            if re.search(pattern, sql, re.IGNORECASE):
                return False, f"Potentially dangerous operation detected: {pattern}"
        
        # Check for balanced parentheses
        open_parens = sql.count('(')
        close_parens = sql.count(')')
        if open_parens != close_parens:
            return False, "Unbalanced parentheses"
        
        return True, None
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Generate a safe fallback query on error"""
        logger.error(f"[{self.name}] Handling error: {error}")
        
        # Build a safe fallback query
        if state.selected_tables:
            table = state.selected_tables[0]
            fallback_sql = f"SELECT TOP 10 * FROM {table};"
            state.generated_sql = fallback_sql
            state.sql_valid = True
            state.sql_error = None
            state.add_trace(self.name, f"Generated fallback query: {fallback_sql}")
        else:
            state.generated_sql = "SELECT 1;"
            state.sql_valid = True
            state.sql_error = None
            state.add_trace(self.name, "Generated minimal fallback query")
        
        return state
