"""
CryptoSphere Analytics Platform - Health Monitor
================================================

Comprehensive system health monitoring for the cryptocurrency analytics platform.
Monitors database connections, API health, system resources, and pipeline performance.

Features:
- Real-time system health checks
- Database connection monitoring
- API endpoint health verification
- Resource utilization tracking
- Performance metrics collection
- Automated health reports

Author: CryptoSphere Analytics Team
Created: 2025-10-07
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import platform

import psutil
import requests
import psycopg2
from psycopg2.pool import SimpleConnectionPool


@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    timestamp: datetime
    response_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    process_count: int
    uptime: float
    timestamp: datetime


class HealthMonitor:
    """
    Comprehensive health monitoring system for the CryptoSphere Analytics Platform.
    
    Monitors various system components and provides health status reporting
    with automated alerting capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the health monitor."""
        self.config = config
        self.logger = self._setup_logging()
        
        # Health check results storage
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metrics_history: List[SystemMetrics] = []
        
        # Connection pools
        self.db_pool = None
        self._initialize_db_pool()
        
        # Health check configuration
        self.check_interval = config.get('health_monitor', {}).get('check_interval', 60)
        self.retention_hours = config.get('health_monitor', {}).get('retention_hours', 24)
        
        # Thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'response_time_warning': 5.0,
            'response_time_critical': 10.0
        }
        self.thresholds.update(config.get('health_monitor', {}).get('thresholds', {}))
        
        self.logger.info("Health Monitor initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('health_monitor')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _initialize_db_pool(self) -> None:
        """Initialize database connection pool."""
        try:
            db_config = self.config.get('database', {})
            
            self.db_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=db_config.get('host', 'localhost'),
                database=db_config.get('database', 'cryptosphere'),
                user=db_config.get('user', 'postgres'),
                password=db_config.get('password', ''),
                port=db_config.get('port', 5432)
            )
            
            self.logger.info("Database connection pool initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {str(e)}")
    
    async def check_database_health(self) -> HealthCheck:
        """Check database connection and performance."""
        start_time = time.time()
        
        try:
            if not self.db_pool:
                return HealthCheck(
                    name="database",
                    status="critical",
                    message="Database connection pool not initialized",
                    timestamp=datetime.now(),
                    response_time=0.0
                )
            
            # Get connection from pool
            conn = self.db_pool.getconn()
            
            try:
                with conn.cursor() as cursor:
                    # Test basic connectivity
                    cursor.execute("SELECT 1")
                    
                    # Check database size
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size(current_database())) as size
                    """)
                    db_size = cursor.fetchone()[0]
                    
                    # Check active connections
                    cursor.execute("""
                        SELECT count(*) FROM pg_stat_activity 
                        WHERE state = 'active'
                    """)
                    active_connections = cursor.fetchone()[0]
                    
                    # Check TimescaleDB extension
                    cursor.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
                        )
                    """)
                    timescaledb_available = cursor.fetchone()[0]
                    
                response_time = time.time() - start_time
                
                # Determine status based on response time
                if response_time > self.thresholds['response_time_critical']:
                    status = "critical"
                    message = f"Database response time too high: {response_time:.2f}s"
                elif response_time > self.thresholds['response_time_warning']:
                    status = "warning"
                    message = f"Database response time elevated: {response_time:.2f}s"
                else:
                    status = "healthy"
                    message = "Database connection healthy"
                
                return HealthCheck(
                    name="database",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={
                        'database_size': db_size,
                        'active_connections': active_connections,
                        'timescaledb_available': timescaledb_available,
                        'pool_status': {
                            'min_connections': self.db_pool.minconn,
                            'max_connections': self.db_pool.maxconn,
                            'closed_connections': self.db_pool.closed
                        }
                    }
                )
                
            finally:
                self.db_pool.putconn(conn)
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="database",
                status="critical",
                message=f"Database health check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=response_time
            )
    
    async def check_api_health(self) -> HealthCheck:
        """Check external API health (CoinMarketCap)."""
        start_time = time.time()
        
        try:
            api_config = self.config.get('coinmarketcap_api', {})
            
            if not api_config.get('api_key'):
                return HealthCheck(
                    name="api",
                    status="critical",
                    message="API key not configured",
                    timestamp=datetime.now()
                )
            
            headers = {'X-CMC_PRO_API_KEY': api_config.get('api_key')}
            
            # Test API key info endpoint
            response = requests.get(
                f"{api_config.get('base_url', 'https://pro-api.coinmarketcap.com')}/v1/key/info",
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check rate limits
                daily_limit = data.get('data', {}).get('plan', {}).get('daily_request_limit', 0)
                daily_used = data.get('data', {}).get('usage', {}).get('current_day', {}).get('requests_made', 0)
                
                usage_percentage = (daily_used / daily_limit * 100) if daily_limit > 0 else 0
                
                if usage_percentage > 90:
                    status = "critical"
                    message = f"API usage critical: {usage_percentage:.1f}% of daily limit used"
                elif usage_percentage > 75:
                    status = "warning"
                    message = f"API usage high: {usage_percentage:.1f}% of daily limit used"
                else:
                    status = "healthy"
                    message = "API connection healthy"
                
                return HealthCheck(
                    name="api",
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={
                        'daily_limit': daily_limit,
                        'daily_used': daily_used,
                        'usage_percentage': usage_percentage,
                        'plan_type': data.get('data', {}).get('plan', {}).get('name'),
                        'rate_limit_remaining': response.headers.get('X-RateLimit-Remaining')
                    }
                )
                
            else:
                return HealthCheck(
                    name="api",
                    status="critical",
                    message=f"API health check failed: HTTP {response.status_code}",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
                
        except requests.RequestException as e:
            response_time = time.time() - start_time
            return HealthCheck(
                name="api",
                status="critical",
                message=f"API connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=response_time
            )
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource utilization."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network_io = psutil.net_io_counters()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Create metrics object
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io={
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                disk_io={
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                },
                process_count=process_count,
                uptime=uptime,
                timestamp=datetime.now()
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Clean old metrics
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Determine overall status
            critical_issues = []
            warning_issues = []
            
            if cpu_usage > self.thresholds['cpu_critical']:
                critical_issues.append(f"CPU usage critical: {cpu_usage:.1f}%")
            elif cpu_usage > self.thresholds['cpu_warning']:
                warning_issues.append(f"CPU usage high: {cpu_usage:.1f}%")
            
            if memory_usage > self.thresholds['memory_critical']:
                critical_issues.append(f"Memory usage critical: {memory_usage:.1f}%")
            elif memory_usage > self.thresholds['memory_warning']:
                warning_issues.append(f"Memory usage high: {memory_usage:.1f}%")
            
            if disk_usage > self.thresholds['disk_critical']:
                critical_issues.append(f"Disk usage critical: {disk_usage:.1f}%")
            elif disk_usage > self.thresholds['disk_warning']:
                warning_issues.append(f"Disk usage high: {disk_usage:.1f}%")
            
            if critical_issues:
                status = "critical"
                message = "; ".join(critical_issues)
            elif warning_issues:
                status = "warning"
                message = "; ".join(warning_issues)
            else:
                status = "healthy"
                message = "System resources healthy"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_usage': disk_usage,
                    'disk_free_gb': disk.free / (1024**3),
                    'process_count': process_count,
                    'uptime_hours': uptime / 3600,
                    'platform': platform.platform(),
                    'python_version': platform.python_version()
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status="unknown",
                message=f"Failed to collect system metrics: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def check_application_health(self) -> HealthCheck:
        """Check application-specific health metrics."""
        try:
            # Check if critical processes are running
            python_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'cryptosphere' in cmdline.lower():
                            python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check data freshness (if database is available)
            data_freshness = {}
            if self.db_pool:
                try:
                    conn = self.db_pool.getconn()
                    try:
                        with conn.cursor() as cursor:
                            # Check latest data timestamps
                            cursor.execute("""
                                SELECT 
                                    'bronze_quotes' as table_name,
                                    MAX(api_call_timestamp) as latest_timestamp,
                                    COUNT(*) as record_count
                                FROM bronze.raw_crypto_quotes
                                WHERE api_call_timestamp >= NOW() - INTERVAL '1 hour'
                            """)
                            
                            result = cursor.fetchone()
                            if result:
                                data_freshness['bronze_quotes'] = {
                                    'latest_timestamp': result[1].isoformat() if result[1] else None,
                                    'recent_records': result[2]
                                }
                    finally:
                        self.db_pool.putconn(conn)
                except Exception as e:
                    self.logger.warning(f"Could not check data freshness: {str(e)}")
            
            # Determine status
            issues = []
            
            if len(python_processes) == 0:
                issues.append("No CryptoSphere processes detected")
            
            if data_freshness.get('bronze_quotes', {}).get('recent_records', 0) == 0:
                issues.append("No recent data updates")
            
            if issues:
                status = "warning"
                message = "; ".join(issues)
            else:
                status = "healthy"
                message = "Application health good"
            
            return HealthCheck(
                name="application",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    'python_processes': len(python_processes),
                    'data_freshness': data_freshness,
                    'process_details': python_processes[:5]  # Limit to first 5
                }
            )
            
        except Exception as e:
            return HealthCheck(
                name="application",
                status="unknown",
                message=f"Application health check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks concurrently."""
        self.logger.info("Running comprehensive health checks")
        
        # Run all checks concurrently
        tasks = [
            self.check_database_health(),
            self.check_api_health(),
            self.check_system_resources(),
            self.check_application_health()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, HealthCheck):
                self.health_checks[result.name] = result
            elif isinstance(result, Exception):
                self.logger.error(f"Health check failed with exception: {str(result)}")
        
        return self.health_checks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status summary."""
        if not self.health_checks:
            return {
                'overall_status': 'unknown',
                'message': 'No health checks have been run',
                'checks': {},
                'last_check': None
            }
        
        # Determine overall status
        statuses = [check.status for check in self.health_checks.values()]
        
        if 'critical' in statuses:
            overall_status = 'critical'
        elif 'warning' in statuses:
            overall_status = 'warning'
        elif 'unknown' in statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        # Count status types
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'overall_status': overall_status,
            'status_counts': status_counts,
            'checks': {
                name: {
                    'status': check.status,
                    'message': check.message,
                    'response_time': check.response_time,
                    'timestamp': check.timestamp.isoformat(),
                    'details': check.details
                }
                for name, check in self.health_checks.items()
            },
            'last_check': max(
                check.timestamp for check in self.health_checks.values()
            ).isoformat() if self.health_checks else None
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics summary."""
        if not self.metrics_history:
            return {'message': 'No metrics available'}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calculate averages over the last hour
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > hour_ago]
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m.disk_usage for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = latest_metrics.cpu_usage
            avg_memory = latest_metrics.memory_usage
            avg_disk = latest_metrics.disk_usage
        
        return {
            'current': {
                'cpu_usage': latest_metrics.cpu_usage,
                'memory_usage': latest_metrics.memory_usage,
                'disk_usage': latest_metrics.disk_usage,
                'process_count': latest_metrics.process_count,
                'uptime_hours': latest_metrics.uptime / 3600,
                'timestamp': latest_metrics.timestamp.isoformat()
            },
            'averages_1h': {
                'cpu_usage': round(avg_cpu, 2),
                'memory_usage': round(avg_memory, 2),
                'disk_usage': round(avg_disk, 2),
                'sample_count': len(recent_metrics)
            },
            'thresholds': self.thresholds,
            'metrics_retention_hours': self.retention_hours
        }
    
    async def continuous_monitoring(self) -> None:
        """Run continuous health monitoring in the background."""
        self.logger.info(f"Starting continuous monitoring (interval: {self.check_interval}s)")
        
        while True:
            try:
                await self.run_all_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.db_pool:
            self.db_pool.closeall()
            self.logger.info("Database connection pool closed")


async def main():
    """Main function for testing health monitor."""
    config = {
        'database': {
            'host': 'localhost',
            'database': 'cryptosphere',
            'user': 'postgres',
            'password': 'password',
            'port': 5432
        },
        'coinmarketcap_api': {
            'base_url': 'https://pro-api.coinmarketcap.com',
            'api_key': 'your-api-key'
        },
        'health_monitor': {
            'check_interval': 30,
            'retention_hours': 24
        }
    }
    
    monitor = HealthMonitor(config)
    
    # Run health checks
    await monitor.run_all_health_checks()
    
    # Print results
    status = monitor.get_health_status()
    print(json.dumps(status, indent=2))
    
    # Print system metrics
    metrics = monitor.get_system_metrics()
    print(json.dumps(metrics, indent=2))
    
    # Cleanup
    monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())