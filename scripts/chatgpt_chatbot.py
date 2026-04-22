#!/usr/bin/env python3
"""
DWH Quality Agent - ChatGPT-Style Interface
A modern, unified chatbot for DWH quality monitoring, SQL assistance, and agentic insights.
"""

import asyncio
import os
import sys
import html
import csv
import io
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context, redirect, url_for
import json
import logging
import sys
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import threading
import queue
import time
from loguru import logger

from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.llm_manager import llm_manager
from app.config import get_database_config
from app.database import SQLExecutor
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from app.agents.chain_of_agents import AgentOrchestrator

load_dotenv()

app = Flask(__name__)

# ============ SYSTEM PROMPTS ============

SOPHIE_SYSTEM_PROMPT = """You are the DWH Quality Agent, an expert data quality assistant for a multi-layer MSSQL warehouse.

Your capabilities:
1. Monitor bronze, silver, and gold layer data quality
2. Generate SQL queries from natural language
3. Analyze schema drift, stored procedures, freshness, and volume metrics
4. Help with table structure and metadata understanding
5. Route complex requests to the appropriate agent

Warehouse and metadata context:
{schema_context}

When answering:
- Be precise, concise, and helpful
- If you generate SQL, explain what it does
- For quality issues, summarize the most important findings first
- If uncertain, ask a clarifying question
- Prefer DWH quality terminology over product-specific branding

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
    <title>DWH Quality Agent</title>
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

        .footer-btn.button-link {
            color: var(--text);
            background: transparent;
            justify-content: flex-start;
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
<body data-theme="{{ theme }}">
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
                    <span>DWH Quality Agent</span>
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
                    <h1 class="welcome-title">How can I help with data quality today?</h1>
                    
                    <div class="example-grid">
                        <div class="example-card" onclick="setInput('Check bronze layer quality')">
                            <h4><i class="fas fa-table"></i> Check quality</h4>
                            <p>Review layer-level quality metrics</p>
                        </div>
                        <div class="example-card" onclick="setInput('Monitor stored procedures')">
                            <h4><i class="fas fa-trophy"></i> Monitor SPs</h4>
                            <p>Track stored procedure changes and performance</p>
                        </div>
                        <div class="example-card" onclick="setInput('Detect schema changes')">
                            <h4><i class="fas fa-code"></i> Schema drift</h4>
                            <p>Detect new tables, columns, and schema changes</p>
                        </div>
                        <div class="example-card" onclick="setInput('Show quality metrics for silver layer')">
                            <h4><i class="fas fa-chart-line"></i> Layer metrics</h4>
                            <p>Inspect table metrics and quality scores</p>
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
                    <h1 class="welcome-title">How can I help with data quality today?</h1>
                    <div class="example-grid">
                        <div class="example-card" onclick="setInput('Check bronze layer quality')">
                            <h4><i class="fas fa-table"></i> Check quality</h4>
                            <p>Review layer-level quality metrics</p>
                        </div>
                        <div class="example-card" onclick="setInput('Monitor stored procedures')">
                            <h4><i class="fas fa-trophy"></i> Monitor SPs</h4>
                            <p>Track stored procedure changes and performance</p>
                        </div>
                        <div class="example-card" onclick="setInput('Detect schema changes')">
                            <h4><i class="fas fa-code"></i> Schema drift</h4>
                            <p>Detect new tables, columns, and schema changes</p>
                        </div>
                        <div class="example-card" onclick="setInput('Show quality metrics for silver layer')">
                            <h4><i class="fas fa-chart-line"></i> Layer metrics</h4>
                            <p>Inspect table metrics and quality scores</p>
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

        function getSidebarCollapsedState() {
            try {
                return localStorage.getItem('dwh-sidebar-collapsed-v1') === '1';
            } catch (error) {
                return false;
            }
        }

        function setSidebarCollapsedState(collapsed) {
            try {
                localStorage.setItem('dwh-sidebar-collapsed-v1', collapsed ? '1' : '0');
            } catch (error) {
                // Ignore storage issues.
            }
        }

        function applySidebarState(collapsed) {
            const sidebar = document.querySelector('.sidebar');
            const toggleBtn = document.getElementById('sidebarToggleBtn');
            const toggleIcon = document.getElementById('sidebarToggleIcon');
            if (!sidebar || !toggleBtn) {
                return;
            }
            sidebar.classList.toggle('is-collapsed', collapsed);
            sidebar.style.width = collapsed ? '92px' : '';
            sidebar.style.paddingLeft = collapsed ? '12px' : '';
            sidebar.style.paddingRight = collapsed ? '12px' : '';
            if (toggleIcon) {
                toggleIcon.textContent = collapsed ? '☰' : '❮';
            }
            toggleBtn.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
            toggleBtn.setAttribute('title', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
            toggleBtn.setAttribute('aria-expanded', String(!collapsed));
        }

        function initSidebarToggle() {
            const toggleBtn = document.getElementById('sidebarToggleBtn');
            if (!toggleBtn) {
                return;
            }
            const initialCollapsed = getSidebarCollapsedState();
            applySidebarState(initialCollapsed);
            toggleBtn.addEventListener('click', () => {
                const sidebar = document.querySelector('.sidebar');
                const collapsed = !(sidebar && sidebar.classList.contains('is-collapsed'));
                setSidebarCollapsedState(collapsed);
                applySidebarState(collapsed);
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

# Daily monitoring dashboard state
SCHEDULE_FILE = project_root / "config" / "dwh_quality_schedule.json"
DEFAULT_SCHEDULE_CONFIG = {
    "enabled": True,
    "time": "02:00",
    "timezone": "Local",
    "layers": ["silver", "gold"],
    "checks": ["nulls", "duplicates", "freshness", "schema_drift", "stored_procedures"],
}

dashboard_lock = threading.Lock()
schedule_config: Dict[str, Any] = {}
runtime_state: Dict[str, Any] = {
    "running": False,
    "last_run_at": None,
    "last_status": "idle",
    "last_score": None,
    "last_message": "Ready to run",
    "next_run_at": None,
}
run_history: List[Dict[str, Any]] = []
scheduler_thread_started = False


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _copy_default_schedule() -> Dict[str, Any]:
    return {
        "enabled": DEFAULT_SCHEDULE_CONFIG["enabled"],
        "time": DEFAULT_SCHEDULE_CONFIG["time"],
        "timezone": DEFAULT_SCHEDULE_CONFIG["timezone"],
        "layers": list(DEFAULT_SCHEDULE_CONFIG["layers"]),
        "checks": list(DEFAULT_SCHEDULE_CONFIG["checks"]),
    }


def _load_schedule_config() -> Dict[str, Any]:
    config = _copy_default_schedule()
    if SCHEDULE_FILE.exists():
        try:
            loaded = json.loads(SCHEDULE_FILE.read_text())
            if isinstance(loaded, dict):
                for key in config:
                    if key in loaded:
                        if key in {"layers", "checks"} and isinstance(loaded[key], list):
                            config[key] = [str(item) for item in loaded[key]]
                        elif key == "enabled":
                            config[key] = _bool(loaded[key])
                        else:
                            config[key] = loaded[key]
        except Exception as e:
            logger.warning(f"Could not load dashboard schedule file: {e}")
    return config


def _save_schedule_config_locked() -> None:
    try:
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCHEDULE_FILE.write_text(json.dumps(schedule_config, indent=2, sort_keys=True))
    except Exception as e:
        logger.warning(f"Could not save dashboard schedule file: {e}")


def _compute_next_run(schedule_time: str, reference: Optional[datetime] = None) -> str:
    now = reference or datetime.now()
    try:
        hour, minute = [int(part) for part in schedule_time.split(":", 1)]
    except Exception:
        hour, minute = 2, 0

    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run.isoformat(timespec="seconds")


def _refresh_next_run_locked(reference: Optional[datetime] = None) -> None:
    if schedule_config.get("enabled", False):
        runtime_state["next_run_at"] = _compute_next_run(schedule_config.get("time", "02:00"), reference)
    else:
        runtime_state["next_run_at"] = None


def _normalize_selection(values: Any, allowed: List[str], fallback: List[str]) -> List[str]:
    if not isinstance(values, list):
        return list(fallback)
    normalized = [str(v) for v in values if str(v) in allowed]
    return normalized or list(fallback)


def _normalize_theme(value: Any) -> str:
    theme = str(value or 'dark').strip().lower()
    return theme if theme in {'dark', 'light'} else 'dark'


def _normalize_dashboard_view(value: Any) -> str:
    view = str(value or 'quality').strip().lower()
    return view if view in {'quality', 'refresh', 'sp', 'intel'} else 'quality'


def _find_latest_gold_report(history: List[Dict[str, Any]]) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    for item in history:
        if not isinstance(item, dict):
            continue
        report = item.get('report')
        if _extract_gold_metrics(report):
            return report, item.get('checked_at')
    return None, None


def _build_quality_check_query(config: Dict[str, Any], target_layer: Optional[str] = None) -> str:
    layers = [layer for layer in ["bronze", "silver", "gold"] if layer in config.get("layers", [])]
    checks = config.get("checks", [])

    if target_layer == "gold":
        query = "Check gold layer quality"
        return query + "."

    if len(layers) == 1:
        query = f"Check {layers[0]} layer quality"
    elif layers == ["silver", "gold"]:
        query = "Run a comprehensive data quality check across silver and gold layers"
    else:
        query = f"Run a comprehensive data quality check across {', '.join(layers)} layers" if layers else "Run a comprehensive data quality check across silver and gold layers"

    if "stored_procedures" in checks:
        query += ", monitor stored procedures"
    if "schema_drift" in checks:
        query += ", detect schema changes"
    if "freshness" in checks:
        query += ", check data freshness"
    if "nulls" in checks:
        query += ", analyze null values"
    if "duplicates" in checks:
        query += ", detect duplicates"

    return query + "."


def _summarize_quality_report(report: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "check_type": report.get("check_type", "comprehensive"),
        "status": report.get("overall_status") or report.get("status") or "unknown",
        "quality_score": None,
        "issues_found": 0,
        "tables_checked": 0,
        "message": report.get("message", ""),
    }

    if summary["check_type"] == "comprehensive":
        stats = report.get("summary", {}) if isinstance(report.get("summary", {}), dict) else {}
        summary["quality_score"] = stats.get("avg_quality_score")
        summary["issues_found"] = report.get("total_issues", 0)
        summary["tables_checked"] = report.get("layers_checked", 0)
        summary["message"] = f"{summary['issues_found']} total issues across all layers"
    elif "layer" in report:
        summary["quality_score"] = report.get("quality_score")
        summary["issues_found"] = report.get("issues_found", 0)
        summary["tables_checked"] = report.get("tables_checked", 0)
        summary["message"] = f"{summary['issues_found']} issues found in {report.get('layer', 'layer')}"
    elif summary["check_type"] == "stored_procedures":
        summary["issues_found"] = report.get("new_sps", 0) + report.get("modified_sps", 0) + report.get("performance_issues", 0)
        summary["message"] = f"{summary['issues_found']} stored procedure alerts"
    elif summary["check_type"] == "schema_changes":
        summary["issues_found"] = report.get("total_changes", 0)
        summary["message"] = f"{summary['issues_found']} schema changes detected"

    return summary


def _build_run_record(trigger: str, query: str, response_text: str, report: Dict[str, Any]) -> Dict[str, Any]:
    summary = _summarize_quality_report(report)
    checked_at = datetime.now().isoformat(timespec="seconds")
    return {
        "id": uuid.uuid4().hex[:8],
        "trigger": trigger,
        "checked_at": checked_at,
        "query": query,
        "status": summary["status"],
        "quality_score": summary["quality_score"],
        "issues_found": summary["issues_found"],
        "tables_checked": summary["tables_checked"],
        "message": summary["message"],
        "check_type": summary["check_type"],
        "response": response_text,
        "report": report,
    }


def _extract_gold_metrics(report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not report:
        return []

    nested_report = report.get("report") if isinstance(report, dict) else None
    if isinstance(nested_report, dict):
        nested_metrics = _extract_gold_metrics(nested_report)
        if nested_metrics:
            return nested_metrics

    direct_metrics = report.get("metrics")
    if isinstance(direct_metrics, list) and direct_metrics:
        return direct_metrics

    layer_reports = report.get("layer_reports") or {}
    gold_layer_report = layer_reports.get("gold") if isinstance(layer_reports, dict) else None
    if isinstance(gold_layer_report, dict):
        gold_metrics = gold_layer_report.get("metrics")
        if isinstance(gold_metrics, list):
            return gold_metrics

    return []


GOLD_TABLE_PAGE_SIZE = 15
REFRESH_TABLE_PAGE_SIZE = 15
SORTABLE_GOLD_COLUMNS = {
    'table',
    'layer',
    'rows',
    'column_count',
    'pk_fk',
    'quality_score',
    'issue_columns',
    'issues',
}


def _normalize_sort_column(value: Optional[str]) -> str:
    sort_column = str(value or 'quality_score').strip()
    return sort_column if sort_column in SORTABLE_GOLD_COLUMNS else 'quality_score'


def _normalize_sort_direction(value: Optional[str]) -> str:
    return 'desc' if str(value or '').strip().lower() in {'desc', 'descending', 'down', 'reverse'} else 'asc'


REFRESH_SORTABLE_COLUMNS = {
    'procedure_name',
    'execution_date',
    'status',
}


def _normalize_refresh_sort_column(value: Optional[str]) -> str:
    sort_column = str(value or 'execution_date').strip()
    return sort_column if sort_column in REFRESH_SORTABLE_COLUMNS else 'execution_date'


def _parse_refresh_datetime(value: Any) -> Optional[datetime]:
    text = _format_refresh_cell_value(value).strip()
    if not text or text == '—':
        return None

    candidates = [text, text.replace('Z', '+00:00')]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            continue

    for fmt in (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
    ):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _refresh_sort_value(item: Dict[str, Any], sort_by: str) -> Any:
    raw_value = item.get(sort_by)
    text_value = _format_refresh_cell_value(raw_value).lower()

    if sort_by == 'execution_date':
        parsed = _parse_refresh_datetime(raw_value)
        if parsed is not None:
            return (0, parsed.timestamp(), text_value)
        return (1, text_value)

    if sort_by == 'status':
        status_rank = {
            'ended': 0,
            'complete': 0,
            'completed': 0,
            'success': 0,
            'succeeded': 0,
            'finished': 0,
            'failed': 1,
            'failure': 1,
            'error': 1,
        }
        return (status_rank.get(text_value, 2), text_value)

    return text_value


def _sort_refresh_records(records: List[Dict[str, Any]], sort_by: str, sort_dir: str) -> List[Dict[str, Any]]:
    normalized_sort_by = _normalize_refresh_sort_column(sort_by)
    normalized_sort_dir = _normalize_sort_direction(sort_dir)
    reverse = normalized_sort_dir == 'desc'
    return sorted(records, key=lambda item: _refresh_sort_value(item, normalized_sort_by), reverse=reverse)


def _normalize_procedure_key(raw_name: str) -> str:
    name = raw_name.strip().lower()
    if '.' in name:
        name = name.rsplit('.', 1)[-1]
    name = name.strip('[]')
    if name.startswith('sp__'):
        name = name[4:]
    elif name.startswith('sp_'):
        name = name[3:]
    return name


def _dedupe_refresh_records_by_latest(records: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
    latest_by_key: Dict[str, Tuple[Tuple[int, float, int], Dict[str, Any]]] = {}
    for index, record in enumerate(records):
        summary = _extract_refresh_summary(columns, record)
        raw_name = (
            summary.get('procedure_name')
            or summary.get('table_name')
            or summary.get('execution_date')
            or f'row-{index}'
        )
        procedure_key = _normalize_procedure_key(raw_name)
        parsed_execution = _parse_refresh_datetime(summary.get('execution_date'))
        record_rank = (
            1 if parsed_execution is not None else 0,
            parsed_execution.timestamp() if parsed_execution is not None else 0.0,
            -index,
        )
        display_record = {
            'procedure_name': summary.get('procedure_name') or summary.get('table_name') or '—',
            'execution_date': summary.get('execution_date') or '—',
            'status': summary.get('status') or summary.get('stage') or '—',
        }
        existing = latest_by_key.get(procedure_key)
        if existing is None or record_rank > existing[0]:
            latest_by_key[procedure_key] = (record_rank, display_record)

    return [entry[1] for entry in sorted(latest_by_key.values(), key=lambda item: item[0], reverse=True)]


def _count_issue_entries(item: Dict[str, Any]) -> int:
    issues = item.get('issues') if isinstance(item.get('issues'), list) else []
    count = len([issue for issue in issues if str(issue).strip()])
    column_issues = item.get('column_issues') if isinstance(item.get('column_issues'), dict) else {}
    count += sum(1 for problems in column_issues.values() if problems)
    return count


def _format_column_issue_summary(column_issues: Any) -> str:
    if not isinstance(column_issues, dict) or not column_issues:
        return 'None'

    summaries = []
    for column_name, problems in column_issues.items():
        if isinstance(problems, list):
            problem_text = '; '.join(str(problem).strip() for problem in problems if str(problem).strip()) or 'Issue detected'
        else:
            problem_text = str(problems).strip() or 'Issue detected'
        summaries.append(f"{column_name} ({problem_text})")

    return '; '.join(summaries) or 'None'


def _format_table_issue_summary(item: Dict[str, Any]) -> str:
    issues = [str(issue).strip() for issue in (item.get('issues') if isinstance(item.get('issues'), list) else []) if str(issue).strip()]
    if issues:
        return '; '.join(issues)

    column_issues = item.get('column_issues') if isinstance(item.get('column_issues'), dict) else {}
    if column_issues:
        return _format_column_issue_summary(column_issues)

    return 'Healthy'


def _sort_gold_metrics(
    metrics: List[Dict[str, Any]],
    sort_by: str = 'quality_score',
    sort_dir: str = 'asc',
) -> List[Dict[str, Any]]:
    sort_by = _normalize_sort_column(sort_by)
    sort_dir = _normalize_sort_direction(sort_dir)

    def _score_value(item: Dict[str, Any]) -> float:
        score = item.get('quality_score')
        try:
            return float(score)
        except (TypeError, ValueError):
            return float('inf')

    def _int_value(item: Dict[str, Any], field: str) -> float:
        value = item.get(field)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float('inf')

    def _text_value(item: Dict[str, Any], field: str) -> str:
        return str(item.get(field) or '').lower()

    def _pk_fk_value(item: Dict[str, Any]) -> str:
        pk_value = _format_metric_values(item.get('pk_columns'))
        fk_value = _format_metric_values(item.get('fk_columns'))
        return f'{pk_value} {fk_value}'.strip().lower()

    def _column_issue_count(item: Dict[str, Any]) -> float:
        column_issues = item.get('column_issues') if isinstance(item.get('column_issues'), dict) else {}
        return float(sum(1 for problems in column_issues.values() if problems))

    def _issues_value(item: Dict[str, Any]) -> tuple:
        return (_count_issue_entries(item), _format_table_issue_summary(item).lower())

    def _key(item: Dict[str, Any]):
        if sort_by == 'quality_score':
            primary = _score_value(item)
        elif sort_by == 'rows':
            primary = _int_value(item, 'rows')
        elif sort_by == 'column_count':
            primary = _int_value(item, 'column_count')
        elif sort_by == 'pk_fk':
            primary = _pk_fk_value(item)
        elif sort_by == 'issue_columns':
            primary = (_column_issue_count(item), _format_column_issue_summary(item.get('column_issues')).lower())
        elif sort_by == 'issues':
            primary = _issues_value(item)
        else:
            primary = _text_value(item, sort_by)

        secondary = _text_value(item, 'table')
        return primary, secondary

    return sorted(metrics, key=_key, reverse=(sort_dir == 'desc'))


def _format_metric_values(value: Any) -> str:
    if isinstance(value, list):
        cleaned = []
        for entry in value:
            if entry is None:
                continue
            if isinstance(entry, dict):
                cleaned.append(str(entry.get("column") or entry.get("name") or entry.get("value") or entry))
            else:
                cleaned.append(str(entry))
        return ", ".join(item for item in cleaned if item) or "-"
    if value is None:
        return "-"
    text = str(value).strip()
    return text or "-"


def _render_gold_metric_rows(metrics: List[Dict[str, Any]]) -> str:
    if not metrics:
        return '<tr><td colspan="8" style="color: var(--muted);">No Gold tables found in the latest run.</td></tr>'

    rows = []
    for item in metrics:
        table_name = html.escape(str(item.get("table") or "—"))
        layer_name = html.escape(str(item.get("layer") or "gold"))
        rows_count = html.escape(str(item.get("rows", "—")))
        col_count = html.escape(str(item.get("column_count", "—")))
        pk_columns = _format_metric_values(item.get("pk_columns"))
        fk_columns = _format_metric_values(item.get("fk_columns"))
        issue_columns_map = item.get("column_issues") if isinstance(item.get("column_issues"), dict) else {}

        issue_columns = ', '.join(map(str, issue_columns_map.keys())) or 'None'
        issues = _format_table_issue_summary(item)
        quality_score = item.get("quality_score")
        quality_score_text = f"{quality_score}%" if quality_score is not None else '—'

        rows.append(
            "<tr>"
            f"<td>{table_name}</td>"
            f"<td><span class=\"layer-tag\">{layer_name}</span></td>"
            f"<td>{rows_count}</td>"
            f"<td>{col_count}</td>"
            f"<td><div class=\"pkfk-block\"><div><span class=\"kv-label\">PK</span> {html.escape(pk_columns)}</div><div><span class=\"kv-label\">FK</span> {html.escape(fk_columns)}</div></div></td>"
            f"<td>{html.escape(quality_score_text)}</td>"
            f"<td>{html.escape(issue_columns)}</td>"
            f"<td>{html.escape(issues)}</td>"
            "</tr>"
        )

    return "\n".join(rows)


def _refresh_status_class(value: Any) -> str:
    status = _format_refresh_cell_value(value).strip().lower()
    if not status:
        return 'status-idle'
    if 'ended' in status or status in {'complete', 'completed', 'success', 'succeeded', 'finished'}:
        return 'status-ended'
    if 'fail' in status or 'error' in status:
        return 'status-failed'
    if 'run' in status or 'progress' in status or 'pending' in status:
        return 'status-warning'
    return 'status-idle'


def _render_refresh_table_headers(columns: List[Dict[str, str]], sort_by: str, sort_dir: str, sort_urls: Dict[str, str]) -> str:
    if not columns:
        return '<th>Value</th>'

    headers = []
    for column in columns:
        column_key = column.get('key', '')
        column_label = column.get('label', column_key)
        sort_url = html.escape(str(sort_urls.get(column_key, '#')), quote=True)
        active = sort_by == column_key
        arrow = f" {'↑' if sort_dir == 'asc' else '↓'}" if active else ''
        sort_class = ' is-active' if active else ''
        headers.append(
            '<th>'
            f'<div class="header-cell"><a class="sort-link{sort_class}" href="{sort_url}">{html.escape(str(column_label))}{arrow}</a></div>'
            '</th>'
        )
    return ''.join(headers)


def _render_refresh_table_rows(columns: List[Dict[str, str]], records: List[Dict[str, Any]]) -> str:
    if not columns:
        return '<tr><td colspan="1" style="color: var(--muted);">No columns available.</td></tr>'

    if not records:
        return f'<tr><td colspan="{len(columns)}" style="color: var(--muted);">No refresh rows found.</td></tr>'

    rows = []
    for record in records:
        cells = []
        for column in columns:
            column_key = column.get('key', '')
            value = record.get(column_key) if isinstance(record, dict) else None
            if column_key == 'status':
                status_text = html.escape(_format_refresh_cell_value(value))
                status_class = _refresh_status_class(value)
                cells.append(f'<td><span class="status-pill {status_class}">{status_text}</span></td>')
            else:
                cells.append(f'<td>{html.escape(_format_refresh_cell_value(value))}</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")

    return "\n".join(rows)


def _render_refresh_summary_rows(execution_date: str, stage: str) -> str:
    return (
        '<tr>'
        f'<td>{html.escape(str(execution_date or "—"))}</td>'
        f'<td>{html.escape(str(stage or "—"))}</td>'
        '</tr>'
    )


def _render_generic_table_headers(columns: List[str]) -> str:
    if not columns:
        return '<th>Value</th>'
    return ''.join(f'<th>{html.escape(str(column))}</th>' for column in columns)


def _quote_sql_identifier(value: Any) -> str:
    return f"[{str(value).replace(']', ']]')}]"


def _format_refresh_cell_value(value: Any) -> str:
    if value is None:
        return '—'
    if isinstance(value, (dict, list, tuple)):
        try:
            text = json.dumps(value, default=str, ensure_ascii=False)
        except Exception:
            text = str(value)
    else:
        text = str(value)
    text = text.strip()
    return text or '—'


def _find_ssis_logs_table() -> Optional[Dict[str, str]]:
    executor = SQLExecutor()
    query = """
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
      AND UPPER(TABLE_NAME) LIKE '%SSIS%'
    ORDER BY
        CASE WHEN UPPER(TABLE_NAME) = 'SSIS' THEN 0 ELSE 1 END,
        CASE WHEN UPPER(TABLE_NAME) LIKE '%LOG%' THEN 0 ELSE 1 END,
        CASE WHEN UPPER(TABLE_NAME) LIKE '%REFRESH%' THEN 0 ELSE 1 END,
        TABLE_SCHEMA,
        TABLE_NAME;
    """
    result = asyncio.run(executor.execute_query(query))
    if not result.get('success') or not result.get('data'):
        return None

    first_row = result['data'][0]
    if isinstance(first_row, dict):
        schema_name = first_row.get('TABLE_SCHEMA') or first_row.get('table_schema') or 'dbo'
        table_name = first_row.get('TABLE_NAME') or first_row.get('table_name')
    else:
        schema_name = first_row[0] if len(first_row) > 0 else 'dbo'
        table_name = first_row[1] if len(first_row) > 1 else None

    if not table_name:
        return None

    return {'schema': str(schema_name or 'dbo'), 'table': str(table_name)}


def _pick_refresh_order_column(column_names: List[str]) -> Optional[str]:
    priority_fragments = [
        'executiontime',
        'execution_date',
        'executiondate',
        'starttime',
        'start_date',
        'startdate',
        'created_at',
        'created',
        'modified_at',
        'modified',
        'logdate',
        'log_time',
        'logtime',
        'timestamp',
        'datetime',
        'date',
        'time',
    ]
    lowered = [str(column).lower() for column in column_names]
    for fragment in priority_fragments:
        for index, column in enumerate(lowered):
            if fragment in column:
                return column_names[index]
    return None


def _load_ssis_refresh_table(limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
    table_info = _find_ssis_logs_table()
    if not table_info:
        return None

    executor = SQLExecutor()
    schema_name = table_info['schema']
    table_name = table_info['table']

    columns_query = f"""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{schema_name.replace("'", "''")}'
      AND TABLE_NAME = '{table_name.replace("'", "''")}'
    ORDER BY ORDINAL_POSITION;
    """
    columns_result = asyncio.run(executor.execute_query(columns_query))
    if not columns_result.get('success') or not columns_result.get('data'):
        return None

    column_names: List[str] = []
    for row in columns_result['data']:
        if isinstance(row, dict):
            column_name = row.get('COLUMN_NAME') or row.get('column_name')
        else:
            column_name = row[0] if row else None
        if column_name:
            column_names.append(str(column_name))

    if not column_names:
        return None

    order_column = _pick_refresh_order_column(column_names)
    select_sql = f"SELECT * FROM {_quote_sql_identifier(schema_name)}.{_quote_sql_identifier(table_name)}"
    if limit is not None and int(limit) > 0:
        select_sql = f"SELECT TOP {int(limit)} * FROM {_quote_sql_identifier(schema_name)}.{_quote_sql_identifier(table_name)}"
    if order_column:
        select_sql += f" ORDER BY {_quote_sql_identifier(order_column)} DESC"

    rows_result = asyncio.run(executor.execute_query(select_sql))
    if not rows_result.get('success'):
        return None

    records = rows_result.get('data') or []
    output_columns = [str(column) for column in (rows_result.get('columns') or column_names)]

    display_records = _dedupe_refresh_records_by_latest(records, output_columns)
    display_records = _sort_refresh_records(display_records, sort_by='execution_date', sort_dir='desc')

    return {
        'source': f'{schema_name}.{table_name}',
        'columns': ['procedure_name', 'execution_date', 'status'],
        'records': display_records,
        'row_count': len(display_records),
        'order_column': order_column,
    }


SP_ANALYSIS_PAGE_SIZE = 15
SORTABLE_SP_COLUMNS = {'sp_name', 'schema_name', 'last_modified', 'parameter_count', 'quality_score'}

_sp_analysis_cache: Optional[Dict[str, Any]] = None
_sp_llm_cache: Dict[str, Dict[str, Any]] = {}
_sp_cache_lock = threading.Lock()


def _analyze_sp_rules(name: str, definition: str) -> tuple:
    """Query-level rule-based SP quality check. Returns (score, issues_list)."""
    if not definition:
        return None, ['Definition not accessible — grant VIEW DEFINITION to enable code analysis']
    issues: List[str] = []
    score = 100
    defn = definition.upper()

    # --- Session settings ---
    if 'SET NOCOUNT ON' not in defn:
        issues.append('Missing SET NOCOUNT ON — causes extra network roundtrips')
        score -= 8
    if 'SET XACT_ABORT ON' not in defn:
        issues.append('Missing SET XACT_ABORT ON — transactions may leave locks on error')
        score -= 5

    # --- Error handling ---
    if 'BEGIN TRY' not in defn:
        issues.append('No TRY/CATCH block — errors will propagate silently')
        score -= 12

    # --- Query anti-patterns ---
    if re.search(r'SELECT\s+\*', defn):
        issues.append('SELECT * used — specify columns to avoid schema-drift issues')
        score -= 10
    if re.search(r'LIKE\s+[\'"]%', defn):
        issues.append('Leading wildcard LIKE — causes full index/table scan')
        score -= 8
    if re.search(r'\bOR\b', defn):
        issues.append('OR in WHERE/JOIN — can prevent index seeks; consider UNION ALL')
        score -= 5
    if re.search(r'\bCONVERT\s*\(|\bCAST\s*\(', defn):
        implicit = re.findall(r'(?:CONVERT|CAST)\s*\([^)]{0,80}\)', defn)
        if len(implicit) > 3:
            issues.append(f'Frequent CONVERT/CAST ({len(implicit)}x) — may cause implicit conversion scans')
            score -= 5
    if re.search(r'NOT\s+IN\s*\(\s*SELECT', defn):
        issues.append('NOT IN (subquery) — use NOT EXISTS for better NULL-safety and performance')
        score -= 8
    if re.search(r'\bORDER\s+BY\b(?!.*\bTOP\b)(?!.*\bROW_NUMBER\b)(?!.*\bRANK\b)', defn):
        issues.append('ORDER BY without TOP/ROW_NUMBER — sorting entire result set is expensive')
        score -= 5

    # --- Cursor & loops ---
    if 'DECLARE' in defn and 'CURSOR' in defn:
        issues.append('CURSOR used — prefer set-based operations for performance')
        score -= 12
    if re.search(r'\bWHILE\b', defn):
        issues.append('WHILE loop detected — consider set-based alternatives')
        score -= 8

    # --- Dynamic SQL ---
    if re.search(r'\bEXEC\s*\(|\bEXECUTE\s*\(|SP_EXECUTESQL', defn):
        issues.append('Dynamic SQL — verify for injection risk and plan cache pollution')
        score -= 8

    # --- Locking ---
    nolock = defn.count('NOLOCK')
    if nolock > 3:
        issues.append(f'Excessive NOLOCK hints ({nolock}x) — risk of dirty reads')
        score -= 5

    # --- Temp objects ---
    if re.search(r'SELECT\s+.{0,80}INTO\s+#', defn):
        issues.append('SELECT INTO #temp — consider table variables for small sets')
        score -= 3

    # --- Complexity ---
    line_count = definition.count('\n')
    if line_count > 300:
        issues.append(f'Large procedure ({line_count} lines) — consider refactoring')
        score -= 5
    elif line_count > 150:
        issues.append(f'Moderate size ({line_count} lines) — review for splitting opportunities')
        score -= 2

    return max(0, score), issues


def _fetch_sp_definitions() -> List[Dict[str, Any]]:
    """Fetch all SPs with metadata and definitions from SQL Server."""
    executor = SQLExecutor()
    meta_query = """
    SELECT
        r.ROUTINE_SCHEMA,
        r.ROUTINE_NAME,
        r.LAST_ALTERED,
        (SELECT COUNT(*) FROM INFORMATION_SCHEMA.PARAMETERS p
         WHERE p.SPECIFIC_SCHEMA = r.ROUTINE_SCHEMA
           AND p.SPECIFIC_NAME = r.ROUTINE_NAME
           AND p.PARAMETER_MODE IS NOT NULL) AS param_count
    FROM INFORMATION_SCHEMA.ROUTINES r
    WHERE r.ROUTINE_TYPE = 'PROCEDURE'
    ORDER BY r.ROUTINE_SCHEMA, r.ROUTINE_NAME;
    """
    result = asyncio.run(executor.execute_query(meta_query))
    if not result.get('success') or not result.get('data'):
        return []

    sps = []
    for row in result['data']:
        if isinstance(row, dict):
            schema = str(row.get('ROUTINE_SCHEMA') or row.get('routine_schema') or '')
            name = str(row.get('ROUTINE_NAME') or row.get('routine_name') or '')
            last_altered = row.get('LAST_ALTERED') or row.get('last_altered')
            param_count = int(row.get('param_count') or row.get('PARAM_COUNT') or 0)
        else:
            schema, name, last_altered, param_count = (row[0] or ''), (row[1] or ''), row[2], int(row[3] or 0)

        if not name:
            continue

        def_result = asyncio.run(executor.execute_query(
            f"SELECT OBJECT_DEFINITION(OBJECT_ID('[{schema}].[{name}]'));"
        ))
        definition = ''
        if def_result.get('success') and def_result.get('data'):
            d = def_result['data'][0]
            raw = list(d.values())[0] if isinstance(d, dict) else d[0]
            definition = str(raw) if raw else ''

        rule_score, issues = _analyze_sp_rules(name, definition)
        quality_score = 0 if rule_score is None else rule_score

        sps.append({
            'sp_name': f'{schema}.{name}',
            'schema_name': schema,
            'name_only': name,
            'last_modified': str(last_altered) if last_altered else '—',
            'parameter_count': param_count,
            'quality_score': quality_score,
            'issues': issues,
            'definition': definition[:6000] if definition else '',
            'llm_analysis': None,
        })

    return sps


def _load_sp_analysis(force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Return SP analysis records, using cache unless force_refresh."""
    global _sp_analysis_cache
    with _sp_cache_lock:
        if not force_refresh and _sp_analysis_cache is not None:
            return _sp_analysis_cache
    records = _fetch_sp_definitions()
    if not records:
        return None
    result = {
        'records': records,
        'row_count': len(records),
        'fetched_at': datetime.now().isoformat(timespec='seconds'),
    }
    with _sp_cache_lock:
        _sp_analysis_cache = result
    return result


