#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for data generation and handling in the trading bot system.
This centralizes synthetic data generation and common data manipulation functions.
"""

import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

from trading_bot.common.market_types import MarketRegime, MarketData


class SyntheticDataGenerator:
    """
    Generates synthetic market data for testing and demonstration purposes.
    This centralizes all synthetic data generation logic used across the system.
    """
    
    def __init__(
        self, 
        symbols: List[str] = None,
        start_price: Union[float, Dict[str, float]] = 100.0,
        base_volatility: Union[float, Dict[str, float]] = 0.01,
        seed: Optional[int] = None
    ):
        """
        Initialize the synthetic data generator.
        
        Args:
            symbols: List of symbols to generate data for
            start_price: Starting price for each symbol (or dict mapping symbols to prices)
            base_volatility: Base volatility for each symbol (or dict mapping symbols to volatilities)
            seed: Random seed for reproducibility
        """
        self.symbols = symbols or ["SPY", "QQQ", "IWM"]
        
        # Set up random seed if provided
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize prices
        self.current_prices = {}
        for symbol in self.symbols:
            if isinstance(start_price, dict) and symbol in start_price:
                self.current_prices[symbol] = start_price[symbol]
            else:
                self.current_prices[symbol] = start_price
        
        # Initialize volatilities
        self.volatilities = {}
        for symbol in self.symbols:
            if isinstance(base_volatility, dict) and symbol in base_volatility:
                self.volatilities[symbol] = base_volatility[symbol]
            else:
                self.volatilities[symbol] = base_volatility
        
        # Initialize tracking variables
        self.current_step = 0
        self._regime_periods = []
        self.current_regime = MarketRegime.UNKNOWN
    
    def set_regime_periods(self, regime_periods: List[Tuple[int, int, MarketRegime]]) -> None:
        """
        Set regime periods for data generation.
        
        Args:
            regime_periods: List of (start_step, end_step, regime) tuples
        """
        self._regime_periods = regime_periods
        self._update_regime()
    
    def set_default_regime_periods(self, total_steps: int = 400) -> None:
        """
        Set default regime periods for demonstration.
        
        Args:
            total_steps: Total number of steps to simulate
        """
        period_length = total_steps // 8
        
        self._regime_periods = [
            (0, period_length, MarketRegime.BULL),                    # Bull market start
            (period_length, period_length * 2, MarketRegime.HIGH_VOL), # High volatility
            (period_length * 2, period_length * 3, MarketRegime.BEAR),  # Bear market
            (period_length * 3, period_length * 4, MarketRegime.SIDEWAYS), # Sideways
            (period_length * 4, period_length * 5, MarketRegime.CRISIS), # Crisis
            (period_length * 5, period_length * 6, MarketRegime.SIDEWAYS), # Recovery sideways
            (period_length * 6, period_length * 7, MarketRegime.BULL), # Bull recovery
            (period_length * 7, total_steps, MarketRegime.LOW_VOL)     # Low volatility end
        ]
        
        self._update_regime()
    
    def _update_regime(self) -> None:
        """Update the current regime based on the current step."""
        for start, end, regime in self._regime_periods:
            if start <= self.current_step < end:
                self.current_regime = regime
                return
        
        # Default to UNKNOWN if no matching period
        self.current_regime = MarketRegime.UNKNOWN
    
    def get_regime_parameters(self, regime: MarketRegime) -> Tuple[float, float]:
        """
        Get drift and volatility parameters for a given market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Tuple of (drift, volatility multiplier)
        """
        if regime == MarketRegime.BULL:
            return 0.0005, 0.8  # Positive drift, slightly reduced volatility
        elif regime == MarketRegime.BEAR:
            return -0.0004, 1.2  # Negative drift, increased volatility
        elif regime == MarketRegime.SIDEWAYS:
            return 0.0001, 0.5  # Very slight drift, lower volatility
        elif regime == MarketRegime.HIGH_VOL:
            return 0.0, 2.0  # No drift, high volatility
        elif regime == MarketRegime.LOW_VOL:
            return 0.0002, 0.3  # Slight positive drift, low volatility
        elif regime == MarketRegime.CRISIS:
            return -0.002, 3.0  # Strong negative drift, extreme volatility
        else:  # UNKNOWN
            return 0.0001, 1.0  # Default parameters
    
    def generate_market_data(self, symbol: str) -> MarketData:
        """
        Generate synthetic market data for a single symbol.
        
        Args:
            symbol: Symbol to generate data for
            
        Returns:
            MarketData object with generated data
        """
        if symbol not in self.symbols:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        # Get base volatility for this symbol
        base_vol = self.volatilities.get(symbol, 0.01)
        
        # Get drift and volatility for current regime
        drift, vol_multiplier = self.get_regime_parameters(self.current_regime)
        
        # Apply volatility multiplier
        vol = base_vol * vol_multiplier
        
        # Generate price movement
        price_change = np.random.normal(drift, vol)
        new_price = self.current_prices[symbol] * (1 + price_change)
        
        # Update current price
        self.current_prices[symbol] = new_price
        
        # Generate volume (log-normal distribution)
        volume = np.random.lognormal(9, 0.5)  # Mean around 8000
        
        # Create market data
        return MarketData(
            symbol=symbol,
            price=new_price,
            timestamp=datetime.now(),
            volume=volume
        )
    
    def generate_ohlc_data(self, symbol: str) -> Dict[str, float]:
        """
        Generate synthetic OHLC data for a single symbol.
        
        Args:
            symbol: Symbol to generate data for
            
        Returns:
            Dictionary with open, high, low, close, and volume
        """
        if symbol not in self.symbols:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        # Get base price and volatility
        base_price = self.current_prices[symbol]
        base_vol = self.volatilities.get(symbol, 0.01)
        
        # Get drift and volatility for current regime
        drift, vol_multiplier = self.get_regime_parameters(self.current_regime)
        
        # Apply volatility multiplier
        vol = base_vol * vol_multiplier
        
        # Generate open price (slight adjustment from current price)
        open_price = base_price * (1 + np.random.normal(0, vol * 0.3))
        
        # Generate close price (with drift)
        close_price = open_price * (1 + np.random.normal(drift, vol))
        
        # Generate high and low prices
        price_range = abs(close_price - open_price) * (1 + np.random.lognormal(-1, 1))
        if close_price > open_price:
            high_price = close_price + np.random.uniform(0, price_range * 0.5)
            low_price = open_price - np.random.uniform(0, price_range * 0.5)
        else:
            high_price = open_price + np.random.uniform(0, price_range * 0.5)
            low_price = close_price - np.random.uniform(0, price_range * 0.5)
        
        # Ensure low <= open, close <= high
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Generate volume
        volume = np.random.lognormal(9, 0.5)
        
        # Update current price
        self.current_prices[symbol] = close_price
        
        # Increment step counter and update regime
        self.current_step += 1
        self._update_regime()
        
        # Return OHLC data
        return {
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_price_dataframe(
        self, 
        periods: int = 100,
        frequency: str = 'D',
        start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with synthetic price data.
        
        Args:
            periods: Number of periods to generate
            frequency: Frequency of data ('D' for daily, etc.)
            start_date: Starting date (defaults to 100 days ago)
            
        Returns:
            DataFrame with synthetic price data
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=periods)
        
        # Create date range
        dates = pd.date_range(start=start_date, periods=periods, freq=frequency)
        
        # Initialize prices DataFrame
        prices_dict = {symbol: [] for symbol in self.symbols}
        
        # Reset generator state
        self.current_step = 0
        for symbol in self.symbols:
            self.current_prices[symbol] = 100.0  # Reset prices
        
        # Generate price data for each date and symbol
        for i in range(periods):
            self.current_step = i
            self._update_regime()
            
            for symbol in self.symbols:
                # Get regime parameters
                drift, vol_multiplier = self.get_regime_parameters(self.current_regime)
                vol = self.volatilities.get(symbol, 0.01) * vol_multiplier
                
                # Generate price change
                if i == 0:
                    # Initial price
                    price = 100.0
                else:
                    # Price change based on regime
                    price_change = np.random.normal(drift, vol)
                    price = prices_dict[symbol][-1] * (1 + price_change)
                
                prices_dict[symbol].append(price)
        
        # Create DataFrame
        df = pd.DataFrame(index=dates)
        for symbol in self.symbols:
            df[symbol] = prices_dict[symbol]
        
        return df
    
    def get_current_regime(self) -> MarketRegime:
        """Get the current market regime."""
        return self.current_regime


def generate_sample_portfolio_data() -> Dict[str, float]:
    """Generate sample portfolio metrics for demonstration."""
    return {
        "total_value": round(random.uniform(90000, 120000), 2),
        "cash": round(random.uniform(20000, 50000), 2),
        "pnl_total": round(random.uniform(-10000, 20000), 2),
        "pnl_pct": round(random.uniform(-10, 20), 2),
        "pnl_daily": round(random.uniform(-2000, 3000), 2),
        "pnl_daily_pct": round(random.uniform(-2, 3), 2),
        "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
        "drawdown": round(random.uniform(2, 15), 2),
        "win_rate": round(random.uniform(40, 75), 1)
    }

def generate_sample_risk_data() -> Dict[str, Any]:
    """Generate sample risk metrics for demonstration."""
    return {
        "portfolio_beta": round(random.uniform(0.8, 1.4), 2),
        "var_daily": round(random.uniform(1000, 5000), 0),
        "portfolio_volatility": round(random.uniform(8, 18), 1),
        "market_exposure": round(random.uniform(60, 95), 0),
        "alerts": [
            {
                "level": "medium" if random.random() > 0.3 else "high",
                "message": "Portfolio concentration in Technology sector (45%) exceeds target threshold (35%)"
            },
            {
                "level": "low" if random.random() > 0.7 else "medium",
                "message": "Portfolio beta (1.15) is above market neutral target (1.0)"
            }
        ] if random.random() > 0.3 else []
    }

def generate_sample_strategy_performance() -> Dict[str, Any]:
    """Generate sample strategy performance data for demonstration."""
    strategies = [
        {"name": "Momentum", "allocation": 30, "return": round(random.uniform(5, 15), 1), "sharpe": round(random.uniform(1.5, 2.5), 1), "win_rate": round(random.uniform(55, 75), 0)},
        {"name": "Mean Reversion", "allocation": 25, "return": round(random.uniform(3, 12), 1), "sharpe": round(random.uniform(1.2, 2.2), 1), "win_rate": round(random.uniform(50, 65), 0)},
        {"name": "Trend Following", "allocation": 20, "return": round(random.uniform(8, 20), 1), "sharpe": round(random.uniform(1.4, 2.4), 1), "win_rate": round(random.uniform(45, 60), 0)},
        {"name": "Volatility", "allocation": 15, "return": round(random.uniform(-5, 10), 1), "sharpe": round(random.uniform(0.4, 1.6), 1), "win_rate": round(random.uniform(40, 55), 0)},
        {"name": "Breakout", "allocation": 10, "return": round(random.uniform(5, 18), 1), "sharpe": round(random.uniform(1.2, 2.0), 1), "win_rate": round(random.uniform(50, 65), 0)}
    ]
    return {"strategies": strategies}

def generate_sample_positions() -> Dict[str, Any]:
    """Generate sample positions data for demonstration."""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ"]
    strategies = ["Momentum", "Mean Reversion", "Trend Following", "Volatility", "Breakout"]
    
    positions = []
    for i in range(min(len(symbols), random.randint(3, 8))):
        is_long = random.random() > 0.3
        entry_price = round(random.uniform(100, 500), 2)
        current_price = entry_price * (1 + random.uniform(-0.1, 0.2))
        pnl_pct = ((current_price / entry_price) - 1) * 100
        if not is_long:
            pnl_pct = -pnl_pct
            
        positions.append({
            "symbol": symbols[i],
            "strategy": random.choice(strategies),
            "type": "Long" if is_long else "Short",
            "entry_price": entry_price,
            "current_price": round(current_price, 2),
            "pnl_pct": round(pnl_pct, 2)
        })
    
    return {"positions": positions} 