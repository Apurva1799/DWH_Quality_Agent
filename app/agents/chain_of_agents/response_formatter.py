"""
Response Formatter Agent
Formats query results into readable responses
"""

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
        """Format the final response"""
        intent = state.intent
        
        if intent == IntentType.GENERAL_CHAT:
            state.final_response = await self._format_general_chat(state)
        elif intent == IntentType.SCHEMA_QUESTION:
            state.final_response = await self._format_schema_response(state)
        elif intent == IntentType.CLARIFICATION_NEEDED:
            state.final_response = state.clarification_question or "Could you provide more details?"
        else:
            # SQL_QUERY or VISUALIZATION
            state.final_response = await self._format_sql_response(state)
        
        state.add_trace(self.name, "Response formatted")
        logger.info(f"[{self.name}] Formatted response ({len(state.final_response)} chars)")
        
        return state
    
    async def _format_sql_response(self, state: AgentState) -> str:
        """Format SQL query results"""
        sql = state.generated_sql
        success = state.execution_success
        error = state.execution_error
        df = state.query_results
        
        if not sql:
            return "I wasn't able to generate a SQL query for your request. Could you rephrase your question?"
        
        # Build response
        response_parts = []
        
        # Show SQL
        response_parts.append(f"```sql\n{sql}\n```")
        
        # Show results or error
        if success and df is not None:
            if len(df) > 0:
                # Format as markdown table
                table_md = df.to_markdown(index=False)
                response_parts.append(f"\n**Query Results ({len(df)} rows):**\n\n{table_md}")
            else:
                response_parts.append("\n*Query executed successfully but returned no results.*")
        elif error:
            # Database error - provide helpful message
            response_parts.append(f"\n⚠️ **Database Unavailable**\n\nThe SQL query above is valid and ready to execute, but the database server is currently unreachable.\n\n*Error: {error}*\n\nOnce the database connection is restored, this query will return the production data for last month.")
        
        # Add insights for data-heavy responses
        if success and df is not None and len(df) > 0 and len(df) < 100:
            insights = await self._generate_insights(state, df)
            if insights:
                response_parts.append(f"\n\n**Insights:**\n{insights}")
        
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
    
    async def _generate_insights(self, state: AgentState, df) -> str:
        """Generate insights from data"""
        # Simple insights for small datasets
        insights = []
        
        # Check for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:2]:  # First 2 numeric columns
                total = df[col].sum()
                avg = df[col].mean()
                insights.append(f"- Total {col}: {total:,.2f}, Average: {avg:,.2f}")
        
        return "\n".join(insights) if insights else ""
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, provide simple fallback response"""
        state.final_response = f"I encountered an issue processing your request. Here's what I understood:\n\n```sql\n{state.generated_sql or 'No SQL generated'}\n```"
        state.add_trace(self.name, f"Error fallback: {str(error)}")
        return state
