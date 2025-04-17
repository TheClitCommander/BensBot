#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha Vantage data source implementation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import time

import pandas as pd
import requests

from trading_bot.data.models import MarketData, TimeFrame, DataSource, SymbolMetadata
from trading_bot.data.sources.base import BaseDataSource


logger = logging.getLogger(__name__)


class AlphaVantageDataSource(BaseDataSource):
    """
    Data source implementation for Alpha Vantage API.
    Requires an API key from https://www.alphavantage.co/
    """
    
    # Base URL for Alpha Vantage API
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Rate limiting settings
    CALLS_PER_MINUTE = 5  # Free tier limit
    
    def __init__(self, name: str = "alpha_vantage", api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage data source.
        
        Args:
            name: Unique identifier for this data source instance
            api_key: Alpha Vantage API key (required)
        """
        super().__init__(name, DataSource.ALPHA_VANTAGE, api_key)
        
        if not api_key:
            logger.warning("No API key provided for Alpha Vantage. Most endpoints will fail.")
            
        self._last_call_time = 0
    
    def _convert_timeframe(self, timeframe: TimeFrame) -> str:
        """
        Convert our TimeFrame enum to Alpha Vantage interval string.
        
        Args:
            timeframe: TimeFrame enum value
            
        Returns:
            Alpha Vantage interval string
        """
        mapping = {
            TimeFrame.MIN_1: "1min",
            TimeFrame.MIN_5: "5min",
            TimeFrame.MIN_15: "15min",
            TimeFrame.MIN_30: "30min",
            TimeFrame.HOUR_1: "60min",
            TimeFrame.DAY_1: "daily",
            TimeFrame.WEEK_1: "weekly",
            TimeFrame.MONTH_1: "monthly",
        }
        
        if timeframe not in mapping:
            logger.warning(f"Unsupported timeframe {timeframe}, defaulting to daily")
            return "daily"
            
        return mapping[timeframe]
    
    def _respect_rate_limit(self):
        """
        Ensure we don't exceed Alpha Vantage's rate limits.
        Implements a simple delay mechanism.
        """
        current_time = time.time()
        time_since_last_call = current_time - self._last_call_time
        
        # Ensure at least 60/CALLS_PER_MINUTE seconds between calls
        min_interval = 60.0 / self.CALLS_PER_MINUTE
        
        if time_since_last_call < min_interval:
            time_to_sleep = min_interval - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {time_to_sleep:.2f} seconds")
            time.sleep(time_to_sleep)
            
        self._last_call_time = time.time()
    
    def _make_api_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make a request to the Alpha Vantage API with rate limiting.
        
        Args:
            params: Request parameters
            
        Returns:
            API response as a dictionary
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
            
        # Add API key to params
        params['apikey'] = self.api_key
        
        # Respect rate limit
        self._respect_rate_limit()
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            
            # Check for error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return {}
                
            # Check for information messages (often rate limit warnings)
            if 'Information' in data:
                logger.warning(f"Alpha Vantage API info: {data['Information']}")
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return {}
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {}
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {}
    
    def get_data(self, symbol: str, start_date: datetime, end_date: datetime, 
                timeframe: TimeFrame = TimeFrame.DAY_1) -> List[MarketData]:
        """
        Retrieve market data for a symbol within the specified date range.
        
        Args:
            symbol: Trading symbol to retrieve data for
            start_date: Start date for the data range
            end_date: End date for the data range
            timeframe: Time frame for the data
            
        Returns:
            List of MarketData objects
        """
        interval = self._convert_timeframe(timeframe)
        
        # Determine which function to use based on the interval
        if interval in ['daily', 'weekly', 'monthly']:
            function = f"TIME_SERIES_{interval.upper()}"
            time_series_key = f"Time Series ({interval.capitalize()})"
            # For daily data we can use adjusted to get adjusted close
            if interval == 'daily':
                function = "TIME_SERIES_DAILY_ADJUSTED"
                time_series_key = "Time Series (Daily)"
        else:
            function = "TIME_SERIES_INTRADAY"
            time_series_key = f"Time Series ({interval})"
            
        # Prepare API parameters
        params = {
            'function': function,
            'symbol': symbol,
            'outputsize': 'full'  # To get as much historical data as possible
        }
        
        # Add interval parameter for intraday data
        if function == "TIME_SERIES_INTRADAY":
            params['interval'] = interval
            
        # Make API request
        data = self._make_api_request(params)
        
        if not data or time_series_key not in data:
            logger.warning(f"No data returned for {symbol} with timeframe {timeframe}")
            return []
            
        # Extract time series data and convert to DataFrame
        time_series = data[time_series_key]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns to match our schema (column names vary by endpoint)
        column_mapping = {
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume',
            '5. adjusted close': 'adj_close',
            '6. volume': 'volume'  # For adjusted daily data
        }
        
        df.rename(columns=column_mapping, inplace=True)
        
        # Convert index to datetime column
        df.index = pd.to_datetime(df.index)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'timestamp'}, inplace=True)
        
        # Filter by date range
        df = df[(df['timestamp'] >= pd.Timestamp(start_date)) & 
                (df['timestamp'] <= pd.Timestamp(end_date))]
                
        # Add symbol column
        df['symbol'] = symbol
        
        # Convert columns to appropriate types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        if 'adj_close' not in df.columns and 'close' in df.columns:
            df['adj_close'] = df['close']  # Use regular close if adjusted not available
        
        # Sort by timestamp (descending)
        df.sort_values('timestamp', ascending=False, inplace=True)
        
        # Convert to our data model
        market_data_list = self.from_dataframe(df)
        
        return market_data_list
    
    def get_latest(self, symbol: str, timeframe: TimeFrame = TimeFrame.DAY_1) -> Optional[MarketData]:
        """
        Get the latest market data for a symbol.
        
        Alpha Vantage doesn't have a specific endpoint for latest data,
        so we retrieve recent data and return the most recent entry.
        
        Args:
            symbol: Trading symbol to retrieve data for
            timeframe: Time frame for the data
            
        Returns:
            Latest MarketData object or None if not available
        """
        # For latest data, we'll retrieve the last month and take the most recent
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = self.get_data(symbol, start_date, end_date, timeframe)
        if not data:
            return None
            
        # Data is already sorted by timestamp in descending order
        return data[0]
    
    def get_available_symbols(self) -> List[str]:
        """
        Get a list of available symbols that match a search query.
        
        Note: Alpha Vantage doesn't provide a complete list of symbols,
        but offers a search endpoint. This implementation returns an empty list
        as a full implementation would require a specific search query.
        
        Returns:
            Empty list (feature not fully supported)
        """
        logger.warning("Alpha Vantage doesn't provide a direct API for listing all available symbols")
        return []
    
    def get_symbol_metadata(self, symbol: str) -> Optional[SymbolMetadata]:
        """
        Get metadata for a specific symbol from Alpha Vantage.
        
        Args:
            symbol: Symbol to retrieve metadata for
            
        Returns:
            SymbolMetadata object or None if not available
        """
        # Use the OVERVIEW function to get company information
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_api_request(params)
        
        if not data or 'Symbol' not in data:
            logger.warning(f"No metadata available for symbol {symbol}")
            # Try the search function as a fallback
            return self._get_metadata_from_search(symbol)
            
        return SymbolMetadata(
            symbol=data.get('Symbol', symbol),
            name=data.get('Name', symbol),
            asset_type='Equity',  # Overview only works for equities
            exchange=data.get('Exchange', 'unknown'),
            currency=data.get('Currency', 'USD'),
            sector=data.get('Sector', None),
            industry=data.get('Industry', None),
            country=data.get('Country', None),
            description=data.get('Description', None)
        )
    
    def _get_metadata_from_search(self, symbol: str) -> Optional[SymbolMetadata]:
        """
        Fallback method to get basic metadata from the SYMBOL_SEARCH endpoint.
        
        Args:
            symbol: Symbol to search for
            
        Returns:
            SymbolMetadata object or None if not available
        """
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': symbol
        }
        
        data = self._make_api_request(params)
        
        if not data or 'bestMatches' not in data or not data['bestMatches']:
            logger.warning(f"No search results for symbol {symbol}")
            return None
            
        # Find the exact match if possible
        exact_matches = [match for match in data['bestMatches'] 
                        if match.get('1. symbol', '').upper() == symbol.upper()]
        
        match = exact_matches[0] if exact_matches else data['bestMatches'][0]
        
        return SymbolMetadata(
            symbol=match.get('1. symbol', symbol),
            name=match.get('2. name', symbol),
            asset_type=match.get('3. type', 'unknown'),
            exchange=match.get('4. region', 'unknown'),
            currency=match.get('8. currency', 'USD'),
            sector=None,
            industry=None,
            country=None,
            description=None
        ) 