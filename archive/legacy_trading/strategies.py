import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TradingStrategies')

class Strategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize the strategy with parameters
        
        Parameters:
        -----------
        params : Dict[str, Any]
            Strategy parameters
        """
        self.params = params or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on input data
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data
            
        Returns:
        --------
        pd.Series
            Series of trading signals where:
            1 = buy signal
            0 = hold/do nothing
            -1 = sell signal
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the strategy"""
        return f"{self.name}(params={self.params})"


class SMACrossover(Strategy):
    """
    Simple Moving Average Crossover strategy
    
    Generates a buy signal when the short-term SMA crosses above the long-term SMA,
    and a sell signal when the short-term SMA crosses below the long-term SMA.
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50, use_adjusted: bool = True):
        """
        Initialize the SMA Crossover strategy
        
        Parameters:
        -----------
        short_window : int
            Short-term moving average window in days
        long_window : int
            Long-term moving average window in days
        use_adjusted : bool
            Whether to use adjusted close prices
        """
        params = {
            'short_window': short_window,
            'long_window': long_window,
            'use_adjusted': use_adjusted
        }
        super().__init__(params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on SMA crossover
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data including 'close' or 'adjusted_close' column
            
        Returns:
        --------
        pd.Series
            Series of trading signals
        """
        if data.empty:
            logger.warning("Empty data provided to SMACrossover strategy")
            return pd.Series(index=data.index)
            
        short_window = self.params['short_window']
        long_window = self.params['long_window']
        use_adjusted = self.params['use_adjusted']
        
        # Determine price column to use
        price_col = 'adjusted_close' if use_adjusted and 'adjusted_close' in data.columns else 'close'
        
        if price_col not in data.columns:
            logger.error(f"Required column '{price_col}' not found in data")
            return pd.Series(index=data.index)
            
        # Calculate SMAs if not present in data
        if f'sma_{short_window}' not in data.columns:
            data[f'sma_{short_window}'] = data[price_col].rolling(window=short_window).mean()
            
        if f'sma_{long_window}' not in data.columns:
            data[f'sma_{long_window}'] = data[price_col].rolling(window=long_window).mean()
            
        # Create signals
        signals = pd.Series(index=data.index, data=0)
        
        # Buy signal: short SMA crosses above long SMA
        signals[
            (data[f'sma_{short_window}'] > data[f'sma_{long_window}']) & 
            (data[f'sma_{short_window}'].shift(1) <= data[f'sma_{long_window}'].shift(1))
        ] = 1
        
        # Sell signal: short SMA crosses below long SMA
        signals[
            (data[f'sma_{short_window}'] < data[f'sma_{long_window}']) & 
            (data[f'sma_{short_window}'].shift(1) >= data[f'sma_{long_window}'].shift(1))
        ] = -1
        
        return signals


class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) strategy
    
    Generates a buy signal when RSI drops below the oversold threshold,
    and a sell signal when RSI rises above the overbought threshold.
    """
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70, use_adjusted: bool = True):
        """
        Initialize the RSI strategy
        
        Parameters:
        -----------
        rsi_period : int
            RSI calculation period in days
        oversold : int
            RSI oversold threshold (below this value, consider buying)
        overbought : int
            RSI overbought threshold (above this value, consider selling)
        use_adjusted : bool
            Whether to use adjusted close prices
        """
        params = {
            'rsi_period': rsi_period,
            'oversold': oversold,
            'overbought': overbought,
            'use_adjusted': use_adjusted
        }
        super().__init__(params)
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI from price series
        
        Parameters:
        -----------
        prices : pd.Series
            Series of prices
        period : int
            RSI calculation period
            
        Returns:
        --------
        pd.Series
            Series of RSI values
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss over the period
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data including 'close' or 'adjusted_close' column
            or 'rsi' column
            
        Returns:
        --------
        pd.Series
            Series of trading signals
        """
        if data.empty:
            logger.warning("Empty data provided to RSIStrategy")
            return pd.Series(index=data.index)
            
        rsi_period = self.params['rsi_period']
        oversold = self.params['oversold']
        overbought = self.params['overbought']
        use_adjusted = self.params['use_adjusted']
        
        # Check if RSI is already calculated
        if 'rsi' in data.columns:
            rsi = data['rsi']
        else:
            # Determine price column to use
            price_col = 'adjusted_close' if use_adjusted and 'adjusted_close' in data.columns else 'close'
            
            if price_col not in data.columns:
                logger.error(f"Required column '{price_col}' not found in data")
                return pd.Series(index=data.index)
                
            # Calculate RSI
            rsi = self._calculate_rsi(data[price_col], period=rsi_period)
            
        # Create signals
        signals = pd.Series(index=data.index, data=0)
        
        # Buy signal: RSI crosses below oversold threshold
        signals[
            (rsi < oversold) & 
            (rsi.shift(1) >= oversold)
        ] = 1
        
        # Sell signal: RSI crosses above overbought threshold
        signals[
            (rsi > overbought) & 
            (rsi.shift(1) <= overbought)
        ] = -1
        
        return signals


