"""
CryptoSphere Analytics Platform - Data Profiling Automation
===========================================================

Automated data profiling and statistical analysis for cryptocurrency analytics.
Generates comprehensive data profiles, identifies patterns, and tracks data evolution.

Features:
- Automated data profiling across all tables
- Statistical analysis and distribution profiling
- Data relationship discovery
- Schema evolution tracking
- Data lineage mapping
- Performance profiling

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
import hashlib

from scipy import stats
from sklearn.preprocessing import LabelEncoder
from collections import Counter


class ProfileType(Enum):
    """Types of data profiles."""
    SCHEMA = "schema"
    STATISTICAL = "statistical"
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    TEMPORAL = "temporal"
    RELATIONSHIP = "relationship"


@dataclass
class ColumnProfile:
    """Profile information for a single column."""
    column_name: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    min_value: Any
    max_value: Any
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_deviation: Optional[float] = None
    most_frequent_values: List[Tuple[Any, int]] = field(default_factory=list)
    data_distribution: Dict[str, Any] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)


@dataclass
class TableProfile:
    """Comprehensive profile for a database table."""
    table_name: str
    timestamp: datetime
    row_count: int
    column_count: int
    columns: Dict[str, ColumnProfile]
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    data_quality_score: float = 0.0
    schema_hash: str = ""
    size_bytes: Optional[int] = None
    
    def __post_init__(self):
        """Calculate schema hash after initialization."""
        schema_str = json.dumps({
            col: {
                'name': profile.column_name,
                'type': profile.data_type
            } for col, profile in self.columns.items()
        }, sort_keys=True)
        self.schema_hash = hashlib.md5(schema_str.encode()).hexdigest()


class DataProfilingAutomation:
    """
    Comprehensive data profiling automation system.
    
    Automatically profiles database tables, tracks schema evolution,
    and generates insights about data characteristics and quality.
    """
    
    def __init__(self, config: Dict[str, Any], db_connection):
        """Initialize the data profiling automation system."""
        self.config = config
        self.db_connection = db_connection
        self.logger = self._setup_logging()
        
        # Profiling configuration
        self.profiling_config = config.get('data_profiling', {})
        
        # Profile storage
        self.table_profiles: Dict[str, TableProfile] = {}
        self.profile_history: List[TableProfile] = []
        
        # Schema evolution tracking
        self.schema_evolution: Dict[str, List[Dict[str, Any]]] = {}
        
        self.logger.info("Data Profiling Automation initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('data_profiling_automation')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    async def profile_column(self, table_name: str, column_name: str, data_type: str) -> ColumnProfile:
        """Generate comprehensive profile for a single column."""
        try:
            # Basic statistics query
            basic_query = f"""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT({column_name}) as non_null_count,
                    COUNT(DISTINCT {column_name}) as unique_count
                FROM {table_name}
            """
            
            basic_df = pd.read_sql(basic_query, self.db_connection)
            
            total_count = basic_df['total_count'].iloc[0]
            non_null_count = basic_df['non_null_count'].iloc[0]
            unique_count = basic_df['unique_count'].iloc[0]
            
            null_count = total_count - non_null_count
            null_percentage = null_count / total_count if total_count > 0 else 0
            unique_percentage = unique_count / non_null_count if non_null_count > 0 else 0
            
            # Get min/max values
            minmax_query = f"""
                SELECT 
                    MIN({column_name}) as min_value,
                    MAX({column_name}) as max_value
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
            """
            
            minmax_df = pd.read_sql(minmax_query, self.db_connection)
            min_value = minmax_df['min_value'].iloc[0] if not minmax_df.empty else None
            max_value = minmax_df['max_value'].iloc[0] if not minmax_df.empty else None
            
            # Initialize profile
            profile = ColumnProfile(
                column_name=column_name,
                data_type=data_type,
                null_count=null_count,
                null_percentage=null_percentage,
                unique_count=unique_count,
                unique_percentage=unique_percentage,
                min_value=min_value,
                max_value=max_value
            )
            
            # Additional statistics for numerical columns
            if data_type in ['numeric', 'double precision', 'real', 'integer', 'bigint']:
                await self._profile_numerical_column(table_name, column_name, profile)
            
            # Profile categorical columns
            elif data_type in ['character varying', 'text', 'character']:
                await self._profile_categorical_column(table_name, column_name, profile)
            
            # Profile temporal columns
            elif data_type in ['timestamp without time zone', 'timestamp with time zone', 'date']:
                await self._profile_temporal_column(table_name, column_name, profile)
            
            # Get most frequent values
            await self._get_frequent_values(table_name, column_name, profile)
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error profiling column {table_name}.{column_name}: {str(e)}")
            # Return basic profile on error
            return ColumnProfile(
                column_name=column_name,
                data_type=data_type,
                null_count=0,
                null_percentage=0,
                unique_count=0,
                unique_percentage=0,
                min_value=None,
                max_value=None
            )
    
    async def _profile_numerical_column(self, table_name: str, column_name: str, profile: ColumnProfile):
        """Add numerical statistics to column profile."""
        try:
            stats_query = f"""
                SELECT 
                    AVG({column_name}) as mean_value,
                    STDDEV({column_name}) as std_deviation,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column_name}) as median_value,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column_name}) as q1,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column_name}) as q3
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
            """
            
            stats_df = pd.read_sql(stats_query, self.db_connection)
            
            if not stats_df.empty:
                profile.mean_value = float(stats_df['mean_value'].iloc[0]) if stats_df['mean_value'].iloc[0] is not None else None
                profile.std_deviation = float(stats_df['std_deviation'].iloc[0]) if stats_df['std_deviation'].iloc[0] is not None else None
                profile.median_value = float(stats_df['median_value'].iloc[0]) if stats_df['median_value'].iloc[0] is not None else None
                
                # Add distribution statistics
                profile.data_distribution = {
                    'q1': float(stats_df['q1'].iloc[0]) if stats_df['q1'].iloc[0] is not None else None,
                    'q3': float(stats_df['q3'].iloc[0]) if stats_df['q3'].iloc[0] is not None else None,
                    'iqr': None,
                    'skewness': None,
                    'kurtosis': None
                }
                
                if profile.data_distribution['q1'] is not None and profile.data_distribution['q3'] is not None:
                    profile.data_distribution['iqr'] = profile.data_distribution['q3'] - profile.data_distribution['q1']
                
                # Calculate skewness and kurtosis using sample data
                sample_query = f"""
                    SELECT {column_name}
                    FROM {table_name}
                    WHERE {column_name} IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT 10000
                """
                
                sample_df = pd.read_sql(sample_query, self.db_connection)
                if not sample_df.empty and len(sample_df) > 3:
                    values = sample_df[column_name].values
                    profile.data_distribution['skewness'] = float(stats.skew(values))
                    profile.data_distribution['kurtosis'] = float(stats.kurtosis(values))
            
        except Exception as e:
            self.logger.error(f"Error profiling numerical column {column_name}: {str(e)}")
    
    async def _profile_categorical_column(self, table_name: str, column_name: str, profile: ColumnProfile):
        """Add categorical statistics to column profile."""
        try:
            # Get value length statistics
            length_query = f"""
                SELECT 
                    AVG(LENGTH({column_name})) as avg_length,
                    MIN(LENGTH({column_name})) as min_length,
                    MAX(LENGTH({column_name})) as max_length
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
            """
            
            length_df = pd.read_sql(length_query, self.db_connection)
            
            if not length_df.empty:
                profile.data_distribution = {
                    'avg_length': float(length_df['avg_length'].iloc[0]) if length_df['avg_length'].iloc[0] is not None else None,
                    'min_length': int(length_df['min_length'].iloc[0]) if length_df['min_length'].iloc[0] is not None else None,
                    'max_length': int(length_df['max_length'].iloc[0]) if length_df['max_length'].iloc[0] is not None else None
                }
            
            # Detect patterns (basic pattern detection)
            sample_query = f"""
                SELECT DISTINCT {column_name}
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                LIMIT 1000
            """
            
            sample_df = pd.read_sql(sample_query, self.db_connection)
            if not sample_df.empty:
                values = sample_df[column_name].values
                patterns = self._detect_string_patterns(values)
                profile.patterns = patterns
            
        except Exception as e:
            self.logger.error(f"Error profiling categorical column {column_name}: {str(e)}")
    
    async def _profile_temporal_column(self, table_name: str, column_name: str, profile: ColumnProfile):
        """Add temporal statistics to column profile."""
        try:
            # Get temporal range and frequency
            temporal_query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT DATE({column_name})) as unique_dates,
                    EXTRACT(EPOCH FROM (MAX({column_name}) - MIN({column_name}))) / 86400 as date_range_days
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
            """
            
            temporal_df = pd.read_sql(temporal_query, self.db_connection)
            
            if not temporal_df.empty:
                profile.data_distribution = {
                    'unique_dates': int(temporal_df['unique_dates'].iloc[0]) if temporal_df['unique_dates'].iloc[0] is not None else None,
                    'date_range_days': float(temporal_df['date_range_days'].iloc[0]) if temporal_df['date_range_days'].iloc[0] is not None else None,
                    'records_per_day': None
                }
                
                if (profile.data_distribution['date_range_days'] and 
                    profile.data_distribution['date_range_days'] > 0):
                    profile.data_distribution['records_per_day'] = (
                        temporal_df['total_records'].iloc[0] / profile.data_distribution['date_range_days']
                    )
            
        except Exception as e:
            self.logger.error(f"Error profiling temporal column {column_name}: {str(e)}")
    
    async def _get_frequent_values(self, table_name: str, column_name: str, profile: ColumnProfile):
        """Get most frequent values for the column."""
        try:
            freq_query = f"""
                SELECT {column_name}, COUNT(*) as frequency
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                GROUP BY {column_name}
                ORDER BY frequency DESC
                LIMIT 10
            """
            
            freq_df = pd.read_sql(freq_query, self.db_connection)
            
            if not freq_df.empty:
                profile.most_frequent_values = [
                    (row[column_name], int(row['frequency']))
                    for _, row in freq_df.iterrows()
                ]
            
        except Exception as e:
            self.logger.error(f"Error getting frequent values for {column_name}: {str(e)}")
    
    def _detect_string_patterns(self, values: List[str]) -> List[str]:
        """Detect common string patterns in categorical data."""
        patterns = []
        
        if not values:
            return patterns
        
        # Check for common patterns
        email_count = sum(1 for v in values if '@' in str(v) and '.' in str(v))
        if email_count > len(values) * 0.8:
            patterns.append("email_addresses")
        
        # Check for UUIDs
        uuid_count = sum(1 for v in values if len(str(v)) == 36 and str(v).count('-') == 4)
        if uuid_count > len(values) * 0.8:
            patterns.append("uuid_format")
        
        # Check for numeric strings
        numeric_count = sum(1 for v in values if str(v).isdigit())
        if numeric_count > len(values) * 0.8:
            patterns.append("numeric_strings")
        
        # Check for consistent length
        lengths = [len(str(v)) for v in values]
        if len(set(lengths)) == 1:
            patterns.append(f"fixed_length_{lengths[0]}")
        
        # Check for common prefixes/suffixes
        str_values = [str(v) for v in values]
        if len(str_values) > 1:
            common_prefix = self._find_common_prefix(str_values)
            if len(common_prefix) > 2:
                patterns.append(f"common_prefix_{common_prefix}")
        
        return patterns
    
    def _find_common_prefix(self, strings: List[str]) -> str:
        """Find common prefix among strings."""
        if not strings:
            return ""
        
        prefix = strings[0]
        for string in strings[1:]:
            while not string.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    break
        
        return prefix
    
    async def profile_table(self, table_name: str) -> TableProfile:
        """Generate comprehensive profile for a database table."""
        self.logger.info(f"Starting table profiling for {table_name}")
        
        try:
            # Get table schema
            schema_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table_name.split('.')[1] if '.' in table_name else table_name}'
                ORDER BY ordinal_position
            """
            
            schema_df = pd.read_sql(schema_query, self.db_connection)
            
            if schema_df.empty:
                raise Exception(f"Table {table_name} not found or no columns")
            
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_df = pd.read_sql(count_query, self.db_connection)
            row_count = count_df['row_count'].iloc[0] if not count_df.empty else 0
            
            # Get table size (if available)
            size_query = f"""
                SELECT pg_total_relation_size('{table_name}') as size_bytes
            """
            try:
                size_df = pd.read_sql(size_query, self.db_connection)
                size_bytes = int(size_df['size_bytes'].iloc[0]) if not size_df.empty else None
            except:
                size_bytes = None
            
            # Profile each column
            column_profiles = {}
            for _, row in schema_df.iterrows():
                column_name = row['column_name']
                data_type = row['data_type']
                
                self.logger.debug(f"Profiling column {column_name} ({data_type})")
                profile = await self.profile_column(table_name, column_name, data_type)
                column_profiles[column_name] = profile
            
            # Calculate data quality score
            quality_score = self._calculate_quality_score(column_profiles)
            
            # Create table profile
            table_profile = TableProfile(
                table_name=table_name,
                timestamp=datetime.now(),
                row_count=row_count,
                column_count=len(column_profiles),
                columns=column_profiles,
                data_quality_score=quality_score,
                size_bytes=size_bytes
            )
            
            # Store profile
            self.table_profiles[table_name] = table_profile
            self.profile_history.append(table_profile)
            
            # Track schema evolution
            await self._track_schema_evolution(table_name, table_profile)
            
            self.logger.info(f"Table profiling completed for {table_name}: {quality_score:.3f} quality score")
            return table_profile
            
        except Exception as e:
            self.logger.error(f"Error profiling table {table_name}: {str(e)}")
            raise
    
    def _calculate_quality_score(self, column_profiles: Dict[str, ColumnProfile]) -> float:
        """Calculate overall data quality score for the table."""
        if not column_profiles:
            return 0.0
        
        scores = []
        
        for profile in column_profiles.values():
            column_score = 1.0
            
            # Penalize high null percentage
            column_score -= (profile.null_percentage * 0.3)
            
            # Reward high uniqueness for key columns
            if 'id' in profile.column_name.lower():
                column_score += (profile.unique_percentage * 0.2)
            
            # Penalize very low or very high uniqueness for non-key columns
            else:
                if profile.unique_percentage < 0.01:  # Too repetitive
                    column_score -= 0.1
                elif profile.unique_percentage > 0.95 and profile.data_type not in ['text', 'character varying']:
                    column_score -= 0.1  # Potentially poor data quality
            
            scores.append(max(0.0, min(1.0, column_score)))
        
        return sum(scores) / len(scores)
    
    async def _track_schema_evolution(self, table_name: str, new_profile: TableProfile):
        """Track schema changes over time."""
        if table_name not in self.schema_evolution:
            self.schema_evolution[table_name] = []
        
        # Get previous profile
        previous_profiles = [p for p in self.profile_history 
                           if p.table_name == table_name and p.timestamp < new_profile.timestamp]
        
        if previous_profiles:
            latest_previous = max(previous_profiles, key=lambda p: p.timestamp)
            
            # Check for schema changes
            changes = []
            
            # Check for new columns
            new_columns = set(new_profile.columns.keys()) - set(latest_previous.columns.keys())
            for col in new_columns:
                changes.append({
                    'type': 'column_added',
                    'column': col,
                    'data_type': new_profile.columns[col].data_type
                })
            
            # Check for removed columns
            removed_columns = set(latest_previous.columns.keys()) - set(new_profile.columns.keys())
            for col in removed_columns:
                changes.append({
                    'type': 'column_removed',
                    'column': col,
                    'data_type': latest_previous.columns[col].data_type
                })
            
            # Check for data type changes
            common_columns = set(new_profile.columns.keys()) & set(latest_previous.columns.keys())
            for col in common_columns:
                if (new_profile.columns[col].data_type != 
                    latest_previous.columns[col].data_type):
                    changes.append({
                        'type': 'data_type_changed',
                        'column': col,
                        'old_type': latest_previous.columns[col].data_type,
                        'new_type': new_profile.columns[col].data_type
                    })
            
            # Record schema evolution
            if changes:
                evolution_record = {
                    'timestamp': new_profile.timestamp,
                    'changes': changes,
                    'previous_hash': latest_previous.schema_hash,
                    'new_hash': new_profile.schema_hash
                }
                
                self.schema_evolution[table_name].append(evolution_record)
                self.logger.info(f"Schema evolution detected for {table_name}: {len(changes)} changes")
    
    async def profile_multiple_tables(self, table_names: List[str]) -> Dict[str, TableProfile]:
        """Profile multiple tables in parallel."""
        self.logger.info(f"Starting batch profiling for {len(table_names)} tables")
        
        profiles = {}
        
        # Profile tables sequentially to avoid overwhelming the database
        for table_name in table_names:
            try:
                profile = await self.profile_table(table_name)
                profiles[table_name] = profile
            except Exception as e:
                self.logger.error(f"Failed to profile table {table_name}: {str(e)}")
        
        return profiles
    
    def get_profiling_summary(self) -> Dict[str, Any]:
        """Get summary of all profiling results."""
        if not self.table_profiles:
            return {'message': 'No table profiles available'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'tables_profiled': len(self.table_profiles),
            'total_columns': sum(p.column_count for p in self.table_profiles.values()),
            'total_rows': sum(p.row_count for p in self.table_profiles.values()),
            'average_quality_score': np.mean([p.data_quality_score for p in self.table_profiles.values()]),
            'tables': {}
        }
        
        for table_name, profile in self.table_profiles.items():
            summary['tables'][table_name] = {
                'row_count': profile.row_count,
                'column_count': profile.column_count,
                'quality_score': profile.data_quality_score,
                'last_profiled': profile.timestamp.isoformat(),
                'size_bytes': profile.size_bytes,
                'schema_hash': profile.schema_hash
            }
        
        return summary
    
    def get_schema_evolution_report(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get schema evolution report."""
        if table_name:
            evolution_data = {table_name: self.schema_evolution.get(table_name, [])}
        else:
            evolution_data = self.schema_evolution
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'tables_tracked': len(evolution_data),
            'evolution_history': {}
        }
        
        for table, history in evolution_data.items():
            if history:
                report['evolution_history'][table] = {
                    'total_changes': sum(len(record['changes']) for record in history),
                    'last_change': max(record['timestamp'] for record in history).isoformat(),
                    'change_types': {},
                    'recent_changes': history[-5:]  # Last 5 changes
                }
                
                # Count change types
                change_types = {}
                for record in history:
                    for change in record['changes']:
                        change_type = change['type']
                        change_types[change_type] = change_types.get(change_type, 0) + 1
                
                report['evolution_history'][table]['change_types'] = change_types
        
        return report
    
    def cleanup_old_profiles(self, retention_days: int = 30) -> None:
        """Clean up old profile data."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Clean profile history
        self.profile_history = [
            profile for profile in self.profile_history
            if profile.timestamp > cutoff_date
        ]
        
        # Clean schema evolution history
        for table_name in self.schema_evolution:
            self.schema_evolution[table_name] = [
                record for record in self.schema_evolution[table_name]
                if record['timestamp'] > cutoff_date
            ]
        
        self.logger.info(f"Cleaned up profile data older than {retention_days} days")


async def main():
    """Main function for testing data profiling automation."""
    config = {
        'data_profiling': {
            'batch_size': 1000,
            'parallel_workers': 4
        }
    }
    
    # Mock database connection
    class MockConnection:
        pass
    
    profiler = DataProfilingAutomation(config, MockConnection())
    
    print("Data Profiling Automation initialized")
    print(f"Configuration: {json.dumps(config, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())