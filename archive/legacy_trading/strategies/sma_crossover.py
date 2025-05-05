#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMA Crossover Strategy

This strategy generates buy signals when a short-term SMA crosses above a long-term SMA
and sell signals when the short-term SMA crosses below the long-term SMA.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class SMACrossover:
    """
    Simple Moving Average Crossover Strategy.
    
    Generates buy signals when short SMA crosses above long SMA,
    and sell signals when short SMA crosses below long SMA.
    """
    
    def __init__(self, short_window=20, long_window=50):
        """
        Initialize the SMA Crossover strategy.
        
        Parameters:
        -----------
        short_window : int
            The window length for the short-term moving average
        long_window : int
            The window length for the long-term moving average
        """
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"SMA_Crossover_{short_window}_{long_window}"
        
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, data):
        """
        Generate trading signals based on SMA crossover.
        
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
        if len(df) < self.long_window:
            logger.warning(f"Data length ({len(df)}) is less than required for long window ({self.long_window})")
            return df
        
        try:
            # Calculate short and long SMAs
            df['short_sma'] = df['close'].rolling(window=self.short_window).mean()
            df['long_sma'] = df['close'].rolling(window=self.long_window).mean()
            
            # Initialize signal column
            df['signal'] = 0
            
            # Generate signals: 1 for buy, -1 for sell
            # Buy when short SMA crosses above long SMA
            # Sell when short SMA crosses below long SMA
            df['signal'] = np.where(
                df['short_sma'] > df['long_sma'], 1, 
                np.where(df['short_sma'] < df['long_sma'], -1, 0)
            )
            
            # Generate position column (to identify entry/exit points)
            # Position changes when signal changes
            df['position'] = df['signal'].diff().fillna(0)
            
            # Entry signal: 1 when position becomes 1
            # Exit signal: -1 when position becomes -1
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
            'type': 'SMA Crossover',
            'short_window': self.short_window,
            'long_window': self.long_window
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
    strategy = SMACrossover(short_window=20, long_window=50)
    
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
        
        plt.figure(figsize=(12, 8))
        
        # Plot close price
        plt.subplot(2, 1, 1)
        plt.plot(signals.index, signals['close'], label='Close Price')
        plt.plot(signals.index, signals['short_sma'], label=f'{strategy.short_window}-day SMA')
        plt.plot(signals.index, signals['long_sma'], label=f'{strategy.long_window}-day SMA')
        
        # Plot buy and sell signals
        plt.plot(signals.loc[signals['entry'] == 1].index, 
                signals.loc[signals['entry'] == 1]['close'], 
                '^', markersize=10, color='g', label='Buy Signal')
        
        plt.plot(signals.loc[signals['exit'] == 1].index, 
                signals.loc[signals['exit'] == 1]['close'], 
                'v', markersize=10, color='r', label='Sell Signal')
        
        plt.title(f'{symbol} - {strategy.name}')
        plt.legend()
        plt.grid(True)
        
        # Plot signal and position
        plt.subplot(2, 1, 2)
        plt.plot(signals.index, signals['signal'], label='Signal (1 = Long, -1 = Short)')
        plt.title('Trading Signals')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        logger.error(f"Error plotting results: {e}") 