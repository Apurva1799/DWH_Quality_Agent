#!/usr/bin/env python3
"""
Gold Database Chatbot - Interactive CLI Interface

A simple interactive chatbot that connects to the Gold database
and answers natural language queries about your data.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentRequest
from app.llm_manager import llm_manager
from loguru import logger
import uuid

class GoldDBChatbot:
    """Interactive chatbot for Gold Database"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.user_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        
        # Suppress loguru output for cleaner CLI
        logger.remove()
        
    async def chat(self, message: str) -> str:
        """Process a chat message and return response"""
        
        # Create agent request
        request = AgentRequest(
            query=message,
            context={
                "conversation_history": self.conversation_history,
                "database": "gold"  # Default to Gold DB
            },
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        # Process through orchestrator
        response = await self.orchestrator.process(request)
        
        # Store conversation
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response.response
        })
        
        return response.response
    
    def print_welcome(self):
        """Print welcome message"""
        print("""
 GOLD DATABASE CHATBOT 


Welcome to your intelligent database assistant!

Connected to: GOLD_DB (afdbsrv.kalyanicorp.com)
Status:  Connected | Tables: 122 available

 Example queries you can ask:
   • "Show me all tables"
   • "What are the top 10 customers?"
   • "Show sales data for last month"
   • "Count total records in main table"
   • "Find duplicate entries"

 Commands:
   • Type 'quit' or 'exit' to end
   • Type 'help' for assistance
   • Type 'tables' to list all tables


        """)
    
    def print_help(self):
        """Print help message"""
        print("""
 HELP - Gold Database Chatbot


  How to ask questions:
   • Use natural language - the chatbot understands plain English
   • Be specific about what you want to know
   • Mention time periods (e.g., "last month", "2023")
   • Specify table names if you know them

 Example queries:
   "Show me the customer table"
   "What are the top 5 products by sales?"
   "Count how many orders we have"
   "Find customers from last year"
   "Show me revenue by month"

 Database info:
   • Server: afdbsrv.kalyanicorp.com
   • Database: GOLD_DB
   • Tables: 122 available
   • Access: Read-only for safety

 Troubleshooting:
   • If query fails, try rephrasing it
   • Be more specific if results are unclear
   • Check spelling of table/column names


        """)
    
    async def list_tables(self):
        """List all available tables"""
        print(" Fetching table list...")
        
        try:
            from app.config import get_database_config
            from sqlalchemy import create_engine, text
            import urllib.parse
            
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
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
                ))
                tables = [row[0] for row in result.fetchall()]
                
                print(f"\n Available Tables in GOLD_DB ({len(tables)} total):")
                print("-" * 50)
                
                for i, table in enumerate(tables, 1):
                    print(f"{i:3}. {table}")
                    
                print()
                
        except Exception as e:
            print(f" Error fetching tables: {str(e)}")
    
    async def run(self):
        """Main chatbot loop"""
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                user_input = input(" You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n Thank you for using Gold Database Chatbot. Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                if user_input.lower() in ['tables', 'list tables', 'show tables']:
                    await self.list_tables()
                    continue
                
                # Process query
                print(" Thinking...")
                response = await self.chat(user_input)
                
                # Print response
                print(f" Bot: {response}")
                print()
                
            except KeyboardInterrupt:
                print("\n\n Goodbye!")
                break
            except Exception as e:
                print(f" Error: {str(e)}")
                print("Please try again or type 'help' for assistance.")
                print()

async def main():
    """Main entry point"""
    chatbot = GoldDBChatbot()
    await chatbot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Chatbot terminated.")
        sys.exit(0)
