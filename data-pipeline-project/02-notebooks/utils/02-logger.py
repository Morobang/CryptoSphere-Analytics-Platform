"""
Logging Utilities Module

Provides centralized logging configuration and utilities for the data pipeline.
Supports file logging, console output, structured logging, and log rotation.

Key Features:
- Configurable log levels and formats
- File rotation and compression
- Structured JSON logging
- Performance logging
- Error tracking and alerting
- Context-aware logging

Usage:
    from utils.logger import setup_logger, get_logger
    
    # Setup logging
    setup_logger('INFO', 'logs/pipeline.log')
    
    # Get logger instance
    logger = get_logger(__name__)
    logger.info("Pipeline started")
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    
    def __init__(self, context_data: Dict[str, Any] = None):
        super().__init__()
        self.context_data = context_data or {}
    
    def filter(self, record):
        # Add context data to record
        for key, value in self.context_data.items():
            setattr(record, key, value)
        return True


class PerformanceLogger:
    """Logger for performance monitoring and timing"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation_name: str):
        """Start timing an operation"""
        self.start_times[operation_name] = datetime.now()
        self.logger.info(f"Started operation: {operation_name}")
    
    def end_timer(self, operation_name: str, extra_data: Dict = None):
        """End timing and log duration"""
        if operation_name not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation_name}")
            return
        
        start_time = self.start_times.pop(operation_name)
        duration = (datetime.now() - start_time).total_seconds()
        
        log_data = {
            'operation': operation_name,
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        # Add performance data to log record
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            __file__,
            0,
            f"Operation completed: {operation_name} ({duration:.3f}s)",
            (),
            None
        )
        record.extra_fields = log_data
        self.logger.handle(record)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up any remaining timers
        for operation in list(self.start_times.keys()):
            self.end_timer(operation, {'status': 'interrupted'})


def setup_logger(log_level: str = 'INFO',
                log_file: Optional[str] = None,
                log_format: str = 'standard',
                max_file_size_mb: int = 100,
                backup_count: int = 5,
                console_output: bool = True) -> logging.Logger:
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Format type ('standard', 'json', 'detailed')
        max_file_size_mb: Maximum file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
        
    Returns:
        Configured root logger
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    log_level_obj = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level_obj)
    
    # Define formatters
    formatters = {
        'standard': logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ),
        'detailed': logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        ),
        'json': JSONFormatter()
    }
    
    formatter = formatters.get(log_format, formatters['standard'])
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_obj)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level_obj)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add error file handler for errors and above
    if log_file:
        error_log_file = log_path.parent / f"error_{log_path.name}"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file}")
    return root_logger


def get_logger(name: str, context_data: Dict[str, Any] = None) -> logging.Logger:
    """
    Get logger instance with optional context
    
    Args:
        name: Logger name (typically __name__)
        context_data: Additional context to include in logs
        
    Returns:
        Logger instance with context filter
    """
    logger = logging.getLogger(name)
    
    # Add context filter if provided
    if context_data:
        context_filter = ContextFilter(context_data)
        logger.addFilter(context_filter)
    
    return logger


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get performance logger for timing operations
    
    Args:
        name: Logger name
        
    Returns:
        PerformanceLogger instance
    """
    base_logger = get_logger(name)
    return PerformanceLogger(base_logger)


class LoggerContextManager:
    """Context manager for temporary logging configuration"""
    
    def __init__(self, logger: logging.Logger, 
                 temp_level: str = None,
                 context_data: Dict[str, Any] = None):
        self.logger = logger
        self.original_level = logger.level
        self.temp_level = getattr(logging, temp_level.upper()) if temp_level else None
        self.context_filter = ContextFilter(context_data) if context_data else None
    
    def __enter__(self):
        if self.temp_level:
            self.logger.setLevel(self.temp_level)
        if self.context_filter:
            self.logger.addFilter(self.context_filter)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_level:
            self.logger.setLevel(self.original_level)
        if self.context_filter:
            self.logger.removeFilter(self.context_filter)


def log_function_calls(logger: logging.Logger = None):
    """
    Decorator to log function entry and exit
    
    Args:
        logger: Logger instance (optional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            func_logger.debug(f"Entering function: {func_name}")
            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"Exiting function: {func_name}")
                return result
            except Exception as e:
                func_logger.error(f"Exception in function {func_name}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_errors(logger: logging.Logger = None, 
               reraise: bool = True,
               default_return: Any = None):
    """
    Decorator to log and optionally handle errors
    
    Args:
        logger: Logger instance (optional)
        reraise: Whether to reraise the exception
        default_return: Default value to return on error
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_logger.error(f"Error in function {func_name}: {e}", exc_info=True)
                
                if reraise:
                    raise
                else:
                    return default_return
        
        return wrapper
    return decorator


# Logging configuration for common scenarios
def setup_pipeline_logging(pipeline_name: str = "data_pipeline",
                          log_dir: str = "logs",
                          log_level: str = "INFO"):
    """Setup logging configuration optimized for data pipelines"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / f"{pipeline_name}.log"
    
    return setup_logger(
        log_level=log_level,
        log_file=str(log_file),
        log_format='detailed',
        max_file_size_mb=100,
        backup_count=10,
        console_output=True
    )


def setup_development_logging():
    """Setup logging configuration for development environment"""
    return setup_logger(
        log_level='DEBUG',
        log_file='logs/development.log',
        log_format='detailed',
        console_output=True
    )


def setup_production_logging():
    """Setup logging configuration for production environment"""
    return setup_logger(
        log_level='INFO',
        log_file='logs/production.log',
        log_format='json',
        max_file_size_mb=500,
        backup_count=20,
        console_output=False
    )


# Utility functions
def log_dataframe_info(logger: logging.Logger, df, df_name: str = "DataFrame"):
    """Log DataFrame information for debugging"""
    logger.info(f"{df_name} shape: {df.shape}")
    logger.info(f"{df_name} columns: {list(df.columns)}")
    logger.info(f"{df_name} memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    if df.empty:
        logger.warning(f"{df_name} is empty")
    else:
        logger.info(f"{df_name} dtypes: {df.dtypes.value_counts().to_dict()}")


def log_execution_time(logger: logging.Logger):
    """Decorator to log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Function {func.__name__} executed in {duration:.3f} seconds")
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    print("Logger Utilities Module")
    print("Provides centralized logging configuration and utilities")
    
    # Setup sample logging
    # setup_development_logging()
    # logger = get_logger(__name__)
    # logger.info("Logger module initialized")