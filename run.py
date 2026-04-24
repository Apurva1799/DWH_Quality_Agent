#!/usr/bin/env python3
"""
DWH Quality Agent - Root Launcher
Starts the DWH Quality Agent dashboard from the backend.
"""
import sys
import os
from pathlib import Path

# Set correct paths before executing
script_dir = Path(__file__).parent
backend_dir = script_dir / 'backend'

# Add backend to path
sys.path.insert(0, str(backend_dir))

# Set __file__ to point to the actual script being executed
# This ensures path calculations in chatgpt_chatbot.py work correctly
script_path = backend_dir / 'scripts' / 'chatgpt_chatbot.py'

# Execute the script with correct __file__ context
exec_globals = {
    '__file__': str(script_path),
    '__name__': '__main__',
    '__package__': None,
    '__cached__': None,
    '__doc__': None,
    '__loader__': None,
    '__spec__': None,
    '__builtins__': __builtins__,
}

exec(open(script_path).read(), exec_globals)
