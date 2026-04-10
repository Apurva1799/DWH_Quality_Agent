"""
Agent Orchestrator
Coordinates the execution of all agents in the chain
"""

import asyncio
import time
from typing import Dict, Any, Optional
from loguru import logger

from app.agents.chain_of_agents.state import AgentState, IntentType
from app.agents.chain_of_agents.intent_classifier import IntentClassifierAgent
from app.agents.chain_of_agents.context_validator import ContextValidatorAgent
from app.agents.chain_of_agents.schema_selector import SchemaSelectorAgent
from app.agents.chain_of_agents.query_generator import QueryGeneratorAgent
from app.agents.chain_of_agents.database_health import DatabaseHealthAgent
from app.agents.chain_of_agents.query_executor import QueryExecutorAgent
from app.agents.chain_of_agents.sql_corrector import SQLQueryCorrectorAgent
from app.agents.chain_of_agents.response_formatter import ResponseFormatterAgent
from app.agents.chain_of_agents.visualizer_decision import VisualizerDecisionAgent
from app.agents.chain_of_agents.data_quality_agent import DataQualityAgent


class AgentOrchestrator:
    """
    Orchestrates the chain of agents for processing database queries.
    
    Flow:
    1. Intent Classifier -> 2. Context Validator -> 3. Schema Selector
    4. Query Generator -> 5. Query Executor -> 6. Visualizer Decision
    7. Response Formatter
    """
    
    def __init__(self):
        logger.info("Initializing AgentOrchestrator")
        
        # Initialize all agents
        self.intent_classifier = IntentClassifierAgent()
        self.context_validator = ContextValidatorAgent()
        self.schema_selector = SchemaSelectorAgent()
        self.query_generator = QueryGeneratorAgent()
        self.db_health = DatabaseHealthAgent()  # NEW: Check DB first
        self.query_executor = QueryExecutorAgent()
        self.sql_corrector = SQLQueryCorrectorAgent()
        self.visualizer_decision = VisualizerDecisionAgent()
        self.response_formatter = ResponseFormatterAgent()
        self.data_quality = DataQualityAgent()  # NEW: Data Quality monitoring

        logger.info("All agents initialized")
    
    async def process_query(self, query: str, session_id: str = "", 
                           conversation_history: list = None) -> AgentState:
        """
        Main entry point for processing a user query through the agent chain.
        
        Args:
            query: User's natural language query
            session_id: Session identifier for tracking
            conversation_history: Previous messages in conversation
            
        Returns:
            AgentState containing final response and trace
        """
        start_time = time.time()
        
        # Initialize state
        state = AgentState(
            user_query=query,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
        
        logger.info(f"="*60)
        logger.info(f"Processing query: {query}")
        logger.info(f"="*60)
        
        try:
            # Step 0: Database Health Check (NEW - check first!)
            state = await self.db_health.run(state)
            db_is_healthy = state.response_data.get('db_healthy', False)

            # Step 1: Intent Classification
            state = await self.intent_classifier.run(state)

            # Check if this is a data quality monitoring request
            if state.intent == IntentType.DATA_QUALITY:
                logger.info("Data quality monitoring request detected")
                state = await self.data_quality.run(state)
                state = await self.response_formatter.run(state)
                return state

            # If clarification needed, skip to response formatting
            if state.intent == IntentType.CLARIFICATION_NEEDED:
                logger.info("Clarification needed, skipping to response")
                state = await self.response_formatter.run(state)
                return state
            
            # Step 2: Context Validation
            state = await self.context_validator.run(state)
            
            # Step 3: Schema Selection (run even with incomplete context to find tables)
            state = await self.schema_selector.run(state)
            
            if not state.selected_tables:
                logger.warning("No tables selected, using fallback")
            
            # If context is incomplete, show relevant tables and ask for clarification
            if not state.context_complete:
                logger.info("Context incomplete - showing relevant tables and asking for clarification")
                state = await self.response_formatter.run(state)
                return state
            
            # For general chat and schema questions, skip SQL generation
            if state.intent in [IntentType.GENERAL_CHAT, IntentType.SCHEMA_QUESTION]:
                state = await self.response_formatter.run(state)
                return state
            
            # Step 4: Query Generation (always generate SQL, even if DB is down)
            state = await self.query_generator.run(state)
            
            if not state.sql_valid:
                logger.warning("SQL generation failed")
                # Continue to formatter to show what we have
                state = await self.response_formatter.run(state)
                return state
            
            # If DB is down, skip execution but still show generated SQL
            if not db_is_healthy:
                logger.warning("Database is down - skipping execution, showing generated SQL")
                state.add_trace("Orchestrator", "DB unhealthy - SQL generated but not executed")
                state.response_data['db_down'] = True
                state = await self.response_formatter.run(state)
                return state
            
            # Step 5: Query Execution (only if DB is healthy)
            state = await self.query_executor.run(state)
            
            # Step 6: SQL Corrector (if execution failed)
            if not state.execution_success and state.execution_error:
                logger.info(f"Query execution failed with error: {state.execution_error[:100]}")
                state = await self.sql_corrector.run(state)
                
                # If correction was made, retry execution
                if state.sql_valid and not state.execution_error:
                    logger.info("SQL corrected, retrying execution")
                    state = await self.query_executor.run(state)
                else:
                    logger.warning("SQL correction failed or no changes made")
            
            # Step 7: Visualizer Decision
            state = await self.visualizer_decision.run(state)
            
            # Step 7: Response Formatting
            state = await self.response_formatter.run(state)
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"="*60)
            logger.info(f"Query processed in {elapsed:.2f}ms")
            logger.info(f"Intent: {state.intent.value if state.intent else 'None'}")
            logger.info(f"Tables: {len(state.selected_tables)}")
            logger.info(f"SQL: {state.generated_sql[:50]}...")
            logger.info(f"Results: {state.row_count} rows")
            logger.info(f"Viz: {state.visualization_type.value}")
            logger.info(f"="*60)
            
            return state
            
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            state.add_trace("Orchestrator", f"Fatal error: {str(e)}")
            state.final_response = f"I encountered an error processing your request: {e}"
            return state
    
    def get_trace(self, state: AgentState) -> str:
        """Get formatted agent trace for debugging"""
        lines = ["Agent Execution Trace:", "="*50]
        for trace in state.agent_trace:
            lines.append(f"  {trace}")
        lines.append(f"\nTotal time: {state.processing_time_ms:.2f}ms")
        return "\n".join(lines)
    
    def get_state_summary(self, state: AgentState) -> Dict[str, Any]:
        """Get summary of state for API response"""
        return {
            "intent": state.intent.value if state.intent else None,
            "intent_confidence": state.intent_confidence,
            "selected_tables": state.selected_tables,
            "generated_sql": state.generated_sql,
            "execution_success": state.execution_success,
            "row_count": state.row_count,
            "visualization_needed": state.visualization_needed,
            "visualization_type": state.visualization_type.value,
            "processing_time_ms": state.processing_time_ms,
            "agent_trace": state.agent_trace
        }
