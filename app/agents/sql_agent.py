from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.database import sql_executor
from app.llm_manager import llm_manager
from app.config import get_database_config
from loguru import logger
import json

class SQLAgent(BaseAgent):
    """SQL Agent supporting multiple databases and LLM models"""
    
    def __init__(self, db_type: str = "silver"):
        super().__init__(f"SQL Agent ({db_type})")
        self.db_type = db_type
        self.db_config = get_database_config(db_type)
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process natural language query with database context"""
        try:
            # Get conversation context
            context = request.context or {}
            conversation_history = context.get("conversation_history", [])
            
            # Get database schema for context
            schema_info = await self._get_relevant_schema(request.query)
            
            # Choose appropriate LLM based on query complexity and availability
            llm_choice = await self._choose_llm_model(request.query, schema_info)
            
            # Generate SQL query using chosen LLM
            sql_query = await self._generate_sql_query(
                request.query, 
                schema_info, 
                conversation_history,
                llm_choice
            )
            
            if not sql_query:
                return AgentResponse(
                    success=False,
                    response="Failed to generate SQL query",
                    error="SQL generation failed",
                    agent_name=self.name
                )
            
            # Execute SQL query with database-specific configuration
            result = await self._execute_sql_query(sql_query)
            
            if not result["success"]:
                return AgentResponse(
                    success=False,
                    response=f"SQL execution failed: {result['error']}",
                    error=result["error"],
                    agent_name=self.name,
                    data={
                        "sql_query": sql_query,
                        "database": self.db_type
                    }
                )
            
            # Format the response
            response_text = await self._format_results(result, request.query)
            
            return AgentResponse(
                success=True,
                response=response_text,
                agent_name=self.name,
                data={
                    "sql_query": sql_query,
                    "result": result,
                    "row_count": result["row_count"],
                    "database": self.db_type,
                    "llm_used": llm_choice
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced SQL Agent processing error: {str(e)}")
            return AgentResponse(
                success=False,
                response="Enhanced SQL Agent processing failed",
                error=str(e),
                agent_name=self.name
            )
    
    async def _choose_llm_model(self, query: str, schema_info: str) -> str:
        """Choose appropriate LLM model based on query complexity and availability"""
        try:
            # Simple queries can use smaller models, complex queries need larger models
            query_lower = query.lower()
            
            # Check for complex query indicators
            complexity_indicators = [
                "join", "union", "subquery", "case when", "window function",
                "partition by", "group by", "having", "aggregate", "sum", "count",
                "average", "max", "min", "recursive", "stored procedure"
            ]
            
            is_complex = any(indicator in query_lower for indicator in complexity_indicators)
            
            # Check LLM availability
            health_status = await llm_manager.health_check()
            
            # Decision matrix for LLM selection
            if is_complex:
                # Complex queries - prefer larger models
                if health_status.get("nemotron_253b", False):
                    logger.info("Using Nemotron 253B for complex query")
                    return "nemotron_253b"
                elif health_status.get("nemotron_49b", False):
                    logger.info("Using Nemotron 49B for complex query")
                    return "nemotron_49b"
                elif health_status.get("deepseek", False):
                    logger.info("Using DeepSeek for complex query")
                    return "deepseek"
                else:
                    logger.warning("No large models available, using Nemotron 49B")
                    return "nemotron_49b"
            else:
                # Simple queries - can use smaller/faster models
                if health_status.get("nemotron_49b", False):
                    logger.info("Using Nemotron 49B for simple query")
                    return "nemotron_49b"
                elif health_status.get("deepseek", False):
                    logger.info("Using DeepSeek for simple query")
                    return "deepseek"
                elif health_status.get("llama", False):
                    logger.info("Using Llama for simple query")
                    return "llama"
                else:
                    logger.warning("No models available, falling back to Nemotron 49B")
                    return "nemotron_49b"
                    
        except Exception as e:
            logger.error(f"Error choosing LLM model: {str(e)}")
            return "nemotron_49b"  # Default fallback
    
    async def _get_relevant_schema(self, query: str) -> str:
        """Get relevant database schema information - limited to prevent token overflow"""
        try:
            # Get all tables first
            schema_result = await sql_executor.get_schema_info()
            
            if not schema_result["success"]:
                return "No schema information available"
            
            tables = schema_result["data"]
            
            # Limit to first 10 tables to prevent token overflow
            # LLM has ~111k char limit, full schema is 279k chars
            max_tables = 10
            limited_tables = tables[:max_tables]
            
            schema_text = f"Available tables in {self.db_type} database (showing {len(limited_tables)} of {len(tables)} tables):\n"
            
            for table in limited_tables:
                table_name = table["TABLE_NAME"]
                schema_text += f"- {table_name}\n"
                
                # Get column information for each table
                table_schema = await sql_executor.get_schema_info(table_name)
                if table_schema["success"]:
                    columns = table_schema["data"]
                    # Limit columns shown
                    max_cols = 5
                    shown_cols = columns[:max_cols]
                    schema_text += "  Columns:\n"
                    for col in shown_cols:
                        schema_text += f"    - {col['COLUMN_NAME']} ({col['DATA_TYPE']})\n"
                    if len(columns) > max_cols:
                        schema_text += f"    ... and {len(columns) - max_cols} more columns\n"
            
            if len(tables) > max_tables:
                schema_text += f"\n... and {len(tables) - max_tables} more tables available\n"
            
            return schema_text
            
        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            return "Schema information unavailable"
    
    async def _generate_sql_query(
        self, 
        natural_query: str, 
        schema_info: str, 
        conversation_history: List[Dict[str, Any]] = None,
        llm_choice: str = "nemotron_49b"
    ) -> Optional[str]:
        """Generate SQL query using chosen LLM"""
        try:
            # Build the prompt for SQL generation
            prompt = self._build_sql_generation_prompt(
                natural_query, 
                schema_info, 
                conversation_history,
                self.db_type
            )
            
            # Generate using the chosen LLM
            if llm_choice == "nemotron_49b":
                result = await llm_manager.generate_with_nemotron_49b(
                    query=prompt,
                    temperature=0.1
                )
            elif llm_choice == "nemotron_253b":
                result = await llm_manager.generate_with_nemotron_253b(
                    query=prompt,
                    temperature=0.1
                )
            elif llm_choice == "deepseek":
                result = await llm_manager.generate_with_deepseek(
                    query=prompt,
                    temperature=0.1
                )
            elif llm_choice == "llama":
                result = await llm_manager.generate_with_llama(
                    query=prompt,
                    temperature=0.1
                )
            else:
                logger.error(f"Unknown LLM choice: {llm_choice}")
                return None
            
            if not result["success"]:
                logger.error(f"LLM generation error: {result.get('error')}")
                return None
            
            # Extract SQL from the response
            sql_query = self._extract_sql_from_response(result["response"])
            
            if sql_query:
                logger.info(f"Generated SQL query using {llm_choice}: {sql_query}")
                return sql_query
            else:
                logger.error("No SQL query found in LLM response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating SQL query: {str(e)}")
            return None
    
    def _build_sql_generation_prompt(
        self, 
        natural_query: str, 
        schema_info: str, 
        conversation_history: List[Dict[str, Any]],
        db_type: str
    ) -> str:
        """Build enhanced prompt for SQL generation"""
        
        prompt = f"""You are an expert SQL query generator for {db_type} database. Generate a SQL query to answer the following natural language question.

