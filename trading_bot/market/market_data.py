#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Module

This module provides the MarketData class for accessing historical and real-time
market data from various sources.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

logger = logging.getLogger(__name__)

class MarketData:
    """
    Market Data class for accessing historical and real-time market data.
    
    This class provides a unified interface for accessing market data from
    various sources, including APIs, local files, and databases.
    """
    
    def __init__(self, data_source: str = "yahoo", cache_dir: Optional[str] = None):
        """
        Initialize the MarketData object.
        
        Args:
            data_source: Source for market data (default: "yahoo")
            cache_dir: Directory for caching data (optional)
        """
        self.data_source = data_source
        self.cache_dir = cache_dir
        self._price_cache = {}  # Cache for price data
        
        logger.info(f"Initialized MarketData with source: {data_source}")
    
    def get_historical_data(self, symbol: str, 
                           start_date: Optional[Union[str, datetime, date]] = None,
                           end_date: Optional[Union[str, datetime, date]] = None,
                           days: Optional[int] = None,
                           fields: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
        """
        Get historical market data for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date for data (optional)
            end_date: End date for data (optional)
            days: Number of days of data to retrieve (optional, alternative to start_date)
            fields: List of fields to retrieve (default: all available)
            
        Returns:
            DataFrame with historical data or None if data could not be retrieved
        """
        # Handle date parameters
        if end_date is None:
            end_date = datetime.now().date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_date is None and days is not None:
            start_date = end_date - timedelta(days=days)
        elif start_date is None:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        # Default fields if none provided
        if fields is None:
            fields = ["open", "high", "low", "close", "volume"]
        
        try:
            # Check cache first
            cache_key = f"{symbol}_{start_date}_{end_date}"
            if cache_key in self._price_cache:
                data = self._price_cache[cache_key]
                # Filter to requested fields
                if fields and not all(field in data.columns for field in fields):
                    logger.warning(f"Some requested fields {fields} not available in cached data")
                available_fields = [f for f in fields if f in data.columns]
                return data[available_fields] if available_fields else data
            
            # If using "mock" data source, generate mock data
            if self.data_source.lower() == "mock":
                data = self._generate_mock_data(symbol, start_date, end_date, fields)
                self._price_cache[cache_key] = data
                return data
            
            # Otherwise, we would fetch from the actual data source
            # For now, return mock data as placeholder
            logger.warning(f"Using mock data for {symbol} as {self.data_source} is not implemented")
            data = self._generate_mock_data(symbol, start_date, end_date, fields)
            self._price_cache[cache_key] = data
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest available price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest price or None if not available
        """
        try:
            # Get recent data (last 5 days to ensure we have at least one data point)
            recent_data = self.get_historical_data(symbol, days=5, fields=["close"])
            
            if recent_data is None or recent_data.empty:
                return None
                
            # Return the most recent close price
            return recent_data["close"].iloc[-1]
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {str(e)}")
            return None
    
    def get_latest_prices(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get the latest prices for multiple symbols.
        
        Args:
            symbols: List of stock symbols (optional)
            
        Returns:
            DataFrame with latest prices
        """
        if symbols is None:
            # If no symbols provided, return empty DataFrame
            return pd.DataFrame(columns=["symbol", "close"])
        
        data = []
        for symbol in symbols:
            price = self.get_latest_price(symbol)
            if price is not None:
                data.append({"symbol": symbol, "close": price})
        
        # Create DataFrame from collected data
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index("symbol", inplace=True)
        
        return df
    
    def has_min_history(self, symbol: str, min_days: int) -> bool:
        """
        Check if a symbol has at least the specified minimum days of history.
        
        Args:
            symbol: Stock symbol
            min_days: Minimum number of days required
            
        Returns:
            True if the symbol has at least min_days of history, False otherwise
        """
        data = self.get_historical_data(symbol, days=min_days)
        return data is not None and len(data) >= min_days
    
    def _generate_mock_data(self, symbol: str, start_date: date, 
                          end_date: date, fields: List[str]) -> pd.DataFrame:
        """
        Generate mock market data for testing purposes.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            fields: List of fields to include
            
        Returns:
            DataFrame with mock data
        """
        # Generate date range
        date_range = pd.date_range(start=start_date, end=end_date, freq="B")
        
        # Generate random starting price based on symbol
        # Use sum of ASCII values of the symbol to generate a consistent price
        base_price = sum(ord(c) for c in symbol) % 100 + 50
        
        # Generate random price data with a slight upward trend
        np.random.seed(sum(ord(c) for c in symbol))  # Seed based on symbol for consistency
        
        # Generate daily returns with a slight drift
        returns = np.random.normal(0.0002, 0.015, len(date_range))
        
        # Calculate prices from returns
        prices = base_price * np.cumprod(1 + returns)
        
        # Generate OHLC data
        data = {
            "open": prices * np.random.uniform(0.99, 1.01, len(date_range)),
            "high": prices * np.random.uniform(1.01, 1.03, len(date_range)),
            "low": prices * np.random.uniform(0.97, 0.99, len(date_range)),
            "close": prices,
            "volume": np.random.randint(100000, 5000000, len(date_range))
        }
        
        # Ensure high >= open, close, low and low <= open, close
        for i in range(len(date_range)):
            data["high"][i] = max(data["high"][i], data["open"][i], data["close"][i])
            data["low"][i] = min(data["low"][i], data["open"][i], data["close"][i])
        
        # Create DataFrame
        df = pd.DataFrame(data, index=date_range)
        
        # Filter to requested fields
        available_fields = [f for f in fields if f in df.columns]
        
        return df[available_fields] if available_fields else df 