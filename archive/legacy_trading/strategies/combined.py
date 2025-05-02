#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combined Strategy

This strategy combines MACD and RSI indicators to generate trading signals.
It requires both indicators to confirm a trade for higher probability setups.
"""

import numpy as np
import pandas as pd
import logging
from trading.strategies.macd import MACD
from trading.strategies.rsi import RSI

logger = logging.getLogger(__name__)


class CombinedStrategy:
    """
    Combined Strategy using both MACD and RSI indicators.
    
    Generates buy signals when both MACD and RSI give buy signals within a confirmation window.
    Generates sell signals when both MACD and RSI give sell signals within a confirmation window.
    """
    
    def __init__(self, 
                 macd_fast=12, macd_slow=26, macd_signal=9,
                 rsi_period=14, rsi_overbought=70, rsi_oversold=30,
                 confirmation_window=3):
        """
        Initialize the Combined strategy.
        
        Parameters:
        -----------
        macd_fast : int
            Fast period for MACD calculation
        macd_slow : int
            Slow period for MACD calculation
        macd_signal : int
            Signal period for MACD calculation
        rsi_period : int
            Period for RSI calculation
        rsi_overbought : int
            Overbought threshold for RSI
        rsi_oversold : int
            Oversold threshold for RSI
        confirmation_window : int
            Number of bars to look for confirmation between indicators
        """
        self.macd_strategy = MACD(
            fast_period=macd_fast,
            slow_period=macd_slow,
            signal_period=macd_signal
        )
        
        self.rsi_strategy = RSI(
            period=rsi_period,
            overbought=rsi_overbought,
            oversold=rsi_oversold
        )
        
        self.confirmation_window = confirmation_window
        
        self.name = f"Combined_MACD({macd_fast},{macd_slow},{macd_signal})_RSI({rsi_period},{rsi_overbought},{rsi_oversold})_W{confirmation_window}"
        
        logger.info(f"Initialized {self.name} strategy")
    
    def generate_signals(self, data):
        """
        Generate trading signals by combining MACD and RSI.
        
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
        
        try:
            # Generate signals from individual strategies
            macd_signals = self.macd_strategy.generate_signals(df)
            rsi_signals = self.rsi_strategy.generate_signals(df)
            
            # Copy necessary columns from both strategies
            df['macd_line'] = macd_signals['macd_line']
            df['signal_line'] = macd_signals['signal_line']
            df['histogram'] = macd_signals['histogram']
            df['macd_entry'] = macd_signals['entry']
            df['macd_exit'] = macd_signals['exit']
            
            df['rsi'] = rsi_signals['rsi']
            df['rsi_entry'] = rsi_signals['entry']
            df['rsi_exit'] = rsi_signals['exit']
            
            # Initialize combined signal
            df['signal'] = 0
            
            # Create rolling windows for buy signals
            for i in range(len(df)):
                # Skip the first few bars where we don't have enough history
                if i < self.confirmation_window:
                    continue
                    
                # Check for buy confirmation (MACD and RSI both give buy signals within the window)
                window_start = max(0, i - self.confirmation_window + 1)
                window = df.iloc[window_start:i+1]
                
                if (window['macd_entry'].sum() > 0) and (window['rsi_entry'].sum() > 0):
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                
                # Check for sell confirmation (MACD and RSI both give sell signals within the window)
                if (window['macd_exit'].sum() > 0) and (window['rsi_exit'].sum() > 0):
                    df.iloc[i, df.columns.get_loc('signal')] = -1
            
            # Generate position column (to identify entry/exit points)
            df['position'] = df['signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
            df['position_change'] = df['position'].diff().fillna(0)
            
            # Generate entry and exit signals
            df['entry'] = np.where(df['position_change'] > 0, 1, 0)
            df['exit'] = np.where(df['position_change'] < 0, 1, 0)
            
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
        macd_params = self.macd_strategy.get_parameters()
        rsi_params = self.rsi_strategy.get_parameters()
        
        return {
            'name': self.name,
            'type': 'Combined',
            'macd_fast_period': macd_params['fast_period'],
            'macd_slow_period': macd_params['slow_period'],
            'macd_signal_period': macd_params['signal_period'],
            'rsi_period': rsi_params['period'],
            'rsi_overbought': rsi_params['overbought'],
            'rsi_oversold': rsi_params['oversold'],
            'confirmation_window': self.confirmation_window
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
    strategy = CombinedStrategy(
        macd_fast=12, macd_slow=26, macd_signal=9,
        rsi_period=14, rsi_overbought=70, rsi_oversold=30,
        confirmation_window=3
    )
    
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
        
        plt.figure(figsize=(12, 14))
        
        # Plot close price
        plt.subplot(3, 1, 1)
        plt.plot(signals.index, signals['close'], label='Close Price')
        plt.title(f'{symbol} - {strategy.name}')
        
        # Plot buy and sell signals
        plt.plot(signals.loc[signals['entry'] == 1].index, 
                signals.loc[signals['entry'] == 1]['close'], 
                '^', markersize=10, color='g', label='Buy Signal')
        
        plt.plot(signals.loc[signals['exit'] == 1].index, 
                signals.loc[signals['exit'] == 1]['close'], 
                'v', markersize=10, color='r', label='Sell Signal')
        
        plt.legend()
        plt.grid(True)
        
        # Plot MACD
        plt.subplot(3, 1, 2)
        plt.plot(signals.index, signals['macd_line'], label='MACD Line')
        plt.plot(signals.index, signals['signal_line'], label='Signal Line')
        plt.bar(signals.index, signals['histogram'], label='Histogram', alpha=0.3)
        plt.title('MACD Indicator')
        plt.legend()
        plt.grid(True)
        
        # Plot RSI
        plt.subplot(3, 1, 3)
        plt.plot(signals.index, signals['rsi'], label='RSI')
        plt.axhline(y=strategy.rsi_strategy.overbought, color='r', linestyle='-', label='Overbought')
        plt.axhline(y=strategy.rsi_strategy.oversold, color='g', linestyle='-', label='Oversold')
        
        # Highlight overbought and oversold regions
        plt.fill_between(signals.index, strategy.rsi_strategy.overbought, 100, 
                        color='r', alpha=0.1)
        plt.fill_between(signals.index, 0, strategy.rsi_strategy.oversold, 
                        color='g', alpha=0.1)
        
        plt.title('RSI Indicator')
        plt.ylim(0, 100)
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        logger.error(f"Error plotting results: {e}") 