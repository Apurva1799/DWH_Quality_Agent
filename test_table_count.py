#!/usr/bin/env python3
"""Test script to check row counts directly"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
from app.database import SQLExecutor

async def test():
    executor = SQLExecutor()
    
    # Test tables that were showing errors
    test_tables = [
        "[BFL].[Dim_Category]",
        "[BFL].[Dim_Area]",
        "[BFL].[Dim_Account_SalesForce]"
    ]
    
    for table in test_tables:
        print(f"\n=== Testing {table} ===")
        try:
            query = f"SELECT COUNT(*) FROM {table}"
            print(f"Query: {query}")
            result = await executor.execute_query(query)
            print(f"Success: {result.get('success')}")
            print(f"Data: {result.get('data')}")
            if result.get('data'):
                row = result['data'][0]
                print(f"Row type: {type(row)}")
                print(f"Row: {row}")
                if isinstance(row, dict):
                    print(f"Row values: {list(row.values())}")
                    count = list(row.values())[0]
                else:
                    count = row[0]
                print(f"Count: {count}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())
