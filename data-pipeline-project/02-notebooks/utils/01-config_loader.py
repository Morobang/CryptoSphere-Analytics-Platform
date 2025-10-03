"""
Configuration Loader Module

Handles loading and managing configuration from various sources including:
- YAML files
- JSON files  
- Environment variables
- Command line arguments

Key Features:
- Hierarchical configuration merging
- Environment-specific configs (dev, staging, prod)
- Environment variable substitution
- Configuration validation
- Default value handling

Usage:
    from utils.config_loader import ConfigLoader
    
    config = ConfigLoader('config/pipeline_config.yaml')
    db_config = config.get('database')
    api_key = config.get('api.key', default='default-key')
"""

import yaml
import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Configuration loader with support for multiple formats and environments
    """
    
    def __init__(self, config_file: Union[str, Path] = None, environment: str = None):
        """
        Initialize configuration loader
        
        Args:
            config_file: Path to primary configuration file
            environment: Environment name (dev, staging, prod)
        """
        self.config_file = Path(config_file) if config_file else None
        self.environment = environment or os.getenv('ENVIRONMENT', 'dev')
        self.config_data = {}
        
        if self.config_file and self.config_file.exists():
            self.load_config()
        
        # Load environment-specific overrides
        self._load_environment_config()
        
        # Substitute environment variables
        self._substitute_env_variables()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.suffix in ['.yaml', '.yml']:
                with open(self.config_file, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
            elif self.config_file.suffix == '.json':
                with open(self.config_file, 'r') as f:
                    self.config_data = json.load(f)
            else:
                logger.error(f"Unsupported config file format: {self.config_file.suffix}")
                
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            self.config_data = {}
    
    def _load_environment_config(self):
        """Load environment-specific configuration overrides"""
        if not self.config_file:
            return
            
        env_config_file = self.config_file.parent / f"{self.config_file.stem}_{self.environment}{self.config_file.suffix}"
        
        if env_config_file.exists():
            try:
                if env_config_file.suffix in ['.yaml', '.yml']:
                    with open(env_config_file, 'r') as f:
                        env_config = yaml.safe_load(f) or {}
                elif env_config_file.suffix == '.json':
                    with open(env_config_file, 'r') as f:
                        env_config = json.load(f)
                else:
                    return
                
                # Merge environment config with base config
                self.config_data = self._deep_merge(self.config_data, env_config)
                logger.info(f"Loaded environment config for {self.environment}")
                
            except Exception as e:
                logger.error(f"Failed to load environment config: {e}")
    
    def _substitute_env_variables(self):
        """Substitute environment variables in configuration values"""
        self.config_data = self._recursive_env_substitute(self.config_data)
    
    def _recursive_env_substitute(self, obj):
        """Recursively substitute environment variables in nested objects"""
        if isinstance(obj, dict):
            return {key: self._recursive_env_substitute(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._recursive_env_substitute(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_string(obj)
        else:
            return obj
    
    def _substitute_env_string(self, text: str) -> str:
        """
        Substitute environment variables in string
        Supports formats: ${VAR_NAME} and ${VAR_NAME:default_value}
        """
        pattern = r'\\$\\{([^}]+)\\}'
        
        def replace_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                return os.getenv(var_expr.strip(), match.group(0))
        
        return re.sub(pattern, replace_var, text)
    
    def _deep_merge(self, base_dict: Dict, override_dict: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base_dict.copy()
        
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            config.get('database.host')
            config.get('api.timeout', 30)
        """
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        current = self.config_data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Dictionary containing section configuration
        """
        return self.get(section, {})
    
    def has(self, key_path: str) -> bool:
        """Check if configuration key exists"""
        return self.get(key_path) is not None
    
    def validate_required_keys(self, required_keys: list) -> bool:
        """
        Validate that all required configuration keys exist
        
        Args:
            required_keys: List of required key paths
            
        Returns:
            True if all keys exist, False otherwise
        """
        missing_keys = []
        
        for key in required_keys:
            if not self.has(key):
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"Missing required configuration keys: {missing_keys}")
            return False
        
        logger.info("All required configuration keys present")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Return complete configuration as dictionary"""
        return self.config_data.copy()
    
    def save_config(self, output_file: Union[str, Path]):
        """
        Save current configuration to file
        
        Args:
            output_file: Path to output file
        """
        output_path = Path(output_file)
        
        try:
            if output_path.suffix in ['.yaml', '.yml']:
                with open(output_path, 'w') as f:
                    yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            elif output_path.suffix == '.json':
                with open(output_path, 'w') as f:
                    json.dump(self.config_data, f, indent=2)
            else:
                logger.error(f"Unsupported output format: {output_path.suffix}")
                return
            
            logger.info(f"Configuration saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")


# Configuration templates
def create_pipeline_config_template() -> Dict[str, Any]:
    """Create template for pipeline configuration"""
    return {
        "database": {
            "host": "${DB_HOST:localhost}",
            "port": "${DB_PORT:5432}",
            "name": "${DB_NAME:pipeline_db}",
            "user": "${DB_USER:pipeline_user}",
            "password": "${DB_PASSWORD:secret}",
            "connection_timeout": 30
        },
        "api": {
            "base_url": "${API_BASE_URL:https://api.example.com}",
            "api_key": "${API_KEY}",
            "timeout": 30,
            "retry_attempts": 3,
            "rate_limit": {
                "requests_per_minute": 100
            }
        },
        "data_pipeline": {
            "batch_size": 1000,
            "parallel_workers": 4,
            "retry_failed_records": True,
            "data_retention_days": 90
        },
        "logging": {
            "level": "${LOG_LEVEL:INFO}",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": "${LOG_FILE_PATH:logs/pipeline.log}",
            "max_file_size_mb": 100,
            "backup_count": 5
        },
        "monitoring": {
            "enabled": True,
            "metrics_endpoint": "${METRICS_ENDPOINT:http://localhost:8080/metrics}",
            "alert_email": "${ALERT_EMAIL:admin@company.com}"
        }
    }


def create_ml_config_template() -> Dict[str, Any]:
    """Create template for ML model configuration"""
    return {
        "model": {
            "algorithm": "random_forest",
            "hyperparameters": {
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42
            },
            "cross_validation_folds": 5,
            "test_size": 0.2
        },
        "features": {
            "target_column": "target",
            "feature_columns": [],
            "categorical_features": [],
            "numeric_features": [],
            "drop_columns": []
        },
        "preprocessing": {
            "handle_missing_values": True,
            "scale_features": True,
            "encode_categorical": True,
            "feature_selection": False
        },
        "evaluation": {
            "metrics": ["accuracy", "precision", "recall", "f1"],
            "threshold": 0.5
        },
        "deployment": {
            "model_registry": "${MODEL_REGISTRY:mlflow}",
            "model_name": "${MODEL_NAME:customer_churn}",
            "staging_endpoint": "${STAGING_ENDPOINT}",
            "production_endpoint": "${PROD_ENDPOINT}"
        }
    }


# Utility functions
def load_config_from_env() -> ConfigLoader:
    """Load configuration from environment variables"""
    config_file = os.getenv('CONFIG_FILE', 'config/pipeline_config.yaml')
    environment = os.getenv('ENVIRONMENT', 'dev')
    
    return ConfigLoader(config_file, environment)


if __name__ == "__main__":
    # Example usage
    print("Configuration Loader Module")
    print("Supports YAML, JSON with environment variable substitution")
    
    # Create sample config
    # config = ConfigLoader()
    # config.config_data = create_pipeline_config_template()
    # print("Sample config created")