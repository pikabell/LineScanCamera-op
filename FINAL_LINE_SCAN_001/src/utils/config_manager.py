#!/usr/bin/env python3
"""
Configuration Manager Module

This module handles all configuration loading and validation for the Line Scan Camera application.
"""

import os
import configparser
from typing import Dict, Any, Optional


class ConfigManager:
    """
    A class to manage configuration settings for the Line Scan Camera application
    
    Attributes:
        config (configparser.ConfigParser): ConfigParser object
        config_path (str): Path to the configuration file
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigManager with optional config path
        
        Args:
            config_path (str, optional): Path to config file. If None, uses default path.
        """
        self.config = configparser.ConfigParser()
        
        if config_path is None:
            # Default config path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(project_root, "config", "config.ini")
        else:
            self.config_path = config_path
            
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            print(f"Warning: Config file not found at {self.config_path}. Using defaults.")
            self._create_default_config()
        else:
            self.config.read(self.config_path)
            print(f"Configuration loaded from: {self.config_path}")
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config['DEFAULT'] = {
            'width_roi': '20',
            'visualize': 'False',
            'motion_detection': 'True',
            'motion_sensitivity': '1000',
            'motion_region_only': 'True',
            'frame_blending': 'True',
            'blend_strength': '0.3'
        }
        
        self.config['DEBUG'] = {
            'visualize': 'False'
        }
        
        self.config['THRESH'] = {
            'visualize': 'False'
        }
        
        self.config['CONTOUR'] = {
            'visualize': 'False'
        }
        
        self.config['STITCH'] = {
            'visualize': 'False'
        }
    
    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get boolean value from config
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (bool): Default value if key not found
            
        Returns:
            bool: Configuration value
        """
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            print(f"Warning: Config key '{section}.{key}' not found or invalid. Using fallback: {fallback}")
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """
        Get integer value from config
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (int): Default value if key not found
            
        Returns:
            int: Configuration value
        """
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            print(f"Warning: Config key '{section}.{key}' not found or invalid. Using fallback: {fallback}")
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """
        Get float value from config
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (float): Default value if key not found
            
        Returns:
            float: Configuration value
        """
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            print(f"Warning: Config key '{section}.{key}' not found or invalid. Using fallback: {fallback}")
            return fallback
    
    def get_string(self, section: str, key: str, fallback: str = '') -> str:
        """
        Get string value from config
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (str): Default value if key not found
            
        Returns:
            str: Configuration value
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            print(f"Warning: Config key '{section}.{key}' not found. Using fallback: '{fallback}'")
            return fallback
    
    def save_config(self):
        """Save current configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        print(f"Configuration saved to: {self.config_path}")
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configuration settings as a dictionary
        
        Returns:
            dict: All configuration settings
        """
        settings = {}
        for section_name in self.config.sections():
            settings[section_name] = dict(self.config.items(section_name))
        
        # Also include DEFAULT section
        if self.config.defaults():
            settings['DEFAULT'] = dict(self.config.defaults())
            
        return settings
    
    def reload_config(self):
        """Reload configuration from file"""
        self.load_config()


# Create a global instance for easy access
_global_config = None

def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance
    
    Returns:
        ConfigManager: Global configuration manager
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config
