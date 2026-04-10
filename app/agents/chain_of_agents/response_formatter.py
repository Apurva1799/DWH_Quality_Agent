"""
Response Formatter Agent
Formats query results into readable responses
"""

import re
import pandas as pd
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState, IntentType
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


class ResponseFormatterAgent(BaseAgent):
    """
    Formats the final response based on:
    - Query intent
    - Execution results
    - Selected tables
    - User's original question
    """
    
    def __init__(self):
        super().__init__("ResponseFormatter", max_retries=1)
        self.llm = KalyaniLangChainLLM()
    
    async def process(self, state: AgentState) -> AgentState:
        """Format the final response based on intent and DB status"""
        intent = state.intent
        db_down = state.response_data.get('db_down', False)

        if intent == IntentType.GENERAL_CHAT:
            state.final_response = await self._format_general_chat(state)
        elif intent == IntentType.SCHEMA_QUESTION:
            state.final_response = await self._format_schema_response(state)
        elif intent == IntentType.CLARIFICATION_NEEDED:
            state.final_response = state.clarification_question or "Could you provide more details?"
        elif intent == IntentType.DATA_QUALITY:
            state.final_response = await self._format_data_quality_response(state)
        elif not state.context_complete:
            # Context incomplete - show relevant tables and ask for clarification
            state.final_response = await self._format_incomplete_context_response(state)
        elif db_down:
            # Database is down - show SQL if generated, otherwise show metadata
            if state.generated_sql:
                state.final_response = await self._format_sql_response(state)
            else:
                state.final_response = await self._format_db_down_response(state)
        else:
            # SQL_QUERY or VISUALIZATION
            state.final_response = await self._format_sql_response(state)

        state.add_trace(self.name, "Response formatted")
        logger.info(f"[{self.name}] Formatted response ({len(state.final_response)} chars)")

        return state
    
    async def _format_db_down_response(self, state: AgentState) -> str:
        """Format response when database is unavailable"""
        response_parts = []
        
        # Explain the situation
        response_parts.append("**Database Currently Unavailable**\n")
        response_parts.append("The database server is currently unreachable. I can still help you explore the available tables and schema information.\n")
        
        # Show relevant tables based on query
        if state.selected_tables:
            response_parts.append(f"**Relevant Tables for your query \"{state.user_query}\":**\n")
            for table in state.selected_tables[:50]:  # Show up to 50 relevant tables
                desc = state.table_descriptions.get(table, "")
                # Extract first line of description
                first_line = desc.split('\n')[0] if desc else "No description"
                response_parts.append(f"- **{table}**: {first_line[:200]}")
        else:
            response_parts.append("**Available Tables:**\n")
            # Show all tables from metadata (up to 100)
            all_tables = list(state.table_descriptions.keys())[:100]
            for table in all_tables:
                desc = state.table_descriptions.get(table, "")
                first_line = desc.split('\n')[0] if desc else "No description"
                response_parts.append(f"- **{table}**: {first_line[:200]}")
        
        response_parts.append("\n*Once the database connection is restored, you'll be able to execute SQL queries on these tables.*")
        
        return "\n".join(response_parts)

    def _format_sql_for_display(self, sql: str) -> str:
        if not sql:
            return sql

        s = str(sql).strip()
        s = re.sub(r"\s+", " ", s)

        keywords = [
            "SELECT",
            "FROM",
            "LEFT JOIN",
            "RIGHT JOIN",
            "INNER JOIN",
            "FULL JOIN",
            "JOIN",
            "WHERE",
            "GROUP BY",
            "HAVING",
            "ORDER BY",
            "LIMIT",
            "OFFSET",
        ]

        for kw in keywords:
            s = re.sub(rf"(?i)\\s+{re.escape(kw)}\\s+", f"\n{kw} ", s)

        s = re.sub(r"(?i)\nWHERE ", "\nWHERE\n  ", s)
        s = re.sub(r"(?i)\nGROUP BY ", "\nGROUP BY\n  ", s)
        s = re.sub(r"(?i)\nORDER BY ", "\nORDER BY\n  ", s)
        s = re.sub(r"(?i)\nHAVING ", "\nHAVING\n  ", s)

        s = re.sub(r"(?i)\s+AND\s+", "\n  AND ", s)
        s = re.sub(r"(?i)\s+OR\s+", "\n  OR ", s)

        # Break long SELECT lists a bit for readability
        s = re.sub(r"(?i)\nSELECT ", "SELECT\n  ", s)
        s = re.sub(r",\s+", ",\n  ", s)

        return s.strip()
    
    async def _format_incomplete_context_response(self, state: AgentState) -> str:
        """Format response when context is incomplete but tables were found"""
        response_parts = []
        
        # Explain what's needed
        response_parts.append("**I found some relevant tables, but need more information:**\n")
        
        if state.missing_context:
            response_parts.append("**Missing Information:**\n")
            for item in state.missing_context:
                response_parts.append(f"- {item}")
            response_parts.append("")
        
        # Show relevant tables
        if state.selected_tables:
            response_parts.append(f"**Relevant Tables for \"{state.user_query}\":**\n")
            for table in state.selected_tables[:10]:  # Show up to 10
                desc = state.table_descriptions.get(table, "")
                # Extract columns if available (handles "Columns:", "Column Profiles:", etc.)
                # Match the heading and capture everything until next ** or end
                columns_match = re.search(r'\*\*Columns?(?:\s+Profiles?)?:\*\*\s*(.*?)(?=\*\*|$)', desc, re.DOTALL)
                if columns_match:
                    columns_text = columns_match.group(1).strip()
                    # Extract column names from the profile format `column (type)`
                    column_names = re.findall(r'`([^`]+)`\s*\(', columns_text)
                    if column_names:
                        columns_text = ', '.join(column_names[:5])
                    else:
                        # Fallback: just take first few lines that look like columns
                        columns_lines = [l.strip() for l in columns_text.split('\n')[:5] if '`' in l]
                        columns_text = ', '.join([c.strip().replace('- ', '').replace('*', '').split('(')[0].strip() for c in columns_lines if c.strip()]) if columns_lines else "See table details"
                else:
                    columns_text = "No column info"
                response_parts.append(f"- **{table}**: {columns_text}")
        else:
            response_parts.append("No specific tables matched your query. Try being more specific about the data you need.")
        
        response_parts.append("\n**Example queries:**\n")
        if state.selected_tables:
            table = state.selected_tables[0]
            response_parts.append(f"- Show data from {table}")
            response_parts.append(f"- Count records in {table}")
            response_parts.append(f"- Show {table} for last month")
        
        return "\n".join(response_parts)
    
    async def _format_sql_response(self, state: AgentState) -> str:
        """Format SQL query results with collapsible SQL and INR number formatting"""
        sql = state.generated_sql
        success = state.execution_success
        error = state.execution_error
        df = state.query_results
        
        if not sql:
            return "I wasn't able to generate a SQL query for your request. Could you rephrase your question?"
        
        # Build response
        response_parts = []
        
        # Show database unavailable notice first if applicable
        if not success and error:
            response_parts.append("**Database Currently Unavailable**")
            response_parts.append("The SQL below is ready to execute once the database connection is restored.\n")
        elif not success and not error:
            response_parts.append("**Database Currently Unavailable**")
            response_parts.append("The SQL query below is ready to execute once connection is restored.\n")
        
        # Show SQL in collapsible section - open by default so it's visible
        sql_display = self._format_sql_for_display(sql)
        sql_section = f"""<details class="sql-collapsible" open>
<summary><span class="sql-summary">SQL Query (click to collapse)</span></summary>

```sql
{sql_display}
```

</details>"""
        response_parts.append(sql_section)
        
        # Get execution time from state if available
        execution_time = getattr(state, 'execution_time', None)
        
        # Show results or additional message with real pagination
        if success and df is not None:
            row_count = len(df)
            if row_count > 0:
                # Format numbers in dataframe (convert to Lakhs/Crores for INR)
                df_formatted = self._format_inr_numbers(df)
                
                # Convert DateKey integers to readable dates
                df_formatted = self._format_date_keys(df_formatted)
                
                # Build table with proper markdown formatting and pagination
                execution_time = getattr(state, 'execution_time', None)
                time_info = f" <span class=\"exec-time\">(executed in {execution_time:.2f}s)</span>" if execution_time else ""
                display_limit = 10
                
                if row_count > display_limit:
                    # Show paginated view with navigation
                    table_md = df_formatted.to_markdown(index=False)
                    remaining_pages = (row_count - 1) // display_limit + 1
                    
                    response_parts.append(f"""\n<div class="table-container" data-page-size="{display_limit}">
<div class="table-header">
<strong>Query Results (showing 1-{display_limit} of {row_count} rows){time_info}</strong>
<div class="table-nav">
<button class="nav-btn" onclick="changePage(this, -1)" disabled>&larr;</button>
<span class="page-indicator">Page 1 of {remaining_pages}</span>
<button class="nav-btn" onclick="changePage(this, 1)">&rarr;</button>
</div>
</div>
<div class="table-wrapper">

{table_md}

</div>
<div class="table-footer">Use arrows to navigate pages</div>
</div>""")
                else:
                    table_md = df_formatted.to_markdown(index=False)
                    response_parts.append(f"\n<div class=\"table-container\">\n**Query Results ({row_count} rows){time_info}:**\n\n<div class=\"table-wrapper\">\n\n{table_md}\n\n</div>\n</div>")
            else:
                response_parts.append("\n*Query executed successfully but returned no results.*")
        elif not success:
            response_parts.append("\n*Note: Query could not be executed due to database connectivity issues.*")
        
        # Add insights for data-heavy responses
        if success and df is not None and len(df) > 0 and len(df) < 100:
            insights = await self._generate_insights(state, df)
            if insights:
                response_parts.append(f"\n\n**Insights:**\n{insights}")
        
        # Add visualization if needed
        if state.visualization_needed and state.visualization_type != VisualizationType.NONE:
            chart_html = await self._generate_chart(state, df)
            if chart_html:
                response_parts.append(f"\n\n**Chart:**\n{chart_html}")
        
        return "\n".join(response_parts)
    
    async def _format_schema_response(self, state: AgentState) -> str:
        """Format schema information"""
        if state.selected_tables:
            parts = ["**Available Tables:**\n"]
            for table in state.selected_tables[:15]:
                desc = state.table_descriptions.get(table, "")
                parts.append(f"- **{table}**: {desc[:150]}...")
            return "\n".join(parts)
        else:
            return "I couldn't find specific table information. Could you be more specific about what tables you're looking for?"
    
    async def _format_general_chat(self, state: AgentState) -> str:
        """Format general chat response using LLM"""
        system_prompt = f"""You are Sophie, a helpful database assistant at Kalyani Group.

You help users with:
- SQL query generation
- Database schema questions
- Data analysis
- General database information

Be professional, helpful, and concise. If the user asks about data, offer to generate SQL queries for them.

Selected Tables: {', '.join(state.selected_tables[:5]) if state.selected_tables else 'None'}
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state.user_query)
            ]
            result = await self.llm._agenerate(messages)
            return result.generations[0].message.content
        except Exception as e:
            logger.error(f"[{self.name}] LLM error: {e}")
            return "I'm here to help with your database questions. What would you like to explore?"
    
    def _format_inr_numbers(self, df) -> pd.DataFrame:
        """Format INR numbers as Lakhs/Crores for better readability"""
        df_formatted = df.copy()
        
        for col in df_formatted.columns:
            # Check if column name suggests it's an amount/currency column
            col_lower = col.lower()
            is_amount_col = any(keyword in col_lower for keyword in ['amount', 'inr', 'usd', 'sales', 'revenue', 'total', 'price', 'cost', 'value'])
            
            if df_formatted[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                if is_amount_col:
                    # Format as Lakhs/Crores for INR columns
                    df_formatted[col] = df_formatted[col].apply(self._format_inr_value)
                else:
                    # Format regular numbers with commas, no exponential
                    df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x == int(x) else f"{x:,.2f}" if pd.notna(x) else "")
        
        return df_formatted
    
    def _format_inr_value(self, value) -> str:
        """Convert number to INR format (Lakhs/Crores)"""
        if pd.isna(value):
            return ""
        
        try:
            num = float(value)
            if num == 0:
                return "0"
            
            # Handle negative numbers
            sign = "-" if num < 0 else ""
            num = abs(num)
            
            # Format based on magnitude
            if num >= 10000000:  # 1 Crore = 10 million
                crores = num / 10000000
                return f"{sign}{crores:,.2f} Cr"
            elif num >= 100000:  # 1 Lakh = 100 thousand
                lakhs = num / 100000
                return f"{sign}{lakhs:,.2f} L"
            else:
                return f"{sign}{num:,.0f}"
        except:
            return str(value)
    
    def _format_date_keys(self, df) -> pd.DataFrame:
        """Convert DateKey integer format (YYYYMMDD) to readable date strings"""
        df_formatted = df.copy()
        
        for col in df_formatted.columns:
            col_lower = col.lower()
            # Match various date key patterns: DateKey, date_key, OrderDateKey, etc.
            is_date_key = (
                'datekey' in col_lower or 
                'date_key' in col_lower or
                (col_lower.endswith('key') and 'date' in col_lower) or
                (col_lower.endswith('id') and 'date' in col_lower and len(col) > 8)
            )
            
            if is_date_key:
                # Convert YYYYMMDD integer to readable date
                def format_date_key(val):
                    if pd.isna(val):
                        return ""
                    try:
                        val_int = int(float(val))
                        year = val_int // 10000
                        month = (val_int % 10000) // 100
                        day = val_int % 100
                        if year > 1900 and 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{day:02d}-{month:02d}-{year}"
                        return str(val)
                    except:
                        return str(val)
                
                df_formatted[col] = df_formatted[col].apply(format_date_key)
                # Rename column to be more user-friendly
                new_col_name = col.replace('Key', '').replace('_key', '').replace('ID', '').strip()
                if new_col_name == col or not new_col_name:
                    new_col_name = 'Date'
                df_formatted = df_formatted.rename(columns={col: new_col_name})
        
        return df_formatted

    async def _generate_chart(self, state: AgentState, df) -> str:
        """Generate a simple chart representation using text/ASCII or HTML"""
        try:
            viz_type = state.visualization_type
            fields = state.chart_fields
            
            if not fields or len(fields) < 1:
                return ""
            
            # For now, create a simple HTML table-based bar chart
            if viz_type.value == 'bar_chart' and len(fields) >= 2:
                x_col = fields[0]
                y_col = fields[1]
                
                # Get top 10 values
                chart_data = df.nlargest(10, y_col)[[x_col, y_col]]
                
                # Find max for scaling
                max_val = chart_data[y_col].max()
                
                # Build simple bar chart with HTML/CSS
                bars = []
                for _, row in chart_data.iterrows():
                    label = str(row[x_col])[:20]  # Truncate long labels
                    value = row[y_col]
                    width = (value / max_val) * 100 if max_val > 0 else 0
                    bars.append(f'<div style="margin: 4px 0;"><div style="display: inline-block; width: 120px; font-size: 12px;">{label}</div><div style="display: inline-block; width: {width}%; min-width: 2px; height: 20px; background: linear-gradient(90deg, #4a9eff, #0d6efd); border-radius: 3px; margin-left: 8px;"></div><span style="font-size: 11px; margin-left: 8px; color: var(--text-secondary);">{value:,.0f}</span></div>')
                
                chart_title = state.chart_title or 'Top Values'
                return f'<div style="background: var(--bg-secondary); padding: 16px; border-radius: 8px; margin: 12px 0;">\n<div style="font-weight: 600; margin-bottom: 12px; font-size: 14px;">{chart_title}</div>\n{chr(10).join(bars)}\n</div>'
            
            return ""
        except Exception as e:
            logger.error(f"[{self.name}] Chart generation error: {e}")
            return ""

    async def _generate_insights(self, state: AgentState, df) -> str:
        """Generate insights for data-heavy responses"""
        insights = []
        
        # Check for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:2]:  # First 2 numeric columns
                total = df[col].sum()
                avg = df[col].mean()
                insights.append(f"- Total {col}: {total:,.2f}, Average: {avg:,.2f}")
        
        return "\n".join(insights) if insights else ""

    async def _format_data_quality_response(self, state: AgentState) -> str:
        """Format data quality monitoring report"""
        report = state.response_data.get('quality_report', {})

        if not report:
            return "No data quality report available."

        check_type = report.get('check_type', 'unknown')
        status = report.get('status', 'unknown')

        response_parts = []

        # Header
        if check_type == 'stored_procedures':
            response_parts.append("## Stored Procedure Monitoring Report\n")
        elif check_type == 'schema_changes':
            response_parts.append("## Schema Change Detection Report\n")
        elif 'layer' in report:
            response_parts.append(f"## {report['layer'].title()} Layer Quality Report\n")
        else:
            response_parts.append("## Data Quality Report\n")

        # Status indicator
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'alert': '🚨',
            'critical': '❌',
            'error': '❌',
            'no_tables': 'ℹ️'
        }.get(status, 'ℹ️')

        response_parts.append(f"**Status:** {status_emoji} {status.upper()}\n")

        # Handle stored procedure report
        if check_type == 'stored_procedures':
            total = report.get('total_sps', 0)
            new = report.get('new_sps', 0)
            modified = report.get('modified_sps', 0)
            perf_issues = report.get('performance_issues', 0)

            response_parts.append(f"- **Total Stored Procedures:** {total}")
            response_parts.append(f"- **New SPs Detected:** {new}")
            response_parts.append(f"- **Modified SPs:** {modified}")
            response_parts.append(f"- **Performance Issues:** {perf_issues}\n")

            if new > 0 and report.get('new_sp_details'):
                response_parts.append("### New Stored Procedures")
                for sp in report['new_sp_details'][:10]:
                    response_parts.append(f"- `{sp['schema']}.{sp['name']}`")
                response_parts.append("")

            if modified > 0 and report.get('modified_sp_details'):
                response_parts.append("### Modified Stored Procedures")
                for sp in report['modified_sp_details'][:10]:
                    response_parts.append(f"- `{sp['name']}` (modified: {sp.get('new_modified', 'unknown')})")
                response_parts.append("")

            if perf_issues > 0 and report.get('performance_issue_details'):
                response_parts.append("### Performance Issues")
                for sp in report['performance_issue_details'][:10]:
                    response_parts.append(f"- `{sp['name']}`: {sp['avg_time_ms']}ms avg execution time")
                response_parts.append("")

        # Handle schema changes report
        elif check_type == 'schema_changes':
            total_changes = report.get('total_changes', 0)
            new_tables = report.get('new_tables', 0)
            added_cols = report.get('added_columns', 0)
            dropped_cols = report.get('dropped_columns', 0)

            response_parts.append(f"- **Total Changes:** {total_changes}")
            response_parts.append(f"- **New Tables:** {new_tables}")
            response_parts.append(f"- **Added Columns:** {added_cols}")
            response_parts.append(f"- **Dropped Columns:** {dropped_cols}\n")

            if total_changes > 0 and report.get('changes'):
                response_parts.append("### Recent Changes")
                for change in report['changes'][:20]:
                    change_type = change['type']
                    table = change['table']
                    column = change.get('column', '')
                    if column:
                        response_parts.append(f"- **{change_type}:** `{table}.{column}`")
                    else:
                        response_parts.append(f"- **{change_type}:** `{table}`")
                response_parts.append("")

        # Handle layer quality report
        elif 'layer' in report:
            quality_score = report.get('quality_score', 0)
            tables_checked = report.get('tables_checked', 0)
            tables_sampled = report.get('tables_sampled', 0)
            issues_found = report.get('issues_found', 0)

            response_parts.append(f"- **Quality Score:** {quality_score}%")
            response_parts.append(f"- **Tables Checked:** {tables_checked}")
            response_parts.append(f"- **Tables Sampled:** {tables_sampled}")
            response_parts.append(f"- **Issues Found:** {issues_found}\n")

            # Quality Score Breakdown
            response_parts.append("### Quality Score Breakdown")
            response_parts.append("```")
            response_parts.append("Base Score:           100%")
            response_parts.append("Empty Tables:         -30% per table (max -30%)")
            response_parts.append("High Null %:          -20% per table")
            response_parts.append("High Duplicate %:     -15% per table")
            response_parts.append("Stale Data:           -10% per table")
            response_parts.append("───────────────────────────────")
            response_parts.append(f"Final Score:          {quality_score}%")
            response_parts.append("```\n")

            if report.get('metrics'):
                all_metrics = report['metrics']
                total_tables = len(all_metrics)
                display_limit = 15  # Show 15 tables per page
                
                response_parts.append(f"### Table Quality Metrics ({total_tables} tables)")
                
                # Sort: tables with issues first, then by table name
                tables_with_issues = [m for m in all_metrics if m['issues'] or m.get('column_issues')]
                healthy_tables = [m for m in all_metrics if not m['issues'] and not m.get('column_issues')]
                sorted_metrics = tables_with_issues + healthy_tables
                
                # Build paginated table content
                if total_tables > display_limit:
                    remaining_pages = (total_tables - 1) // display_limit + 1
                    
                    # Build full markdown table for client-side pagination
                    table_rows = []
                    table_rows.append("| Table | Rows | Cols | PK/FK | Quality Score | Issues |")
                    table_rows.append("|-------|------|------|-------|---------------|--------|")
                    
                    for m in sorted_metrics:
                        issues_str = '; '.join(m['issues'][:2]) if m['issues'] else ''
                        
                        # Add column-specific issues
                        col_issues = m.get('column_issues', {})
                        if col_issues:
                            col_details = []
                            for col_name, col_problems in col_issues.items():
                                col_details.append(f"{col_name}: {', '.join(col_problems[:1])}")
                            col_str = '; '.join(col_details[:2])
                            if issues_str and col_str:
                                issues_str += f" | {col_str}"
                            elif col_str:
                                issues_str = col_str
                        else:
                            col_str = 'None' if not issues_str else ''
                        
                        if not issues_str:
                            issues_str = 'Healthy'
                        
                        # Build PK/FK summary
                        pk_fk_parts = []
                        if m.get('pk_columns'):
                            pk_fk_parts.append(f"PK: {', '.join(m['pk_columns'][:2])}")
                        if m.get('fk_columns'):
                            pk_fk_parts.append(f"FK: {', '.join(m['fk_columns'][:2])}")
                        pk_fk_str = '; '.join(pk_fk_parts) if pk_fk_parts else '-'
                        
                        col_count = m.get('column_count', 0)
                        
                        table_rows.append(f"| {m['table']} | {m['rows']:,} | {col_count} | {pk_fk_str[:25]} | {m['quality_score']}% | {issues_str[:40]} |")
                    
                    table_md = '\n'.join(table_rows)
                    
                    response_parts.append(f"""<div class="table-container" data-page-size="{display_limit}">
