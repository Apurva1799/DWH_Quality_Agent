#!/usr/bin/env python3
"""
DWH Quality Agent - Root Launcher
Starts the DWH Quality Agent dashboard from the backend.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Run the main script
exec(open(os.path.join(os.path.dirname(__file__), 'backend', 'scripts', 'chatgpt_chatbot.py')).read())
