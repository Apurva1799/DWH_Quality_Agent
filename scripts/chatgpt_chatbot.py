#!/usr/bin/env python3
"""
Kalyani Database Assistant - ChatGPT-Style Interface
A modern, unified chatbot with integrated SQL, metadata, and LLM capabilities.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import asyncio
import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import queue

from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.llm_manager import llm_manager
from app.config import get_database_config
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ============ SYSTEM PROMPTS ============

SOPHIE_SYSTEM_PROMPT = """You are Sophie, an expert Database Assistant at Kalyani Group.

Your capabilities:
1. Answer database-related questions using the Gold/Silver/IoT/Dev databases
2. Generate SQL queries from natural language
3. Analyze data and provide insights
4. Help with schema understanding
5. Route complex queries to appropriate agents

Database Schema Information:
{schema_context}

When answering:
- Be professional, precise, and helpful
- If you generate SQL, explain what it does
- For data questions, use the metadata available
- Always validate your understanding before executing queries
- If uncertain, ask clarifying questions

Current conversation context will be provided to help you give relevant answers."""

SQL_GENERATION_PROMPT = """You are an expert SQL query generator for {db_type} database.

Available Tables and Schema:
{schema_info}

CRITICAL RULES:
1. ALWAYS use exact table names from the schema above
2. ALWAYS specify column names after SELECT (use * only when asked)
3. Use proper MSSQL T-SQL syntax
4. For date filters, use: DATEADD(month, -1, GETDATE()) for "last month"
5. End with semicolon
6. NO natural language in SQL - only valid SQL code
7. NO markdown code blocks in output

BAD EXAMPLES:
- SELECT * FROM that table WHERE date is last month;  (wrong)
- SELECT data FROM table WHERE date = last month;  (wrong)

GOOD EXAMPLES:
- SELECT SBU, CustomerName FROM ActualCapacityDecember2025 WHERE ENTRY_DATE >= DATEADD(month, -1, GETDATE());
- SELECT COUNT(*) FROM information_schema.tables;

User Question: {question}

