#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Validation Utilities

This module provides functions to validate market data quality and completeness
before running backtests to ensure reliable results.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def validate_data(data: pd.DataFrame, symbol: str, min_required_bars: int = 100) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the quality and completeness of market data.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Market data to validate
    symbol : str
        Symbol for the data
    min_required_bars : int
        Minimum number of bars required for reliable backtesting
        
    Returns:
    --------
    Tuple[bool, Dict[str, Any]]
        (is_valid, validation_results) tuple where is_valid is a boolean indicating
        if the data is valid for backtesting, and validation_results is a dictionary
        with detailed validation metrics
    """
    results = {
        'symbol': symbol,
        'is_valid': True,
        'warnings': [],
        'length': len(data),
        'start_date': data.index.min() if not data.empty else None,
        'end_date': data.index.max() if not data.empty else None,
        'missing_values': {},
        'duplicated_dates': 0,
        'price_anomalies': 0,
        'data_gaps': 0,
        'summary': ''
    }
    
    # Check if dataframe is empty
    if data.empty:
        results['is_valid'] = False
        results['warnings'].append("Data is empty")
        results['summary'] = "Invalid: Empty dataset"
        return False, results
    
    # Check data length
    if len(data) < min_required_bars:
        results['is_valid'] = False
        results['warnings'].append(f"Insufficient data length: {len(data)} bars (minimum {min_required_bars} required)")
    
    # Check for required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        results['is_valid'] = False
        results['warnings'].append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Check for missing values
    for column in data.columns:
        missing_count = data[column].isna().sum()
        if missing_count > 0:
            results['missing_values'][column] = missing_count
            if column in required_columns:
                results['warnings'].append(f"Missing values in {column}: {missing_count} rows")
                if missing_count > len(data) * 0.05:  # More than 5% missing
                    results['is_valid'] = False
    
    # Check for duplicated dates
    duplicated_dates = data.index.duplicated().sum()
    results['duplicated_dates'] = duplicated_dates
    if duplicated_dates > 0:
        results['warnings'].append(f"Duplicated dates: {duplicated_dates} instances")
        results['is_valid'] = False
    
    # Check for price anomalies
    if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
        # High should be >= max(open, close)
        high_anomalies = (data['high'] < data[['open', 'close']].max(axis=1)).sum()
        
        # Low should be <= min(open, close)
        low_anomalies = (data['low'] > data[['open', 'close']].min(axis=1)).sum()
        
        # High should be >= Low
        hl_anomalies = (data['high'] < data['low']).sum()
        
        price_anomalies = high_anomalies + low_anomalies + hl_anomalies
        results['price_anomalies'] = price_anomalies
        
        if price_anomalies > 0:
            results['warnings'].append(f"Price anomalies detected: {price_anomalies} instances")
            if price_anomalies > len(data) * 0.01:  # More than 1% anomalies
                results['is_valid'] = False
    
    # Check for gaps in time series
    if len(data) > 1:
        # Calculate the expected interval between dates
        # This assumes the most common interval is the correct one
        date_diffs = pd.Series(np.diff(data.index.values) / np.timedelta64(1, 'D')).value_counts()
        expected_interval = date_diffs.idxmax()  # Most common interval in days
        
        # Find gaps larger than the expected interval
        gaps = []
        for i in range(1, len(data)):
            diff_days = (data.index[i] - data.index[i-1]) / np.timedelta64(1, 'D')
            if diff_days > expected_interval * 2:  # Gap is more than twice the expected interval
                gaps.append((data.index[i-1], data.index[i], diff_days))
        
        results['data_gaps'] = len(gaps)
        if len(gaps) > 0:
            gap_info = [f"{start.date()} to {end.date()} ({days:.1f} days)" for start, end, days in gaps[:3]]
            results['warnings'].append(f"Data gaps detected: {len(gaps)} instances")
            results['warnings'].append(f"Example gaps: {', '.join(gap_info)}")
            
            # Only invalidate if there are significant gaps
            if len(gaps) > 5 or any(days > 30 for _, _, days in gaps):
                results['is_valid'] = False
    
    # Check for extreme price movements (potential data errors)
    if 'close' in data.columns and len(data) > 1:
        returns = data['close'].pct_change()
        extreme_returns = returns[abs(returns) > 0.2].count()  # 20% daily move is extreme
        
        if extreme_returns > 0:
            results['warnings'].append(f"Extreme price movements: {extreme_returns} instances of >20% daily moves")
            if extreme_returns > 5:  # Several extreme moves might indicate data issues
                results['warnings'].append("Multiple extreme price movements may indicate data quality issues")
    
    # Generate summary
    if results['is_valid']:
        results['summary'] = "Valid: Data passed quality checks"
        if results['warnings']:
            results['summary'] += f" with {len(results['warnings'])} warnings"
    else:
        results['summary'] = f"Invalid: {len(results['warnings'])} data quality issues detected"
    
    return results['is_valid'], results


def validate_dataset(data_dict: Dict[str, pd.DataFrame], min_required_bars: int = 100) -> Dict[str, Any]:
    """
    Validate a dictionary of market data for multiple symbols.
    
    Parameters:
    -----------
    data_dict : Dict[str, pd.DataFrame]
        Dictionary mapping symbols to their market data
    min_required_bars : int
        Minimum number of bars required for reliable backtesting
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary with validation results for each symbol and overall summary
    """
    overall_results = {
        'symbols_total': len(data_dict),
        'symbols_valid': 0,
        'symbols_invalid': 0,
        'symbol_results': {},
        'is_valid_for_backtest': True,
        'summary': ""
    }
    
    # Validate each symbol's data
    for symbol, data in data_dict.items():
        is_valid, validation_results = validate_data(data, symbol, min_required_bars)
        overall_results['symbol_results'][symbol] = validation_results
        
        if is_valid:
            overall_results['symbols_valid'] += 1
        else:
            overall_results['symbols_invalid'] += 1
            overall_results['is_valid_for_backtest'] = False
    
    # Generate overall summary
    if overall_results['symbols_invalid'] == 0:
        overall_results['summary'] = f"All {overall_results['symbols_total']} symbols passed validation checks"
    else:
        overall_results['summary'] = (
            f"{overall_results['symbols_invalid']} out of {overall_results['symbols_total']} "
            f"symbols failed validation checks"
        )
    
    return overall_results


def prepare_data_for_backtest(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Prepare data for backtesting by cleaning and handling common issues.
    
    Parameters:
    -----------
    data_dict : Dict[str, pd.DataFrame]
        Dictionary mapping symbols to their market data
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary with cleaned data ready for backtesting
    """
    cleaned_data = {}
    
    for symbol, data in data_dict.items():
        if data.empty:
            logger.warning(f"Empty dataset for {symbol}, skipping")
            continue
        
        # Make a copy to avoid modifying original data
        df = data.copy()
        
        # Handle missing values in required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col in df.columns and df[col].isna().any():
                # Forward fill first (use previous values)
                df[col] = df[col].fillna(method='ffill')
                # Then backward fill any remaining NAs at the beginning
                df[col] = df[col].fillna(method='bfill')
        
        # Remove duplicated dates
        if df.index.duplicated().any():
            logger.warning(f"Removing {df.index.duplicated().sum()} duplicated dates for {symbol}")
            df = df[~df.index.duplicated(keep='first')]
        
        # Handle price anomalies
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # Fix high values that are less than max(open, close)
            max_oc = df[['open', 'close']].max(axis=1)
            invalid_high = df['high'] < max_oc
            if invalid_high.any():
                logger.warning(f"Fixing {invalid_high.sum()} invalid high values for {symbol}")
                df.loc[invalid_high, 'high'] = max_oc[invalid_high] * 1.0001  # Slightly higher
            
            # Fix low values that are greater than min(open, close)
            min_oc = df[['open', 'close']].min(axis=1)
            invalid_low = df['low'] > min_oc
            if invalid_low.any():
                logger.warning(f"Fixing {invalid_low.sum()} invalid low values for {symbol}")
                df.loc[invalid_low, 'low'] = min_oc[invalid_low] * 0.9999  # Slightly lower
        
        # Sort by date
        df = df.sort_index()
        
        # Store the cleaned data
        cleaned_data[symbol] = df
        
        logger.info(f"Prepared data for {symbol}: {len(df)} bars from {df.index.min().date()} to {df.index.max().date()}")
    
    return cleaned_data


