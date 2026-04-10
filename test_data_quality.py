#!/usr/bin/env python3
"""Test script to diagnose Data Quality Agent issues"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
from app.database import SQLExecutor

async def test():
    executor = SQLExecutor()
    
    # Test 1: Get all tables
    print("=== Test 1: Get all tables ===")
    result = await executor.execute_query(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
    )
    print(f"Success: {result.get('success')}")
    data = result.get('data', [])
    print(f"Table count: {len(data)}")
    print(f"Data type: {type(data)}")
    if data:
        print(f"First row type: {type(data[0])}")
        print(f"First row: {data[0]}")
        if isinstance(data[0], dict):
            print(f"First 10 tables: {[r.get('TABLE_NAME', r) for r in data[:10]]}")
        else:
            print(f"First 10 tables: {[r[0] if isinstance(r, (list, tuple)) else r for r in data[:10]]}")
    print()
    
    # Test 2: Gold pattern
    print("=== Test 2: Gold pattern match ===")
    result = await executor.execute_query(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME LIKE '%gold%' ORDER BY TABLE_NAME"
    )
    print(f"Success: {result.get('success')}")
    print(f"Gold table count: {len(result.get('data', []))}")
    if result.get('data'):
        print(f"Gold tables: {[r[0] for r in result['data']]}")
    print()
    
    # Test 3: Check current database
    print("=== Test 3: Current database ===")
    result = await executor.execute_query("SELECT DB_NAME() AS CurrentDB")
    print(f"Database: {result.get('data', [['Unknown']])[0][0]}")
    print()
    
    # Test 4: Check schemas
    print("=== Test 4: Check schemas ===")
    result = await executor.execute_query(
        "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA"
    )
    print(f"Schemas: {[r[0] for r in result.get('data', [])]}")

if __name__ == "__main__":
    asyncio.run(test())
