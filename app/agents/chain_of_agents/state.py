"""
Chain of Agents Architecture for Kalyani Database Assistant

This module implements a multi-agent workflow for processing database queries.
Each agent has a specific responsibility and passes state to the next agent.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import pandas as pd


class IntentType(Enum):
    """Types of user intents"""
    SQL_QUERY = "sql_query"
    SCHEMA_QUESTION = "schema_question"
    GENERAL_CHAT = "general_chat"
    CLARIFICATION_NEEDED = "clarification_needed"
    VISUALIZATION = "visualization"
    DATA_QUALITY = "data_quality"


class VisualizationType(Enum):
    """Types of visualizations supported"""
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    SCATTER_PLOT = "scatter_plot"
    AREA_CHART = "area_chart"
    HISTOGRAM = "histogram"
    NONE = "none"


@dataclass
class AgentState:
    """
    Shared state passed between agents in the chain.
    Each agent can read and write to this state.
    """
    # Input
    user_query: str = ""
    session_id: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Intent Classification
    intent: Optional[IntentType] = None
    intent_confidence: float = 0.0
    
    # Context Validation
    context_complete: bool = False
    clarification_question: Optional[str] = None
    missing_context: List[str] = field(default_factory=list)
    
    # Schema Selection
    selected_tables: List[str] = field(default_factory=list)
    table_descriptions: Dict[str, str] = field(default_factory=dict)
    join_relationships: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)  # table -> [{related_table, join_key}]
    
    # Query Generation
    generated_sql: str = ""
    sql_valid: bool = False
    sql_error: Optional[str] = None
    
    # Query Execution
    execution_success: bool = False
    query_results: Optional[pd.DataFrame] = None
    execution_error: Optional[str] = None
    row_count: int = 0
    
    # Visualization Decision
    visualization_needed: bool = False
    visualization_type: VisualizationType = VisualizationType.NONE
    chart_fields: List[str] = field(default_factory=list)
    chart_title: str = ""
    
    # Response Formatting
    final_response: str = ""
    response_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    processing_time_ms: float = 0.0
    agent_trace: List[str] = field(default_factory=list)
    
    def add_trace(self, agent_name: str, action: str):
        """Add a trace entry for debugging"""
        self.agent_trace.append(f"[{agent_name}] {action}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization"""
        return {
            "user_query": self.user_query,
            "intent": self.intent.value if self.intent else None,
            "intent_confidence": self.intent_confidence,
            "context_complete": self.context_complete,
            "selected_tables": self.selected_tables,
            "generated_sql": self.generated_sql,
            "sql_valid": self.sql_valid,
            "execution_success": self.execution_success,
            "row_count": self.row_count,
            "visualization_needed": self.visualization_needed,
            "visualization_type": self.visualization_type.value,
            "chart_title": self.chart_title,
            "final_response": self.final_response[:500] + "..." if len(self.final_response) > 500 else self.final_response,
            "agent_trace": self.agent_trace
        }
