#!/usr/bin/env python3
"""Test the Kalyani LangChain LLM wrapper"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage

async def test_llm():
    """Test the LLM connection"""
    print("=" * 60)
    print("Testing Kalyani LangChain LLM Wrapper")
    print("=" * 60)
    print()
    
    # Create LLM instance
    llm = KalyaniLangChainLLM()
    print(f"Base URL: {llm.base_url}")
    print(f"Model: {llm.model_name}")
    print()
    
    # Test 1: List available models
    print("Test 1: Listing available models...")
    try:
        models = await llm.list_models()
        print(f"Response: {models}")
        print()
    except Exception as e:
        print(f"Error listing models: {e}")
        print()
    
    # Test 2: Simple generation
    print("Test 2: Simple text generation...")
    print("Prompt: 'Hello, what is SQL?'")
    print("Response: ", end="", flush=True)
    
    try:
        messages = [HumanMessage(content="Hello, what is SQL?")]
        response = await llm._agenerate(messages)
        print(response.generations[0].message.content)
        print()
        print("SUCCESS! LLM is working.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print()
        print("FAILED: Could not generate text.")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_llm())
    sys.exit(0 if success else 1)
