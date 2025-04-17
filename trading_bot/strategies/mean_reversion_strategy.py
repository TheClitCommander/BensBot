#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mean Reversion Strategy - Exploits the tendency of asset prices to revert to their
long-term mean. Buys oversold assets and sells overbought assets.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MeanReversionStrategy:
    """
    Mean Reversion strategy that exploits the tendency of asset prices to revert to their mean.
    
    This strategy identifies assets that have deviated significantly from their historical average
    and takes positions with the expectation that prices will revert back to that average.
    
    Features:
    - Multiple lookback periods for calculating averages
    - Z-score based signal generation
    - Configurable entry and exit thresholds
    - Volatility-adjusted position sizing
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        entry_z_score: float = 2.0,
        exit_z_score: float = 0.5,
        holding_period: int = 5,
        use_volatility_filter: bool = True,
        volatility_lookback: int = 50,
        name: str = "mean_reversion"
    ):
        """
        Initialize the mean reversion strategy.
        
        Args:
            lookback_period: Period for calculating mean and standard deviation
            entry_z_score: Z-score threshold for trade entry
            exit_z_score: Z-score threshold for trade exit
            holding_period: Maximum holding period for trades
            use_volatility_filter: Whether to filter based on volatility
            volatility_lookback: Period for volatility calculation
            name: Strategy name
        """
        self.lookback_period = lookback_period
        self.entry_z_score = entry_z_score
        self.exit_z_score = exit_z_score
        self.holding_period = holding_period
        self.use_volatility_filter = use_volatility_filter
        self.volatility_lookback = volatility_lookback
        self.name = name
        
        # Performance tracking
        self.signals = {}
        self.performance = {}
        
        logger.info(f"Initialized {self.name} strategy with lookback period: {lookback_period}")
    
    def calculate_zscore(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate z-scores for the given price data.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            
        Returns:
            DataFrame of z-scores
        """
        # Calculate returns
        returns = prices.pct_change()
        
        # Calculate rolling mean and standard deviation
        rolling_mean = returns.rolling(window=self.lookback_period).mean()
        rolling_std = returns.rolling(window=self.lookback_period).std()
        
        # Calculate z-scores (how many standard deviations from the mean)
        z_scores = (returns - rolling_mean) / rolling_std
        
        # Replace inf/NaN values with 0
        z_scores = z_scores.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        return z_scores
    
    def generate_signals(
        self, 
        prices: pd.DataFrame, 
        market_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Generate trade signals based on mean reversion indicators.
        
        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            market_data: Additional market data (optional)
            
        Returns:
            DataFrame of trade signals (1=buy, -1=sell, 0=neutral)
        """
        # Check if we have enough data
        if len(prices) < self.lookback_period:
            logger.warning(f"Insufficient data for {self.name} strategy, need at least {self.lookback_period} bars")
            return pd.DataFrame(0, index=prices.index, columns=prices.columns)
        
        # Calculate z-scores
        z_scores = self.calculate_zscore(prices)
        
        # Initialize signals DataFrame
        signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
        
        # Long signal: z-score < -entry_z_score (price has moved down too far)
        signals[z_scores < -self.entry_z_score] = 1
        
        # Short signal: z-score > entry_z_score (price has moved up too far)
        signals[z_scores > self.entry_z_score] = -1
        
        # Exit long positions when z-score > -exit_z_score
        exit_long = (signals.shift(1) == 1) & (z_scores > -self.exit_z_score)
        signals[exit_long] = 0
        
        # Exit short positions when z-score < exit_z_score
        exit_short = (signals.shift(1) == -1) & (z_scores < self.exit_z_score)
        signals[exit_short] = 0
        
        # Apply volatility filter if enabled
        if self.use_volatility_filter:
            # Calculate historical volatility
            returns = prices.pct_change()
            current_vol = returns.rolling(window=self.volatility_lookback).std() * np.sqrt(252)
            
            # Calculate long-term volatility as baseline
            long_term_vol = returns.std() * np.sqrt(252)
            
            # Calculate volatility ratio
            vol_ratio = current_vol / long_term_vol.mean() if long_term_vol.mean() > 0 else current_vol
            
            # Filter out signals when volatility is too high (>1.5x baseline)
            high_vol_mask = vol_ratio > 1.5
            signals[high_vol_mask] = 0
        
        # Implement holding period limit (exit after holding_period bars)
        # This would be more complex in a real implementation
        
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
        
        # Test combinations of parameters
        lookback_options = [10, 20, 40]
        entry_z_options = [1.5, 2.0, 2.5]
        exit_z_options = [0.5, 1.0, 1.5]
        
        # Use last 1 year of data for optimization
        test_prices = prices.iloc[-252:]
        
        for lookback in lookback_options:
            for entry_z in entry_z_options:
                for exit_z in exit_z_options:
                    # Skip invalid combinations
                    if exit_z >= entry_z:
                        continue
                    
                    # Create test strategy with these parameters
                    test_strategy = MeanReversionStrategy(
                        lookback_period=lookback,
                        entry_z_score=entry_z,
                        exit_z_score=exit_z
                    )
                    
                    # Generate signals
                    signals = test_strategy.generate_signals(test_prices)
                    
                    # Simulate returns
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
                            "lookback_period": lookback,
                            "entry_z_score": entry_z,
                            "exit_z_score": exit_z,
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
            "bull": 0.6,     # Poor in strong bull markets
            "bear": 1.0,     # Average in bear markets
            "sideways": 1.8, # Excellent in sideways markets
            "high_vol": 1.5, # Good in high volatility (but risky)
            "low_vol": 1.3,  # Good in low volatility
            "crisis": 0.3,   # Poor in crisis (excessive volatility)
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
            "type": "mean_reversion",
            "lookback_period": self.lookback_period,
            "entry_z_score": self.entry_z_score,
            "exit_z_score": self.exit_z_score,
            "holding_period": self.holding_period,
            "use_volatility_filter": self.use_volatility_filter,
            "performance": self.performance,
            "signals": self.signals
        } 