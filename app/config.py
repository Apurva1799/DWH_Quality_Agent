from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 9000
    debug: bool = False
    
    # Database Configuration - Multiple databases
    # Silver DB
    sql_silverdb_server: str = os.getenv("SQL_SILVERDB_SERVER", "afdbsrv.kalyanicorp.com")
    sql_silverdb_name: str = os.getenv("SQL_SILVERDB_NAME", "Silver_DB")
    sql_silverdb_username: str = os.getenv("SQL_SILVERDB_USERNAME", "Silver_Reader")
    sql_silverdb_password: str = os.getenv("SQL_SILVERDB_PASSWORD", "Silver_Reader@123")
    
    # Gold DB
    sql_golddb_server: str = os.getenv("SQL_GOLDDB_SERVER", "afdbsrv.kalyanicorp.com")
    sql_golddb_name: str = os.getenv("SQL_GOLDDB_NAME", "GOLD_DB")
    sql_golddb_username: str = os.getenv("SQL_GOLDDB_USERNAME", "Gold_Reader")
    sql_golddb_password: str = os.getenv("SQL_GOLDDB_PASSWORD", "goldreader@bfl123")
    
    # IoT DB
    sql_iot_server: str = os.getenv("SQL_IOT_SERVER", "sqldbsrv.kalyanicorp.com")
    sql_iot_name: str = os.getenv("SQL_IOT_NAME", "IOTEDGEDB")
    sql_iot_password: str = os.getenv("SQL_IOT_PASSWORD", "dbaccess@123")
    
    # Development DB
    sql_server_dev: str = os.getenv("SQL_SERVER_DEV", "sqldbDEV.kalyanicorp.com")
    sql_database_dev: str = os.getenv("SQL_DATABASE_DEV", "Development")
    
    # Audit DB
    audit_db_name: str = os.getenv("AUDIT_DB_NAME", "audit_logs")
    chatbot_db_username: str = os.getenv("CHATBOT_DB_USERNAME", "AI_Agent_Chatbot")
    chatbot_db_password: str = os.getenv("CHATBOT_DB_PASSWORD", "AI_Agent_Chatbot@2025")
    
    # MSSQL Driver
    sql_server_driver: str = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    
    # LLM Client Configuration - Multiple models
    # Nemotron Models
    llm_nemotron_49b: str = os.getenv("LLM_NEMOTRON_49B", "nvidia/llama-3.3-nemotron-super-49b-v1.5")
    base_url_nemotron_49b: str = os.getenv("BASE_URL_LLM_NEMOTRON_49B", "https://10.7.30.1:8191")
    
    llm_nemotron_253b: str = os.getenv("LLM_NEMOTRON_253B", "nvidia/llama-3.1-nemotron-ultra-253b-v1")
    base_url_nemotron_253b: str = os.getenv("BASE_URL_LLM_NEMOTRON_253B", "https://10.7.30.1:8190")
    
    # Qwen Model
    model_qwen_thinking: str = os.getenv("MODEL_QWEN_THINKING", "/raid/hf/models/Qwen__Qwen3-Next-80B-A3B-Thinking")
    
    # DeepSeek Model
    llm_deepseek_r1_70b: str = os.getenv("LLM_DEEPSEEK_R1_70B", "deepseek-r1:70b")
    base_url_deepseek_r1_70b: str = os.getenv("BASE_URL_LLM_DEEPSEEK_R1_70B", "https://10.7.110.82:9999")
    
    # Llama Model
    llm_llama_70b_instruct: str = os.getenv("LLM_LLAMA_70B_INSTRUCT", "meta/llama-3.3-70b-instruct")
    base_url_llama_70b_instruct: str = os.getenv("BASE_URL_LLM_LLAMA_70B_INSTRUCT", "https://10.7.30.1:8192")
    
    # AI Gateway Configuration
    ai_gateway_url: str = os.getenv("AI_GATEWAY_URL", "https://10.7.30.1:8192")
    streaming_ai_gateway_url: str = os.getenv("STREAMING_AI_GATEWAY_URL", "http://10.7.30.1:8000")
    
    # DocumentDB Configuration
    documentdb_base_url: str = os.getenv("DOCUMENTDB_BASE_URL", "https://10.7.1.200:8002")
    documentdb_username: str = os.getenv("DOCUMENTDB_USERNAME", "AI_Agent_Chatbot")
    documentdb_password: str = os.getenv("DOCUMENTDB_PASSWORD", "AI_Agent_Chatbot@2025")
    documentdb_ssl_verify: bool = True
    
    # Vector DB Configuration
    vectordb_learning_username: str = os.getenv("VECTORDB_LEARNING_USERNAME", "Learning_VectorDB")
    vectordb_learning_password: str = os.getenv("VECTORDB_LEARNING_PASSWORD", "LearningVecDB@2025")
    vector_documents_path_for_learning: str = os.getenv("VECTOR_DOCUMENTS_PATH_FOR_LEARNING", "vector_db_learning_uat_test_4.db")
    
    # Learning DB Configuration
    learning_documentdb_name: str = os.getenv("LEARNING_DOCUMENTDB_NAME", "ai_agent_learning_uat_test_1")
    learning_documentdb_collection: str = os.getenv("LEARNING_DOCUMENTDB_COLLECTION", "ai_agent_learning_data_uat_test_1")
    
    # Namespace Configuration for Learning
    orchestrator_learning_namespace: str = os.getenv("ORCHESTRATOR_LEARNING_NAMESPACE", "orchestrator_few_shot_uat_test_4")
    planner_learning_namespace: str = os.getenv("PLANNER_LEARNING_NAMESPACE", "planner_few_shot_uat_test_4")
    coder_learning_namespace: str = os.getenv("CODER_LEARNING_NAMESPACE", "coder_few_shot_uat_test_4")
    schema_optimizer_learning_namespace: str = os.getenv("SCHEMA_OPTIMIZER_LEARNING_NAMESPACE", "schema_optimizer_few_shot_uat_test_4")
    
    # Customer Satisfaction Projects DB
    documentdb_name_projects: str = os.getenv("DOCUMENTDB_NAME_PROJECTS", "CustomerSatisfaction_Projects_DB")
    documentdb_collection_projects: str = os.getenv("DOCUMENTDB_COLLECTION_PROJECTS", "CustomerSatisfaction_Projects_Collection")
    
    # Memory DB Configuration
    memory_db_name: str = os.getenv("MEMORY_DB_NAME", "User_Memories_CustomerSatisfaction_DB")
    memory_db_collection_name: str = os.getenv("MEMORY_DB_COLLECTION_NAME", "User_Memories_CustomerSatisfaction")
    
    # User Info DB Configuration
    user_info_db_name: str = os.getenv("USER_INFO_DB_NAME", "User_Info_DB_CustomerSatisfaction")
    user_info_db_collection_name: str = os.getenv("USER_INFO_DB_COLLECTION_NAME", "User_Info_Data_CustomerSatisfaction")
    
    # Feedback DB Configuration
    feedback_db_cs_name: str = os.getenv("FEEDBACK_DB_CS_NAME", "User_Feedback_DB_CustomerSatisfaction")
    feedback_db_collection_cs_name: str = os.getenv("FEEDBACK_DB_COLLECTION_CS_NAME", "User_Feedback_Data_CustomerSatisfaction")
    
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