def _sort_sp_records(records: List[Dict[str, Any]], sort_by: str = 'quality_score', sort_dir: str = 'asc') -> List[Dict[str, Any]]:
    sort_by = sort_by if sort_by in SORTABLE_SP_COLUMNS else 'quality_score'
    reverse = sort_dir == 'desc'
    if sort_by in ('quality_score', 'parameter_count'):
        return sorted(records, key=lambda r: (float(r.get(sort_by) or 0)), reverse=reverse)
    return sorted(records, key=lambda r: str(r.get(sort_by) or '').lower(), reverse=reverse)


def _extract_llm_item(item) -> str:
    """Coerce an LLM list item (str or dict) to a plain string."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ('text', 'description', 'recommendation', 'issue', 'message', 'content'):
            if item.get(key):
                return str(item[key])
        return '; '.join(f'{k}: {v}' for k, v in item.items() if v)
    return str(item)


def _render_sp_table_rows(records: List[Dict[str, Any]]) -> str:
    rows_html = []
    for rec in records:
        score = rec.get('quality_score', 0)
        if score >= 80:
            score_cls = 'score-high'
        elif score >= 50:
            score_cls = 'score-med'
        else:
            score_cls = 'score-low'
        score_display = f'{score}%' if score is not None else 'N/A'
        issues = rec.get('issues') or []
        issues_html_parts = []
        for iss in issues:
            issues_html_parts.append(f'<span class="issue-tag">{html.escape(iss)}</span>')
        issues_text = ''.join(issues_html_parts) if issues_html_parts else '<span style="color:#22c55e">No issues detected</span>'
        llm = rec.get('llm_analysis')
        if llm:
            llm_recs = llm.get('recommendations') or []
            llm_issues = llm.get('issues') or []
            if not isinstance(llm_recs, list): llm_recs = [llm_recs]
            if not isinstance(llm_issues, list): llm_issues = [llm_issues]
            parts = [html.escape(_extract_llm_item(r)) for r in llm_recs if r]
            if not parts:
                parts = [html.escape(_extract_llm_item(i)) for i in llm_issues if i]
            llm_cell = '<br>'.join(f'<span class="issue-tag" style="background:var(--primary-light,#e0f2fe);color:var(--primary,#0369a1)">{p}</span>' for p in parts) if parts else '<span style="color:#22c55e">✓ Clean</span>'
        else:
            llm_cell = '<span style="color:var(--muted)">—</span>'
        sp_name_safe = html.escape(rec.get('sp_name') or '')
        sp_name_js = rec.get('sp_name', '').replace("'", "\\'")
        analyze_btn = f'<button onclick="showSpDetail(\'{sp_name_js}\')" class="btn-sp-analyze" title="View definition &amp; AI analysis">🔍 Analyze</button>'
        rows_html.append(
            f'<tr>'
            f'<td>{sp_name_safe}</td>'
            f'<td>{html.escape(rec.get("schema_name") or "")}</td>'
            f'<td style="white-space:nowrap">{html.escape(str(rec.get("last_modified") or "—"))}</td>'
            f'<td style="text-align:center">{html.escape(str(rec.get("parameter_count") or 0))}</td>'
            f'<td><span class="score-pill {score_cls}">{score_display}</span></td>'
            f'<td class="issue-cell">{issues_text}</td>'
            f'<td class="issue-cell">{llm_cell}</td>'
            f'<td style="text-align:center">{analyze_btn}</td>'
            f'</tr>'
        )
    return '\n'.join(rows_html)



# ---------------------------------------------------------------------------
# Table Intelligence pane
# ---------------------------------------------------------------------------
INTEL_PAGE_SIZE = 12
_METADATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'metadata_md')
_intel_cache: Optional[Dict[str, Any]] = None
_intel_cache_lock = threading.Lock()


def _parse_bus_matrix() -> Dict[str, str]:
    """Return {table_name_lower: grain_description} parsed from bus_matrix.md."""
    grains: Dict[str, str] = {}
    bus_matrix_path = os.path.join(_METADATA_DIR, 'bus_matrix.md')
    try:
        text = Path(bus_matrix_path).read_text(encoding='utf-8')
    except OSError:
        return grains
    current_table = None
    for line in text.splitlines():
        m = re.search(r'`((?:Fact|Dim|FT)_\w+)`', line)
        if m:
            current_table = m.group(1).lower()
        if current_table and line.strip().startswith('**Grain:**'):
            grain = line.strip().replace('**Grain:**', '').strip()
            grains[current_table] = grain
    return grains


def _parse_single_md(path: str, grains: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse one metadata .md file into a table-intel record."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError:
        return None
    # Table name + type from header
    m = re.search(r'##\s+(Fact|Dimension|FT)\s+Table:\s+`([^`]+)`', text, re.I)
    if not m:
        m2 = re.search(r'##\s+`([^`]+)`', text)
        if not m2:
            return None
        raw_name = m2.group(1)
        tbl_type = 'Fact' if raw_name.lower().startswith('fact') else 'Dimension' if raw_name.lower().startswith('dim') else 'Other'
    else:
        tbl_type = 'Fact' if m.group(1).lower().startswith('fact') else 'Dimension'
        raw_name = m.group(2)

    if '.' in raw_name:
        schema, table_name = raw_name.split('.', 1)
    else:
        schema = 'BFL'
        table_name = raw_name

    # Columns with mode/sample values
    columns: List[Dict[str, str]] = []
    for col_match in re.finditer(
        r'[*\-]\s+`(\w+)`\s+\(([^)]+)\)(.*?)(?=\n[*\-]\s+`|\Z)', text, re.S
    ):
        col_name = col_match.group(1)
        col_type = col_match.group(2).strip()
        col_detail = col_match.group(3)
        mode_m = re.search(r'\*\*(?:Mode \d+ values|All Values)[^:]*:\*\*\s*`([^`]{0,200})`', col_detail)
        sample = mode_m.group(1).strip() if mode_m else ''
        columns.append({'name': col_name, 'type': col_type, 'sample': sample})

    # Related dimensions
    rel_dims: List[str] = []
    in_related = False
    for line in text.splitlines():
        if '**Related Dimensions:**' in line:
            in_related = True
            continue
        if in_related:
            if line.strip().startswith('-'):
                dim_m = re.search(r'(Dim_\w+|Fact_\w+)', line)
                if dim_m:
                    rel_dims.append(dim_m.group(1))
            elif line.strip() and not line.strip().startswith('-'):
                break

    table_key = table_name.lower()
    grain = grains.get(table_key, '')

    return {
        'table_name': table_name,
        'schema': schema,
        'full_name': f'{schema}.{table_name}',
        'table_type': tbl_type,
        'grain': grain,
        'columns': columns,
        'column_count': len(columns),
        'related_dims': rel_dims,
        'row_count': None,
        'sample_rows': [],
        'llm_summary': None,
    }


def _fetch_table_stats(schema: str, table_name: str) -> Dict[str, Any]:
    """Return row_count and up to 3 sample rows for a table."""
    executor = SQLExecutor()
    try:
        cnt_result = asyncio.run(executor.execute_query(
            f"SELECT COUNT(*) AS cnt FROM [{schema}].[{table_name}];"
        ))
        row_count = None
        if cnt_result.get('success') and cnt_result.get('data'):
            d = cnt_result['data'][0]
            raw = list(d.values())[0] if isinstance(d, dict) else d[0]
            row_count = int(raw) if raw is not None else None

        smp_result = asyncio.run(executor.execute_query(
            f"SELECT TOP 3 * FROM [{schema}].[{table_name}];"
        ))
        sample_rows: List[Dict[str, Any]] = []
        if smp_result.get('success') and smp_result.get('data'):
            for row in smp_result['data']:
                if isinstance(row, dict):
                    sample_rows.append({k: str(v) if v is not None else '' for k, v in row.items()})
        return {'row_count': row_count, 'sample_rows': sample_rows}
    except Exception:
        return {'row_count': None, 'sample_rows': []}


def _load_table_intel(force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Load and cache all table metadata + live stats."""
    global _intel_cache
    with _intel_cache_lock:
        if not force_refresh and _intel_cache is not None:
            return _intel_cache

    grains = _parse_bus_matrix()
    records: List[Dict[str, Any]] = []
    md_dir = Path(_METADATA_DIR)
    skip_files = {'bus_matrix.md', 'kg_metadata.md', 'manufacturing.md', 'sales.md',
                  'internet_metadata.md', 'db_owner.md', 'auto_md_generator.py',
                  'generate_sql_schema_info.py', 'excel_to md.py'}
    for md_file in sorted(md_dir.glob('*.md')):
        if md_file.name in skip_files:
            continue
        rec = _parse_single_md(str(md_file), grains)
        if rec is None:
            continue
        stats = _fetch_table_stats(rec['schema'], rec['table_name'])
        rec['row_count'] = stats['row_count']
        rec['sample_rows'] = stats['sample_rows']
        records.append(rec)

    if not records:
        return None
    result = {
        'records': records,
        'total': len(records),
        'fetched_at': datetime.now().isoformat(timespec='seconds'),
    }
    with _intel_cache_lock:
        _intel_cache = result
    return result


