"""
CryptoSphere Analytics Platform - Alert Manager
===============================================

Comprehensive alerting system for monitoring cryptocurrency analytics platform.
Supports multiple notification channels including email, Slack, Discord, and webhooks.

Features:
- Multi-channel alert delivery
- Alert severity levels and routing
- Rate limiting and alert suppression
- Alert templates and customization
- Integration with monitoring systems
- Alert escalation workflows

Author: CryptoSphere Analytics Team
Created: 2025-10-07
"""

import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import requests
import aiohttp


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class Alert:
    """Alert message definition."""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledgment: Optional[str] = None
    escalated: bool = False


@dataclass
class AlertRule:
    """Alert routing and processing rule."""
    name: str
    condition: str  # Simple condition string
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    rate_limit_minutes: int = 15
    escalation_minutes: int = 60
    template: Optional[str] = None


class AlertManager:
    """
    Comprehensive alert management system for the CryptoSphere Analytics Platform.
    
    Handles alert generation, routing, delivery, and lifecycle management
    with support for multiple notification channels and escalation workflows.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the alert manager."""
        self.config = config
        self.logger = self._setup_logging()
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Rate limiting
        self.rate_limit_cache: Dict[str, datetime] = {}
        self.suppressed_alerts: Set[str] = set()
        
        # Alert rules
        self.alert_rules: List[AlertRule] = []
        self._load_default_rules()
        
        # Channel configurations
        self.email_config = config.get('alerts', {}).get('email', {})
        self.slack_config = config.get('alerts', {}).get('slack', {})
        self.discord_config = config.get('alerts', {}).get('discord', {})
        self.webhook_config = config.get('alerts', {}).get('webhook', {})
        
        # Templates
        self.templates = {
            'default': {
                'title': '[{severity}] {title}',
                'body': '{message}\n\nSource: {source}\nTime: {timestamp}\n\nDetails: {details}'
            },
            'system_health': {
                'title': '🔍 System Health Alert: {title}',
                'body': '**Alert:** {message}\n**Source:** {source}\n**Time:** {timestamp}\n**Severity:** {severity}'
            },
            'pipeline_failure': {
                'title': '🚨 Pipeline Failure: {title}',
                'body': '**Pipeline:** {source}\n**Error:** {message}\n**Time:** {timestamp}\n**Details:** {details}'
            },
            'api_issues': {
                'title': '🔌 API Issue: {title}',
                'body': '**API:** {source}\n**Issue:** {message}\n**Time:** {timestamp}\n**Response Time:** {response_time}s'
            }
        }
        
        self.logger.info("Alert Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('alert_manager')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _load_default_rules(self) -> None:
        """Load default alert routing rules."""
        self.alert_rules = [
            AlertRule(
                name="critical_system_alerts",
                condition="severity == 'critical'",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                rate_limit_minutes=5,
                escalation_minutes=30
            ),
            AlertRule(
                name="pipeline_failures",
                condition="source.startswith('pipeline') and severity in ['error', 'critical']",
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                rate_limit_minutes=10,
                template="pipeline_failure"
            ),
            AlertRule(
                name="api_health_issues",
                condition="source == 'api' and severity in ['warning', 'error', 'critical']",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK],
                rate_limit_minutes=15,
                template="api_issues"
            ),
            AlertRule(
                name="system_resource_warnings",
                condition="source == 'system_resources' and severity in ['warning', 'critical']",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.EMAIL],
                rate_limit_minutes=30,
                template="system_health"
            ),
            AlertRule(
                name="info_notifications",
                condition="severity == 'info'",
                severity=AlertSeverity.INFO,
                channels=[AlertChannel.SLACK],
                rate_limit_minutes=60
            )
        ]
    
    def _generate_alert_id(self, title: str, source: str, message: str) -> str:
        """Generate unique alert ID based on content."""
        content = f"{title}|{source}|{message}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed due to rate limiting."""
        # Find matching rules
        matching_rules = self._find_matching_rules(alert)
        
        for rule in matching_rules:
            if not rule.enabled:
                continue
                
            # Check rate limiting
            rate_limit_key = f"{rule.name}|{alert.source}|{alert.title}"
            
            if rate_limit_key in self.rate_limit_cache:
                last_sent = self.rate_limit_cache[rate_limit_key]
                time_diff = (datetime.now() - last_sent).total_seconds() / 60
                
                if time_diff < rule.rate_limit_minutes:
                    self.logger.debug(f"Alert suppressed due to rate limit: {alert.title}")
                    return True
        
        return False
    
    def _find_matching_rules(self, alert: Alert) -> List[AlertRule]:
        """Find alert rules that match the given alert."""
        matching_rules = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            # Simple condition evaluation (in production, use a proper expression evaluator)
            try:
                context = {
                    'severity': alert.severity.value,
                    'source': alert.source,
                    'title': alert.title,
                    'message': alert.message,
                    'tags': alert.tags
                }
                
                # Basic condition evaluation
                if self._evaluate_condition(rule.condition, context):
                    matching_rules.append(rule)
                    
            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
        
        return matching_rules
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a simple alert condition."""
        # This is a simplified implementation
        # In production, use a proper expression evaluator like py-expression-eval
        
        try:
            # Replace variables with actual values
            for key, value in context.items():
                if isinstance(value, str):
                    condition = condition.replace(key, f"'{value}'")
                elif isinstance(value, list):
                    condition = condition.replace(key, str(value))
                else:
                    condition = condition.replace(key, str(value))
            
            # Simple evaluation (dangerous in production - use proper parser)
            return eval(condition)
            
        except Exception:
            return False
    
    async def send_alert(self, 
                        title: str, 
                        message: str, 
                        severity: str = "info",
                        source: str = "system",
                        details: Optional[Dict[str, Any]] = None,
                        tags: Optional[List[str]] = None) -> str:
        """Send an alert through appropriate channels."""
        
        # Create alert object
        alert = Alert(
            id=self._generate_alert_id(title, source, message),
            title=title,
            message=message,
            severity=AlertSeverity(severity.lower()),
            source=source,
            timestamp=datetime.now(),
            details=details or {},
            tags=tags or []
        )
        
        # Check if alert should be suppressed
        if self._should_suppress_alert(alert):
            return alert.id
        
        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Find matching rules and send notifications
        matching_rules = self._find_matching_rules(alert)
        
        if not matching_rules:
            self.logger.warning(f"No matching rules for alert: {alert.title}")
            return alert.id
        
        # Send through all matching channels
        for rule in matching_rules:
            try:
                await self._send_to_channels(alert, rule)
                
                # Update rate limit cache
                rate_limit_key = f"{rule.name}|{alert.source}|{alert.title}"
                self.rate_limit_cache[rate_limit_key] = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Failed to send alert via rule {rule.name}: {str(e)}")
        
        self.logger.info(f"Alert sent: {alert.title} (ID: {alert.id})")
        return alert.id
    
    async def _send_to_channels(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert to all channels specified in the rule."""
        for channel in rule.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email(alert, rule)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack(alert, rule)
                elif channel == AlertChannel.DISCORD:
                    await self._send_discord(alert, rule)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook(alert, rule)
                else:
                    self.logger.warning(f"Unsupported channel: {channel}")
                    
            except Exception as e:
                self.logger.error(f"Failed to send alert to {channel.value}: {str(e)}")
    
    def _format_alert(self, alert: Alert, rule: AlertRule) -> Dict[str, str]:
        """Format alert using appropriate template."""
        template_name = rule.template or 'default'
        template = self.templates.get(template_name, self.templates['default'])
        
        context = {
            'title': alert.title,
            'message': alert.message,
            'severity': alert.severity.value.upper(),
            'source': alert.source,
            'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'details': json.dumps(alert.details, indent=2) if alert.details else 'None',
            'tags': ', '.join(alert.tags) if alert.tags else 'None'
        }
        
        # Add details as individual variables
        if alert.details:
            context.update(alert.details)
        
        return {
            'title': template['title'].format(**context),
            'body': template['body'].format(**context)
        }
    
    async def _send_email(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert via email."""
        if not self.email_config.get('enabled', False):
            return
        
        formatted = self._format_alert(alert, rule)
        
        msg = MIMEMultipart()
        msg['From'] = self.email_config.get('from_address')
        msg['To'] = ', '.join(self.email_config.get('to_addresses', []))
        msg['Subject'] = formatted['title']
        
        msg.attach(MIMEText(formatted['body'], 'plain'))
        
        # Send email
        with smtplib.SMTP(
            self.email_config.get('smtp_host'), 
            self.email_config.get('smtp_port', 587)
        ) as server:
            if self.email_config.get('use_tls', True):
                server.starttls()
            
            if self.email_config.get('username'):
                server.login(
                    self.email_config.get('username'),
                    self.email_config.get('password')
                )
            
            server.send_message(msg)
        
        self.logger.info(f"Email alert sent: {alert.title}")
    
    async def _send_slack(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert to Slack."""
        if not self.slack_config.get('enabled', False):
            return
        
        formatted = self._format_alert(alert, rule)
        
        # Choose emoji based on severity
        emoji_map = {
            AlertSeverity.INFO: '🔵',
            AlertSeverity.WARNING: '🟡',
            AlertSeverity.ERROR: '🔴',
            AlertSeverity.CRITICAL: '🚨'
        }
        
        # Choose color based on severity
        color_map = {
            AlertSeverity.INFO: '#36a64f',
            AlertSeverity.WARNING: '#ff9500',
            AlertSeverity.ERROR: '#ff0000',
            AlertSeverity.CRITICAL: '#990000'
        }
        
        payload = {
            "text": f"{emoji_map.get(alert.severity, '🔵')} {formatted['title']}",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, '#36a64f'),
                    "fields": [
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False
                        },
                        {
                            "title": "Source",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ],
                    "footer": "CryptoSphere Analytics",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        # Add details if available
        if alert.details:
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": f"```{json.dumps(alert.details, indent=2)}```",
                "short": False
            })
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.slack_config.get('webhook_url'),
                json=payload
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Slack alert sent: {alert.title}")
                else:
                    self.logger.error(f"Failed to send Slack alert: {response.status}")
    
    async def _send_discord(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert to Discord."""
        if not self.discord_config.get('enabled', False):
            return
        
        formatted = self._format_alert(alert, rule)
        
        # Choose color based on severity
        color_map = {
            AlertSeverity.INFO: 0x3498db,
            AlertSeverity.WARNING: 0xf39c12,
            AlertSeverity.ERROR: 0xe74c3c,
            AlertSeverity.CRITICAL: 0x992d22
        }
        
        embed = {
            "title": formatted['title'],
            "description": alert.message,
            "color": color_map.get(alert.severity, 0x3498db),
            "fields": [
                {
                    "name": "Source",
                    "value": alert.source,
                    "inline": True
                },
                {
                    "name": "Severity",
                    "value": alert.severity.value.upper(),
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "inline": True
                }
            ],
            "footer": {
                "text": "CryptoSphere Analytics"
            },
            "timestamp": alert.timestamp.isoformat()
        }
        
        # Add details if available
        if alert.details:
            embed["fields"].append({
                "name": "Details",
                "value": f"```json\n{json.dumps(alert.details, indent=2)}\n```",
                "inline": False
            })
        
        payload = {"embeds": [embed]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.discord_config.get('webhook_url'),
                json=payload
            ) as response:
                if response.status == 204:
                    self.logger.info(f"Discord alert sent: {alert.title}")
                else:
                    self.logger.error(f"Failed to send Discord alert: {response.status}")
    
    async def _send_webhook(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert to custom webhook."""
        if not self.webhook_config.get('enabled', False):
            return
        
        payload = {
            "alert_id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity.value,
            "source": alert.source,
            "timestamp": alert.timestamp.isoformat(),
            "details": alert.details,
            "tags": alert.tags
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.webhook_config.get('auth_token'):
            headers['Authorization'] = f"Bearer {self.webhook_config.get('auth_token')}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_config.get('url'),
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Webhook alert sent: {alert.title}")
                else:
                    self.logger.error(f"Failed to send webhook alert: {response.status}")
    
    async def send_notification(self, title: str, message: str, severity: str = "info") -> str:
        """Send a simple notification (alias for send_alert)."""
        return await self.send_alert(title, message, severity, "notification")
    
    def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            alert.acknowledgment = resolution_note
            
            # Move to resolved alerts
            self.resolved_alerts.append(alert)
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert.title} (ID: {alert_id})")
            return True
        
        return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [
            {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'details': alert.details,
                'tags': alert.tags
            }
            for alert in self.active_alerts.values()
        ]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics and metrics."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp > hour_ago]
        daily_alerts = [a for a in self.alert_history if a.timestamp > day_ago]
        
        severity_counts = {}
        for alert in daily_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
        
        source_counts = {}
        for alert in daily_alerts:
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1
        
        return {
            'active_alerts': len(self.active_alerts),
            'resolved_alerts_today': len([a for a in self.resolved_alerts if a.resolved_at and a.resolved_at > day_ago]),
            'alerts_last_hour': len(recent_alerts),
            'alerts_last_24h': len(daily_alerts),
            'severity_distribution_24h': severity_counts,
            'source_distribution_24h': source_counts,
            'suppressed_alerts': len(self.suppressed_alerts),
            'rate_limited_rules': len(self.rate_limit_cache)
        }
    
    def cleanup_old_alerts(self, retention_days: int = 30) -> None:
        """Clean up old resolved alerts and history."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Clean resolved alerts
        self.resolved_alerts = [
            alert for alert in self.resolved_alerts
            if alert.resolved_at and alert.resolved_at > cutoff_date
        ]
        
        # Clean alert history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_date
        ]
        
        # Clean rate limit cache
        self.rate_limit_cache = {
            key: timestamp for key, timestamp in self.rate_limit_cache.items()
            if timestamp > cutoff_date
        }
        
        self.logger.info(f"Cleaned up alerts older than {retention_days} days")


async def main():
    """Main function for testing alert manager."""
    config = {
        'alerts': {
            'email': {
                'enabled': False,
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'from_address': 'alerts@cryptosphere.com',
                'to_addresses': ['admin@cryptosphere.com'],
                'username': 'your-email@gmail.com',
                'password': 'your-app-password'
            },
            'slack': {
                'enabled': False,
                'webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            },
            'discord': {
                'enabled': False,
                'webhook_url': 'https://discord.com/api/webhooks/YOUR/WEBHOOK'
            },
            'webhook': {
                'enabled': False,
                'url': 'https://your-webhook-endpoint.com/alerts',
                'auth_token': 'your-auth-token'
            }
        }
    }
    
    alert_manager = AlertManager(config)
    
    # Test different types of alerts
    await alert_manager.send_alert(
        "Database Connection Failed",
        "Unable to connect to PostgreSQL database",
        "critical",
        "database",
        {"error_code": "CONNECTION_REFUSED", "retry_count": 3}
    )
    
    await alert_manager.send_alert(
        "High CPU Usage",
        "CPU usage has exceeded 85% for 5 minutes",
        "warning",
        "system_resources",
        {"cpu_usage": 87.5, "duration_minutes": 5}
    )
    
    await alert_manager.send_notification(
        "Pipeline Completed Successfully",
        "Data processing pipeline completed in 2.5 minutes"
    )
    
    # Print statistics
    stats = alert_manager.get_alert_statistics()
    print(json.dumps(stats, indent=2))
    
    # Print active alerts
    active = alert_manager.get_active_alerts()
    print(json.dumps(active, indent=2))


if __name__ == "__main__":
    asyncio.run(main())