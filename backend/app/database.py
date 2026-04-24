from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import List, Dict, Any
import pandas as pd
import urllib.parse
from loguru import logger
from app.config import settings

# Database engine configuration (using Gold DB as default)
# URL-encode credentials to handle special characters like @ in passwords
_encoded_username = urllib.parse.quote_plus(settings.sql_golddb_username)
_encoded_password = urllib.parse.quote_plus(settings.sql_golddb_password)
DATABASE_URL = f"mssql+pymssql://{_encoded_username}:{_encoded_password}@{settings.sql_golddb_server}:1433/{settings.sql_golddb_name}"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

class SQLExecutor:
    """SQL execution handler for MSSQL"""
    
    def __init__(self):
        self.engine = engine
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            with get_db_connection() as conn:
                # Use pandas for better data handling
                df = pd.read_sql_query(text(query), conn, params=params or {})
                
                result = {
                    "success": True,
                    "data": df.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "row_count": len(df),
                    "query": query
                }
                
                logger.info(f"Query executed successfully. Returned {len(df)} rows.")
                return result
                
        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "data": [],
                "columns": [],
                "row_count": 0
            }
    
    async def get_schema_info(self, table_name: str = None) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            with get_db_connection() as conn:
                if table_name:
                    # Get specific table schema
                    schema_query = """
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = :table_name
                    ORDER BY ORDINAL_POSITION
                    """
                    df = pd.read_sql_query(text(schema_query), conn, params={"table_name": table_name})
                else:
                    # Get all tables
                    tables_query = """
                    SELECT TABLE_NAME, TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    """
                    df = pd.read_sql_query(text(tables_query), conn)
                
                return {
                    "success": True,
                    "data": df.to_dict('records'),
                    "columns": df.columns.tolist()
                }
                
        except Exception as e:
            logger.error(f"Schema query error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": []
            }
    
    async def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate SQL query syntax without executing"""
        try:
            with get_db_connection() as conn:
                # Use SET PARSEONLY to validate syntax
                validate_query = f"SET PARSEONLY ON; {query}"
                conn.execute(text(validate_query))
                
                return {
                    "valid": True,
                    "error": None
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

sql_executor = SQLExecutor()
