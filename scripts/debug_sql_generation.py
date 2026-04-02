#!/usr/bin/env python3
"""Debug SQL generation by showing actual LLM response"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.sql_agent import SQLAgent
from app.llm_manager import llm_manager

async def debug_sql_generation():
    """Debug SQL generation step by step"""
    print("=" * 70)
    print("DEBUGGING SQL GENERATION")
    print("=" * 70)
    
    agent = SQLAgent("gold")
    
    # Test query
    query = "Show all tables"
    
    print(f"\n1. Testing query: '{query}'")
    
    # Step 1: Get schema
    print("\n2. Getting schema...")
    schema = await agent._get_relevant_schema(query)
    print(f"Schema preview: {schema[:200]}...")
    
    # Step 2: Build prompt
    print("\n3. Building prompt...")
    prompt = agent._build_sql_generation_prompt(query, schema, [], "gold")
    print(f"Prompt:\n{prompt}\n")
    
    # Step 3: Call LLM
    print("4. Calling LLM...")
    result = await llm_manager.generate_with_nemotron_49b(prompt, temperature=0.1)
    
    if result["success"]:
        print(f"LLM Response:\n{result['response']}\n")
        
        # Step 4: Extract SQL
        print("5. Extracting SQL...")
        sql = agent._extract_sql_from_response(result["response"])
        
        if sql:
            print(f"Extracted SQL: {sql}")
            print("\nSUCCESS!")
        else:
            print("FAILED: Could not extract SQL from response")
            print("\nRaw response for manual inspection:")
            print(repr(result["response"]))
    else:
        print(f"LLM FAILED: {result.get('error')}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(debug_sql_generation())
