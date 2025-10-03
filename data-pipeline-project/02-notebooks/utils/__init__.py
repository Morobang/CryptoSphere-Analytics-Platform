"""
Utilities Package Initialization

Common utilities for configuration loading, logging, and helper functions
used across the data pipeline project.

This package provides:
- Configuration management
- Logging setup and utilities
- Common helper functions
- Environment variable handling

Usage:
    from utils.config_loader import ConfigLoader
    from utils.logger import setup_logger
"""

__version__ = "1.0.0"

try:
    from .config_loader import ConfigLoader
    from .logger import setup_logger, get_logger
    
    __all__ = ['ConfigLoader', 'setup_logger', 'get_logger']
except ImportError:
    __all__ = []