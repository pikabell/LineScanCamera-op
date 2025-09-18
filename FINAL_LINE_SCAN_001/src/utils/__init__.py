"""
Utilities module for Line Scan Camera

This module contains utility functions and classes for configuration management
and other helper functionality.
"""

from .config_manager import ConfigManager, get_config

__all__ = [
    'ConfigManager',
    'get_config'
]
