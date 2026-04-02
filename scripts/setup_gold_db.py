#!/usr/bin/env python3
"""
MSSQL Gold Database Setup Script

This script helps set up and configure the Gold database connection
for the Multi-Agent Database Chatbot system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_env_file():
    """Create .env file with Gold DB configuration"""
    print(" Setting up MSSQL Gold Database Configuration")
    print("=" * 50)
    
    # Check if .env exists
    env_path = project_root / ".env"
    
    if env_path.exists():
        print(" .env file already exists.")
        choice = input("Do you want to update it? (y/n): ").lower().strip()
        if choice != 'y':
            print(" Setup cancelled.")
            return
    
    # Get Gold DB configuration
    print("\n Enter Gold Database Configuration:")
    print("-" * 40)
    
    server = input("Server (e.g., afdbsrv.kalyanicorp.com): ").strip()
    if not server:
        server = "afdbsrv.kalyanicorp.com"
    
    database = input("Database name (e.g., GOLD_DB): ").strip()
    if not database:
        database = "GOLD_DB"
    
    username = input("Username (e.g., Gold_Reader): ").strip()
    if not username:
        username = "Gold_Reader"
    
    password = input("Password: ").strip()
    if not password:
        print(" Password is required!")
        return
    
    # Create .env content
    env_content = f"""# Multi-Agent Database Chatbot Configuration
# Gold Database Configuration

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Gold Database Configuration
SQL_GOLDDB_SERVER={server}
SQL_GOLDDB_NAME={database}
SQL_GOLDDB_USERNAME={username}
SQL_GOLDDB_PASSWORD={password}

# Silver Database (default)
SQL_SILVERDB_SERVER=afdbsrv.kalyanicorp.com
SQL_SILVERDB_NAME=Silver_DB
SQL_SILVERDB_USERNAME=Silver_Reader
SQL_SILVERDB_PASSWORD=Silver_Reader@123

# IoT Database
SQL_IOT_SERVER=sqldbsrv.kalyanicorp.com
SQL_IOT_NAME=IOTEDGEDB
SQL_IOT_PASSWORD=dbaccess@123

# Dev Database
SQL_SERVER_DEV=sqldbDEV.kalyanicorp.com
SQL_DATABASE_DEV=Development

# LLM Configuration
LLM_NEMOTRON_49B=nvidia/llama-3.3-nemotron-super-49b-v1.5
BASE_URL_LLM_NEMOTRON_49B=https://10.7.30.1:8191

LLM_NEMOTRON_253B=nvidia/llama-3.1-nemotron-ultra-253b-v1
BASE_URL_LLM_NEMOTRON_253B=https://10.7.30.1:8190

LLM_DEEPSEEK_R1_70B=deepseek-r1:70b
BASE_URL_LLM_DEEPSEEK_R1_70B=https://10.7.110.82:9999

LLM_LLAMA_70B_INSTRUCT=meta/llama-3.3-70b-instruct
BASE_URL_LLAMA_70B_INSTRUCT=https://10.7.30.1:8192

# DocumentDB Configuration
DOCUMENTDB_BASE_URL=https://10.7.1.200:8002
DOCUMENTDB_USERNAME=AI_Agent_Chatbot
DOCUMENTDB_PASSWORD=AI_Agent_Chatbot@2025
DOCUMENTDB_SSL_VERIFY=false

# Additional Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
QUERY_TIMEOUT_SECONDS=30
SESSION_TIMEOUT_HOURS=2
CLEANUP_INTERVAL_MINUTES=5
MAX_RECONNECT_ATTEMPTS=5
OFFLINE_MODE=false
"""
    
    # Write to .env file
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"Configuration saved to {env_path}")
        print()
        print("Security Note:")
        print("  - The .env file contains sensitive credentials")
        print("  - Make sure it's not committed to version control")
        print("  - Set appropriate file permissions")
        print()
        print(" Next Steps:")
        print("  1. Test connection: python scripts/test_gold_db_connection.py")
        print("  2. Start application: make run")
        print("  3. Check health: make health")
        
    except Exception as e:
        print(f" Error saving configuration: {str(e)}")
        return

def show_current_config():
    """Show current Gold DB configuration"""
    print(" Current Gold Database Configuration:")
    print("-" * 40)
    
    try:
        from app.config import get_database_config
        gold_config = get_database_config("gold")
        
        print(f"Server: {gold_config['server']}")
        print(f"Database: {gold_config['database']}")
        print(f"Username: {gold_config['username']}")
        print(f"Password: {'*' * len(gold_config['password'])}")
        
    except Exception as e:
        print(f" Error reading configuration: {str(e)}")

def main():
    """Main setup menu"""
    print(" MSSQL Gold Database Setup")
    print(" Multi-Agent Database Chatbot")
    print()
    
    while True:
        print("\n Setup Options:")
        print("1. Create/Update .env configuration")
        print("2. Show current configuration")
        print("3. Test connection")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            create_env_file()
        elif choice == "2":
            show_current_config()
        elif choice == "3":
            # Import and run test script
            try:
                from scripts.test_gold_db_connection import test_gold_connection
                test_gold_connection()
            except ImportError:
                print(" Cannot import test script. Run it directly:")
                print("   python scripts/test_gold_db_connection.py")
        elif choice == "4":
            print(" Goodbye!")
            break
        else:
            print(" Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()
