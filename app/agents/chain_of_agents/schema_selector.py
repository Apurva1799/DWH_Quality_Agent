"""
Schema Selector Agent
Selects relevant tables based on the query context
"""

import json
import re
from pathlib import Path
from typing import List, Tuple, Dict
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


METADATA_PATH = Path("/home/robotics/Multi_Agent_System/metadata_md")


class SchemaSelectorAgent(BaseAgent):
    """
    Analyzes the user query and selects the most relevant tables
    from the metadata to minimize token usage and improve SQL quality.
    """
    
    def __init__(self):
        super().__init__("SchemaSelector", max_retries=2)
        self.llm = KalyaniLangChainLLM()
        self.all_tables = self._load_all_tables()
        
    def _load_all_tables(self) -> Dict[str, str]:
        """Load all table metadata into memory"""
        tables = {}
        if METADATA_PATH.exists():
            for md_file in METADATA_PATH.glob("*.md"):
                try:
                    content = md_file.read_text()
                    tables[md_file.stem] = content[:1000]  # First 1000 chars
                except Exception as e:
                    logger.warning(f"Failed to load {md_file}: {e}")
        logger.info(f"Loaded {len(tables)} tables into SchemaSelector")
        return tables
    
    async def process(self, state: AgentState) -> AgentState:
        """Select relevant tables based on query"""
        query = state.user_query.lower()
        query_keywords = set(query.split())
        
        # First, try keyword matching for quick selection
        scored_tables = self._score_tables(query_keywords, query)
        
        # If we have good keyword matches, use them
        if scored_tables and scored_tables[0][1] > 5:
            selected = [t[0] for t in scored_tables[:10]]  # Top 10
            state.selected_tables = selected
            state.table_descriptions = {t: self.all_tables.get(t, "")[:500] for t in selected}
            state.add_trace(self.name, f"Keyword selected {len(selected)} tables")
            logger.info(f"[{self.name}] Keyword match: {selected[:5]}")
            return state
        
        # Use LLM for semantic table selection
        table_list = "\n".join([f"- {name}" for name in list(self.all_tables.keys())[:50]])
        
        system_prompt = f"""You are a database schema expert. Your task is to select the most relevant tables for a given query.

Available Tables:
{table_list}

Select 3-8 tables that would be most useful for answering the user's query.
Consider:
- Table names matching query keywords
- Tables likely to contain the data requested
- Related dimension tables that might be needed for joins

Respond ONLY with a JSON object:
{{
    "selected_tables": ["table1", "table2", ...],
    "reasoning": "brief explanation"
}}"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User Query: {state.user_query}")
            ]
            
            result = await self.llm._agenerate(messages)
            raw_response = result.generations[0].message.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{{.*?\}}', raw_response, re.DOTALL)
            if json_match:
                selection = json.loads(json_match.group(0))
                selected = selection.get("selected_tables", [])
                
                # Validate selected tables exist
                valid_tables = [t for t in selected if t in self.all_tables]
                
                if valid_tables:
                    state.selected_tables = valid_tables[:10]  # Limit to 10
                    state.table_descriptions = {
                        t: self.all_tables.get(t, "")[:500] 
                        for t in valid_tables[:10]
                    }
                    state.add_trace(self.name, f"LLM selected {len(valid_tables)} tables")
                    logger.info(f"[{self.name}] LLM selected: {valid_tables}")
                else:
                    # Fallback to keyword matching
                    state.selected_tables = [t[0] for t in scored_tables[:10]]
                    state.add_trace(self.name, "LLM selection invalid, used keyword fallback")
            else:
                state.selected_tables = [t[0] for t in scored_tables[:10]]
                state.add_trace(self.name, "No JSON from LLM, used keyword fallback")
                
        except Exception as e:
            logger.error(f"[{self.name}] LLM selection error: {e}")
            state.selected_tables = [t[0] for t in scored_tables[:10]]
            state.add_trace(self.name, f"Error, used keyword fallback: {str(e)}")
        
        return state
    
    def _score_tables(self, query_keywords: set, query: str) -> List[Tuple[str, int]]:
        """Score tables based on keyword relevance"""
        scores = []
        
        for table_name, content in self.all_tables.items():
            score = 0
            table_lower = table_name.lower()
            content_lower = content.lower()
            
            # Check table name matches
            for keyword in query_keywords:
                if len(keyword) > 2:  # Skip short words
                    if keyword in table_lower:
                        score += 10
                    if keyword in content_lower:
                        score += 5
            
            # Check for common patterns
            if 'production' in query and 'production' in table_lower:
                score += 15
            if 'sales' in query and 'sales' in table_lower:
                score += 15
            if 'customer' in query and 'customer' in table_lower:
                score += 15
            if 'capacity' in query and 'capacity' in table_lower:
                score += 15
            
            # Dim tables for dimensions
            if 'dim_' in table_lower and any(d in query for d in ['category', 'type', 'group', 'by']):
                score += 8
            
            # Fact tables for metrics
            if 'fact_' in table_lower and any(m in query for m in ['total', 'sum', 'count', 'sales', 'revenue']):
                score += 8
            
            if score > 0:
                scores.append((table_name, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, select common tables as fallback"""
        logger.error(f"[{self.name}] Error: {error}")
        
        # Fallback to common tables
        common_tables = [
            "Fact_Sales", "Dim_Customer", "Dim_Date", 
            "Fact_Production", "Dim_Product"
        ]
        
        # Only include tables that exist in metadata
        available = [t for t in common_tables if t in self.all_tables]
        if not available:
            available = list(self.all_tables.keys())[:5]  # First 5 tables
        
        state.selected_tables = available
        state.table_descriptions = {t: self.all_tables.get(t, "")[:500] for t in available}
        state.add_trace(self.name, f"Error fallback, selected {len(available)} common tables")
        
        return state
