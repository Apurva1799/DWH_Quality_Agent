from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent, AgentRequest, AgentResponse
from app.llm_manager import llm_manager
from loguru import logger
import pandas as pd
import json

class ResponseAnalyserAgent(BaseAgent):
    """Response Analyser Agent for analyzing and formatting query results using DGX 3B Client"""
    
    def __init__(self):
        super().__init__("Response Analyser Agent")
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process and analyze query results"""
        try:
            # Extract query results from request context
            query_results = self._extract_query_results(request)
            
            if not query_results:
                return AgentResponse(
                    success=False,
                    response="No query results found for analysis",
                    error="Missing query results",
                    agent_name=self.name
                )
            
            # Analyze the results
            analysis = await self._analyze_results(query_results, request.query)
            
            # Generate natural language explanation
            explanation = await self._generate_explanation(query_results, request.query, analysis)
            
            # Store conversation in DocumentDB
            await self._store_conversation(request, query_results, analysis, explanation)
            
            return AgentResponse(
                success=True,
                response=explanation,
                agent_name=self.name,
                data={
                    "analysis": analysis,
                    "results_summary": self._create_results_summary(query_results),
                    "original_query": request.query
                }
            )
            
        except Exception as e:
            logger.error(f"Response Analyser Agent processing error: {str(e)}")
            return AgentResponse(
                success=False,
                response="Response Analyser Agent processing failed",
                error=str(e),
                agent_name=self.name
            )
    
    def _extract_query_results(self, request: AgentRequest) -> Optional[Dict[str, Any]]:
        """Extract query results from request context"""
        try:
            # Check if results are in the context
            if request.context and "result" in request.context:
                return request.context["result"]
            
            # Check if results are in the metadata
            if request.metadata and "result" in request.metadata:
                return request.metadata["result"]
            
            # Check if results are in the data
            if request.data and "result" in request.data:
                return request.data["result"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting query results: {str(e)}")
            return None
    
    async def _analyze_results(self, results: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Analyze query results for insights and patterns"""
        try:
            analysis = {
                "row_count": results.get("row_count", 0),
                "column_count": len(results.get("columns", [])),
                "data_types": {},
                "null_counts": {},
                "value_ranges": {},
                "patterns": [],
                "anomalies": [],
                "insights": []
            }
            
            if not results.get("success") or results.get("row_count", 0) == 0:
                analysis["insights"].append("Query returned no results")
                return analysis
            
            data = results.get("data", [])
            columns = results.get("columns", [])
            
            if not data or not columns:
                return analysis
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(data)
            
            # Analyze each column
            for col in columns:
                if col in df.columns:
                    series = df[col]
                    
                    # Data type analysis
                    analysis["data_types"][col] = str(series.dtype)
                    
                    # Null count analysis
                    null_count = series.isnull().sum()
                    analysis["null_counts"][col] = null_count
                    
                    # Value range analysis for numeric columns
                    if pd.api.types.is_numeric_dtype(series):
                        if series.notna().sum() > 0:
                            analysis["value_ranges"][col] = {
                                "min": float(series.min()),
                                "max": float(series.max()),
                                "mean": float(series.mean()),
                                "median": float(series.median())
                            }
                    
                    # Pattern detection
                    patterns = self._detect_patterns(series, col)
                    if patterns:
                        analysis["patterns"].extend(patterns)
                    
                    # Anomaly detection
                    anomalies = self._detect_anomalies(series, col)
                    if anomalies:
                        analysis["anomalies"].extend(anomalies)
            
            # Generate insights
            analysis["insights"] = self._generate_insights(analysis, original_query)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            return {"error": str(e)}
    
    def _detect_patterns(self, series, column_name: str) -> List[str]:
        """Detect patterns in column data"""
        patterns = []
        
        try:
            # Check for high cardinality
            unique_ratio = series.nunique() / len(series)
            if unique_ratio > 0.9:
                patterns.append(f"{column_name}: High cardinality (mostly unique values)")
            elif unique_ratio < 0.1:
                patterns.append(f"{column_name}: Low cardinality (many repeated values)")
            
            # Check for missing data
            missing_ratio = series.isnull().sum() / len(series)
            if missing_ratio > 0.5:
                patterns.append(f"{column_name}: High missing data ({missing_ratio:.1%})")
            
            # Check for text patterns
            if series.dtype == 'object':
                # Check for email patterns
                if series.str.contains(r'@.*\.', regex=True, na=False).any():
                    patterns.append(f"{column_name}: Contains email addresses")
                
                # Check for phone patterns
                if series.str.contains(r'\d{3}-\d{3}-\d{4}', regex=True, na=False).any():
                    patterns.append(f"{column_name}: Contains phone numbers")
                
                # Check for date patterns
                if series.str.contains(r'\d{4}-\d{2}-\d{2}', regex=True, na=False).any():
                    patterns.append(f"{column_name}: Contains date patterns")
            
        except Exception as e:
            logger.error(f"Error detecting patterns for {column_name}: {str(e)}")
        
        return patterns
    
    def _detect_anomalies(self, series, column_name: str) -> List[str]:
        """Detect anomalies in column data"""
        anomalies = []
        
        try:
            if pd.api.types.is_numeric_dtype(series) and series.notna().sum() > 0:
                # Statistical outlier detection using IQR
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                
                if len(outliers) > 0:
                    anomalies.append(f"{column_name}: {len(outliers)} statistical outliers detected")
            
            # Check for empty strings in text columns
            if series.dtype == 'object':
                empty_strings = (series == '') | (series == ' ') | (series.isnull())
                if empty_strings.sum() > 0:
                    anomalies.append(f"{column_name}: {empty_strings.sum()} empty or null values")
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {column_name}: {str(e)}")
        
        return anomalies
    
    def _generate_insights(self, analysis: Dict[str, Any], original_query: str) -> List[str]:
        """Generate insights from analysis"""
        insights = []
        
        try:
            row_count = analysis.get("row_count", 0)
            
            # General insights
            if row_count == 0:
                insights.append("No data returned from query")
            elif row_count < 10:
                insights.append(f"Small dataset: {row_count} rows returned")
            elif row_count > 10000:
                insights.append(f"Large dataset: {row_count:,} rows returned")
            else:
                insights.append(f"Medium dataset: {row_count:,} rows returned")
            
            # Column insights
            column_count = analysis.get("column_count", 0)
            insights.append(f"Query returned {column_count} columns")
            
            # Data quality insights
            null_counts = analysis.get("null_counts", {})
            high_null_columns = [col for col, count in null_counts.items() if count > row_count * 0.3]
            
            if high_null_columns:
                insights.append(f"High missing data in columns: {', '.join(high_null_columns)}")
            
            # Pattern insights
            patterns = analysis.get("patterns", [])
            if patterns:
                insights.append(f"Data patterns detected: {len(patterns)} patterns found")
            
            # Anomaly insights
            anomalies = analysis.get("anomalies", [])
            if anomalies:
                insights.append(f"Anomalies detected: {len(anomalies)} anomalies found")
            
            # Value range insights
            value_ranges = analysis.get("value_ranges", {})
            if value_ranges:
                insights.append("Numeric columns have been analyzed for value ranges")
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            insights.append("Error occurred during insight generation")
        
        return insights
    
    async def _generate_explanation(
        self, 
        results: Dict[str, Any], 
        original_query: str, 
        analysis: Dict[str, Any]
    ) -> str:
        """Generate natural language explanation using DGX 3B Client"""
        try:
            # Build the explanation prompt
            prompt = self._build_explanation_prompt(original_query, results, analysis)
            
            # Use DGX 3B Client for explanation generation
            result = await llm_manager.generate_with_dgx(
                query=prompt,
                model="qwen-72b",
                temperature=0.3
            )
            
            if not result["success"]:
                logger.error(f"DGX 3B Client error: {result.get('error')}")
                return self._generate_fallback_explanation(results, analysis)
            
            return result["response"].strip()
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return self._generate_fallback_explanation(results, analysis)
    
    def _build_explanation_prompt(self, original_query: str, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Build prompt for explanation generation"""
        
        # Create a summary of the results
        results_summary = {
            "row_count": results.get("row_count", 0),
            "columns": results.get("columns", []),
            "success": results.get("success", False)
        }
        
        # Get key insights
        insights = analysis.get("insights", [])
        patterns = analysis.get("patterns", [])
        anomalies = analysis.get("anomalies", [])
        
        prompt = f"""You are a data analyst. Explain the following SQL query results in natural language.

Original Query:
{original_query}

Results Summary:
- Rows returned: {results_summary['row_count']}
- Columns: {', '.join(results_summary['columns'])}
- Success: {results_summary['success']}

Key Insights:
{chr(10).join(f"- {insight}" for insight in insights) if insights else "- No specific insights detected"}

Patterns Found:
{chr(10).join(f"- {pattern}" for pattern in patterns) if patterns else "- No specific patterns detected"}

Anomalies:
{chr(10).join(f"- {anomaly}" for anomaly in anomalies) if anomalies else "- No anomalies detected"}

Instructions:
1. Provide a clear, natural language explanation of what the query results show
2. Highlight any important patterns or insights
3. Mention any anomalies or data quality issues if relevant
4. Keep the explanation concise and user-friendly
5. Avoid technical SQL terminology
6. Focus on the business meaning of the results

Explanation:
"""
        
        return prompt
    
    def _generate_fallback_explanation(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate fallback explanation without LLM"""
        try:
            row_count = results.get("row_count", 0)
            columns = results.get("columns", [])
            
            explanation = f"Your query returned {row_count} rows"
            
            if columns:
                explanation += f" with {len(columns)} columns: {', '.join(columns[:5])}"
                if len(columns) > 5:
                    explanation += f" and {len(columns) - 5} more columns"
            
            if row_count == 0:
                explanation += ". No data matched your query criteria."
            elif row_count == 1:
                explanation += ". Here's the single result."
            else:
                explanation += f". Here are the results from your database query."
            
            # Add key insights
            insights = analysis.get("insights", [])
            if insights:
                explanation += f"\n\nKey insights: {insights[0]}"
                if len(insights) > 1:
                    explanation += f" and {len(insights) - 1} other observations."
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating fallback explanation: {str(e)}")
            return "Query processed successfully. Results are available for review."
    
    def _create_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the results"""
        try:
            return {
                "row_count": results.get("row_count", 0),
                "column_count": len(results.get("columns", [])),
                "columns": results.get("columns", []),
                "success": results.get("success", False),
                "execution_time": results.get("execution_time"),
                "query": results.get("query")
            }
            
        except Exception as e:
            logger.error(f"Error creating results summary: {str(e)}")
            return {}
    
    async def _store_conversation(
        self, 
        request: AgentRequest, 
        results: Dict[str, Any], 
        analysis: Dict[str, Any], 
        explanation: str
    ) -> bool:
        """Store conversation in DocumentDB"""
        try:
            if not request.user_id or not request.session_id:
                return False
            
            # Prepare conversation data
            conversation_data = {
                "user_id": request.user_id,
                "session_id": request.session_id,
                "query": request.query,
                "response": explanation,
                "query_results": {
                    "row_count": results.get("row_count", 0),
                    "columns": results.get("columns", []),
                    "success": results.get("success", False)
                },
                "analysis": {
                    "insights": analysis.get("insights", []),
                    "patterns": analysis.get("patterns", []),
                    "anomalies": analysis.get("anomalies", [])
                },
                "agent": self.name,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            
            # Store in DocumentDB
            success = await llm_manager.store_conversation(
                user_id=request.user_id,
                session_id=request.session_id,
                message=request.query,
                response=explanation,
                metadata=conversation_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}")
            return False
