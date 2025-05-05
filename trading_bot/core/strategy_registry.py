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
    def list_strategies_by_asset(cls, asset_type: str):
        """Return strategies for a specific asset type (stock, crypto, forex, options)."""
        with cls._lock:
            if asset_type.lower() == "stock":
                return [s for s in cls._registry.keys() if s.startswith("stock_")]
            elif asset_type.lower() == "crypto":
                return [s for s in cls._registry.keys() if s.startswith("crypto_")]
            elif asset_type.lower() == "forex":
                return [s for s in cls._registry.keys() if s.startswith("forex_")]
            elif asset_type.lower() == "options":
                return [s for s in cls._registry.keys() if s.startswith("options_")]
            else:
                return cls.list_strategies()

    @classmethod
    def create(cls, name: str, *args, **kwargs):
        strategy_cls = cls.get(name)
        return strategy_cls(*args, **kwargs)

# Enhanced Strategy Registry with comprehensive multi-asset strategy support
# Import base strategies
from trading_bot.strategy.implementations.standard_strategies import (
    MomentumStrategy, TrendFollowingStrategy, MeanReversionStrategy
)
from trading_bot.strategy.rl_strategy import MetaLearningStrategy
from trading_bot.strategy.ml_strategy import MLStrategy

# Import stock-specific strategies
from trading_bot.strategies.stocks.momentum import (
    StockMomentumStrategy, RelativeStrengthStrategy, PriceVolumeStrategy
)
from trading_bot.strategies.stocks.mean_reversion import (
    StockMeanReversionStrategy, RSIReversionStrategy, BollingerBandStrategy
)
from trading_bot.strategies.stocks.trend import (
    MovingAverageCrossStrategy, MAACDStrategy, TrendChannelStrategy
)
from trading_bot.strategies.stocks.breakout import (
    VolatilityBreakoutStrategy, PriceBreakoutStrategy, VolumeBreakoutStrategy
)

# Import crypto-specific strategies
from trading_bot.strategies.crypto.momentum import (
    CryptoMomentumStrategy, CryptoRSIStrategy 
)
from trading_bot.strategies.crypto.mean_reversion import (
    CryptoMeanReversionStrategy, CryptoRangeTradingStrategy
)
from trading_bot.strategies.crypto.onchain import (
    OnChainAnalysisStrategy, TokenFlowStrategy
)

# Import forex-specific strategies
from trading_bot.strategies.forex.trend import (
    ForexTrendStrategy, ForexMAStrategy
)
from trading_bot.strategies.forex.range import (
    ForexRangeStrategy, ForexSupportResistanceStrategy
)
from trading_bot.strategies.forex.carry import (
    ForexCarryTradeStrategy, InterestRateDifferentialStrategy
)

# Import options-specific strategies
from trading_bot.strategies.options.income import (
    CoveredCallStrategy, CashSecuredPutStrategy, WheelStrategy
)
from trading_bot.strategies.options.volatility import (
    VolatilityArbitrageStrategy, VIXStrategy, ImpliedVolatilityStrategy
)
from trading_bot.strategies.options.spreads import (
    BullCallSpreadStrategy, BearPutSpreadStrategy, IronCondorStrategy
)
from trading_bot.strategies.options.strangles import (
    LongStrangleStrategy, ShortStrangleStrategy
)

# Register base strategies
StrategyRegistry.register("momentum", MomentumStrategy)
StrategyRegistry.register("trend_following", TrendFollowingStrategy)
StrategyRegistry.register("mean_reversion", MeanReversionStrategy)
StrategyRegistry.register("meta_learning", MetaLearningStrategy)
StrategyRegistry.register("ml_strategy", MLStrategy)

# Register stock-specific strategies
StrategyRegistry.register("stock_momentum", StockMomentumStrategy)
StrategyRegistry.register("stock_relative_strength", RelativeStrengthStrategy)
StrategyRegistry.register("stock_price_volume", PriceVolumeStrategy)
StrategyRegistry.register("stock_mean_reversion", StockMeanReversionStrategy)
StrategyRegistry.register("stock_rsi_reversion", RSIReversionStrategy)
StrategyRegistry.register("stock_bollinger", BollingerBandStrategy)
StrategyRegistry.register("stock_ma_cross", MovingAverageCrossStrategy)
StrategyRegistry.register("stock_macd", MAACDStrategy)
StrategyRegistry.register("stock_trend_channel", TrendChannelStrategy)
StrategyRegistry.register("stock_volatility_breakout", VolatilityBreakoutStrategy)
StrategyRegistry.register("stock_price_breakout", PriceBreakoutStrategy)
StrategyRegistry.register("stock_volume_breakout", VolumeBreakoutStrategy)

# Register crypto-specific strategies
StrategyRegistry.register("crypto_momentum", CryptoMomentumStrategy)
StrategyRegistry.register("crypto_rsi", CryptoRSIStrategy)
StrategyRegistry.register("crypto_mean_reversion", CryptoMeanReversionStrategy)
StrategyRegistry.register("crypto_range", CryptoRangeTradingStrategy)
StrategyRegistry.register("crypto_onchain", OnChainAnalysisStrategy)
StrategyRegistry.register("crypto_token_flow", TokenFlowStrategy)

# Register forex-specific strategies
StrategyRegistry.register("forex_trend", ForexTrendStrategy)
StrategyRegistry.register("forex_ma", ForexMAStrategy)
StrategyRegistry.register("forex_range", ForexRangeStrategy)
StrategyRegistry.register("forex_support_resistance", ForexSupportResistanceStrategy)
StrategyRegistry.register("forex_carry", ForexCarryTradeStrategy)
StrategyRegistry.register("forex_interest_rate", InterestRateDifferentialStrategy)

# Register options-specific strategies
StrategyRegistry.register("options_covered_call", CoveredCallStrategy)
StrategyRegistry.register("options_cash_secured_put", CashSecuredPutStrategy)
StrategyRegistry.register("options_wheel", WheelStrategy)
StrategyRegistry.register("options_volatility_arbitrage", VolatilityArbitrageStrategy)
StrategyRegistry.register("options_vix", VIXStrategy)
StrategyRegistry.register("options_implied_volatility", ImpliedVolatilityStrategy)
StrategyRegistry.register("options_bull_call_spread", BullCallSpreadStrategy)
StrategyRegistry.register("options_bear_put_spread", BearPutSpreadStrategy)
StrategyRegistry.register("options_iron_condor", IronCondorStrategy)
StrategyRegistry.register("options_long_strangle", LongStrangleStrategy)
StrategyRegistry.register("options_short_strangle", ShortStrangleStrategy)

# Asset type mapping for asset detection
AssetTypeStrategies = {
    "stock": [strategy for strategy in StrategyRegistry._registry.keys() if strategy.startswith("stock_")],
    "crypto": [strategy for strategy in StrategyRegistry._registry.keys() if strategy.startswith("crypto_")],
    "forex": [strategy for strategy in StrategyRegistry._registry.keys() if strategy.startswith("forex_")],
    "options": [strategy for strategy in StrategyRegistry._registry.keys() if strategy.startswith("options_")],
}
