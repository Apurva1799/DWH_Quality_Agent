from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.database import sql_executor
from app.llm_manager import llm_manager
from loguru import logger
import re

class QueryCorrectorAgent(BaseAgent):
    """Query Corrector Agent for validating and fixing SQL queries using DGX 3B Client"""
    
    def __init__(self):
        super().__init__("Query Corrector Agent")
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process SQL query for validation and correction"""
        try:
            # Extract SQL query from request
            sql_query = self._extract_sql_query(request)
            
            if not sql_query:
                return AgentResponse(
                    success=False,
                    response="No SQL query found in request",
                    error="Missing SQL query",
                    agent_name=self.name
                )
            
            # Validate the SQL query syntax
            validation_result = await sql_executor.validate_query(sql_query)
            
            if validation_result["valid"]:
                # Query is valid, check for potential optimizations
                optimization_suggestions = await self._check_optimizations(sql_query)
                
                response = "SQL query is valid and syntactically correct."
                if optimization_suggestions:
                    response += f"\n\nOptimization suggestions:\n{optimization_suggestions}"
                
                return AgentResponse(
                    success=True,
                    response=response,
                    agent_name=self.name,
                    data={
                        "original_query": sql_query,
                        "corrected_query": sql_query,
                        "validation_passed": True,
                        "optimizations": optimization_suggestions
                    }
                )
            
            # Query has syntax errors, attempt to fix them
            corrected_query = await self._correct_sql_query(sql_query, validation_result.get("error"))
            
            if not corrected_query:
                return AgentResponse(
                    success=False,
                    response=f"Unable to correct SQL query. Original error: {validation_result.get('error')}",
                    error="Query correction failed",
                    agent_name=self.name,
                    data={
                        "original_query": sql_query,
                        "validation_error": validation_result.get("error")
                    }
                )
            
            # Validate the corrected query
            corrected_validation = await sql_executor.validate_query(corrected_query)
            
            if corrected_validation["valid"]:
                return AgentResponse(
                    success=True,
                    response=f"SQL query corrected successfully.\n\nOriginal query: {sql_query}\nCorrected query: {corrected_query}",
                    agent_name=self.name,
                    data={
                        "original_query": sql_query,
                        "corrected_query": corrected_query,
                        "validation_passed": True,
                        "corrections_made": True
                    }
                )
            else:
                return AgentResponse(
                    success=False,
                    response=f"Corrected query still has errors: {corrected_validation.get('error')}",
                    error="Correction validation failed",
                    agent_name=self.name,
                    data={
                        "original_query": sql_query,
                        "corrected_query": corrected_query,
                        "remaining_error": corrected_validation.get("error")
                    }
                )
                
        except Exception as e:
            logger.error(f"Query Corrector Agent processing error: {str(e)}")
            return AgentResponse(
                success=False,
                response="Query Corrector Agent processing failed",
                error=str(e),
                agent_name=self.name
            )
    
    def _extract_sql_query(self, request: AgentRequest) -> Optional[str]:
        """Extract SQL query from request context or data"""
        try:
            # Check if SQL query is in the context
            if request.context and "sql_query" in request.context:
                return request.context["sql_query"]
            
            # Check if SQL query is in the metadata
            if request.metadata and "sql_query" in request.metadata:
                return request.metadata["sql_query"]
            
            # Try to extract SQL query from the query text
            return self._extract_sql_from_text(request.query)
            
        except Exception as e:
            logger.error(f"Error extracting SQL query: {str(e)}")
            return None
    
    def _extract_sql_from_text(self, text: str) -> Optional[str]:
        """Extract SQL query from text"""
        try:
            # Look for SQL keywords in the text
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP"]
            
            text_upper = text.upper()
            
            for keyword in sql_keywords:
                if keyword in text_upper:
                    # Find the start of the SQL query
                    start_idx = text_upper.find(keyword)
                    potential_sql = text[start_idx:].strip()
                    
                    # Try to identify the complete SQL statement
                    if potential_sql:
                        # Remove common prefixes and extract clean SQL
                        sql_match = re.search(r'(SELECT.*?;|INSERT.*?;|UPDATE.*?;|DELETE.*?;|WITH.*?;)', 
                                            potential_sql, re.IGNORECASE | re.DOTALL)
                        if sql_match:
                            return sql_match.group(1).strip()
                        
                        # Fallback: return the potential SQL as-is
                        if potential_sql.endswith(';'):
                            return potential_sql
                        else:
                            return potential_sql + ';'
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SQL from text: {str(e)}")
            return None
    
    async def _correct_sql_query(self, original_query: str, error_message: str) -> Optional[str]:
        """Correct SQL query using DGX 3B Client"""
        try:
            # Build the correction prompt
            prompt = self._build_correction_prompt(original_query, error_message)
            
            # Use DGX 3B Client for query correction
            result = await llm_manager.generate_with_dgx(
                query=prompt,
                model="qwen-72b",
                temperature=0.2
            )
            
            if not result["success"]:
                logger.error(f"DGX 3B Client error: {result.get('error')}")
                return None
            
            # Extract corrected SQL from the response
            corrected_sql = self._extract_sql_from_response(result["response"])
            
            if corrected_sql:
                logger.info(f"Corrected SQL query: {corrected_sql}")
                return corrected_sql
            else:
                logger.error("No corrected SQL found in DGX response")
                return None
                
        except Exception as e:
            logger.error(f"Error correcting SQL query: {str(e)}")
            return None
    
    def _build_correction_prompt(self, original_query: str, error_message: str) -> str:
        """Build prompt for SQL correction"""
        
        prompt = f"""You are a SQL expert. Fix the syntax error in the following MSSQL query.

