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
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta
import os

from trading_bot.core.service_registry import ServiceRegistry
from trading_bot.core.interfaces import DataProvider, StrategyInterface as Strategy, RiskManager, OrderManager

# Import legacy config utils for backwards compatibility
from trading_bot.utils.config_parser import load_config_file, validate_calendar_spread_config

# Import typed settings if available
try:
    from trading_bot.config.typed_settings import (
        load_config as typed_load_config, 
        TradingBotSettings,
        OrchestratorSettings,
        RiskSettings,
        BrokerSettings,
        DataSettings
    )
    from trading_bot.config.migration_utils import get_config_from_legacy_path
    TYPED_SETTINGS_AVAILABLE = True
except ImportError:
    TYPED_SETTINGS_AVAILABLE = False
from trading_bot.data.data_manager import DataManager
from trading_bot.strategies.options.spreads.calendar_spread import CalendarSpread as CalendarSpreadStrategy
from trading_bot.strategies.stocks.swing import StockSwingTradingStrategy

logger = logging.getLogger(__name__)

class MainOrchestrator:
    """
    Main orchestrator that coordinates the trading bot components.
    """
    
    def __init__(self, config_path: str, settings: Optional[TradingBotSettings] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to the main configuration file
            settings: Optional typed settings object (new approach)
        """
        # Store initialization parameters
        self.config_path = config_path
        self.typed_settings = settings
        
        # Try to load configuration with typed settings first if available
        if TYPED_SETTINGS_AVAILABLE and not settings and os.path.exists(config_path):
            try:
                # Check if config path looks like a YAML file for typed settings
                if config_path.endswith(('.yaml', '.yml', '.json')):
                    self.typed_settings = typed_load_config(config_path)
                    logger.info(f"Loaded typed settings from {config_path}")
            except Exception as e:
                logger.warning(f"Could not load typed settings: {e}, falling back to legacy config")
        
        # Initialize traditional config (for backward compatibility)
        self.config = {}
        if not self.typed_settings:
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
            # Check if we have typed settings for data manager
            if TYPED_SETTINGS_AVAILABLE and self.typed_settings and hasattr(self.typed_settings, 'data'):
                data_settings = self.typed_settings.data
                
                # Create combined config from typed settings
                data_manager_config = {
                    "data_providers": {
                        "tradier": {
                            "api_key": data_settings.tradier_api_key,
                            "account_id": data_settings.tradier_account_id
                        },
                        "alpha_vantage": {
                            "api_key": data_settings.alpha_vantage_api_key
                        }
                    },
                    "data_storage": {
                        "type": data_settings.storage_type,
                        "path": data_settings.storage_path
                    },
                    "realtime_providers": {
                        "tradier": {
                            "enabled": data_settings.enable_realtime_updates
                        }
                    },
                    "enable_cache": data_settings.enable_cache,
                    "cache_expiry_minutes": data_settings.cache_expiry_minutes
                }
                
                logger.info("Using data manager configuration from typed settings")
            else:
                # Use legacy config
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
                
                logger.info("Using data manager configuration from legacy config")
            
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
            # Check if we have typed settings for strategies
            if TYPED_SETTINGS_AVAILABLE and self.typed_settings and hasattr(self.typed_settings, 'strategy'):
                # Get strategy settings
                strategy_settings = self.typed_settings.strategy
                
                # Import our strategy factory if available
                try:
                    from trading_bot.strategies.strategy_factory import StrategyFactory
                    factory_available = True
                except ImportError:
                    factory_available = False
                
                # Create strategies from typed settings using factory if available
                if factory_available:
                    for strategy_name in strategy_settings.enabled_strategies:
                        try:
                            # Create strategy using the factory with typed settings
                            strategy = StrategyFactory.create_strategy(
                                strategy_type=strategy_name,
                                settings=strategy_settings,
                                enable_notifications=strategy_settings.enable_notifications
                            )
                            
                            # Register strategy
                            self.strategies[strategy_name] = strategy
                            self.active_strategies.add(strategy_name)
                            
                            logger.info(f"Strategy {strategy_name} initialized using strategy factory")
                        except Exception as e:
                            logger.error(f"Failed to initialize strategy {strategy_name}: {e}")
                else:
                    # Fall back to individual strategy creation
                    # For now we'll handle specifically configured strategies
                    if "calendar_spread" in strategy_settings.enabled_strategies:
                        self._initialize_calendar_spread("calendar_spread", {})
                    
                    if "swing_trading" in strategy_settings.enabled_strategies:
                        self._initialize_swing_trading("swing_trading", {})
            else:
                # Load strategies from legacy configuration
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
        try:
            # Check if we have typed settings for risk manager
            if TYPED_SETTINGS_AVAILABLE and self.typed_settings and hasattr(self.typed_settings, 'risk'):
                # Import risk manager
                from trading_bot.risk.risk_manager import RiskManager
                
                # Create risk manager with typed settings
                risk_manager = RiskManager(settings=self.typed_settings.risk)
                
                # Import and apply risk check capability
                from trading_bot.risk.risk_check import add_check_trade_to_risk_manager
                add_check_trade_to_risk_manager(risk_manager, self.typed_settings.risk)
                
                # Register risk manager
                ServiceRegistry.register("risk_manager", risk_manager)
                
                logger.info("Risk manager initialized with typed settings")
            else:
                # Use legacy config if available
                risk_config = self.config.get("risk_management", {})
                if risk_config:
                    # Import risk manager
                    from trading_bot.risk.risk_manager import RiskManager
                    
                    # Create risk manager with legacy config
                    risk_manager = RiskManager(config=risk_config)
                    
                    # Import and apply risk check capability
                    from trading_bot.risk.risk_check import add_check_trade_to_risk_manager
                    add_check_trade_to_risk_manager(risk_manager)
                    
                    # Register risk manager
                    ServiceRegistry.register("risk_manager", risk_manager)
                    
                    logger.info("Risk manager initialized with legacy config")
                else:
                    logger.warning("No risk management configuration found - running without risk controls")
        except Exception as e:
            logger.error(f"Error initializing risk manager: {e}")
            # Don't re-raise, we can operate without risk management but with limited safety load and register the risk manager
        logger.info("Risk manager would be initialized here")
    
    def _initialize_order_manager(self) -> None:
        """Initialize order manager based on configuration."""
        try:
            # Check if we have typed settings for broker/order management
            if TYPED_SETTINGS_AVAILABLE and self.typed_settings and hasattr(self.typed_settings, 'broker'):
                # Get broker settings
                broker_settings = self.typed_settings.broker
                
                # Initialize Tradier client with typed settings
                from trading_bot.brokers.tradier_client import TradierClient
                tradier_client = TradierClient(
                    api_key=broker_settings.api_key,
                    account_id=broker_settings.account_id,
                    sandbox=broker_settings.sandbox_mode
                )
                
                # Initialize trade executor with typed settings and risk manager
                from trading_bot.brokers.trade_executor import TradeExecutor
                risk_manager = ServiceRegistry.get("risk_manager", None)
                
                # Create trade executor
                trade_executor = TradeExecutor(
                    tradier_client=tradier_client,
                    risk_manager=risk_manager,
                    settings=broker_settings,
                    config_path=self.config_path
                )
                
                # Register order manager
                ServiceRegistry.register("order_manager", trade_executor)
                
                logger.info("Order manager initialized with typed settings")
            else:
                # Use legacy config
                broker_config = self.config.get("broker", {})
                if broker_config:
                    # Initialize Tradier client with legacy config
                    from trading_bot.brokers.tradier_client import TradierClient
                    tradier_client = TradierClient(
                        api_key=broker_config.get("api_key"),
                        account_id=broker_config.get("account_id"),
                        sandbox=broker_config.get("sandbox_mode", True)
                    )
                    
                    # Initialize trade executor with legacy config and risk manager
                    from trading_bot.brokers.trade_executor import TradeExecutor
                    risk_manager = ServiceRegistry.get("risk_manager", None)
                    
                    # Create trade executor
                    trade_executor = TradeExecutor(
                        tradier_client=tradier_client,
                        risk_manager=risk_manager,
                        max_position_pct=broker_config.get("max_position_pct", 0.05),
                        max_risk_pct=broker_config.get("max_risk_pct", 0.01),
                        order_type=broker_config.get("default_order_type", "market"),
                        order_duration=broker_config.get("default_order_duration", "day")
                    )
                    
                    # Register order manager
                    ServiceRegistry.register("order_manager", trade_executor)
                    
                    logger.info("Order manager initialized with legacy config")
                else:
                    logger.warning("No broker configuration found - trading execution disabled")
        except Exception as e:
            logger.error(f"Error initializing order manager: {e}")
            # Don't re-raise, we can still run in analysis-only mode load and register the order manager
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
            
            # 3. Validate signals with risk manager
            risk_manager = ServiceRegistry.get("risk_manager", None)
            
            if risk_manager:
                approved_signals = []
                for signal in signals:
                    # Convert signal to order format for risk check
                    order = {
                        "symbol": signal.get("symbol"),
                        "side": signal.get("action"),  # 'buy' or 'sell'
                        "quantity": signal.get("quantity", 0),
                        "price": signal.get("price", 0),
                        "stop_price": signal.get("stop_price"),
                        "dollar_amount": signal.get("estimated_value", 0),
                        "strategy": strategy_name
                    }
                    
                    # Perform risk check
                    if hasattr(risk_manager, 'check_trade'):
                        result = risk_manager.check_trade(order)
                        if result.get("approved", False):
                            approved_signals.append(signal)
                            if result.get("warnings"):
                                logger.warning(f"Risk warnings for {signal.get('symbol')}: {', '.join(result.get('warnings', []))}")
                        else:
                            logger.warning(f"Signal rejected by risk manager: {result.get('reason')}")
                    else:
                        # Risk manager doesn't have check_trade method
                        approved_signals.append(signal)
                        logger.warning(f"Risk manager doesn't have check_trade method, signal approved without risk check")
            else:
                # No risk manager available
                approved_signals = signals
                logger.warning("No risk manager available, all signals approved without risk check")
            
            # 4. Execute approved signals
            if approved_signals:
                logger.info(f"Executing {len(approved_signals)} signals for strategy: {strategy_name}")
                self._execute_signals(strategy_name, approved_signals)
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

    def _execute_signals(self, strategy_name: str, signals: List[Dict[str, Any]]) -> None:
        """
        Execute approved trading signals using the order manager.
        
        Args:
            strategy_name: Name of the strategy that generated the signals
            signals: List of approved trading signals to execute
        """
        try:
            # Get the order manager from service registry
            order_manager = ServiceRegistry.get("order_manager", None)
            
            if not order_manager:
                logger.warning("No order manager available, cannot execute signals")
                return
            
            for signal in signals:
                try:
                    symbol = signal.get("symbol")
                    action = signal.get("action")  # 'buy' or 'sell'
                    price = signal.get("price")   # Can be None for market orders
                    stop_price = signal.get("stop_price")
                    target_price = signal.get("target_price")
                    quantity = signal.get("quantity")
                    risk_pct = signal.get("risk_pct")
                    
                    # Add metadata to the trade
                    metadata = {
                        "strategy": strategy_name,
                        "signal_time": datetime.now().isoformat(),
                        "confidence": signal.get("confidence", 0),
                        "signal_id": signal.get("id", str(uuid.uuid4()))
                    }
                    
                    # Execute the trade
                    logger.info(f"Executing {action} signal for {symbol} from {strategy_name}")
                    
                    result = order_manager.execute_trade(
                        symbol=symbol,
                        side=action,
                        entry_price=price,
                        stop_price=stop_price,
                        target_price=target_price,
                        shares=quantity,
                        risk_pct=risk_pct,
                        strategy_name=strategy_name,
                        metadata=metadata
                    )
                    
                    if result.get("status") == "rejected":
                        logger.warning(f"Order rejected: {result.get('message')}")
                    elif result.get("status") == "error":
                        logger.error(f"Order error: {result.get('message')}")
                    else:
                        logger.info(f"Order placed successfully: {result.get('order_id')}")
                        
                except Exception as signal_error:
                    logger.error(f"Error executing signal for {signal.get('symbol', 'unknown')}: {signal_error}")
        
        except Exception as e:
            logger.error(f"Error executing signals for strategy {strategy_name}: {e}")


def setup_signal_handlers(orchestrator: MainOrchestrator) -> None:
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        orchestrator.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler) 