# CryptoSphere Analytics Platform - 07-automation Module

## Overview
The 07-automation module provides comprehensive automation capabilities for the CryptoSphere Analytics Platform. This module includes pipeline orchestration, health monitoring, alerting, deployment management, and data quality automation.

## Module Structure

```
07-automation/
├── 01-orchestration/           # Pipeline orchestration and task management
│   └── pipeline_orchestrator.py
├── 02-monitoring/              # System and service health monitoring  
│   └── health_monitor.py
├── 03-alerting/               # Multi-channel alert management
│   └── alert_manager.py
├── 04-deployment/             # Automated deployment and rollback
│   └── deployment_manager.py
├── 05-data-quality/           # Data quality automation and profiling
│   ├── data_quality_automation.py
│   └── data_profiling_automation.py
└── README.md                  # This file
```

## Components

### 1. Pipeline Orchestration (`01-orchestration/`)
- **Purpose**: Manages complex data pipelines and task dependencies
- **Key Features**:
  - Asynchronous task execution with dependency management
  - Configurable retry logic and error handling
  - Performance monitoring and metrics collection
  - Cron-based and interval-based scheduling
  - Pipeline status tracking and reporting

### 2. Health Monitoring (`02-monitoring/`)
- **Purpose**: Monitors system health and service availability
- **Key Features**:
  - Database connection monitoring with connection pooling
  - API endpoint health checks
  - System resource monitoring (CPU, memory, disk, network)
  - Service availability tracking
  - Real-time health status reporting

### 3. Alert Management (`03-alerting/`)
- **Purpose**: Multi-channel alerting and notification system
- **Key Features**:
  - Email, Slack, Discord, webhook, and SMS notifications
  - Alert routing and prioritization
  - Rate limiting and alert suppression
  - Template-based alert formatting
  - Alert escalation and acknowledgment

### 4. Deployment Management (`04-deployment/`)
- **Purpose**: Automated deployment and rollback capabilities
- **Key Features**:
  - Multiple deployment strategies (rolling, blue-green, canary)
  - Artifact management and versioning
  - Automated health checks and validation
  - Rollback capabilities with backup management
  - Service restart and configuration management

### 5. Data Quality Automation (`05-data-quality/`)
- **Purpose**: Automated data quality monitoring and profiling
- **Key Features**:
  - Comprehensive data quality assessments
  - Anomaly detection and statistical analysis
  - Data profiling and schema evolution tracking
  - Quality score calculation and trending
  - Automated remediation recommendations

## Installation and Setup

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for automation module
pip install asyncio apscheduler psycopg2-binary sqlalchemy pandas numpy scipy scikit-learn
```

### Database Setup
The automation module requires database connections for monitoring and data quality checks:

```python
# Example PostgreSQL connection
import psycopg2
from sqlalchemy import create_engine

# Database connection for TimescaleDB/PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'cryptosphere_analytics',
    'username': 'your_username',
    'password': 'your_password'
}

connection_string = f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
db_engine = create_engine(connection_string)
```

### Configuration
Create a configuration file for the automation system:

```yaml
# automation_config.yaml
automation:
  pipeline_orchestration:
    max_concurrent_tasks: 10
    default_timeout: 3600
    retry_attempts: 3
    
  health_monitoring:
    check_interval: 60  # seconds
    database_timeout: 30
    api_timeout: 10
    
  alerting:
    rate_limit_window: 300  # 5 minutes
    max_alerts_per_window: 10
    channels:
      email:
        smtp_server: "smtp.gmail.com"
        smtp_port: 587
        username: "your_email@gmail.com"
        password: "your_app_password"
      slack:
        webhook_url: "https://hooks.slack.com/services/..."
      discord:
        webhook_url: "https://discord.com/api/webhooks/..."
        
  deployment:
    strategies: ["rolling", "blue_green", "canary"]
    health_check_timeout: 300
    rollback_enabled: true
    
  data_quality:
    thresholds:
      completeness:
        excellent: 0.99
        good: 0.95
        fair: 0.90
        poor: 0.80
      accuracy:
        excellent: 0.98
        good: 0.95
        fair: 0.90
        poor: 0.85
```

## Usage Examples

### 1. Pipeline Orchestration
```python
from pipeline_orchestrator import PipelineOrchestrator
import asyncio

