import requests
import pandas as pd
import numpy as np
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

from trading.config import config

# Set up logging
logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """
    A comprehensive client for the Alpha Vantage API that supports:
    - Stock Time Series
    - Technical Indicators
    - Forex Data
    - Cryptocurrency Data
    - Fundamental Data
    - Economic Indicators
    - News & Sentiment
    
    Features:
    - Automatic rate limiting
    - Response caching
    - Comprehensive error handling
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the Alpha Vantage client
        
        Args:
            api_key: Alpha Vantage API key (if None, gets from config)
            cache_dir: Directory for caching API responses (if None, gets from config)
        """
        # Get API key from parameters, config, or environment variable
        self.api_key = api_key or config.get_api_key('alpha_vantage') or os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            logger.warning("No Alpha Vantage API key provided! API calls will fail.")
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir or config.get_cache_dir())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting settings (5 API requests per minute for free tier)
        self.request_count = 0
        self.last_request_time = 0
        self.requests_per_minute = 5
        self.premium_tier = False  # Set to True for premium API access with higher limits
    
    def set_premium_tier(self, premium: bool = True):
        """
        Set premium tier status for rate limiting
        
        Args:
            premium: Whether using premium tier (allows more requests per minute)
        """
        self.premium_tier = premium
        self.requests_per_minute = 75 if premium else 5
        logger.info(f"Set to {'premium' if premium else 'free'} tier: {self.requests_per_minute} requests per minute")
    
    def _throttle_requests(self):
        """Throttle requests to respect API limits"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Reset counter after a minute
        if elapsed >= 60:
            self.request_count = 0
            self.last_request_time = current_time
            return
        
        # If we've reached the limit, wait until the minute is up
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - elapsed
            if sleep_time > 0:
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = current_time
    
    def _get_cache_path(self, function: str, params: Dict[str, Any]) -> Path:
        """
        Generate a cache file path based on the function and parameters
        
        Args:
            function: API function name
            params: API request parameters
            
        Returns:
            Path object for the cache file
        """
        # Remove common parameters that don't affect the data
        cache_params = {k: v for k, v in params.items() if k not in ['apikey', 'datatype']}
        
        # Create a filename from parameters
        param_str = "_".join(f"{k}_{v}" for k, v in sorted(cache_params.items()))
        return self.cache_dir / f"{function}_{param_str}.parquet"
    
    def _get_from_cache(self, cache_path: Path, max_age_days: int = 1) -> Optional[pd.DataFrame]:
        """
        Get data from cache if available and not too old
        
        Args:
            cache_path: Path to cache file
            max_age_days: Maximum age of cache in days
            
        Returns:
            DataFrame with cached data or None if not available/valid
        """
        if not cache_path.exists():
            return None
        
        # Check if cache is too old
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(days=max_age_days):
            logger.info(f"Cache too old ({file_age.days} days): {cache_path}")
            return None
        
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Error reading cache file {cache_path}: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, cache_path: Path):
        """
        Save data to cache
        
        Args:
            df: DataFrame to cache
            cache_path: Path to cache file
        """
        try:
            df.to_parquet(cache_path, index=True)
            logger.info(f"Saved data to cache: {cache_path}")
        except Exception as e:
            logger.warning(f"Error saving to cache file {cache_path}: {e}")
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Alpha Vantage API with throttling
        
        Args:
            params: Request parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ValueError: If the API returns an error
        """
        if not self.api_key:
            raise ValueError("No Alpha Vantage API key provided!")
        
        # Add API key to parameters
        params["apikey"] = self.api_key
        
        # Throttle requests to respect API limits
        self._throttle_requests()
        
        try:
            logger.debug(f"Making API request: {params}")
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            # Increment request counter
            self.request_count += 1
            self.last_request_time = time.time()
            
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for rate limiting or information messages
            if "Note" in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
            
            if "Information" in data:
                logger.info(f"Alpha Vantage API info: {data['Information']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise ValueError(f"Failed to fetch data from Alpha Vantage: {e}")
    
    def get_time_series(
        self,
        symbol: str,
        interval: str = 'daily',
        adjusted: bool = True,
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        cache_days: int = 1
    ) -> pd.DataFrame:
        """
        Get stock time series data
        
        Args:
            symbol: Stock symbol
            interval: Time interval ('intraday', 'daily', 'weekly', 'monthly')
            adjusted: Whether to use adjusted data (for daily)
            outputsize: 'compact' (latest 100 data points) or 'full' (up to 20 years)
            start_date: Start date (YYYY-MM-DD) for filtering
            end_date: End date (YYYY-MM-DD) for filtering
            use_cache: Whether to use cached data
            cache_days: Max age of cached data in days
            
        Returns:
            DataFrame with time series data
        """
        # Map interval to the corresponding API function
        function_map = {
            'intraday': 'TIME_SERIES_INTRADAY',
            'daily': 'TIME_SERIES_DAILY_ADJUSTED' if adjusted else 'TIME_SERIES_DAILY',
            'weekly': 'TIME_SERIES_WEEKLY_ADJUSTED' if adjusted else 'TIME_SERIES_WEEKLY',
            'monthly': 'TIME_SERIES_MONTHLY_ADJUSTED' if adjusted else 'TIME_SERIES_MONTHLY'
        }
        
        if interval not in function_map:
            valid_intervals = list(function_map.keys())
            raise ValueError(f"Invalid interval: '{interval}'. Valid options are: {valid_intervals}")
        
        function = function_map[interval]
        
        # Set up parameters for the API request
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        # Add interval parameter for intraday data
        if interval == 'intraday':
            if 'intraday_interval' not in locals():
                intraday_interval = '15min'  # Default
            params['interval'] = intraday_interval
        
        # Check cache first if requested
        cache_path = self._get_cache_path(function, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path, max_age_days=cache_days)
            if cached_data is not None:
                logger.info(f"Using cached data for {symbol} ({interval})")
                
                # Filter by date if needed
                if start_date or end_date:
                    return self._filter_by_date(cached_data, start_date, end_date)
                
                return cached_data
        
        # Make API request if no cache or cache is too old
        data = self._make_request(params)
        
        # Determine the key for the time series data
        time_series_key = self._get_time_series_key(function)
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found in response. Available keys: {available_keys}")
        
        # Process and return the data
        df = self._process_time_series_data(data, time_series_key, function, symbol)
        
        # Save to cache if requested
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        # Filter by date if needed
        if start_date or end_date:
            return self._filter_by_date(df, start_date, end_date)
        
        return df
    
    def _get_time_series_key(self, function: str) -> str:
        """
        Determine the time series key in the API response
        
        Args:
            function: API function name
            
        Returns:
            Key string for the time series data
        """
        key_map = {
            'TIME_SERIES_INTRADAY': lambda params: f"Time Series ({params.get('interval', '15min')})",
            'TIME_SERIES_DAILY': 'Time Series (Daily)',
            'TIME_SERIES_DAILY_ADJUSTED': 'Time Series (Daily)',
            'TIME_SERIES_WEEKLY': 'Weekly Time Series',
            'TIME_SERIES_WEEKLY_ADJUSTED': 'Weekly Adjusted Time Series',
            'TIME_SERIES_MONTHLY': 'Monthly Time Series',
            'TIME_SERIES_MONTHLY_ADJUSTED': 'Monthly Adjusted Time Series',
            'FX_DAILY': 'Time Series FX (Daily)',
            'FX_WEEKLY': 'Time Series FX (Weekly)',
            'FX_MONTHLY': 'Time Series FX (Monthly)',
            'DIGITAL_CURRENCY_DAILY': 'Time Series (Digital Currency Daily)',
            'DIGITAL_CURRENCY_WEEKLY': 'Time Series (Digital Currency Weekly)',
            'DIGITAL_CURRENCY_MONTHLY': 'Time Series (Digital Currency Monthly)'
        }
        
        if function in key_map:
            if callable(key_map[function]):
                # For functions that need parameters to determine the key
                return key_map[function]({})
            return key_map[function]
        
        return None
    
    def _process_time_series_data(self, data: Dict, time_series_key: str, function: str, symbol: str) -> pd.DataFrame:
        """
        Process time series data from API response
        
        Args:
            data: API response data
            time_series_key: Key for time series data in the response
            function: API function used
            symbol: Symbol requested
            
        Returns:
            Processed DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Rename columns based on the function
        if 'ADJUSTED' in function:
            # For adjusted data
            renames = {
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. adjusted close': 'adjusted_close',
                '6. volume': 'volume',
                '7. dividend amount': 'dividend',
                '8. split coefficient': 'split'
            }
        else:
            # For regular data
            renames = {
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. volume': 'volume'
            }
        
        # Apply the column renames where the columns exist
        df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})
        
        # Convert numeric columns
        for col in df.columns:
            if col != 'split':  # Skip split coefficient
                df[col] = pd.to_numeric(df[col])
        
        # Set index to datetime and sort
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        df = df.sort_index()
        
        # Add symbol column
        df['symbol'] = symbol
        
        return df
    
    def _filter_by_date(self, df: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: DataFrame to filter
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Filtered DataFrame
        """
        result = df.copy()
        
        if start_date:
            result = result[result.index >= pd.to_datetime(start_date)]
        
        if end_date:
            result = result[result.index <= pd.to_datetime(end_date)]
        
        return result
    
    def get_intraday(
        self,
        symbol: str,
        interval: str = '15min',
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get intraday time series data
        
        Args:
            symbol: Stock symbol
            interval: Time interval ('1min', '5min', '15min', '30min', '60min')
            outputsize: 'compact' or 'full'
            start_date: Start date for filtering
            end_date: End date for filtering
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with intraday data
        """
        function = 'TIME_SERIES_INTRADAY'
        
        params = {
            "function": function,
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        
        # Check cache
        cache_path = self._get_cache_path(function, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path)
            if cached_data is not None:
                logger.info(f"Using cached intraday data for {symbol} ({interval})")
                return self._filter_by_date(cached_data, start_date, end_date)
        
        # Make API request
        data = self._make_request(params)
        
        # Get time series key
        time_series_key = f"Time Series ({interval})"
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found in response. Available keys: {available_keys}")
        
        # Process data
        df = self._process_time_series_data(data, time_series_key, function, symbol)
        
        # Save to cache
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        # Filter by date
        return self._filter_by_date(df, start_date, end_date)
    
    def get_daily(
        self,
        symbol: str,
        adjusted: bool = True,
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get daily time series data
        
        Args:
            symbol: Stock symbol
            adjusted: Whether to use adjusted prices
            outputsize: 'compact' or 'full'
            start_date: Start date for filtering
            end_date: End date for filtering
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with daily data
        """
        return self.get_time_series(
            symbol=symbol,
            interval='daily',
            adjusted=adjusted,
            outputsize=outputsize,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
    
    def get_weekly(
        self,
        symbol: str,
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get weekly time series data
        
        Args:
            symbol: Stock symbol
            adjusted: Whether to use adjusted prices
            start_date: Start date for filtering
            end_date: End date for filtering
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with weekly data
        """
        return self.get_time_series(
            symbol=symbol,
            interval='weekly',
            adjusted=adjusted,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
    
    def get_monthly(
        self,
        symbol: str,
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get monthly time series data
        
        Args:
            symbol: Stock symbol
            adjusted: Whether to use adjusted prices
            start_date: Start date for filtering
            end_date: End date for filtering
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with monthly data
        """
        return self.get_time_series(
            symbol=symbol,
            interval='monthly',
            adjusted=adjusted,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get current quote for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with current quote data
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        
        data = self._make_request(params)
        
        if "Global Quote" not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key 'Global Quote' not found in response. Available keys: {available_keys}")
        
        quote = data["Global Quote"]
        
        # Convert to a cleaner format
        cleaned_quote = {}
        for key, value in quote.items():
            # Remove numbers and dots from keys (e.g., "01. symbol" -> "symbol")
            clean_key = key.split(". ", 1)[1] if ". " in key else key
            
            # Convert numeric values
            if clean_key in ['price', 'open', 'high', 'low', 'previous close', 'change', 'change percent']:
                try:
                    if clean_key == 'change percent':
                        # Remove % sign before converting
                        value = float(value.rstrip('%'))
                    else:
                        value = float(value)
                except ValueError:
                    pass  # Keep as string if conversion fails
            elif clean_key == 'volume':
                try:
                    value = int(value)
                except ValueError:
                    pass
                
            cleaned_quote[clean_key] = value
            
        return cleaned_quote
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = 'daily',
        time_period: int = 14,
        series_type: str = 'close',
        use_cache: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get technical indicator data
        
        Args:
            symbol: Stock symbol
            indicator: Technical indicator function (e.g., 'SMA', 'EMA', 'RSI')
            interval: Time interval
            time_period: Number of data points used to calculate indicator
            series_type: Price series to use ('close', 'open', 'high', 'low')
            use_cache: Whether to use cached data
            **kwargs: Additional parameters specific to the indicator
            
        Returns:
            DataFrame with indicator data
        """
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type
        }
        
        # Add additional parameters
        params.update({k: v for k, v in kwargs.items() if v is not None})
        
        # Check cache
        cache_path = self._get_cache_path(indicator, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path)
            if cached_data is not None:
                logger.info(f"Using cached {indicator} data for {symbol}")
                return cached_data
        
        # Make API request
        data = self._make_request(params)
        
        # Get indicator key
        indicator_key = None
        for key in data.keys():
            if "Technical Analysis" in key:
                indicator_key = key
                break
        
        if not indicator_key:
            available_keys = list(data.keys())
            raise ValueError(f"Technical analysis key not found in response. Available keys: {available_keys}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[indicator_key], orient='index')
        
        # Convert all columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Set index to datetime and sort
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        df = df.sort_index()
        
        # Add symbol and indicator columns
        df['symbol'] = symbol
        df['indicator'] = indicator
        
        # Save to cache
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        return df
    
    # Technical Indicators - Convenience Methods
    def get_sma(self, symbol: str, time_period: int = 20, interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """Get Simple Moving Average"""
        return self.get_technical_indicator(symbol, 'SMA', interval, time_period, series_type)
    
    def get_ema(self, symbol: str, time_period: int = 20, interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """Get Exponential Moving Average"""
        return self.get_technical_indicator(symbol, 'EMA', interval, time_period, series_type)
    
    def get_rsi(self, symbol: str, time_period: int = 14, interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """Get Relative Strength Index"""
        return self.get_technical_indicator(symbol, 'RSI', interval, time_period, series_type)
    
    def get_macd(
        self, 
        symbol: str, 
        interval: str = 'daily', 
        series_type: str = 'close',
        fastperiod: int = 12,
        slowperiod: int = 26,
        signalperiod: int = 9
    ) -> pd.DataFrame:
        """Get Moving Average Convergence/Divergence"""
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='MACD',
            interval=interval,
            series_type=series_type,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod
        )
    
    def get_bbands(
        self,
        symbol: str,
        time_period: int = 20,
        interval: str = 'daily',
        series_type: str = 'close',
        nbdevup: int = 2,
        nbdevdn: int = 2,
        matype: int = 0
    ) -> pd.DataFrame:
        """Get Bollinger Bands"""
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='BBANDS',
            interval=interval,
            time_period=time_period,
            series_type=series_type,
            nbdevup=nbdevup,
            nbdevdn=nbdevdn,
            matype=matype
        )
    
    def get_fundamental_data(self, symbol: str, function: str) -> Dict[str, Any]:
        """
        Get fundamental data for a company
        
        Args:
            symbol: Stock symbol
            function: Fundamental data function ('OVERVIEW', 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW')
            
        Returns:
            Dictionary with fundamental data
        """
        params = {
            "function": function,
            "symbol": symbol
        }
        
        return self._make_request(params)
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview"""
        return self.get_fundamental_data(symbol, 'OVERVIEW')
    
    def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """Get income statement"""
        return self.get_fundamental_data(symbol, 'INCOME_STATEMENT')
    
    def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Get balance sheet"""
        return self.get_fundamental_data(symbol, 'BALANCE_SHEET')
    
    def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """Get cash flow statement"""
        return self.get_fundamental_data(symbol, 'CASH_FLOW')
    
    def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data"""
        return self.get_fundamental_data(symbol, 'EARNINGS')
    
    def get_forex_data(
        self,
        from_currency: str,
        to_currency: str,
        interval: str = 'daily',
        outputsize: str = 'compact',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get forex exchange rate time series
        
        Args:
            from_currency: From currency code
            to_currency: To currency code
            interval: Time interval ('daily', 'weekly', 'monthly', 'intraday')
            outputsize: 'compact' or 'full'
            start_date: Start date for filtering
            end_date: End date for filtering
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with forex data
        """
        # Map to correct function
        function_map = {
            'intraday': 'FX_INTRADAY',
            'daily': 'FX_DAILY',
            'weekly': 'FX_WEEKLY',
            'monthly': 'FX_MONTHLY'
        }
        
        if interval not in function_map:
            valid_intervals = list(function_map.keys())
            raise ValueError(f"Invalid interval: '{interval}'. Valid options are: {valid_intervals}")
        
        function = function_map[interval]
        
        params = {
            "function": function,
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize
        }
        
        # Add interval parameter for intraday
        if interval == 'intraday':
            if 'intraday_interval' not in locals():
                intraday_interval = '15min'  # Default
            params['interval'] = intraday_interval
        
        # Check cache
        cache_path = self._get_cache_path(function, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path)
            if cached_data is not None:
                logger.info(f"Using cached forex data for {from_currency}/{to_currency}")
                return self._filter_by_date(cached_data, start_date, end_date)
        
        # Make API request
        data = self._make_request(params)
        
        # Get time series key
        time_series_key = None
        for potential_key in [f"Time Series FX ({interval.capitalize()})", f"Time Series FX"]:
            if potential_key in data:
                time_series_key = potential_key
                break
        
        if not time_series_key:
            available_keys = list(data.keys())
            raise ValueError(f"Expected forex time series key not found. Available keys: {available_keys}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Rename columns
        df.columns = [col.split('. ')[1] for col in df.columns]
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Set index, add symbol
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        df['symbol'] = f"{from_currency}/{to_currency}"
        
        # Sort
        df = df.sort_index()
        
        # Save to cache
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        # Filter by date
        return self._filter_by_date(df, start_date, end_date)
    
    def get_crypto_data(
        self,
        symbol: str,
        market: str = 'USD',
        interval: str = 'daily',
        use_cache: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get cryptocurrency data
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC')
            market: Market (e.g., 'USD')
            interval: Time interval ('daily', 'weekly', 'monthly')
            use_cache: Whether to use cached data
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            DataFrame with cryptocurrency data
        """
        # Map to correct function
        function_map = {
            'daily': 'DIGITAL_CURRENCY_DAILY',
            'weekly': 'DIGITAL_CURRENCY_WEEKLY',
            'monthly': 'DIGITAL_CURRENCY_MONTHLY'
        }
        
        if interval not in function_map:
            valid_intervals = list(function_map.keys())
            raise ValueError(f"Invalid interval: '{interval}'. Valid options are: {valid_intervals}")
        
        function = function_map[interval]
        
        params = {
            "function": function,
            "symbol": symbol,
            "market": market
        }
        
        # Check cache
        cache_path = self._get_cache_path(function, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path)
            if cached_data is not None:
                logger.info(f"Using cached crypto data for {symbol}/{market}")
                return self._filter_by_date(cached_data, start_date, end_date)
        
        # Make API request
        data = self._make_request(params)
        
        # Get time series key
        time_series_key = f"Time Series (Digital Currency {interval.capitalize()})"
        
        if time_series_key not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key '{time_series_key}' not found. Available keys: {available_keys}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        
        # Filter for columns with the specified market
        market_cols = [col for col in df.columns if f"({market})" in col]
        df = df[market_cols]
        
        # Rename columns to remove the market suffix
        rename_dict = {}
        for col in df.columns:
            new_col = col.split(' (')[0].split('. ')[1]
            rename_dict[col] = new_col
        
        df = df.rename(columns=rename_dict)
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        # Set index, add symbol
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        df['symbol'] = f"{symbol}/{market}"
        
        # Sort
        df = df.sort_index()
        
        # Save to cache
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        # Filter by date
        return self._filter_by_date(df, start_date, end_date)
    
    def get_economic_indicator(
        self, 
        indicator: str,
        use_cache: bool = True,
        interval: Optional[str] = None  # For certain indicators like CPI, INFLATION
    ) -> pd.DataFrame:
        """
        Get economic indicator data
        
        Args:
            indicator: Economic indicator ('GDP', 'REAL_GDP', 'CPI', etc.)
            use_cache: Whether to use cached data
            interval: Interval ('monthly', 'quarterly', 'annual') for certain indicators
            
        Returns:
            DataFrame with economic indicator data
        """
        params = {
            "function": indicator
        }
        
        # Add interval for indicators that require it
        if interval:
            params["interval"] = interval
        
        # Check cache with longer validity (economic data changes less frequently)
        cache_path = self._get_cache_path(indicator, params)
        if use_cache:
            cached_data = self._get_from_cache(cache_path, max_age_days=7)  # Cache for a week
            if cached_data is not None:
                logger.info(f"Using cached economic data for {indicator}")
                return cached_data
        
        # Make API request
        data = self._make_request(params)
        
        # Find the data key (varies by indicator)
        data_key = None
        for key in data.keys():
            if key not in ["Meta Data", "Information", "Note"]:
                data_key = key
                break
        
        if not data_key:
            available_keys = list(data.keys())
            raise ValueError(f"Could not find data key in response. Available keys: {available_keys}")
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[data_key], orient='index')
        
        # Convert columns to numeric where possible
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass  # Keep as string if conversion fails
        
        # Set index to datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort
        df = df.sort_index()
        
        # Add indicator info
        df['indicator'] = indicator
        
        # Save to cache
        if use_cache:
            self._save_to_cache(df, cache_path)
        
        return df
    
    def get_stock_news(
        self, 
        tickers: Optional[List[str]] = None, 
        topics: Optional[List[str]] = None,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        limit: int = 50,
        sort: str = 'LATEST'
    ) -> List[Dict[str, Any]]:
        """
        Get news articles for stocks
        
        Args:
            tickers: List of ticker symbols
            topics: List of topics ('earnings', 'ipo', 'mergers_and_acquisitions', etc.)
            time_from: Start time (YYYYMMDDTHHMM format)
            time_to: End time (YYYYMMDDTHHMM format)
            limit: Number of articles to return (max 1000)
            sort: Sort order ('LATEST', 'EARLIEST', 'RELEVANCE')
            
        Returns:
            List of news articles
        """
        params = {
            "function": "NEWS_SENTIMENT"
        }
        
        if tickers:
            params["tickers"] = ",".join(tickers)
        
        if topics:
            params["topics"] = ",".join(topics)
        
        if time_from:
            params["time_from"] = time_from
            
        if time_to:
            params["time_to"] = time_to
            
        params["limit"] = min(1000, limit)  # API limit is 1000
        params["sort"] = sort
        
        # Make API request (don't cache news as it changes frequently)
        data = self._make_request(params)
        
        if "feed" not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key 'feed' not found in response. Available keys: {available_keys}")
            
        return data["feed"]
    
    def get_search_results(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Search for symbols based on keywords
        
        Args:
            keywords: Search keywords
            
        Returns:
            List of matching symbols with metadata
        """
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords
        }
        
        data = self._make_request(params)
        
        if "bestMatches" not in data:
            available_keys = list(data.keys())
            raise ValueError(f"Expected key 'bestMatches' not found in response. Available keys: {available_keys}")
            
        # Clean up results
        results = []
        for match in data["bestMatches"]:
            clean_result = {}
            for key, value in match.items():
                clean_key = key.split(". ")[1] if ". " in key else key
                clean_result[clean_key] = value
            results.append(clean_result)
            
        return results
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status (open/closed)
        
        Returns:
            Dictionary with market status information
        """
        params = {
            "function": "MARKET_STATUS"
        }
        
        return self._make_request(params)
        
    def get_multiple_symbols(
        self, 
        symbols: List[str], 
        interval: str = 'daily',
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple symbols
        
        Args:
            symbols: List of symbols
            interval: Time interval
            adjusted: Whether to use adjusted prices
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        result = {}
        
        for symbol in symbols:
            try:
                df = self.get_time_series(
                    symbol=symbol,
                    interval=interval,
                    adjusted=adjusted,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty:
                    result[symbol] = df
                    
            except Exception as e:
                logger.error(f"Failed to get data for {symbol}: {e}")
                
        return result


# Example usage
if __name__ == "__main__":
    # Get API key from config
    api_key = config.get_api_key('alpha_vantage')
    
    # Initialize client
    client = AlphaVantageClient(api_key=api_key)
    
    # Example: Get daily stock data for AAPL
    aapl_data = client.get_daily(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    if not aapl_data.empty:
        print(f"Retrieved {len(aapl_data)} days of AAPL data")
        print(aapl_data.head())
        
        # Example: Add some technical indicators
        rsi = client.get_rsi('AAPL', time_period=14)
        sma_50 = client.get_sma('AAPL', time_period=50)
        
        print("\nRSI:")
        print(rsi.head())
        
        print("\nSMA (50):")
        print(sma_50.head()) 