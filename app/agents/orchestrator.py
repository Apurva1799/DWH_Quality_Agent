from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.agents.sql_agent import SQLAgent
from app.agents.query_corrector import QueryCorrectorAgent
from app.agents.response_analyser import ResponseAnalyserAgent
from app.llm_manager import llm_manager
from app.config import get_database_config
from loguru import logger
import asyncio

class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent supporting multiple databases and LLM models"""
    
    def __init__(self):
        super().__init__("Orchestrator Agent")
        self.sql_agents = {
            "silver": SQLAgent("silver"),
            "gold": SQLAgent("gold"),
            "iot": SQLAgent("iot"),
            "dev": SQLAgent("dev")
        }
        self.query_corrector = QueryCorrectorAgent()
        self.response_analyser = ResponseAnalyserAgent()
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Orchestration with multi-database support"""
        try:
            # Get conversation history
            conversation_history = await self._get_conversation_history(request)
            
            # Enhanced intent classification
            intent = await self._classify_intent_enhanced(request.query, conversation_history)
            
            # Route to appropriate workflow
            if intent["type"] == "sql_query":
                return await self._handle_enhanced_sql_workflow(request, conversation_history, intent)
            elif intent["type"] == "database_selection":
                return await self._handle_database_selection(request, intent)
            elif intent["type"] == "general_question":
                return await self._handle_general_question(request, conversation_history)
            elif intent["type"] == "clarification_needed":
                return await self._handle_clarification(request, intent["clarification"])
            else:
                return await self._handle_default_workflow(request, conversation_history)
                
        except Exception as e:
            logger.error(f"Orchestrator Agent processing error: {str(e)}")
            return AgentResponse(
                success=False,
                response="Orchestrator Agent processing failed",
                error=str(e),
                agent_name=self.name
            )
    
    async def _get_conversation_history(self, request: AgentRequest) -> List[Dict[str, Any]]:
        """Get conversation history from DocumentDB"""
        try:
            if not request.user_id or not request.session_id:
                return []
            
            history = await llm_manager.get_conversation_history(
                user_id=request.user_id,
                session_id=request.session_id,
                limit=10  # Get last 10 conversations for better context
            )
            
            return history or []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def _classify_intent_enhanced(self, query: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced intent classification with database detection"""
        try:
            # Build enhanced intent classification prompt
            prompt = self._build_enhanced_intent_prompt(query, conversation_history)
            
            # Use Nemotron 253B for best intent classification if available
            health_status = await llm_manager.health_check()
            
            if health_status.get("nemotron_253b", False):
                result = await llm_manager.generate_with_nemotron_253b(
                    query=prompt,
                    temperature=0.1
                )
            elif health_status.get("nemotron_49b", False):
                result = await llm_manager.generate_with_nemotron_49b(
                    query=prompt,
                    temperature=0.1
                )
            else:
                result = await llm_manager.generate_with_fallback(
                    query=prompt,
                    primary="deepseek",
                    fallback="llama",
                    temperature=0.1
                )
            
            if not result["success"]:
                logger.error(f"Intent classification error: {result.get('error')}")
                return {"type": "general_question", "confidence": 0.5}
            
            # Parse enhanced intent response
            intent = self._parse_enhanced_intent_response(result["response"])
            
            logger.info(f"Enhanced intent classification: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying enhanced intent: {str(e)}")
            return {"type": "general_question", "confidence": 0.5}
    
    def _build_enhanced_intent_prompt(self, query: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Build enhanced prompt for intent classification"""
        
        prompt = f"""You are an advanced intent classifier for a multi-database customer satisfaction chatbot. Classify the user's query into one of these categories:

1. "sql_query" - User wants to query or analyze data from the database
2. "database_selection" - User wants to specify which database to use (silver, gold, iot, dev)
3. "general_question" - User asks a general question not requiring database queries
4. "clarification_needed" - Query is unclear and needs clarification

Available Databases:
- Silver DB: Customer satisfaction data, feedback, projects
- Gold DB: Production customer data, analytics, reports
- IoT DB: Sensor data, device information, real-time metrics
- Dev DB: Development and testing data

User Query: "{query}"

Instructions:
1. Analyze the query for database-related keywords (SELECT, INSERT, UPDATE, DELETE, tables, columns, data, etc.)
2. Check if user specifies a particular database (silver, gold, iot, dev)
3. Consider the conversation context from previous interactions
4. Return the classification in JSON format
5. If clarification is needed, specify what clarification is required
6. For database selection, identify which database the user wants to use

Response format:
{{"type": "category", "confidence": 0.95, "clarification": "what needs clarification if applicable", "database": "silver|gold|iot|dev|null"}}

Examples:
- "Show me customer satisfaction from silver database" -> {{"type": "sql_query", "confidence": 0.9, "database": "silver"}}
- "Use the gold database to show top customers" -> {{"type": "sql_query", "confidence": 0.9, "database": "gold"}}
- "Switch to IoT database" -> {{"type": "database_selection", "confidence": 0.8, "database": "iot"}}
- "What is the weather today?" -> {{"type": "general_question", "confidence": 0.8, "database": null}}
- "Can you help me?" -> {{"type": "clarification_needed", "confidence": 0.7, "clarification": "What specific task would you like help with?", "database": null}}

"""
        
        # Add conversation context if available
        if conversation_history:
            prompt += "\nConversation Context:\n"
            for i, conv in enumerate(conversation_history[-5:]):  # Last 5 conversations
                prompt += f"Q{i+1}: {conv.get('message', '')}\n"
                prompt += f"A{i+1}: {conv.get('response', '')}\n"
        
        prompt += "\nClassification:\n"
        
        return prompt
    
    def _parse_enhanced_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse enhanced intent classification response"""
        try:
            import json
            
            response = response.strip()
            
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                json_str = response[start_idx:end_idx]
                
                intent_data = json.loads(json_str)
                
                # Validate required fields
                intent_type = intent_data.get("type", "general_question")
                confidence = intent_data.get("confidence", 0.5)
                clarification = intent_data.get("clarification")
                database = intent_data.get("database")
                
                # Ensure valid intent type
                valid_types = ["sql_query", "general_question", "clarification_needed", "database_selection"]
                if intent_type not in valid_types:
                    intent_type = "general_question"
                
                # Validate database
                valid_databases = ["silver", "gold", "iot", "dev", None]
                if database not in valid_databases:
                    database = None
                
                return {
                    "type": intent_type,
                    "confidence": min(max(confidence, 0.0), 1.0),
                    "clarification": clarification,
                    "database": database
                }
            
            # Fallback: keyword-based classification
            response_lower = response.lower()
            
            # Database detection
            database = None
            if "silver" in response_lower:
                database = "silver"
            elif "gold" in response_lower:
                database = "gold"
            elif "iot" in response_lower:
                database = "iot"
            elif "dev" in response_lower:
                database = "dev"
            
            # Intent detection
            if any(keyword in response_lower for keyword in ["sql_query", "database", "data"]):
                return {"type": "sql_query", "confidence": 0.7, "database": database}
            elif any(keyword in response_lower for keyword in ["clarification", "unclear", "help"]):
                return {"type": "clarification_needed", "confidence": 0.6, "clarification": "Please provide more details about your request", "database": None}
            elif database:
                return {"type": "database_selection", "confidence": 0.8, "database": database}
            else:
                return {"type": "general_question", "confidence": 0.5, "database": None}
                
        except Exception as e:
            logger.error(f"Error parsing enhanced intent response: {str(e)}")
            return {"type": "general_question", "confidence": 0.5, "database": None}
    
    async def _handle_enhanced_sql_workflow(self, request: AgentRequest, conversation_history: List[Dict[str, Any]], intent: Dict[str, Any]) -> AgentResponse:
        """Handle SQL workflow with database selection"""
        try:
            # Determine which database to use
            target_database = intent.get("database", "silver")  # Default to silver
            
            if target_database not in self.sql_agents:
                target_database = "silver"
            
            logger.info(f"Starting SQL workflow for {target_database} database")
            
            # Step 1: Generate SQL query with appropriate agent
            sql_agent = self.sql_agents[target_database]
            sql_request = AgentRequest(
                query=request.query,
                context={
                    "conversation_history": conversation_history,
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "database": target_database
                },
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            sql_response = await sql_agent.process(sql_request)
            
            if not sql_response.success:
                return AgentResponse(
                    success=False,
                    response=f"SQL generation failed for {target_database} database: {sql_response.error}",
                    error="SQL workflow failed at generation step",
                    agent_name=self.name,
                    data={"workflow_step": "sql_generation", "database": target_database, "error": sql_response.error}
                )
            
            # Step 2: Validate and correct SQL query
            correction_request = AgentRequest(
                query=sql_response.response,
                context={
                    "sql_query": sql_response.data.get("sql_query"),
                    "original_query": request.query,
                    "database": target_database
                },
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            correction_response = await self.query_corrector.process(correction_request)
            
            # Use corrected query if available
            final_sql_query = correction_response.data.get("corrected_query") if correction_response.success else sql_response.data.get("sql_query")
            
            # Step 3: Execute the final SQL query (if not already executed)
            if not sql_response.data.get("result") or correction_response.data.get("corrections_made"):
                execution_result = await sql_agent._execute_sql_query(final_sql_query)
                
                if not execution_result["success"]:
                    return AgentResponse(
                        success=False,
                        response=f"SQL execution failed on {target_database} database: {execution_result['error']}",
                        error="SQL workflow failed at execution step",
                        agent_name=self.name,
                        data={"workflow_step": "sql_execution", "database": target_database, "sql_query": final_sql_query, "error": execution_result["error"]}
                    )
            else:
                execution_result = sql_response.data.get("result")
            
            # Step 4: Analyze and format results
            analysis_request = AgentRequest(
                query=request.query,
                context={
                    "result": execution_result,
                    "sql_query": final_sql_query,
                    "corrections_made": correction_response.data.get("corrections_made", False),
                    "database": target_database
                },
                user_id=request.user_id,
                session_id=request.session_id,
                data={"result": execution_result}
            )
            
            analysis_response = await self.response_analyser.process(analysis_request)
            
            # Combine all workflow information
            workflow_summary = {
                "original_query": request.query,
                "sql_query": final_sql_query,
                "corrections_made": correction_response.data.get("corrections_made", False),
                "execution_result": execution_result,
                "analysis": analysis_response.data.get("analysis"),
                "workflow_steps": ["sql_generation", "query_correction", "sql_execution", "response_analysis"],
                "database": target_database,
                "llm_used": sql_response.data.get("llm_used")
            }
            
            return AgentResponse(
                success=analysis_response.success,
                response=analysis_response.response,
                agent_name=self.name,
                data=workflow_summary,
                metadata={
                    "workflow_type": "sql_query",
                    "database": target_database,
                    "steps_completed": len(workflow_summary["workflow_steps"])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in SQL workflow: {str(e)}")
            return AgentResponse(
                success=False,
                response="SQL workflow execution failed",
                error=str(e),
                agent_name=self.name
            )
    
    async def _handle_database_selection(self, request: AgentRequest, intent: Dict[str, Any]) -> AgentResponse:
        """Handle database selection requests"""
        try:
            target_database = intent.get("database", "silver")
            
            if target_database not in self.sql_agents:
                return AgentResponse(
                    success=False,
                    response=f"Database '{target_database}' is not available. Available databases: silver, gold, iot, dev",
                    error="Invalid database selection",
                    agent_name=self.name
                )
            
            # Get database info
            db_config = get_database_config(target_database)
            
            response_text = f"Database switched to **{target_database.upper()}** database.\n\n"
            response_text += f"Database Configuration:\n"
            response_text += f"- Server: {db_config['server']}\n"
            response_text += f"- Database: {db_config['database']}\n"
            response_text += f"- Username: {db_config['username']}\n\n"
            response_text += f"You can now query the {target_database} database. What would you like to know?"
            
            return AgentResponse(
                success=True,
                response=response_text,
                agent_name=self.name,
                data={
                    "workflow_type": "database_selection",
                    "selected_database": target_database,
                    "database_config": db_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling database selection: {str(e)}")
            return AgentResponse(
                success=False,
                response="Database selection failed",
                error=str(e),
                agent_name=self.name
            )
    
    async def _handle_general_question(self, request: AgentRequest, conversation_history: List[Dict[str, Any]]) -> AgentResponse:
        """Handle general questions with enhanced LLM selection"""
        try:
            # Build conversation context
            context_text = ""
            if conversation_history:
                context_text = "Previous conversation:\n"
                for conv in conversation_history[-5:]:
                    context_text += f"Q: {conv.get('message', '')}\n"
                    context_text += f"A: {conv.get('response', '')}\n"
            
            # Build enhanced prompt for general question
            prompt = f"""You are a helpful customer satisfaction database assistant. Answer the user's general question.

Available Databases:
- Silver DB: Customer satisfaction data, feedback, projects
- Gold DB: Production customer data, analytics, reports  
- IoT DB: Sensor data, device information, real-time metrics
- Dev DB: Development and testing data

{context_text}

User Question: {request.query}

Instructions:
1. Provide a helpful and accurate response
2. If the question seems related to database queries, suggest how you could help with data analysis
3. If user asks about specific data, mention which database might contain that information
4. Keep the response concise and user-friendly
5. Do not make up information about specific database content
6. Offer to help with database queries if relevant

Response:"""
            
            # Use fallback mechanism for general questions
            result = await llm_manager.generate_with_fallback(
                query=prompt,
                primary="nemotron_49b",
                fallback="deepseek",
                temperature=0.3
            )
            
            if not result["success"]:
                return AgentResponse(
                    success=False,
                    response="I'm having trouble processing your question right now.",
                    error=result.get("error"),
                    agent_name=self.name
                )
            
            # Store conversation
            await llm_manager.store_conversation(
                user_id=request.user_id,
                session_id=request.session_id,
                message=request.query,
                response=result["response"],
                metadata={"agent": self.name, "workflow_type": "general_question"}
            )
            
            return AgentResponse(
                success=True,
                response=result["response"],
                agent_name=self.name,
                data={"workflow_type": "general_question", "llm_used": result.get("client_used")}
            )
            
        except Exception as e:
            logger.error(f"Error handling general question: {str(e)}")
            return AgentResponse(
                success=False,
                response="I'm having trouble processing your question. Please try again.",
                error=str(e),
                agent_name=self.name
            )
    
    async def _handle_clarification(self, request: AgentRequest, clarification: str) -> AgentResponse:
        """Handle clarification needed scenario"""
        try:
            clarification_text = clarification or "Could you please provide more details about what you'd like to know or do?"
            
            return AgentResponse(
                success=True,
                response=clarification_text,
                agent_name=self.name,
                data={"workflow_type": "clarification_needed", "clarification": clarification}
            )
            
        except Exception as e:
            logger.error(f"Error handling clarification: {str(e)}")
            return AgentResponse(
                success=False,
                response="I need more information to help you better.",
                error=str(e),
                agent_name=self.name
            )
    
    async def _handle_default_workflow(self, request: AgentRequest, conversation_history: List[Dict[str, Any]]) -> AgentResponse:
        """Handle default workflow (fallback to SQL workflow)"""
        try:
            logger.info("Using default workflow - falling back to SQL workflow")
            return await self._handle_enhanced_sql_workflow(request, conversation_history, {"type": "sql_query", "database": "silver"})
            
        except Exception as e:
            logger.error(f"Error in default workflow: {str(e)}")
            return AgentResponse(
                success=False,
                response="I'm having trouble processing your request. Please try rephrasing your question.",
                error=str(e),
                agent_name=self.name
            )