Database Schema (showing available tables and columns):
{schema_info}

CRITICAL RULES - Your SQL MUST follow these exactly:
1. ALWAYS specify column names after SELECT (e.g., SELECT column1, column2 or SELECT *)
2. ALWAYS use actual table names from the schema above (NEVER use "that table" or generic names)
3. Use proper SQL syntax - no natural language in SQL
4. Date filters must use proper SQL date functions (DATEADD, DATEDIFF, etc.)
5. End with semicolon
6. NO explanations, ONLY the SQL query
7. NO markdown code blocks

BAD EXAMPLES (NEVER do this):
- select from that table where date is last month;  (missing columns, bad table name)
- SELECT * FROM table WHERE date = last month;  (natural language in SQL)
- SELECT data from the table;  (vague table reference)

GOOD EXAMPLES:
- SELECT * FROM ActualCapacityDecember2025 WHERE ENTRY_DATE >= DATEADD(month, -1, GETDATE());
- SELECT SBU, CustomerName FROM ActualCapacityMay2026 WHERE DieNumber IS NOT NULL;
- SELECT COUNT(*) FROM information_schema.tables;

Question: {natural_query}

Generate ONLY the SQL query:"""
        
        return prompt
        
        # Add conversation context if available
        if conversation_history:
            prompt += "\nRecent conversation context:\n"
            for i, msg in enumerate(conversation_history[-3:]):  # Last 3 messages
                prompt += f"{i+1}. {msg.get('role', 'user')}: {msg.get('content', '')}\n"
            prompt += "\n"
        
        prompt += "SQL Query:\n"
        
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response - improved for Kalyani LLM"""
        try:
            if not response:
                return None
                
            response = response.strip()
            
            # Common SQL keywords to identify queries
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP"]
            
            # Method 1: Look for SQL code blocks
            if "```sql" in response.lower() or "```" in response:
                # Extract from code blocks
                import re
                # Match ```sql ... ``` or just ``` ... ```
                pattern = r'```(?:sql)?\s*\n?(.*?)```'
                matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
                if matches:
                    for match in matches:
                        match = match.strip()
                        if any(keyword in match.upper() for keyword in sql_keywords):
                            sql_query = match.rstrip(';') + ';'
                            return sql_query
            
            # Method 2: Find SQL starting with keywords
            for keyword in sql_keywords:
                if keyword in response.upper():
                    # Find the start of SQL
                    start_idx = response.upper().find(keyword)
                    if start_idx >= 0:
                        # Extract from this point
                        potential_sql = response[start_idx:]
                        
                        # Clean up - stop at common sentence endings
                        stop_markers = ['\n\n', '. ', 'Here', 'This', 'Please', 'Note:', 'Explanation:']
                        for marker in stop_markers:
                            if marker in potential_sql:
                                potential_sql = potential_sql[:potential_sql.find(marker)]
                        
                        # Clean the query
                        lines = potential_sql.split('\n')
                        cleaned_lines = []
                        for line in lines:
                            line = line.strip()
                            # Skip markdown and explanations
                            if line and not line.startswith(('```', '#', '-', '*', 'Note:', 'Explanation:', 'Here')):
                                cleaned_lines.append(line)
                        
                        if cleaned_lines:
                            sql_query = ' '.join(cleaned_lines)
                            sql_query = sql_query.rstrip(';').rstrip() + ';'
                            # Validate it looks like SQL
                            if any(keyword in sql_query.upper() for keyword in sql_keywords[:3]):  # SELECT, INSERT, UPDATE
                                return sql_query
            
            # Method 3: Look for lines that start with SQL keywords
            lines = response.split('\n')
            for i, line in enumerate(lines):
                line_stripped = line.strip().upper()
                if any(line_stripped.startswith(keyword) for keyword in sql_keywords):
                    # Found SQL start, collect all SQL-like lines
                    sql_lines = []
                    for j in range(i, len(lines)):
                        current_line = lines[j].strip()
                        if not current_line:
                            continue
                        # Stop if we hit explanation markers
                        if current_line.lower() in ['this', 'here', 'please', 'note:', 'explanation:']:
                            break
                        sql_lines.append(current_line)
                    
                    if sql_lines:
                        sql_query = ' '.join(sql_lines)
                        sql_query = sql_query.rstrip(';').rstrip() + ';'
                        return sql_query
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SQL from response: {str(e)}")
            return None
    
    async def _execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query with database-specific configuration"""
        try:
            # Import urllib.parse for URL encoding credentials
            import urllib.parse
            from sqlalchemy import create_engine
            from sqlalchemy.pool import QueuePool
            
            # URL-encode credentials to handle special characters
            encoded_username = urllib.parse.quote_plus(self.db_config['username'])
            encoded_password = urllib.parse.quote_plus(self.db_config['password'])
            
            # Build database URL for the specific database with encoded credentials
            db_url = f"mssql+pymssql://{encoded_username}:{encoded_password}@{self.db_config['server']}:{self.db_config.get('port', 1433)}/{self.db_config['database']}"
            
            # Create temporary engine for this query
            temp_engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Execute the query
            with temp_engine.connect() as conn:
                import pandas as pd
                df = pd.read_sql_query(sql_query, conn)
                
                result = {
                    "success": True,
                    "data": df.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "row_count": len(df),
                    "query": sql_query
                }
                
                logger.info(f"Query executed successfully on {self.db_type} database. Returned {len(df)} rows.")
                return result
                
        except Exception as e:
            logger.error(f"SQL execution error on {self.db_type} database: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": sql_query,
                "data": [],
                "columns": [],
                "row_count": 0
            }
    
    async def _format_results(self, result: Dict[str, Any], original_query: str) -> str:
        """Format SQL results for user response"""
        try:
            if result["row_count"] == 0:
                return f"No results found for your query in the {self.db_type} database: '{original_query}'"
            
            # Format results in a user-friendly way
            response = f"Found {result['row_count']} results in the {self.db_type} database:\n\n"
            
            # Show first few rows as preview
            data = result["data"]
            columns = result["columns"]
            
            if data:
                # Create a table-like format for the first 5 rows
                max_rows = min(5, len(data))
                
                # Header
                header = " | ".join([col[:15].ljust(15) for col in columns])
                response += header + "\n"
                response += "-" * len(header) + "\n"
                
                # Data rows
                for i, row in enumerate(data[:max_rows]):
                    row_values = []
                    for col in columns:
                        value = str(row.get(col, ""))[:15]
                        row_values.append(value.ljust(15))
                    response += " | ".join(row_values) + "\n"
                
                if len(data) > max_rows:
                    response += f"... and {len(data) - max_rows} more rows\n\n"
            
            response += f"\nSQL Query executed on {self.db_type} database: {result['query']}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return f"Query executed successfully on {self.db_type} database. Found {result.get('row_count', 0)} results."