Generate ONLY the SQL query, nothing else:"""

# ============ CHATGPT-STYLE HTML TEMPLATE ============

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kalyani Database Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.2/marked.min.js"></script>
    <style>
        :root {
            --sidebar-width: 260px;
            --header-height: 60px;
            --input-height: 80px;
        }
        
        [data-theme="dark"] {
            --bg-primary: #343541;
            --bg-secondary: #40414f;
            --bg-sidebar: #202123;
            --bg-hover: #2a2b32;
            --text-primary: #ececf1;
            --text-secondary: #8e8ea0;
            --accent: #10a37f;
            --accent-hover: #0d8f6e;
            --border: #4d4d4f;
            --code-bg: #1e1e1e;
        }
        
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f7f7f8;
            --bg-sidebar: #f7f7f8;
            --bg-hover: #e5e5e5;
            --text-primary: #343541;
            --text-secondary: #6e6e80;
            --accent: #10a37f;
            --accent-hover: #0d8f6e;
            --border: #d9d9e3;
            --code-bg: #f6f6f6;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 12px;
            gap: 8px;
        }
        
        .new-chat-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .new-chat-btn:hover {
            background: var(--bg-hover);
        }
        
        .chat-history {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .chat-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text-secondary);
            transition: background 0.2s;
            overflow: hidden;
        }
        
        .chat-item:hover {
            background: var(--bg-hover);
        }
        
        .chat-item.active {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        .chat-item i {
            font-size: 14px;
            flex-shrink: 0;
        }
        
        .chat-item span {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .sidebar-footer {
            border-top: 1px solid var(--border);
            padding-top: 8px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .footer-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text-secondary);
            transition: background 0.2s;
        }
        
        .footer-btn:hover {
            background: var(--bg-hover);
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .header {
            height: var(--header-height);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 20px;
            position: relative;
        }
        
        .header-title {
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .header-actions {
            position: absolute;
            right: 20px;
            display: flex;
            gap: 12px;
        }
        
        .header-btn {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        .header-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        /* Chat Area */
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 0;
            scroll-behavior: smooth;
        }
        
        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 40px;
            gap: 32px;
        }
        
        .welcome-logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
        }
        
        .welcome-title {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .example-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            max-width: 600px;
            width: 100%;
        }
        
        .example-card {
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
            border: 1px solid transparent;
        }
        
        .example-card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        
        .example-card h4 {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            color: var(--text-primary);
        }
        
        .example-card p {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        /* Messages */
        .message {
            display: flex;
            gap: 16px;
            padding: 20px 20%;
            border-bottom: 1px solid var(--border);
        }
        
        .message.user {
            background: var(--bg-primary);
        }
        
        .message.assistant {
            background: var(--bg-secondary);
        }
        
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 16px;
        }
        
        .message.user .message-avatar {
            background: var(--accent);
            color: white;
        }
        
        .message.assistant .message-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message-content {
            flex: 1;
            font-size: 16px;
            line-height: 1.6;
            max-width: none;
        }
        
        .message-content p {
            margin-bottom: 12px;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        .message-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .message:hover .message-actions {
            opacity: 1;
        }
        
        .action-btn {
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s;
        }
        
        .action-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        /* Code Blocks */
        .code-block {
            background: var(--code-bg);
            border-radius: 8px;
            margin: 16px 0;
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 16px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid var(--border);
        }
        
        .code-language {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }
        
        .copy-btn {
            padding: 4px 12px;
            border-radius: 6px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        
        .copy-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        .code-block pre {
            padding: 16px;
            overflow-x: auto;
            margin: 0;
        }
        
        .code-block code {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        
        /* Input Area */
        .input-container {
            border-top: 1px solid var(--border);
            padding: 12px 20%;
            background: var(--bg-primary);
        }
        
        .input-wrapper {
            display: flex;
            align-items: flex-end;
            gap: 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 12px 16px;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .input-field {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 16px;
            line-height: 1.5;
            resize: none;
            max-height: 200px;
            min-height: 24px;
            font-family: inherit;
        }
        
        .input-field:focus {
            outline: none;
        }
        
        .input-field::placeholder {
            color: var(--text-secondary);
        }
        
        .send-btn {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            border: none;
            background: var(--accent);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .send-btn:hover:not(:disabled) {
            background: var(--accent-hover);
        }
        
        .send-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .input-hint {
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 8px;
        }
        
        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 4px 0;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--text-secondary);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out both;
        }
        
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .message { padding: 16px; }
            .input-container { padding: 12px 16px; }
            .example-grid { grid-template-columns: 1fr; }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <button class="new-chat-btn" onclick="newChat()">
                <i class="fas fa-plus"></i>
                <span>New Chat</span>
            </button>
            
            <div class="chat-history" id="chatHistory">
                <!-- Chat history items will be added here -->
            </div>
            
            <div class="sidebar-footer">
                <div class="footer-btn" onclick="toggleTheme()">
                    <i class="fas fa-moon" id="themeIcon"></i>
                    <span>Dark mode</span>
                </div>
                <div class="footer-btn" onclick="clearConversations()">
                    <i class="fas fa-trash"></i>
                    <span>Clear conversations</span>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <div class="header-title">
                    <i class="fas fa-robot"></i>
                    <span>Kalyani Database Assistant</span>
                </div>
                <div class="header-actions">
                    <button class="header-btn" onclick="shareChat()" title="Share">
                        <i class="fas fa-share-alt"></i>
                    </button>
                    <button class="header-btn" onclick="showSettings()" title="Settings">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <!-- Welcome Screen -->
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-logo">
                        <i class="fas fa-database"></i>
                    </div>
                    <h1 class="welcome-title">How can I help you today?</h1>
                    
                    <div class="example-grid">
                        <div class="example-card" onclick="setInput('Show all tables in Gold database')">
                            <h4><i class="fas fa-table"></i> Show tables</h4>
                            <p>List all available tables in the database</p>
                        </div>
                        <div class="example-card" onclick="setInput('What are the top 10 customers by sales?')">
                            <h4><i class="fas fa-trophy"></i> Top customers</h4>
                            <p>Find top customers by sales volume</p>
                        </div>
                        <div class="example-card" onclick="setInput('Generate SQL to find recent orders')">
                            <h4><i class="fas fa-code"></i> Generate SQL</h4>
                            <p>Create SQL queries from natural language</p>
                        </div>
                        <div class="example-card" onclick="setInput('Analyze production data trends')">
                            <h4><i class="fas fa-chart-line"></i> Analyze data</h4>
                            <p>Get insights from your data</p>
                        </div>
                    </div>
                </div>
                
                <!-- Messages will be added here -->
            </div>
            
            <div class="input-container">
                <div class="input-wrapper">
                    <textarea class="input-field" id="userInput" placeholder="Message Kalyani Database Assistant..." rows="1" onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()" disabled>
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="input-hint">Press Enter to send, Shift+Enter for new line</div>
            </div>
        </div>
    </div>
    
    <script>
        // State
        let sessionId = generateId();
        let currentChat = [];
        let isStreaming = false;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadTheme();
            document.getElementById('userInput').focus();
        });
        
        // Utilities
        function generateId() {
            return Math.random().toString(36).substring(2, 15);
        }
        
        function setInput(text) {
            const input = document.getElementById('userInput');
            input.value = text;
            input.focus();
            autoResize(input);
            updateSendButton();
        }
        
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        }
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function updateSendButton() {
            const input = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = !input.value.trim() || isStreaming;
        }
        
        document.getElementById('userInput').addEventListener('input', updateSendButton);
        
        // Theme
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            
            const icon = document.getElementById('themeIcon');
            const text = icon.nextElementSibling;
            icon.className = next === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            text.textContent = next === 'dark' ? 'Dark mode' : 'Light mode';
        }
        
        function loadTheme() {
            const saved = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', saved);
            const icon = document.getElementById('themeIcon');
            const text = icon.nextElementSibling;
            icon.className = saved === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
            text.textContent = saved === 'dark' ? 'Dark mode' : 'Light mode';
        }
        
        // Chat functions
        function newChat() {
            sessionId = generateId();
            currentChat = [];
            document.getElementById('chatContainer').innerHTML = `
                <div class="welcome-screen" id="welcomeScreen">
                    <div class="welcome-logo"><i class="fas fa-database"></i></div>
                    <h1 class="welcome-title">How can I help you today?</h1>
                    <div class="example-grid">
                        <div class="example-card" onclick="setInput('Show all tables in Gold database')">
                            <h4><i class="fas fa-table"></i> Show tables</h4>
                            <p>List all available tables</p>
                        </div>
                        <div class="example-card" onclick="setInput('What are the top 10 customers by sales?')">
                            <h4><i class="fas fa-trophy"></i> Top customers</h4>
                            <p>Find top customers</p>
                        </div>
                        <div class="example-card" onclick="setInput('Generate SQL to find recent orders')">
                            <h4><i class="fas fa-code"></i> Generate SQL</h4>
                            <p>Create SQL queries</p>
                        </div>
                        <div class="example-card" onclick="setInput('Analyze production data trends')">
                            <h4><i class="fas fa-chart-line"></i> Analyze data</h4>
                            <p>Get insights</p>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('userInput').value = '';
            updateSendButton();
            addToHistory('New Chat', sessionId);
        }
        
        function addToHistory(title, id) {
            const history = document.getElementById('chatHistory');
            const item = document.createElement('div');
            item.className = 'chat-item active';
            item.dataset.id = id;
            item.onclick = () => loadChat(id);
            item.innerHTML = `<i class="fas fa-message"></i><span>${title}</span>`;
            
            // Remove active from others
            history.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
            history.insertBefore(item, history.firstChild);
        }
        
        function clearConversations() {
            if (confirm('Clear all conversations?')) {
                document.getElementById('chatHistory').innerHTML = '';
                newChat();
            }
        }
        
        function shareChat() {
            const text = currentChat.map(m => `${m.role}: ${m.content}`).join('\\n');
            navigator.clipboard.writeText(text).then(() => {
                showToast('Chat copied to clipboard');
            });
        }
        
        function showSettings() {
            showToast('Settings coming soon');
        }
        
        function showToast(message) {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                bottom: 100px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 1000;
                border: 1px solid var(--border);
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
        
        // Message functions
        function createMessageElement(role, content = '', isStreaming = false) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            const id = `msg-${generateId()}`;
            div.id = id;
            
            div.innerHTML = `
                <div class="message-avatar">
                    <i class="fas fa-${role === 'user' ? 'user' : 'robot'}"></i>
                </div>
                <div class="message-content">
                    ${isStreaming ? '<div class="typing-indicator"><span></span><span></span><span></span></div>' : '<div class="message-text"></div>'}
                    <div class="message-actions">
                        <button class="action-btn" onclick="copyMessage('${id}')">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                        <button class="action-btn" onclick="regenerateMessage()">
                            <i class="fas fa-rotate"></i> Regenerate
                        </button>
                    </div>
                </div>
            `;
            
            return { element: div, id };
        }
        
        function addMessage(role, content) {
            const chatContainer = document.getElementById('chatContainer');
            const welcome = document.getElementById('welcomeScreen');
            if (welcome) welcome.remove();
            
            const { element } = createMessageElement(role, content, false);
            element.querySelector('.message-text').innerHTML = marked.parse(content);
            
            chatContainer.appendChild(element);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Highlight code
            element.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
                addCopyButton(block.parentElement);
            });
            
            currentChat.push({ role, content });
        }
        
        function addCopyButton(pre) {
            const header = document.createElement('div');
            header.className = 'code-header';
            
            const lang = pre.querySelector('code')?.className?.replace('language-', '') || 'code';
            header.innerHTML = `
                <span class="code-language">${lang}</span>
                <button class="copy-btn" onclick="copyCode(this)">
                    <i class="fas fa-copy"></i> Copy
                </button>
            `;
            
            pre.insertBefore(header, pre.firstChild);
        }
        
        function copyCode(btn) {
            const code = btn.closest('.code-block')?.querySelector('code')?.textContent;
            if (code) {
                navigator.clipboard.writeText(code);
                btn.innerHTML = '<i class="fas fa-check"></i> Copied';
                setTimeout(() => btn.innerHTML = '<i class="fas fa-copy"></i> Copy', 2000);
            }
        }
        
        function copyMessage(id) {
            const text = document.getElementById(id)?.querySelector('.message-text')?.textContent;
            if (text) {
                navigator.clipboard.writeText(text);
                showToast('Copied to clipboard');
            }
        }
        
        function regenerateMessage() {
            showToast('Regenerating...');
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;
            
            // Add user message
            addMessage('user', message);
            
            // Clear input
            input.value = '';
            input.style.height = 'auto';
            updateSendButton();
            
            // Show typing indicator
            const chatContainer = document.getElementById('chatContainer');
            const welcome = document.getElementById('welcomeScreen');
            if (welcome) welcome.remove();
            
            const { element: typingEl, id: typingId } = createMessageElement('assistant', '', true);
            chatContainer.appendChild(typingEl);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            isStreaming = true;
            updateSendButton();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId,
                        history: currentChat.slice(0, -1)
                    })
                });
                
                const data = await response.json();
                
                // Remove typing indicator
                typingEl.remove();
                
                if (data.success) {
                    addMessage('assistant', data.response);
                } else {
                    addMessage('assistant', `Error: ${data.error || 'Something went wrong'}`);
                }
            } catch (error) {
                typingEl.remove();
                addMessage('assistant', `Connection error: ${error.message}. Please try again.`);
            } finally {
                isStreaming = false;
                updateSendButton();
            }
        }
        
        // Configure marked for code highlighting
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            langPrefix: 'language-'
        });
    </script>
</body>
</html>
"""