def _table_readable_name(table_name: str) -> str:
    """Convert CamelCase/underscore table name to spaced readable form."""
    name = re.sub(r'^(Fact_|Dim_|FT_)', '', table_name)
    name = re.sub(r'([A-Z])', r' \1', name).strip()
    return name


def _auto_description(rec: Dict[str, Any]) -> str:
    """Build a short header description (1 sentence) from metadata."""
    ttype = rec.get('table_type', 'table')
    readable = _table_readable_name(rec.get('table_name', ''))
    row_count = rec.get('row_count')
    size_note = f' ({row_count:,} rows)' if isinstance(row_count, int) else ''
    if ttype == 'Fact':
        return f'Fact table tracking {readable.lower()} data{size_note}.'
    return f'Dimension / lookup table for {readable.lower()}{size_note}.'


def _build_card_summary(rec: Dict[str, Any]) -> str:
    """Generate business insight text for a table card."""
    tn = rec.get('table_name', '').lower()
    ttype = rec.get('table_type', 'Other')
    col_names = [c['name'].lower() for c in (rec.get('columns') or [])]
    row_count = rec.get('row_count')
    size_str = f'{row_count:,} records' if isinstance(row_count, int) else 'records'

    # ── Per-table specific insights ──────────────────────────────────────────
    _INSIGHTS: Dict[str, Dict[str, Any]] = {
        'fact_actualsales': {
            'kpis': 'Revenue by customer, product, plant and channel; gross vs net invoice variance; exchange-rate-adjusted USD revenue.',
            'questions': 'Which products/customers drive the most revenue? How does actual sales compare across plants and distribution channels?',
            'users': 'Finance, Sales, C-suite',
        },
        'fact_plansales_monthly': {
            'kpis': 'Plan vs actual sales gap; monthly forecast accuracy by product and customer.',
            'questions': 'Are we hitting our sales targets? Which segments are under-performing against plan?',
            'users': 'Sales Planning, Finance',
        },
        'fact_manpower': {
            'kpis': 'Headcount by department, grade and location; attendance and absenteeism trends.',
            'questions': 'Which departments are over/under-staffed? How is headcount evolving month-on-month?',
            'users': 'HR, Operations, Plant Managers',
        },
        'ft_employee_details': {
            'kpis': 'Employee tenure, grade distribution, vendor-wise contract headcount.',
            'questions': 'What is the age/grade profile of the workforce? Who are contract vs permanent employees?',
            'users': 'HR, Payroll',
        },
        'fact_downtimewithreasons': {
            'kpis': 'Total downtime hours by reason, line and shift; top breakdown categories; mean time between failures.',
            'questions': 'Which production lines lose the most time? What are the root causes of downtime?',
            'users': 'Production, Maintenance, Plant Managers',
        },
        'fact_maintenanceactivity': {
            'kpis': 'Planned vs actual maintenance time; breakdown frequency; maintenance completion rate.',
            'questions': 'Are maintenance activities completed on schedule? Which equipment requires the most attention?',
            'users': 'Maintenance Team, Plant Managers',
        },
        'fact_oee': {
            'kpis': 'Overall Equipment Effectiveness (Availability × Performance × Quality) by line and date.',
            'questions': 'Which lines are under-performing on OEE? Where are the biggest losses — availability, performance or quality?',
            'users': 'Production, Operations, Plant Managers',
        },
        'fact_forgingscrap': {
            'kpis': 'Scrap quantity and rate by die, line and date; rejection cost impact.',
            'questions': 'Which dies/lines produce the most scrap? Is scrap trending up or down over time?',
            'users': 'Quality, Production',
        },
        'fact_machiningscrap': {
            'kpis': 'Machining scrap rate by line, die and date.',
            'questions': 'Where does machining scrap originate? Which components have the highest rejection rate?',
            'users': 'Quality, Machining Team',
        },
        'fact_forging_dielevel_periodicsnapshot': {
            'kpis': 'Pieces produced per die per shift; die utilisation and yield.',
            'questions': 'How productive is each die? Which dies are under-utilised or nearing end-of-life?',
            'users': 'Production Planning, Tool Room',
        },
        'fact_forging_diesparelevel_accumulatingsnapshot': {
            'kpis': 'Cumulative good/bad pieces per die-spare; die spare lifespan tracking.',
            'questions': 'When should die spares be replaced? What is the total yield from each spare?',
            'users': 'Tool Room, Production',
        },
        'fact_inventory_monthly': {
            'kpis': 'Month-end inventory value and quantity by material, plant and storage location.',
            'questions': 'Where is inventory piling up? Which materials have excess or insufficient stock?',
            'users': 'Supply Chain, Finance, Plant Managers',
        },
        'fact_inventorystoragelocation': {
            'kpis': 'Storage location utilisation; material stock levels.',
            'questions': 'Which storage locations are near capacity? How is stock distributed across plants?',
            'users': 'Warehouse, Supply Chain',
        },
        'fact_procurement': {
            'kpis': 'PO-to-GR cycle time; spend by vendor and material; PR-to-PO conversion rate.',
            'questions': 'Which vendors have the longest lead times? Where is procurement spend concentrated?',
            'users': 'Procurement, Finance',
        },
        'fact_bom': {
            'kpis': 'Component quantity per parent material; BOM completeness and validity periods.',
            'questions': 'What materials make up each product? Are BOM records current and valid?',
            'users': 'Engineering, Production Planning',
        },
        'fact_consumingeneregy': {
            'kpis': 'Daily energy consumption by line; cost per unit of production.',
            'questions': 'Which lines consume the most energy? Is energy consumption correlated with output volume?',
            'users': 'Operations, Sustainability, Finance',
        },
        'fact_requestforquotation_salesforce': {
            'kpis': 'RFQ volume and win rate by customer account; average time-to-quote.',
            'questions': 'How many RFQs convert to orders? Which accounts generate the most business opportunities?',
            'users': 'Sales, Business Development',
        },
        'fact_partrequestforquotation_salesforce': {
            'kpis': 'Part-level RFQ conversion; quoted vs awarded quantities.',
            'questions': 'Which parts are most frequently quoted? What is the win rate at the part level?',
            'users': 'Sales, Engineering',
        },
        'fact_totalproductivemaintenance': {
            'kpis': 'TPM score by SBU and month; planned maintenance compliance.',
            'questions': 'Which SBUs are achieving TPM targets? How is the TPM programme progressing over time?',
            'users': 'Maintenance, Plant Management',
        },
        'fact_assetmonitoring': {
            'kpis': 'Asset availability and condition by plant and location; snapshot-level status trends.',
            'questions': 'Which assets are showing degraded availability? Are critical assets being monitored consistently?',
            'users': 'Asset Management, Plant Managers',
        },
    }

    # Dimension-level insights by keyword
    _DIM_INSIGHTS: List[tuple] = [
        (('customer',), 'Enables segmentation of revenue and RFQs by customer name, region and account type. Used to filter sales reports by customer hierarchy.'),
        (('material', 'product'), 'Supports product-level reporting across sales, inventory and BOM. Helps identify material type mix and valuation class distribution.'),
        (('employee',), 'Powers HR dashboards — headcount by grade, location and vendor. Essential for payroll and workforce planning analysis.'),
        (('plant',), 'Provides plant-level filtering for production, sales and inventory KPIs. Enables cross-plant benchmarking.'),
        (('date',), 'Central time dimension enabling trend analysis, period comparisons and fiscal/calendar hierarchies across all fact tables.'),
        (('equipment', 'maintenance'), 'Links maintenance activities to specific equipment, enabling asset-level downtime and cost tracking.'),
        (('downtime', 'reason'), 'Classifies breakdown events to root-cause level — essential for Pareto analysis of production losses.'),
        (('grade', 'position'), 'Provides HR classification data for compensation analysis, career-ladder reporting and workforce structure.'),
        (('vendor',), 'Supports procurement analysis by vendor — spend, lead times and purchase order volumes.'),
        (('leader', 'sector', 'salesforce'), 'Enables CRM-level reporting — territory performance, leader productivity and pipeline by sector.'),
        (('invoice', 'currency'), 'Supports multi-currency financial reporting and invoice-level reconciliation.'),
        (('storage', 'location'), 'Enables warehouse-level inventory analysis and storage utilisation tracking.'),
        (('die',), 'Core dimension for forging operations — tracks die status, type and usage history.'),
        (('shift',), 'Enables shift-level analysis of production output, downtime and quality metrics.'),
    ]

    # ── Look up specific insight ─────────────────────────────────────────────
    specific = _INSIGHTS.get(tn)
    if specific:
        parts = [
            f'<strong>KPIs enabled:</strong> {specific["kpis"]}',
            f'<strong>Business questions answered:</strong> {specific["questions"]}',
            f'<strong>Primary users:</strong> {specific["users"]} &nbsp;·&nbsp; {size_str}.',
        ]
        return '<br>'.join(parts)

    # ── Dimension fallback ───────────────────────────────────────────────────
    if ttype == 'Dimension':
        for keywords, insight in _DIM_INSIGHTS:
            if any(k in tn for k in keywords):
                return f'{insight} Contains {size_str}.'
        readable = _table_readable_name(rec.get('table_name', ''))
        return (f'Lookup / reference table for {readable.lower()}. '
                f'Use this to add descriptive context to fact table metrics. Contains {size_str}.')

    # ── Generic Fact fallback ────────────────────────────────────────────────
    readable = _table_readable_name(rec.get('table_name', ''))
    measure_cols = [c['name'] for c in (rec.get('columns') or [])
                    if not c['name'].lower().endswith('key')
                    and c['name'].lower() not in ('id',)][:4]
    measures_str = ' · '.join(measure_cols) if measure_cols else 'key measures'
    return (f'Tracks {readable.lower()} with {size_str}. '
            f'Key measures: {measures_str}. '
            f'Combine with related dimensions to slice by time, location or product.')


