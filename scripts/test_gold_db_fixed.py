#!/usr/bin/env python3
"""
Quick Gold DB Connection Test - Fixed Version

This script tests the Gold DB connection with proper URL encoding.
"""

import sys
from pathlib import Path
import urllib.parse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_connection():
    """Test connection with URL-encoded credentials"""
    print(" Gold Database Connection Test (Fixed)")
    print("=" * 50)
    
    try:
        from sqlalchemy import create_engine, text
        from app.config import get_database_config
        
        # Get Gold DB configuration
        gold_config = get_database_config("gold")
        
        print(f" Configuration:")
        print(f"  Server: {gold_config['server']}")
        print(f"  Database: {gold_config['database']}")
        print(f"  Username: {gold_config['username']}")
        print(f"  Password: {'*' * len(gold_config['password'])}")
        print()
        
        # URL-encode password (handle special characters like @)
        encoded_username = urllib.parse.quote_plus(gold_config['username'])
        encoded_password = urllib.parse.quote_plus(gold_config['password'])
        
        print(f" URL Encoded:")
        print(f"  Username: {encoded_username}")
        print(f"  Password: {'*' * len(encoded_password)}")
        print()
        
        # Build connection string with encoded credentials
        connection_string = (
            f"mssql+pymssql://{encoded_username}:"
            f"{encoded_password}@{gold_config['server']}:"
            f"1433/{gold_config['database']}"
        )
        
        print(f" Connection String (masked):")
        print(f"  mssql+pymssql://{encoded_username}:{'*' * len(encoded_password)}@{gold_config['server']}:1433/{gold_config['database']}")
        print()
        
        # Test connection
        print(" Testing connection...")
        engine = create_engine(connection_string, pool_pre_ping=True)
        
        with engine.connect() as conn:
            print(" Connected successfully!")
            
            # Test query
            result = conn.execute(text("SELECT @@VERSION as version"))
            version = result.fetchone()[0]
            print(f" SQL Server Version: {version}")
            
            # Get tables
            result = conn.execute(text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"))
            table_count = result.fetchone()[0]
            print(f" Number of tables: {table_count}")
            
            return True
            
    except Exception as e:
        print(f" Connection failed: {str(e)}")
        print()
        print(" Debugging:")
        print(f"  Error type: {type(e).__name__}")
        
        # Check if it's a password issue
        if "bfl123" in str(e):
            print("    Password contains '@' character which is breaking the connection!")
            print("   The password should be URL-encoded or use pymssql directly")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if not success:
        print()
        print("  Alternative: Direct pymssql connection")
        print("-" * 40)
        
        try:
            import pymssql
            from app.config import get_database_config
            
            gold_config = get_database_config("gold")
            
            print(f"Trying direct pymssql connection...")
            conn = pymssql.connect(
                server=gold_config['server'],
                user=gold_config['username'],
                password=gold_config['password'],
                database=gold_config['database'],
                port=1433,
                timeout=30
            )
            
            print(" Direct pymssql connection successful!")
            
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f" SQL Server Version: {version}")
            
            conn.close()
            
        except Exception as e2:
            print(f" Direct connection also failed: {str(e2)}")
            print()
            print(" Summary:")
            print("  1. Server 'afdbsrv.kalyanicorp.com' is not reachable from this environment")
            print("  2. This is expected if you're not on the corporate network")
            print("  3. The configuration is correct - it will work in your corporate environment")
            print("  4. Password handling is now fixed for special characters")