# ============ PYTHON BACKEND LOGIC ============

# Initialize components
orchestrator = OrchestratorAgent()
user_sessions = {}
llm = KalyaniLangChainLLM()

# Load metadata
METADATA_PATH = Path("/home/robotics/Multi_Agent_System/metadata_md")

def load_metadata():
    """Load all table metadata from markdown files"""
    metadata = {}
    if METADATA_PATH.exists():
        for md_file in METADATA_PATH.glob("*.md"):
            try:
                table_name = md_file.stem
                content = md_file.read_text()
                metadata[table_name] = content
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
    return metadata

def get_relevant_metadata(query: str) -> str:
    """Get relevant metadata based on query keywords"""
    metadata = load_metadata()
    relevant = []
    query_lower = query.lower()
    keywords = query_lower.split()
    
    for table_name, content in metadata.items():
        table_lower = table_name.lower()
        if any(keyword in table_lower or keyword in content.lower() for keyword in keywords):
            relevant.append(f"## {table_name}\\n{content[:500]}...")
    
    return "\\n\\n".join(relevant[:5])

def get_schema_context() -> str:
    """Get database schema context for prompts"""
    metadata = load_metadata()
    if not metadata:
        return "No metadata available"
    tables = list(metadata.keys())[:20]
    return f"Available tables ({len(metadata)} total, showing {len(tables)}):\\n" + "\\n".join([f"- {t}" for t in tables])