def _render_intel_cards(records: List[Dict[str, Any]]) -> str:
    """Render one human-readable card per table for the Table Intelligence view."""
    parts: List[str] = []
    for rec in records:
        ttype = rec.get('table_type', 'Other')
        badge_cls = 'badge-fact' if ttype == 'Fact' else 'badge-dim'
        row_count = rec.get('row_count')
        row_count_html = f'{row_count:,}' if isinstance(row_count, int) else '—'
        col_count = rec.get('column_count', 0)

        # Auto description
        description = _auto_description(rec)

        # Grain (only for Fact tables)
        grain = rec.get('grain', '')
        grain_html = (
            f'<div class="intel-grain"><span class="intel-grain-label">Grain:</span> {html.escape(grain)}</div>'
            if grain else ''
        )

        # Column list — show up to 10 with type and sample value in plain English
        cols = rec.get('columns') or []
        col_items = []
        for c in cols[:10]:
            sample = c.get('sample', '').strip()
            sample_part = f'<span class="col-sample">e.g. {html.escape(sample[:60])}</span>' if sample else ''
            col_items.append(
                f'<li><span class="col-name">{html.escape(c["name"])}</span>'
                f'<span class="col-type">{html.escape(c["type"])}</span>'
                f'{sample_part}</li>'
            )
        more_note = f'<li class="col-more-note">… and {col_count - 10} more columns</li>' if col_count > 10 else ''
        cols_html = f'<ul class="intel-col-list">{"".join(col_items)}{more_note}</ul>'

        # Sample data — show as clean key: value pairs
        samples = rec.get('sample_rows') or []
        if samples:
            s = samples[0]
            shown = list(s.items())[:6]
            kv_html = ''.join(
                f'<div class="kv-row"><span class="kv-key">{html.escape(k)}</span>'
                f'<span class="kv-val">{html.escape(str(v)[:60] if v else "—")}</span></div>'
                for k, v in shown
            )
            sample_html = f'<div class="intel-kv-block"><div class="intel-section-label">Sample record</div>{kv_html}</div>'
        else:
            sample_html = '<div class="intel-kv-block muted-text">No sample data — SELECT permission may be required</div>'

        # Related dims
        rel = rec.get('related_dims') or []
        if rel:
            rel_items = ''.join(f'<span class="rel-badge">{html.escape(d)}</span>' for d in rel[:6])
            more_rel = f'<span class="rel-badge rel-more">+{len(rel)-6} more</span>' if len(rel) > 6 else ''
            rel_html = f'<div class="intel-rels"><span class="intel-section-label">Joins to:</span>{rel_items}{more_rel}</div>'
        else:
            rel_html = ''

        # Auto business summary (may contain safe HTML like <strong>)
        summary_text = _build_card_summary(rec)
        summary_html = (
            f'<div class="intel-summary-block">'
            f'<span class="intel-section-label">Business Insights</span>'
            f'{summary_text}'
            f'</div>'
        )

        parts.append(f'''<div class="intel-card" data-table="{html.escape(rec['full_name'].lower())}" data-type="{html.escape(ttype.lower())}">
  <div class="intel-card-header">
    <span class="intel-table-name">{html.escape(rec['full_name'])}</span>
    <span class="intel-badge {badge_cls}">{html.escape(ttype)}</span>
    <span class="intel-meta">{col_count} cols &nbsp;·&nbsp; {row_count_html} rows</span>
  </div>
  {grain_html}
  <details class="intel-details">
    <summary class="intel-details-toggle">Columns ({col_count})</summary>
    {cols_html}
  </details>
  {sample_html}
  {rel_html}
  {summary_html}
</div>''')

    return '\n'.join(parts) if parts else '<p class="muted-text">No table metadata found.</p>'


def _find_column_by_keywords(column_names: List[str], keywords: List[str]) -> Optional[str]:
    lowered_columns = [str(column).lower() for column in column_names]
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for index, lowered_column in enumerate(lowered_columns):
            if keyword_lower in lowered_column:
                return column_names[index]
    return None


def _extract_refresh_summary(columns: List[str], record: Any, order_column: Optional[str] = None) -> Dict[str, str]:
    if isinstance(record, dict):
        row_map = {str(key): value for key, value in record.items()}
    elif isinstance(record, (list, tuple)):
        row_map = {str(columns[index]): record[index] for index in range(min(len(columns), len(record)))}
    else:
        row_map = {}

    table_column = _find_column_by_keywords(
        columns,
        ['table_name', 'tablename', 'target_table', 'source_table', 'object_name', 'entity_name', 'table'],
    )
    procedure_column = _find_column_by_keywords(
        columns,
        ['procedure_name', 'proc_name', 'stored_procedure', 'procedure', 'package_name', 'ssis_package', 'package'],
    )
    execution_column = _find_column_by_keywords(
        columns,
        [
            'execution_date', 'executiondate', 'checked_at', 'checkedat', 'run_date', 'rundate',
            'start_time', 'starttime', 'log_date', 'logdate', 'created_at', 'createdat', 'timestamp',
            'date', 'time'
        ],
    )
    status_column = _find_column_by_keywords(
        columns,
        ['execution_status', 'run_status', 'status', 'state', 'result', 'outcome'],
    )
    stage_column = _find_column_by_keywords(
        columns,
        ['execution_stage', 'stage', 'step_name', 'step', 'status', 'state', 'phase', 'trigger'],
    )

    table_value = row_map.get(table_column) if table_column else None
    procedure_value = row_map.get(procedure_column) if procedure_column else None
    execution_value = row_map.get(execution_column) if execution_column else None
    if execution_value in (None, '') and order_column:
        execution_value = row_map.get(order_column)

    status_value = row_map.get(status_column) if status_column else None
    if status_value in (None, ''):
        status_value = row_map.get(stage_column) if stage_column else None

    stage_value = row_map.get(stage_column) if stage_column else None
    if stage_value in (None, ''):
        stage_value = row_map.get('trigger') or row_map.get('status') or row_map.get('Stage') or row_map.get('stage')

    return {
        'table_name': _format_refresh_cell_value(table_value),
        'procedure_name': _format_refresh_cell_value(procedure_value),
        'execution_date': _format_refresh_cell_value(execution_value),
        'status': _format_refresh_cell_value(status_value),
        'stage': _format_refresh_cell_value(stage_value),
    }


