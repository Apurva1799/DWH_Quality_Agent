"""
Visualizer Decision Agent
Decides if visualization would be helpful for the data
"""

import json
import re
from loguru import logger

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState, IntentType, VisualizationType
from clients.kalyani_langchain_llm import KalyaniLangChainLLM
from langchain_core.messages import HumanMessage, SystemMessage


class VisualizerDecisionAgent(BaseAgent):
    """
    Analyzes query results and decides if a chart/visualization would help.
    Always returns a visualization decision (never skips).
    """
    
    def __init__(self):
        super().__init__("VisualizerDecision", max_retries=1)
        self.llm = KalyaniLangChainLLM()
    
    async def process(self, state: AgentState) -> AgentState:
        """Decide if visualization is needed"""
        # Skip if no results or general chat
        if state.intent in [IntentType.GENERAL_CHAT, IntentType.CLARIFICATION_NEEDED]:
            state.visualization_needed = False
            state.visualization_type = VisualizationType.NONE
            state.add_trace(self.name, "Skipped - general chat or clarification")
            return state
        
        if not state.execution_success or state.query_results is None:
            state.visualization_needed = False
            state.visualization_type = VisualizationType.NONE
            state.add_trace(self.name, "Skipped - no query results")
            return state
        
        df = state.query_results
        if len(df) == 0:
            state.visualization_needed = False
            state.visualization_type = VisualizationType.NONE
            state.add_trace(self.name, "Skipped - empty results")
            return state
        
        # Analyze data structure and query intent
        viz_type = await self._decide_visualization(state, df)
        
        state.visualization_type = viz_type
        state.visualization_needed = (viz_type != VisualizationType.NONE)
        
        if state.visualization_needed:
            # Identify fields for the chart
            state.chart_fields = self._identify_chart_fields(df, viz_type)
            state.chart_title = self._generate_chart_title(state)
            state.add_trace(self.name, f"Visualization: {viz_type.value}")
            logger.info(f"[{self.name}] Decision: {viz_type.value}")
        else:
            state.add_trace(self.name, "No visualization needed")
            logger.info(f"[{self.name}] Decision: none")
        
        return state
    
    async def _decide_visualization(self, state: AgentState, df) -> VisualizationType:
        """Use LLM to decide visualization type"""
        query = state.user_query.lower()
        
        # Quick checks first
        if 'chart' in query or 'graph' in query or 'plot' in query:
            # User explicitly wants visualization
            pass
        
        # Check data structure
        numeric_cols = list(df.select_dtypes(include=['number']).columns)
        categorical_cols = list(df.select_dtypes(include=['object', 'category']).columns)
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
        
        # Build analysis prompt
        data_info = f"""
Rows: {len(df)}
Numeric columns: {numeric_cols}
Categorical columns: {categorical_cols}
Date columns: {date_cols}

Sample data (first 3 rows):
{df.head(3).to_string()}
"""
        
        system_prompt = f"""You are a visualization expert. Analyze the query and data to select the best chart type.

User Query: {state.user_query}

Data Structure:
{data_info}

Available Chart Types:
- bar_chart: Comparing categories, rankings, top N items
- line_chart: Trends over time, time series data
- pie_chart: Proportions, percentages of a whole (max 6-8 categories)
- heatmap: Correlations, intensity across two dimensions
- scatter_plot: Relationships between two numeric variables
- histogram: Distribution of a single numeric variable
- none: No chart needed (text/table is sufficient)

Decision Rules:
- If user explicitly asks for a chart type, use that type
- If data has 1-2 numeric columns and categorical: bar_chart
- If date column exists and numeric: line_chart
- If percentages/proportions: pie_chart
- If correlation/comparison matrix: heatmap
- If relationship analysis: scatter_plot

Respond ONLY with a JSON object:
{{
    "chart_type": "bar_chart|line_chart|pie_chart|heatmap|scatter_plot|histogram|none",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="What chart type should be used?")
            ]
            
            result = await self.llm._agenerate(messages)
            raw_response = result.generations[0].message.content.strip()
            
            # Extract JSON
            json_match = re.search(r'\{{.*?\}}', raw_response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(0))
                chart_type = decision.get("chart_type", "none")
                
                try:
                    return VisualizationType(chart_type)
                except ValueError:
                    return VisualizationType.NONE
            else:
                return VisualizationType.NONE
                
        except Exception as e:
            logger.error(f"[{self.name}] Decision error: {e}")
            return VisualizationType.NONE
    
    def _identify_chart_fields(self, df, viz_type: VisualizationType) -> list:
        """Identify which fields to use for the chart"""
        fields = []
        
        numeric_cols = list(df.select_dtypes(include=['number']).columns)
        categorical_cols = list(df.select_dtypes(include=['object', 'category']).columns)
        
        if viz_type == VisualizationType.BAR_CHART:
            # Need 1 categorical + 1 numeric
            if categorical_cols:
                fields.append(categorical_cols[0])  # X-axis
            if numeric_cols:
                fields.append(numeric_cols[0])  # Y-axis
                
        elif viz_type == VisualizationType.LINE_CHART:
            # Need date + numeric
            date_cols = [c for c in df.columns if 'date' in c.lower()]
            if date_cols:
                fields.append(date_cols[0])
            elif categorical_cols:
                fields.append(categorical_cols[0])
            if numeric_cols:
                fields.append(numeric_cols[0])
                
        elif viz_type == VisualizationType.PIE_CHART:
            # Need 1 categorical + 1 numeric
            if categorical_cols:
                fields.append(categorical_cols[0])
            if numeric_cols:
                fields.append(numeric_cols[0])
                
        elif viz_type == VisualizationType.SCATTER_PLOT:
            # Need 2 numeric
            if len(numeric_cols) >= 2:
                fields = numeric_cols[:2]
            elif len(numeric_cols) == 1:
                fields = numeric_cols
        
        return fields
    
    def _generate_chart_title(self, state: AgentState) -> str:
        """Generate a title for the chart"""
        # Simple title based on query
        query = state.user_query
        # Remove common words
        words = query.replace('?', '').replace('.', '').split()
        key_words = [w for w in words if len(w) > 3 and w.lower() not in ['show', 'give', 'what', 'from', 'with', 'have', 'that', 'this', 'would', 'could', 'please']]
        
        if key_words:
            title = " ".join(key_words[:5]).title()
            return title
        else:
            return "Data Visualization"
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """On error, skip visualization"""
        state.visualization_needed = False
        state.visualization_type = VisualizationType.NONE
        state.add_trace(self.name, f"Error, skipping viz: {str(error)}")
        return state
