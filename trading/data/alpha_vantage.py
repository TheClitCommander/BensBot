import requests
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

class AlphaVantageFetcher:
    """Class for fetching market data from Alpha Vantage API"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str):
        """
        Initialize the AlphaVantage fetcher
        
        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key
        if not api_key:
            logger.warning("No Alpha Vantage API key provided. API calls will fail.")
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make a request to Alpha Vantage API
        
        Args:
            params: Request parameters
            
        Returns:
            JSON response from the API
        
        Raises:
            ValueError: If the API returns an error
        """
        params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            data = response.json()
            
            # Check if the response contains an error message
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for information messages (often about API limits)
            if "Information" in data:
                logger.warning(f"Alpha Vantage API info: {data['Information']}")
            
            # Check for API call limit
            if "Note" in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ValueError(f"Failed to fetch data from Alpha Vantage: {e}")
    
    def get_stock_time_series(
        self, 
        symbol: str, 
        interval: str = 'daily', 
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get stock time series data
        
        Args:
            symbol: Stock symbol
            interval: Time interval ('daily', 'weekly', 'monthly', '1min', '5min', etc.)
            outputsize: 'compact' returns the latest 100 data points, 'full' returns up to 20 years of data
            start_date: Start date in 'YYYY-MM-DD' format (used for filtering)
            end_date: End date in 'YYYY-MM-DD' format (used for filtering)
            
        Returns:
            DataFrame with OHLCV data
        """
        # Map interval to the corresponding API function
        interval_mapping = {
            'daily': 'TIME_SERIES_DAILY',
            'weekly': 'TIME_SERIES_WEEKLY',
            'monthly': 'TIME_SERIES_MONTHLY',
            '1min': 'TIME_SERIES_INTRADAY',
            '5min': 'TIME_SERIES_INTRADAY',
            '15min': 'TIME_SERIES_INTRADAY',
            '30min': 'TIME_SERIES_INTRADAY',
            '60min': 'TIME_SERIES_INTRADAY'
        }
        
        function = interval_mapping.get(interval)
        if not function:
            raise ValueError(f"Invalid interval: {interval}. Supported intervals: {list(interval_mapping.keys())}")
        
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize,
        }
        
        # Add interval parameter for intraday data
        if function == 'TIME_SERIES_INTRADAY':
            params["interval"] = interval
        
        # Make the API request
        data = self._make_request(params)
        
        # Determine the key for the time series data based on the function
        time_series_key = None
        if function == 'TIME_SERIES_DAILY':
            time_series_key = 'Time Series (Daily)'
        elif function == 'TIME_SERIES_WEEKLY':
            time_series_key = 'Weekly Time Series'
        elif function == 'TIME_SERIES_MONTHLY':
            time_series_key = 'Monthly Time Series'
        elif function == 'TIME_SERIES_INTRADAY':
            time_series_key = f'Time Series ({interval})'
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found in response. Available keys: {available_keys}")
        
        # Convert data to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Rename columns
        df.columns = [col.split('. ')[1] for col in df.columns]
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Convert columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort by date
        df = df.sort_index()
        
        # Filter by date range if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df.index >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df.index <= end_date]
            
        # Add symbol column
        df['symbol'] = symbol
            
        return df
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = 'daily',
        time_period: int = 14,
        series_type: str = 'close',
        **kwargs
    ) -> pd.DataFrame:
        """
        Get technical indicator data
        
        Args:
            symbol: Stock symbol
            indicator: Technical indicator function name (e.g., 'SMA', 'EMA', 'RSI', etc.)
            interval: Time interval (e.g., 'daily', 'weekly', 'monthly', '1min', '5min', etc.)
            time_period: Number of data points to calculate the indicator
            series_type: Price type to use ('close', 'open', 'high', 'low')
            **kwargs: Additional parameters specific to the indicator
            
        Returns:
            DataFrame with indicator data
        """
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": str(time_period),
            "series_type": series_type,
        }
        
        # Add additional parameters if provided
        for key, value in kwargs.items():
            params[key] = str(value)
        
        # Make the API request
        data = self._make_request(params)
        
        # Extract the technical indicator data
        meta_data_key = "Meta Data"
        technical_indicator_key = f"Technical Analysis: {indicator}"
        
        if technical_indicator_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{technical_indicator_key}' not found in response. Available keys: {available_keys}")
        
        # Convert data to DataFrame
        df = pd.DataFrame.from_dict(data[technical_indicator_key], orient='index')
        
        # Convert columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort by date
        df = df.sort_index()
        
        # Add metadata
        df['symbol'] = symbol
        df['indicator'] = indicator
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame, indicators: List[Dict[str, any]]) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe
        
        Args:
            df: DataFrame with OHLCV data
            indicators: List of dicts with indicator parameters
                Each dict should have: 
                - 'name': indicator name to use as column name
                - 'function': Alpha Vantage indicator function
                - Other parameters specific to the indicator
                
        Returns:
            DataFrame with added technical indicators
        """
        if df.empty:
            return df
        
        symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else 'UNKNOWN'
        
        for indicator_config in indicators:
            try:
                name = indicator_config.pop('name')
                function = indicator_config.pop('function')
                
                # Default values for common parameters
                time_period = indicator_config.pop('time_period', 14)
                series_type = indicator_config.pop('series_type', 'close')
                
                # Get interval from config or default to daily
                interval = indicator_config.pop('interval', 'daily')
                
                # Fetch indicator data
                indicator_df = self.get_technical_indicator(
                    symbol=symbol,
                    indicator=function,
                    interval=interval,
                    time_period=time_period,
                    series_type=series_type,
                    **indicator_config
                )
                
                # Rename the indicator column to the specified name
                indicator_col = indicator_df.columns[0]
                indicator_df = indicator_df.rename(columns={indicator_col: name})
                
                # Merge with main dataframe
                df = df.join(indicator_df[[name]])
                
            except Exception as e:
                logger.error(f"Failed to add indicator {name}: {e}")
        
        return df
    
    def get_multiple_symbols(
        self, 
        symbols: List[str], 
        interval: str = 'daily',
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Get market data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            interval: Time interval
            outputsize: Data size
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping symbols to their respective DataFrames
        """
        result = {}
        
        for symbol in symbols:
            try:
                df = self.get_stock_time_series(
                    symbol=symbol,
                    interval=interval,
                    outputsize=outputsize,
                    start_date=start_date,
                    end_date=end_date
                )
                result[symbol] = df
                
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
        
        return result
    
    def get_forex_data(
        self, 
        from_currency: str, 
        to_currency: str, 
        interval: str = 'daily',
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get forex time series data
        
        Args:
            from_currency: From currency code
            to_currency: To currency code
            interval: Time interval
            outputsize: Data size
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with forex data
        """
        # Map interval to the corresponding API function
        interval_mapping = {
            'daily': 'FX_DAILY',
            'weekly': 'FX_WEEKLY',
            'monthly': 'FX_MONTHLY',
            '1min': 'FX_INTRADAY',
            '5min': 'FX_INTRADAY',
            '15min': 'FX_INTRADAY',
            '30min': 'FX_INTRADAY',
            '60min': 'FX_INTRADAY'
        }
        
        function = interval_mapping.get(interval)
        if not function:
            raise ValueError(f"Invalid interval: {interval}. Supported intervals: {list(interval_mapping.keys())}")
        
        params = {
            "function": function,
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize,
        }
        
        # Add interval parameter for intraday data
        if function == 'FX_INTRADAY':
            params["interval"] = interval
        
        # Make the API request
        data = self._make_request(params)
        
        # Determine the key for the time series data based on the function
        time_series_key = None
        if function == 'FX_DAILY':
            time_series_key = 'Time Series FX (Daily)'
        elif function == 'FX_WEEKLY':
            time_series_key = 'Time Series FX (Weekly)'
        elif function == 'FX_MONTHLY':
            time_series_key = 'Time Series FX (Monthly)'
        elif function == 'FX_INTRADAY':
            time_series_key = f'Time Series FX ({interval})'
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found in response. Available keys: {available_keys}")
        
        # Convert data to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Rename columns
        df.columns = [col.split('. ')[1] for col in df.columns]
        df.columns = ['open', 'high', 'low', 'close']
        
        # Convert columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort by date
        df = df.sort_index()
        
        # Filter by date range if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df.index >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df.index <= end_date]
            
        # Add symbol column
        df['symbol'] = f"{from_currency}/{to_currency}"
            
        return df
    
    def get_crypto_data(
        self, 
        symbol: str, 
        market: str = 'USD',
        interval: str = 'daily',
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get cryptocurrency time series data
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC)
            market: Market (e.g., USD, EUR)
            interval: Time interval
            outputsize: Data size
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with cryptocurrency data
        """
        # Map interval to the corresponding API function
        interval_mapping = {
            'daily': 'DIGITAL_CURRENCY_DAILY',
            'weekly': 'DIGITAL_CURRENCY_WEEKLY',
            'monthly': 'DIGITAL_CURRENCY_MONTHLY'
        }
        
        function = interval_mapping.get(interval)
        if not function:
            raise ValueError(f"Invalid interval: {interval}. Supported intervals: {list(interval_mapping.keys())}")
        
        params = {
            "function": function,
            "symbol": symbol,
            "market": market
        }
        
        # Make the API request
        data = self._make_request(params)
        
        # Determine the key for the time series data based on the function
        time_series_key = None
        if function == 'DIGITAL_CURRENCY_DAILY':
            time_series_key = 'Time Series (Digital Currency Daily)'
        elif function == 'DIGITAL_CURRENCY_WEEKLY':
            time_series_key = 'Time Series (Digital Currency Weekly)'
        elif function == 'DIGITAL_CURRENCY_MONTHLY':
            time_series_key = 'Time Series (Digital Currency Monthly)'
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found in response. Available keys: {available_keys}")
        
        # Convert data to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Select only columns for the specified market
        market_cols = [col for col in df.columns if f"({market})" in col]
        df = df[market_cols]
        
        # Rename columns
        df.columns = [col.split(' ')[1].split('(')[0] for col in df.columns]
        
        # Convert columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort by date
        df = df.sort_index()
        
        # Filter by date range if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df.index >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df.index <= end_date]
            
        # Add symbol column
        df['symbol'] = f"{symbol}/{market}"
            
        return df 