Original Query:
{original_query}

Error Message:
{error_message}

Instructions:
1. Identify and fix the syntax error
2. Ensure the query follows MSSQL syntax rules
3. Maintain the original query's intent
4. Return ONLY the corrected SQL query, no explanations
5. Do not add any additional text or formatting
6. Make sure the query ends with a semicolon

Corrected SQL Query:
"""
        
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract corrected SQL from DGX response"""
        try:
            response = response.strip()
            
            # Look for SQL keywords in the response
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
            
            lines = response.split('\n')
            sql_lines = []
            
            for line in lines:
                line = line.strip()
                
                # Skip explanatory lines
                if any(skip_word in line.lower() for skip_word in 
                       ['here', 'corrected', 'fixed', 'original', 'error', 'explanation', 'note']):
                    continue
                
                # Check if line contains SQL
                if any(keyword in line.upper() for keyword in sql_keywords):
                    sql_lines.append(line)
                elif sql_lines and line:  # Continue SQL block if started
                    sql_lines.append(line)
                elif sql_lines and not line:  # Empty line might end SQL block
                    break
            
            if sql_lines:
                corrected_query = ' '.join(sql_lines)
                
                # Clean up the query
                corrected_query = corrected_query.rstrip(';')
                corrected_query += ';'
                
                # Basic validation
                if any(keyword in corrected_query.upper() for keyword in sql_keywords):
                    return corrected_query
            
            # Fallback: try to find SQL in the entire response
            for keyword in sql_keywords:
                if keyword in response.upper():
                    start_idx = response.upper().find(keyword)
                    potential_sql = response[start_idx:].strip()
                    
                    # Extract up to the semicolon
                    if ';' in potential_sql:
                        corrected_query = potential_sql.split(';')[0] + ';'
                    else:
                        corrected_query = potential_sql + ';'
                    
                    return corrected_query
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting corrected SQL: {str(e)}")
            return None
    
    async def _check_optimizations(self, sql_query: str) -> Optional[str]:
        """Check for potential SQL optimizations"""
        try:
            # Basic optimization checks
            optimizations = []
            
            query_upper = sql_query.upper()
            
            # Check for SELECT *
            if "SELECT *" in query_upper:
                optimizations.append("- Consider specifying specific columns instead of using SELECT *")
            
            # Check for missing WHERE clauses in DELETE/UPDATE
            if ("DELETE" in query_upper or "UPDATE" in query_upper) and "WHERE" not in query_upper:
                optimizations.append("- WARNING: DELETE/UPDATE without WHERE clause will affect all rows")
            
            # Check for potential index usage suggestions
            if "WHERE" in query_upper and "ORDER BY" in query_upper:
                optimizations.append("- Consider adding indexes on columns used in WHERE and ORDER BY clauses")
            
            # Check for JOIN optimization
            if "JOIN" in query_upper and "ON" in query_upper:
                optimizations.append("- Ensure JOIN columns are properly indexed")
            
            if optimizations:
                return "\n".join(optimizations)
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking optimizations: {str(e)}")
            return None
