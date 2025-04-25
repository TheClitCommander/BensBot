#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI Strategy

This strategy generates buy signals when the RSI crosses below the oversold threshold
and sell signals when the RSI crosses above the overbought threshold.
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RSI:
    """
    Relative Strength Index (RSI) Strategy.
    
    Generates buy signals when RSI crosses below an oversold threshold,
    and sell signals when RSI crosses above an overbought threshold.
    """
    
    def __init__(self, period=14, overbought=70, oversold=30):
        """
        Initialize the RSI strategy.
        
        Parameters:
        -----------
        period : int
            The window length for the RSI calculation
        overbought : int
            The threshold above which the market is considered overbought (typically 70)
        oversold : int
            The threshold below which the market is considered oversold (typically 30)
        """
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.name = f"RSI_{period}_{overbought}_{oversold}"
        
        logger.info(f"Initialized {self.name} strategy")
    
    def calculate_rsi(self, data):
        """
        Calculate the Relative Strength Index (RSI).
        
        Parameters:
        -----------
        data : pandas.Series
            Close price series
            
        Returns:
        --------
        pandas.Series
            The RSI values
        """
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss over the period
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        # Calculate RS (Relative Strength)
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)  # Avoid division by zero
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data):
        """
        Generate trading signals based on RSI values.
        
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
        if len(df) < self.period:
            logger.warning(f"Data length ({len(df)}) is less than required ({self.period})")
            return df
        
        try:
            # Calculate RSI
            df['rsi'] = self.calculate_rsi(df['close'])
            
            # Initialize signals
            df['signal'] = 0
            
            # Create overbought and oversold indicators
            df['overbought'] = df['rsi'] > self.overbought
            df['oversold'] = df['rsi'] < self.oversold
            
            # Previous day's overbought and oversold status
            df['prev_overbought'] = df['overbought'].shift(1)
            df['prev_oversold'] = df['oversold'].shift(1)
            
            # Generate signals: 1 for buy (crossing up from oversold), -1 for sell (crossing down from overbought)
            # Buy when RSI crosses from below oversold to above oversold
            df.loc[(df['prev_oversold'] == True) & (df['oversold'] == False), 'signal'] = 1
            
            # Sell when RSI crosses from above overbought to below overbought
            df.loc[(df['prev_overbought'] == True) & (df['overbought'] == False), 'signal'] = -1
            
            # Calculate position changes for entry/exit
            df['position'] = df['signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
            df['position_change'] = df['position'].diff().fillna(0)
            
            # Generate entry and exit signals
            df['entry'] = np.where(df['signal'] == 1, 1, 0)
            df['exit'] = np.where(df['signal'] == -1, 1, 0)
            
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
            'type': 'RSI',
            'period': self.period,
            'overbought': self.overbought,
            'oversold': self.oversold
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
    strategy = RSI(period=14, overbought=70, oversold=30)
    
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
        plt.subplot(2, 1, 1)
        plt.plot(signals.index, signals['close'], label='Close Price')
        plt.title(f'{symbol} - {strategy.name}')
        
        # Plot buy and sell signals on price chart
        plt.plot(signals.loc[signals['entry'] == 1].index, 
                signals.loc[signals['entry'] == 1]['close'], 
                '^', markersize=10, color='g', label='Buy Signal')
        
        plt.plot(signals.loc[signals['exit'] == 1].index, 
                signals.loc[signals['exit'] == 1]['close'], 
                'v', markersize=10, color='r', label='Sell Signal')
        
        plt.legend()
        plt.grid(True)
        
        # Plot RSI
        plt.subplot(2, 1, 2)
        plt.plot(signals.index, signals['rsi'], label='RSI')
        
        # Add overbought and oversold lines
        plt.axhline(y=strategy.overbought, color='r', linestyle='-', label='Overbought')
        plt.axhline(y=strategy.oversold, color='g', linestyle='-', label='Oversold')
        
        # Highlight overbought and oversold regions
        plt.fill_between(signals.index, strategy.overbought, 100, 
                        color='r', alpha=0.1)
        plt.fill_between(signals.index, 0, strategy.oversold, 
                        color='g', alpha=0.1)
        
        plt.title('RSI Indicator')
        plt.ylim(0, 100)
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        logger.error(f"Error plotting results: {e}") 