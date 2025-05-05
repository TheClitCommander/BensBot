#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD Strategy

This strategy generates buy signals when the MACD line crosses above the signal line
and sell signals when the MACD line crosses below the signal line.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class MACD:
    """
    Moving Average Convergence Divergence (MACD) Strategy.
    
    Generates buy signals when MACD line crosses above signal line,
    and sell signals when MACD line crosses below signal line.
    """
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Initialize the MACD strategy.
        
        Parameters:
        -----------
        fast_period : int
            The window length for the fast exponential moving average
        slow_period : int
            The window length for the slow exponential moving average
        signal_period : int
            The window length for the signal exponential moving average
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = f"MACD_{fast_period}_{slow_period}_{signal_period}"
        
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, data):
        """
        Generate trading signals based on MACD crossover.
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Historical market data including at least 'close' prices
            
        Returns:
        --------
        pandas.DataFrame
            Original data with additional columns for signals
        """
        # Make a copy of the data to avoid modifying the original
        df = data.copy()
        
        # Check if we have enough data
        if len(df) < self.slow_period + self.signal_period:
            logger.warning(f"Data length ({len(df)}) is less than required " 
                          f"({self.slow_period + self.signal_period})")
            return df
        
        try:
            # Calculate fast and slow EMAs
            df['fast_ema'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
            df['slow_ema'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
            
            # Calculate MACD line
            df['macd_line'] = df['fast_ema'] - df['slow_ema']
            
            # Calculate signal line
            df['signal_line'] = df['macd_line'].ewm(span=self.signal_period, adjust=False).mean()
            
            # Calculate histogram (difference between MACD line and signal line)
            df['histogram'] = df['macd_line'] - df['signal_line']
            
            # Initialize signal column
            df['signal'] = 0
            
            # Generate signals: 1 for buy, -1 for sell
            # Buy when MACD line crosses above signal line
            # Sell when MACD line crosses below signal line
            df['signal'] = np.where(
                df['macd_line'] > df['signal_line'], 1, 
                np.where(df['macd_line'] < df['signal_line'], -1, 0)
            )
            
            # Generate position column (to identify entry/exit points)
            # Position changes when signal changes
            df['position'] = df['signal'].diff().fillna(0)
            
            # Entry signal: 1 when position becomes 2
            # Exit signal: -1 when position becomes -2
            df['entry'] = np.where(df['position'] > 0, 1, 0)
            df['exit'] = np.where(df['position'] < 0, 1, 0)
            
            # Log signal stats
            num_entries = df['entry'].sum()
            num_exits = df['exit'].sum()
            logger.info(f"Generated {num_entries} buy signals and {num_exits} sell signals")
            
            return df
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return df
    
    def get_parameters(self):
        """
        Return the strategy parameters.
        
        Returns:
        --------
        dict
            Dictionary containing strategy parameters
        """
        return {
            'name': self.name,
            'type': 'MACD',
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'signal_period': self.signal_period
        }


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    import yfinance as yf
    
    # Download sample data
    symbol = 'AAPL'
    data = yf.download(symbol, start='2022-01-01', end='2023-01-01')
    
    # Initialize strategy
    strategy = MACD(fast_period=12, slow_period=26, signal_period=9)
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    # Print summary
    print(f"\nStrategy: {strategy.name}")
    print(f"Data points: {len(signals)}")
    print(f"Buy signals: {signals['entry'].sum()}")
    print(f"Sell signals: {signals['exit'].sum()}")
    
    # Plot the results
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 10))
        
        # Plot close price
        plt.subplot(3, 1, 1)
        plt.plot(signals.index, signals['close'], label='Close Price')
        plt.title(f'{symbol} - {strategy.name}')
        plt.legend()
        plt.grid(True)
        
        # Plot MACD components
        plt.subplot(3, 1, 2)
        plt.plot(signals.index, signals['macd_line'], label='MACD Line')
        plt.plot(signals.index, signals['signal_line'], label='Signal Line')
        
        # Plot histogram as bar chart
        plt.bar(signals.index, signals['histogram'], label='Histogram', alpha=0.5)
        
        # Plot buy and sell signals
        plt.plot(signals.loc[signals['entry'] == 1].index, 
                signals.loc[signals['entry'] == 1]['macd_line'], 
                '^', markersize=10, color='g', label='Buy Signal')
        
        plt.plot(signals.loc[signals['exit'] == 1].index, 
                signals.loc[signals['exit'] == 1]['macd_line'], 
                'v', markersize=10, color='r', label='Sell Signal')
        
        plt.title('MACD Indicator')
        plt.legend()
        plt.grid(True)
        
        # Plot signal and position
        plt.subplot(3, 1, 3)
        plt.plot(signals.index, signals['signal'], label='Signal (1 = Long, -1 = Short)')
        plt.title('Trading Signals')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        logger.error(f"Error plotting results: {e}") 