def classify_intent(query: str) -> str:
    """Classify user intent based on keywords"""
    query_lower = query.lower()
    sql_keywords = ['select', 'show', 'query', 'find', 'get', 'count', 'list', 'sql', 'table', 'tables']
    schema_keywords = ['schema', 'columns', 'fields', 'structure', 'metadata', 'describe', 'what is', 'how to']
    
    if any(kw in query_lower for kw in sql_keywords):
        return 'sql_query'
    elif any(kw in query_lower for kw in schema_keywords):
        return 'schema_question'
    else:
        return 'general_chat'

def handle_sql_query(query: str, metadata: str, schema: str, session: dict) -> str:
    """Handle SQL query generation and execution"""
    prompt = f"""You are an expert SQL query generator for MSSQL Gold Database.

Available Tables and Schema:
{schema[:2000]}

CRITICAL RULES:
1. ALWAYS use exact table names from the schema
2. ALWAYS specify column names after SELECT
3. Use proper MSSQL T-SQL syntax
4. For date filters: DATEADD(month, -1, GETDATE()) for "last month"
5. End with semicolon
6. NO markdown code blocks in output

User Question: {query}

Generate ONLY the SQL query:"""
    
    try:
        messages = [
            SystemMessage(content="You are a SQL expert. Generate valid T-SQL queries."),
            HumanMessage(content=prompt)
        ]
        result = asyncio.run(llm._agenerate(messages))
        sql_query = result.generations[0].message.content.strip()
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        response = f"Here's the SQL query to answer your question:\\n\\n```sql\\n{sql_query}\\n```\\n\\n"
        return response
    except Exception as e:
        return f"I encountered an error generating the SQL: {e}. Please try rephrasing your question."

