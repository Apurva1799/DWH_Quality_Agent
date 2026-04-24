from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from config directory (parent of backend)
env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 9000
    debug: bool = False
    
    # Database Configuration - Multiple databases
    # Silver DB
    sql_silverdb_server: str = os.getenv("SQL_SILVERDB_SERVER", "")
    sql_silverdb_name: str = os.getenv("SQL_SILVERDB_NAME", "")
    sql_silverdb_username: str = os.getenv("SQL_SILVERDB_USERNAME", "")
    sql_silverdb_password: str = os.getenv("SQL_SILVERDB_PASSWORD", "")
    
    # Gold DB
    sql_golddb_server: str = os.getenv("SQL_GOLDDB_SERVER", "")
    sql_golddb_name: str = os.getenv("SQL_GOLDDB_NAME", "")
    sql_golddb_username: str = os.getenv("SQL_GOLDDB_USERNAME", "")
    sql_golddb_password: str = os.getenv("SQL_GOLDDB_PASSWORD", "")
    
    # IoT DB
    sql_iot_server: str = os.getenv("SQL_IOT_SERVER", "")
    sql_iot_name: str = os.getenv("SQL_IOT_NAME", "")
    sql_iot_password: str = os.getenv("SQL_IOT_PASSWORD", "")
    
    # Development DB
    sql_server_dev: str = os.getenv("SQL_SERVER_DEV", "")
    sql_database_dev: str = os.getenv("SQL_DATABASE_DEV", "")
    
    # Audit DB
    audit_db_name: str = os.getenv("AUDIT_DB_NAME", "")
    chatbot_db_username: str = os.getenv("CHATBOT_DB_USERNAME", "")
    chatbot_db_password: str = os.getenv("CHATBOT_DB_PASSWORD", "")
    
    # MSSQL Driver
    sql_server_driver: str = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    
    # LLM Client Configuration - Multiple models
    # Nemotron Models
    llm_nemotron_49b: str = os.getenv("LLM_NEMOTRON_49B", "")
    base_url_nemotron_49b: str = os.getenv("BASE_URL_LLM_NEMOTRON_49B", "")
    
    llm_nemotron_253b: str = os.getenv("LLM_NEMOTRON_253B", "")
    base_url_nemotron_253b: str = os.getenv("BASE_URL_LLM_NEMOTRON_253B", "")
    
    # Qwen Model
    model_qwen_thinking: str = os.getenv("MODEL_QWEN_THINKING", "")
    
    # DeepSeek Model
    llm_deepseek_r1_70b: str = os.getenv("LLM_DEEPSEEK_R1_70B", "")
    base_url_deepseek_r1_70b: str = os.getenv("BASE_URL_LLM_DEEPSEEK_R1_70B", "")
    
    # Llama Model
    llm_llama_70b_instruct: str = os.getenv("LLM_LLAMA_70B_INSTRUCT", "")
    base_url_llama_70b_instruct: str = os.getenv("BASE_URL_LLM_LLAMA_70B_INSTRUCT", "")
    
    # AI Gateway Configuration
    ai_gateway_url: str = os.getenv("AI_GATEWAY_URL", "")
    streaming_ai_gateway_url: str = os.getenv("STREAMING_AI_GATEWAY_URL", "")
    
    # DocumentDB Configuration
    documentdb_base_url: str = os.getenv("DOCUMENTDB_BASE_URL", "")
    documentdb_username: str = os.getenv("DOCUMENTDB_USERNAME", "")
    documentdb_password: str = os.getenv("DOCUMENTDB_PASSWORD", "")
    documentdb_ssl_verify: bool = True
    
    # Vector DB Configuration
    vectordb_learning_username: str = os.getenv("VECTORDB_LEARNING_USERNAME", "")
    vectordb_learning_password: str = os.getenv("VECTORDB_LEARNING_PASSWORD", "")
    vector_documents_path_for_learning: str = os.getenv("VECTOR_DOCUMENTS_PATH_FOR_LEARNING", "")
    
    # Learning DB Configuration
    learning_documentdb_name: str = os.getenv("LEARNING_DOCUMENTDB_NAME", "")
    learning_documentdb_collection: str = os.getenv("LEARNING_DOCUMENTDB_COLLECTION", "")
    
    # Namespace Configuration for Learning
    orchestrator_learning_namespace: str = os.getenv("ORCHESTRATOR_LEARNING_NAMESPACE", "")
    planner_learning_namespace: str = os.getenv("PLANNER_LEARNING_NAMESPACE", "")
    coder_learning_namespace: str = os.getenv("CODER_LEARNING_NAMESPACE", "")
    schema_optimizer_learning_namespace: str = os.getenv("SCHEMA_OPTIMIZER_LEARNING_NAMESPACE", "")
    
    # Customer Satisfaction Projects DB
    documentdb_name_projects: str = os.getenv("DOCUMENTDB_NAME_PROJECTS", "")
    documentdb_collection_projects: str = os.getenv("DOCUMENTDB_COLLECTION_PROJECTS", "")
    
    # Memory DB Configuration
    memory_db_name: str = os.getenv("MEMORY_DB_NAME", "")
    memory_db_collection_name: str = os.getenv("MEMORY_DB_COLLECTION_NAME", "")
    
    # User Info DB Configuration
    user_info_db_name: str = os.getenv("USER_INFO_DB_NAME", "")
    user_info_db_collection_name: str = os.getenv("USER_INFO_DB_COLLECTION_NAME", "")
    
    # Feedback DB Configuration
    feedback_db_cs_name: str = os.getenv("FEEDBACK_DB_CS_NAME", "")
    feedback_db_collection_cs_name: str = os.getenv("FEEDBACK_DB_COLLECTION_CS_NAME", "")
    
    # Session Configuration
    session_timeout_hours: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "2"))
    cleanup_interval_minutes: int = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "5"))
    max_reconnect_attempts: int = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "5"))
    
    # Agent Configuration
    max_sql_execution_time: int = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))
    max_tokens: int = 4000
    temperature: float = 0.1
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    service_name: str = os.getenv("SERVICE_NAME", "customer-satisfaction")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Conversation Management
    max_conversation_history: int = 20
    session_timeout: int = 3600  # 1 hour
    
    # Offline Mode
    offline_mode: bool = os.getenv("OFFLINE_MODE", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create global settings instance
settings = Settings()

def get_database_config(db_type: str = "silver"):
    """Get database configuration based on type"""
    if db_type.lower() == "gold":
        return {
            "server": settings.sql_golddb_server,
            "database": settings.sql_golddb_name,
            "username": settings.sql_golddb_username,
            "password": settings.sql_golddb_password
        }
    elif db_type.lower() == "iot":
        return {
            "server": settings.sql_iot_server,
            "database": settings.sql_iot_name,
            "username": "IOTEDGEDB_USER",  # Default username for IoT
            "password": settings.sql_iot_password
        }
    elif db_type.lower() == "dev":
        return {
            "server": settings.sql_server_dev,
            "database": settings.sql_database_dev,
            "username": "dev_user",  # Default dev username
            "password": "dev_password"  # Default dev password
        }
    else:  # Default to silver
        return {
            "server": settings.sql_silverdb_server,
            "database": settings.sql_silverdb_name,
            "username": settings.sql_silverdb_username,
            "password": settings.sql_silverdb_password
        }

def get_llm_config(model_type: str = "nemotron"):
    """Get LLM configuration based on model type"""
    if model_type.lower() == "nemotron_253b":
        return {
            "model": settings.llm_nemotron_253b,
            "base_url": settings.base_url_nemotron_253b,
            "verify_ssl": False
        }
    elif model_type.lower() == "deepseek":
        return {
            "model": settings.llm_deepseek_r1_70b,
            "base_url": settings.base_url_deepseek_r1_70b,
            "verify_ssl": False
        }
    elif model_type.lower() == "llama":
        return {
            "model": settings.llm_llama_70b_instruct,
            "base_url": settings.base_url_llama_70b_instruct,
            "verify_ssl": False
        }
    else:  # Default to nemotron 49b
        return {
            "model": settings.llm_nemotron_49b,
            "base_url": settings.base_url_nemotron_49b,
            "verify_ssl": False
        }
