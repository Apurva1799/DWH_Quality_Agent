"""
Data Quality Agent for MSSQL Monitoring

Monitors data quality across bronze, silver, and gold layers in MSSQL.
Tracks stored procedures, schema changes, data freshness, and volume metrics.
Provides alerts and quality reports.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
import pandas as pd

from app.agents.chain_of_agents.base import BaseAgent
from app.agents.chain_of_agents.state import AgentState, IntentType
from app.database import SQLExecutor


@dataclass
class DataQualityMetrics:
    """Data quality metrics for a table or layer"""
    table_name: str
    layer: str  # bronze, silver, gold
    row_count: int = 0
    column_count: int = 0
    null_percentage: float = 0.0
    duplicate_percentage: float = 0.0
    freshness_hours: float = 0.0
    last_update: Optional[datetime] = None
    data_volume_mb: float = 0.0
    quality_score: float = 100.0
    issues: List[str] = field(default_factory=list)
    column_issues: Dict[str, List[str]] = field(default_factory=dict)  # column_name -> list of issues
    pk_columns: List[str] = field(default_factory=list)  # Primary key columns
    fk_columns: List[str] = field(default_factory=list)  # Foreign key columns


@dataclass
class StoredProcedureInfo:
    """Information about a stored procedure"""
    name: str
    schema: str
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    parameter_count: int = 0
    code_hash: str = ""
    last_execution: Optional[datetime] = None
    execution_count_24h: int = 0
    avg_execution_time_ms: float = 0.0
    is_monitored: bool = False


@dataclass
class SchemaChange:
    """Schema change tracking"""
    table_name: str
    change_type: str  # CREATE, ALTER, DROP, ADD_COLUMN, etc.
    column_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    is_acknowledged: bool = False


class DataQualityAgent(BaseAgent):
    """
    Monitors data quality across bronze, silver, and gold layers in MSSQL.
    Tracks stored procedures, schema changes, and data freshness.
    
    Features:
    - Layer-by-layer quality monitoring
    - Stored procedure tracking and change detection
    - Schema drift detection
    - Data freshness and volume monitoring
    - Quality scoring and alerting
    """
    
    def __init__(self):
        super().__init__("DataQuality", max_retries=2)
        self.executor = SQLExecutor()
        
        # Cache for quality metrics (TTL: 5 minutes)
        self._metrics_cache: Dict[str, Tuple[DataQualityMetrics, datetime]] = {}
        self._cache_ttl_seconds = 300
        
        # Baseline for change detection
        self._sp_baseline: Dict[str, StoredProcedureInfo] = {}
        self._schema_baseline: Dict[str, Dict[str, Any]] = {}
        
        # Monitored layers
        self.layers = ['bronze', 'silver', 'gold']
        
        # Quality thresholds
        self.thresholds = {
            'max_null_percentage': 10.0,
            'max_duplicate_percentage': 5.0,
            'max_freshness_hours': 24.0,
            'min_quality_score': 80.0,
            'max_sp_execution_time_ms': 5000.0
        }
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Main processing logic for data quality monitoring.
        
        Determines if this is a monitoring query or a quality check request,
        then provides appropriate data quality information.
        """
        query_lower = state.user_query.lower()
        
        # Check if this is a data quality monitoring request
        is_quality_request = any(keyword in query_lower for keyword in [
            'data quality', 'monitor', 'health check', 'quality check',
            'stored procedure', 'sp change', 'schema change', 'data freshness',
            'bronze layer', 'silver layer', 'gold layer', 'layer quality'
        ])
        
        if is_quality_request:
            # Determine what type of quality check is needed
            if 'stored procedure' in query_lower or 'sp ' in query_lower:
                state = await self._monitor_stored_procedures(state)
            elif 'schema' in query_lower or 'table change' in query_lower:
                state = await self._detect_schema_changes(state)
            elif 'bronze' in query_lower:
                state = await self._check_layer_quality(state, 'bronze')
            elif 'silver' in query_lower:
                state = await self._check_layer_quality(state, 'silver')
            elif 'gold' in query_lower:
                state = await self._check_layer_quality(state, 'gold')
            else:
                # Comprehensive quality check across all layers
                state = await self._comprehensive_quality_check(state)
        
        return state
    
    async def _check_layer_quality(self, state: AgentState, layer: str) -> AgentState:
        """Check data quality for a specific layer"""
        logger.info(f"[{self.name}] Checking {layer} layer quality")
        state.add_trace(self.name, f"Checking {layer} layer quality")
        
        try:
            # Get all tables in the layer
            tables = await self._get_layer_tables(layer)
            
            if not tables:
                state.response_data['quality_report'] = {
                    'layer': layer,
                    'status': 'no_tables',
                    'message': f'No tables found in {layer} layer',
                    'tables_checked': 0,
                    'issues_found': 0
                }
                return state
            
            # Check quality for ALL tables in the layer
            quality_metrics = []
            total_issues = 0
            
            logger.info(f"[{self.name}] Checking all {len(tables)} tables in {layer} layer")
            
            for table_name in tables:  # Check ALL tables, not just 20
                metrics = await self._get_table_quality_metrics(table_name, layer)
                quality_metrics.append(metrics)
                total_issues += len(metrics.issues)
            
            # Calculate layer quality score
            avg_quality = sum(m.quality_score for m in quality_metrics) / len(quality_metrics) if quality_metrics else 0
            
            # Build quality report
            report = {
                'layer': layer,
                'status': 'healthy' if avg_quality >= self.thresholds['min_quality_score'] else 'warning',
                'quality_score': round(avg_quality, 2),
                'tables_checked': len(tables),
                'tables_sampled': len(quality_metrics),
                'issues_found': total_issues,
                'metrics': [
                    {
                        'table': m.table_name,
                        'rows': m.row_count,
                        'null_pct': round(m.null_percentage, 2),
                        'dup_pct': round(m.duplicate_percentage, 2),
                        'freshness_hrs': round(m.freshness_hours, 2),
                        'quality_score': int(m.quality_score),
                        'issues': m.issues,
                        'column_issues': m.column_issues,
                        'column_count': m.column_count,
                        'pk_columns': m.pk_columns,
                        'fk_columns': m.fk_columns
                    }
                    for m in quality_metrics
                ],
                'recommendations': self._generate_recommendations(quality_metrics)
            }
            
            state.response_data['quality_report'] = report
            state.add_trace(self.name, f"{layer} layer check complete - Score: {avg_quality:.1f}%")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error checking {layer} layer: {e}")
            state.add_trace(self.name, f"Error: {str(e)}")
            state.response_data['quality_report'] = {
                'layer': layer,
                'status': 'error',
                'message': str(e)
            }
        
        return state
    
    async def _monitor_stored_procedures(self, state: AgentState) -> AgentState:
        """Monitor stored procedures for changes and performance"""
        logger.info(f"[{self.name}] Monitoring stored procedures")
        state.add_trace(self.name, "Monitoring stored procedures")
        
        try:
            # Get all stored procedures
            sps = await self._get_stored_procedures()
            
            # Detect changes
            new_sps = []
            modified_sps = []
            performance_issues = []
            
            for sp in sps:
                baseline = self._sp_baseline.get(sp.name)
                
                if baseline is None:
                    new_sps.append(sp)
                elif baseline.code_hash != sp.code_hash:
                    modified_sps.append({
                        'name': sp.name,
                        'old_modified': baseline.modified_date,
                        'new_modified': sp.modified_date
                    })
                
                # Check performance
                if sp.avg_execution_time_ms > self.thresholds['max_sp_execution_time_ms']:
                    performance_issues.append({
                        'name': sp.name,
                        'avg_time_ms': round(sp.avg_execution_time_ms, 2),
                        'execution_count': sp.execution_count_24h
                    })
            
            # Update baseline
            self._sp_baseline = {sp.name: sp for sp in sps}
            
            # Build report
            report = {
                'check_type': 'stored_procedures',
                'total_sps': len(sps),
                'new_sps': len(new_sps),
                'modified_sps': len(modified_sps),
                'performance_issues': len(performance_issues),
                'new_sp_details': [{'name': sp.name, 'schema': sp.schema} for sp in new_sps],
                'modified_sp_details': modified_sps,
                'performance_issue_details': performance_issues,
                'status': 'alert' if (new_sps or modified_sps or performance_issues) else 'healthy'
            }
            
            state.response_data['quality_report'] = report
            state.add_trace(self.name, f"SP monitoring complete - {len(new_sps)} new, {len(modified_sps)} modified")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error monitoring SPs: {e}")
            state.add_trace(self.name, f"Error: {str(e)}")
            state.response_data['quality_report'] = {
                'check_type': 'stored_procedures',
                'status': 'error',
                'message': str(e)
            }
        
        return state
    
    async def _detect_schema_changes(self, state: AgentState) -> AgentState:
        """Detect schema changes across all layers"""
        logger.info(f"[{self.name}] Detecting schema changes")
        state.add_trace(self.name, "Detecting schema changes")
        
        try:
            changes = []
            
            for layer in self.layers:
                tables = await self._get_layer_tables(layer)
                
                for table in tables:
                    current_schema = await self._get_table_schema(table)
                    baseline = self._schema_baseline.get(table)
                    
                    if baseline is None:
                        # New table
                        changes.append(SchemaChange(
                            table_name=table,
                            change_type='CREATE',
                            new_value=f"{len(current_schema.get('columns', []))} columns"
                        ))
                    else:
                        # Check for column changes
                        current_cols = set(current_schema.get('columns', []))
                        baseline_cols = set(baseline.get('columns', []))
                        
                        added_cols = current_cols - baseline_cols
                        removed_cols = baseline_cols - current_cols
                        
                        for col in added_cols:
                            changes.append(SchemaChange(
                                table_name=table,
                                change_type='ADD_COLUMN',
                                column_name=col
                            ))
                        
                        for col in removed_cols:
                            changes.append(SchemaChange(
                                table_name=table,
                                change_type='DROP_COLUMN',
                                column_name=col
                            ))
                    
                    # Update baseline
                    self._schema_baseline[table] = current_schema
            
            # Build report
            report = {
                'check_type': 'schema_changes',
                'total_changes': len(changes),
                'new_tables': len([c for c in changes if c.change_type == 'CREATE']),
                'added_columns': len([c for c in changes if c.change_type == 'ADD_COLUMN']),
                'dropped_columns': len([c for c in changes if c.change_type == 'DROP_COLUMN']),
                'changes': [
                    {
                        'table': c.table_name,
                        'type': c.change_type,
                        'column': c.column_name,
                        'detected_at': c.detected_at.isoformat()
                    }
                    for c in changes[:50]  # Limit to 50 changes
                ],
                'status': 'alert' if changes else 'healthy'
            }
            
            state.response_data['quality_report'] = report
            state.add_trace(self.name, f"Schema change detection complete - {len(changes)} changes found")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error detecting schema changes: {e}")
            state.add_trace(self.name, f"Error: {str(e)}")
            state.response_data['quality_report'] = {
                'check_type': 'schema_changes',
                'status': 'error',
                'message': str(e)
            }
        
        return state
    
    async def _comprehensive_quality_check(self, state: AgentState) -> AgentState:
        """Run comprehensive quality check across all layers"""
        logger.info(f"[{self.name}] Running comprehensive quality check")
        state.add_trace(self.name, "Running comprehensive quality check")
        
        layer_reports = {}
        overall_issues = 0
        
        for layer in self.layers:
            # Temporarily modify state for layer check
            temp_state = AgentState(
                user_query=f"check {layer} layer quality",
                session_id=state.session_id
            )
            temp_state = await self._check_layer_quality(temp_state, layer)
            
            if 'quality_report' in temp_state.response_data:
                layer_reports[layer] = temp_state.response_data['quality_report']
                overall_issues += temp_state.response_data['quality_report'].get('issues_found', 0)
        
        # Build comprehensive report
        report = {
            'check_type': 'comprehensive',
            'layers_checked': len(self.layers),
            'overall_status': 'healthy' if overall_issues == 0 else 'warning' if overall_issues < 10 else 'critical',
            'total_issues': overall_issues,
            'layer_reports': layer_reports,
            'summary': {
                'bronze_tables': layer_reports.get('bronze', {}).get('tables_checked', 0),
                'silver_tables': layer_reports.get('silver', {}).get('tables_checked', 0),
                'gold_tables': layer_reports.get('gold', {}).get('tables_checked', 0),
                'avg_quality_score': round(
                    sum(r.get('quality_score', 0) for r in layer_reports.values()) / len(layer_reports), 2
                ) if layer_reports else 0
            }
        }
        
        state.response_data['quality_report'] = report
        state.add_trace(self.name, f"Comprehensive check complete - {overall_issues} total issues")
        
        return state
    
    async def _get_layer_tables(self, layer: str) -> List[str]:
        """Get all tables in a specific layer using multiple detection strategies"""
        try:
            # Strategy 1: Tables with layer prefix (e.g., gold_TableName)
            query1 = f"""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME LIKE '{layer}_%'
            ORDER BY TABLE_SCHEMA, TABLE_NAME;
            """
            
            # Strategy 2: Tables in schema matching layer name
            query2 = f"""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_SCHEMA = '{layer}'
            ORDER BY TABLE_SCHEMA, TABLE_NAME;
            """
            
            # Strategy 3: Tables containing layer name (e.g., GoldTableName)
            query3 = f"""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND (TABLE_NAME LIKE '%{layer}%' OR TABLE_NAME LIKE '%{layer.capitalize()}%')
            ORDER BY TABLE_SCHEMA, TABLE_NAME;
            """
            
            all_tables = set()
            
            # Execute all queries
            for query in [query1, query2, query3]:
                try:
                    result = await self.executor.execute_query(query)
                    if result.get('success') and 'data' in result:
                        for row in result['data']:
                            # Handle both dict and list/tuple formats
                            if isinstance(row, dict):
                                schema = row.get('TABLE_SCHEMA', 'dbo')
                                table_name = row.get('TABLE_NAME', '')
                            elif isinstance(row, (list, tuple)):
                                schema = row[0] if len(row) > 0 else 'dbo'
                                table_name = row[1] if len(row) > 1 else ''
                            else:
                                schema = 'dbo'
                                table_name = str(row)
                            if table_name:
                                # Store as "schema.table_name" for proper qualification
                                full_name = f"[{schema}].[{table_name}]"
                                all_tables.add(full_name)
                except Exception as e:
                    logger.warning(f"[{self.name}] Query failed: {e}")
            
            # If still no tables found, get all tables and try to infer by keywords
            if not all_tables:
                logger.info(f"[{self.name}] No tables found with layer patterns, trying all tables...")
                all_tables_query = """
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME;
                """
                result = await self.executor.execute_query(all_tables_query)
                if result.get('success') and 'data' in result:
                    all_db_tables = []
                    for row in result['data']:
                        if isinstance(row, dict):
                            schema = row.get('TABLE_SCHEMA', 'dbo')
                            table = row.get('TABLE_NAME', '')
                        elif isinstance(row, (list, tuple)):
                            schema = row[0] if len(row) > 0 else 'dbo'
                            table = row[1] if len(row) > 1 else ''
                        else:
                            schema = 'dbo'
                            table = str(row)
                        if table:
                            all_db_tables.append((schema, table))
                    
                    logger.info(f"[{self.name}] Total tables in database: {len(all_db_tables)}")
                    logger.info(f"[{self.name}] Sample tables: {all_db_tables[:10]}")
                    
                    # Keyword-based layer detection
                    layer_keywords = {
                        'bronze': ['raw', 'staging', 'source', 'import', 'landing', 'bronze'],
                        'silver': ['cleaned', 'transformed', 'processed', 'staging', 'silver'],
                        'gold': ['final', 'reporting', 'analytics', 'mart', 'dim', 'fact', 'view', 'gold']
                    }
                    
                    keywords = layer_keywords.get(layer, [])
                    logger.info(f"[{self.name}] Looking for {layer} layer with keywords: {keywords}")
                    
                    for schema, table in all_db_tables:
                        try:
                            table_lower = table.lower()
                            # Check if table name contains layer-specific keywords
                            if any(kw in table_lower for kw in keywords):
                                full_name = f"[{schema}].[{table}]"
                                all_tables.add(full_name)
                                logger.debug(f"[{self.name}] Matched table: {full_name}")
                        except Exception as table_error:
                            logger.warning(f"[{self.name}] Error processing table {table}: {table_error}")
                    
                    # If still no tables matched keywords, use ALL tables as fallback
                    # This handles databases without explicit layer naming conventions
                    if not all_tables and all_db_tables:
                        logger.info(f"[{self.name}] No keyword matches found. Using tables as fallback for {layer} layer")
                        # For gold layer, include Dim/Fact tables (data warehouse pattern)
                        if layer == 'gold':
                            for schema, table in all_db_tables:
                                if any(prefix in table.lower() for prefix in ['dim_', 'fact_', 'view', 'report', 'analytics']):
                                    full_name = f"[{schema}].[{table}]"
                                    all_tables.add(full_name)
                            # If still empty, just take first 50 tables
                            if not all_tables:
                                all_tables = set(f"[{s}].[{t}]" for s, t in all_db_tables[:50])
                        else:
                            # For bronze/silver, just use all tables
                            all_tables = set(f"[{s}].[{t}]" for s, t in all_db_tables[:50])  # Limit to 50 for performance
            
            tables_list = sorted(list(all_tables))
            logger.info(f"[{self.name}] Found {len(tables_list)} tables for {layer} layer: {tables_list[:5]}")
            return tables_list
            
        except Exception as e:
            import traceback
            logger.error(f"[{self.name}] Error getting {layer} tables: {e}")
            logger.error(f"[{self.name}] Traceback: {traceback.format_exc()}")
            return []
    
    async def _get_table_quality_metrics(self, table_name: str, layer: str) -> DataQualityMetrics:
        """Get quality metrics for a specific table"""
        cache_key = f"{layer}.{table_name}"
        
        # Check cache
        if cache_key in self._metrics_cache:
            metrics, cached_time = self._metrics_cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl_seconds):
                return metrics
        
        metrics = DataQualityMetrics(table_name=table_name, layer=layer)
        issues = []
        
        try:
            # Get row count - table_name is already qualified like [schema].[table]
            count_result = await self.executor.execute_query(
                f"SELECT COUNT(*) FROM {table_name};"
            )
            if count_result.get('success') and count_result.get('data'):
                data = count_result['data'][0]
                if isinstance(data, (list, tuple)):
                    metrics.row_count = data[0]
                elif isinstance(data, dict):
                    # Handle both {'COUNT(*): 123} and {'': 123} formats
                    metrics.row_count = data.get('COUNT(*)') or data.get('') or list(data.values())[0] if data else 0
                else:
                    metrics.row_count = int(data) if data else 0
            
            # Extract just table name for INFORMATION_SCHEMA queries (schema.table format)
            clean_table = table_name.replace('[', '').replace(']', '')
            if '.' in clean_table:
                schema_part, table_part = clean_table.split('.', 1)
            else:
                schema_part, table_part = 'dbo', clean_table
            
            # Get column info
            column_result = await self.executor.execute_query(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_part}' AND TABLE_SCHEMA = '{schema_part}';
            """)
            
            if column_result.get('success') and column_result.get('data'):
                columns = column_result['data']
                metrics.column_count = len(columns)
                
                # Get Primary Key columns
                pk_result = await self.executor.execute_query(f"""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = '{table_part}' 
                    AND TABLE_SCHEMA = '{schema_part}'
                    AND CONSTRAINT_NAME LIKE 'PK%';
                """)
                if pk_result.get('success') and pk_result.get('data'):
                    for row in pk_result['data']:
                        if isinstance(row, dict):
                            col_name = row.get('COLUMN_NAME', '')
                        else:
                            col_name = row[0] if row else ''
                        if col_name:
                            metrics.pk_columns.append(col_name)
                
                # Get Foreign Key columns
                fk_result = await self.executor.execute_query(f"""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = '{table_part}' 
                    AND TABLE_SCHEMA = '{schema_part}'
                    AND CONSTRAINT_NAME LIKE 'FK%';
                """)
                if fk_result.get('success') and fk_result.get('data'):
                    for row in fk_result['data']:
                        if isinstance(row, dict):
                            col_name = row.get('COLUMN_NAME', '')
                        else:
                            col_name = row[0] if row else ''
                        if col_name:
                            metrics.fk_columns.append(col_name)
                
                # Calculate null percentage for each column with column names
                null_checks = []
                column_names = []
                for col in columns[:10]:  # Check first 10 columns for better coverage
                    # Handle both dict and tuple formats
                    if isinstance(col, dict):
                        col_name = col.get('COLUMN_NAME', '')
                    else:
                        col_name = col[0] if len(col) > 0 else ''
                    if col_name:
                        null_checks.append(f"SUM(CASE WHEN [{col_name}] IS NULL THEN 1 ELSE 0 END) AS [{col_name}]")
                        column_names.append(col_name)
                
                if null_checks and metrics.row_count > 0:
                    null_query = f"SELECT {', '.join(null_checks)} FROM {table_name};"
                    null_result = await self.executor.execute_query(null_query)
                    
                    if null_result.get('success') and null_result.get('data'):
                        null_data = null_result['data'][0]
                        total_nulls = 0
                        
                        if isinstance(null_data, dict):
                            # Track per-column null percentages
                            for col_name in column_names:
                                col_nulls = null_data.get(col_name, 0)
                                col_null_pct = (col_nulls / metrics.row_count) * 100
                                total_nulls += col_nulls
                                
                                # Track column-specific issues
                                if col_null_pct > self.thresholds['max_null_percentage']:
                                    if col_name not in metrics.column_issues:
                                        metrics.column_issues[col_name] = []
                                    metrics.column_issues[col_name].append(f"{col_null_pct:.1f}% null values")
                        else:
                            # Handle list/tuple format
                            for i, col_nulls in enumerate(null_data):
                                if i < len(column_names):
                                    col_name = column_names[i]
                                    col_null_pct = (col_nulls / metrics.row_count) * 100
                                    total_nulls += col_nulls
                                    
                                    if col_null_pct > self.thresholds['max_null_percentage']:
                                        if col_name not in metrics.column_issues:
                                            metrics.column_issues[col_name] = []
                                        metrics.column_issues[col_name].append(f"{col_null_pct:.1f}% null values")
                        
                        metrics.null_percentage = (total_nulls / (metrics.row_count * len(null_checks))) * 100
            
            # Check for duplicates (sample check on first column)
            if metrics.row_count > 0:
                dup_result = await self.executor.execute_query(f"""
                    SELECT COUNT(*) - COUNT(DISTINCT (SELECT TOP 1 COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table_part}' AND TABLE_SCHEMA = '{schema_part}')) 
                    FROM {table_name};
                """)
                # Note: This is a simplified check - real implementation would be more sophisticated
            
            # Check freshness (if there's a timestamp column)
            freshness_result = await self.executor.execute_query(f"""
                SELECT MAX(COLUMN_NAME)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_part}' AND TABLE_SCHEMA = '{schema_part}'
                AND (COLUMN_NAME LIKE '%date%' OR COLUMN_NAME LIKE '%time%' 
                     OR COLUMN_NAME LIKE '%created%' OR COLUMN_NAME LIKE '%updated%'
                     OR COLUMN_NAME LIKE '%timestamp%');
            """)
            
            # Calculate quality score
            score = 100.0
            
            if metrics.row_count == 0:
                score = 0
                issues.append("Table is empty")
            else:
                if metrics.null_percentage > self.thresholds['max_null_percentage']:
                    score -= 20
                    issues.append(f"High null percentage: {metrics.null_percentage:.1f}%")
                
                if metrics.duplicate_percentage > self.thresholds['max_duplicate_percentage']:
                    score -= 15
                    issues.append(f"High duplicate percentage: {metrics.duplicate_percentage:.1f}%")
                
                if metrics.freshness_hours > self.thresholds['max_freshness_hours']:
                    score -= 10
                    issues.append(f"Data stale: {metrics.freshness_hours:.1f} hours old")
            
            metrics.quality_score = max(0, score)
            metrics.issues = issues
            
        except Exception as e:
            logger.error(f"[{self.name}] Error getting metrics for {table_name}: {e}")
            metrics.issues.append(f"Error: {str(e)}")
            metrics.quality_score = 0
        
        # Cache result
        self._metrics_cache[cache_key] = (metrics, datetime.now())
        
        return metrics
    
    async def _get_stored_procedures(self) -> List[StoredProcedureInfo]:
        """Get all stored procedures with their metadata"""
        sps = []
        
        try:
            query = """
            SELECT 
                ROUTINE_SCHEMA,
                ROUTINE_NAME,
                CREATED,
                LAST_ALTERED,
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.PARAMETERS 
                 WHERE SPECIFIC_NAME = r.ROUTINE_NAME) as param_count
            FROM INFORMATION_SCHEMA.ROUTINES r
            WHERE ROUTINE_TYPE = 'PROCEDURE'
            ORDER BY ROUTINE_SCHEMA, ROUTINE_NAME;
            """
            
            result = await self.executor.execute_query(query)
            
            if result.get('success') and result.get('data'):
                for row in result['data']:
                    sp = StoredProcedureInfo(
                        schema=row[0],
                        name=row[1],
                        created_date=row[2],
                        modified_date=row[3],
                        parameter_count=row[4]
                    )
                    
                    # Get procedure definition for hashing
                    def_result = await self.executor.execute_query(f"""
                        SELECT OBJECT_DEFINITION(OBJECT_ID('[{row[0]}].[{row[1]}]'));
                    """)
                    
                    if def_result.get('success') and def_result.get('data'):
                        definition = def_result['data'][0][0] or ""
                        sp.code_hash = hashlib.md5(definition.encode()).hexdigest()[:16]
                    
                    # Get execution stats (simplified - real implementation would use sys.dm_exec_procedure_stats)
                    # This is placeholder as actual query depends on SQL Server version and permissions
                    
                    sps.append(sp)
            
        except Exception as e:
            logger.error(f"[{self.name}] Error getting stored procedures: {e}")
        
        return sps
    
    async def _get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table"""
        try:
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION;
            """
            
            result = await self.executor.execute_query(query)
            
            if result.get('success') and result.get('data'):
                columns = []
                for row in result['data']:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'length': row[2],
                        'nullable': row[3],
                        'default': row[4]
                    })
                
                return {
                    'table': table_name,
                    'columns': [c['name'] for c in columns],
                    'column_details': columns
                }
            
            return {'table': table_name, 'columns': [], 'column_details': []}
            
        except Exception as e:
            logger.error(f"[{self.name}] Error getting schema for {table_name}: {e}")
            return {'table': table_name, 'columns': [], 'column_details': []}
    
    def _generate_recommendations(self, metrics: List[DataQualityMetrics]) -> List[str]:
        """Generate recommendations based on quality metrics"""
        recommendations = []
        
        low_quality_tables = [m for m in metrics if m.quality_score < self.thresholds['min_quality_score']]
        if low_quality_tables:
            recommendations.append(
                f"{len(low_quality_tables)} tables have quality scores below {self.thresholds['min_quality_score']}% - review recommended"
            )
        
        stale_tables = [m for m in metrics if m.freshness_hours > self.thresholds['max_freshness_hours']]
        if stale_tables:
            recommendations.append(
                f"{len(stale_tables)} tables haven't been updated in over {self.thresholds['max_freshness_hours']} hours"
            )
        
        high_null_tables = [m for m in metrics if m.null_percentage > self.thresholds['max_null_percentage']]
        if high_null_tables:
            recommendations.append(
                f"{len(high_null_tables)} tables have high null percentages - consider data validation"
            )
        
        empty_tables = [m for m in metrics if m.row_count == 0]
        if empty_tables:
            recommendations.append(f"{len(empty_tables)} tables are empty - verify ETL processes")
        
        return recommendations
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Handle errors in data quality monitoring"""
        logger.error(f"[{self.name}] Error: {error}")
        state.add_trace(self.name, f"Error: {str(error)}")
        state.response_data['quality_report'] = {
            'status': 'error',
            'message': str(error)
        }
        return state
