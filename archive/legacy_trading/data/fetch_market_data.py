#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market data fetching utilities for the trading backtester.
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path

# Import the AlphaVantage client
from trading.data.alpha_vantage_client import AlphaVantageClient
from trading.data.mock_data import get_mock_stock_data, get_multiple_mock_data

# Set up logging
logger = logging.getLogger(__name__)

def fetch_market_data(
    symbols: Union[str, List[str]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = 'daily',
    adjusted: bool = True,
    use_mock: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch market data for one or more symbols.
    
    Parameters:
    -----------
    symbols : str or List[str]
        Symbol or list of symbols to fetch data for
    start_date : str, optional
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
    interval : str
        Time interval ('daily', 'weekly', 'monthly', 'intraday')
    adjusted : bool
        Whether to use adjusted prices
    use_mock : bool
        Whether to use mock data instead of API
    api_key : str, optional
        Alpha Vantage API key
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary mapping symbols to DataFrames with market data
    """
    # Convert single symbol to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    # Default to recent data if dates not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        # Default to one year of data
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Use mock data if requested
    if use_mock:
        logger.info(f"Using mock data for {len(symbols)} symbols")
        return get_multiple_mock_data(symbols, start_date, end_date)
    
    # Initialize Alpha Vantage client
    try:
        client = AlphaVantageClient(api_key=api_key)
        logger.info(f"Initialized Alpha Vantage client")
    except Exception as e:
        logger.error(f"Failed to initialize Alpha Vantage client: {e}")
        logger.info("Falling back to mock data")
        return get_multiple_mock_data(symbols, start_date, end_date)
    
    # Fetch data for each symbol
    result = {}
    
    for symbol in symbols:
        try:
            logger.info(f"Fetching {interval} data for {symbol} from {start_date} to {end_date}")
            
            if interval == 'daily':
                df = client.get_daily(
                    symbol=symbol,
                    adjusted=adjusted,
                    outputsize='full',
                    start_date=start_date,
                    end_date=end_date
                )
            elif interval == 'weekly':
                df = client.get_weekly(
                    symbol=symbol,
                    adjusted=adjusted,
                    start_date=start_date,
                    end_date=end_date
                )
            elif interval == 'monthly':
                df = client.get_monthly(
                    symbol=symbol,
                    adjusted=adjusted,
                    start_date=start_date,
                    end_date=end_date
                )
            elif interval == 'intraday':
                df = client.get_intraday(
                    symbol=symbol,
                    interval='15min',  # Default to 15-minute intervals
                    outputsize='full',
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                raise ValueError(f"Unsupported interval: {interval}")
            
            if not df.empty:
                result[symbol] = df
                logger.info(f"Retrieved {len(df)} data points for {symbol}")
            else:
                logger.warning(f"No data retrieved for {symbol}, using mock data instead")
                result[symbol] = get_mock_stock_data(symbol, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            logger.info(f"Using mock data for {symbol} due to error")
            result[symbol] = get_mock_stock_data(symbol, start_date, end_date)
    
    return result

def fetch_technical_indicators(
    symbols: Union[str, List[str]],
    indicators: List[Dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_mock: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Fetch technical indicators for one or more symbols.
    
    Parameters:
    -----------
    symbols : str or List[str]
        Symbol or list of symbols to fetch data for
    indicators : List[Dict[str, Any]]
        List of indicator specifications with keys:
        - name: Indicator name (e.g., 'SMA', 'RSI', 'BBANDS')
        - params: Dictionary of parameters for the indicator
    start_date : str, optional
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
    use_mock : bool
        Whether to use mock data instead of API
    api_key : str, optional
        Alpha Vantage API key
        
    Returns:
    --------
    Dict[str, Dict[str, pd.DataFrame]]
        Dictionary mapping symbols to dictionaries of indicator DataFrames
    """
    # Convert single symbol to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    # If using mock data, return empty indicators
    if use_mock:
        logger.info(f"Mock data requested for indicators, returning empty result")
        return {symbol: {} for symbol in symbols}
    
    # Initialize Alpha Vantage client
    try:
        client = AlphaVantageClient(api_key=api_key)
        logger.info(f"Initialized Alpha Vantage client for indicators")
    except Exception as e:
        logger.error(f"Failed to initialize Alpha Vantage client: {e}")
        return {symbol: {} for symbol in symbols}
    
    # Fetch indicators for each symbol
    result = {}
    
    for symbol in symbols:
        result[symbol] = {}
        
        for indicator_spec in indicators:
            indicator_name = indicator_spec.get('name')
            params = indicator_spec.get('params', {})
            
            try:
                logger.info(f"Fetching {indicator_name} for {symbol}")
                
                # Common indicators
                if indicator_name == 'SMA':
                    df = client.get_sma(
                        symbol=symbol,
                        time_period=params.get('time_period', 20),
                        interval=params.get('interval', 'daily'),
                        series_type=params.get('series_type', 'close')
                    )
                elif indicator_name == 'EMA':
                    df = client.get_ema(
                        symbol=symbol,
                        time_period=params.get('time_period', 20),
                        interval=params.get('interval', 'daily'),
                        series_type=params.get('series_type', 'close')
                    )
                elif indicator_name == 'RSI':
                    df = client.get_rsi(
                        symbol=symbol,
                        time_period=params.get('time_period', 14),
                        interval=params.get('interval', 'daily'),
                        series_type=params.get('series_type', 'close')
                    )
                elif indicator_name == 'MACD':
                    df = client.get_macd(
                        symbol=symbol,
                        interval=params.get('interval', 'daily'),
                        series_type=params.get('series_type', 'close'),
                        fastperiod=params.get('fastperiod', 12),
                        slowperiod=params.get('slowperiod', 26),
                        signalperiod=params.get('signalperiod', 9)
                    )
                elif indicator_name == 'BBANDS':
                    df = client.get_bbands(
                        symbol=symbol,
                        time_period=params.get('time_period', 20),
                        interval=params.get('interval', 'daily'),
                        series_type=params.get('series_type', 'close'),
                        nbdevup=params.get('nbdevup', 2),
                        nbdevdn=params.get('nbdevdn', 2),
                        matype=params.get('matype', 0)
                    )
                else:
                    # Generic indicator fetching
                    df = client.get_technical_indicator(
                        symbol=symbol,
                        indicator=indicator_name,
                        **params
                    )
                
                # Filter by date if needed
                if start_date or end_date:
                    if start_date:
                        df = df[df.index >= pd.to_datetime(start_date)]
                    if end_date:
                        df = df[df.index <= pd.to_datetime(end_date)]
                
                result[symbol][indicator_name] = df
                logger.info(f"Retrieved {len(df)} {indicator_name} data points for {symbol}")
                
            except Exception as e:
                logger.error(f"Error fetching {indicator_name} for {symbol}: {e}")
    
    return result

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Fetch daily data for multiple symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    # Get market data
    market_data = fetch_market_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval='daily',
        adjusted=True,
        use_mock=True  # Use mock data for testing
    )
    
    # Print summary of retrieved data
    for symbol, df in market_data.items():
        print(f"\n{symbol} data summary:")
        print(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
        print(f"Number of data points: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        print(f"Sample data:")
        print(df.head(3))
    
    # Example: Fetch technical indicators
    indicators = [
        {'name': 'SMA', 'params': {'time_period': 20}},
        {'name': 'RSI', 'params': {'time_period': 14}},
        {'name': 'BBANDS', 'params': {'time_period': 20}}
    ]
    
    # Get indicators (using mock=True to avoid API calls in this example)
    indicator_data = fetch_technical_indicators(
        symbols=symbols[0],  # Just for AAPL
        indicators=indicators,
        start_date=start_date,
        end_date=end_date,
        use_mock=True
    )
    
    # If we had actual indicator data, we could print it like this:
    # for symbol, indicators_dict in indicator_data.items():
    #     for indicator_name, df in indicators_dict.items():
    #         print(f"\n{symbol} {indicator_name} data summary:")
    #         print(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
    #         print(f"Number of data points: {len(df)}")
    #         print(f"Columns: {', '.join(df.columns)}")
    #         print(f"Sample data:")
    #         print(df.head(3)) 