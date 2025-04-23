# trading_bot/core/strategy_registry.py
"""
StrategyRegistry: Central registry for all trading strategies (including ML/AI).
Allows registration, retrieval, and extension of strategies by name.
Robust, extensible, and future-proof for all strategy logic.
"""

import threading
import logging
from typing import Dict, Type, Any

logger = logging.getLogger("StrategyRegistry")

class StrategyRegistry:
    _registry: Dict[str, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def register(cls, name: str, strategy_cls: Any):
        with cls._lock:
            if name in cls._registry:
                logger.warning(f"Strategy '{name}' is already registered. Overwriting.")
            cls._registry[name] = strategy_cls
            logger.info(f"Registered strategy: {name}")

    @classmethod
    def get(cls, name: str):
        with cls._lock:
            if name not in cls._registry:
                raise ValueError(f"Strategy '{name}' not registered.")
            return cls._registry[name]

    @classmethod
    def list_strategies(cls):
        with cls._lock:
            return list(cls._registry.keys())

    @classmethod
    def create(cls, name: str, *args, **kwargs):
        strategy_cls = cls.get(name)
        return strategy_cls(*args, **kwargs)

# Example: Registering existing strategies
from trading_bot.strategy.implementations.standard_strategies import (
    MomentumStrategy, TrendFollowingStrategy, MeanReversionStrategy
)
from trading_bot.strategy.rl_strategy import MetaLearningStrategy
from trading_bot.strategy.ml_strategy import MLStrategy
# Add more as needed

StrategyRegistry.register("momentum", MomentumStrategy)
StrategyRegistry.register("trend_following", TrendFollowingStrategy)
StrategyRegistry.register("mean_reversion", MeanReversionStrategy)
StrategyRegistry.register("meta_learning", MetaLearningStrategy)
StrategyRegistry.register("ml_strategy", MLStrategy)

# To add more strategies, just call StrategyRegistry.register("name", Class)
