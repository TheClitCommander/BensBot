import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Tuple, Optional
import os
import json
from datetime import datetime
import sys
import inspect

# Add parent directory to path to import from data and strategies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.alpha_vantage_fetcher import AlphaVantageFetcher
from strategies.technical_indicators import TechnicalStrategy

class Backtester:
    """Class to backtest trading strategies"""
    
    def __init__(self, strategy: TechnicalStrategy, initial_capital: float = 10000.0):
        """
        Initialize backtester with strategy and initial capital
        
        Parameters:
        -----------
        strategy : TechnicalStrategy
            Trading strategy to backtest
        initial_capital : float
            Initial capital to start trading with
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.data = {}
        self.results = {}
        self.performance_metrics = {}
        
    def load_data(self, symbols: List[str], start_date: str = None, end_date: str = None):
        """
        Load historical price data for symbols
        
        Parameters:
        -----------
        symbols : List[str]
            List of stock symbols to load data for
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str
            End date in YYYY-MM-DD format
        """
        # Initialize Alpha Vantage fetcher
        av_fetcher = AlphaVantageFetcher()
        
        for symbol in symbols:
            # Fetch daily adjusted data
            df = av_fetcher.get_daily_adjusted(symbol)
            
            # Filter by date range if provided
            if start_date and end_date:
                df = df[(df.index >= start_date) & (df.index <= end_date)]
            elif start_date:
                df = df[df.index >= start_date]
            elif end_date:
                df = df[df.index <= end_date]
                
            self.data[symbol] = df
            
        return self.data
    
    def run_backtest(self):
        """
        Run backtest on loaded data
        
        Returns:
        --------
        Dict
            Dictionary with backtest results
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_data() first.")
            
        # Generate signals
        signals = self.strategy.generate_signals(self.data)
        
        # Calculate positions
        positions = self.strategy.calculate_positions(signals, self.initial_capital)
        
        # Calculate returns
        returns = self.strategy.calculate_returns()
        
        # Calculate performance metrics
        self.performance_metrics = self._calculate_performance_metrics(positions)
        
        # Store results
        self.results = {
            'signals': signals,
            'positions': positions,
            'returns': returns,
            'performance_metrics': self.performance_metrics
        }
        
        return self.results
    
    def _calculate_performance_metrics(self, positions: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """
        Calculate performance metrics for each symbol
        
        Parameters:
        -----------
        positions : Dict[str, pd.DataFrame]
            Dictionary with positions for each symbol
            
        Returns:
        --------
        Dict[str, Dict[str, float]]
            Dictionary with performance metrics for each symbol
        """
        metrics = {}
        
        for symbol, pos_df in positions.items():
            # Calculate daily returns
            daily_returns = pos_df['total'].pct_change().dropna()
            
            # Calculate annualized return
            total_return = (pos_df['total'].iloc[-1] - pos_df['total'].iloc[0]) / pos_df['total'].iloc[0]
            days = (pos_df.index[-1] - pos_df.index[0]).days
            annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # Calculate max drawdown
            pos_df['previous_peak'] = pos_df['total'].cummax()
            pos_df['drawdown'] = (pos_df['total'] - pos_df['previous_peak']) / pos_df['previous_peak']
            max_drawdown = pos_df['drawdown'].min()
            
            # Calculate Sharpe ratio (assuming risk-free rate of 0)
            sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
            
            # Calculate win rate
            trades = pos_df[pos_df['position'] != 0]
            if len(trades) > 0:
                winning_trades = trades[trades['position'] * trades['close'].diff() > 0]
                win_rate = len(winning_trades) / len(trades)
            else:
                win_rate = 0
                
            # Store metrics
            metrics[symbol] = {
                'total_return': total_return * 100,  # Convert to percentage
                'annualized_return': annualized_return * 100,  # Convert to percentage
                'max_drawdown': max_drawdown * 100,  # Convert to percentage
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate * 100,  # Convert to percentage
                'num_trades': len(trades)
            }
            
        return metrics
    
    def plot_results(self, symbol: str, figsize: Tuple[int, int] = (14, 10)):
        """
        Plot backtest results for a symbol
        
        Parameters:
        -----------
        symbol : str
            Symbol to plot results for
        figsize : Tuple[int, int]
            Figure size
        """
        if not self.results:
            raise ValueError("No results. Call run_backtest() first.")
            
        if symbol not in self.results['signals']:
            raise ValueError(f"No results for symbol {symbol}")
            
        # Get signal and position DataFrames
        signal_df = self.results['signals'][symbol]
        position_df = self.results['positions'][symbol]
        
        # Create figure and axes
        fig, axes = plt.subplots(3, 1, figsize=figsize, gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)
        
        # Plot price and signals on first axis
        axes[0].plot(signal_df.index, signal_df['close'], label='Price')
        
        # Plot buy signals
        buy_signals = signal_df[signal_df['signal'] == 1]
        axes[0].scatter(buy_signals.index, buy_signals['close'], 
                       marker='^', color='green', s=100, label='Buy Signal')
        
        # Plot sell signals
        sell_signals = signal_df[signal_df['signal'] == -1]
        axes[0].scatter(sell_signals.index, sell_signals['close'], 
                       marker='v', color='red', s=100, label='Sell Signal')
        
        # Add title and legend
        axes[0].set_title(f'{self.strategy.name} - {symbol}')
        axes[0].set_ylabel('Price')
        axes[0].legend(loc='best')
        axes[0].grid(True)
        
        # Plot portfolio value on second axis
        axes[1].plot(position_df.index, position_df['total'], label='Portfolio Value')
        
        # Add title and legend
        axes[1].set_ylabel('Portfolio Value')
        axes[1].legend(loc='best')
        axes[1].grid(True)
        
        # Plot daily returns on third axis
        daily_returns = position_df['total'].pct_change()
        axes[2].plot(position_df.index, daily_returns, label='Daily Returns')
        
        # Add title and legend
        axes[2].set_xlabel('Date')
        axes[2].set_ylabel('Returns (%)')
        axes[2].legend(loc='best')
        axes[2].grid(True)
        
        plt.tight_layout()
        plt.show()
        
        # Print performance metrics
        print(f"\nPerformance Metrics for {symbol}:")
        for metric, value in self.performance_metrics[symbol].items():
            print(f"{metric.replace('_', ' ').title()}: {value:.2f}%")
    
    def save_results(self, filename: str):
        """
        Save backtest results to file
        
        Parameters:
        -----------
        filename : str
            Filename to save results to
        """
        if not self.results:
            raise ValueError("No results. Call run_backtest() first.")
            
        # Create results dict
        results_dict = {
            'strategy': self.strategy.name,
            'initial_capital': self.initial_capital,
            'symbols': list(self.data.keys()),
            'date_range': {
                'start': str(min([df.index[0] for df in self.data.values()])),
                'end': str(max([df.index[-1] for df in self.data.values()]))
            },
            'performance_metrics': self.performance_metrics,
            'returns': self.results['returns']
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save results to file
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=4)
            
        print(f"Results saved to {filename}")


def run_backtest_example():
    """Example of how to run a backtest"""
    # Import strategies
    from strategies.technical_indicators import (
        SMACrossover, 
        MACDStrategy, 
        RSIStrategy, 
        BollingerBandsStrategy,
        MultiIndicatorStrategy
    )
    
    # Set up symbols and date range
    symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN']
    start_date = '2021-01-01'
    end_date = '2022-01-01'
    
    # Initialize strategy
    strategy = SMACrossover(short_window=20, long_window=50)
    
    # Initialize backtester
    backtester = Backtester(strategy, initial_capital=10000.0)
    
    # Load data
    print(f"Loading data for {symbols}...")
    backtester.load_data(symbols, start_date, end_date)
    
    # Run backtest
    print("Running backtest...")
    results = backtester.run_backtest()
    
    # Plot results
    for symbol in symbols:
        backtester.plot_results(symbol)
    
    # Save results
    backtester.save_results(f"backtest/results/{strategy.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")


if __name__ == "__main__":
    run_backtest_example() 