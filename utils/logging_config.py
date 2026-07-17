#!/usr/bin/env python3
"""
Logging Configuration for KosXER

Provides centralized logging setup with configurable levels
and output destinations.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(level=logging.INFO, log_file=None, console=True):
    """
    Setup logging configuration for KosXER.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        console: Whether to output to console
    
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger('kosxer')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """
    Get logger instance.
    
    Args:
        name: Optional logger name (defaults to 'kosxer')
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'kosxer.{name}')
    return logging.getLogger('kosxer')


# Convenience functions for common logging patterns
def log_operation(logger, operation, details=None):
    """Log an operation with optional details."""
    msg = f"OPERATION: {operation}"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_error(logger, operation, error, details=None):
    """Log an error with context."""
    msg = f"ERROR in {operation}: {str(error)}"
    if details:
        msg += f" | {details}"
    logger.error(msg, exc_info=True)


def log_state_change(logger, component, old_state, new_state):
    """Log a state change."""
    logger.debug(f"STATE CHANGE [{component}]: {old_state} -> {new_state}")


def log_file_operation(logger, operation, filepath, success=True):
    """Log file operations."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"FILE {operation}: {filepath} [{status}]")


# Create default logger
default_logger = setup_logging()