<div class="table-header">
<strong>Quality Metrics (showing 1-{min(display_limit, total_tables)} of {total_tables} tables)</strong>
<div class="table-nav">
<button class="nav-btn" onclick="changePage(this, -1)" disabled>&larr;</button>
<span class="page-indicator">Page 1 of {remaining_pages}</span>
<button class="nav-btn" onclick="changePage(this, 1)">&rarr;</button>
</div>
</div>
<div class="table-wrapper">

{table_md}

</div>
<div class="table-footer">Use arrows to navigate pages (15 tables per page)</div>
</div>""")
                else:
                    # Show all tables without pagination if less than 15
                    response_parts.append("| Table | Rows | Cols | PK/FK | Quality Score | Issues |")
                    response_parts.append("|-------|------|------|-------|---------------|--------|")
                    
                    for m in sorted_metrics:
                        issues_str = '; '.join(m['issues'][:2]) if m['issues'] else ''
                        
                        col_issues = m.get('column_issues', {})
                        if col_issues:
                            col_details = []
                            for col_name, col_problems in col_issues.items():
                                col_details.append(f"{col_name}: {', '.join(col_problems[:1])}")
                            col_str = '; '.join(col_details[:2])
                            if issues_str and col_str:
                                issues_str += f" | {col_str}"
                            elif col_str:
                                issues_str = col_str
                        else:
                            col_str = ''
                        
                        if not issues_str:
                            issues_str = 'Healthy'
                        
                        # Build PK/FK summary
                        pk_fk_parts = []
                        if m.get('pk_columns'):
                            pk_fk_parts.append(f"PK: {', '.join(m['pk_columns'][:2])}")
                        if m.get('fk_columns'):
                            pk_fk_parts.append(f"FK: {', '.join(m['fk_columns'][:2])}")
                        pk_fk_str = '; '.join(pk_fk_parts) if pk_fk_parts else '-'
                        
                        col_count = m.get('column_count', 0)
                        
                        response_parts.append(f"| {m['table']} | {m['rows']:,} | {col_count} | {pk_fk_str[:25]} | {m['quality_score']}% | {issues_str[:40]} |")
                    
                    response_parts.append("")

            if report.get('recommendations'):
                response_parts.append("### Recommendations")
                for rec in report['recommendations']:
                    response_parts.append(f"- {rec}")
                response_parts.append("")

        # Handle comprehensive report
        elif check_type == 'comprehensive':
            layers = report.get('layers_checked', 0)
            total_issues = report.get('total_issues', 0)
            summary = report.get('summary', {})

            response_parts.append(f"- **Layers Checked:** {layers}")
            response_parts.append(f"- **Total Issues:** {total_issues}")
            response_parts.append(f"- **Average Quality Score:** {summary.get('avg_quality_score', 0)}%\n")

            response_parts.append("### Layer Summary")
            response_parts.append(f"- Bronze: {summary.get('bronze_tables', 0)} tables")
            response_parts.append(f"- Silver: {summary.get('silver_tables', 0)} tables")
            response_parts.append(f"- Gold: {summary.get('gold_tables', 0)} tables\n")

            # Show individual layer reports
            if report.get('layer_reports'):
                for layer, lr in report['layer_reports'].items():
                    if isinstance(lr, dict) and 'quality_score' in lr:
                        layer_status = lr.get('status', 'unknown')
                        layer_score = lr.get('quality_score', 0)
                        layer_issues = lr.get('issues_found', 0)
                        response_parts.append(f"- **{layer.title()}:** {layer_score}% quality, {layer_issues} issues ({layer_status})")
                response_parts.append("")

        # Error case
        elif status == 'error':
            message = report.get('message', 'Unknown error occurred')
            response_parts.append(f"**Error:** {message}\n")

        # Footer
        if status in ['healthy']:
            response_parts.append("✅ All checks passed. Data quality is good.")
        elif status in ['warning', 'alert']:
            response_parts.append("⚠️ Issues detected. Please review the recommendations above.")
        elif status == 'critical':
            response_parts.append("❌ Critical issues found. Immediate attention required.")

        return "\n".join(response_parts)

    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, provide simple fallback response"""
        state.final_response = f"I encountered an issue processing your request. Here's what I understood:\n\n```sql\n{state.generated_sql or 'No SQL generated'}\n```"
        state.add_trace(self.name, f"Error fallback: {str(error)}")
        return state