def analyze_strategy_data_requirements(strategy_obj: Any) -> Dict[str, Any]:
    """
    Analyze the data requirements for a given strategy.
    
    Parameters:
    -----------
    strategy_obj : Any
        Strategy object with get_parameters method
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary with the strategy's data requirements
    """
    requirements = {
        'strategy_name': getattr(strategy_obj, 'name', 'Unknown Strategy'),
        'min_bars': 100,  # Default minimum
        'required_columns': ['open', 'high', 'low', 'close', 'volume'],
        'lookback_periods': [],
        'description': 'Base data requirements'
    }
    
    # Get strategy parameters
    try:
        params = strategy_obj.get_parameters()
        
        # Add strategy parameters to requirements
        requirements['parameters'] = params
        
        # Determine minimum bars based on strategy type
        if getattr(strategy_obj, 'type', '') == 'SMA Crossover':
            # For SMA, we need at least the longest window for proper calculation
            long_window = params.get('long_window', 50)
            # Add some extra bars for signal generation
            requirements['min_bars'] = long_window + 20
            requirements['lookback_periods'].append(long_window)
            requirements['description'] = f"SMA Crossover strategy requires at least {long_window} bars for calculation"
            
        elif hasattr(strategy_obj, 'macd_strategy') and hasattr(strategy_obj, 'rsi_strategy'):
            # For combined strategy, take the max requirement of both components
            macd_slow = params.get('macd_slow_period', 26)
            rsi_period = params.get('rsi_period', 14)
            
            requirements['min_bars'] = max(macd_slow, rsi_period) + 30  # Extra bars for signal generation
            requirements['lookback_periods'].extend([macd_slow, rsi_period])
            requirements['description'] = f"Combined strategy requires at least {requirements['min_bars']} bars for calculation"
            
        elif 'MACD' in getattr(strategy_obj, 'name', ''):
            # For MACD, we need at least the slow period + signal period
            macd_slow = params.get('slow_period', 26)
            macd_signal = params.get('signal_period', 9)
            
            requirements['min_bars'] = macd_slow + macd_signal + 10
            requirements['lookback_periods'].extend([macd_slow, macd_signal])
            requirements['description'] = f"MACD strategy requires at least {requirements['min_bars']} bars for calculation"
            
        elif 'RSI' in getattr(strategy_obj, 'name', ''):
            # For RSI, we need at least the RSI period
            rsi_period = params.get('period', 14)
            
            requirements['min_bars'] = rsi_period + 10
            requirements['lookback_periods'].append(rsi_period)
            requirements['description'] = f"RSI strategy requires at least {requirements['min_bars']} bars for calculation"
            
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not analyze strategy requirements: {e}")
    
    return requirements


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    
    # Import test utilities
    from trading.data.fetch_market_data import fetch_market_data
    from trading.strategies.macd import MACD
    from trading.strategies.rsi import RSI
    from trading.strategies.combined import CombinedStrategy
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test data validation
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    start_date = '2022-01-01'
    end_date = '2023-01-01'
    
    # Fetch test data
    print(f"Fetching data for {', '.join(symbols)}...")
    data = fetch_market_data(symbols, start_date, end_date, use_mock=True)
    
    # Validate the data
    print("\nValidating dataset...")
    validation_results = validate_dataset(data)
    
    print(f"\nValidation Summary: {validation_results['summary']}")
    for symbol, result in validation_results['symbol_results'].items():
        print(f"\n{symbol} ({result['length']} bars from {result['start_date'].date()} to {result['end_date'].date()}):")
        print(f"  Status: {'Valid' if result['is_valid'] else 'Invalid'}")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    # Analyze strategy requirements
    strategies = {
        'MACD': MACD(),
        'RSI': RSI(),
        'Combined': CombinedStrategy()
    }
    
    print("\nStrategy Data Requirements:")
    for name, strategy in strategies.items():
        req = analyze_strategy_data_requirements(strategy)
        print(f"\n{name} Strategy:")
        print(f"  Minimum bars required: {req['min_bars']}")
        print(f"  Lookback periods: {req['lookback_periods']}")
        print(f"  Description: {req['description']}") 