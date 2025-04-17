#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trend-Following Strategy - Identifies and follows the prevailing trend in the market
by using moving averages, trend lines, and other technical indicators.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrendFollowingStrategy:
    """
    Trend-Following strategy that identifies and follows the prevailing trend in the market.
    
    This strategy uses a combination of moving averages and other technical indicators
    to determine the direction and strength of the trend, and generate trading signals
    accordingly.
    
    Features:
    - Multiple moving average combinations
    - Trend strength measurement
    - Volatility-adjusted position sizing
    - Customizable entry and exit conditions
    """
    
    def __init__(
        self,
        short_ma_period: int = 20,
        long_ma_period: int = 50,
        signal_ma_period: int = 10,
        trend_strength_threshold: float = 0.05,
        use_atr_filter: bool = True,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        name: str = "trend_following"
    ):
        """
        Initialize the trend following strategy.
        
        Args:
            short_ma_period: Period for short moving average
            long_ma_period: Period for long moving average
            signal_ma_period: Period for signal moving average
            trend_strength_threshold: Minimum trend strength to generate signals
            use_atr_filter: Whether to use ATR for filtering
            atr_period: Period for ATR calculation
            atr_multiplier: Multiplier for ATR
            name: Strategy name
        """
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.signal_ma_period = signal_ma_period
        self.trend_strength_threshold = trend_strength_threshold
        self.use_atr_filter = use_atr_filter
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.name = name
        
        # Performance tracking
        self.signals = {}
        self.performance = {}
        
        logger.info(f"Initialized {self.name} strategy with MA periods: {short_ma_period}/{long_ma_period}")
    
    def calculate_indicators(self, prices: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Calculate trend following indicators for the given price data.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            
        Returns:
            Dict of indicator DataFrames
        """
        indicators = {}
        
        # Calculate moving averages
        indicators['short_ma'] = prices.rolling(self.short_ma_period).mean()
        indicators['long_ma'] = prices.rolling(self.long_ma_period).mean()
        
        # Calculate trend direction (short_ma - long_ma)
        indicators['trend_direction'] = indicators['short_ma'] - indicators['long_ma']
        
        # Calculate trend strength (as percentage of price)
        indicators['trend_strength'] = indicators['trend_direction'] / prices
        
        # Calculate signal line (smoothed trend direction)
        indicators['signal_line'] = indicators['trend_direction'].rolling(self.signal_ma_period).mean()
        
        # Calculate ATR if needed
        if self.use_atr_filter:
            # Calculate daily ranges
            high_low_range = prices.rolling(2).max() - prices.rolling(2).min()
            
            # Simple approximation of ATR using high-low range
            indicators['atr'] = high_low_range.rolling(self.atr_period).mean()
            
            # ATR as percentage of price
            indicators['atr_pct'] = indicators['atr'] / prices
        
        return indicators
    
    def generate_signals(
        self, 
        prices: pd.DataFrame, 
        market_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Generate trade signals based on trend following indicators.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            market_data: Additional market data (optional)
            
        Returns:
            DataFrame of trade signals (1=buy, -1=sell, 0=neutral)
        """
        # Initialize signals DataFrame
        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        
        # Calculate indicators
        indicators = self.calculate_indicators(prices)
        
        # Generate signals based on trend direction and strength
        trend_direction = indicators['trend_direction']
        trend_strength = indicators['trend_strength']
        signal_line = indicators['signal_line']
        
        # Long signal: trend direction positive and strong enough
        long_condition = (
            (trend_direction > 0) & 
            (trend_strength > self.trend_strength_threshold) &
            (trend_direction > signal_line)
        )
        signals[long_condition] = 1
        
        # Short signal: trend direction negative and strong enough
        short_condition = (
            (trend_direction < 0) & 
            (trend_strength < -self.trend_strength_threshold) &
            (trend_direction < signal_line)
        )
        signals[short_condition] = -1
        
        # Apply ATR filter if enabled
        if self.use_atr_filter and 'atr_pct' in indicators:
            atr_pct = indicators['atr_pct']
            
            # Only take trades if ATR is reasonable (not too high or too low)
            min_atr_threshold = 0.005  # 0.5% daily range minimum
            max_atr_threshold = 0.03   # 3% daily range maximum
            
            # Filter out signals where volatility is too low or too high
            invalid_atr = (atr_pct < min_atr_threshold) | (atr_pct > max_atr_threshold)
            signals[invalid_atr] = 0
        
        # Store last signals for reference
        self.signals = signals.iloc[-1].to_dict()
        
        return signals
    
    def optimize_parameters(
        self, 
        prices: pd.DataFrame, 
        market_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters based on historical performance.
        
        Args:
            prices: DataFrame of asset prices
            market_data: Additional market data (optional)
            
        Returns:
            Dict of optimized parameters
        """
        # Simple optimization example - test a few parameter combinations
        best_sharpe = -np.inf
        best_params = {}
        
        # Test combinations of moving average periods
        short_ma_options = [10, 20, 30]
        long_ma_options = [50, 100, 200]
        threshold_options = [0.02, 0.05, 0.1]
        
        # Use last 1 year of data for optimization
        test_prices = prices.iloc[-252:]
        
        for short_ma in short_ma_options:
            for long_ma in long_ma_options:
                for threshold in threshold_options:
                    # Skip invalid combinations
                    if short_ma >= long_ma:
                        continue
                    
                    # Create test strategy with these parameters
                    test_strategy = TrendFollowingStrategy(
                        short_ma_period=short_ma,
                        long_ma_period=long_ma,
                        trend_strength_threshold=threshold
                    )
                    
                    # Generate signals
                    signals = test_strategy.generate_signals(test_prices)
                    
                    # Simulate returns (simplified)
                    shifted_signals = signals.shift(1).fillna(0)
                    returns = test_prices.pct_change() * shifted_signals
                    
                    # Calculate performance
                    portfolio_returns = returns.mean(axis=1)
                    
                    annualized_return = portfolio_returns.mean() * 252
                    volatility = portfolio_returns.std() * np.sqrt(252)
                    sharpe = annualized_return / volatility if volatility > 0 else 0
                    
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = {
                            "short_ma_period": short_ma,
                            "long_ma_period": long_ma,
                            "trend_strength_threshold": threshold,
                            "sharpe_ratio": sharpe,
                            "annualized_return": annualized_return,
                            "volatility": volatility
                        }
        
        logger.info(f"Optimized {self.name} strategy parameters: {best_params}")
        return best_params
    
    def update_performance(
        self, 
        prices: pd.DataFrame, 
        signals: pd.DataFrame = None
    ) -> Dict[str, float]:
        """
        Update strategy performance metrics.
        
        Args:
            prices: DataFrame of asset prices
            signals: Signals used (if None, generates new signals)
            
        Returns:
            Dict of performance metrics
        """
        if signals is None:
            signals = self.generate_signals(prices)
        
        # Simulate returns (signals are applied to next day's returns)
        shifted_signals = signals.shift(1).fillna(0)
        asset_returns = prices.pct_change()
        strategy_returns = asset_returns * shifted_signals
        
        # Calculate portfolio returns (equal weight across assets with signals)
        portfolio_returns = strategy_returns.mean(axis=1)
        
        # Calculate performance metrics
        total_return = (1 + portfolio_returns).prod() - 1
        annualized_return = portfolio_returns.mean() * 252
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Calculate drawdown
        cum_returns = (1 + portfolio_returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns / running_max) - 1
        max_drawdown = drawdown.min()
        
        # Calculate win rate
        win_rate = (portfolio_returns > 0).mean()
        
        # Store performance metrics
        self.performance = {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "last_updated": datetime.now().isoformat()
        }
        
        return self.performance
    
    def regime_compatibility(self, regime: str) -> float:
        """
        Get compatibility score for this strategy in the given market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Compatibility score (0-2, higher is better)
        """
        # Regime compatibility scores
        compatibility = {
            "bull": 1.5,     # Very good in bullish markets
            "bear": 1.2,     # Good in bearish markets
            "sideways": 0.5, # Poor in sideways markets
            "high_vol": 0.7, # Below average in high volatility
            "low_vol": 1.0,  # Average in low volatility
            "crisis": 1.0,   # Average in crisis (can adapt)
            "unknown": 1.0   # Neutral in unknown regime
        }
        
        return compatibility.get(regime.lower(), 1.0)
    
    def get_current_signals(self) -> Dict[str, int]:
        """
        Get the most recent signals.
        
        Returns:
            Dict of assets and their signals
        """
        return self.signals
    
    def get_performance(self) -> Dict[str, float]:
        """
        Get current performance metrics.
        
        Returns:
            Dict of performance metrics
        """
        return self.performance
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert strategy to dict representation.
        
        Returns:
            Dict representation of strategy
        """
        return {
            "name": self.name,
            "type": "trend_following",
            "short_ma_period": self.short_ma_period,
            "long_ma_period": self.long_ma_period,
            "signal_ma_period": self.signal_ma_period,
            "trend_strength_threshold": self.trend_strength_threshold,
            "use_atr_filter": self.use_atr_filter,
            "performance": self.performance,
            "signals": self.signals
        } 