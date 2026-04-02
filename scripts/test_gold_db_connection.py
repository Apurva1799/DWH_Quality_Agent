#!/usr/bin/env python3
"""
MSSQL Gold Database Connection Test

This script helps test connectivity to the Gold database and provides
connection information for troubleshooting.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.exc import SQLAlchemyError
    import pymssql
    from app.config import get_database_config
    from loguru import logger
    
    def test_gold_connection():
        """Test connection to Gold database"""
        print(" Testing MSSQL Gold Database Connection")
        print("=" * 50)
        
        # Get Gold DB configuration
        gold_config = get_database_config("gold")
        
        print(f" Database Configuration:")
        print(f"  Server: {gold_config['server']}")
        print(f"  Database: {gold_config['database']}")
        print(f"  Username: {gold_config['username']}")
        print(f"  Password: {'*' * len(gold_config['password'])}")
        print()
        
        # Build connection string
        connection_string = (
            f"mssql+pymssql://{gold_config['username']}:"
            f"{gold_config['password']}@{gold_config['server']}:"
            f"1433/{gold_config['database']}"
        )
        
        print(f" Connection String (masked):")
        print(f"  mssql+pymssql://{gold_config['username']}:"
            f"{'*' * len(gold_config['password'])}@{gold_config['server']}:"
            f"1433/{gold_config['database']}")
        print()
        
        try:
            # Test basic connection
            print(" Attempting connection...")
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                connect_args={
                    "timeout": 30
                }
            )
            
            with engine.connect() as connection:
                print(" Connection successful!")
                
                # Test basic query
                result = connection.execute(text("SELECT @@VERSION as version"))
                version = result.fetchone()[0]
                print(f" SQL Server Version: {version}")
                
                # Get database info
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f" Available Tables: {len(tables)} tables")
                
                if tables:
                    print(" First 10 tables:")
                    for table in tables[:10]:
                        print(f"  - {table}")
                    if len(tables) > 10:
                        print(f"  ... and {len(tables) - 10} more")
                
                print()
                print(" Connection test completed successfully!")
                return True
                
        except SQLAlchemyError as e:
            print(f" SQLAlchemy Error: {str(e)}")
            return False
        except Exception as e:
            print(f" Connection Error: {str(e)}")
            return False
    
    def check_dependencies():
        """Check if required dependencies are installed"""
        print(" Checking Dependencies...")
        
        try:
            import pymssql
            print(" pymssql installed")
        except ImportError:
            print(" pymssql not installed. Run: pip install pymssql")
            return False
        
        try:
            import sqlalchemy
            print(" sqlalchemy installed")
        except ImportError:
            print(" sqlalchemy not installed. Run: pip install sqlalchemy")
            return False
        
        return True
    
    def show_troubleshooting(gold_config):
        """Show troubleshooting tips"""
        print()
        print("  Troubleshooting Tips:")
        print("=" * 30)
        print("1. Network Connectivity:")
        print(f"   - Can you ping {gold_config['server']}?")
        print(f"   - Is port 1433 open on the server?")
        print()
        print("2. Authentication:")
        print(f"   - Username: {gold_config['username']}")
        print(f"   - Password: Check if password is correct")
        print()
        print("3. Database Access:")
        print(f"   - Database: {gold_config['database']}")
        print("   - Does the user have read permissions?")
        print()
        print("4. Firewall/Network:")
        print("   - Check if firewall allows MSSQL connections")
        print("   - Try connecting from different network")
        print()
        print("5. Configuration:")
        print("   - Verify .env file has correct values")
        print("   - Check for typos in server/database names")
    
    if __name__ == "__main__":
        print(" MSSQL Gold Database Connection Test")
        print(" Multi-Agent Database Chatbot")
        print()
        
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Test connection
        success = test_gold_connection()
        
        if not success:
            # Get gold_config for troubleshooting
            from app.config import get_database_config
            gold_config = get_database_config("gold")
            show_troubleshooting(gold_config)
            sys.exit(1)

except ImportError as e:
    print(f" Import Error: {str(e)}")
    print("Make sure you're running from the project root directory")
    print("Or install dependencies: pip install -e .")
    sys.exit(1)
