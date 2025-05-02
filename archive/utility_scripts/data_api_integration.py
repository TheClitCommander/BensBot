import os
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AlphaVantageAPI:
    """
    API integration with Alpha Vantage for market data
    """
    
    def __init__(self, api_key=None, base_url="https://www.alphavantage.co/query", 
                 data_dir="data/market_data"):
        """
        Initialize the Alpha Vantage API client.
        
        Args:
            api_key (str): Alpha Vantage API key, defaults to environment variable
            base_url (str): Base URL for Alpha Vantage API
            data_dir (str): Directory to cache data
        """
        # Use API key from environment variable if not provided
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            logger.warning("No Alpha Vantage API key found. Get one at https://www.alphavantage.co/")
            
        self.base_url = base_url
        self.data_dir = data_dir
        self.rate_limit_per_min = 5  # Alpha Vantage free tier limit
        self.last_request_time = 0
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "daily"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "intraday"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "indicators"), exist_ok=True)
        
    def _enforce_rate_limit(self):
        """
        Enforce API rate limiting
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Ensure we don't exceed rate limit (with a small buffer)
        if time_since_last_request < (60 / self.rate_limit_per_min):
            sleep_time = (60 / self.rate_limit_per_min) - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def _api_request(self, params):
        """
        Make a request to the Alpha Vantage API with rate limiting.
        
        Args:
            params (dict): API request parameters
            
        Returns:
            dict: API response data
        """
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        # Enforce rate limit
        self._enforce_rate_limit()
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            
            # Check if the response contains an error message
            if 'Error Message' in data:
                logger.error(f"API Error: {data['Error Message']}")
                return None
                
            # Check for information messages (might indicate API limit reached)
            if 'Information' in data:
                logger.warning(f"API Information: {data['Information']}")
                if 'limit' in data['Information'].lower():
                    # If we hit the API limit, wait a minute before continuing
                    logger.warning("API limit reached, waiting 60 seconds...")
                    time.sleep(60)
                    return None
                    
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return None
            
    def get_daily_data(self, symbol, outputsize="compact", force_refresh=False):
        """
        Get daily stock data for a symbol.
        
        Args:
            symbol (str): Stock symbol
            outputsize (str): 'compact' for last 100 points, 'full' for 20+ years
            force_refresh (bool): Force API call even if cached data exists
            
        Returns:
            pd.DataFrame: Daily stock data
        """
        # Check if we have cached data
        cache_file = os.path.join(self.data_dir, "daily", f"{symbol.upper()}.csv")
        
        # Use cached data if it exists and is recent enough (less than 1 day old)
        if not force_refresh and os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached daily data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._api_request(params)
        
        if not data or 'Time Series (Daily)' not in data:
            logger.error(f"Failed to get daily data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Time Series (Daily)']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns to more convenient names
        df.columns = [c.split('. ')[1] for c in df.columns]
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved daily data for {symbol} to cache")
        
        return df
        
    def get_intraday_data(self, symbol, interval="5min", outputsize="compact", force_refresh=False):
        """
        Get intraday stock data for a symbol.
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval between data points (1min, 5min, 15min, 30min, 60min)
            outputsize (str): 'compact' for last 100 points, 'full' for extended history
            force_refresh (bool): Force API call even if cached data exists
            
        Returns:
            pd.DataFrame: Intraday stock data
        """
        # Check if we have cached data
        cache_file = os.path.join(self.data_dir, "intraday", f"{symbol.upper()}_{interval}.csv")
        
        # Use cached data if it exists and is recent enough
        if not force_refresh and os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            cache_age = time.time() - file_mod_time
            
            # For 1min and 5min data, cache should be less than 10 minutes old
            # For other intervals, cache should be less than 1 hour old
            max_cache_age = 3600  # Default: 1 hour
            if interval in ["1min", "5min"]:
                max_cache_age = 600  # 10 minutes
                
            if cache_age < max_cache_age:
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached intraday data for {symbol} ({interval})")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached intraday data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._api_request(params)
        
        if not data or f'Time Series ({interval})' not in data:
            logger.error(f"Failed to get intraday data for {symbol} ({interval})")
            return None
            
        # Convert to DataFrame
        time_series = data[f'Time Series ({interval})']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns to more convenient names
        df.columns = [c.split('. ')[1] for c in df.columns]
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved intraday data for {symbol} ({interval}) to cache")
        
        return df
        
    def get_sma(self, symbol, time_period=20, series_type="close"):
        """
        Get Simple Moving Average (SMA) technical indicator.
        
        Args:
            symbol (str): Stock symbol
            time_period (int): Number of data points used to calculate the SMA
            series_type (str): Price type to use (close, open, high, low)
            
        Returns:
            pd.DataFrame: SMA data
        """
        # Check if we have cached data
        cache_file = os.path.join(
            self.data_dir, 
            "indicators", 
            f"{symbol.upper()}_SMA_{time_period}_{series_type}.csv"
        )
        
        # Use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached SMA data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached SMA data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'SMA',
            'symbol': symbol,
            'interval': 'daily',
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._api_request(params)
        
        if not data or 'Technical Analysis: SMA' not in data:
            logger.error(f"Failed to get SMA data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Technical Analysis: SMA']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved SMA data for {symbol} to cache")
        
        return df
        
    def get_ema(self, symbol, time_period=20, series_type="close"):
        """
        Get Exponential Moving Average (EMA) technical indicator.
        
        Args:
            symbol (str): Stock symbol
            time_period (int): Number of data points used to calculate the EMA
            series_type (str): Price type to use (close, open, high, low)
            
        Returns:
            pd.DataFrame: EMA data
        """
        # Check if we have cached data
        cache_file = os.path.join(
            self.data_dir, 
            "indicators", 
            f"{symbol.upper()}_EMA_{time_period}_{series_type}.csv"
        )
        
        # Use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached EMA data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached EMA data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'EMA',
            'symbol': symbol,
            'interval': 'daily',
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._api_request(params)
        
        if not data or 'Technical Analysis: EMA' not in data:
            logger.error(f"Failed to get EMA data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Technical Analysis: EMA']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved EMA data for {symbol} to cache")
        
        return df
        
    def get_rsi(self, symbol, time_period=14, series_type="close"):
        """
        Get Relative Strength Index (RSI) technical indicator.
        
        Args:
            symbol (str): Stock symbol
            time_period (int): Number of data points used to calculate the RSI
            series_type (str): Price type to use (close, open, high, low)
            
        Returns:
            pd.DataFrame: RSI data
        """
        # Check if we have cached data
        cache_file = os.path.join(
            self.data_dir, 
            "indicators", 
            f"{symbol.upper()}_RSI_{time_period}_{series_type}.csv"
        )
        
        # Use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached RSI data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached RSI data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': 'daily',
            'time_period': time_period,
            'series_type': series_type
        }
        
        data = self._api_request(params)
        
        if not data or 'Technical Analysis: RSI' not in data:
            logger.error(f"Failed to get RSI data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Technical Analysis: RSI']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved RSI data for {symbol} to cache")
        
        return df
        
    def get_macd(self, symbol, series_type="close", 
                fast_period=12, slow_period=26, signal_period=9):
        """
        Get Moving Average Convergence Divergence (MACD) technical indicator.
        
        Args:
            symbol (str): Stock symbol
            series_type (str): Price type to use (close, open, high, low)
            fast_period (int): Fast period
            slow_period (int): Slow period
            signal_period (int): Signal period
            
        Returns:
            pd.DataFrame: MACD data
        """
        # Check if we have cached data
        cache_file = os.path.join(
            self.data_dir, 
            "indicators", 
            f"{symbol.upper()}_MACD_{fast_period}_{slow_period}_{signal_period}_{series_type}.csv"
        )
        
        # Use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached MACD data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached MACD data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': 'daily',
            'series_type': series_type,
            'fastperiod': fast_period,
            'slowperiod': slow_period,
            'signalperiod': signal_period
        }
        
        data = self._api_request(params)
        
        if not data or 'Technical Analysis: MACD' not in data:
            logger.error(f"Failed to get MACD data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Technical Analysis: MACD']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved MACD data for {symbol} to cache")
        
        return df
        
    def get_bbands(self, symbol, time_period=20, series_type="close",
                 nbdevup=2, nbdevdn=2, matype=0):
        """
        Get Bollinger Bands (BBANDS) technical indicator.
        
        Args:
            symbol (str): Stock symbol
            time_period (int): Number of data points used to calculate the BBANDS
            series_type (str): Price type to use (close, open, high, low)
            nbdevup (int): Standard deviation multiplier for upper band
            nbdevdn (int): Standard deviation multiplier for lower band
            matype (int): Moving average type (0=SMA, 1=EMA, etc.)
            
        Returns:
            pd.DataFrame: Bollinger Bands data
        """
        # Check if we have cached data
        cache_file = os.path.join(
            self.data_dir, 
            "indicators", 
            f"{symbol.upper()}_BBANDS_{time_period}_{nbdevup}_{nbdevdn}_{matype}_{series_type}.csv"
        )
        
        # Use cached data if it exists and is less than 1 day old
        if os.path.exists(cache_file):
            file_mod_time = os.path.getmtime(cache_file)
            if (time.time() - file_mod_time) < 86400:  # Less than 1 day old
                try:
                    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    logger.info(f"Loaded cached Bollinger Bands data for {symbol}")
                    return df
                except Exception as e:
                    logger.warning(f"Error reading cached Bollinger Bands data for {symbol}: {str(e)}")
        
        # If no valid cache, make API request
        params = {
            'function': 'BBANDS',
            'symbol': symbol,
            'interval': 'daily',
            'time_period': time_period,
            'series_type': series_type,
            'nbdevup': nbdevup,
            'nbdevdn': nbdevdn,
            'matype': matype
        }
        
        data = self._api_request(params)
        
        if not data or 'Technical Analysis: BBANDS' not in data:
            logger.error(f"Failed to get Bollinger Bands data for {symbol}")
            return None
            
        # Convert to DataFrame
        time_series = data['Technical Analysis: BBANDS']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Convert strings to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Sort by date
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to cache
        df.to_csv(cache_file)
        logger.info(f"Saved Bollinger Bands data for {symbol} to cache")
        
        return df
        
    def get_indicators_for_symbol(self, symbol):
        """
        Get a set of common technical indicators for a symbol.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Dictionary of technical indicators
        """
        # Get price data
        price_data = self.get_daily_data(symbol)
        
        if price_data is None:
            logger.error(f"Failed to get price data for {symbol}")
            return None
            
        # Get various indicators
        indicators = {
            'price': price_data,
            'sma_20': self.get_sma(symbol, time_period=20),
            'sma_50': self.get_sma(symbol, time_period=50),
            'sma_200': self.get_sma(symbol, time_period=200),
            'ema_12': self.get_ema(symbol, time_period=12),
            'ema_26': self.get_ema(symbol, time_period=26),
            'rsi_14': self.get_rsi(symbol, time_period=14),
            'macd': self.get_macd(symbol),
            'bbands': self.get_bbands(symbol, time_period=20)
        }
        
        # Remove any failed indicator requests
        indicators = {k: v for k, v in indicators.items() if v is not None}
        
        logger.info(f"Retrieved {len(indicators)} indicators for {symbol}")
        
        return indicators
        
    def merge_indicators(self, indicators):
        """
        Merge multiple indicators into a single DataFrame.
        
        Args:
            indicators (dict): Dictionary of technical indicators
            
        Returns:
            pd.DataFrame: Merged DataFrame with all indicators
        """
        if not indicators or 'price' not in indicators:
            logger.error("No price data provided for merging indicators")
            return None
            
        # Start with price data as the base
        df = indicators['price'].copy()
        
        # Add each indicator
        for name, indicator_df in indicators.items():
            if name == 'price':
                continue
                
            if indicator_df is None:
                continue
                
            # For each column in the indicator DataFrame
            for col in indicator_df.columns:
                # Create a unique column name
                new_col = f"{name}_{col}" if len(indicator_df.columns) > 1 else name
                
                # Add to main DataFrame
                df[new_col] = np.nan
                
                # Find matching dates and add values
                for date in indicator_df.index:
                    if date in df.index:
                        df.loc[date, new_col] = indicator_df.loc[date, col]
                        
        logger.info(f"Merged {len(indicators)} indicators into a DataFrame with {len(df.columns)} columns")
        
        return df


# Example usage
if __name__ == "__main__":
    # Check if API key exists in environment
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("Warning: No API key found in environment variables.")
        print("Please get a free API key from https://www.alphavantage.co/support/#api-key")
        print("Then set it in your environment as ALPHA_VANTAGE_API_KEY or pass it to the constructor.")
        
    # Create API client
    api = AlphaVantageAPI()
    
    # Example: Get daily data for AAPL
    symbol = "AAPL"
    print(f"\nGetting daily data for {symbol}...")
    daily_data = api.get_daily_data(symbol)
    if daily_data is not None:
        print(f"Retrieved {len(daily_data)} days of data for {symbol}")
        print(daily_data.tail())
    
    # Example: Get intraday data
    print(f"\nGetting intraday data for {symbol}...")
    intraday_data = api.get_intraday_data(symbol, interval="5min")
    if intraday_data is not None:
        print(f"Retrieved {len(intraday_data)} intraday data points for {symbol}")
        print(intraday_data.tail())
    
    # Example: Get SMA indicator
    print(f"\nGetting SMA(20) for {symbol}...")
    sma_data = api.get_sma(symbol, time_period=20)
    if sma_data is not None:
        print(f"Retrieved {len(sma_data)} SMA data points for {symbol}")
        print(sma_data.tail())
    
    # Example: Get RSI indicator
    print(f"\nGetting RSI(14) for {symbol}...")
    rsi_data = api.get_rsi(symbol, time_period=14)
    if rsi_data is not None:
        print(f"Retrieved {len(rsi_data)} RSI data points for {symbol}")
        print(rsi_data.tail())
    
    # Example: Get multiple indicators for a symbol
    print(f"\nGetting all indicators for {symbol}...")
    indicators = api.get_indicators_for_symbol(symbol)
    if indicators:
        print(f"Retrieved {len(indicators)} indicators for {symbol}")
        
        # Merge indicators
        merged_data = api.merge_indicators(indicators)
        if merged_data is not None:
            print(f"Merged data has {len(merged_data.columns)} columns")
            print(merged_data.tail())
            
            # Save merged data to CSV
            output_file = f"{symbol}_merged_indicators.csv"
            merged_data.to_csv(output_file)
            print(f"Saved merged indicators to {output_file}") 