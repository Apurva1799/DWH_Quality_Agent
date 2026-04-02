"""
Multi-Agent Database Chatbot System

A comprehensive multi-agent system for MSSQL database interactions 
using on-prem LLM clients (Nemotron, DeepSeek, Llama) and DocumentDB.
"""

__version__ = "2.0.0"
__author__ = "Apurva Raj"
__description__ = "Enhanced Multi-Agent Database Chatbot"

# Import main components
from .main import app
from .config import settings
from .llm_manager import llm_manager

__all__ = [
    "app",
    "settings",
    "llm_manager"
]
