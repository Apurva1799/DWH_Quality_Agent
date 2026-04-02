#!/usr/bin/env python3
"""
MSSQL Gold Database Usage Example

This script shows how to use the Gold database with the Multi-Agent system.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_database_config
from app.database import sql_executor

async def gold_db_examples():
    """Examples of using Gold database"""
    
    print(" Gold Database Usage Examples")
    print("=" * 40)
    
    # 1. Get Gold DB Configuration
    print("\n1⃣  Database Configuration:")
    gold_config = get_database_config("gold")
    print(f"   Server: {gold_config['server']}")
    print(f"   Database: {gold_config['database']}")
    print(f"   Username: {gold_config['username']}")
    
    # 2. Test Connection
    print("\n2⃣  Testing Connection:")
    try:
        from sqlalchemy import create_engine, text
        
        # Build connection string
        db_url = (
            f"mssql+pymssql://{gold_config['username']}:"
            f"{gold_config['password']}@{gold_config['server']}:"
            f"1433/{gold_config['database']}"
        )
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT @@VERSION as version"))
            version = result.fetchone()[0]
            print(f"    Connected! SQL Server Version: {version[:50]}...")
            
    except Exception as e:
        print(f"    Connection failed: {str(e)}")
        return
    
    # 3. Query Examples
    print("\n3⃣  Sample Queries:")
    
    queries = [
        "-- Get table count\nSELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
        "-- List all tables\nSELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
        "-- Get database size\nSELECT DB_NAME(database_id) AS DatabaseName, SUM(size) * 8 / 1024 AS DatabaseSizeMB FROM sys.master_files WHERE DB_NAME(database_id) = DB_NAME() GROUP BY database_id"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"   Query {i}:")
        print(f"   {query}")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                print(f"   Result: {rows}")
        except Exception as e:
            print(f"   Error: {str(e)}")
        print()

async def use_in_application():
    """Show how to use Gold DB in application code"""
    
    print("\n  Using Gold DB in Application:")
    print("-" * 30)
    
    example_code = '''
from app.agents.sql_agent import SQLAgent
from app.agents.base import AgentRequest

# Create SQL Agent for Gold database
sql_agent = SQLAgent(db_type="gold")

# Create request
request = AgentRequest(
    query="Show me top 10 customers",
    context={},
    user_id="user123",
    session_id="session456"
)

# Process request
response = await sql_agent.process(request)
print(response.response)
'''
    
    print(example_code)
    
    print("\n Using via REST API:")
    api_example = '''
# Query Gold database via API
curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Show top customers from gold database",
    "user_id": "user123",
    "session_id": "session456"
  }'
'''
    print(api_example)

if __name__ == "__main__":
    print(" MSSQL Gold Database - Usage Guide")
    print("=" * 40)
    print()
    
    # Run examples
    asyncio.run(gold_db_examples())
    asyncio.run(use_in_application())
    
    print("\n Quick Commands:")
    print("  • Test connection: make test-gold-db")
    print("  • Setup config: make setup-gold-db")
    print("  • Start API: make run")
    print("  • Query via API: curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"message\": \"Query from gold database\"}'")
