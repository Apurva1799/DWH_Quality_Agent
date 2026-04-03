"""
Intent Classifier Agent
Determines what type of query the user is asking
"""

import json
import re
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState, IntentType
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


class IntentClassifierAgent(BaseAgent):
    """
    Classifies user intent into categories:
    - SQL_QUERY: User wants to query data
    - SCHEMA_QUESTION: User asks about table structure
    - GENERAL_CHAT: General conversation
    - CLARIFICATION_NEEDED: Need more information
    - VISUALIZATION: User wants charts/graphs
    """
    
    def __init__(self):
        super().__init__("IntentClassifier", max_retries=1)
        self.llm = KalyaniLangChainLLM()
        
        self.system_prompt = """You are an intent classifier for a database chatbot.
Analyze the user's query and classify it into one of these categories:

1. SQL_QUERY - User wants to query data from the database
   Examples: "show sales last month", "count customers", "find top products"

2. SCHEMA_QUESTION - User asks about database structure
   Examples: "what tables exist?", "describe customer table", "show columns"

3. GENERAL_CHAT - General conversation or greetings
   Examples: "hello", "how are you?", "what can you do?"

4. CLARIFICATION_NEEDED - Query is ambiguous or incomplete
   Examples: "show data" (which table?), "sales" (time period?), incomplete sentences

5. VISUALIZATION - User explicitly wants charts or graphs
   Examples: "show bar chart of sales", "plot revenue trend", "visualize top products"

Respond ONLY with a JSON object in this exact format:
{
    "intent": "sql_query|schema_question|general_chat|clarification_needed|visualization",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your decision",
    "clarification_question": "question to ask user if clarification_needed, otherwise null"
}"""
    
    async def process(self, state: AgentState) -> AgentState:
        """Classify user intent using LLM"""
        query = state.user_query
        
        # Quick keyword check for obvious cases
        quick_intent = self._quick_check(query)
        if quick_intent:
            state.intent = quick_intent
            state.intent_confidence = 0.8
            state.add_trace(self.name, f"Quick classification: {quick_intent.value}")
            logger.info(f"[{self.name}] Quick match: {quick_intent.value}")
            return state
        
        # Use LLM for classification
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"User Query: {query}\n\nClassify this query:")
        ]
        
        try:
            result = await self.llm._agenerate(messages)
            raw_response = result.generations[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*?\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                classification = json.loads(json_str)
                
                intent_str = classification.get("intent", "general_chat")
                state.intent = IntentType(intent_str)
                state.intent_confidence = classification.get("confidence", 0.5)
                
                if state.intent == IntentType.CLARIFICATION_NEEDED:
                    state.clarification_question = classification.get("clarification_question")
                    state.context_complete = False
                else:
                    state.context_complete = True
                
                state.add_trace(self.name, f"LLM classification: {state.intent.value} (confidence: {state.intent_confidence})")
                logger.info(f"[{self.name}] LLM result: {state.intent.value}")
            else:
                # Fallback to general chat
                state.intent = IntentType.GENERAL_CHAT
                state.intent_confidence = 0.3
                state.add_trace(self.name, "No JSON found, fallback to general_chat")
                
        except Exception as e:
            logger.error(f"[{self.name}] Classification error: {e}")
            state.intent = IntentType.GENERAL_CHAT
            state.intent_confidence = 0.3
            state.add_trace(self.name, f"Error, fallback: {str(e)}")
        
        return state
    
    def _quick_check(self, query: str) -> IntentType:
        """Quick keyword-based classification for common patterns"""
        query_lower = query.lower()
        
        # Schema questions
        schema_patterns = [
            r'what tables',
            r'show tables',
            r'list tables',
            r'describe \w+',
            r'columns in',
            r'schema of',
            r'structure of',
            r'fields in'
        ]
        for pattern in schema_patterns:
            if re.search(pattern, query_lower):
                return IntentType.SCHEMA_QUESTION
        
        # Visualization
        viz_patterns = [
            r'chart|graph|plot|visualize|visualization|bar chart|line chart|pie chart',
            r'show me a (chart|graph)',
            r'display (chart|graph)'
        ]
        for pattern in viz_patterns:
            if re.search(pattern, query_lower):
                return IntentType.VISUALIZATION
        
        # SQL queries - data analysis patterns
        sql_patterns = [
            r'(show|get|find|list|count|sum|average|total|top|bottom)\s+\w+',
            r'(sales|revenue|production|orders|customers|inventory)\s+(last|this|for|in)',
            r'(month|week|year|day|quarter)',
            r'how many',
            r'what is the total',
            r'compare'
        ]
        for pattern in sql_patterns:
            if re.search(pattern, query_lower):
                return IntentType.SQL_QUERY
        
        # General chat
        chat_patterns = [
            r'^(hi|hello|hey|good morning|good afternoon|good evening)',
            r'how are you',
            r'what can you do',
            r'thank you|thanks',
            r'bye|goodbye'
        ]
        for pattern in chat_patterns:
            if re.search(pattern, query_lower):
                return IntentType.GENERAL_CHAT
        
        return None
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Fallback to general chat on error"""
        state.intent = IntentType.GENERAL_CHAT
        state.intent_confidence = 0.3
        state.context_complete = True
        state.add_trace(self.name, f"Error fallback to general_chat: {str(error)}")
        return state
