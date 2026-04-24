"""
External LLM Client Integrations

This package contains the client implementations for external services:
- SequentialLLMClient: For Nemotron models
- LLM_3B_Client: For DGX 3B/Qwen models  
- DocumentDBClient: For DocumentDB operations

These clients are provided by the user and integrated into the multi-agent system.
"""

from .llm_clients import LLMClient as SequentialLLMClient
from .dgx_3b_client import LLM_3B_Client
from .documentdb_client import DocumentDBClient

__all__ = [
    "SequentialLLMClient",
    "LLM_3B_Client", 
    "DocumentDBClient"
]