class MACDStrategy(Strategy):
    """
    Moving Average Convergence Divergence (MACD) strategy
    
    Generates a buy signal when the MACD line crosses above the signal line,
    and a sell signal when the MACD line crosses below the signal line.
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, 
                use_adjusted: bool = True):
        """
        Initialize the MACD strategy
        
        Parameters:
        -----------
        fast_period : int
            Fast EMA period
        slow_period : int
            Slow EMA period
        signal_period : int
            Signal line period
        use_adjusted : bool
            Whether to use adjusted close prices
        """
        params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'use_adjusted': use_adjusted
        }
        super().__init__(params)
        
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, 
                       signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD from price series
        
        Parameters:
        -----------
        prices : pd.Series
            Series of prices
        fast_period : int
            Fast EMA period
        slow_period : int
            Slow EMA period
        signal_period : int
            Signal line period
            
        Returns:
        --------
        Tuple[pd.Series, pd.Series, pd.Series]
            MACD line, signal line, and histogram
        """
        # Calculate fast and slow EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MACD
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data including 'close' or 'adjusted_close' column
            or 'macd' and 'macd_signal' columns
            
        Returns:
        --------
        pd.Series
            Series of trading signals
        """
        if data.empty:
            logger.warning("Empty data provided to MACDStrategy")
            return pd.Series(index=data.index)
            
        fast_period = self.params['fast_period']
        slow_period = self.params['slow_period']
        signal_period = self.params['signal_period']
        use_adjusted = self.params['use_adjusted']
        
        # Check if MACD is already calculated
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            macd_line = data['macd']
            signal_line = data['macd_signal']
        else:
            # Determine price column to use
            price_col = 'adjusted_close' if use_adjusted and 'adjusted_close' in data.columns else 'close'
            
            if price_col not in data.columns:
                logger.error(f"Required column '{price_col}' not found in data")
                return pd.Series(index=data.index)
                
            # Calculate MACD
            macd_line, signal_line, _ = self._calculate_macd(
                data[price_col], 
                fast_period=fast_period, 
                slow_period=slow_period, 
                signal_period=signal_period
            )
            
        # Create signals
        signals = pd.Series(index=data.index, data=0)
        
        # Buy signal: MACD line crosses above signal line
        signals[
            (macd_line > signal_line) & 
            (macd_line.shift(1) <= signal_line.shift(1))
        ] = 1
        
        # Sell signal: MACD line crosses below signal line
        signals[
            (macd_line < signal_line) & 
            (macd_line.shift(1) >= signal_line.shift(1))
        ] = -1
        
        return signals


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands strategy
    
    Generates a buy signal when the price touches the lower band,
    and a sell signal when the price touches the upper band.
    """
    
    def __init__(self, window: int = 20, num_std: float = 2, use_adjusted: bool = True):
        """
        Initialize the Bollinger Bands strategy
        
        Parameters:
        -----------
        window : int
            Window for moving average calculation
        num_std : float
            Number of standard deviations for band width
        use_adjusted : bool
            Whether to use adjusted close prices
        """
        params = {
            'window': window,
            'num_std': num_std,
            'use_adjusted': use_adjusted
        }
        super().__init__(params)
        
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, 
                                  num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands from price series
        
        Parameters:
        -----------
        prices : pd.Series
            Series of prices
        window : int
            Window for moving average calculation
        num_std : float
            Number of standard deviations for band width
            
        Returns:
        --------
        Tuple[pd.Series, pd.Series, pd.Series]
            Upper band, middle band, and lower band
        """
        # Calculate middle band (simple moving average)
        middle_band = prices.rolling(window=window).mean()
        
        # Calculate standard deviation
        rolling_std = prices.rolling(window=window).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (rolling_std * num_std)
        lower_band = middle_band - (rolling_std * num_std)
        
        return upper_band, middle_band, lower_band
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Bollinger Bands
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data including 'close' or 'adjusted_close' column
            or 'bb_upper', 'bb_middle', and 'bb_lower' columns
            
        Returns:
        --------
        pd.Series
            Series of trading signals
        """
        if data.empty:
            logger.warning("Empty data provided to BollingerBandsStrategy")
            return pd.Series(index=data.index)
            
        window = self.params['window']
        num_std = self.params['num_std']
        use_adjusted = self.params['use_adjusted']
        
        # Check if Bollinger Bands are already calculated
        if 'bb_upper' in data.columns and 'bb_lower' in data.columns:
            upper_band = data['bb_upper']
            lower_band = data['bb_lower']
        else:
            # Determine price column to use
            price_col = 'adjusted_close' if use_adjusted and 'adjusted_close' in data.columns else 'close'
            
            if price_col not in data.columns:
                logger.error(f"Required column '{price_col}' not found in data")
                return pd.Series(index=data.index)
                
            # Calculate Bollinger Bands
            upper_band, _, lower_band = self._calculate_bollinger_bands(
                data[price_col], 
                window=window, 
                num_std=num_std
            )
            
        # Get price data
        price_col = 'adjusted_close' if use_adjusted and 'adjusted_close' in data.columns else 'close'
        prices = data[price_col]
        
        # Create signals
        signals = pd.Series(index=data.index, data=0)
        
        # Buy signal: price touches or crosses below lower band
        signals[
            (prices <= lower_band) & 
            (prices.shift(1) > lower_band.shift(1))
        ] = 1
        
        # Sell signal: price touches or crosses above upper band
        signals[
            (prices >= upper_band) & 
            (prices.shift(1) < upper_band.shift(1))
        ] = -1
        
        return signals


