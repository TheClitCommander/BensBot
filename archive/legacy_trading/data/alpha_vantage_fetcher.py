import pandas as pd
import numpy as np
import requests
import os
import time
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AlphaVantageFetcher')

class AlphaVantageFetcher:
    """Class for fetching data from Alpha Vantage API"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = 'data/cache'):
        """
        Initialize the Alpha Vantage fetcher
        
        Parameters:
        -----------
        api_key : str, optional
            Alpha Vantage API key. If None, looks for ALPHA_VANTAGE_API_KEY environment variable
        cache_dir : str
            Directory to cache data
        """
        self.api_key = api_key or os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            logger.warning("No Alpha Vantage API key provided! Please set the ALPHA_VANTAGE_API_KEY environment variable.")
        
        self.base_url = 'https://www.alphavantage.co/query'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.request_count = 0
        self.last_request_time = 0
        
    def _throttle_requests(self):
        """Throttle requests to respect API limits (5 API requests per minute)"""
        current_time = time.time()
        if current_time - self.last_request_time < 12 and self.request_count >= 5:
            sleep_time = 12 - (current_time - self.last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = time.time()
        elif current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
            
    def _get_cache_filename(self, function: str, symbol: str, interval: str = None) -> Path:
        """
        Get the cache filename for a specific query
        
        Parameters:
        -----------
        function : str
            Alpha Vantage function
        symbol : str
            Stock symbol
        interval : str, optional
            Time interval for intraday data
            
        Returns:
        --------
        Path
            Path to cache file
        """
        if interval:
            return self.cache_dir / f"{symbol}_{function}_{interval}.csv"
        else:
            return self.cache_dir / f"{symbol}_{function}.csv"
            
    def _get_from_cache(self, filename: Path, max_age_days: int = 1) -> Optional[pd.DataFrame]:
        """
        Get data from cache if available and not too old
        
        Parameters:
        -----------
        filename : Path
            Path to cache file
        max_age_days : int
            Maximum age of cache in days
            
        Returns:
        --------
        pd.DataFrame or None
            Cached data or None if not available or too old
        """
        if not filename.exists():
            return None
            
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(filename.stat().st_mtime)
        if file_age > timedelta(days=max_age_days):
            logger.info(f"Cache too old ({file_age.days} days): {filename}")
            return None
            
        try:
            return pd.read_csv(filename, index_col=0, parse_dates=True)
        except Exception as e:
            logger.warning(f"Error reading cache file {filename}: {e}")
            return None
            
    def _save_to_cache(self, df: pd.DataFrame, filename: Path):
        """
        Save data to cache
        
        Parameters:
        -----------
        df : pd.DataFrame
            Data to save
        filename : Path
            Path to cache file
        """
        try:
            df.to_csv(filename)
            logger.info(f"Saved data to cache: {filename}")
        except Exception as e:
            logger.warning(f"Error saving to cache file {filename}: {e}")
            
    def _make_request(self, params: Dict[str, str]) -> Dict:
        """
        Make a request to Alpha Vantage API
        
        Parameters:
        -----------
        params : Dict[str, str]
            Request parameters
            
        Returns:
        --------
        Dict
            JSON response
        
        Raises:
        -------
        ValueError
            If the API request fails
        """
        if not self.api_key:
            raise ValueError("No Alpha Vantage API key provided!")
            
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        # Throttle requests
        self._throttle_requests()
        
        try:
            logger.info(f"Making API request: {params}")
            response = requests.get(self.base_url, params=params)
            self.request_count += 1
            self.last_request_time = time.time()
            
            if 'Error Message' in response.text:
                raise ValueError(f"API Error: {response.text}")
                
            if 'Note' in response.text and 'thank you for using Alpha Vantage' in response.text:
                logger.warning("API call frequency limit reached!")
                
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise ValueError(f"API request failed: {e}")
            
    def get_stock_data(self, symbol: str, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None, use_adjusted: bool = True,
                    use_cache: bool = True) -> pd.DataFrame:
        """
        Get stock data for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        start_date : str, optional
            Start date (YYYY-MM-DD)
        end_date : str, optional
            End date (YYYY-MM-DD)
        use_adjusted : bool
            Whether to use adjusted prices
        use_cache : bool
            Whether to use cached data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with stock data
        """
        function = 'TIME_SERIES_DAILY_ADJUSTED' if use_adjusted else 'TIME_SERIES_DAILY'
        output_size = 'full'  # Get full data, will filter later
        
        cache_file = self._get_cache_filename(function, symbol)
        
        # Try to get from cache
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data is not None:
                logger.info(f"Using cached data for {symbol}")
                
                # Filter by date
                if start_date:
                    cached_data = cached_data[cached_data.index >= start_date]
                if end_date:
                    cached_data = cached_data[cached_data.index <= end_date]
                    
                return cached_data
                
        # Make API request
        params = {
            'function': function,
            'symbol': symbol,
            'outputsize': output_size,
            'datatype': 'json'
        }
        
        try:
            data = self._make_request(params)
            
            # Parse time series data
            if function == 'TIME_SERIES_DAILY_ADJUSTED':
                time_series_key = 'Time Series (Daily)'
                columns = {
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
                time_series_key = 'Time Series (Daily)'
                columns = {
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close',
                    '5. volume': 'volume'
                }
                
            if time_series_key not in data:
                logger.error(f"Invalid API response: {data}")
                raise ValueError(f"Invalid API response for {symbol}")
                
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            df = df.rename(columns=columns)
            
            # Convert data types
            for col in df.columns:
                if col != 'split':
                    df[col] = pd.to_numeric(df[col])
                    
            # Add symbol column
            df['symbol'] = symbol
            
            # Sort by date (oldest first)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Save to cache
            if use_cache:
                self._save_to_cache(df, cache_file)
                
            # Filter by date
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to get stock data for {symbol}: {e}")
            return pd.DataFrame()
            
    def get_intraday_data(self, symbol: str, interval: str = '15min', 
                       start_date: Optional[str] = None, end_date: Optional[str] = None,
                       use_cache: bool = True) -> pd.DataFrame:
        """
        Get intraday stock data for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        interval : str
            Time interval (1min, 5min, 15min, 30min, 60min)
        start_date : str, optional
            Start date (YYYY-MM-DD)
        end_date : str, optional
            End date (YYYY-MM-DD)
        use_cache : bool
            Whether to use cached data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with intraday stock data
        """
        function = 'TIME_SERIES_INTRADAY'
        output_size = 'full'  # Get full data, will filter later
        
        cache_file = self._get_cache_filename(function, symbol, interval)
        
        # Try to get from cache
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data is not None:
                logger.info(f"Using cached intraday data for {symbol}")
                
                # Filter by date
                if start_date:
                    cached_data = cached_data[cached_data.index >= start_date]
                if end_date:
                    cached_data = cached_data[cached_data.index <= end_date]
                    
                return cached_data
                
        # Make API request
        params = {
            'function': function,
            'symbol': symbol,
            'interval': interval,
            'outputsize': output_size,
            'datatype': 'json'
        }
        
        try:
            data = self._make_request(params)
            
            # Parse time series data
            time_series_key = f'Time Series ({interval})'
            columns = {
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. volume': 'volume'
            }
                
            if time_series_key not in data:
                logger.error(f"Invalid API response: {data}")
                raise ValueError(f"Invalid API response for {symbol}")
                
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            df = df.rename(columns=columns)
            
            # Convert data types
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
                    
            # Add symbol column
            df['symbol'] = symbol
            
            # Sort by date (oldest first)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Save to cache
            if use_cache:
                self._save_to_cache(df, cache_file)
                
            # Filter by date
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to get intraday data for {symbol}: {e}")
            return pd.DataFrame()
            
    def get_technical_indicator(self, symbol: str, indicator: str, 
                             interval: str = 'daily',
                             time_period: int = 14,
                             series_type: str = 'close',
                             use_cache: bool = True,
                             **kwargs) -> pd.DataFrame:
        """
        Get technical indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        indicator : str
            Technical indicator (e.g., SMA, EMA, RSI)
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        time_period : int
            Time period for indicator
        series_type : str
            Series type (open, high, low, close)
        use_cache : bool
            Whether to use cached data
        **kwargs : dict
            Additional parameters for specific indicators
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with technical indicator data
        """
        function = indicator
        
        cache_file = self._get_cache_filename(function, symbol, f"{interval}_{time_period}")
        
        # Try to get from cache
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data is not None:
                logger.info(f"Using cached {indicator} data for {symbol}")
                return cached_data
                
        # Make API request
        params = {
            'function': function,
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type,
            'datatype': 'json'
        }
        
        # Add any additional parameters
        params.update(kwargs)
        
        try:
            data = self._make_request(params)
            
            # Determine the key for the indicator data
            indicator_key = None
            for key in data.keys():
                if 'Technical Analysis' in key:
                    indicator_key = key
                    break
                    
            if not indicator_key:
                logger.error(f"Invalid API response: {data}")
                raise ValueError(f"Invalid API response for {symbol} {indicator}")
                
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data[indicator_key], orient='index')
            
            # Convert data types
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
                    
            # Add symbol column
            df['symbol'] = symbol
            
            # Sort by date (oldest first)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Save to cache
            if use_cache:
                self._save_to_cache(df, cache_file)
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to get {indicator} data for {symbol}: {e}")
            return pd.DataFrame()
            
    def get_company_overview(self, symbol: str, use_cache: bool = True) -> Dict:
        """
        Get company overview for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        use_cache : bool
            Whether to use cached data
            
        Returns:
        --------
        Dict
            Dictionary with company overview data
        """
        function = 'OVERVIEW'
        
        cache_file = self._get_cache_filename(function, symbol)
        
        # Try to get from cache
        if use_cache:
            cached_data = self._get_from_cache(cache_file, max_age_days=30)  # Company data can be cached longer
            if cached_data is not None and not cached_data.empty:
                logger.info(f"Using cached company overview for {symbol}")
                return cached_data.iloc[0].to_dict()
                
        # Make API request
        params = {
            'function': function,
            'symbol': symbol,
        }
        
        try:
            data = self._make_request(params)
            
            # Convert to DataFrame for consistent caching
            df = pd.DataFrame([data])
            
            # Save to cache
            if use_cache:
                self._save_to_cache(df, cache_file)
                
            return data
            
        except Exception as e:
            logger.error(f"Failed to get company overview for {symbol}: {e}")
            return {}
    
    def get_sma(self, symbol: str, time_period: int = 20, 
             interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """
        Get SMA indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        time_period : int
            Time period for indicator
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        series_type : str
            Series type (open, high, low, close)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with SMA data
        """
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='SMA',
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )
        
    def get_ema(self, symbol: str, time_period: int = 20, 
             interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """
        Get EMA indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        time_period : int
            Time period for indicator
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        series_type : str
            Series type (open, high, low, close)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with EMA data
        """
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='EMA',
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )
        
    def get_rsi(self, symbol: str, time_period: int = 14, 
             interval: str = 'daily', series_type: str = 'close') -> pd.DataFrame:
        """
        Get RSI indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        time_period : int
            Time period for indicator
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        series_type : str
            Series type (open, high, low, close)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with RSI data
        """
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='RSI',
            interval=interval,
            time_period=time_period,
            series_type=series_type
        )
        
    def get_macd(self, symbol: str, interval: str = 'daily', 
              series_type: str = 'close', fastperiod: int = 12,
              slowperiod: int = 26, signalperiod: int = 9) -> pd.DataFrame:
        """
        Get MACD indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        series_type : str
            Series type (open, high, low, close)
        fastperiod : int
            Fast period
        slowperiod : int
            Slow period
        signalperiod : int
            Signal period
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with MACD data
        """
        return self.get_technical_indicator(
            symbol=symbol,
            indicator='MACD',
            interval=interval,
            series_type=series_type,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod
        )
        
    def get_bbands(self, symbol: str, time_period: int = 20, 
                interval: str = 'daily', series_type: str = 'close',
                nbdevup: int = 2, nbdevdn: int = 2, matype: int = 0) -> pd.DataFrame:
        """
        Get Bollinger Bands indicator for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        time_period : int
            Time period for indicator
        interval : str
            Time interval (daily, weekly, monthly, 1min, 5min, 15min, 30min, 60min)
        series_type : str
            Series type (open, high, low, close)
        nbdevup : int
            Standard deviation multiplier for upper band
        nbdevdn : int
            Standard deviation multiplier for lower band
        matype : int
            Moving average type (0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with Bollinger Bands data
        """
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
        
    def get_multiple_stocks_data(self, symbols: List[str], start_date: Optional[str] = None,
                              end_date: Optional[str] = None, use_adjusted: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple stocks
        
        Parameters:
        -----------
        symbols : List[str]
            List of stock symbols
        start_date : str, optional
            Start date (YYYY-MM-DD)
        end_date : str, optional
            End date (YYYY-MM-DD)
        use_adjusted : bool
            Whether to use adjusted prices
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary with stock data for each symbol
        """
        result = {}
        for symbol in symbols:
            df = self.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                use_adjusted=use_adjusted
            )
            if not df.empty:
                result[symbol] = df
            
        return result


# Example usage
if __name__ == "__main__":
    # Initialize fetcher
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    fetcher = AlphaVantageFetcher(api_key=api_key)
    
    # Get stock data
    aapl_data = fetcher.get_stock_data(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    if not aapl_data.empty:
        # Print summary
        print("AAPL Data Summary:")
        print(aapl_data.describe())
        
        # Get RSI indicator
        rsi_data = fetcher.get_rsi(
            symbol='AAPL',
            time_period=14,
            interval='daily'
        )
        
        if not rsi_data.empty:
            print("\nRSI Data:")
            print(rsi_data.head())
            
        # Get MACD indicator
        macd_data = fetcher.get_macd(
            symbol='AAPL',
            interval='daily'
        )
        
        if not macd_data.empty:
            print("\nMACD Data:")
            print(macd_data.head())
            
        # Get Bollinger Bands
        bbands_data = fetcher.get_bbands(
            symbol='AAPL',
            time_period=20
        )
        
        if not bbands_data.empty:
            print("\nBollinger Bands Data:")
            print(bbands_data.head())
    else:
        print("Failed to fetch AAPL data. Check your API key and connection.") 