async def main():
    config = {
        'max_concurrent_tasks': 5,
        'default_timeout': 1800
    }
    
    orchestrator = PipelineOrchestrator(config)
    
    # Define tasks
    tasks = [
        {
            'id': 'fetch_crypto_data',
            'name': 'Fetch Cryptocurrency Data',
            'command': 'python fetch_crypto_data.py',
            'timeout': 600,
            'retry_attempts': 3
        },
        {
            'id': 'clean_data',
            'name': 'Clean Raw Data',
            'command': 'python clean_data.py',
            'dependencies': ['fetch_crypto_data'],
            'timeout': 300
        }
    ]
    
    # Execute pipeline
    results = await orchestrator.execute_pipeline('crypto_etl_pipeline', tasks)
    print(f"Pipeline completed with status: {results['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Health Monitoring
```python
from health_monitor import HealthMonitor
import asyncio

async def main():
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'cryptosphere_analytics'
        },
        'apis': [
            {
                'name': 'CoinMarketCap',
                'url': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest',
                'headers': {'X-CMC_PRO_API_KEY': 'your_api_key'}
            }
        ]
    }
    
    monitor = HealthMonitor(config)
    
    # Start monitoring
    await monitor.start_monitoring()
    
    # Get health status
    status = await monitor.get_health_status()
    print(f"System Health: {status['overall_status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Alert Management
```python
from alert_manager import AlertManager, Alert, AlertLevel
import asyncio

async def main():
    config = {
        'channels': {
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'alerts@yourdomain.com',
                'password': 'your_password'
            }
        }
    }
    
    alert_manager = AlertManager(config)
    
    # Send alert
    alert = Alert(
        id='db_connection_failed',
        level=AlertLevel.CRITICAL,
        title='Database Connection Failed',
        message='Unable to connect to PostgreSQL database',
        source='health_monitor',
        metadata={'database': 'cryptosphere_analytics'}
    )
    
    await alert_manager.send_alert(alert, ['email'])

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Data Quality Automation
```python
from data_quality_automation import DataQualityAutomation
import asyncio

async def main():
    config = {
        'data_quality': {
            'thresholds': {
                'completeness': {'excellent': 0.99, 'good': 0.95}
            }
        }
    }
    
    # Assuming you have a database connection
    db_connection = get_database_connection()
    
    dq_automation = DataQualityAutomation(config, db_connection)
    
    # Run quality check
    report = await dq_automation.run_comprehensive_quality_check('clean_crypto_quotes')
    
    print(f"Quality Score: {report.overall_score:.3f}")
    print(f"Status: {report.overall_status.value}")
    print(f"Recommendations: {len(report.recommendations)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Integration with Other Modules

### With SQL Processing (03-sql-processing/)
```python
# Monitor SQL pipeline execution
await orchestrator.execute_pipeline('sql_processing', [
    {'id': 'bronze_layer', 'command': 'psql -f 01-bronze_layer/01-create_bronze_tables.sql'},
    {'id': 'silver_layer', 'command': 'psql -f 02-silver_layer/01-create_silver_tables.sql', 'dependencies': ['bronze_layer']},
    {'id': 'gold_layer', 'command': 'psql -f 03-gold_layer/01-create_gold_data_marts.sql', 'dependencies': ['silver_layer']}
])
```

### With ML Models (04-ml-models/)
```python
# Automated model deployment
deployment_config = {
    'strategy': 'blue_green',
    'model_artifact': 'crypto_price_predictor_v2.pkl',
    'target_service': 'prediction_service',
    'health_check_endpoint': '/health'
}

await deployment_manager.deploy_model(deployment_config)
```

### With Data Visualization (06-data-visualization/)
```python
# Monitor PowerBI refresh status
health_checks = [
    {
        'name': 'PowerBI Dataset Refresh',
        'type': 'api',
        'url': 'https://api.powerbi.com/v1.0/myorg/datasets/refresh-status',
        'expected_status': 200
    }
]

await monitor.add_health_checks(health_checks)
```

## Monitoring and Observability

### Metrics Collection
The automation module collects various metrics:

- **Pipeline Metrics**: Execution time, success rate, error count
- **Health Metrics**: Response time, availability, resource usage
- **Alert Metrics**: Alert volume, resolution time, escalation rate
- **Quality Metrics**: Data quality scores, anomaly detection rate

### Logging
All components use structured logging:

```python
import logging

logger = logging.getLogger('cryptosphere_automation')
logger.setLevel(logging.INFO)

# Example log entry
logger.info("Pipeline executed successfully", extra={
    'pipeline_id': 'crypto_etl_pipeline',
    'execution_time': 120.5,
    'tasks_completed': 5,
    'status': 'success'
})
```

### Dashboard Integration
Metrics can be exported to monitoring dashboards:

- **Grafana**: For real-time monitoring and alerting
- **PowerBI**: For business intelligence and reporting
- **Custom Dashboards**: Using the visualization module

## Best Practices

### 1. Configuration Management
- Use environment variables for sensitive configuration
- Implement configuration validation
- Support multiple environments (dev, staging, prod)

### 2. Error Handling
- Implement comprehensive error handling and recovery
- Use structured logging for troubleshooting
- Set up proper alerting for critical failures

### 3. Performance Optimization
- Use connection pooling for database operations
- Implement caching where appropriate
- Monitor resource usage and optimize accordingly

### 4. Security
- Secure API keys and credentials
- Implement proper authentication and authorization
- Use encrypted connections for external communications

### 5. Testing
- Write unit tests for individual components
- Implement integration tests for end-to-end workflows
- Use mocking for external dependencies in tests

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   - Check connection parameters and credentials
   - Verify database server is running and accessible
   - Check firewall and network connectivity

2. **Pipeline Execution Failures**
   - Review task dependencies and execution order
   - Check resource availability and limits
   - Verify task command syntax and permissions

3. **Alert Delivery Issues**
   - Validate notification channel configurations
   - Check rate limiting and suppression rules
   - Verify external service availability (SMTP, webhooks)

4. **Performance Issues**
   - Monitor resource usage and bottlenecks
   - Optimize database queries and connections
   - Adjust concurrency and timeout settings

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   logging.getLogger('cryptosphere_automation').setLevel(logging.DEBUG)
   ```

2. **Monitor System Resources**
   ```python
   # Check system resources
   health_status = await monitor.get_system_health()
   print(f"CPU Usage: {health_status['cpu_usage']}")
   print(f"Memory Usage: {health_status['memory_usage']}")
   ```

3. **Validate Configuration**
   ```python
   # Test configuration
   await orchestrator.validate_configuration()
   await alert_manager.test_channels()
   ```

## Contributing

When contributing to the automation module:

1. Follow the established code structure and patterns
2. Add comprehensive logging and error handling
3. Include unit tests for new functionality
4. Update documentation and examples
5. Consider backward compatibility

## License

This module is part of the CryptoSphere Analytics Platform and follows the same licensing terms as the main project.