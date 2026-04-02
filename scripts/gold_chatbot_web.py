#!/usr/bin/env python3
"""
Simple Web Chatbot for Gold Database

A lightweight web interface for chatting with the Gold database.
Run this alongside the main API for a simple chat experience.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template_string, request, jsonify
import asyncio
from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.config import get_database_config
from app.llm_manager import llm_manager
import uuid
import urllib.parse
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Initialize components
orchestrator = OrchestratorAgent()
user_sessions = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title> Gold Database Chatbot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .chat-area {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 15px;
            max-width: 70%;
        }
        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .bot-message {
            background: white;
            border: 1px solid #e0e0e0;
            color: #333;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1em;
            outline: none;
        }
        input[type="text"]:focus {
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .examples {
            padding: 20px;
            background: #f0f0f0;
        }
        .examples h3 {
            margin-bottom: 10px;
            color: #667eea;
        }
        .example-chip {
            display: inline-block;
            padding: 8px 15px;
            margin: 5px;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }
        .example-chip:hover {
            background: #667eea;
            color: white;
        }
        .typing {
            font-style: italic;
            color: #666;
        }
        .status {
            padding: 10px 20px;
            background: #e8f5e9;
            color: #2e7d32;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> Gold Database Chatbot</h1>
            <p>Ask questions about your data in natural language</p>
        </div>
        
        <div class="status">
             Connected to GOLD_DB | Server: afdbsrv.kalyanicorp.com | Tables: 122
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message bot-message">
                <strong> Bot:</strong><br>
                Hello! I'm your Gold Database assistant. I can help you:<br><br>
                • Query data using natural language<br>
                • Analyze database information<br>
                • Generate SQL queries automatically<br>
                • Show table structures<br><br>
                What would you like to know?
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-group">
                <input type="text" id="userInput" placeholder="Ask me anything about your data..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="examples">
            <h3> Try these examples:</h3>
            <span class="example-chip" onclick="setInput('Show all tables')">Show all tables</span>
            <span class="example-chip" onclick="setInput('What are the top 10 customers?')">Top 10 customers</span>
            <span class="example-chip" onclick="setInput('Count total records')">Count records</span>
            <span class="example-chip" onclick="setInput('Show sales data')">Sales data</span>
            <span class="example-chip" onclick="setInput('Find duplicates')">Find duplicates</span>
            <span class="example-chip" onclick="setInput('Recent orders')">Recent orders</span>
        </div>
    </div>

    <script>
        let sessionId = '{{ session_id }}';
        
        function setInput(text) {
            document.getElementById('userInput').value = text;
            document.getElementById('userInput').focus();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                // Remove typing indicator and add bot response
                removeTyping();
                addMessage(data.response, 'bot');
                
            } catch (error) {
                removeTyping();
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        }
        
        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const prefix = sender === 'user' ? ' You:' : ' Bot:';
            messageDiv.innerHTML = `<strong>${prefix}</strong><br>${text}`;
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function showTyping() {
            const chatArea = document.getElementById('chatArea');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot-message typing';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = '<strong> Bot:</strong> Thinking...';
            chatArea.appendChild(typingDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function removeTyping() {
            const typingDiv = document.getElementById('typingIndicator');
            if (typingDiv) {
                typingDiv.remove();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    session_id = str(uuid.uuid4())
    return render_template_string(HTML_TEMPLATE, session_id=session_id)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    if not message:
        return jsonify({'response': 'Please enter a message'})
    
    # Handle simple commands directly
    if message.lower() in ['tables', 'show tables', 'list tables']:
        return jsonify({'response': get_tables_response()})
    
    # Process through orchestrator
    try:
        request_obj = AgentRequest(
            query=message,
            context={'database': 'gold'},
            user_id='web_user',
            session_id=session_id
        )
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(orchestrator.process(request_obj))
        loop.close()
        
        return jsonify({'response': response.response})
        
    except Exception as e:
        return jsonify({'response': f'Error processing request: {str(e)}'})

def get_tables_response():
    """Get list of tables"""
    try:
        gold_config = get_database_config("gold")
        
        # URL-encode credentials
        encoded_username = urllib.parse.quote_plus(gold_config['username'])
        encoded_password = urllib.parse.quote_plus(gold_config['password'])
        
        db_url = (
            f"mssql+pymssql://{encoded_username}:{encoded_password}"
            f"@{gold_config['server']}:1433/{gold_config['database']}"
        )
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT TOP 20 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            response = " <strong>Available Tables:</strong><br><br>"
            for i, table in enumerate(tables, 1):
                response += f"{i}. {table}<br>"
            
            if len(tables) == 20:
                response += "<br>... and more tables available"
            
            return response
            
    except Exception as e:
        return f" Error fetching tables: {str(e)}"

if __name__ == '__main__':
    print(" Gold Database Chatbot - Web Interface")
    print("=" * 40)
    print(" Open your browser and go to: http://localhost:8080")
    print(" Access from any device on your network")
    print(" Features: Natural language queries, Auto SQL generation")
    print("=" * 40)
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
