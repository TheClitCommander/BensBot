#!/usr/bin/env python3

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import logging
from enum import Enum  # Added for MarketRegime enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StrategyRotator')

# Define MarketRegime enum directly in this file to avoid import dependency
class MarketRegime(Enum):
    """Market regime classifications"""
    UNKNOWN = 0
    BULL = 1      # Rising prices, low volatility
    BEAR = 2      # Falling prices, high volatility
    SIDEWAYS = 3  # Range-bound, moderate volatility
    HIGH_VOL = 4  # High volatility regardless of direction
    LOW_VOL = 5   # Low volatility regardless of direction
    CRISIS = 6    # Extreme volatility, sharp declines

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, name):
        self.name = name
        self.current_weight = 0.0
        self.historical_performance = []
    
    def generate_signal(self, data):
        """Generate trading signals based on the strategy logic
        
        Args:
            data: Market data (pandas DataFrame)
            
        Returns:
            float: Signal strength between -1.0 (strong sell) and 1.0 (strong buy)
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def calculate_performance(self, data):
        """Calculate historical performance of the strategy
        
        Args:
            data: Market data including returns
            
        Returns:
            float: Performance metric (e.g., Sharpe ratio)
        """
        raise NotImplementedError("Subclasses must implement this method")


class MomentumStrategy(BaseStrategy):
    """Strategy based on price momentum"""
    
    def __init__(self, window=20):
        super().__init__("Momentum")
        self.window = window
    
    def generate_signal(self, data):
        """Generate signals based on price momentum
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            float: Signal strength between -1 and 1
        """
        if len(data) < self.window:
            return 0.0
        
        returns = data['close'].pct_change(self.window).iloc[-1]
        # Normalize between -1 and 1
        signal = np.clip(returns, -0.1, 0.1) / 0.1
        return signal
    
    def calculate_performance(self, data):
        """Calculate Sharpe ratio of the strategy"""
        if len(data) < 30:  # Need sufficient data
            return 0.0
        
        # Simple implementation: calculate returns based on signals
        signals = [self.generate_signal(data.iloc[:i+1]) for i in range(self.window, len(data))]
        returns = data['close'].pct_change().iloc[self.window+1:].values
        
        strategy_returns = [signals[i-1] * returns[i] for i in range(1, len(returns))]
        
        if len(strategy_returns) == 0:
            return 0.0
        
        sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-6) * np.sqrt(252)
        return sharpe


class TrendFollowingStrategy(BaseStrategy):
    """Strategy based on trend following using moving averages"""
    
    def __init__(self, short_window=10, long_window=50):
        super().__init__("Trend Following")
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signal(self, data):
        """Generate signals based on moving average crossovers
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            float: Signal strength between -1 and 1
        """
        if len(data) < self.long_window:
            return 0.0
        
        short_ma = data['close'].rolling(self.short_window).mean().iloc[-1]
        long_ma = data['close'].rolling(self.long_window).mean().iloc[-1]
        
        # Calculate signal strength based on percent difference
        diff_pct = (short_ma - long_ma) / long_ma
        
        # Normalize between -1 and 1
        signal = np.clip(diff_pct * 5, -1.0, 1.0)  # Scale by 5 to amplify
        return signal
    
    def calculate_performance(self, data):
        """Calculate Sharpe ratio of the strategy"""
        if len(data) < self.long_window + 30:  # Need sufficient data
            return 0.0
        
        # Calculate signals for historical periods
        signals = []
        for i in range(self.long_window, len(data)):
            signal = self.generate_signal(data.iloc[:i+1])
            signals.append(signal)
        
        returns = data['close'].pct_change().iloc[self.long_window+1:].values
        
        strategy_returns = [signals[i-1] * returns[i] for i in range(1, len(returns))]
        
        if len(strategy_returns) == 0:
            return 0.0
        
        sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-6) * np.sqrt(252)
        return sharpe


class MeanReversionStrategy(BaseStrategy):
    """Strategy based on mean reversion"""
    
    def __init__(self, window=20, std_dev=2.0):
        super().__init__("Mean Reversion")
        self.window = window
        self.std_dev = std_dev
    
    def generate_signal(self, data):
        """Generate signals based on Bollinger Bands
        
        Args:
            data: DataFrame with 'close' prices
            
        Returns:
            float: Signal strength between -1 and 1
        """
        if len(data) < self.window:
            return 0.0
        
        rolling_mean = data['close'].rolling(self.window).mean()
        rolling_std = data['close'].rolling(self.window).std()
        
        # Calculate upper and lower bands
        upper_band = rolling_mean + (rolling_std * self.std_dev)
        lower_band = rolling_mean - (rolling_std * self.std_dev)
        
        # Calculate current position relative to bands
        current_price = data['close'].iloc[-1]
        upper_band_last = upper_band.iloc[-1]
        lower_band_last = lower_band.iloc[-1]
        mean_last = rolling_mean.iloc[-1]
        
        # Normalize position between bands to get signal
        if current_price > upper_band_last:
            # Oversold - sell signal
            return -1.0
        elif current_price < lower_band_last:
            # Underbought - buy signal
            return 1.0
        else:
            # Within bands - proportional signal
            position = (current_price - mean_last) / (upper_band_last - mean_last)
            return -position  # Inverted because we want to go against the direction
    
    def calculate_performance(self, data):
        """Calculate Sharpe ratio of the strategy"""
        if len(data) < self.window + 30:  # Need sufficient data
            return 0.0
        
        # Calculate signals for historical periods
        signals = []
        for i in range(self.window, len(data)):
            signal = self.generate_signal(data.iloc[:i+1])
            signals.append(signal)
        
        returns = data['close'].pct_change().iloc[self.window+1:].values
        
        strategy_returns = [signals[i-1] * returns[i] for i in range(1, len(returns))]
        
        if len(strategy_returns) == 0:
            return 0.0
        
        sharpe = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-6) * np.sqrt(252)
        return sharpe


class StrategyRotator:
    """Strategy rotator that allocates weights to different strategies"""
    
    def __init__(self):
        self.strategies = []
        self.last_rotation = None
        self.rotation_frequency = 7  # days
        self.performance_window = 30  # days for calculating strategy performance
    
    def add_strategy(self, strategy):
        """Add a strategy to the rotator
        
        Args:
            strategy: BaseStrategy object
        """
        self.strategies.append(strategy)
    
    def update_strategy_weights(self, data):
        """Update weights assigned to strategies based on recent performance
        
        Args:
            data: Market data including recent history
            
        Returns:
            dict: Strategy weights
        """
        # Check if rotation is needed
        current_date = datetime.now()
        if (self.last_rotation is not None and 
            (current_date - self.last_rotation).days < self.rotation_frequency):
            # Return current weights if not time to rotate
            return {s.name: s.current_weight for s in self.strategies}
        
        # Calculate performance for each strategy
        performances = []
        for strategy in self.strategies:
            perf = strategy.calculate_performance(data)
            performances.append(perf)
        
        # If all performances are zero, distribute evenly
        if sum(abs(p) for p in performances) < 1e-6:
            weight = 1.0 / len(self.strategies)
            for strategy in self.strategies:
                strategy.current_weight = weight
        else:
            # Normalize performances to get weights (only use positive performances)
            positive_perfs = [max(0, p) for p in performances]
            total_perf = sum(positive_perfs)
            
            if total_perf > 0:
                for i, strategy in enumerate(self.strategies):
                    strategy.current_weight = positive_perfs[i] / total_perf
            else:
                # If all performances are negative, use inverse weights of negative performances
                neg_perfs = [abs(min(0, p)) for p in performances]
                total_neg = sum(neg_perfs)
                
                if total_neg > 0:
                    for i, strategy in enumerate(self.strategies):
                        strategy.current_weight = (1.0 - neg_perfs[i] / total_neg) / (len(self.strategies) - 1) \
                                               if neg_perfs[i] > 0 else 0.0
                else:
                    # Equal weights as fallback
                    for strategy in self.strategies:
                        strategy.current_weight = 1.0 / len(self.strategies)
        
        # Update rotation timestamp
        self.last_rotation = current_date
        
        # Return dict of strategy weights
        return {s.name: s.current_weight for s in self.strategies}
    
    def generate_combined_signal(self, data):
        """Generate combined signal based on weighted strategies
        
        Args:
            data: Market data
            
        Returns:
            float: Combined signal between -1 and 1
        """
        combined_signal = 0.0
        
        for strategy in self.strategies:
            signal = strategy.generate_signal(data)
            combined_signal += strategy.current_weight * signal
        
        return combined_signal


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    data = pd.DataFrame({
        'close': np.random.normal(loc=100, scale=2, size=100) * 
                 np.exp(np.cumsum(np.random.normal(loc=0.001, scale=0.01, size=100)))
    }, index=dates)
    
    # Create strategies
    momentum = MomentumStrategy(window=10)
    trend = TrendFollowingStrategy(short_window=5, long_window=20)
    mean_rev = MeanReversionStrategy(window=10, std_dev=2.0)
    
    # Create rotator
    rotator = StrategyRotator()
    rotator.add_strategy(momentum)
    rotator.add_strategy(trend)
    rotator.add_strategy(mean_rev)
    
    # Update weights
    weights = rotator.update_strategy_weights(data)
    print("Strategy Weights:")
    for name, weight in weights.items():
        print(f"{name}: {weight:.2f}")
    
    # Generate combined signal
    signal = rotator.generate_combined_signal(data)
    print(f"Combined Signal: {signal:.4f}") 