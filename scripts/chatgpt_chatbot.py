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
from loguru import logger

from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.llm_manager import llm_manager
from app.config import get_database_config
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from app.agents.chain_of_agents import AgentOrchestrator

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
            --sidebar-width: 280px;
            --header-height: 60px;
            --input-height: 70px;
        }
        
        [data-theme="dark"] {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-sidebar: #252525;
            --bg-hover: #3a3a3a;
            --text-primary: #e8eaed;
            --text-secondary: #9aa0a6;
            --accent: #8ab4f8;
            --accent-hover: #669df6;
            --border: #3c4043;
            --code-bg: #1e1e1e;
            --success: #81c995;
            --warning: #f28b82;
            --shadow: rgba(0, 0, 0, 0.2);
        }
        
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-sidebar: #f1f3f4;
            --bg-hover: #e8eaed;
            --text-primary: #202124;
            --text-secondary: #5f6368;
            --accent: #1a73e8;
            --accent-hover: #1557b0;
            --border: #dadce0;
            --code-bg: #f8f9fa;
            --success: #188038;
            --warning: #d93025;
            --shadow: rgba(0, 0, 0, 0.08);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            font-size: 15px;
            line-height: 1.6;
        }
        
        button, .chat-item, .new-chat-btn, .nav-btn {
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 16px;
            gap: 8px;
            flex-shrink: 0;
        }
        
        .new-chat-btn {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
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
            gap: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text-primary);
            overflow: hidden;
        }
        
        .chat-item:hover {
            background: var(--bg-hover);
        }
        
        .chat-item.active {
            background: var(--bg-hover);
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
            max-width: 100%;
            overflow-x: hidden;
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
            overflow-x: hidden;
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
        
        /* Messages - Redesigned for robustness */
        .message {
            display: flex;
            gap: 12px;
            padding: 16px 10%;
            border-bottom: 1px solid var(--border);
            max-width: 100%;
        }
        
        .message.user {
            background: var(--bg-primary);
        }
        
        .message.assistant {
            background: var(--bg-primary);
        }
        
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: var(--accent);
            color: white;
        }
        
        .message.assistant .message-avatar {
            background: var(--text-secondary);
            color: white;
        }
        
        .message-content {
            flex: 1;
            font-size: 15px;
            line-height: 1.6;
            min-width: 0;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
        }
        
        .message-text {
            max-width: 100%;
            overflow-x: hidden;
        }
        
        .message-content p {
            margin-bottom: 12px;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        /* Message Actions */
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
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .action-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        .message-text pre {
            background: var(--code-bg);
            border-radius: 8px;
            margin: 16px 0;
            border: 1px solid var(--border);
            padding: 0;
            max-width: 100%;
            overflow-x: auto;
            box-sizing: border-box;
        }
        
        .message-text pre code {
            display: block;
            padding: 16px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 14px;
            line-height: 1.5;
            background: transparent;
            max-width: 100%;
            box-sizing: border-box;
        }
        
        .message-text code {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 14px;
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
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
            display: none;
            justify-content: space-between;
            align-items: center;
            padding: 8px 16px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid var(--border);
        }
        
        .code-block:hover .code-header {
            display: flex;
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
            padding: 16px 10%;
            border-top: 1px solid var(--border);
            background: var(--bg-primary);
        }
        
        .input-wrapper {
            display: flex;
            gap: 8px;
            align-items: center;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 8px 12px;
        }
        
        .input-wrapper:focus-within {
            border-color: var(--accent);
        }
        
        .input-wrapper input,
        .input-wrapper textarea {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 15px;
            padding: 8px;
            resize: none;
        }
        
        .input-wrapper input::placeholder,
        .input-wrapper textarea::placeholder {
            color: var(--text-secondary);
        }
        
        .send-btn {
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 50%;
            background: var(--accent);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        
        .send-btn:hover:not(:disabled) {
            background: var(--accent-hover);
        }
        
        .send-btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            opacity: 0.5;
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
        
        /* Collapsible SQL Section - Fixed */
        details.sql-collapsible {
            background: var(--bg-secondary);
            border-radius: 8px;
            margin: 12px 0;
            border: 1px solid var(--border);
            overflow: hidden;
            max-width: 100%;
            width: 100%;
            box-sizing: border-box;
            min-width: 0;
        }
        
        details.sql-collapsible summary {
            padding: 10px 14px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
            list-style: none;
            display: flex;
            align-items: center;
            gap: 8px;
            user-select: none;
            -webkit-user-select: none;
        }

        details.sql-collapsible summary .sql-summary {
            color: var(--text-secondary);
        }
        
        details.sql-collapsible summary::-webkit-details-marker {
            display: none;
        }
        
        details.sql-collapsible summary::before {
            content: '▶';
            font-size: 10px;
            color: var(--text-secondary);
            transition: transform 0.2s;
        }
        
        details.sql-collapsible[open] summary::before {
            content: '▼';
        }
        
        details.sql-collapsible summary:hover {
            background: var(--bg-hover);
        }
        
        details.sql-collapsible pre {
            margin: 0;
            border-radius: 0;
            border-top: 1px solid var(--border);
            max-height: 400px;
            overflow-x: auto;
            overflow-y: auto;
            white-space: pre;
            word-wrap: normal;
            width: 100%;
            box-sizing: border-box;
            max-width: 100%;
            min-width: 0;
            display: block;
        }
        
        details.sql-collapsible pre code {
            display: block;
            padding: 16px;
            background: transparent;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 13px;
            line-height: 1.5;
            white-space: pre;
            width: 100%;
            box-sizing: border-box;
            max-width: 100%;
            min-width: 0;
        }
        
        /* Table Navigation */
        .table-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
            max-width: 100%;
        }
        
        .table-wrapper {
            overflow-x: auto;
            max-width: 100%;
            display: block;
        }
        
        .table-wrapper table {
            width: auto;
            min-width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            table-layout: auto;
        }
        
        .table-wrapper th,
        .table-wrapper td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 250px;
        }
        
        .table-wrapper th {
            background: var(--bg-secondary);
            font-weight: 500;
            color: var(--text-primary);
            position: sticky;
            top: 0;
            font-size: 13px;
        }
        
        .table-wrapper tr:hover {
            background: var(--bg-hover);
        }
        
        .table-wrapper tr:last-child td {
            border-bottom: none;
        }
        
        .table-container > table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        .table-container > table th,
        .table-container > table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 250px;
        }
        
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }
        
        .table-nav {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .nav-btn {
            width: 32px;
            height: 32px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: transparent;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
        }
        
        .nav-btn:hover:not(:disabled) {
            background: var(--bg-hover);
        }
        
        .nav-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .page-indicator {
            font-size: 13px;
            color: var(--text-secondary);
            padding: 0 4px;
        }
        
        .table-footer {
            padding: 8px 16px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-secondary);
            text-align: center;
        }
        
        .exec-time {
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: normal;
        }
        
        /* Table Container Scrollbar Styles */
        .table-container::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        .table-container::-webkit-scrollbar-track {
            background: var(--bg-primary);
            border-radius: 4px;
        }
        
        .table-container::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        .table-container::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        /* Table Styling - Professional */
        .message-text table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
            background: var(--bg-secondary);
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .message-text table thead {
            background: linear-gradient(135deg, var(--bg-hover) 0%, var(--bg-secondary) 100%);
        }
        
        .message-text table th {
            padding: 12px 14px;
            text-align: left;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }
        
        .message-text table td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
            vertical-align: middle;
        }
        
        .message-text table tr:hover {
            background: rgba(74, 158, 255, 0.05);
        }
        
        .message-text table tr:last-child td {
            border-bottom: none;
        }
        
        .message-text table td {
            color: var(--text-secondary);
        }
        
        /* Results Count Badge */
        .results-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: var(--success);
            color: white;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 12px;
        }
        
        .results-badge.warning {
            background: var(--warning);
            color: var(--text-primary);
        }
        
        /* Ensure content fits */
        .message-content {
            max-width: 100%;
            overflow-x: hidden;
        }
        
        .message-text {
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .message { padding: 16px; }
            .input-container { padding: 12px 16px; }
            .example-grid { grid-template-columns: 1fr; }
            .message-text table {
                font-size: 12px;
            }
            .message-text table th,
            .message-text table td {
                padding: 6px 8px;
            }
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
                    <span>Kalyani Warehouse Agent</span>
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
                        <span class="ai-badge">AI</span>
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
                    <textarea class="input-field" id="userInput" placeholder="" rows="1" onkeydown="handleKeyDown(event)" oninput="autoResize(this)"></textarea>
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
                    ${role === 'user' ? '<i class="fas fa-user"></i>' : '<span class="ai-badge">AI</span>'}
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

            // Initialize pagination for any rendered result tables
            element.querySelectorAll('.table-container').forEach((container) => {
                const table = container.querySelector('table');
                if (!table) return;

                const pageSizeAttr = container.getAttribute('data-page-size');
                const pageSize = pageSizeAttr ? parseInt(pageSizeAttr) : 10;
                if (!Number.isFinite(pageSize) || pageSize <= 0) return;

                const rows = table.querySelectorAll('tr');
                if (!rows || rows.length === 0) return;

                // Keep the header row (index 0) always visible; paginate remaining rows
                rows.forEach((row, idx) => {
                    if (idx === 0) {
                        row.style.display = '';
                        return;
                    }
                    const dataIdx = idx - 1;
                    row.style.display = dataIdx < pageSize ? '' : 'none';
                });
            });
            
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
            // Copy button disabled for cleaner UI display
            // The code block is now displayed without header
            return;
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
        
        // Table pagination function
        function changePage(btn, direction) {
            const nav = btn.closest('.table-nav');
            const container = btn.closest('.table-container');
            const indicator = nav.querySelector('.page-indicator');
            
            if (!indicator) return;
            
            const match = indicator.textContent.match(/Page (\d+) of (\d+)/);
            if (!match) return;
            
            let currentPage = parseInt(match[1]);
            const totalPages = parseInt(match[2]);
            
            currentPage += direction;
            if (currentPage < 1) currentPage = 1;
            if (currentPage > totalPages) currentPage = totalPages;
            
            // Update indicator
            indicator.textContent = `Page ${currentPage} of ${totalPages}`;
            
            // Update button states
            nav.querySelectorAll('.nav-btn')[0].disabled = currentPage === 1;
            nav.querySelectorAll('.nav-btn')[1].disabled = currentPage === totalPages;
            
            // Get the table
            const table = container.querySelector('table');
            if (!table) return;
            
            const pageSizeAttr = container.getAttribute('data-page-size');
            const pageSize = pageSizeAttr ? parseInt(pageSizeAttr) : 10;
            const effectivePageSize = (Number.isFinite(pageSize) && pageSize > 0) ? pageSize : 10;

            // Pandas markdown tables may not include <tbody>, so paginate using all <tr>
            const rows = table.querySelectorAll('tr');
            if (!rows || rows.length === 0) return;

            const startIdx = (currentPage - 1) * effectivePageSize;
            const endIdx = currentPage * effectivePageSize;
            
            // Show/hide rows based on current page
            rows.forEach((row, idx) => {
                if (idx === 0) {
                    row.style.display = '';
                    return;
                }

                const dataIdx = idx - 1;
                if (dataIdx >= startIdx && dataIdx < endIdx) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
            
            // Update showing text
            const header = container.querySelector('.table-header strong');
            if (header) {
                const totalRowsMatch = header.textContent.match(/of (\d+) rows/);
                if (totalRowsMatch) {
                    const totalRows = parseInt(totalRowsMatch[1]);
                    const startRow = (currentPage - 1) * effectivePageSize + 1;
                    const endRow = Math.min(currentPage * effectivePageSize, totalRows);
                    const timeInfo = header.querySelector('.exec-time')?.outerHTML || '';
                    header.innerHTML = `Query Results (showing ${startRow}-${endRow} of ${totalRows} rows)${timeInfo}`;
                }
            }
            
            showToast(`Page ${currentPage} of ${totalPages}`);
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
agent_orchestrator = AgentOrchestrator()  # Chain of Agents
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
    
    sql_keywords = ['select', 'show', 'query', 'find', 'get', 'count', 'list', 'sql', 'table', 'tables', 
                    'production', 'sales', 'revenue', 'orders', 'customers', 'capacity', 'inventory',
                    'month', 'week', 'year', 'daily', 'total', 'average', 'sum', 'max', 'min', 'top',
                    'recent', 'last', 'this', 'current', 'data', 'report', 'analytics', 'metrics']
    schema_keywords = ['schema', 'columns', 'fields', 'structure', 'metadata', 'describe', 'what is', 'how to']
    
    if any(kw in query_lower for kw in sql_keywords):
        return 'sql_query'
    elif any(kw in query_lower for kw in schema_keywords):
        return 'schema_question'
    else:
        return 'general_chat'

def extract_sql_from_response(content: str) -> str:
    """Extract SQL query from LLM response, removing thinking and explanations"""
    # Remove thinking tags if present
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'.*?(SELECT|WITH|INSERT|UPDATE|DELETE)', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract code blocks
    code_block_match = re.search(r'```sql\s*(.*?)```', content, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    code_block_match = re.search(r'```\s*(.*?)```', content, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # Extract SQL query - look for SELECT, WITH, etc.
    sql_pattern = re.search(r'(SELECT\s+.*?;)', content, re.DOTALL | re.IGNORECASE)
    if sql_pattern:
        return sql_pattern.group(1).strip()
    
    # If no SQL pattern found, return cleaned content
    lines = content.strip().split('\n')
    sql_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.lower().startswith(('here', 'okay', 'first', 'let', 'this', 'the', 'i ', 'wait', 'hmm', 'maybe', 'but', 'therefore', 'so ', 'yes', 'no ')):
            sql_lines.append(line)
    
    return ' '.join(sql_lines) if sql_lines else content.strip()

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
7. NO explanations, thinking, or reasoning - ONLY the SQL query
8. Output MUST start with SELECT, WITH, INSERT, UPDATE, or DELETE

User Question: {query}

Generate ONLY the SQL query, nothing else:"""
    
    try:
        messages = [
            SystemMessage(content="You are a SQL expert. Generate valid T-SQL queries ONLY. Never include thinking, explanations, or markdown. Output raw SQL only."),
            HumanMessage(content=prompt)
        ]
        result = asyncio.run(llm._agenerate(messages))
        raw_content = result.generations[0].message.content.strip()
        
        # Extract SQL using the extraction function
        sql_query = extract_sql_from_response(raw_content)
        
        # Execute the query and get results
        try:
            from app.database import SQLExecutor
            executor = SQLExecutor()
            result_data = asyncio.run(executor.execute_query(sql_query))
            
            if result_data.get('success'):
                data = result_data.get('data', [])
                columns = result_data.get('columns', [])
                if data and len(data) > 0:
                    # Format results as markdown table
                    import pandas as pd
                    df = pd.DataFrame(data)
                    result_table = df.to_markdown(index=False)
                    response = f"**Query Results ({len(data)} rows):**\n\n```sql\n{sql_query}\n```\n\n{result_table}"
                else:
                    response = f"Query executed successfully but returned no results.\n\n```sql\n{sql_query}\n```"
            else:
                error_msg = result_data.get('error', 'Unknown error')
                
                # Fallback: If asking for tables and DB is down, show metadata
                if 'table' in query.lower() and ('information_schema' in sql_query.lower() or 'table_name' in sql_query.lower() or 'sys.tables' in sql_query.lower() or 'from sys' in sql_query.lower()):
                    metadata = load_metadata()
                    if metadata:
                        table_list = list(metadata.keys())
                        tables_md = "\n".join([f"- {t}" for t in sorted(table_list)])
                        response = f"**Available Tables (from metadata - {len(table_list)} total):**\n\n```sql\n{sql_query}\n```\n\n*Note: Database is currently unavailable, showing cached metadata:*\n\n{tables_md}"
                    else:
                        response = f"SQL query generated:\n\n```sql\n{sql_query}\n```\n\n*Database unavailable and no metadata cached*"
                else:
                    response = f"SQL query generated:\n\n```sql\n{sql_query}\n```\n\n*Error executing query: {error_msg}*"
                
        except Exception as exec_err:
            # If execution fails, still show the SQL
            response = f"Here's the SQL query:\n\n```sql\n{sql_query}\n```\n\n*Note: Could not execute query - {exec_err}*"
        
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
    """Handle chat requests using Chain of Agents (unified endpoint)"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Get or create session history
        if session_id not in user_sessions:
            user_sessions[session_id] = {'history': []}
        
        session = user_sessions[session_id]
        
        # Process through Chain of Agents
        state = asyncio.run(agent_orchestrator.process_query(
            query=user_message,
            session_id=session_id,
            conversation_history=session['history']
        ))
        
        # Update session history
        session['history'].append({'role': 'user', 'content': user_message})
        session['history'].append({'role': 'assistant', 'content': state.final_response})
        
        # Build response
        response_data = {
            'success': True,
            'response': state.final_response,
            'session_id': session_id,
            'intent': state.intent.value if state.intent else None,
            'intent_confidence': state.intent_confidence,
            'selected_tables': state.selected_tables,
            'generated_sql': state.generated_sql,
            'execution_success': state.execution_success,
            'row_count': state.row_count,
            'visualization_needed': state.visualization_needed,
            'visualization_type': state.visualization_type.value,
            'processing_time_ms': state.processing_time_ms,
            'agent_trace': state.agent_trace
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Chain of Agents error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'chatgpt-chatbot'})

@app.route('/chat/v2', methods=['POST'])
def chat_v2():
    """Handle chat requests using Chain of Agents architecture"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Get or create session history
        if session_id not in user_sessions:
            user_sessions[session_id] = {'history': []}
        
        session = user_sessions[session_id]
        
        # Process through Chain of Agents
        state = asyncio.run(agent_orchestrator.process_query(
            query=user_message,
            session_id=session_id,
            conversation_history=session['history']
        ))
        
        # Update session history
        session['history'].append({'role': 'user', 'content': user_message})
        session['history'].append({'role': 'assistant', 'content': state.final_response})
        
        # Build response
        response_data = {
            'success': True,
            'response': state.final_response,
            'session_id': session_id,
            'intent': state.intent.value if state.intent else None,
            'intent_confidence': state.intent_confidence,
            'selected_tables': state.selected_tables,
            'generated_sql': state.generated_sql,
            'execution_success': state.execution_success,
            'row_count': state.row_count,
            'visualization_needed': state.visualization_needed,
            'visualization_type': state.visualization_type.value,
            'processing_time_ms': state.processing_time_ms,
            'agent_trace': state.agent_trace
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Chain of Agents error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
