"""
Strategy Factory

This module provides a factory for creating trading strategies
based on strategy type and configuration.
"""

import logging
import os
from typing import Dict, Any, Optional, Type, Union

logger = logging.getLogger(__name__)

# Import typed settings if available
try:
    from trading_bot.config.typed_settings import (
        load_config, StrategySettings, NotificationSettings, TradingBotSettings
    )
    from trading_bot.config.migration_utils import get_config_from_legacy_path
    TYPED_SETTINGS_AVAILABLE = True
except ImportError:
    TYPED_SETTINGS_AVAILABLE = False

# Import our notification wrapper
try:
    from trading_bot.strategies.strategy_notification_wrapper import wrap_strategy_with_notifications
    NOTIFICATION_WRAPPER_AVAILABLE = True
except ImportError:
    logger.warning("Strategy notification wrapper not available")
    NOTIFICATION_WRAPPER_AVAILABLE = False

# Import available strategies
try:
    from trading_bot.strategies.stocks.momentum import MomentumStrategy
    from trading_bot.strategies.stocks.mean_reversion import MeanReversionStrategy
    from trading_bot.strategies.stocks.trend import MultiTimeframeCorrelationStrategy as TrendFollowingStrategy
    from trading_bot.strategies.stocks.breakout import VolatilityBreakoutStrategy
    STRATEGIES_AVAILABLE = True
except ImportError:
    logger.warning("Some strategy modules could not be imported. Using mock strategies.")
    STRATEGIES_AVAILABLE = False

    # Define mock strategy classes for when real ones aren't available
    class BaseStrategy:
        """Base class for all trading strategies"""
        
        def __init__(self, config=None):
            self.config = config or {}
            logger.info(f"Initialized {self.__class__.__name__}")
            
        def generate_signals(self, data, **kwargs):
            """Generate trading signals"""
            return {"action": "hold", "confidence": 0.5}
        
        @classmethod
        def is_available(cls):
            return True
    
    class MomentumStrategy(BaseStrategy):
        """Mock momentum strategy"""
        pass
    
    class MeanReversionStrategy(BaseStrategy):
        """Mock mean reversion strategy"""
        pass
    
    class TrendFollowingStrategy(BaseStrategy):
        """Mock trend following strategy"""
        pass
    
    class VolatilityBreakoutStrategy(BaseStrategy):
        """Mock volatility breakout strategy"""
        pass


class StrategyFactory:
    """Factory class for creating strategy objects"""
    
    @staticmethod
    def create_strategy(strategy_type: str, 
                     config: Optional[Dict[str, Any]] = None, 
                     enable_notifications: bool = True,
                     settings: Optional[Union[StrategySettings, TradingBotSettings]] = None,
                     config_path: Optional[str] = None):
        """
        Create a strategy object by type
        
        Args:
            strategy_type: Type of strategy to create
            config: Optional configuration dictionary (legacy approach)
            enable_notifications: Whether to enable notifications for this strategy
            settings: Optional typed settings object (new approach)
            config_path: Optional path to config file to load settings from
            
        Returns:
            Strategy object with notification capabilities if enabled
        """
        # Prioritize typed settings if available, fall back to legacy config
        if TYPED_SETTINGS_AVAILABLE:
            # If full settings provided, extract strategy settings
            if settings is not None:
                if hasattr(settings, 'strategy') and hasattr(settings, 'notification'):
                    # Full TradingBotSettings provided
                    strategy_settings = settings.strategy
                    notification_settings = settings.notification
                elif hasattr(settings, 'parameters'):  
                    # Just StrategySettings provided
                    strategy_settings = settings
                    # Try to load notification settings from config path
                    notification_settings = None
                    if config_path:
                        try:
                            full_config = load_config(config_path)
                            notification_settings = full_config.notification
                        except Exception as e:
                            logger.warning(f"Could not load notification settings from config: {e}")
                else:
                    strategy_settings = None
                    notification_settings = None
            # If no settings provided but config path is, try to load from there
            elif config_path:
                try:
                    full_config = load_config(config_path)
                    strategy_settings = full_config.strategy
                    notification_settings = full_config.notification
                except Exception as e:
                    logger.warning(f"Could not load typed settings from path: {e}")
                    strategy_settings = None
                    notification_settings = None
            else:
                strategy_settings = None
                notification_settings = None
                
            # Convert typed settings to config dict if available
            if strategy_settings:
                # Use typed settings parameters for the specific strategy
                strategy_params = getattr(strategy_settings.parameters, strategy_type, {})
                # Start with strategy-specific parameters
                combined_config = {k: v for k, v in strategy_params.__dict__.items() if not k.startswith('_')}
                # Add general strategy settings
                combined_config.update({
                    'risk_per_trade': strategy_settings.risk_per_trade,
                    'max_positions': strategy_settings.max_positions
                })
                # Merge with provided legacy config (legacy takes precedence)
                if config:
                    combined_config.update(config)
                config = combined_config
            elif config is None:
                config = {}
        else:
            # Typed settings not available, just use the provided config
            config = config or {}
        
        # Create base strategy based on type
        strategy = None
        if strategy_type.lower() == "momentum":
            strategy = MomentumStrategy("Momentum Strategy", parameters=config)
        elif strategy_type.lower() == "mean_reversion":
            strategy = MeanReversionStrategy("Mean Reversion Strategy", config)
        elif strategy_type.lower() == "trend_following":
            strategy = TrendFollowingStrategy("Trend Following Strategy", config)
        elif strategy_type.lower() == "volatility_breakout":
            strategy = VolatilityBreakoutStrategy("Volatility Breakout Strategy", config)
        else:
            logger.warning(f"Unknown strategy type: {strategy_type}. Using momentum strategy.")
            strategy = MomentumStrategy("Momentum Strategy", parameters=config)
        
        # Wrap with notification capabilities if enabled
        if enable_notifications and NOTIFICATION_WRAPPER_AVAILABLE:
            # Check for notification settings from typed settings
            telegram_token = None
            telegram_chat_id = None
            
            if TYPED_SETTINGS_AVAILABLE and 'notification_settings' in locals() and notification_settings:
                # Use notification settings from typed config
                telegram_token = notification_settings.telegram_token
                telegram_chat_id = notification_settings.telegram_chat_id
                logger.info("Using telegram notification settings from typed config")
            
            # Fall back to environment variables or config dict
            telegram_token = telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("telegram_token")
            telegram_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID") or config.get("telegram_chat_id")
            
            if telegram_token and telegram_chat_id:
                # Wrap the strategy
                wrapped_strategy = wrap_strategy_with_notifications(strategy, telegram_token, telegram_chat_id)
                logger.info(f"Strategy {strategy_type} wrapped with notification capabilities")
                return wrapped_strategy
            else:
                logger.warning("Notification wrapper enabled but telegram credentials missing")
                return strategy
        
        return strategy
    
    @staticmethod
    def available_strategies():
        """Get names of available strategies"""
        return [
            "momentum",
            "mean_reversion",
            "trend_following",
            "volatility_breakout"
        ] 