class CompositeStrategy(Strategy):
    """
    Composite strategy that combines multiple strategies
    
    Generate signals based on a weighted combination of multiple strategies
    """
    
    def __init__(self, strategies: List[Tuple[Strategy, float]]):
        """
        Initialize the composite strategy
        
        Parameters:
        -----------
        strategies : List[Tuple[Strategy, float]]
            List of (strategy, weight) tuples
        """
        self.strategies = strategies
        strategy_names = ", ".join([f"{s[0].name}({s[1]})" for s in strategies])
        params = {
            'strategies': strategy_names
        }
        super().__init__(params)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the weighted combination of strategies
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with market data
            
        Returns:
        --------
        pd.Series
            Series of trading signals
        """
        if data.empty:
            logger.warning("Empty data provided to CompositeStrategy")
            return pd.Series(index=data.index)
            
        # Initialize combined signal
        combined_signal = pd.Series(index=data.index, data=0.0)
        
        # Get signals from each strategy and apply weights
        for strategy, weight in self.strategies:
            signals = strategy.generate_signals(data)
            combined_signal += signals * weight
            
        # Convert to discrete signals
        threshold = 0.5
        discrete_signals = pd.Series(index=data.index, data=0)
        discrete_signals[combined_signal > threshold] = 1
        discrete_signals[combined_signal < -threshold] = -1
        
        return discrete_signals


# Example usage
if __name__ == "__main__":
    from data.alpha_vantage_fetcher import AlphaVantageFetcher
    
    # Initialize data fetcher
    fetcher = AlphaVantageFetcher()
    
    # Get historical data for Apple
    data = fetcher.get_stock_data("AAPL", start_date="2022-01-01", end_date="2022-12-31")
    
    # Initialize strategies
    sma_strategy = SMACrossover(short_window=20, long_window=50)
    rsi_strategy = RSIStrategy(rsi_period=14, oversold=30, overbought=70)
    macd_strategy = MACDStrategy()
    bb_strategy = BollingerBandsStrategy()
    
    # Generate signals
    sma_signals = sma_strategy.generate_signals(data)
    rsi_signals = rsi_strategy.generate_signals(data)
    macd_signals = macd_strategy.generate_signals(data)
    bb_signals = bb_strategy.generate_signals(data)
    
    # Create composite strategy
    composite = CompositeStrategy([
        (sma_strategy, 0.3),
        (rsi_strategy, 0.2),
        (macd_strategy, 0.3),
        (bb_strategy, 0.2)
    ])
    
    composite_signals = composite.generate_signals(data)
    
    # Print signal statistics
    print(f"SMA Signals - Buy: {sum(sma_signals == 1)}, Sell: {sum(sma_signals == -1)}")
    print(f"RSI Signals - Buy: {sum(rsi_signals == 1)}, Sell: {sum(rsi_signals == -1)}")
    print(f"MACD Signals - Buy: {sum(macd_signals == 1)}, Sell: {sum(macd_signals == -1)}")
    print(f"Bollinger Bands Signals - Buy: {sum(bb_signals == 1)}, Sell: {sum(bb_signals == -1)}")
    print(f"Composite Signals - Buy: {sum(composite_signals == 1)}, Sell: {sum(composite_signals == -1)}") 