#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration utilities for the trading bot.
"""

import os
import json
import logging
from typing import Dict, Any, Callable, Optional
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

def setup_directories(
    data_dir: Optional[str] = None,
    component_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Setup directories for the trading bot.
    
    Args:
        data_dir: Base directory for data storage
        component_name: Name of the component
        
    Returns:
        Dictionary with directory paths
    """
    # Determine base directories
    if data_dir is None:
        # Default to a 'data' directory next to the code
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, 'data')
    
    # Ensure base data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Create component subdirectory if specified
    component_dir = data_dir
    if component_name:
        component_dir = os.path.join(data_dir, component_name)
        os.makedirs(component_dir, exist_ok=True)
    
    # Create standard subdirectories
    paths = {
        'data_dir': data_dir,
        'component_dir': component_dir,
        'config_path': os.path.join(component_dir, 'config.json'),
        'state_path': os.path.join(component_dir, 'state.json'),
        'log_dir': os.path.join(component_dir, 'logs'),
        'model_dir': os.path.join(component_dir, 'models')
    }
    
    # Create all directories
    for dir_path in [paths['log_dir'], paths['model_dir']]:
        os.makedirs(dir_path, exist_ok=True)
    
    return paths

def load_config(
    config_path: str,
    default_config_factory: Optional[Callable[[], Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to config file
        default_config_factory: Function to generate default config
        
    Returns:
        Configuration dictionary
    """
    config = {}
    
    # Try to load existing config
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            
            # If loading fails and we have a default factory, use it
            if default_config_factory:
                config = default_config_factory()
                logger.info("Using default configuration")
    # If no config exists and we have a default factory, use it and save
    elif default_config_factory:
        config = default_config_factory()
        logger.info("Creating default configuration")
        
        # Save default config
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved default configuration to {config_path}")
        except Exception as e:
            logger.error(f"Error saving default config to {config_path}: {str(e)}")
    
    return config

def save_state(state_path: str, state: Dict[str, Any]) -> bool:
    """
    Save state to a JSON file.
    
    Args:
        state_path: Path to state file
        state: State dictionary to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        
        # Save the state
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
            
        logger.info(f"Saved state to {state_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving state to {state_path}: {str(e)}")
        return False

def load_state(state_path: str) -> Optional[Dict[str, Any]]:
    """
    Load state from a JSON file.
    
    Args:
        state_path: Path to state file
        
    Returns:
        State dictionary or None if loading failed
    """
    if not os.path.exists(state_path):
        logger.info(f"No state file found at {state_path}")
        return None
        
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
            
        logger.info(f"Loaded state from {state_path}")
        return state
    except Exception as e:
        logger.error(f"Error loading state from {state_path}: {str(e)}")
        return None 