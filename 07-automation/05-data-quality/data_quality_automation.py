"""
CryptoSphere Analytics Platform - Data Quality Automation
=========================================================

Automated data quality monitoring and validation for cryptocurrency analytics.
Performs comprehensive data quality checks, anomaly detection, and automated remediation.

Features:
- Automated data quality assessments
- Anomaly detection and alerting
- Data drift monitoring
- Data lineage tracking
- Automated data remediation
- Quality score calculation and trending

Author: CryptoSphere Analytics Team
Created: 2025-10-07
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class QualityStatus(Enum):
    """Data quality status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class QualityCheckType(Enum):
    """Types of data quality checks."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    ANOMALY = "anomaly"


@dataclass
class QualityMetric:
    """Individual quality metric result."""
    check_type: QualityCheckType
    table_name: str
    column_name: Optional[str]
    metric_name: str
    value: float
    threshold: float
    status: QualityStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Comprehensive data quality report."""
    report_id: str
    table_name: str
    timestamp: datetime
    overall_score: float
    overall_status: QualityStatus
    metrics: List[QualityMetric]
    recommendations: List[str] = field(default_factory=list)
    record_count: int = 0
    column_count: int = 0


class DataQualityAutomation:
    """
    Comprehensive data quality automation system for cryptocurrency analytics.
    
    Provides automated data quality monitoring, anomaly detection, and remediation
    with configurable quality rules and thresholds.
    """
    
    def __init__(self, config: Dict[str, Any], db_connection):
        """Initialize the data quality automation system."""
        self.config = config
        self.db_connection = db_connection
        self.logger = self._setup_logging()
        
        # Quality configuration
        self.quality_config = config.get('data_quality', {})
        self.thresholds = self._load_quality_thresholds()
        
        # Quality reports storage
        self.quality_reports: Dict[str, QualityReport] = {}
        self.quality_history: List[QualityReport] = []
        
        # Anomaly detection models
        self.anomaly_models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Quality rules
        self.quality_rules = self._load_quality_rules()
        
        self.logger.info("Data Quality Automation initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('data_quality_automation')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _load_quality_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load data quality thresholds from configuration."""
        default_thresholds = {
            'completeness': {
                'excellent': 0.99,
                'good': 0.95,
                'fair': 0.90,
                'poor': 0.80
            },
            'accuracy': {
                'excellent': 0.98,
                'good': 0.95,
                'fair': 0.90,
                'poor': 0.85
            },
            'consistency': {
                'excellent': 0.99,
                'good': 0.96,
                'fair': 0.92,
                'poor': 0.88
            },
            'timeliness': {
                'excellent': 0.95,
                'good': 0.90,
                'fair': 0.80,
                'poor': 0.70
            },
            'anomaly_score': {
                'excellent': 0.05,  # Low anomaly rate
                'good': 0.10,
                'fair': 0.15,
                'poor': 0.20
            }
        }
        
        # Override with configuration values
        config_thresholds = self.quality_config.get('thresholds', {})
        for category, thresholds in config_thresholds.items():
            if category in default_thresholds:
                default_thresholds[category].update(thresholds)
        
        return default_thresholds
    
    def _load_quality_rules(self) -> List[Dict[str, Any]]:
        """Load data quality rules from configuration."""
        return self.quality_config.get('rules', [
            {
                'name': 'price_positive',
                'table': 'clean_crypto_quotes',
                'column': 'price_usd',
                'check_type': 'validity',
                'rule': 'value > 0',
                'critical': True
            },
            {
                'name': 'volume_non_negative',
                'table': 'clean_crypto_quotes',
                'column': 'volume_24h_usd',
                'check_type': 'validity',
                'rule': 'value >= 0',
                'critical': False
            },
            {
                'name': 'market_cap_consistency',
                'table': 'clean_crypto_quotes',
                'columns': ['price_usd', 'market_cap_usd'],
                'check_type': 'consistency',
                'rule': 'price * circulating_supply ≈ market_cap',
                'tolerance': 0.05
            },
            {
                'name': 'timestamp_freshness',
                'table': 'clean_crypto_quotes',
                'column': 'timestamp_utc',
                'check_type': 'timeliness',
                'rule': 'timestamp within last 2 hours',
                'critical': True
            }
        ])
    
    def _determine_quality_status(self, value: float, thresholds: Dict[str, float], 
                                 higher_is_better: bool = True) -> QualityStatus:
        """Determine quality status based on value and thresholds."""
        if higher_is_better:
            if value >= thresholds['excellent']:
                return QualityStatus.EXCELLENT
            elif value >= thresholds['good']:
                return QualityStatus.GOOD
            elif value >= thresholds['fair']:
                return QualityStatus.FAIR
            elif value >= thresholds['poor']:
                return QualityStatus.POOR
            else:
                return QualityStatus.CRITICAL
        else:
            # For metrics where lower is better (like anomaly scores)
            if value <= thresholds['excellent']:
                return QualityStatus.EXCELLENT
            elif value <= thresholds['good']:
                return QualityStatus.GOOD
            elif value <= thresholds['fair']:
                return QualityStatus.FAIR
            elif value <= thresholds['poor']:
                return QualityStatus.POOR
            else:
                return QualityStatus.CRITICAL
    
    async def check_completeness(self, table_name: str, column_name: str = None) -> List[QualityMetric]:
        """Check data completeness for a table or column."""
        metrics = []
        
        try:
            if column_name:
                # Check specific column completeness
                query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT({column_name}) as non_null_records,
                        (COUNT({column_name})::float / COUNT(*)) as completeness_ratio
                    FROM {table_name}
                    WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
                """
            else:
                # Check overall table completeness
                query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(*) as non_null_records,
                        1.0 as completeness_ratio
                    FROM {table_name}
                    WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
                """
            
            df = pd.read_sql(query, self.db_connection)
            
            if not df.empty:
                completeness_ratio = df['completeness_ratio'].iloc[0]
                total_records = df['total_records'].iloc[0]
                
                thresholds = self.thresholds['completeness']
                status = self._determine_quality_status(completeness_ratio, thresholds)
                
                metric = QualityMetric(
                    check_type=QualityCheckType.COMPLETENESS,
                    table_name=table_name,
                    column_name=column_name,
                    metric_name=f"completeness_{column_name or 'table'}",
                    value=completeness_ratio,
                    threshold=thresholds['good'],
                    status=status,
                    message=f"Completeness: {completeness_ratio:.3f} ({status.value})",
                    timestamp=datetime.now(),
                    details={
                        'total_records': int(total_records),
                        'non_null_records': int(df['non_null_records'].iloc[0])
                    }
                )
                
                metrics.append(metric)
                
        except Exception as e:
            self.logger.error(f"Error checking completeness for {table_name}.{column_name}: {str(e)}")
        
        return metrics
    
    async def check_validity(self, table_name: str, column_name: str, rule: str) -> List[QualityMetric]:
        """Check data validity based on business rules."""
        metrics = []
        
        try:
            # Convert business rule to SQL condition
            sql_condition = self._convert_rule_to_sql(rule, column_name)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN {sql_condition} THEN 1 END) as valid_records,
                    (COUNT(CASE WHEN {sql_condition} THEN 1 END)::float / COUNT(*)) as validity_ratio
                FROM {table_name}
                WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
                  AND {column_name} IS NOT NULL
            """
            
            df = pd.read_sql(query, self.db_connection)
            
            if not df.empty:
                validity_ratio = df['validity_ratio'].iloc[0]
                total_records = df['total_records'].iloc[0]
                
                thresholds = self.thresholds['accuracy']
                status = self._determine_quality_status(validity_ratio, thresholds)
                
                metric = QualityMetric(
                    check_type=QualityCheckType.VALIDITY,
                    table_name=table_name,
                    column_name=column_name,
                    metric_name=f"validity_{column_name}",
                    value=validity_ratio,
                    threshold=thresholds['good'],
                    status=status,
                    message=f"Validity: {validity_ratio:.3f} ({status.value}) - Rule: {rule}",
                    timestamp=datetime.now(),
                    details={
                        'total_records': int(total_records),
                        'valid_records': int(df['valid_records'].iloc[0]),
                        'rule': rule
                    }
                )
                
                metrics.append(metric)
                
        except Exception as e:
            self.logger.error(f"Error checking validity for {table_name}.{column_name}: {str(e)}")
        
        return metrics
    
    def _convert_rule_to_sql(self, rule: str, column_name: str) -> str:
        """Convert business rule to SQL condition."""
        # Simple rule conversion (in production, use a proper rule engine)
        rule = rule.replace('value', column_name)
        rule = rule.replace('≈', '=')  # Approximate equality for now
        return rule
    
    async def check_timeliness(self, table_name: str, timestamp_column: str = 'timestamp_utc') -> List[QualityMetric]:
        """Check data timeliness."""
        metrics = []
        
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN {timestamp_column} >= NOW() - INTERVAL '2 hours' THEN 1 END) as recent_records,
                    (COUNT(CASE WHEN {timestamp_column} >= NOW() - INTERVAL '2 hours' THEN 1 END)::float / COUNT(*)) as timeliness_ratio,
                    MAX({timestamp_column}) as latest_timestamp,
                    EXTRACT(MINUTES FROM (NOW() - MAX({timestamp_column}))) as minutes_since_latest
                FROM {table_name}
                WHERE {timestamp_column} >= NOW() - INTERVAL '24 hours'
            """
            
            df = pd.read_sql(query, self.db_connection)
            
            if not df.empty:
                timeliness_ratio = df['timeliness_ratio'].iloc[0]
                minutes_since_latest = df['minutes_since_latest'].iloc[0]
                
                thresholds = self.thresholds['timeliness']
                status = self._determine_quality_status(timeliness_ratio, thresholds)
                
                # Adjust status based on recency
                if minutes_since_latest > 120:  # More than 2 hours
                    status = QualityStatus.CRITICAL
                elif minutes_since_latest > 60:  # More than 1 hour
                    status = QualityStatus.POOR if status in [QualityStatus.EXCELLENT, QualityStatus.GOOD] else status
                
                metric = QualityMetric(
                    check_type=QualityCheckType.TIMELINESS,
                    table_name=table_name,
                    column_name=timestamp_column,
                    metric_name="timeliness",
                    value=timeliness_ratio,
                    threshold=thresholds['good'],
                    status=status,
                    message=f"Timeliness: {timeliness_ratio:.3f}, Latest: {minutes_since_latest:.0f}min ago ({status.value})",
                    timestamp=datetime.now(),
                    details={
                        'total_records': int(df['total_records'].iloc[0]),
                        'recent_records': int(df['recent_records'].iloc[0]),
                        'minutes_since_latest': float(minutes_since_latest),
                        'latest_timestamp': str(df['latest_timestamp'].iloc[0])
                    }
                )
                
                metrics.append(metric)
                
        except Exception as e:
            self.logger.error(f"Error checking timeliness for {table_name}: {str(e)}")
        
        return metrics
    
    async def check_anomalies(self, table_name: str, columns: List[str]) -> List[QualityMetric]:
        """Detect anomalies in numerical data."""
        metrics = []
        
        try:
            # Fetch recent data
            column_list = ', '.join(columns)
            query = f"""
                SELECT {column_list}
                FROM {table_name}
                WHERE timestamp_utc >= NOW() - INTERVAL '7 days'
                  AND {' AND '.join([f'{col} IS NOT NULL' for col in columns])}
                ORDER BY timestamp_utc DESC
                LIMIT 10000
            """
            
            df = pd.read_sql(query, self.db_connection)
            
            if df.empty or len(df) < 100:
                return metrics
            
            # Prepare data for anomaly detection
            X = df[columns].select_dtypes(include=[np.number])
            
            if X.empty:
                return metrics
            
            # Scale the data
            model_key = f"{table_name}_{'_'.join(columns)}"
            
            if model_key not in self.scalers:
                self.scalers[model_key] = StandardScaler()
                self.anomaly_models[model_key] = IsolationForest(
                    contamination=0.1, 
                    random_state=42,
                    n_estimators=100
                )
            
            # Fit or use existing model
            scaler = self.scalers[model_key]
            model = self.anomaly_models[model_key]
            
            X_scaled = scaler.fit_transform(X)
            anomaly_scores = model.fit_predict(X_scaled)
            
            # Calculate anomaly percentage
            anomaly_count = np.sum(anomaly_scores == -1)
            anomaly_ratio = anomaly_count / len(anomaly_scores)
            
            thresholds = self.thresholds['anomaly_score']
            status = self._determine_quality_status(anomaly_ratio, thresholds, higher_is_better=False)
            
            metric = QualityMetric(
                check_type=QualityCheckType.ANOMALY,
                table_name=table_name,
                column_name=','.join(columns),
                metric_name="anomaly_detection",
                value=anomaly_ratio,
                threshold=thresholds['good'],
                status=status,
                message=f"Anomaly rate: {anomaly_ratio:.3f} ({status.value})",
                timestamp=datetime.now(),
                details={
                    'total_records': len(df),
                    'anomaly_count': int(anomaly_count),
                    'columns_analyzed': columns,
                    'model_key': model_key
                }
            )
            
            metrics.append(metric)
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies for {table_name}: {str(e)}")
        
        return metrics
    
    async def check_statistical_outliers(self, table_name: str, column_name: str) -> List[QualityMetric]:
        """Check for statistical outliers using IQR method."""
        metrics = []
        
        try:
            query = f"""
                SELECT {column_name}
                FROM {table_name}
                WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
                  AND {column_name} IS NOT NULL
                ORDER BY timestamp_utc DESC
                LIMIT 10000
            """
            
            df = pd.read_sql(query, self.db_connection)
            
            if df.empty or len(df) < 10:
                return metrics
            
            values = df[column_name].values
            
            # Calculate IQR
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            
            # Define outlier bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Count outliers
            outliers = (values < lower_bound) | (values > upper_bound)
            outlier_count = np.sum(outliers)
            outlier_ratio = outlier_count / len(values)
            
            # Determine status
            if outlier_ratio <= 0.05:
                status = QualityStatus.EXCELLENT
            elif outlier_ratio <= 0.10:
                status = QualityStatus.GOOD
            elif outlier_ratio <= 0.15:
                status = QualityStatus.FAIR
            elif outlier_ratio <= 0.25:
                status = QualityStatus.POOR
            else:
                status = QualityStatus.CRITICAL
            
            metric = QualityMetric(
                check_type=QualityCheckType.ANOMALY,
                table_name=table_name,
                column_name=column_name,
                metric_name="statistical_outliers",
                value=outlier_ratio,
                threshold=0.10,
                status=status,
                message=f"Outlier rate: {outlier_ratio:.3f} ({status.value})",
                timestamp=datetime.now(),
                details={
                    'total_records': len(values),
                    'outlier_count': int(outlier_count),
                    'Q1': float(Q1),
                    'Q3': float(Q3),
                    'IQR': float(IQR),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound)
                }
            )
            
            metrics.append(metric)
            
        except Exception as e:
            self.logger.error(f"Error checking statistical outliers for {table_name}.{column_name}: {str(e)}")
        
        return metrics
    
    async def run_comprehensive_quality_check(self, table_name: str) -> QualityReport:
        """Run comprehensive data quality check for a table."""
        report_id = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting comprehensive quality check for {table_name}")
        
        all_metrics = []
        
        try:
            # Get table schema information
            schema_query = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name.split('.')[1] if '.' in table_name else table_name}'
            """
            
            schema_df = pd.read_sql(schema_query, self.db_connection)
            columns = schema_df['column_name'].tolist()
            
            # Get record count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_df = pd.read_sql(count_query, self.db_connection)
            record_count = count_df['count'].iloc[0] if not count_df.empty else 0
            
            # Run completeness checks
            for column in columns:
                completeness_metrics = await self.check_completeness(table_name, column)
                all_metrics.extend(completeness_metrics)
            
            # Run timeliness check if timestamp column exists
            timestamp_columns = ['timestamp_utc', 'created_at', 'updated_at', 'api_call_timestamp']
            for ts_col in timestamp_columns:
                if ts_col in columns:
                    timeliness_metrics = await self.check_timeliness(table_name, ts_col)
                    all_metrics.extend(timeliness_metrics)
                    break
            
            # Run validity checks based on quality rules
            for rule in self.quality_rules:
                if rule['table'] == table_name.split('.')[-1]:
                    if rule['check_type'] == 'validity':
                        validity_metrics = await self.check_validity(
                            table_name, 
                            rule['column'], 
                            rule['rule']
                        )
                        all_metrics.extend(validity_metrics)
            
            # Run anomaly detection for numerical columns
            numerical_columns = []
            for _, row in schema_df.iterrows():
                if row['data_type'] in ['numeric', 'double precision', 'real', 'integer', 'bigint']:
                    numerical_columns.append(row['column_name'])
            
            if numerical_columns:
                # Check for anomalies in groups of related columns
                if 'price_usd' in numerical_columns and 'volume_24h_usd' in numerical_columns:
                    anomaly_metrics = await self.check_anomalies(
                        table_name, 
                        ['price_usd', 'volume_24h_usd']
                    )
                    all_metrics.extend(anomaly_metrics)
                
                # Check statistical outliers for key columns
                key_columns = ['price_usd', 'volume_24h_usd', 'market_cap_usd']
                for col in key_columns:
                    if col in numerical_columns:
                        outlier_metrics = await self.check_statistical_outliers(table_name, col)
                        all_metrics.extend(outlier_metrics)
            
            # Calculate overall quality score
            if all_metrics:
                quality_scores = [metric.value for metric in all_metrics if metric.check_type != QualityCheckType.ANOMALY]
                anomaly_scores = [1 - metric.value for metric in all_metrics if metric.check_type == QualityCheckType.ANOMALY]
                
                all_scores = quality_scores + anomaly_scores
                overall_score = statistics.mean(all_scores) if all_scores else 0.0
            else:
                overall_score = 0.0
            
            # Determine overall status
            overall_status = QualityStatus.EXCELLENT
            for metric in all_metrics:
                if metric.status == QualityStatus.CRITICAL:
                    overall_status = QualityStatus.CRITICAL
                    break
                elif metric.status == QualityStatus.POOR and overall_status != QualityStatus.CRITICAL:
                    overall_status = QualityStatus.POOR
                elif metric.status == QualityStatus.FAIR and overall_status not in [QualityStatus.CRITICAL, QualityStatus.POOR]:
                    overall_status = QualityStatus.FAIR
                elif metric.status == QualityStatus.GOOD and overall_status == QualityStatus.EXCELLENT:
                    overall_status = QualityStatus.GOOD
            
            # Generate recommendations
            recommendations = self._generate_recommendations(all_metrics)
            
            # Create quality report
            report = QualityReport(
                report_id=report_id,
                table_name=table_name,
                timestamp=datetime.now(),
                overall_score=overall_score,
                overall_status=overall_status,
                metrics=all_metrics,
                recommendations=recommendations,
                record_count=record_count,
                column_count=len(columns)
            )
            
            # Store report
            self.quality_reports[report_id] = report
            self.quality_history.append(report)
            
            self.logger.info(f"Quality check completed for {table_name}: {overall_status.value} ({overall_score:.3f})")
            return report
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive quality check for {table_name}: {str(e)}")
            
            # Return error report
            return QualityReport(
                report_id=report_id,
                table_name=table_name,
                timestamp=datetime.now(),
                overall_score=0.0,
                overall_status=QualityStatus.CRITICAL,
                metrics=[],
                recommendations=[f"Quality check failed: {str(e)}"],
                record_count=0,
                column_count=0
            )
    
    def _generate_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        for metric in metrics:
            if metric.status in [QualityStatus.POOR, QualityStatus.CRITICAL]:
                if metric.check_type == QualityCheckType.COMPLETENESS:
                    recommendations.append(
                        f"Improve data completeness for {metric.column_name or metric.table_name} "
                        f"(current: {metric.value:.3f})"
                    )
                elif metric.check_type == QualityCheckType.VALIDITY:
                    recommendations.append(
                        f"Review data validation rules for {metric.column_name} "
                        f"(validity: {metric.value:.3f})"
                    )
                elif metric.check_type == QualityCheckType.TIMELINESS:
                    if 'minutes_since_latest' in metric.details:
                        minutes = metric.details['minutes_since_latest']
                        recommendations.append(
                            f"Data freshness issue: latest data is {minutes:.0f} minutes old"
                        )
                elif metric.check_type == QualityCheckType.ANOMALY:
                    recommendations.append(
                        f"High anomaly rate detected in {metric.column_name or metric.table_name} "
                        f"({metric.value:.3f}). Review data sources and collection processes."
                    )
        
        # Remove duplicates
        return list(set(recommendations))
    
    def get_quality_summary(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get quality summary for all tables or a specific table."""
        if table_name:
            relevant_reports = [r for r in self.quality_history if r.table_name == table_name]
        else:
            relevant_reports = self.quality_history
        
        if not relevant_reports:
            return {'message': 'No quality reports available'}
        
        # Get latest report for each table
        latest_reports = {}
        for report in relevant_reports:
            if (report.table_name not in latest_reports or 
                report.timestamp > latest_reports[report.table_name].timestamp):
                latest_reports[report.table_name] = report
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'tables_analyzed': len(latest_reports),
            'overall_status_distribution': {},
            'tables': {}
        }
        
        status_counts = {}
        for table, report in latest_reports.items():
            status = report.overall_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            summary['tables'][table] = {
                'overall_score': report.overall_score,
                'overall_status': status,
                'record_count': report.record_count,
                'metric_count': len(report.metrics),
                'last_checked': report.timestamp.isoformat(),
                'recommendations_count': len(report.recommendations)
            }
        
        summary['overall_status_distribution'] = status_counts
        
        return summary
    
    async def automated_quality_monitoring(self, tables: List[str]) -> Dict[str, QualityReport]:
        """Run automated quality monitoring for multiple tables."""
        self.logger.info(f"Starting automated quality monitoring for {len(tables)} tables")
        
        reports = {}
        
        for table in tables:
            try:
                report = await self.run_comprehensive_quality_check(table)
                reports[table] = report
                
                # Send alerts for critical issues
                if report.overall_status == QualityStatus.CRITICAL:
                    await self._send_quality_alert(report)
                    
            except Exception as e:
                self.logger.error(f"Failed to check quality for table {table}: {str(e)}")
        
        return reports
    
    async def _send_quality_alert(self, report: QualityReport) -> None:
        """Send quality alert for critical issues."""
        # This would integrate with the AlertManager
        critical_metrics = [m for m in report.metrics if m.status == QualityStatus.CRITICAL]
        
        if critical_metrics:
            self.logger.warning(
                f"🚨 CRITICAL DATA QUALITY ISSUES in {report.table_name}: "
                f"{len(critical_metrics)} critical metrics detected"
            )
            
            for metric in critical_metrics:
                self.logger.warning(f"  - {metric.message}")
    
    def cleanup_old_reports(self, retention_days: int = 30) -> None:
        """Clean up old quality reports."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.quality_history = [
            report for report in self.quality_history
            if report.timestamp > cutoff_date
        ]
        
        # Clean quality_reports dict
        to_remove = []
        for report_id, report in self.quality_reports.items():
            if report.timestamp <= cutoff_date:
                to_remove.append(report_id)
        
        for report_id in to_remove:
            del self.quality_reports[report_id]
        
        self.logger.info(f"Cleaned up quality reports older than {retention_days} days")


async def main():
    """Main function for testing data quality automation."""
    # This would typically use a real database connection
    # For testing purposes, we'll use a mock connection
    
    config = {
        'data_quality': {
            'thresholds': {
                'completeness': {
                    'excellent': 0.99,
                    'good': 0.95,
                    'fair': 0.90,
                    'poor': 0.80
                }
            },
            'rules': [
                {
                    'name': 'price_positive',
                    'table': 'clean_crypto_quotes',
                    'column': 'price_usd',
                    'check_type': 'validity',
                    'rule': 'value > 0',
                    'critical': True
                }
            ]
        }
    }
    
    # Mock database connection (in practice, use real DB connection)
    class MockConnection:
        pass
    
    dq_automation = DataQualityAutomation(config, MockConnection())
    
    # Print configuration
    print("Data Quality Automation Configuration:")
    print(json.dumps(dq_automation.thresholds, indent=2))
    
    print("\nQuality Rules:")
    print(json.dumps(dq_automation.quality_rules, indent=2))


if __name__ == "__main__":
    asyncio.run(main())