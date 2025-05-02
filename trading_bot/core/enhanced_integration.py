#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Integration Module for BensBot

This module provides initialization and integration functions
for the enhanced reliability and efficiency components:
1. Persistence Layer (MongoDB)
2. Watchdog & Fault Tolerance
3. Dynamic Capital Scaling
4. Strategy Retirement & Promotion
5. Execution Quality Modeling

Usage:
    from trading_bot.core.enhanced_integration import initialize_enhanced_components
    
    # Initialize components
    components = initialize_enhanced_components(config)
    
    # Access individual components
    persistence = components['persistence']
    watchdog = components['watchdog']
    capital_manager = components['capital_manager']
    strategy_manager = components['strategy_manager']
    execution_model = components['execution_model']
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import enhanced components
from trading_bot.data.persistence import PersistenceManager
from trading_bot.core.watchdog import ServiceWatchdog, RecoveryStrategy
from trading_bot.risk.capital_manager import CapitalManager
from trading_bot.core.strategy_manager import StrategyPerformanceManager
from trading_bot.execution.execution_model import ExecutionQualityModel

logger = logging.getLogger(__name__)

def initialize_enhanced_components(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize all enhanced reliability and efficiency components
    
    Args:
        config: Configuration dictionary with settings for all components
        
    Returns:
        dict: Dictionary containing initialized component instances
    """
    components = {}
    
    try:
        # Extract configurations
        persistence_config = config.get('persistence', {})
        watchdog_config = config.get('watchdog', {})
        capital_config = config.get('capital', {})
        strategy_config = config.get('strategy_manager', {})
        execution_config = config.get('execution', {})
        
        # 1. Initialize Persistence Layer
        logger.info("Initializing Persistence Layer")
        persistence = PersistenceManager(
            connection_string=persistence_config.get('mongodb_uri', "mongodb://localhost:27017/"),
            database=persistence_config.get('database', "bensbot"),
            auto_connect=persistence_config.get('auto_connect', True)
        )
        components['persistence'] = persistence
        
        # 2. Initialize Capital Manager
        logger.info("Initializing Capital Manager")
        capital_manager = CapitalManager(
            initial_capital=capital_config.get('initial_capital', 100000.0),
            risk_params=capital_config.get('risk_params', None),
            persistence_manager=persistence
        )
        components['capital_manager'] = capital_manager
        
        # 3. Initialize Strategy Manager
        logger.info("Initializing Strategy Performance Manager")
        strategy_manager = StrategyPerformanceManager(
            persistence_manager=persistence,
            evaluation_params=strategy_config.get('evaluation_params', None)
        )
        components['strategy_manager'] = strategy_manager
        
        # 4. Initialize Execution Quality Model
        logger.info("Initializing Execution Quality Model")
        execution_model = ExecutionQualityModel(
            parameters=execution_config.get('parameters', None)
        )
        components['execution_model'] = execution_model
        
        # 5. Initialize Watchdog (last, since it may depend on other components)
        logger.info("Initializing Service Watchdog")
        watchdog = ServiceWatchdog(
            check_interval_seconds=watchdog_config.get('check_interval', 30),
            persistence_manager=persistence
        )
        components['watchdog'] = watchdog
        
        logger.info("All enhanced components initialized successfully")
        return components
    
    except Exception as e:
        logger.error(f"Error initializing enhanced components: {str(e)}")
        # Return any components that were successfully initialized
        return components

def register_core_services(watchdog: ServiceWatchdog, 
                         data_feed: Any, 
                         broker: Any,
                         trading_engine: Any) -> None:
    """
    Register core services with the watchdog for monitoring
    
    Args:
        watchdog: Initialized ServiceWatchdog instance
        data_feed: Data feed service
        broker: Broker service
        trading_engine: Trading engine service
    """
    # Register data feed service
    watchdog.register_service(
        name="data_feed",
        health_check=lambda: data_feed.is_connected(),
        recovery_action=lambda: data_feed.reconnect(),
        recovery_strategy=RecoveryStrategy.RECONNECT,
        max_failures=3,
        cooldown_seconds=60
    )
    
    # Register broker service
    watchdog.register_service(
        name="broker_connection",
        health_check=lambda: broker.is_connected(),
        recovery_action=lambda: broker.reconnect(),
        recovery_strategy=RecoveryStrategy.RECONNECT,
        max_failures=2,
        cooldown_seconds=120
    )
    
    # Register trading engine service
    watchdog.register_service(
        name="trading_engine",
        health_check=lambda: trading_engine.check_health(),
        recovery_action=lambda: trading_engine.restore_from_saved_state(),
        recovery_strategy=RecoveryStrategy.RELOAD_STATE,
        max_failures=2,
        cooldown_seconds=300,
        dependencies=["data_feed", "broker_connection"]
    )
    
    logger.info("Core services registered with watchdog")

def integrate_with_trading_system(trading_engine: Any, 
                                components: Dict[str, Any]) -> None:
    """
    Integrate enhanced components with the main trading system
    
    Args:
        trading_engine: The main trading engine instance
        components: Dictionary of enhanced components
    """
    # Extract components
    persistence = components.get('persistence')
    capital_manager = components.get('capital_manager')
    strategy_manager = components.get('strategy_manager')
    execution_model = components.get('execution_model')
    
    # Set references in trading engine
    if hasattr(trading_engine, 'set_persistence_manager'):
        trading_engine.set_persistence_manager(persistence)
        
    if hasattr(trading_engine, 'set_capital_manager'):
        trading_engine.set_capital_manager(capital_manager)
        
    if hasattr(trading_engine, 'set_strategy_manager'):
        trading_engine.set_strategy_manager(strategy_manager)
        
    if hasattr(trading_engine, 'set_execution_model'):
        trading_engine.set_execution_model(execution_model)
        
    logger.info("Enhanced components integrated with trading engine")

def load_saved_states(components: Dict[str, Any]) -> bool:
    """
    Load saved states for all components from persistence
    
    Args:
        components: Dictionary of enhanced components
        
    Returns:
        bool: True if all states loaded successfully
    """
    persistence = components.get('persistence')
    if not persistence or not persistence.is_connected():
        logger.warning("Cannot load states: Persistence not available")
        return False
        
    try:
        # Load capital manager state
        capital_manager = components.get('capital_manager')
        if capital_manager:
            state = persistence.load_strategy_state('capital_manager')
            if state:
                capital_manager.load_state(state)
                logger.info("Capital manager state loaded")
            
        # Load strategy manager state
        strategy_manager = components.get('strategy_manager')
        if strategy_manager:
            state = persistence.load_strategy_state('strategy_manager')
            if state:
                strategy_manager.load_state(state)
                logger.info("Strategy manager state loaded")
                
        return True
    except Exception as e:
        logger.error(f"Error loading saved states: {str(e)}")
        return False

def save_states(components: Dict[str, Any]) -> bool:
    """
    Save states for all components to persistence
    
    Args:
        components: Dictionary of enhanced components
        
    Returns:
        bool: True if all states saved successfully
    """
    persistence = components.get('persistence')
    if not persistence or not persistence.is_connected():
        logger.warning("Cannot save states: Persistence not available")
        return False
        
    try:
        # Save capital manager state
        capital_manager = components.get('capital_manager')
        if capital_manager:
            capital_manager.save_state()
            logger.info("Capital manager state saved")
            
        # Save strategy manager state
        strategy_manager = components.get('strategy_manager')
        if strategy_manager:
            strategy_manager.save_state()
            logger.info("Strategy manager state saved")
                
        return True
    except Exception as e:
        logger.error(f"Error saving states: {str(e)}")
        return False
        
def shutdown_components(components: Dict[str, Any]) -> None:
    """
    Properly shut down all enhanced components
    
    Args:
        components: Dictionary of enhanced components
    """
    # Save states first
    save_states(components)
    
    # Shutdown watchdog
    watchdog = components.get('watchdog')
    if watchdog:
        watchdog.stop()
        logger.info("Watchdog stopped")
        
    # Disconnect from persistence
    persistence = components.get('persistence')
    if persistence:
        persistence.disconnect()
        logger.info("Persistence disconnected")
        
    logger.info("All enhanced components shut down")

# Example usage in a main function
def example_usage():
    """Example of how to use the enhanced integration module"""
    # Sample configuration
    config = {
        'persistence': {
            'mongodb_uri': "mongodb://localhost:27017/",
            'database': "bensbot",
            'auto_connect': True
        },
        'capital': {
            'initial_capital': 100000.0,
            'risk_params': {
                'base_risk_pct': 0.01,
                'max_account_risk_pct': 0.05
            }
        },
        'watchdog': {
            'check_interval': 30
        },
        'strategy_manager': {
            'evaluation_params': {
                'min_trades': 20,
                'evaluation_window': 30
            }
        },
        'execution': {
            'parameters': {
                'volatility_spread_multiplier': 2.0
            }
        }
    }
    
    # Initialize components
    components = initialize_enhanced_components(config)
    
    # Access individual components
    persistence = components.get('persistence')
    capital_manager = components.get('capital_manager')
    strategy_manager = components.get('strategy_manager')
    execution_model = components.get('execution_model')
    watchdog = components.get('watchdog')
    
    # Load saved states
    load_saved_states(components)
    
    # Start watchdog
    if watchdog:
        watchdog.start()
    
    # Use components in your trading system...
    
    # When shutting down
    shutdown_components(components)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
