#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Strategy - Captures continued price movement by buying assets that have
shown strong recent performance and selling those that have underperformed.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MomentumStrategy:
    """
    Momentum trading strategy that seeks to profit from the continuation of existing price trends.
    It captures continued price movement by buying assets that have shown strong recent performance 
    and selling those that have underperformed.
    
    Features:
    - Flexible lookback periods for momentum calculation
    - Adjustable signal thresholds
    - Cross-sectional ranking for relative strength
    - Volatility adjustment to normalize signals
    """
    
    def __init__(
        self,
        lookback_periods: List[int] = [20, 60, 120],
        signal_threshold: float = 0.0,
        volatility_lookback: int = 20,
        volatility_adjust: bool = True,
        cross_sectional: bool = True,
        name: str = "momentum"
    ):
        """
        Initialize the momentum strategy.
        
        Args:
            lookback_periods: List of periods to calculate momentum over
            signal_threshold: Threshold for momentum signal to generate a trade
            volatility_lookback: Period for volatility calculation
            volatility_adjust: Whether to adjust momentum by volatility
            cross_sectional: Whether to use cross-sectional momentum (relative ranking)
            name: Strategy name
        """
        self.lookback_periods = lookback_periods
        self.signal_threshold = signal_threshold
        self.volatility_lookback = volatility_lookback
        self.volatility_adjust = volatility_adjust
        self.cross_sectional = cross_sectional
        self.name = name
        
        # Performance tracking
        self.signals = {}
        self.performance = {}
        
        logger.info(f"Initialized {self.name} strategy with lookback periods {self.lookback_periods}")
    
    def calculate_momentum(
        self, 
        prices: pd.DataFrame, 
        lookback: int = None
    ) -> pd.DataFrame:
        """
        Calculate momentum indicators for given price data.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            lookback: Lookback period (uses all periods in self.lookback_periods if None)
            
        Returns:
            DataFrame of momentum indicators
        """
        if lookback is None:
            # Calculate for all lookback periods and average
            momentum_indicators = []
            
            for period in self.lookback_periods:
                momentum = prices.pct_change(period)
                momentum_indicators.append(momentum)
            
            # Average across all lookback periods
            momentum = pd.concat(momentum_indicators).groupby(level=0).mean()
        else:
            # Calculate for specific lookback period
            momentum = prices.pct_change(lookback)
        
        if self.volatility_adjust and momentum.shape[0] > self.volatility_lookback:
            # Adjust momentum by volatility
            volatility = prices.pct_change().rolling(self.volatility_lookback).std() * np.sqrt(252)
            # Add small constant to avoid division by zero
            momentum = momentum / (volatility + 1e-8)
        
        if self.cross_sectional:
            # Cross-sectional momentum (rank assets relative to each other)
            momentum = momentum.rank(axis=1, pct=True) - 0.5
        
        return momentum
    
    def generate_signals(
        self, 
        prices: pd.DataFrame, 
        market_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Generate trade signals based on momentum indicators.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            market_data: Additional market data (optional)
            
        Returns:
            DataFrame of trade signals (1=buy, -1=sell, 0=neutral)
        """
        # Calculate momentum indicators
        momentum = self.calculate_momentum(prices)
        
        # Generate signals based on momentum and threshold
        signals = pd.DataFrame(0, index=momentum.index, columns=momentum.columns)
        
        # Long positions for momentum > threshold
        signals[momentum > self.signal_threshold] = 1
        
        # Short positions for momentum < -threshold (if threshold is positive)
        if self.signal_threshold > 0:
            signals[momentum < -self.signal_threshold] = -1
        else:
            # If threshold is 0 or negative, short the bottom half
            signals[momentum < 0] = -1
        
        # Store signals for performance tracking
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
        
        # Test combinations of lookback periods and thresholds
        lookback_options = [[20, 60, 120], [5, 20, 60], [10, 30, 90]]
        threshold_options = [0.0, 0.1, 0.2]
        volatility_adjust_options = [True, False]
        
        # Use last 1 year of data for optimization
        test_prices = prices.iloc[-252:]
        
        for lookback in lookback_options:
            for threshold in threshold_options:
                for vol_adjust in volatility_adjust_options:
                    # Create test strategy with these parameters
                    test_strategy = MomentumStrategy(
                        lookback_periods=lookback,
                        signal_threshold=threshold,
                        volatility_adjust=vol_adjust
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
                            "lookback_periods": lookback,
                            "signal_threshold": threshold,
                            "volatility_adjust": vol_adjust,
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
            "bull": 1.8,     # Excellent in bullish markets
            "bear": 0.5,     # Poor in bearish markets
            "sideways": 0.4, # Poor in sideways markets
            "high_vol": 0.6, # Below average in high volatility
            "low_vol": 1.2,  # Good in low volatility
            "crisis": 0.2,   # Very poor in crisis
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
            "type": "momentum",
            "lookback_periods": self.lookback_periods,
            "signal_threshold": self.signal_threshold,
            "volatility_adjust": self.volatility_adjust,
            "cross_sectional": self.cross_sectional,
            "performance": self.performance,
            "signals": self.signals
        } 