def _render_generic_table_rows(columns: List[str], records: List[Dict[str, Any]]) -> str:
    if not columns:
        return '<tr><td colspan="1" style="color: var(--muted);">No columns available.</td></tr>'

    if not records:
        return f'<tr><td colspan="{len(columns)}" style="color: var(--muted);">No refresh rows found.</td></tr>'

    rows = []
    for record in records:
        cells = []
        for column in columns:
            value = record.get(column) if isinstance(record, dict) else None
            cells.append(f'<td>{html.escape(_format_refresh_cell_value(value))}</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")

    return "\n".join(rows)


def _render_refresh_log_rows(history: List[Dict[str, Any]]) -> str:
    if not history:
        return '<tr><td colspan="7" style="color: var(--muted);">No refresh history found.</td></tr>'

    rows = []
    for item in history:
        checked_at = html.escape(str(item.get('checked_at') or '—'))
        trigger = html.escape(str(item.get('trigger') or 'manual'))
        status = str(item.get('status') or 'unknown').strip().lower() or 'unknown'
        status_label = html.escape(status)
        quality_score = item.get('quality_score')
        quality_score_text = html.escape(f"{quality_score}%" if quality_score is not None else '—')
        issues_found = html.escape(str(item.get('issues_found', 0)))
        tables_checked = html.escape(str(item.get('tables_checked', 0)))
        message = html.escape(str(item.get('message') or '—'))

        rows.append(
            "<tr>"
            f"<td>{checked_at}</td>"
            f"<td>{trigger}</td>"
            f"<td><span class=\"status-pill status-{status_label}\">{status_label}</span></td>"
            f"<td>{quality_score_text}</td>"
            f"<td>{issues_found}</td>"
            f"<td>{tables_checked}</td>"
            f"<td>{message}</td>"
            "</tr>"
        )

    return "\n".join(rows)


def _execute_quality_check(trigger: str = "manual", target_layer: Optional[str] = None) -> Dict[str, Any]:
    with dashboard_lock:
        if runtime_state["running"]:
            return {"success": False, "error": "A quality check is already running."}
        runtime_state["running"] = True
        schedule_snapshot = json.loads(json.dumps(schedule_config))

    query = _build_quality_check_query(schedule_snapshot, target_layer=target_layer)

    try:
        state = asyncio.run(
            agent_orchestrator.process_query(
                query=query,
                session_id=f"dashboard-{trigger}",
                conversation_history=[]
            )
        )
        report = state.response_data.get("quality_report", {}) if hasattr(state, "response_data") else {}
        response_text = getattr(state, "final_response", "") or ""
        run_record = _build_run_record(trigger, query, response_text, report)

        with dashboard_lock:
            run_history.insert(0, run_record)
            runtime_state["last_run_at"] = run_record["checked_at"]
            runtime_state["last_status"] = run_record["status"]
            runtime_state["last_score"] = run_record["quality_score"]
            runtime_state["last_message"] = run_record["message"]
            _refresh_next_run_locked(datetime.now())
            runtime_state["running"] = False
            _save_schedule_config_locked()

        return {"success": True, "run": run_record}

    except Exception as e:
        logger.error(f"Quality check execution failed: {e}")
        with dashboard_lock:
            runtime_state["last_status"] = "error"
            runtime_state["last_message"] = str(e)
            runtime_state["running"] = False
        return {"success": False, "error": str(e)}


def _scheduler_loop() -> None:
    while True:
        time.sleep(30)
        with dashboard_lock:
            enabled = schedule_config.get("enabled", False)
            next_run_at = runtime_state.get("next_run_at")
            running = runtime_state.get("running", False)

        if not enabled or running or not next_run_at:
            continue

        try:
            next_run_dt = datetime.fromisoformat(next_run_at)
        except Exception:
            with dashboard_lock:
                _refresh_next_run_locked(datetime.now())
                _save_schedule_config_locked()
            continue

        if datetime.now() >= next_run_dt:
            _execute_quality_check(trigger="scheduled")


def _start_scheduler_thread() -> None:
    global scheduler_thread_started
    if scheduler_thread_started:
        return
    scheduler_thread_started = True
    thread = threading.Thread(target=_scheduler_loop, name="DWHQualityScheduler", daemon=True)
    thread.start()


with dashboard_lock:
    schedule_config = _load_schedule_config()
    _refresh_next_run_locked(datetime.now())
    _save_schedule_config_locked()

# Load metadata
METADATA_PATH = project_root / "metadata_md"

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
    prompt = f"""You are an expert SQL query generator for the DWH Quality Agent.

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
    
    sophie_prompt = f"""You are the DWH Quality Agent, an AI assistant for warehouse data quality and metadata exploration.

Database Context:
{schema[:1000]}

Relevant Metadata:
{metadata[:1000]}

Conversation History:
{history_text}

Current Question: {query}

Respond as a helpful, professional DWH quality assistant."""
    
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

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality</title>
    <style>
        :root {
            --bg: #0b1020;
            --panel: #111827;
            --border: rgba(255,255,255,0.08);
            --text: #e5e7eb;
            --muted: #94a3b8;
            --accent: #60a5fa;
            --shadow: 0 20px 50px rgba(0,0,0,0.35);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at top left, rgba(96,165,250,0.12), transparent 28%), var(--bg);
            color: var(--text);
        }
        body[data-theme="light"] {
            --bg: #f8fafc;
            --panel: rgba(255,255,255,0.96);
            --border: rgba(15,23,42,0.12);
            --text: #0f172a;
            --muted: #475569;
            --accent: #2563eb;
            --shadow: 0 20px 50px rgba(15,23,42,0.08);
            background: radial-gradient(circle at top left, rgba(37,99,235,0.10), transparent 28%), var(--bg);
        }
        .shell {
            min-height: 100vh;
            padding: 28px;
            display: flex;
            justify-content: center;
        }
        .main {
            width: min(1200px, 100%);
        }
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 26px;
            box-shadow: var(--shadow);
            isolation: isolate;
        }
        h1 {
            margin: 0 0 8px;
            font-size: 30px;
        }
        p {
            margin: 0;
            color: var(--muted);
            line-height: 1.6;
        }
        .toolbar {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 20px;
            margin-bottom: 16px;
            position: relative;
            z-index: 2;
        }
        button,
        .button-link {
            border: 0;
            border-radius: 14px;
            padding: 12px 16px;
            cursor: pointer;
            color: white;
            font-weight: 600;
            position: relative;
            z-index: 3;
            pointer-events: auto;
        }
        .button-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            line-height: 1;
        }
        .sort-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            flex: 1 1 auto;
            min-width: 0;
            color: inherit;
            text-decoration: none;
        }
        .sort-link:hover {
            text-decoration: underline;
        }
        .sort-link.is-active {
            color: var(--accent);
        }
        .primary { background: linear-gradient(135deg, #2563eb, #7c3aed); }
        .secondary { background: rgba(255,255,255,0.08); }
        body[data-theme="light"] .secondary { background: rgba(37,99,235,0.08); color: #0f172a; }
        body[data-theme="light"] .toolbar .button-link,
        body[data-theme="light"] .pager-actions .button-link {
            color: #0f172a;
        }
        body[data-theme="light"] .sidebar-footer .button-link {
            color: #0f172a;
        }
        body[data-theme="light"] .primary { color: #ffffff; }
        body[data-theme="light"] .status { background: rgba(37,99,235,0.08); }
        body[data-theme="light"] table { background: rgba(15,23,42,0.02); }
        body[data-theme="light"] .layer-tag { background: rgba(37,99,235,0.12); color: #1d4ed8; border-color: rgba(37,99,235,0.16); }
        body[data-theme="light"] .sidebar { background: rgba(255,255,255,0.82); }
        body[data-theme="light"] .nav-link.active {
            background: rgba(37,99,235,0.10);
            border-color: rgba(37,99,235,0.18);
        }
        .button-link.is-disabled {
            opacity: 0.45;
            pointer-events: none;
        }
        .app-shell {
            min-height: 100vh;
            display: flex;
            width: 100%;
        }
        .sidebar {
            width: 260px;
            padding: 24px 18px;
            border-right: 1px solid var(--border);
            background: rgba(15,23,42,0.22);
            backdrop-filter: blur(18px);
            display: flex;
            flex-direction: column;
            gap: 18px;
            flex-shrink: 0;
            transition: width 0.25s ease, padding 0.25s ease;
            overflow: hidden;
        }
        .sidebar.is-collapsed {
            width: 92px;
            padding-left: 12px;
            padding-right: 12px;
            overflow: hidden;
        }
        .sidebar.is-collapsed .sidebar-title,
        .sidebar.is-collapsed .sidebar-subtitle,
        .sidebar.is-collapsed .nav-text {
            display: none;
        }
        .sidebar.is-collapsed .sidebar-brand {
            align-items: center;
        }
        .sidebar.is-collapsed .nav-link {
            justify-content: center;
            padding-left: 10px;
            padding-right: 10px;
        }
        .sidebar.is-collapsed .sidebar-footer {
            align-items: stretch;
        }
        .sidebar.is-collapsed .sidebar-footer .button-link {
            justify-content: center;
            width: 100%;
        }
        .sidebar-brand {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }
        .sidebar-title {
            margin: 0;
            font-size: 20px;
            line-height: 1.2;
        }
        .sidebar-subtitle {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.5;
        }
        .sidebar-nav {
            display: grid;
            gap: 8px;
        }
        .nav-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            border-radius: 14px;
            text-decoration: none;
            color: var(--text);
            border: 1px solid transparent;
            transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
        }
        .nav-link:hover {
            background: rgba(96,165,250,0.08);
            transform: translateX(2px);
        }
        .nav-link.active {
            background: rgba(96,165,250,0.14);
            border-color: rgba(96,165,250,0.18);
        }
        .nav-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: var(--accent);
            flex: 0 0 auto;
        }
        .nav-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .nav-label {
            font-weight: 600;
            font-size: 14px;
        }
        .nav-hint {
            font-size: 12px;
            color: var(--muted);
        }
        .sidebar-footer .button-link {
            width: 100%;
        }
        .sidebar-toggle-btn {
            width: 44px;
            height: 44px;
            padding: 0;
            background: rgba(255,255,255,0.06);
            color: var(--text);
            border: 1px solid var(--border);
            text-align: center;
            justify-content: center;
            color: var(--text);
        }
        .sidebar-toggle-btn:hover {
            background: rgba(96,165,250,0.12);
        }
        .sidebar-toggle-icon {
            font-size: 18px;
            line-height: 1;
        }
        .content-area {
            flex: 1;
            padding: 24px;
            min-width: 0;
        }
        .content-shell {
            width: min(1400px, 100%);
            margin: 0 auto;
        }
        .status {
            margin-top: 14px;
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: 14px;
            color: var(--text);
            background: rgba(96,165,250,0.10);
        }
        .meta {
            margin-top: 12px;
            color: var(--muted);
            font-size: 13px;
        }
        .table-wrap {
            overflow-x: auto;
            margin-top: 18px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: rgba(255,255,255,0.02);
        }
        .table-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-top: 14px;
            flex-wrap: wrap;
            position: relative;
            z-index: 2;
        }
        .pager-info {
            color: var(--muted);
            font-size: 13px;
        }
        .pager-actions {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .pager-actions button {
            min-width: 104px;
        }
        .quality-summary-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 14px;
        }
        .qs-card {
            background: var(--card-bg, rgba(255,255,255,0.06));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 16px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 110px;
        }
        .qs-card .qs-value { font-size: 22px; font-weight: 700; line-height: 1.1; }
        .qs-card .qs-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
        .qs-card.healthy .qs-value { color: #22c55e; }
        .qs-card.warning .qs-value { color: #f59e0b; }
        .qs-card.critical .qs-value { color: #ef4444; }
        .qs-card.fact .qs-value { color: var(--primary, #0369a1); }
        .qs-card.dim .qs-value  { color: #8b5cf6; }
        .scoring-info {
            background: var(--card-bg, rgba(255,255,255,0.04));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
            font-size: 12px;
        }
        .scoring-info summary {
            cursor: pointer;
            font-weight: 600;
            font-size: 12px;
            color: var(--muted);
            user-select: none;
            list-style: none;
        }
        .scoring-info summary::before { content: '▶  '; font-size: 10px; }
        .scoring-info[open] summary::before { content: '▼  '; }
        .scoring-info .checks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 8px;
            margin-top: 10px;
        }
        .scoring-info .check-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 8px 10px;
            border-radius: 6px;
            background: var(--hover-bg, rgba(0,0,0,0.04));
        }
        .scoring-info .check-name { font-weight: 600; font-size: 12px; }
        .scoring-info .check-desc { font-size: 11px; color: var(--muted); }
        .scoring-info .check-penalty { font-size: 11px; font-weight: 600; color: #ef4444; }
        .top-pager {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            padding: 6px 0 10px 0;
            flex-wrap: wrap;
        }
        .top-pager .pager-info { font-size: 12px; }
        .btn-sp-analyze {
            background: none;
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--primary, #0369a1);
            cursor: pointer;
            font-size: 12px;
            padding: 3px 8px;
            transition: background 0.15s;
        }
        .btn-sp-analyze:hover { background: var(--hover-bg, rgba(0,0,0,0.06)); }
        .sp-modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.55);
            z-index: 9000;
            align-items: center;
            justify-content: center;
        }
        .sp-modal-overlay.open { display: flex; }
        .sp-modal {
            background: var(--card-bg, #fff);
            border-radius: 10px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.3);
            width: min(860px, 94vw);
            max-height: 88vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .sp-modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            gap: 12px;
        }
        .sp-modal-header h2 { font-size: 15px; margin: 0; word-break: break-all; }
        .sp-modal-close {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 20px;
            color: var(--muted);
            padding: 0 4px;
            line-height: 1;
        }
        .sp-modal-body {
            overflow-y: auto;
            padding: 18px 20px;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .sp-modal-section-title {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: var(--muted);
            margin-bottom: 6px;
        }
        .sp-definition-box {
            background: var(--code-bg, #1e1e2e);
            color: var(--code-fg, #cdd6f4);
            border-radius: 6px;
            padding: 12px 14px;
            font-family: monospace;
            font-size: 12px;
            line-height: 1.55;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 300px;
            overflow-y: auto;
        }
        .sp-llm-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
        .sp-llm-list li { display: flex; gap: 8px; font-size: 13px; }
        .sp-llm-list li::before { content: '→'; color: var(--primary, #0369a1); flex-shrink: 0; }
        .sp-modal-footer {
            padding: 12px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.02);
            table-layout: fixed;
        }
        th, td {
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
            vertical-align: top;
            overflow-wrap: anywhere;
        }
        th {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            position: relative;
            user-select: none;
        }
        tbody tr:hover {
            background: rgba(96,165,250,0.05);
        }
        .quality-table {
            min-width: 1320px;
        }
        .quality-table col:nth-child(1) { width: 230px; }
        .quality-table col:nth-child(2) { width: 100px; }
        .quality-table col:nth-child(3) { width: 90px; }
        .quality-table col:nth-child(4) { width: 90px; }
        .quality-table col:nth-child(5) { width: 240px; }
        .quality-table col:nth-child(6) { width: 120px; }
        .quality-table col:nth-child(7) { width: 280px; }
        .quality-table col:nth-child(8) { width: 300px; }
        .refresh-table col:nth-child(1) { width: 260px; }
        .refresh-table col:nth-child(2) { width: 240px; }
        .refresh-table col:nth-child(3) { width: 220px; }
        .refresh-table {
            min-width: 760px;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .status-healthy { background: rgba(34,197,94,0.12); color: #22c55e; }
        .status-warning { background: rgba(245,158,11,0.12); color: #f59e0b; }
        .status-error { background: rgba(239,68,68,0.12); color: #ef4444; }
        .status-ended { background: rgba(34,197,94,0.12); color: #22c55e; }
        .status-failed { background: rgba(239,68,68,0.12); color: #ef4444; }
        .status-idle { background: rgba(148,163,184,0.12); color: #94a3b8; }
        .score-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
        .score-high { background: rgba(34,197,94,0.15); color: #22c55e; }
        .score-med  { background: rgba(234,179,8,0.15);  color: #eab308; }
        .score-low  { background: rgba(239,68,68,0.15);  color: #ef4444; }
        .issue-cell { font-size: 12px; color: var(--muted); max-width: 380px; word-break: break-word; }
        .issue-tag { display: inline-block; background: rgba(239,68,68,0.1); color: #ef4444; border-radius: 4px; padding: 1px 6px; margin: 1px 2px; font-size: 11px; white-space: normal; }
        .intel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 18px; margin-top: 16px; }
        .intel-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px 22px; display: flex; flex-direction: column; gap: 12px; }
        .intel-card-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .intel-table-name { font-size: 13px; font-weight: 700; color: var(--text); font-family: monospace; }
        .intel-badge { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
        .badge-fact { background: rgba(139,92,246,.15); color: #8b5cf6; }
        .badge-dim  { background: rgba(14,165,233,.15); color: #0ea5e9; }
        .intel-meta { margin-left: auto; font-size: 11px; color: var(--muted); white-space: nowrap; }
        .intel-desc { font-size: 13px; color: var(--text); line-height: 1.6; margin: 0; }
        .intel-grain { font-size: 12px; color: var(--muted); border-left: 3px solid var(--border); padding: 4px 0 4px 10px; }
        .intel-grain-label { font-weight: 600; color: var(--muted); margin-right: 4px; }
        .intel-section-label { display: block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); margin-bottom: 6px; }
        .intel-details { border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
        .intel-details-toggle { font-size: 12px; font-weight: 600; color: var(--muted); padding: 7px 12px; cursor: pointer; list-style: none; user-select: none; }
        .intel-details-toggle::-webkit-details-marker { display: none; }
        .intel-details-toggle::before { content: '▶ '; font-size: 9px; }
        details[open] .intel-details-toggle::before { content: '▼ '; }
        .intel-col-list { margin: 0; padding: 8px 12px 10px; list-style: none; display: flex; flex-direction: column; gap: 5px; }
        .intel-col-list li { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; font-size: 12px; }
        .col-name { font-weight: 600; color: var(--text); min-width: 160px; }
        .col-type { font-size: 10px; color: var(--muted); background: var(--hover); border-radius: 3px; padding: 1px 5px; flex-shrink: 0; }
        .col-sample { font-size: 11px; color: var(--muted); font-style: italic; }
        .col-more-note { color: var(--muted); font-style: italic; }
        .intel-kv-block { background: var(--hover); border-radius: 6px; padding: 10px 14px; }
        .kv-row { display: flex; gap: 10px; align-items: baseline; padding: 3px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
        .kv-row:last-child { border-bottom: none; }
        .kv-key { font-weight: 600; color: var(--muted); min-width: 170px; flex-shrink: 0; }
        .kv-val { color: var(--text); word-break: break-all; }
        .intel-rels { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
        .rel-badge { font-size: 10px; background: rgba(34,197,94,.1); color: #22c55e; border-radius: 4px; padding: 2px 7px; }
        .rel-more { background: var(--hover); color: var(--muted); }
        .intel-summary-block { background: rgba(139,92,246,.07); border-left: 3px solid #8b5cf6; border-radius: 4px; padding: 10px 14px; font-size: 12.5px; color: var(--text); line-height: 1.7; }
        .intel-summary-block strong { color: var(--text); font-weight: 700; }
        .intel-search { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; color: var(--text); font-size: 13px; width: 260px; }
        .intel-filter-row { display: flex; gap: 6px; margin-top: 8px; }
        .intel-filter-btn { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 4px 14px; font-size: 12px; color: var(--muted); cursor: pointer; }
        .intel-filter-btn.active { border-color: #8b5cf6; color: #8b5cf6; background: rgba(139,92,246,.08); }
        .header-cell {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 8px;
            width: 100%;
            min-height: 24px;
            position: relative;
            padding-right: 14px;
        }
        .column-resizer {
            position: absolute;
            top: -6px;
            right: -2px;
            bottom: -6px;
            width: 14px;
            cursor: col-resize;
            flex: 0 0 14px;
            touch-action: none;
            z-index: 2;
        }
        .column-resizer::after {
            content: '';
            position: absolute;
            top: 18%;
            bottom: 18%;
            right: 5px;
            width: 3px;
            border-radius: 999px;
            background: var(--border);
            transition: background 0.2s ease;
        }
        .header-cell:hover .column-resizer::after {
            background: var(--accent);
        }
        .layer-tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(96,165,250,0.15);
            color: #bfdbfe;
            font-size: 12px;
            border: 1px solid rgba(96,165,250,0.2);
        }
        .pkfk-block {
            display: grid;
            gap: 4px;
            line-height: 1.35;
            white-space: normal;
        }
        .kv-label {
            display: inline-block;
            min-width: 28px;
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .page-header {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: flex-start;
            flex-wrap: wrap;
        }
        .page-kicker {
            margin: 0 0 8px;
            color: var(--accent);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }
        @media (max-width: 720px) {
            .app-shell { flex-direction: column; }
            .sidebar { width: 100%; }
            .content-area { padding: 18px; }
            h1 { font-size: 28px; }
        }
    </style>
</head>
<body data-theme="{{ theme }}">
    <div class="app-shell">
        <aside class="sidebar">
            <div class="sidebar-brand">
                <h2 class="sidebar-title">DWH Quality</h2>
                <p class="sidebar-subtitle">Monitoring dashboard and refresh activity.</p>
            </div>

            <nav class="sidebar-nav" aria-label="Dashboard navigation">
                <a class="nav-link {{ 'active' if active_view == 'quality' else '' }}" href="{{ quality_url }}">
                    <span class="nav-dot"></span>
                    <span class="nav-text">
                        <span class="nav-label">Data Quality</span>
                        <span class="nav-hint">Gold DB health</span>
                    </span>
                </a>
                <a class="nav-link {{ 'active' if active_view == 'refresh' else '' }}" href="{{ refresh_url }}">
                    <span class="nav-dot"></span>
                    <span class="nav-text">
                        <span class="nav-label">Data Refresh Status</span>
                        <span class="nav-hint">Latest execution per unique procedure</span>
                    </span>
                </a>
                <a class="nav-link {{ 'active' if active_view == 'sp' else '' }}" href="{{ sp_url }}">
                    <span class="nav-dot"></span>
                    <span class="nav-text">
                        <span class="nav-label">SP Analysis</span>
                        <span class="nav-hint">Stored procedure quality &amp; best practices</span>
                    </span>
                </a>
                <a class="nav-link {{ 'active' if active_view == 'intel' else '' }}" href="{{ intel_url }}">
                    <span class="nav-dot"></span>
                    <span class="nav-text">
                        <span class="nav-label">Table Intelligence</span>
                        <span class="nav-hint">Schema, samples &amp; business context</span>
                    </span>
                </a>
            </nav>

            <div class="sidebar-footer">
                <button type="button" class="footer-btn button-link sidebar-toggle-btn" id="sidebarToggleBtn" aria-label="Collapse sidebar" title="Collapse sidebar">
                    <span class="sidebar-toggle-icon" id="sidebarToggleIcon" aria-hidden="true">❮</span>
                </button>
                <a class="footer-btn button-link" href="{{ theme_toggle_url }}">{{ theme_toggle_label }}</a>
            </div>
        </aside>

        <div class="content-area">
            <div class="content-shell">
                {% if active_view == 'quality' %}
                <section class="panel">
                    <div class="page-header">
                        <div>
                            <p class="page-kicker">Data Quality</p>
                            <h1>Data Quality</h1>
                            <p>Gold DB quality table from the latest data quality run. Drag the column edges to resize them.</p>
                        </div>
                    </div>

                    <div class="toolbar">
                        <a class="primary button-link" id="loadGoldBtn" href="{{ refresh_gold_url }}">Load Gold Table</a>
                        <a class="secondary button-link" id="refreshGoldBtn" href="{{ refresh_gold_url }}">Refresh</a>
                        <a class="secondary button-link" id="exportCsvBtn" href="{{ export_csv_url }}">Export CSV</a>
                    </div>

                    {% if initial_metrics_json != '[]' %}
                    <div class="quality-summary-bar">
                        <div class="qs-card fact">
                            <span class="qs-value">{{ quality_fact_count }}</span>
                            <span class="qs-label">Fact Tables</span>
                        </div>
                        <div class="qs-card dim">
                            <span class="qs-value">{{ quality_dim_count }}</span>
                            <span class="qs-label">Dimension Tables</span>
                        </div>
                        <div class="qs-card">
                            <span class="qs-value">{{ quality_avg_score }}%</span>
                            <span class="qs-label">Avg Quality Score</span>
                        </div>
                        <div class="qs-card healthy">
                            <span class="qs-value">{{ quality_healthy }}</span>
                            <span class="qs-label">&#8805; 80% Healthy</span>
                        </div>
                        <div class="qs-card warning">
                            <span class="qs-value">{{ quality_warning }}</span>
                            <span class="qs-label">50–79% Warning</span>
                        </div>
                        <div class="qs-card critical">
                            <span class="qs-value">{{ quality_critical }}</span>
                            <span class="qs-label">&lt; 50% Critical</span>
                        </div>
                        {% if quality_empty_count > 0 %}
                        <div class="qs-card critical">
                            <span class="qs-value">{{ quality_empty_count }}</span>
                            <span class="qs-label">Empty Tables</span>
                        </div>
                        {% endif %}
                    </div>

                    <details class="scoring-info">
                        <summary>How scores are calculated</summary>
                        <div class="checks-grid">
                            <div class="check-item">
                                <span class="check-name">Null Check</span>
                                <span class="check-desc">Scans key columns (IDs, dates, amounts) for null values per row</span>
                                <span class="check-penalty">&#8722;20 pts if overall null % &gt; 10%</span>
                            </div>
                            <div class="check-item">
                                <span class="check-name">Column-level Nulls</span>
                                <span class="check-desc">Each column with &gt; 10% nulls is flagged individually</span>
                                <span class="check-penalty">&#8722;5 pts per column (max &#8722;20)</span>
                            </div>
                            <div class="check-item">
                                <span class="check-name">Duplicate Check</span>
                                <span class="check-desc">Checks for duplicate rows relative to primary column</span>
                                <span class="check-penalty">&#8722;15 pts if dup % &gt; 5%</span>
                            </div>
                            <div class="check-item">
                                <span class="check-name">Data Freshness</span>
                                <span class="check-desc">Checks timestamp/date columns to detect stale data</span>
                                <span class="check-penalty">&#8722;10 pts if last update &gt; 24 hours ago</span>
                            </div>
                            <div class="check-item">
                                <span class="check-name">Empty Table</span>
                                <span class="check-desc">If a table has 0 rows it cannot be evaluated</span>
                                <span class="check-penalty">Score = 0 (no data to assess)</span>
                            </div>
                        </div>
                        <p style="margin-top:10px;color:var(--muted);font-size:11px">
                            Thresholds — Null: &gt;10% | Duplicates: &gt;5% | Staleness: &gt;24h &nbsp;·&nbsp;
                            Healthy &#8805; 80% &nbsp; Warning 50–79% &nbsp; Critical &lt; 50%
                        </p>
                    </details>
                    {% endif %}

                    <div class="status" id="statusBox">{{ initial_status }}</div>
                    <div class="meta" id="metaBox">{{ initial_meta }}</div>

                    <div class="top-pager">
                        <span class="pager-info" id="pagerInfo">{{ initial_pager_info }}</span>
                        <div class="pager-actions">
                            <a class="secondary button-link {{ 'is-disabled' if initial_prev_disabled else '' }}" id="prevPageBtn" href="{{ prev_page_url }}">&#8592; Previous</a>
                            <a class="secondary button-link {{ 'is-disabled' if initial_next_disabled else '' }}" id="nextPageBtn" href="{{ next_page_url }}">Next &#8594;</a>
                        </div>
                    </div>

                    <div class="table-wrap">
                        <table class="quality-table">
                            <colgroup>
                                <col data-col-index="0">
                                <col data-col-index="1">
                                <col data-col-index="2">
                                <col data-col-index="3">
                                <col data-col-index="4">
                                <col data-col-index="5">
                                <col data-col-index="6">
                                <col data-col-index="7">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'table' else '' }}" href="{{ sort_urls['table'] }}">Table{% if sort_by == 'table' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="0" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'layer' else '' }}" href="{{ sort_urls['layer'] }}">Layer{% if sort_by == 'layer' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="1" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'rows' else '' }}" href="{{ sort_urls['rows'] }}">Rows{% if sort_by == 'rows' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="2" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'column_count' else '' }}" href="{{ sort_urls['column_count'] }}">Cols{% if sort_by == 'column_count' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="3" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'pk_fk' else '' }}" href="{{ sort_urls['pk_fk'] }}">PK / FK{% if sort_by == 'pk_fk' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="4" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'quality_score' else '' }}" href="{{ sort_urls['quality_score'] }}">Quality Score{% if sort_by == 'quality_score' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="5" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'issue_columns' else '' }}" href="{{ sort_urls['issue_columns'] }}">Issue Columns{% if sort_by == 'issue_columns' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="6" aria-hidden="true"></span></div></th>
                                    <th><div class="header-cell"><a class="sort-link {{ 'is-active' if sort_by == 'issues' else '' }}" href="{{ sort_urls['issues'] }}">Issues{% if sort_by == 'issues' %} {{ '↑' if sort_dir == 'asc' else '↓' }}{% endif %}</a><span class="column-resizer" data-col-index="7" aria-hidden="true"></span></div></th>
                                </tr>
                            </thead>
                            <tbody id="tableBody">{{ initial_rows_html|safe }}</tbody>
                        </table>
                    </div>
                </section>
                {% elif active_view == 'refresh' %}
                <section class="panel">
                    <div class="page-header">
                        <div>
                            <p class="page-kicker">Data Refresh Status</p>
                            <h1>Data Refresh Status</h1>
                            <p>Latest execution per unique procedure, including execution date and status.</p>
                        </div>
                    </div>

                    <div class="status" id="refreshStatusBox">{{ refresh_summary_status }}</div>
                    <div class="meta" id="refreshMetaBox">{{ refresh_summary_meta }}</div>

                    <div class="top-pager">
                        <span class="pager-info">{{ refresh_table_pager_info }}</span>
                        <div class="pager-actions">
                            <a class="secondary button-link {{ 'is-disabled' if refresh_prev_disabled else '' }}" href="{{ refresh_prev_page_url }}">&#8592; Previous</a>
                            <a class="secondary button-link {{ 'is-disabled' if refresh_next_disabled else '' }}" href="{{ refresh_next_page_url }}">Next &#8594;</a>
                        </div>
                    </div>

                    <div class="table-wrap">
                        <table class="refresh-table">
                            <thead>
                                <tr>{{ refresh_table_headers_html|safe }}</tr>
                            </thead>
                            <tbody id="refreshTableBody">{{ refresh_table_rows_html|safe }}</tbody>
                        </table>
                    </div>

                    <div class="table-footer">
                        <div class="pager-info">{{ refresh_table_pager_info }}</div>
                        <div class="pager-actions">
                            <a class="secondary button-link {{ 'is-disabled' if refresh_prev_disabled else '' }}" id="refreshPrevPageBtn" href="{{ refresh_prev_page_url }}">Previous</a>
                            <a class="secondary button-link {{ 'is-disabled' if refresh_next_disabled else '' }}" id="refreshNextPageBtn" href="{{ refresh_next_page_url }}">Next</a>
                        </div>
                    </div>
                </section>
                {% elif active_view == 'sp' %}
                <section class="panel">
                    <div class="page-header">
                        <div>
                            <p class="page-kicker">SP Analysis</p>
                            <h1>Stored Procedure Analysis</h1>
                            <p>Rule-based quality scores for all stored procedures. Click <strong>Analyze with AI</strong> to enrich with LLM recommendations.</p>
                        </div>
                    </div>

                    <div class="toolbar">
                        <button type="button" class="primary button-link" id="spLlmBtn" onclick="runSpLlmAnalysis()">Analyze with AI</button>
                        <button type="button" class="secondary button-link" onclick="window.location.href='{{ sp_refresh_url }}'" >Refresh</button>
                        <button type="button" class="secondary button-link" onclick="exportSpCSV()">Export CSV</button>
                    </div>

                    <div class="status" id="spStatusBox">{{ sp_status }}</div>
                    <div class="meta" id="spMetaBox">{{ sp_meta }}</div>

                    <div class="top-pager">
                        <span class="pager-info" id="spPagerInfoTop">{{ sp_pager_info }}</span>
                        <div class="pager-actions">
                            <a class="button-link secondary {{ sp_prev_disabled }}" href="{{ sp_prev_page_url }}">&#8592; Previous</a>
                            <a class="button-link secondary {{ sp_next_disabled }}" href="{{ sp_next_page_url }}">Next &#8594;</a>
                        </div>
                    </div>

                    <div class="table-wrap" id="spTableWrap">
                        <table class="data-table" id="spTable">
                            <thead>
                                <tr>
                                    <th><a href="{{ sp_sort_urls['sp_name'] }}">SP Name{% if sp_sort_by == 'sp_name' %} {{ '▲' if sp_sort_dir == 'asc' else '▼' }}{% endif %}</a></th>
                                    <th><a href="{{ sp_sort_urls['schema_name'] }}">Schema{% if sp_sort_by == 'schema_name' %} {{ '▲' if sp_sort_dir == 'asc' else '▼' }}{% endif %}</a></th>
                                    <th><a href="{{ sp_sort_urls['last_modified'] }}">Last Modified{% if sp_sort_by == 'last_modified' %} {{ '▲' if sp_sort_dir == 'asc' else '▼' }}{% endif %}</a></th>
                                    <th style="text-align:center"><a href="{{ sp_sort_urls['parameter_count'] }}">Params{% if sp_sort_by == 'parameter_count' %} {{ '▲' if sp_sort_dir == 'asc' else '▼' }}{% endif %}</a></th>
                                    <th><a href="{{ sp_sort_urls['quality_score'] }}">Quality Score{% if sp_sort_by == 'quality_score' %} {{ '▲' if sp_sort_dir == 'asc' else '▼' }}{% endif %}</a></th>
                                    <th>Code Quality Issues</th>
                                    <th>AI Recommendations</th>
                                    <th style="text-align:center">Analyze</th>
                                </tr>
                            </thead>
                            <tbody id="spTableBody">
                                {{ sp_rows_html|safe }}
                            </tbody>
                        </table>
                    </div>

                    <div class="table-footer">
                        <div class="pager-info" id="spPagerInfo">{{ sp_pager_info }}</div>
                        <div class="pager-actions">
                            <a class="button-link secondary {{ sp_prev_disabled }}" id="spPrevPageBtn" href="{{ sp_prev_page_url }}">&#8592; Previous</a>
                            <a class="button-link secondary {{ sp_next_disabled }}" id="spNextPageBtn" href="{{ sp_next_page_url }}">Next &#8594;</a>
                        </div>
                    </div>
                </section>

                <!-- SP Analyze Modal -->
                <div class="sp-modal-overlay" id="spModalOverlay" onclick="if(event.target===this)closeSpModal()">
                    <div class="sp-modal">
                        <div class="sp-modal-header">
                            <h2 id="spModalTitle">SP Analysis</h2>
                            <button class="sp-modal-close" onclick="closeSpModal()" title="Close">&times;</button>
                        </div>
                        <div class="sp-modal-body" id="spModalBody">
                            <p style="color:var(--muted)">Loading…</p>
                        </div>
                        <div class="sp-modal-footer">
                            <span id="spModalStatus" style="font-size:12px;color:var(--muted)"></span>
                            <button class="secondary button-link" onclick="closeSpModal()">Close</button>
                        </div>
                    </div>
                </div>
                <script>
                (function() {
                    function esc(s) {
                        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
                    }
                    window.showSpDetail = function(spName) {
                        var overlay = document.getElementById('spModalOverlay');
                        var body = document.getElementById('spModalBody');
                        var title = document.getElementById('spModalTitle');
                        var status = document.getElementById('spModalStatus');
                        title.textContent = spName;
                        status.textContent = '';
                        body.innerHTML = '<p style="color:var(--muted)">Loading definition &amp; AI analysis…</p>';
                        overlay.classList.add('open');
                        fetch('/api/sp-analyze-single', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({sp_name: spName})
                        })
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (!data.success) {
                                body.innerHTML = '<p style="color:var(--danger,#ef4444)">Error: ' + esc(data.error || 'unknown') + '</p>';
                                return;
                            }
                            var llm = data.llm_analysis || {};
                            var recs = llm.recommendations || [];
                            var issues = llm.issues || [];
                            var summary = llm.summary || '';
                            var score = llm.score != null ? llm.score : '—';
                            var recsHtml = recs.length ? '<ul class="sp-llm-list">' + recs.map(function(r){return '<li>' + esc(typeof r==='string'?r:JSON.stringify(r)) + '</li>';}).join('') + '</ul>' : '<p style="color:var(--muted)">None</p>';
                            var issuesHtml = issues.length ? '<ul class="sp-llm-list">' + issues.map(function(i){return '<li>' + esc(typeof i==='string'?i:JSON.stringify(i)) + '</li>';}).join('') + '</ul>' : '<p style="color:#22c55e">✓ No issues found</p>';
                            var defHtml = data.definition ? '<div class="sp-definition-box">' + esc(data.definition) + '</div>' : '<p style="color:var(--muted)">Definition unavailable</p>';
                            body.innerHTML =
                                '<div>' +
                                    '<div class="sp-modal-section-title">AI Score</div>' +
                                    '<span class="score-pill ' + (score>=80?'score-high':score>=50?'score-med':'score-low') + '">' + score + '%</span>' +
                                    (summary ? '<p style="font-size:13px;margin-top:8px">' + esc(summary) + '</p>' : '') +
                                '</div>' +
                                '<div><div class="sp-modal-section-title">AI Recommendations</div>' + recsHtml + '</div>' +
                                '<div><div class="sp-modal-section-title">Issues Detected</div>' + issuesHtml + '</div>' +
                                '<div><div class="sp-modal-section-title">SP Definition</div>' + defHtml + '</div>';
                            status.textContent = data.cached ? 'Cached result' : 'Fresh analysis';
                        })
                        .catch(function(err) {
                            body.innerHTML = '<p style="color:var(--danger,#ef4444)">Request failed: ' + esc(String(err)) + '</p>';
                        });
                    };
                    window.closeSpModal = function() {
                        document.getElementById('spModalOverlay').classList.remove('open');
                    };
                    document.addEventListener('keydown', function(e) {
                        if (e.key === 'Escape') window.closeSpModal();
                    });
                })();
                </script>
                {% elif active_view == 'intel' %}
                <section class="panel">
                    <div class="page-header">
                        <div>
                            <p class="page-kicker">Table Intelligence</p>
                            <h1>Table Intelligence</h1>
                            <p>Schema metadata, sample data, grain definitions, and on-demand AI business summaries for every table.</p>
                        </div>
                    </div>
                    <div class="toolbar" style="flex-wrap:wrap;gap:8px">
                        <input type="text" id="intelSearch" class="intel-search" placeholder="Filter tables…" oninput="filterIntelCards(this.value)">
                        <span style="font-size:12px;color:var(--muted);margin-left:4px" id="intelCount">{{ intel_total }} tables</span>
                        <div style="margin-left:auto;display:flex;align-items:center;gap:8px">
                            <button id="intelPrevBtn" class="button-link secondary" onclick="intelPrevPage()" disabled>&#8592; Prev</button>
                            <span class="pager-info" id="intelPagerInfo" style="min-width:140px;text-align:center">Page 1</span>
                            <button id="intelNextBtn" class="button-link secondary" onclick="intelNextPage()">Next &#8594;</button>
                            <button type="button" class="secondary button-link" onclick="window.location.href='{{ intel_refresh_url }}'">Refresh</button>
                        </div>
                    </div>
                    <div class="intel-filter-row">
                        <button class="intel-filter-btn active" onclick="filterIntelType(this,'all')">All</button>
                        <button class="intel-filter-btn" onclick="filterIntelType(this,'fact')">Fact</button>
                        <button class="intel-filter-btn" onclick="filterIntelType(this,'dimension')">Dimension</button>
                    </div>
                    <div class="intel-grid" id="intelGrid">
                        {{ intel_cards_html|safe }}
                    </div>
                </section>
                <script>
                (function() {
                    var _typeFilter = 'all';
                    var _page = 1;
                    var _pageSize = 12;

                    function applyFilter() {
                        var q = ((document.getElementById('intelSearch') || {}).value || '').toLowerCase().trim();
                        var cards = document.querySelectorAll('#intelGrid .intel-card');
                        cards.forEach(function(card) {
                            var name = (card.getAttribute('data-table') || '').toLowerCase();
                            var type = (card.getAttribute('data-type') || '').toLowerCase();
                            var tm = (_typeFilter === 'all') || (type === _typeFilter);
                            var qm = !q || name.indexOf(q) !== -1;
                            card.setAttribute('data-m', (tm && qm) ? '1' : '0');
                        });
                        _page = 1;
                        renderPage();
                    }

                    function renderPage() {
                        var all = Array.prototype.slice.call(document.querySelectorAll('#intelGrid .intel-card'));
                        var matched = all.filter(function(c) { return c.getAttribute('data-m') === '1'; });
                        var total = matched.length;
                        var totalPages = Math.max(1, Math.ceil(total / _pageSize));
                        _page = Math.min(Math.max(_page, 1), totalPages);
                        var start = (_page - 1) * _pageSize;
                        var end = start + _pageSize;
                        all.forEach(function(c) { c.style.display = 'none'; });
                        matched.slice(start, end).forEach(function(c) { c.style.display = ''; });
                        var cnt = document.getElementById('intelCount');
                        if (cnt) cnt.textContent = total + ' tables';
                        var info = document.getElementById('intelPagerInfo');
                        if (info) info.textContent = 'Page ' + _page + ' of ' + totalPages + ' \u00b7 ' + total + ' tables';
                        var prev = document.getElementById('intelPrevBtn');
                        var next = document.getElementById('intelNextBtn');
                        if (prev) prev.disabled = (_page <= 1);
                        if (next) next.disabled = (_page >= totalPages);
                    }

                    window.filterIntelCards = function() { applyFilter(); };
                    window.filterIntelType = function(btn, type) {
                        document.querySelectorAll('.intel-filter-btn').forEach(function(b) { b.classList.remove('active'); });
                        btn.classList.add('active');
                        _typeFilter = type;
                        applyFilter();
                    };
                    window.intelPrevPage = function() {
                        if (_page > 1) { _page--; renderPage(); }
                    };
                    window.intelNextPage = function() {
                        var all = Array.prototype.slice.call(document.querySelectorAll('#intelGrid .intel-card'));
                        var matched = all.filter(function(c) { return c.getAttribute('data-m') === '1'; });
                        var tp = Math.max(1, Math.ceil(matched.length / _pageSize));
                        if (_page < tp) { _page++; renderPage(); }
                    };

                    applyFilter();
                })();
                </script>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        const spRecordsJson = {{ sp_records_json|safe }};

        function runSpLlmAnalysis() {
            const btn = document.getElementById('spLlmBtn');
            const statusBox = document.getElementById('spStatusBox');
            if (btn) { btn.textContent = 'Analyzing…'; btn.disabled = true; }
            if (statusBox) statusBox.textContent = 'Running AI analysis — this may take a minute…';
            fetch('/api/sp-llm-analyze', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (statusBox) statusBox.textContent = data.success ? `AI analysis complete — ${data.analyzed} SPs analyzed. Refreshing page…` : `Error: ${data.error}`;
                    if (data.success) setTimeout(() => window.location.reload(), 1200);
                })
                .catch(err => { if (statusBox) statusBox.textContent = 'AI analysis request failed: ' + err; })
                .finally(() => { if (btn) { btn.textContent = 'Analyze with AI'; btn.disabled = false; } });
        }

        function exportSpCSV() {
            if (!spRecordsJson.length) return;
            const header = ['SP Name','Schema','Last Modified','Params','Quality Score','Code Quality Issues'];
            const rows = spRecordsJson.map(r => [
                '"' + (r.sp_name || '').replace(/"/g, '""') + '"',
                '"' + (r.schema_name || '').replace(/"/g, '""') + '"',
                '"' + (r.last_modified || '').replace(/"/g, '""') + '"',
                r.parameter_count || 0,
                r.quality_score !== null ? r.quality_score : '',
                '"' + (r.issues || []).join('; ').replace(/"/g, '""') + '"'
            ].join(','));
            const csv = [header.join(','), ...rows].join('\n');
            const a = document.createElement('a');
            a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
            a.download = 'sp_analysis.csv';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        /* intel filter/pagination handled in inline script inside the intel section */

        const initialMetrics = {{ initial_metrics_json|safe }};
        const initialCurrentPage = {{ initial_current_page }};
        const pageSize = {{ table_page_size }};
        const activeView = {{ active_view|tojson }};
        const tableState = {
            metrics: Array.isArray(initialMetrics) ? initialMetrics : [],
            currentPage: initialCurrentPage,
            pageSize: pageSize,
        };

        function sortMetrics(metrics) {
            return [...metrics].sort((left, right) => {
                const leftScore = Number.isFinite(Number(left.quality_score)) ? Number(left.quality_score) : Number.POSITIVE_INFINITY;
                const rightScore = Number.isFinite(Number(right.quality_score)) ? Number(right.quality_score) : Number.POSITIVE_INFINITY;
                if (leftScore !== rightScore) {
                    return leftScore - rightScore;
                }
                const leftTable = String(left.table || '').toLowerCase();
                const rightTable = String(right.table || '').toLowerCase();
                return leftTable.localeCompare(rightTable);
            });
        }

        function getSavedColumnWidths() {
            try {
                const saved = localStorage.getItem('dwh-quality-column-widths-v1');
                return saved ? JSON.parse(saved) : null;
            } catch (error) {
                return null;
            }
        }

        function saveColumnWidths(widths) {
            try {
                localStorage.setItem('dwh-quality-column-widths-v1', JSON.stringify(widths));
            } catch (error) {
                // Ignore storage issues.
            }
        }

        function applyColumnWidths(widths) {
            const cols = document.querySelectorAll('.quality-table col[data-col-index]');
            cols.forEach((col, index) => {
                if (Array.isArray(widths) && Number.isFinite(Number(widths[index]))) {
                    col.style.width = `${Number(widths[index])}px`;
                }
            });
        }

        function captureColumnWidths() {
            const cols = document.querySelectorAll('.quality-table col[data-col-index]');
            return Array.from(cols).map((col) => Math.max(80, Math.round(col.getBoundingClientRect().width)));
        }

        function initResizableColumns() {
            const cols = Array.from(document.querySelectorAll('.quality-table col[data-col-index]'));
            const handles = Array.from(document.querySelectorAll('.column-resizer'));
            if (!cols.length || !handles.length) {
                return;
            }

            const savedWidths = getSavedColumnWidths();
            if (Array.isArray(savedWidths) && savedWidths.length === cols.length) {
                applyColumnWidths(savedWidths);
            }

            let activeResize = null;

            handles.forEach((handle) => {
                handle.addEventListener('mousedown', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const index = Number(handle.dataset.colIndex);
                    const col = cols[index];
                    if (!col) {
                        return;
                    }
                    const width = parseFloat(getComputedStyle(col).width) || col.getBoundingClientRect().width;
                    activeResize = {
                        index,
                        startX: event.clientX,
                        startWidth: width,
                    };
                    document.body.classList.add('is-resizing-columns');
                });
            });

            window.addEventListener('mousemove', (event) => {
                if (!activeResize) {
                    return;
                }
                const col = cols[activeResize.index];
                if (!col) {
                    return;
                }
                const nextWidth = Math.max(80, Math.round(activeResize.startWidth + (event.clientX - activeResize.startX)));
                col.style.width = `${nextWidth}px`;
                saveColumnWidths(captureColumnWidths());
            });

            window.addEventListener('mouseup', () => {
                if (activeResize) {
                    saveColumnWidths(captureColumnWidths());
                    activeResize = null;
                    document.body.classList.remove('is-resizing-columns');
                }
            });
        }

        function formatMetricValues(value) {
            if (Array.isArray(value)) {
                const entries = value.map((entry) => {
                    if (entry && typeof entry === 'object') {
                        return entry.column || entry.name || entry.value || JSON.stringify(entry);
                    }
                    return entry;
                }).filter(Boolean);
                return entries.length ? entries.join(', ') : '-';
            }
            if (value === null || value === undefined) {
                return '-';
            }
            const text = String(value).trim();
            return text || '-';
        }

        function formatColumnIssueSummary(columnIssues) {
            if (!columnIssues || typeof columnIssues !== 'object') {
                return 'None';
            }

            const entries = Object.entries(columnIssues).map(([columnName, problems]) => {
                let problemText = 'Issue detected';
                if (Array.isArray(problems)) {
                    const cleaned = problems.map((problem) => String(problem).trim()).filter(Boolean);
                    if (cleaned.length) {
                        problemText = cleaned.join('; ');
                    }
                } else if (problems !== null && problems !== undefined) {
                    const text = String(problems).trim();
                    if (text) {
                        problemText = text;
                    }
                }
                return `${columnName} (${problemText})`;
            });

            return entries.length ? entries.join('; ') : 'None';
        }

        function formatIssueSummary(item) {
            const issues = Array.isArray(item.issues)
                ? item.issues.map((issue) => String(issue).trim()).filter(Boolean)
                : [];
            if (issues.length) {
                return issues.join('; ');
            }

            const columnIssues = item.column_issues && typeof item.column_issues === 'object' ? item.column_issues : null;
            if (columnIssues && Object.keys(columnIssues).length) {
                return formatColumnIssueSummary(columnIssues);
            }

            return 'Healthy';
        }

        function csvEscape(value) {
            const text = value === null || value === undefined ? '' : String(value);
            return '"' + text.replace(/"/g, '""') + '"';
        }

        function exportTableCSV() {
            if (!tableState.metrics.length) {
                document.getElementById('statusBox').textContent = 'No Gold tables available to export.';
                return;
            }

            const header = ['Table', 'Layer', 'Rows', 'Cols', 'PK', 'FK', 'Quality Score', 'Issue Columns', 'Issues'];
            const rows = [header];

            tableState.metrics.forEach((item) => {
                const issueColumns = formatColumnIssueSummary(item.column_issues);
                const issues = formatIssueSummary(item);
                rows.push([
                    item.table || '',
                    item.layer || 'gold',
                    item.rows ?? '',
                    item.column_count ?? '',
                    formatMetricValues(item.pk_columns),
                    formatMetricValues(item.fk_columns),
                    item.quality_score ?? '',
                    issueColumns,
                    issues,
                ]);
            });

            const csv = '\ufeff' + rows.map((row) => row.map(csvEscape).join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'dwh_gold_quality_table.csv';
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            setTimeout(() => {
                link.remove();
                URL.revokeObjectURL(url);
            }, 1000);
        }

        function renderRows() {
            const body = document.getElementById('tableBody');
            const pagerInfo = document.getElementById('pagerInfo');
            const prevBtn = document.getElementById('prevPageBtn');
            const nextBtn = document.getElementById('nextPageBtn');
            if (!body || !pagerInfo || !prevBtn || !nextBtn) {
                return;
            }
            const total = tableState.metrics.length;
            const totalPages = total ? Math.ceil(total / tableState.pageSize) : 1;
            const currentPage = Math.min(Math.max(tableState.currentPage, 1), totalPages);
            tableState.currentPage = currentPage;

            const start = (currentPage - 1) * tableState.pageSize;
            const visibleMetrics = tableState.metrics.slice(start, start + tableState.pageSize);

            if (!visibleMetrics.length) {
                body.innerHTML = '<tr><td colspan="8" style="color: var(--muted);">No Gold tables found in the latest run.</td></tr>';
                pagerInfo.textContent = 'Page 0 of 0';
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }

            body.innerHTML = visibleMetrics.map((item) => {
                const issueColumns = formatColumnIssueSummary(item.column_issues);
                const issues = formatIssueSummary(item);
                const pk = formatMetricValues(item.pk_columns);
                const fk = formatMetricValues(item.fk_columns);
                return `
                    <tr>
                        <td>${item.table || '—'}</td>
                        <td><span class="layer-tag">${item.layer || '—'}</span></td>
                        <td>${item.rows ?? '—'}</td>
                        <td>${item.column_count ?? '—'}</td>
                        <td><div class="pkfk-block"><div><span class="kv-label">PK</span> ${pk}</div><div><span class="kv-label">FK</span> ${fk}</div></div></td>
                        <td>${item.quality_score ?? '—'}%</td>
                        <td>${issueColumns}</td>
                        <td>${issues}</td>
                    </tr>
                `;
            }).join('');

            pagerInfo.textContent = `Page ${currentPage} of ${totalPages} — showing ${start + 1}-${Math.min(start + tableState.pageSize, total)} of ${total}`;
            prevBtn.disabled = currentPage <= 1;
            nextBtn.disabled = currentPage >= totalPages;
        }

        function setMetrics(metrics) {
            tableState.metrics = sortMetrics(Array.isArray(metrics) ? metrics : []);
            tableState.currentPage = 1;
            renderRows();
        }

        function changePage(delta) {
            tableState.currentPage += delta;
            renderRows();
        }

        function extractGoldMetrics(report) {
            if (!report) return [];

            if (report.report && typeof report.report === 'object') {
                const nestedMetrics = extractGoldMetrics(report.report);
                if (nestedMetrics.length) {
                    return nestedMetrics;
                }
            }

            const directMetrics = Array.isArray(report.metrics) ? report.metrics : [];
            if (directMetrics.length) {
                const reportLayer = String(report.layer || report.check_type || '').toLowerCase();
                if (reportLayer === 'gold' || reportLayer === 'comprehensive' || !reportLayer) {
                    return directMetrics;
                }
                return directMetrics.filter((item) => String(item.layer || '').toLowerCase() === 'gold');
            }

            const goldLayerReport = report.layer_reports && report.layer_reports.gold;
            if (goldLayerReport && Array.isArray(goldLayerReport.metrics)) {
                return goldLayerReport.metrics;
            }

            return [];
        }

        function findLatestGoldReport(history) {
            for (const item of history) {
                const report = item && item.report;
                if (extractGoldMetrics(report).length) {
                    return { report, checkedAt: item.checked_at };
                }
            }
            return { report: null, checkedAt: null };
        }

        async function loadGoldTable(forceRun) {
            const statusBox = document.getElementById('statusBox');
            const metaBox = document.getElementById('metaBox');

            try {
                statusBox.textContent = forceRun ? 'Running Gold quality check...' : 'Refreshing Gold DB status...';

                let report = null;
                let checkedAt = null;

                if (forceRun) {
                    const response = await fetch('/api/run-now', { method: 'POST' });
                    const data = await response.json();
                    if (!data.success) {
                        throw new Error(data.error || 'Could not load the Gold table');
                    }
                    report = data.run?.report || null;
                    checkedAt = data.run?.checked_at || null;
                } else {
                    const response = await fetch('/api/dashboard-state');
                    const data = await response.json();
                    const latestGold = findLatestGoldReport(data.history || []);
                    report = latestGold.report;
                    checkedAt = latestGold.checkedAt;
                }

                const goldMetrics = extractGoldMetrics(report);

                setMetrics(goldMetrics);
                statusBox.textContent = goldMetrics.length
                    ? `Loaded ${goldMetrics.length} Gold table${goldMetrics.length === 1 ? '' : 's'}.`
                    : 'No Gold tables found in the latest run.';
                metaBox.textContent = checkedAt ? `Last checked at: ${checkedAt}` : 'No previous Gold run found.';
            } catch (error) {
                statusBox.textContent = `Unable to load Gold table: ${error.message}`;
                metaBox.textContent = 'Please try again.';
                setMetrics([]);
            }
        }

        function getSidebarCollapsedState() {
            try { return localStorage.getItem('dwh-sidebar-collapsed-v1') === '1'; } catch(e) { return false; }
        }
        function setSidebarCollapsedState(collapsed) {
            try { localStorage.setItem('dwh-sidebar-collapsed-v1', collapsed ? '1' : '0'); } catch(e) {}
        }
        function applySidebarState(collapsed) {
            const sidebar = document.querySelector('.sidebar');
            const toggleIcon = document.getElementById('sidebarToggleIcon');
            if (!sidebar) return;
            if (collapsed) {
                sidebar.classList.add('is-collapsed');
                sidebar.style.width = '72px';
                sidebar.style.paddingLeft = '10px';
                sidebar.style.paddingRight = '10px';
                sidebar.style.overflow = 'hidden';
            } else {
                sidebar.classList.remove('is-collapsed');
                sidebar.style.width = '';
                sidebar.style.paddingLeft = '';
                sidebar.style.paddingRight = '';
                sidebar.style.overflow = '';
            }
            if (toggleIcon) toggleIcon.textContent = collapsed ? '\u2630' : '\u276e';
        }
        function initSidebarToggle() {
            const btn = document.getElementById('sidebarToggleBtn');
            if (!btn) return;
            applySidebarState(getSidebarCollapsedState());
            btn.addEventListener('click', function() {
                const sidebar = document.querySelector('.sidebar');
                const collapsed = sidebar && !sidebar.classList.contains('is-collapsed');
                setSidebarCollapsedState(collapsed);
                applySidebarState(collapsed);
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            initSidebarToggle();
            if (activeView === 'quality') {
                initResizableColumns();
                renderRows();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/sp-analysis')
def sp_analysis_redirect():
    theme = _normalize_theme(request.args.get('theme'))
    return redirect(url_for('home', view='sp', theme=theme))


@app.route('/sp-refresh')
def sp_refresh():
    """Clear the SP cache and reload the SP Analysis tab."""
    global _sp_analysis_cache
    with _sp_cache_lock:
        _sp_analysis_cache = None
    theme = _normalize_theme(request.args.get('theme'))
    return redirect(url_for('home', view='sp', theme=theme))


@app.route('/intel-refresh')
def intel_refresh():
    """Clear the Table Intelligence cache and reload the tab."""
    global _intel_cache
    with _intel_cache_lock:
        _intel_cache = None
    theme = _normalize_theme(request.args.get('theme'))
    return redirect(url_for('home', view='intel', theme=theme))


@app.route('/api/table-llm-summary', methods=['POST'])
def table_llm_summary():
    """Generate a business summary for one table using the LLM."""
    data = request.get_json(force=True, silent=True) or {}
    full_name = str(data.get('table', '')).strip()
    if not full_name:
        return jsonify({'success': False, 'error': 'table param required'}), 400

    with _intel_cache_lock:
        cache = _intel_cache
    if not cache:
        return jsonify({'success': False, 'error': 'Table intel not loaded yet'}), 400

    rec = next((r for r in cache.get('records', []) if r['full_name'].lower() == full_name.lower()), None)
    if rec is None:
        return jsonify({'success': False, 'error': f'Table {full_name} not found in metadata'}), 404

    cols_text = ', '.join(f"{c['name']} ({c['type']})" for c in (rec.get('columns') or [])[:20])
    sample_text = ''
    samples = rec.get('sample_rows') or []
    if samples:
        sample_text = '\n'.join(str(s) for s in samples[:2])

    prompt = (
        f"You are a data warehouse expert. Provide a concise 2-3 sentence business summary "
        f"for the table {rec['full_name']}. "
        f"Table type: {rec.get('table_type','Unknown')}. "
        f"Grain: {rec.get('grain','unknown')}. "
        f"Columns: {cols_text}. "
        f"Sample data (first 2 rows):\n{sample_text}\n"
        f"Explain: what business process this table tracks, what the key measures/attributes are, "
        f"and who would use this data."
    )
    try:
        llm = LLMManager()
        response = asyncio.run(llm.generate([{'role': 'user', 'content': prompt}]))
        summary = (response or '').strip()
        if not summary:
            return jsonify({'success': False, 'error': 'LLM returned empty response'}), 502
        with _intel_cache_lock:
            if _intel_cache:
                for r in _intel_cache['records']:
                    if r['full_name'].lower() == full_name.lower():
                        r['llm_summary'] = summary
                        break
        return jsonify({'success': True, 'summary': summary})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/sp-llm-analyze', methods=['POST'])
def sp_llm_analyze():
    """Run LLM analysis on all SPs and update the in-memory cache."""
    global _sp_analysis_cache
    with _sp_cache_lock:
        cache = _sp_analysis_cache
    if not cache:
        return jsonify({'success': False, 'error': 'No SP data loaded yet. Open the SP Analysis tab first.'}), 400

    system_prompt = (
        'You are an expert SQL Server DBA reviewing stored procedure code for best practices and optimisation. '
        'For each procedure return a JSON object with keys: '
        '"score" (int 0-100), "issues" (list of strings), "recommendations" (list of strings). '
        'Be concise. Return ONLY valid JSON, no markdown.'
    )

    updated = []
    for rec in cache['records']:
        sp_name = rec.get('sp_name', '')
        with _sp_cache_lock:
            if sp_name in _sp_llm_cache:
                rec['llm_analysis'] = _sp_llm_cache[sp_name]
                updated.append({'sp_name': sp_name, 'cached': True})
                continue

        definition = rec.get('definition', '')
        code_snippet = definition[:4000] if definition else '(definition unavailable)'
        prompt = (
            f'Analyze this SQL Server stored procedure and return ONLY a JSON object.\n'
            f'SP name: {sp_name}\n'
            f'Rule-based score: {rec["quality_score"]}/100\n'
            f'Rule-based issues: {", ".join(rec["issues"]) or "none"}\n\n'
            f'Code:\n{code_snippet}\n\n'
            f'Return exactly this JSON structure (no markdown, no extra text):\n'
            f'{{"score": <int 0-100>, "recommendations": ["<string>", ...], "issues": ["<string>", ...]}}'
        )
        try:
            result = asyncio.run(llm_manager.generate(prompt, system_prompt=system_prompt))
            if not result.get('success'):
                logger.warning(f'LLM SP analysis error for {sp_name}: {result.get("error")}')
                continue
            text = result.get('response', '')
            logger.info(f'LLM SP raw response for {sp_name} ({len(text)} chars): {text[:200]}')
            json_match = re.search(r'\{.*\}', text, re.S)
            if not json_match:
                logger.warning(f'No JSON found in LLM response for {sp_name}: {text[:300]}')
                continue
            try:
                analysis = json.loads(json_match.group())
            except json.JSONDecodeError as je:
                logger.warning(f'JSON parse failed for {sp_name}: {je} | raw: {json_match.group()[:200]}')
                continue
            with _sp_cache_lock:
                _sp_llm_cache[sp_name] = analysis
                rec['llm_analysis'] = analysis
            updated.append({'sp_name': sp_name, 'cached': False})
        except Exception as exc:
            logger.warning(f'LLM SP analysis failed for {sp_name}: {exc}')

    return jsonify({'success': True, 'analyzed': len(updated)})


@app.route('/api/sp-analyze-single', methods=['POST'])
def sp_analyze_single():
    """Return definition + LLM analysis for a single SP."""
    global _sp_analysis_cache
    data = request.get_json(force=True, silent=True) or {}
    sp_name = (data.get('sp_name') or '').strip()
    if not sp_name:
        return jsonify({'success': False, 'error': 'sp_name required'}), 400
    with _sp_cache_lock:
        cache = _sp_analysis_cache
    if not cache:
        return jsonify({'success': False, 'error': 'SP data not loaded — open the SP Analysis tab first.'}), 400
    rec = next((r for r in cache['records'] if r.get('sp_name') == sp_name), None)
    if not rec:
        return jsonify({'success': False, 'error': f'SP not found: {sp_name}'}), 404
    definition = rec.get('definition', '') or ''
    existing_llm = rec.get('llm_analysis')
    if existing_llm:
        return jsonify({'success': True, 'sp_name': sp_name, 'definition': definition, 'llm_analysis': existing_llm, 'cached': True})
    system_prompt = (
        'You are an expert SQL Server DBA. Analyze the stored procedure code provided. '
        'Return ONLY a JSON object with keys: '
        '"score" (int 0-100), "summary" (string, 1-2 sentences), '
        '"recommendations" (list of strings), "issues" (list of strings). No markdown.'
    )
    code_snippet = definition[:4000] if definition else '(definition unavailable)'
    prompt = (
        f'Analyze this SQL Server stored procedure.\n'
        f'SP name: {sp_name}\n'
        f'Rule-based score: {rec["quality_score"]}/100\n'
        f'Rule-based issues: {", ".join(rec["issues"]) or "none"}\n\n'
        f'Code:\n{code_snippet}\n\n'
        f'Return exactly: {{"score": 0-100, "summary": "...", "recommendations": ["..."], "issues": ["..."]}}'
    )
    try:
        result = asyncio.run(llm_manager.generate(prompt, system_prompt=system_prompt))
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', 'LLM error')}), 500
        text = result.get('response', '')
        json_match = re.search(r'\{.*\}', text, re.S)
        if not json_match:
            return jsonify({'success': False, 'error': 'LLM did not return valid JSON', 'raw': text[:400]}), 500
        analysis = json.loads(json_match.group())
        with _sp_cache_lock:
            _sp_llm_cache[sp_name] = analysis
            rec['llm_analysis'] = analysis
        return jsonify({'success': True, 'sp_name': sp_name, 'definition': definition, 'llm_analysis': analysis, 'cached': False})
    except Exception as exc:
        logger.error(f'sp_analyze_single error for {sp_name}: {exc}')
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/')
def home():
    """Render the dashboard."""
    theme = _normalize_theme(request.args.get('theme'))
    active_view = _normalize_dashboard_view(request.args.get('view'))
    try:
        requested_page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        requested_page = 1

    requested_sort = request.args.get('sort')
    requested_order = request.args.get('order')
    sort_by = _normalize_sort_column(requested_sort) if active_view == 'quality' else 'quality_score'
    sort_dir = _normalize_sort_direction(requested_order) if active_view == 'quality' else 'asc'
    refresh_sort_by = _normalize_refresh_sort_column(requested_sort) if active_view == 'refresh' else 'execution_date'
    refresh_sort_dir = _normalize_sort_direction(requested_order) if active_view == 'refresh' else 'desc'

    sp_sort_by = requested_sort if requested_sort in SORTABLE_SP_COLUMNS else 'quality_score'
    sp_sort_dir = _normalize_sort_direction(requested_order) if active_view == 'sp' else 'asc'

    with dashboard_lock:
        latest_report, latest_checked_at = _find_latest_gold_report(run_history)
        recent_refresh_logs = list(run_history[:15])
    ssis_refresh_table = _load_ssis_refresh_table() if active_view == 'refresh' else None
    sp_data = _load_sp_analysis() if active_view == 'sp' else None
    intel_data = _load_table_intel() if active_view == 'intel' else None

    if active_view == 'quality' and latest_report is None:
        run_result = _execute_quality_check(trigger='page-load', target_layer='gold')
        if run_result.get('success'):
            latest_report = run_result['run'].get('report', {})
            latest_checked_at = run_result['run'].get('checked_at')
            with dashboard_lock:
                recent_refresh_logs = list(run_history[:15])

    initial_metrics = _sort_gold_metrics(_extract_gold_metrics(latest_report), sort_by=sort_by, sort_dir=sort_dir)
    initial_total_pages = (len(initial_metrics) + GOLD_TABLE_PAGE_SIZE - 1) // GOLD_TABLE_PAGE_SIZE if initial_metrics else 0
    current_page = 1
    if initial_total_pages:
        current_page = min(max(requested_page, 1), initial_total_pages)
    start_index = (current_page - 1) * GOLD_TABLE_PAGE_SIZE if initial_metrics else 0
    initial_rows_html = _render_gold_metric_rows(initial_metrics[start_index:start_index + GOLD_TABLE_PAGE_SIZE])
    if initial_metrics:
        start_row = start_index + 1
        end_row = min(start_index + GOLD_TABLE_PAGE_SIZE, len(initial_metrics))
        initial_pager_info = f"Page {current_page} of {initial_total_pages} — showing {start_row}-{end_row} of {len(initial_metrics)}"
    else:
        initial_pager_info = 'Page 0 of 0'
    # Summary stats for the quality tab header
    _tname_lower = lambda m: (m.get('table') or '').lower()
    quality_fact_count   = sum(1 for m in initial_metrics if 'fact' in _tname_lower(m))
    quality_dim_count    = sum(1 for m in initial_metrics if any(p in _tname_lower(m) for p in ('dim_', 'dim.')))
    quality_empty_count  = sum(1 for m in initial_metrics if (m.get('rows') or 0) == 0)
    quality_scores       = [m['quality_score'] for m in initial_metrics if m.get('quality_score') is not None]
    quality_avg_score    = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0
    quality_healthy      = sum(1 for s in quality_scores if s >= 80)
    quality_warning      = sum(1 for s in quality_scores if 50 <= s < 80)
    quality_critical     = sum(1 for s in quality_scores if s < 50)

    initial_status = (
        f"Loaded {len(initial_metrics)} Gold table{'s' if len(initial_metrics) != 1 else ''}."
        if initial_metrics else 'No Gold tables found in the latest run.'
    )
    if request.args.get('refreshed') == '1' and initial_metrics:
        initial_status = f"Refreshed {len(initial_metrics)} Gold table{'s' if len(initial_metrics) != 1 else ''}."
    initial_meta = f"Last checked at: {latest_checked_at}" if latest_checked_at else 'No previous Gold run found.'

    refresh_summary_status = 'No refresh history found.'
    refresh_summary_meta = 'Latest execution date and status from the most recent refresh record.'
    refresh_table_columns = [
        {'key': 'procedure_name', 'label': 'Procedure Name'},
        {'key': 'execution_date', 'label': 'Execution Date'},
        {'key': 'status', 'label': 'Status'},
    ]
    refresh_records: List[Dict[str, Any]] = []
    refresh_page_records: List[Dict[str, Any]] = []
    refresh_total_pages = 0
    refresh_current_page = 1
    refresh_pager_info = 'Page 0 of 0'
    refresh_prev_disabled = 'disabled'
    refresh_next_disabled = 'disabled'
    refresh_prev_page_url = url_for('home', page=1, theme=theme, sort=refresh_sort_by, order=refresh_sort_dir, view='refresh')
    refresh_next_page_url = refresh_prev_page_url
    if ssis_refresh_table:
        refresh_records = _sort_refresh_records(ssis_refresh_table['records'], sort_by=refresh_sort_by, sort_dir=refresh_sort_dir)
        refresh_total_pages = (len(refresh_records) + REFRESH_TABLE_PAGE_SIZE - 1) // REFRESH_TABLE_PAGE_SIZE if refresh_records else 0
        refresh_current_page = min(max(requested_page, 1), refresh_total_pages) if refresh_total_pages else 1
        refresh_start_index = (refresh_current_page - 1) * REFRESH_TABLE_PAGE_SIZE if refresh_records else 0
        refresh_page_records = refresh_records[refresh_start_index:refresh_start_index + REFRESH_TABLE_PAGE_SIZE]
        refresh_summary_status = f"Showing latest execution for {len(refresh_records)} unique procedure{'s' if len(refresh_records) != 1 else ''}."
        refresh_summary_meta = f"Source: {ssis_refresh_table['source']} · Deduplicated by procedure name."
        refresh_table_headers_html = _render_refresh_table_headers(refresh_table_columns, refresh_sort_by, refresh_sort_dir, {
            column['key']: url_for('home', page=1, theme=theme, sort=column['key'], order=('desc' if refresh_sort_by == column['key'] and refresh_sort_dir == 'asc' else 'asc'), view='refresh')
            for column in refresh_table_columns
        })
        refresh_table_rows_html = _render_refresh_table_rows(refresh_table_columns, refresh_page_records)
        if refresh_total_pages:
            refresh_start_row = refresh_start_index + 1
            refresh_end_row = min(refresh_start_index + REFRESH_TABLE_PAGE_SIZE, len(refresh_records))
            refresh_pager_info = f"Page {refresh_current_page} of {refresh_total_pages} — showing {refresh_start_row}-{refresh_end_row} of {len(refresh_records)}"
        else:
            refresh_pager_info = 'Page 0 of 0'
        refresh_prev_disabled = 'disabled' if refresh_total_pages <= 1 or refresh_current_page <= 1 else ''
        refresh_next_disabled = 'disabled' if refresh_total_pages <= 1 or refresh_current_page >= refresh_total_pages else ''
        refresh_prev_page_url = url_for('home', page=max(refresh_current_page - 1, 1), theme=theme, sort=refresh_sort_by, order=refresh_sort_dir, view='refresh')
        refresh_next_page_url = url_for('home', page=min(refresh_current_page + 1, refresh_total_pages or 1), theme=theme, sort=refresh_sort_by, order=refresh_sort_dir, view='refresh')
    else:
        refresh_history_entries = recent_refresh_logs[:1]
        refresh_table_headers_html = _render_refresh_table_headers(refresh_table_columns, refresh_sort_by, refresh_sort_dir, {
            column['key']: url_for('home', page=1, theme=theme, sort=column['key'], order=('desc' if refresh_sort_by == column['key'] and refresh_sort_dir == 'asc' else 'asc'), view='refresh')
            for column in refresh_table_columns
        })
        if refresh_history_entries:
            latest_refresh = refresh_history_entries[0]
            refresh_summary_status = f"Latest dashboard execution date: {latest_refresh.get('checked_at', '—')}"
            refresh_summary_meta = f"Procedure: {latest_refresh.get('trigger') or 'manual'} · Status: {latest_refresh.get('status') or 'unknown'}"
            refresh_table_rows_html = _render_refresh_table_rows(
                refresh_table_columns,
                [{
                    'procedure_name': latest_refresh.get('trigger') or 'manual',
                    'execution_date': latest_refresh.get('checked_at') or '—',
                    'status': latest_refresh.get('status') or 'unknown',
                }],
            )
        else:
            refresh_table_rows_html = '<tr><td colspan="3" style="color: var(--muted);">No refresh history found.</td></tr>'
        refresh_pager_info = 'Latest execution only'

    sp_records: List[Dict[str, Any]] = []
    sp_rows_html = '<tr><td colspan="7" style="color:var(--muted)">No stored procedures found.</td></tr>'
    sp_total_pages = 0
    sp_current_page = 1
    sp_pager_info = 'Page 0 of 0'
    sp_prev_disabled = 'disabled'
    sp_next_disabled = 'disabled'
    sp_status = 'SP analysis not loaded.'
    sp_meta = 'Navigate to this tab to load stored procedure analysis.'
    sp_prev_page_url = url_for('home', page=1, theme=theme, sort=sp_sort_by, order=sp_sort_dir, view='sp')
    sp_next_page_url = sp_prev_page_url
    sp_records_json: str = '[]'

    if sp_data:
        sp_records = _sort_sp_records(sp_data['records'], sort_by=sp_sort_by, sort_dir=sp_sort_dir)
        sp_total_pages = max(1, (len(sp_records) + SP_ANALYSIS_PAGE_SIZE - 1) // SP_ANALYSIS_PAGE_SIZE)
        sp_current_page = min(max(requested_page, 1), sp_total_pages)
        sp_start = (sp_current_page - 1) * SP_ANALYSIS_PAGE_SIZE
        sp_page_records = sp_records[sp_start:sp_start + SP_ANALYSIS_PAGE_SIZE]
        sp_rows_html = _render_sp_table_rows(sp_page_records)
        sp_end = min(sp_start + SP_ANALYSIS_PAGE_SIZE, len(sp_records))
        sp_pager_info = f"Page {sp_current_page} of {sp_total_pages} — showing {sp_start + 1}-{sp_end} of {len(sp_records)}"
        sp_prev_disabled = 'disabled' if sp_current_page <= 1 else ''
        sp_next_disabled = 'disabled' if sp_current_page >= sp_total_pages else ''
        sp_prev_page_url = url_for('home', page=max(sp_current_page - 1, 1), theme=theme, sort=sp_sort_by, order=sp_sort_dir, view='sp')
        sp_next_page_url = url_for('home', page=min(sp_current_page + 1, sp_total_pages), theme=theme, sort=sp_sort_by, order=sp_sort_dir, view='sp')
        sp_status = f"Loaded {len(sp_records)} stored procedure{'s' if len(sp_records) != 1 else ''}."
        sp_meta = f"Fetched at: {sp_data.get('fetched_at', '—')} · Rule-based analysis. Click 'Analyze with AI' for LLM recommendations."
        sp_records_json = json.dumps([{k: v for k, v in r.items() if k != 'llm_analysis'} for r in sp_records], default=str)

    def _sp_sort_url(col: str) -> str:
        nxt = 'desc' if sp_sort_by == col and sp_sort_dir == 'asc' else 'asc'
        return url_for('home', page=1, theme=theme, sort=col, order=nxt, view='sp')

    sp_sort_urls = {col: _sp_sort_url(col) for col in SORTABLE_SP_COLUMNS}
    sp_url = url_for('home', theme=theme, sort=sp_sort_by, order=sp_sort_dir, page=sp_current_page if active_view == 'sp' else 1, view='sp')
    sp_refresh_url = url_for('sp_refresh', theme=theme)
    intel_url = url_for('home', theme=theme, view='intel')
    intel_refresh_url = url_for('intel_refresh', theme=theme)

    intel_cards_html = '<p class="muted-text">Navigate to this tab to load table intelligence.</p>'
    intel_total = 0
    if active_view == 'intel':
        if intel_data:
            intel_total = intel_data.get('total', 0)
            intel_cards_html = _render_intel_cards(intel_data.get('records', []))
        else:
            intel_cards_html = '<p class="muted-text">No metadata files found in metadata_md/.</p>'

    def _page_url(page_number: int) -> str:
        return url_for('home', page=page_number, theme=theme, sort=sort_by, order=sort_dir, view='quality')

    def _sort_url(column_name: str) -> str:
        next_order = 'desc' if sort_by == column_name and sort_dir == 'asc' else 'asc'
        return url_for('home', page=1, theme=theme, sort=column_name, order=next_order, view='quality')

    sort_urls = {column_name: _sort_url(column_name) for column_name in SORTABLE_GOLD_COLUMNS}

    prev_page_url = _page_url(max(current_page - 1, 1))
    next_page_url = _page_url(min(current_page + 1, initial_total_pages or 1))
    theme_toggle = 'light' if theme == 'dark' else 'dark'
    theme_toggle_label = 'Switch to light theme' if theme == 'dark' else 'Switch to dark theme'
    active_sort_by = refresh_sort_by if active_view == 'refresh' else (sp_sort_by if active_view == 'sp' else sort_by)
    active_sort_dir = refresh_sort_dir if active_view == 'refresh' else (sp_sort_dir if active_view == 'sp' else sort_dir)
    active_page = refresh_current_page if active_view == 'refresh' else (sp_current_page if active_view == 'sp' else current_page)
    theme_toggle_url = url_for('home', page=active_page, theme=theme_toggle, sort=active_sort_by, order=active_sort_dir, view=active_view)
    refresh_gold_url = url_for('refresh_gold_view', page=current_page, theme=theme, sort=sort_by, order=sort_dir, view=active_view)
    export_csv_url = url_for('export_gold_csv', theme=theme, sort=sort_by, order=sort_dir, view=active_view)
    quality_url = url_for('home', theme=theme, sort=sort_by, order=sort_dir, page=current_page, view='quality')
    refresh_url = url_for('refresh_status', theme=theme, sort=refresh_sort_by, order=refresh_sort_dir, page=refresh_current_page if active_view == 'refresh' else 1, view='refresh')

    return render_template_string(
        DASHBOARD_TEMPLATE,
        active_view=active_view,
        initial_status=initial_status,
        initial_meta=initial_meta,
        initial_rows_html=initial_rows_html,
        initial_pager_info=initial_pager_info,
        initial_prev_disabled='disabled' if initial_total_pages <= 1 or current_page <= 1 else '',
        initial_next_disabled='disabled' if initial_total_pages <= 1 or current_page >= initial_total_pages else '',
        initial_current_page=current_page,
        initial_metrics_json=json.dumps(initial_metrics, default=str),
        quality_fact_count=quality_fact_count,
        quality_dim_count=quality_dim_count,
        quality_empty_count=quality_empty_count,
        quality_avg_score=quality_avg_score,
        quality_healthy=quality_healthy,
        quality_warning=quality_warning,
        quality_critical=quality_critical,
        theme=theme,
        sort_by=sort_by,
        sort_dir=sort_dir,
        table_page_size=GOLD_TABLE_PAGE_SIZE,
        sort_urls=sort_urls,
        prev_page_url=prev_page_url,
        next_page_url=next_page_url,
        refresh_gold_url=refresh_gold_url,
        export_csv_url=export_csv_url,
        theme_toggle_url=theme_toggle_url,
        theme_toggle_label=theme_toggle_label,
        quality_url=quality_url,
        refresh_url=refresh_url,
        refresh_summary_status=refresh_summary_status,
        refresh_summary_meta=refresh_summary_meta,
        refresh_table_headers_html=refresh_table_headers_html,
        refresh_table_rows_html=refresh_table_rows_html,
        refresh_table_pager_info=refresh_pager_info,
        refresh_prev_disabled=refresh_prev_disabled,
        refresh_next_disabled=refresh_next_disabled,
        refresh_prev_page_url=refresh_prev_page_url,
        refresh_next_page_url=refresh_next_page_url,
        sp_url=sp_url,
        sp_refresh_url=sp_refresh_url,
        sp_status=sp_status,
        sp_meta=sp_meta,
        sp_rows_html=sp_rows_html,
        sp_pager_info=sp_pager_info,
        sp_prev_disabled=sp_prev_disabled,
        sp_next_disabled=sp_next_disabled,
        sp_prev_page_url=sp_prev_page_url,
        sp_next_page_url=sp_next_page_url,
        sp_sort_by=sp_sort_by,
        sp_sort_dir=sp_sort_dir,
        sp_sort_urls=sp_sort_urls,
        sp_records_json=sp_records_json,
        intel_url=intel_url,
        intel_refresh_url=intel_refresh_url,
        intel_cards_html=intel_cards_html,
        intel_total=intel_total,
    )


@app.route('/dwh-status/run-now')
def refresh_gold_view():
    """Trigger a fresh Gold quality run and return to the Data Quality page."""
    theme = _normalize_theme(request.args.get('theme'))
    sort_by = _normalize_sort_column(request.args.get('sort'))
    sort_dir = _normalize_sort_direction(request.args.get('order'))
    view = _normalize_dashboard_view(request.args.get('view'))
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    _execute_quality_check(trigger='manual', target_layer='gold')
    return redirect(url_for('home', page=page, theme=theme, sort=sort_by, order=sort_dir, view=view, refreshed=1))


@app.route('/data-refresh-status')
def refresh_status():
    """Render the refresh log view."""
    theme = _normalize_theme(request.args.get('theme'))
    sort_by = _normalize_refresh_sort_column(request.args.get('sort'))
    sort_dir = _normalize_sort_direction(request.args.get('order'))
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    return redirect(url_for('home', theme=theme, view='refresh', sort=sort_by, order=sort_dir, page=page))


@app.route('/dwh-status/export.csv')
def export_gold_csv():
    """Export the full sorted Gold quality table as CSV."""
    theme = _normalize_theme(request.args.get('theme'))
    sort_by = _normalize_sort_column(request.args.get('sort'))
    sort_dir = _normalize_sort_direction(request.args.get('order'))
    with dashboard_lock:
        latest_report, _ = _find_latest_gold_report(run_history)

    metrics = _sort_gold_metrics(_extract_gold_metrics(latest_report), sort_by=sort_by, sort_dir=sort_dir)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Table', 'Layer', 'Rows', 'Cols', 'PK', 'FK', 'Quality Score', 'Issue Columns', 'Issues'])
    for item in metrics:
        issue_columns = _format_column_issue_summary(item.get('column_issues'))
        issues = _format_table_issue_summary(item)
        writer.writerow([
            item.get('table') or '',
            item.get('layer') or 'gold',
            item.get('rows') if item.get('rows') is not None else '',
            item.get('column_count') if item.get('column_count') is not None else '',
            _format_metric_values(item.get('pk_columns')),
            _format_metric_values(item.get('fk_columns')),
            item.get('quality_score') if item.get('quality_score') is not None else '',
            issue_columns,
            issues,
        ])

    csv_data = output.getvalue()
    response = Response('\ufeff' + csv_data, mimetype='text/csv; charset=utf-8')
    response.headers['Content-Disposition'] = 'attachment; filename=dwh_gold_quality_table.csv'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/api/dashboard-state')
def dashboard_state():
    """Return dashboard state including schedule and run history"""
    with dashboard_lock:
        return jsonify({
            'success': True,
            'schedule': dict(schedule_config),
            'runtime': dict(runtime_state),
            'history': list(run_history[:15]),
        })


@app.route('/api/schedule', methods=['POST'])
def update_schedule():
    """Update the daily schedule configuration"""
    try:
        data = request.get_json(silent=True) or {}
        enabled = _bool(data.get('enabled', True))
        time_value = str(data.get('time', '02:00')).strip() or '02:00'
        timezone = str(data.get('timezone', 'Local')).strip() or 'Local'
        layers = _normalize_selection(data.get('layers'), ['bronze', 'silver', 'gold'], ['bronze', 'silver', 'gold'])
        checks = _normalize_selection(
            data.get('checks'),
            ['nulls', 'duplicates', 'freshness', 'schema_drift', 'stored_procedures'],
            ['nulls', 'duplicates', 'freshness', 'schema_drift', 'stored_procedures']
        )

        with dashboard_lock:
            schedule_config.update({
                'enabled': enabled,
                'time': time_value,
                'timezone': timezone,
                'layers': layers,
                'checks': checks,
            })
            _refresh_next_run_locked(datetime.now())
            _save_schedule_config_locked()

        return jsonify({
            'success': True,
            'schedule': schedule_config,
            'runtime': runtime_state,
        })

    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/run-now', methods=['POST'])
def run_now():
    """Execute the quality check immediately"""
    data = request.get_json(silent=True) or {}
    target_layer = str(data.get('layer', 'gold')).strip().lower() or 'gold'
    result = _execute_quality_check(trigger='manual', target_layer=target_layer)
    if result.get('success'):
        return jsonify(result)
    return jsonify(result), 500


@app.route('/api/history')
def history():
    """Return recent run history"""
    with dashboard_lock:
        return jsonify({'success': True, 'history': list(run_history[:15])})

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
    print("DWH Quality Agent - Daily Monitoring Dashboard")
    print("="*60)
    print("Starting dashboard at http://localhost:8080")
    print("Features: Daily scheduling, latest run status, run history")
    print("="*60)
    print()
    _start_scheduler_thread()
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, use_reloader=False)
