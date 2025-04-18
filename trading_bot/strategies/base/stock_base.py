#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Base Strategy Module

This module provides the base class for stock trading strategies, with
stock-specific functionality built in.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

from trading_bot.strategies.strategy_template import StrategyOptimizable, Signal, SignalType, TimeFrame, MarketRegime

logger = logging.getLogger(__name__)

class StockBaseStrategy(StrategyOptimizable):
    """
    Base class for stock trading strategies.
    
    This class extends the StrategyOptimizable to add stock-specific
    functionality including:
    - Sector/industry context
    - Fundamental data handling
    - Stock-specific technical indicators
    - Volatility handling appropriate for equities
    - Market session awareness (pre-market, regular hours, after-hours)
    """
    
    # Default parameters specific to stock trading
    DEFAULT_STOCK_PARAMS = {
        # Market data parameters
        'use_premarket_data': False,
        'use_afterhours_data': False,
        'min_stock_price': 5.0,      # Minimum price filter
        'max_stock_price': 1000.0,   # Maximum price filter
        'min_avg_volume': 100000,    # Minimum average volume
        
        # Fundamental filters
        'use_fundamentals': False,   # Whether to use fundamental data
        'min_market_cap': 100000000, # Minimum market cap ($100M)
        'max_pe_ratio': 50,          # Maximum P/E ratio
        'min_pe_ratio': 0,           # Minimum P/E ratio
        
        # Sector/industry parameters
        'sector_filter': None,       # Specific sector to focus on
        'industry_filter': None,     # Specific industry to focus on
        'exclude_sectors': [],       # Sectors to exclude
        
        # Stock-specific technical parameters
        'use_volume_profile': False, # Whether to use volume profile analysis
        'gap_threshold': 0.02,       # Gap threshold (2%)
        'use_market_breadth': False, # Whether to use market breadth indicators
        
        # Stock-specific risk parameters
        'position_sizing_method': 'percent_risk', # Risk-based position sizing
        'max_position_size_percent': 0.05,        # Maximum position size (5%)
        'default_stop_percent': 0.05,             # Default stop loss (5%)
    }
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a stock trading strategy.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters (will be merged with DEFAULT_STOCK_PARAMS)
            metadata: Strategy metadata
        """
        # Start with default stock parameters
        stock_params = self.DEFAULT_STOCK_PARAMS.copy()
        
        # Override with provided parameters
        if parameters:
            stock_params.update(parameters)
        
        # Initialize the parent class
        super().__init__(name=name, parameters=stock_params, metadata=metadata)
        
        # Stock-specific member variables
        self.sector_performance = {}  # Track sector performance
        self.industry_performance = {}  # Track industry performance
        
        logger.info(f"Initialized stock strategy: {name}")
    
    def filter_universe(self, universe: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Filter the universe based on stock-specific criteria.
        
        Args:
            universe: Dictionary mapping symbols to DataFrames with stock data
            
        Returns:
            Filtered universe
        """
        filtered_universe = {}
        
        for symbol, data in universe.items():
            # Skip if no data
            if data.empty:
                continue
            
            # Get latest data
            latest = data.iloc[-1]
            
            # Apply price filters
            if self.parameters['min_stock_price'] > 0 and latest['close'] < self.parameters['min_stock_price']:
                continue
                
            if self.parameters['max_stock_price'] > 0 and latest['close'] > self.parameters['max_stock_price']:
                continue
            
            # Apply volume filter
            if 'volume' in data.columns and self.parameters['min_avg_volume'] > 0:
                avg_volume = data['volume'].mean()
                if avg_volume < self.parameters['min_avg_volume']:
                    continue
            
            # Apply sector filter if applicable
            if self.parameters['sector_filter'] and 'sector' in latest:
                if latest['sector'] != self.parameters['sector_filter']:
                    continue
            
            # Apply industry filter if applicable
            if self.parameters['industry_filter'] and 'industry' in latest:
                if latest['industry'] != self.parameters['industry_filter']:
                    continue
            
            # Apply sector exclusion if applicable
            if self.parameters['exclude_sectors'] and 'sector' in latest:
                if latest['sector'] in self.parameters['exclude_sectors']:
                    continue
            
            # Symbol passed all filters
            filtered_universe[symbol] = data
        
        logger.info(f"Filtered universe from {len(universe)} to {len(filtered_universe)} symbols")
        return filtered_universe
    
    def calculate_stock_indicators(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Calculate stock-specific technical indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary of calculated indicators
        """
        indicators = {}
        
        # Calculate Moving Averages
        for period in [20, 50, 200]:
            ma_key = f'ma_{period}'
            indicators[ma_key] = pd.DataFrame({
                ma_key: data['close'].rolling(window=period).mean()
            })
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = pd.DataFrame({'rsi': rsi})
        
        # Calculate MACD
        ema12 = data['close'].ewm(span=12, adjust=False).mean()
        ema26 = data['close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        indicators['macd'] = pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'macd_hist': macd_hist
        })
        
        # Calculate Bollinger Bands
        ma20 = data['close'].rolling(window=20).mean()
        std20 = data['close'].rolling(window=20).std()
        
        upper_band = ma20 + (std20 * 2)
        lower_band = ma20 - (std20 * 2)
        
        indicators['bbands'] = pd.DataFrame({
            'middle_band': ma20,
            'upper_band': upper_band,
            'lower_band': lower_band
        })
        
        # Calculate Volume Profile if enabled
        if self.parameters['use_volume_profile'] and 'volume' in data.columns:
            # Simple volume distribution by price
            price_buckets = pd.cut(data['close'], bins=10)
            volume_profile = data.groupby(price_buckets)['volume'].sum()
            
            # Convert to DataFrame
            indicators['volume_profile'] = pd.DataFrame({
                'volume_by_price': volume_profile
            })
        
        return indicators
    
    def check_earnings_announcement(self, symbol: str, data: Dict[str, Any]) -> bool:
        """
        Check if there's an upcoming earnings announcement.
        
        Args:
            symbol: Stock symbol
            data: Stock data including fundamental info
            
        Returns:
            True if earnings are upcoming within parameter threshold days
        """
        # Skip if fundamental data is not enabled
        if not self.parameters['use_fundamentals']:
            return False
            
        # Check if earnings data is available
        if 'earnings_date' not in data:
            return False
            
        # Get next earnings date
        next_earnings = data['earnings_date']
        
        # If it's not a datetime, try to convert
        if not isinstance(next_earnings, datetime):
            try:
                next_earnings = pd.to_datetime(next_earnings)
            except:
                return False
        
        # Check if earnings are upcoming within threshold
        days_to_earnings = (next_earnings - datetime.now()).days
        
        # Default threshold is 5 days
        earnings_threshold = self.parameters.get('earnings_announcement_threshold', 5)
        
        return 0 <= days_to_earnings <= earnings_threshold
    
    def adjust_for_market_regime(self, signals: Dict[str, Signal], 
                                market_regime: MarketRegime) -> Dict[str, Signal]:
        """
        Adjust signals based on overall market regime.
        
        Args:
            signals: Dictionary of generated signals
            market_regime: Current market regime
            
        Returns:
            Adjusted signals
        """
        adjusted_signals = signals.copy()
        
        # In bear market, reduce position sizes and increase stop distance
        if market_regime == MarketRegime.BEAR_TREND:
            for symbol, signal in adjusted_signals.items():
                # Reduce confidence
                signal.confidence = signal.confidence * 0.7
                
                # Adjust stop loss to be wider
                if signal.stop_loss is not None and signal.price is not None:
                    # For buy signals
                    if signal.signal_type == SignalType.BUY:
                        stop_distance = signal.price - signal.stop_loss
                        # Increase stop distance by 50%
                        adjusted_stop = signal.price - (stop_distance * 1.5)
                        signal.stop_loss = adjusted_stop
        
        # In high volatility regime, tighten profit targets
        elif market_regime == MarketRegime.HIGH_VOLATILITY:
            for symbol, signal in adjusted_signals.items():
                if signal.take_profit is not None and signal.price is not None:
                    # For buy signals
                    if signal.signal_type == SignalType.BUY:
                        profit_distance = signal.take_profit - signal.price
                        # Reduce profit target by 30%
                        adjusted_target = signal.price + (profit_distance * 0.7)
                        signal.take_profit = adjusted_target
        
        return adjusted_signals
    
    def check_sector_rotation(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Analyze sector rotation to identify strong/weak sectors.
        
        Args:
            data: Dictionary mapping symbols to DataFrames with market data
            
        Returns:
            Dictionary mapping sectors to strength scores (higher is stronger)
        """
        # Skip if sector data not available
        if not data or 'sector' not in next(iter(data.values())).columns:
            return {}
            
        sector_returns = {}
        
        # Calculate returns for each sector
        for symbol, df in data.items():
            if df.empty or 'sector' not in df.columns:
                continue
                
            sector = df['sector'].iloc[-1]
            
            # Calculate 1-month return
            if len(df) > 20:
                returns = df['close'].iloc[-1] / df['close'].iloc[-21] - 1
                
                if sector not in sector_returns:
                    sector_returns[sector] = []
                    
                sector_returns[sector].append(returns)
        
        # Average returns by sector
        sector_strength = {}
        for sector, returns in sector_returns.items():
            if returns:
                sector_strength[sector] = np.mean(returns)
        
        return sector_strength 