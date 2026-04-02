#!/usr/bin/env python3
"""Test the updated chatbot with working LLM"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.llm_manager import llm_manager

async def test_chatbot():
    """Test chatbot with working LLM"""
    print("=" * 60)
    print("Testing Updated Chatbot with Kalyani Gateway")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    print("Test 1: Health Check...")
    try:
        health = await llm_manager.health_check()
        print(f"Health Status: {health}")
        if health.get("kalyani_gateway"):
            print("✓ LLM Gateway is healthy!")
        else:
            print("✗ LLM Gateway failed")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    print()
    
    # Test 2: Simple generation
    print("Test 2: Simple Generation...")
    print("Query: 'What is SQL?'")
    print("Response: ", end="", flush=True)
    
    try:
        result = await llm_manager.generate("What is SQL?")
        if result["success"]:
            print(result["response"][:200] + "...")
            print()
            print("✓ Generation successful!")
        else:
            print(f"\n✗ Generation failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"\n✗ Generation error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("All tests passed! Chatbot is ready to use.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_chatbot())
    sys.exit(0 if success else 1)
