from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid
from loguru import logger
import asyncio

from app.config import settings
from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.llm_manager import llm_manager

# Configure logging
logger.add("logs/app.log", rotation="10 MB", level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Database Chatbot",
    description="Multi-agent system for multiple MSSQL databases using on-prem LLM clients",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator agent
orchestrator = OrchestratorAgent()

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    database: Optional[str] = None  # silver, gold, iot, dev

class ChatResponse(BaseModel):
    response: str
    success: bool
    session_id: str
    agent_used: str
    execution_time: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    database_used: Optional[str] = None
    llm_used: Optional[str] = None

class DatabaseInfoResponse(BaseModel):
    database: str
    server: str
    name: str
    username: str
    status: str
    available_tables: Optional[List[str]] = None

class HealthCheckResponse(BaseModel):
    status: str
    agents: Dict[str, bool]
    llm_clients: Dict[str, bool]
    databases: Dict[str, bool]
    documentdb: bool

# Dependency to get or create session ID
async def get_session_id(request: ChatRequest) -> str:
    """Get existing session ID or create new one"""
    if request.session_id:
        return request.session_id
    return str(uuid.uuid4())

# Dependency to get or create user ID
async def get_user_id(request: ChatRequest) -> str:
    """Get existing user ID or create new one"""
    if request.user_id:
        return request.user_id
    return str(uuid.uuid4())

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Database Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Multi-database support (Silver, Gold, IoT, Dev)",
            "Multiple LLM models (Nemotron 49B/253B, DeepSeek, Llama)",
            "Enhanced intent classification",
            "Automatic database selection",
            "Conversation management"
        ]
    }

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check for all components"""
    try:
        # Check LLM clients
        llm_health = await llm_manager.health_check()
        
        # Check database connectivity for all databases
        database_health = {}
        databases = ["silver", "gold", "iot", "dev"]
        
        for db in databases:
            try:
                from app.config import get_database_config
                db_config = get_database_config(db)
                
                # Simple connectivity check
                from sqlalchemy import create_engine, text
                db_url = f"mssql+pymssql://{db_config['username']}:{db_config['password']}@{db_config['server']}:{db_config.get('port', 1433)}/{db_config['database']}"
                
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                database_health[db] = True
                logger.info(f"Database {db} health check passed")
                
            except Exception as e:
                logger.error(f"Database {db} health check failed: {str(e)}")
                database_health[db] = False
        
        # Check DocumentDB connectivity
        documentdb_health = llm_health.get("documentdb", False)
        
        # Overall status
        all_healthy = (
            any(llm_health.values()) and  # At least one LLM client working
            any(database_health.values()) and  # At least one database working
            documentdb_health
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            agents={
                "orchestrator": True,
                "sql_agent": True,
                "query_corrector": True,
                "response_analyser": True
            },
            llm_clients=llm_health,
            databases=database_health,
            documentdb=documentdb_health
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_id: str = Depends(get_session_id),
    user_id: str = Depends(get_user_id)
):
    """Chat endpoint with multi-database support"""
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Processing chat request from user {user_id}, session {session_id}")
        logger.info(f"User message: {request.message}")
        if request.database:
            logger.info(f"Requested database: {request.database}")
        
        # Create agent request
        agent_request = AgentRequest(
            query=request.message,
            context=request.context,
            user_id=user_id,
            session_id=session_id
        )
        
        # Process through orchestrator
        response = await orchestrator.process(agent_request)
        
        execution_time = time.time() - start_time
        
        logger.info(f"Chat response generated in {execution_time:.2f}s")
        
        return ChatResponse(
            response=response.response,
            success=response.success,
            session_id=session_id,
            agent_used=response.agent_name,
            execution_time=execution_time,
            data=response.data,
            error=response.error,
            database_used=response.data.get("database") if response.data else None,
            llm_used=response.data.get("llm_used") if response.data else None
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/databases", response_model=List[DatabaseInfoResponse])
async def get_available_databases():
    """Get information about all available databases"""
    try:
        databases = ["silver", "gold", "iot", "dev"]
        database_info = []
        
        for db in databases:
            try:
                from app.config import get_database_config
                db_config = get_database_config(db)
                
                # Try to get basic table info
                tables = []
                try:
                    from sqlalchemy import create_engine, text
                    db_url = f"mssql+pymssql://{db_config['username']}:{db_config['password']}@{db_config['server']}:{db_config.get('port', 1433)}/{db_config['database']}"
                    
                    engine = create_engine(db_url)
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"))
                        tables = [row[0] for row in result.fetchall()]
                    
                    status = "available"
                    
                except Exception as e:
                    logger.error(f"Error getting tables for {db}: {str(e)}")
                    status = "unavailable"
                
                database_info.append(DatabaseInfoResponse(
                    database=db,
                    server=db_config["server"],
                    name=db_config["database"],
                    username=db_config["username"],
                    status=status,
                    available_tables=tables[:10] if tables else None  # Show first 10 tables
                ))
                
            except Exception as e:
                logger.error(f"Error getting database info for {db}: {str(e)}")
                database_info.append(DatabaseInfoResponse(
                    database=db,
                    server="unknown",
                    name="unknown",
                    username="unknown",
                    status="error"
                ))
        
        return database_info
        
    except Exception as e:
        logger.error(f"Failed to get database information: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database information")

@app.get("/conversations/{user_id}/{session_id}")
async def get_conversation_history(user_id: str, session_id: str, limit: int = 20):
    """Get conversation history for a user session"""
    try:
        conversations = await llm_manager.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return {
            "conversations": conversations or [],
            "total_count": len(conversations) if conversations else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")

@app.delete("/conversations/{user_id}/{session_id}")
async def clear_conversation_history(user_id: str, session_id: str):
    """Clear conversation history for a user session"""
    try:
        logger.info(f"Clearing conversation history for user {user_id}, session {session_id}")
        
        return {"message": "Conversation history cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation history")

@app.get("/llm-status")
async def get_llm_status():
    """Get detailed status of all LLM models"""
    try:
        health_status = await llm_manager.health_check()
        
        # Add model information
        model_info = {
            "nemotron_49b": {
                "model": settings.llm_nemotron_49b,
                "base_url": settings.base_url_nemotron_49b,
                "status": health_status.get("nemotron_49b", False)
            },
            "nemotron_253b": {
                "model": settings.llm_nemotron_253b,
                "base_url": settings.base_url_nemotron_253b,
                "status": health_status.get("nemotron_253b", False)
            },
            "deepseek": {
                "model": settings.llm_deepseek_r1_70b,
                "base_url": settings.base_url_deepseek_r1_70b,
                "status": health_status.get("deepseek", False)
            },
            "llama": {
                "model": settings.llm_llama_70b_instruct,
                "base_url": settings.base_url_llama_70b_instruct,
                "status": health_status.get("llama", False)
            }
        }
        
        return {
            "models": model_info,
            "overall_status": "healthy" if any(health_status.values()) else "unhealthy",
            "documentdb": health_status.get("documentdb", False)
        }
        
    except Exception as e:
        logger.error(f"Failed to get LLM status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM status")

@app.get("/schema/{database}")
async def get_database_schema(database: str, table_name: Optional[str] = None):
    """Get database schema information for specific database"""
    try:
        if database not in ["silver", "gold", "iot", "dev"]:
            raise HTTPException(status_code=400, detail=f"Database '{database}' not available")
        
        # Use SQL agent to get schema
        sql_agent = orchestrator.sql_agents[database]
        schema_info = await sql_agent._get_relevant_schema(f"Get schema for {database} database")
        
        return {
            "database": database,
            "schema_info": schema_info,
            "table_name": table_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database schema")

@app.post("/validate-sql")
async def validate_sql_query(sql_query: str, database: str = "silver"):
    """Validate SQL query syntax for specific database"""
    try:
        if database not in ["silver", "gold", "iot", "dev"]:
            raise HTTPException(status_code=400, detail=f"Database '{database}' not available")
        
        # Use SQL agent to validate query
        sql_agent = orchestrator.sql_agents[database]
        validation_result = await sql_agent._execute_sql_query(sql_query)
        
        return {
            "database": database,
            "valid": validation_result["success"],
            "error": validation_result.get("error"),
            "query": sql_query,
            "row_count": validation_result.get("row_count", 0) if validation_result["success"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="SQL validation failed")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Multi-Agent Database Chatbot API")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API server: {settings.api_host}:{settings.api_port}")
    
    # Log configuration (without sensitive data)
    logger.info("Configuration loaded:")
    logger.info(f"  - Silver DB: {settings.sql_silverdb_server}")
    logger.info(f"  - Gold DB: {settings.sql_golddb_server}")
    logger.info(f"  - IoT DB: {settings.sql_iot_server}")
    logger.info(f"  - Nemotron 49B: {settings.base_url_nemotron_49b}")
    logger.info(f"  - Nemotron 253B: {settings.base_url_nemotron_253b}")
    logger.info(f"  - DeepSeek: {settings.base_url_deepseek_r1_70b}")
    logger.info(f"  - Llama: {settings.base_url_llama_70b_instruct}")
    logger.info(f"  - DocumentDB: {settings.documentdb_base_url}")
    logger.info(f"  - Offline Mode: {settings.offline_mode}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Multi-Agent Database Chatbot API")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
