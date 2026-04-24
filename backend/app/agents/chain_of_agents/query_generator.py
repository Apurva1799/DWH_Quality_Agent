"""
Query Generator Agent
Generates optimized SQL based on selected tables and user query
"""

import asyncio
import re
from typing import List, Dict
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
        
        # Build table info for prompt with columns
        table_info_parts = []
        for table in selected_tables[:5]:  # Limit to top 5
            desc = table_descriptions.get(table, 'No description')
            
            # Extract full table name with schema from description
            schema_match = re.search(r'[`"]?(\w+\.\w+)[`"]?', desc)
            if schema_match:
                full_table_name = schema_match.group(1)
            else:
                full_table_name = table
            
            # Extract columns section if present (handles "Columns:", "Column Profiles:", etc.)
            # Match the heading and capture everything until next ** or end
            columns_match = re.search(r'\*\*Columns?(?:\s+Profiles?)?:\*\*\s*(.*?)(?=\*\*|$)', desc, re.DOTALL)
            if columns_match:
                columns_section = columns_match.group(1).strip()
                # Extract column names from the profile format
                column_names = re.findall(r'`([^`]+)`\s*\(', columns_section)
                if column_names:
                    columns_text = 'Columns: ' + ', '.join(column_names[:10])
                else:
                    # Fallback: limit columns to first 10 lines
                    columns_lines = columns_section.split('\n')[:10]
                    columns_text = 'Columns:\n' + '\n'.join(columns_lines)
            else:
                columns_text = "No column info available"
            
            table_info_parts.append(f"Table: {full_table_name}\n{columns_text}")
        
        table_info = "\n\n".join(table_info_parts)
        
        system_prompt = f"""You are an expert MSSQL T-SQL query generator.

User Query: {query}

Selected Tables:
{table_info}

Generate a valid MSSQL T-SQL query following these rules:

1. Use exact table names from the selected tables (including schema prefix like BFL.Fact_OEE)
2. Use proper T-SQL syntax (MSSQL, NOT PostgreSQL or MySQL)
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
11. For INFORMATION_SCHEMA queries, use TABLE_CATALOG = DB_NAME() NOT table_schema = 'public'
12. Use DB_NAME() to get current database name

IMPORTANT: Output ONLY the SQL query. Do NOT include any thinking, explanations, or markdown formatting. Start directly with SELECT.

Output ONLY the SQL query, nothing else:"""
        
        try:
            # Always use Python-based fallback SQL generation (no LLM for SQL)
            query_lower = query.lower()
            
            # Handle table listing queries
            if any(phrase in query_lower for phrase in ['show all tables', 'list all tables', 'show tables', 'what tables']):
                sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;"
                state.generated_sql = sql
                state.sql_valid = True
                state.sql_error = None
                state.add_trace(self.name, "Generated SQL (table listing - Python)")
                return state
            
            # Use Python-based SQL generation for all queries
            logger.info(f"[{self.name}] Using Python-based SQL generation")
            sql = self._generate_fallback_sql(selected_tables, table_descriptions, query, state.join_relationships)
            is_valid, error_msg = self._validate_sql(sql)
            
            state.generated_sql = sql
            state.sql_valid = is_valid
            state.sql_error = error_msg if not is_valid else None
            state.add_trace(self.name, f"Generated SQL (Python - valid={is_valid})")
            logger.info(f"[{self.name}] Python SQL: {sql[:100]}...")
            
        except Exception as e:
            logger.error(f"[{self.name}] Generation error: {e}")
            state.generated_sql = ""
            state.sql_valid = False
            state.sql_error = str(e)
            state.add_trace(self.name, f"Error: {str(e)}")
        
        return state
    
    def _clean_sql(self, raw: str) -> str:
        """Clean SQL from LLM response - remove ALL non-SQL content aggressively"""
        import re
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', raw, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove thinking tags
        sql = re.sub(r'<thinking>.*?</thinking>', '', sql, flags=re.DOTALL | re.IGNORECASE)
        
        # AGGRESSIVE: Find ONLY the first SQL statement, stop at first semicolon
        # Use non-greedy match but don't cross line boundaries for SQL keywords
        sql_pattern = r'(SELECT\s+(?:DISTINCT\s+)?[\w\*,\s\(\)]+?FROM\s+\w+.*?;)'
        match = re.search(sql_pattern, sql, re.IGNORECASE)
        
        if match:
            sql = match.group(1)
        else:
            # Try simpler pattern for single-line SQL
            sql_pattern = r'(SELECT\s+.*?;|INSERT\s+INTO\s+.*?;|UPDATE\s+\w+\s+.*?;|DELETE\s+FROM\s+.*?;)'
            match = re.search(sql_pattern, sql, re.IGNORECASE)
            if match:
                sql = match.group(1)
            else:
                # Last resort: take first line that looks like SQL
                lines = sql.split('\n')
                for line in lines:
                    line_stripped = line.strip()
                    if re.match(r'^(SELECT|INSERT|UPDATE|DELETE)\s', line_stripped, re.IGNORECASE):
                        # Remove everything after the semicolon if present
                        if ';' in line_stripped:
                            sql = line_stripped.split(';')[0] + ';'
                        else:
                            sql = line_stripped + ';'
                        break
                else:
                    sql = ""
        
        # Remove any lines after the SQL that contain explanation words
        if '\n' in sql:
            lines = sql.split('\n')
            cleaned_lines = []
            for line in lines:
                if re.search(r'\b(But|Let\'s|I should|Here\'s|For|If you|Maybe|Perhaps|Alternatively|Or|Also|Note|Wait|Hmm|Actually)\b', line, re.IGNORECASE):
                    break
                cleaned_lines.append(line)
            sql = '\n'.join(cleaned_lines)
        
        # Replace placeholder dates with actual MSSQL date functions
        sql = re.sub(r"'start_of_last_month'", 
                     "DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0)", 
                     sql, flags=re.IGNORECASE)
        sql = re.sub(r"'start_of_current_month'", 
                     "DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)", 
                     sql, flags=re.IGNORECASE)
        
        # Apply all PostgreSQL to MSSQL conversions
        sql = self._convert_postgresql_to_mssql(sql)
        
        # Clean up
        sql = sql.strip()
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _convert_postgresql_to_mssql(self, sql: str) -> str:
        """Convert PostgreSQL syntax to MSSQL T-SQL"""
        import re
        
        # pg_catalog.pg_tables → INFORMATION_SCHEMA.TABLES
        sql = re.sub(r'FROM\s+pg_catalog\.pg_tables', 'FROM INFORMATION_SCHEMA.TABLES', sql, flags=re.IGNORECASE)
        sql = re.sub(r'FROM\s+pg_tables', 'FROM INFORMATION_SCHEMA.TABLES', sql, flags=re.IGNORECASE)
        
        # CURRENT_DATE → CAST(GETDATE() AS DATE)
        sql = re.sub(r'CURRENT_DATE', 'CAST(GETDATE() AS DATE)', sql, flags=re.IGNORECASE)
        
        # NOW() → GETDATE()
        sql = re.sub(r'NOW\(\)', 'GETDATE()', sql, flags=re.IGNORECASE)
        
        # DATE_TRUNC('month', date) → DATEADD(month, DATEDIFF(month, 0, date), 0)
        sql = re.sub(r"DATE_TRUNC\s*\(\s*['\"]month['\"]\s*,\s*([^)]+)\)", 
                     r'DATEADD(month, DATEDIFF(month, 0, \1), 0)', sql, flags=re.IGNORECASE)
        
        # INTERVAL → DATEADD
        sql = re.sub(r"DATEADD\s*\(\s*['\"](\w+)['\"]\s*,\s*([^)]+)\)\s*-\s*INTERVAL\s+['\"](\d+)\s+(\w+)['\"]", 
                     r'DATEADD(\1, \2 - \3, GETDATE())', sql, flags=re.IGNORECASE)
        
        # schemaname/tablename → TABLE_SCHEMA/TABLE_NAME
        sql = re.sub(r'schemaname', 'TABLE_SCHEMA', sql, flags=re.IGNORECASE)
        sql = re.sub(r'tablename', 'TABLE_NAME', sql, flags=re.IGNORECASE)
        
        # table_schema = 'public' → TABLE_CATALOG = DB_NAME()
        sql = re.sub(r"TABLE_SCHEMA\s*=\s*'public'", "TABLE_CATALOG = DB_NAME()", sql, flags=re.IGNORECASE)
        
        return sql
    
    def _generate_fallback_sql(self, selected_tables: List[str], table_descriptions: Dict[str, str], query: str = "", join_relationships: Dict = None) -> str:
        """Generate SQL query with multi-table JOIN support"""
        if not selected_tables:
            return ""
        
        query_lower = query.lower()
        join_rels = join_relationships or {}
        
        # Identify fact and dimension tables
        fact_table = None
        dim_tables = []
        
        for table in selected_tables:
            if 'fact_' in table.lower():
                fact_table = table
            elif 'dim_' in table.lower():
                dim_tables.append(table)
        
        # If no fact table found, use first table
        if not fact_table and selected_tables:
            fact_table = selected_tables[0]
        
        # Get fact table description and columns
        fact_desc = table_descriptions.get(fact_table, '')
        fact_schema_match = re.search(r'[`"]?(\w+\.\w+)[`"]?', fact_desc)
        fact_full_name = fact_schema_match.group(1) if fact_schema_match else fact_table
        
        # Extract fact table columns
        fact_columns_match = re.search(r'\*\*Columns?(?:\s+Profiles?)?:\*\*\s*(.*?)(?=\*\*|$)', fact_desc, re.DOTALL)
        fact_column_names = []
        if fact_columns_match:
            fact_columns_section = fact_columns_match.group(1).strip()
            fact_column_names = re.findall(r'`([^`]+)`\s*\(', fact_columns_section)
        
        # Build SELECT columns
        select_cols = []
        join_clauses = []
        
        # Check if we need aggregation (top N by metric)
        needs_agg = any(phrase in query_lower for phrase in ['top', 'by sales', 'by revenue', 'total'])
        agg_col = None
        
        # Find aggregation column (sales amount) - prioritize amount columns
        if needs_agg:
            # First pass: look for columns with 'amount' in the name (excluding keys)
            for col in fact_column_names:
                col_lower = col.lower()
                if 'amount' in col_lower and 'key' not in col_lower:
                    agg_col = col
                    break
            # Second pass: look for sales/revenue columns (excluding keys)
            if not agg_col:
                for col in fact_column_names:
                    col_lower = col.lower()
                    if any(metric in col_lower for metric in ['sales', 'revenue', 'total']):
                        if 'key' not in col_lower and 'id' not in col_lower:
                            agg_col = col
                            break
        
        # Add dimension columns for customer names
        dim_alias_idx = 0
        for dim_table in dim_tables:
            dim_desc = table_descriptions.get(dim_table, '')
            dim_schema_match = re.search(r'[`"]?(\w+\.\w+)[`"]?', dim_desc)
            dim_full_name = dim_schema_match.group(1) if dim_schema_match else dim_table
            
            # Generate unique alias for this dimension
            dim_alias = f"d{dim_alias_idx}" if dim_alias_idx > 0 else "d"
            dim_alias_idx += 1
            
            # Extract dimension columns
            dim_columns_match = re.search(r'\*\*Columns?(?:\s+Profiles?)?:\*\*\s*(.*?)(?=\*\*|$)', dim_desc, re.DOTALL)
            dim_column_names = []
            if dim_columns_match:
                dim_columns_section = dim_columns_match.group(1).strip()
                dim_column_names = re.findall(r'`([^`]+)`\s*\(', dim_columns_section)
                logger.info(f"[QueryGenerator] Extracted {len(dim_column_names)} columns from {dim_table}: {dim_column_names[:10]}")
            
            # Find join key from relationships
            join_key = None
            if fact_table in join_rels:
                for rel in join_rels[fact_table]:
                    if rel['related_table'] == dim_table:
                        join_key = rel['join_key']
                        break
            
            # If no join key found, try common patterns
            if not join_key:
                for col in fact_column_names:
                    if any(keyword in col.lower() for keyword in ['customer', 'product', 'date']):
                        if col in [c.lower().replace('_', '') for c in dim_column_names] or \
                           any(col.lower() in c.lower() for c in dim_column_names):
                            join_key = col
                            break
            
            if join_key:
                # Add meaningful dimension columns (name/description columns), exclude keys
                # Look for columns with 'name', 'description', or the entity name itself (e.g., 'Customer', 'Product')
                entity_name = dim_table.replace('Dim_', '').replace('_Sales', '').lower()
                name_cols = [c for c in dim_column_names if any(n in c.lower() for n in ['name', 'description', entity_name]) and not c.lower().endswith('key')]
                # Filter out any column that ends with 'Key' or 'ID' - show only human-readable values
                name_cols = [c for c in name_cols if not (c.lower().endswith('key') or c.lower().endswith('id'))]
                # Also exclude the key column itself
                key_col_lower = join_key.lower()
                name_cols = [c for c in name_cols if c.lower() != key_col_lower]
                if not name_cols:
                    # Fallback: get any column that is NOT a key/ID column and not the join key
                    name_cols = [c for c in dim_column_names if not (c.lower().endswith('key') or c.lower().endswith('id') or 'key' in c.lower() or c.lower() == key_col_lower)]
                if not name_cols:
                    name_cols = dim_column_names[:1]  # Last resort: just first column
                
                for col in name_cols[:2]:  # Limit to 2 descriptive columns per dimension
                    select_cols.append(f"{dim_alias}.{col}")
                
                # Build JOIN clause
                join_clauses.append(f"LEFT JOIN {dim_full_name} {dim_alias} ON f.{join_key} = {dim_alias}.{join_key}")
        
        # Add aggregation if needed
        group_by_cols = []
        if needs_agg and agg_col:
            select_cols.insert(0, f"SUM(f.{agg_col}) as Total{agg_col}")
            # For GROUP BY, we need to reference the actual columns being selected (non-aggregated)
            group_by_cols = [c for c in select_cols if not c.startswith("SUM")]
            # Convert aliases like "d.CustomerName" to just the column reference
            group_by_refs = []
            for col in group_by_cols:
                if '.' in col:
                    group_by_refs.append(col)  # Keep table aliases
                else:
                    group_by_refs.append(col)
            group_by = " GROUP BY " + ", ".join(group_by_refs) if group_by_refs else ""
        else:
            # Just select fact columns - exclude key columns, only show meaningful data
            meaningful_cols = [c for c in fact_column_names[:7] if not (c.lower().endswith('key') or c.lower().endswith('id'))]
            if not meaningful_cols:
                meaningful_cols = fact_column_names[:3]  # Fallback if all are keys
            for col in meaningful_cols:
                select_cols.append(f"f.{col}")
            group_by = ""
        
        # Build date filter
        date_filter = ""
        date_col = None
        for col in fact_column_names:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        # Add date column to select for display
        if date_col and date_col not in [c.replace('f.', '') for c in select_cols]:
            select_cols.append(f"f.{date_col}")
            # If aggregating, also add date_col to GROUP BY and rebuild the clause
            if needs_agg and agg_col:
                group_by_cols.append(f"f.{date_col}")
                # Rebuild GROUP BY with updated columns
                group_by_refs = []
                for col in group_by_cols:
                    if '.' in col:
                        group_by_refs.append(col)
                    else:
                        group_by_refs.append(col)
                group_by = " GROUP BY " + ", ".join(group_by_refs) if group_by_refs else ""
        
        # Determine if query has explicit time period
        has_time_period = any(phrase in query_lower for phrase in ['last month', 'this month', 'last week', 'this year', 'yesterday', 'today', 'last year', 'current year'])
        
        if date_col:
            is_int_date = 'key' in date_col.lower()
            if 'last month' in query_lower:
                if is_int_date:
                    date_filter = f" WHERE f.{date_col} >= YEAR(DATEADD(month, -1, GETDATE())) * 10000 + MONTH(DATEADD(month, -1, GETDATE())) * 100 AND f.{date_col} < YEAR(GETDATE()) * 10000 + MONTH(GETDATE()) * 100"
                else:
                    date_filter = f" WHERE f.{date_col} >= DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0) AND f.{date_col} < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)"
            elif 'last year' in query_lower or not has_time_period:
                # Default to last year if no time period specified
                if is_int_date:
                    date_filter = f" WHERE f.{date_col} >= (YEAR(GETDATE()) - 1) * 10000 + 100 AND f.{date_col} < YEAR(GETDATE()) * 10000 + 100"
                else:
                    date_filter = f" WHERE f.{date_col} >= DATEADD(year, DATEDIFF(year, 0, GETDATE()) - 1, 0) AND f.{date_col} < DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)"
        
        # Determine TOP N - only if explicitly requested
        top_match = re.search(r'top\s+(\d+)', query_lower)
        top_n = top_match.group(1) if top_match else None
        
        # Build ORDER BY for aggregation
        order_by = ""
        if needs_agg and agg_col:
            order_by = f" ORDER BY Total{agg_col} DESC"
        
        # Assemble final SQL with proper spacing
        select_clause = ", ".join(select_cols) if select_cols else "f.*"
        join_clause = " ".join(join_clauses) if join_clauses else ""
        
        # Only add TOP if explicitly requested
        top_clause = f"TOP {top_n} " if top_n else ""
        sql = f"SELECT {top_clause}{select_clause} FROM {fact_full_name} f"
        if join_clause:
            sql += f" {join_clause}"
        if date_filter:
            sql += f" {date_filter}"
        if group_by:
            sql += f" {group_by}"
        if order_by:
            sql += f" {order_by}"
        sql += ";"
        
        return sql
    
    def _validate_sql(self, sql: str) -> tuple:
        """Basic SQL validation"""
        if not sql or sql == ';':
            return False, "Empty SQL generated"
        
        # Check for required keywords
        if not re.search(r'SELECT|WITH|INSERT|UPDATE|DELETE', sql, re.IGNORECASE):
            return False, "No SQL statement found"
        
        # Check for FROM clause in SELECT statements
        if re.search(r'SELECT', sql, re.IGNORECASE) and not re.search(r'FROM', sql, re.IGNORECASE):
            return False, "SELECT statement missing FROM clause"
        
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
