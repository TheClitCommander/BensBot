#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Orchestrator

This module provides the central orchestration for the trading bot system,
coordinating different components like data fetching, strategy execution,
risk management, and order management.
"""

import logging
import time
import signal
import threading
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from trading_bot.core.service_registry import ServiceRegistry
from trading_bot.core.interfaces import DataProvider, Strategy, RiskManager, OrderManager
from trading_bot.utils.config_parser import load_config_file, validate_calendar_spread_config
from trading_bot.data.data_manager import DataManager
from trading_bot.strategies.options.spreads.calendar_spread import CalendarSpread as CalendarSpreadStrategy
from trading_bot.strategies.stocks.swing import StockSwingTradingStrategy

logger = logging.getLogger(__name__)

class MainOrchestrator:
    """
    Main orchestrator that coordinates the trading bot components.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config = load_config_file(config_path)
        if not self.config:
            raise ValueError(f"Failed to load configuration from {config_path}")
        
        self.running = False
        self.should_stop = threading.Event()
        self.active_strategies: Set[str] = set()
        self.last_run_time: Dict[str, datetime] = {}
        
        # Store registered strategies
        self.strategies: Dict[str, Any] = {}
        
        # Initialize components based on configuration
        self._initialize_components()
        
        logger.info("MainOrchestrator initialized")
    
    def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        try:
            # Initialize data manager first
            self._initialize_data_manager()
            
            # Initialize strategies
            self._initialize_strategies()
            
            # Initialize risk manager
            self._initialize_risk_manager()
            
            # Initialize order manager
            self._initialize_order_manager()
            
            logger.info("All components initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _initialize_data_manager(self) -> None:
        """Initialize data manager based on configuration."""
        try:
            # Get data manager configuration
            data_config = self.config.get("data_providers", {})
            storage_config = self.config.get("data_storage", {})
            realtime_config = self.config.get("realtime_providers", {})
            
            # Create combined config
            data_manager_config = {
                "data_providers": data_config,
                "data_storage": storage_config,
                "realtime_providers": realtime_config,
                "enable_cache": True,
                "cache_expiry_minutes": 30
            }
            
            # Initialize data manager
            data_manager = DataManager(data_manager_config)
            
            # Register data manager
            ServiceRegistry.register("data_manager", data_manager, DataManager)
            
            logger.info("Data manager initialized")
            
        except Exception as e:
            logger.error(f"Error initializing data manager: {e}")
            raise
    
    def _initialize_strategies(self) -> None:
        """Initialize trading strategies based on configuration."""
        try:
            # Load strategies from configuration
            strategy_configs = self.config.get("strategies", {})
            
            for strategy_name, strategy_config in strategy_configs.items():
                if not strategy_config.get("enabled", False):
                    logger.info(f"Strategy '{strategy_name}' is disabled, skipping initialization")
                    continue
                
                # Initialize the strategy based on type
                if strategy_name == "calendar_spread":
                    self._initialize_calendar_spread(strategy_name, strategy_config)
                elif strategy_name == "swing_trading":
                    self._initialize_swing_trading(strategy_name, strategy_config)
                else:
                    logger.warning(f"Unknown strategy type: {strategy_name}")
            
        except Exception as e:
            logger.error(f"Error initializing strategies: {e}")
            raise
    
    def _initialize_calendar_spread(self, name: str, config: Dict[str, Any]) -> None:
        """
        Initialize calendar spread strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        try:
            # Extract parameters from config
            params = config.get("parameters", {})
            symbols = config.get("symbols", [])
            interval_minutes = config.get("interval_minutes", 60)
            
            # Create strategy instance
            strategy = CalendarSpreadStrategy(name=name, parameters=params)
            
            # Store in active strategies and strategies dict
            self.strategies[name] = strategy
            self.active_strategies.add(name)
            
            # Register strategy in service registry
            ServiceRegistry.register(f"strategy.{name}", strategy, Strategy)
            
            logger.info(f"Calendar spread strategy '{name}' initialized with {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error initializing calendar spread strategy '{name}': {e}")
    
    def _initialize_swing_trading(self, name: str, config: Dict[str, Any]) -> None:
        """
        Initialize swing trading strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        try:
            # Extract parameters from config
            params = config.get("parameters", {})
            symbols = config.get("symbols", [])
            interval_minutes = config.get("interval_minutes", 240)  # 4 hours default
            
            # Create strategy instance
            strategy = StockSwingTradingStrategy(name=name, parameters=params)
            
            # Store in active strategies and strategies dict
            self.strategies[name] = strategy
            self.active_strategies.add(name)
            
            # Register strategy in service registry
            ServiceRegistry.register(f"strategy.{name}", strategy, Strategy)
            
            logger.info(f"Stock swing trading strategy '{name}' initialized with {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error initializing stock swing trading strategy '{name}': {e}")
    
    def _initialize_risk_manager(self) -> None:
        """Initialize risk manager based on configuration."""
        # This would load and register the risk manager
        logger.info("Risk manager would be initialized here")
    
    def _initialize_order_manager(self) -> None:
        """Initialize order manager based on configuration."""
        # This would load and register the order manager
        logger.info("Order manager would be initialized here")
    
    def start(self) -> None:
        """Start the orchestrator and its components."""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        logger.info("Starting MainOrchestrator")
        self.running = True
        self.should_stop.clear()
        
        try:
            # Start data manager and real-time streams
            data_manager = ServiceRegistry.get("data_manager")
            data_manager.start_realtime_stream()
            
            # Main processing loop
            while not self.should_stop.is_set():
                try:
                    self._process_cycle()
                except Exception as e:
                    logger.error(f"Error in processing cycle: {e}")
                
                # Sleep to avoid excessive CPU usage
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping")
        except Exception as e:
            logger.error(f"Error in orchestrator main loop: {e}")
        
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the orchestrator and all components."""
        if not self.running:
            return
        
        logger.info("Stopping MainOrchestrator")
        self.should_stop.set()
        self.running = False
        
        # Perform cleanup of components
        try:
            # Stop data manager and real-time streams
            if ServiceRegistry.has_service("data_manager"):
                data_manager = ServiceRegistry.get("data_manager")
                data_manager.stop_realtime_stream()
                data_manager.shutdown()
            
            logger.info("Components stopped and cleaned up")
        
        except Exception as e:
            logger.error(f"Error stopping components: {e}")
    
    def _process_cycle(self) -> None:
        """Process a single cycle of the trading system."""
        current_time = datetime.now()
        
        for strategy_name in self.active_strategies:
            # Check if it's time to run this strategy
            last_run = self.last_run_time.get(strategy_name, datetime.min)
            strategy_interval = self._get_strategy_interval(strategy_name)
            
            if current_time - last_run >= strategy_interval:
                self._run_strategy_cycle(strategy_name)
                self.last_run_time[strategy_name] = current_time
    
    def _get_strategy_interval(self, strategy_name: str) -> timedelta:
        """Get the execution interval for a strategy."""
        # Default to 5 minutes if not specified
        interval_minutes = self.config.get("strategies", {}).get(
            strategy_name, {}).get("interval_minutes", 5)
        return timedelta(minutes=interval_minutes)
    
    def _run_strategy_cycle(self, strategy_name: str) -> None:
        """Run a complete cycle for a specific strategy."""
        logger.info(f"Running cycle for strategy: {strategy_name}")
        
        try:
            # Get strategy configuration
            strategy_config = self.config.get("strategies", {}).get(strategy_name, {})
            symbols = strategy_config.get("symbols", [])
            
            if not symbols:
                logger.warning(f"No symbols configured for strategy: {strategy_name}")
                return
            
            # 1. Fetch market data using data manager
            data_manager = ServiceRegistry.get("data_manager")
            market_data = self._fetch_market_data(strategy_name, symbols, data_manager)
            
            if not market_data:
                logger.warning(f"No market data available for strategy: {strategy_name}")
                return
            
            # 2. Generate signals using the strategy
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                logger.warning(f"Strategy not found: {strategy_name}")
                return
                
            signals = strategy.generate_signals(market_data)
            
            if not signals:
                logger.info(f"No signals generated for strategy: {strategy_name}")
                return
            
            logger.info(f"Generated {len(signals)} signals for strategy: {strategy_name}")
            
            # 3. Validate signals with risk manager (to be implemented)
            # approved_signals = self._validate_signals(signals)
            approved_signals = signals  # Temporary, until risk manager is implemented
            
            # 4. Execute approved signals (to be implemented)
            if approved_signals:
                logger.info(f"Would execute {len(approved_signals)} signals for strategy: {strategy_name}")
                # self._execute_signals(approved_signals)
            else:
                logger.info(f"No approved signals for strategy: {strategy_name}")
        
        except Exception as e:
            logger.error(f"Error running cycle for strategy '{strategy_name}': {e}")
    
    def _fetch_market_data(self, strategy_name: str, symbols: List[str], data_manager: Any) -> Dict[str, Any]:
        """
        Fetch market data for a strategy.
        
        Args:
            strategy_name: Strategy name
            symbols: List of symbols to fetch data for
            data_manager: Data manager instance
            
        Returns:
            Dictionary with market data
        """
        try:
            # Determine required lookback period (default to 1 year)
            lookback_days = self.config.get("strategies", {}).get(
                strategy_name, {}).get("lookback_days", 365)
            
            # Calculate dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Fetch market data
            market_data = data_manager.get_market_data(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
            
            # If this is a strategy that needs option data, fetch it
            if strategy_name == "calendar_spread":
                # Fetch option chains for each symbol
                option_data = {}
                for symbol in symbols:
                    option_data[symbol] = data_manager.get_option_chain(symbol)
                
                # Add option data to market data
                for symbol, data in market_data.items():
                    if symbol in option_data:
                        data['options'] = option_data[symbol]
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data for strategy '{strategy_name}': {e}")
            return {}

def setup_signal_handlers(orchestrator: MainOrchestrator) -> None:
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        orchestrator.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler) 