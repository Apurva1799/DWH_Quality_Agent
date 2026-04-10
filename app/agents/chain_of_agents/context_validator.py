"""
Context Validator Agent
Validates if we have enough information to proceed with the query
"""

import re
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState, IntentType


class ContextValidatorAgent(BaseAgent):
    """
    Validates whether the context is complete enough to proceed.
    If not, identifies what's missing and asks for clarification.
    """
    
    def __init__(self):
        super().__init__("ContextValidator", max_retries=1)
    
    async def process(self, state: AgentState) -> AgentState:
        """Validate context completeness"""
        intent = state.intent
        query = state.user_query.lower()
        
        # Skip validation for general chat and schema questions
        if intent in [IntentType.GENERAL_CHAT, IntentType.SCHEMA_QUESTION]:
            state.context_complete = True
            state.add_trace(self.name, f"Skipped validation for {intent.value}")
            return state
        
        # If intent classifier already flagged as clarification needed
        if intent == IntentType.CLARIFICATION_NEEDED:
            if not state.clarification_question:
                state.clarification_question = "Could you provide more details about what you're looking for?"
            state.context_complete = False
            state.add_trace(self.name, "Clarification flagged by classifier")
            return state
        
        # Check for common missing context in SQL queries
        missing_elements = []
        
        # Check for time period ambiguity
        time_indicators = ['last', 'this', 'current', 'recent', 'month', 'week', 'year', 'day', 'quarter']
        has_time = any(ind in query for ind in time_indicators)
        
        # Check for table references
        from_patterns = [
            r'from\s+(\w+)',
            r'in\s+(?:the\s+)?(\w+)\s+(?:table|db|database)',
            r'table\s+(\w+)'
        ]
        has_table_ref = any(re.search(p, query) for p in from_patterns)
        
        # Check for vague terms
        vague_terms = ['data', 'information', 'stuff', 'things', 'records']
        has_vague = any(term in query for term in vague_terms)
        
        # Check for clear domain keywords that can be resolved by SchemaSelector
        domain_keywords = ['production', 'sales', 'inventory', 'forging', 'machining', 'oee', 'employee']
        has_domain = any(kw in query for kw in domain_keywords)
        
        # Validation rules
        # If query has domain keyword AND time period, allow it (SchemaSelector will find tables)
        if has_domain and has_time:
            state.context_complete = True
            state.add_trace(self.name, "Context complete - domain + time specified")
            logger.info(f"[{self.name}] Context complete (domain+time)")
            return state
        
        # If query has explicit table reference, allow it
        if has_table_ref:
            state.context_complete = True
            state.add_trace(self.name, "Context complete - table specified")
            logger.info(f"[{self.name}] Context complete (table ref)")
            return state
        
        # Otherwise, check for missing elements
        if has_vague and not has_table_ref:
            missing_elements.append("which table to query")
        
        if 'production' in query and not has_time:
            missing_elements.append("time period for production data (e.g., 'last month', 'this week')")
        
        # Note: sales queries no longer require explicit time period - defaults to last year
        
        if 'top' in query or 'bottom' in query:
            if not re.search(r'(top|bottom)\s+\d+', query):
                missing_elements.append("number of items (e.g., 'top 10', 'bottom 5')")
        
        # If we have missing elements, ask for clarification
        if missing_elements:
            state.context_complete = False
            state.missing_context = missing_elements
            state.clarification_question = self._build_clarification(missing_elements, query)
            state.add_trace(self.name, f"Missing context: {missing_elements}")
            logger.info(f"[{self.name}] Missing: {missing_elements}")
        else:
            state.context_complete = True
            state.add_trace(self.name, "Context validated as complete")
            logger.info(f"[{self.name}] Context complete")
        
        return state
    
    def _build_clarification(self, missing: list, query: str) -> str:
        """Build a natural clarification question"""
        if len(missing) == 1:
            return f"I need a bit more information to help you. Could you specify {missing[0]}?"
        else:
            items = ", ".join(missing[:-1]) + f" and {missing[-1]}"
            return f"To answer your question accurately, I need to know: {items}. Could you provide these details?"
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, assume context is incomplete and ask for clarification"""
        state.context_complete = False
        state.clarification_question = "I'm not sure I understand completely. Could you rephrase your question with more specific details?"
        state.add_trace(self.name, f"Error in validation: {str(error)}")
        return state