def handle_schema_question(query: str, schema: str) -> str:
    """Handle schema-related questions"""
    prompt = f"""You are a database schema expert. Answer based on available schema.

Available Schema:
{schema}

User Question: {query}

Provide a clear, helpful answer about the database schema."""
    
    try:
        messages = [
            SystemMessage(content="You are a helpful database schema assistant."),
            HumanMessage(content=prompt)
        ]
        result = asyncio.run(llm._agenerate(messages))
        return result.generations[0].message.content
    except Exception as e:
        return f"I can see the database has tables like ActualCapacityDecember2025, Dim_Customer, Fact_Sales, etc. What would you like to know?"

def handle_general_chat(query: str, metadata: str, schema: str, session: dict) -> str:
    """Handle general chat with full context"""
    history_text = ""
    if session.get('history'):
        recent = session['history'][-4:]
        for msg in recent:
            history_text += f"{msg['role'].title()}: {msg['content']}\\n"
    
    sophie_prompt = f"""You are Sophie, an AI Database Assistant at Kalyani Group.

Database Context:
{schema[:1000]}

Relevant Metadata:
{metadata[:1000]}

Conversation History:
{history_text}

Current Question: {query}

Respond as a helpful, professional database assistant."""
    
    try:
        messages = [
            SystemMessage(content=sophie_prompt),
            HumanMessage(content=query)
        ]
        result = asyncio.run(llm._agenerate(messages))
        return result.generations[0].message.content
    except Exception as e:
        return f"I'm here to help with your database questions. I can generate SQL queries, explain schema, or analyze data. What would you like to explore?"

# ============ FLASK ROUTES ============

@app.route('/')
def home():
    """Render the ChatGPT-style interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with full context"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if session_id not in user_sessions:
            user_sessions[session_id] = {'history': []}
        
        session = user_sessions[session_id]
        metadata_context = get_relevant_metadata(user_message)
        schema_context = get_schema_context()
        
        intent = classify_intent(user_message)
        
        if intent == 'sql_query':
            response_text = handle_sql_query(user_message, metadata_context, schema_context, session)
        elif intent == 'schema_question':
            response_text = handle_schema_question(user_message, schema_context)
        else:
            response_text = handle_general_chat(user_message, metadata_context, schema_context, session)
        
        session['history'].append({'role': 'user', 'content': user_message})
        session['history'].append({'role': 'assistant', 'content': response_text})
        
        return jsonify({
            'success': True,
            'response': response_text,
            'session_id': session_id,
            'intent': intent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'chatgpt-chatbot'})

@app.route('/metadata', methods=['GET'])
def get_metadata():
    """Get all available metadata tables"""
    metadata = load_metadata()
    return jsonify({'success': True, 'tables': list(metadata.keys()), 'count': len(metadata)})

if __name__ == '__main__':
    print("="*60)
    print("Kalyani Database Assistant - ChatGPT Style")
    print("="*60)
    print("Starting server at http://localhost:8080")
    print("Features: SQL Generation, Schema Analysis, Metadata Integration")
    print("="*60)
    print()
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
