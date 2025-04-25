import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

def generate_mock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    include_indicators: bool = True
) -> pd.DataFrame:
    """
    Generate mock market data for testing purposes
    
    Parameters:
    -----------
    symbol : str
        Stock symbol
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
    include_indicators : bool
        Whether to include technical indicators
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with mock market data
    """
    # Convert dates to datetime
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Create date range (business days only)
    date_range = pd.date_range(start=start, end=end, freq='B')
    
    # Set seed for reproducibility
    np.random.seed(42 + sum(ord(c) for c in symbol))
    
    # Generate base price
    base_price = np.random.uniform(50, 200)
    
    # Generate price series with random walk
    n = len(date_range)
    returns = np.random.normal(0.0005, 0.015, n)
    prices = base_price * np.cumprod(1 + returns)
    
    # Generate OHLC prices
    high = prices * np.random.uniform(1.0, 1.03, n)
    low = prices * np.random.uniform(0.97, 1.0, n)
    
    # Generate open prices
    prev_close = np.roll(prices, 1)
    prev_close[0] = prices[0] * np.random.uniform(0.98, 1.02)
    
    # Randomize open price between previous close and current close
    weight = np.random.uniform(0, 1, n)
    open_prices = weight * prev_close + (1 - weight) * prices
    
    # Ensure high/low bounds are respected
    high = np.maximum(high, np.maximum(open_prices, prices))
    low = np.minimum(low, np.minimum(open_prices, prices))
    
    # Generate volume
    volume = np.random.lognormal(14, 1, n) * (1 + 3 * np.abs(returns))
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume.astype(int),
        'adjusted_close': prices,
        'symbol': symbol
    }, index=date_range)
    
    # Add technical indicators if requested
    if include_indicators:
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (std * 2)
        df['bb_lower'] = df['bb_middle'] - (std * 2)
    
    return df

def get_mock_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get mock stock data for a given symbol and date range.
    Acts as a drop-in replacement for AlphaVantageFetcher.get_stock_data.
    
    Parameters:
    -----------
    symbol : str
        Stock symbol
    start_date : str, optional
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with mock stock data
    """
    # Default to recent data if dates not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Generate mock data
    return generate_mock_data(symbol, start_date, end_date)

def get_multiple_mock_data(
    symbols: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Get mock data for multiple symbols
    
    Parameters:
    -----------
    symbols : List[str]
        List of stock symbols
    start_date : str, optional
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary of DataFrames with mock stock data by symbol
    """
    result = {}
    
    for symbol in symbols:
        df = get_mock_stock_data(symbol, start_date, end_date)
        result[symbol] = df
    
    return result 

class MockDataGenerator:
    """
    Class for generating mock financial data for testing purposes
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the mock data generator
        
        Args:
            seed: Random seed for reproducible data generation
        """
        self.seed = seed
        np.random.seed(seed)
    
    def generate_price_series(
        self,
        start_date: str,
        end_date: str,
        initial_price: float = 100.0,
        volatility: float = 0.01,
        drift: float = 0.0001,
        freq: str = 'D'
    ) -> pd.Series:
        """
        Generate a price series using geometric Brownian motion
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            initial_price: Starting price
            volatility: Daily volatility
            drift: Daily drift (trend)
            freq: Frequency ('D' for daily, 'W' for weekly, etc.)
            
        Returns:
            Series of prices
        """
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        n = len(date_range)
        
        # Generate random returns
        np.random.seed(self.seed)
        returns = np.random.normal(loc=drift, scale=volatility, size=n)
        
        # Calculate cumulative returns
        cumulative_returns = np.cumprod(1 + returns)
        
        # Calculate prices
        prices = initial_price * cumulative_returns
        
        # Create series
        price_series = pd.Series(prices, index=date_range)
        
        return price_series
    
    def generate_ohlcv_dataframe(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_price: float = 100.0,
        volatility: float = 0.01,
        drift: float = 0.0001,
        volume_mean: float = 1000000,
        volume_std: float = 200000,
        freq: str = 'D'
    ) -> pd.DataFrame:
        """
        Generate a DataFrame with OHLCV data
        
        Args:
            symbol: Stock symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            initial_price: Starting price
            volatility: Daily volatility
            drift: Daily drift (trend)
            volume_mean: Mean daily volume
            volume_std: Standard deviation of daily volume
            freq: Frequency ('D' for daily, 'W' for weekly, etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        n = len(date_range)
        
        # Generate close prices
        close_prices = self.generate_price_series(
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_price,
            volatility=volatility,
            drift=drift,
            freq=freq
        )
        
        # Generate daily percentage changes for intraday variations
        np.random.seed(self.seed + 1)
        daily_changes = np.random.normal(loc=0, scale=volatility, size=(n, 3))
        
        # Calculate high, low, and open prices based on close prices
        high_pct = np.abs(daily_changes[:, 0]) + 0.001  # Always higher than close
        low_pct = -np.abs(daily_changes[:, 1]) - 0.001  # Always lower than close
        open_pct = daily_changes[:, 2]
        
        high_prices = close_prices.values * (1 + high_pct)
        low_prices = close_prices.values * (1 + low_pct)
        open_prices = close_prices.values * (1 + open_pct)
        
        # Make sure low is always the lowest
        for i in range(n):
            min_price = min(open_prices[i], close_prices[i])
            max_price = max(open_prices[i], close_prices[i])
            
            if low_prices[i] > min_price:
                low_prices[i] = min_price * 0.999
                
            if high_prices[i] < max_price:
                high_prices[i] = max_price * 1.001
        
        # Generate volume data
        np.random.seed(self.seed + 2)
        volume = np.random.normal(loc=volume_mean, scale=volume_std, size=n)
        volume = np.maximum(volume, 0)  # Ensure non-negative volume
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices.values,
            'volume': volume.astype(int),
            'symbol': symbol
        }, index=date_range)
        
        df.index.name = 'date'
        
        return df
    
    def generate_multiple_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        base_price: float = 100.0,
        correlation_matrix: Optional[np.ndarray] = None,
        freq: str = 'D'
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate OHLCV data for multiple symbols with specified correlations
        
        Args:
            symbols: List of stock symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            base_price: Base price for all symbols
            correlation_matrix: Correlation matrix for symbols (if None, random correlations will be used)
            freq: Frequency ('D' for daily, 'W' for weekly, etc.)
            
        Returns:
            Dictionary mapping symbols to their respective DataFrames
        """
        n_symbols = len(symbols)
        
        # Create correlation matrix if not provided
        if correlation_matrix is None:
            np.random.seed(self.seed + 3)
            # Generate a random correlation matrix
            A = np.random.rand(n_symbols, n_symbols)
            correlation_matrix = np.corrcoef(A)
        
        # Check correlation matrix dimensions
        if correlation_matrix.shape != (n_symbols, n_symbols):
            raise ValueError(f"Correlation matrix dimensions {correlation_matrix.shape} don't match number of symbols {n_symbols}")
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        n_days = len(date_range)
        
        # Generate correlated random returns
        np.random.seed(self.seed + 4)
        
        # Cholesky decomposition for generating correlated random variables
        L = np.linalg.cholesky(correlation_matrix)
        
        # Generate uncorrelated random returns
        uncorrelated_returns = np.random.normal(loc=0.0001, scale=0.01, size=(n_days, n_symbols))
        
        # Convert to correlated returns
        correlated_returns = np.dot(uncorrelated_returns, L.T)
        
        # Generate DataFrames for each symbol
        result = {}
        
        for i, symbol in enumerate(symbols):
            # Calculate prices from returns
            prices = base_price * np.cumprod(1 + correlated_returns[:, i])
            
            # Set different base prices and variations for each symbol to make them look different
            symbol_base_price = base_price * (0.5 + i)
            symbol_volatility = 0.01 * (1 + 0.2 * i)
            symbol_drift = 0.0001 * (1 + 0.5 * i)
            symbol_volume = 1000000 * (1 + 0.3 * i)
            
            # Generate individual DataFrame
            df = self.generate_ohlcv_dataframe(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_price=symbol_base_price,
                volatility=symbol_volatility,
                drift=symbol_drift,
                volume_mean=symbol_volume,
                freq=freq
            )
            
            result[symbol] = df
        
        return result
    
    def generate_technical_indicator(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        window: int = 14,
        add_noise: bool = True,
        noise_level: float = 0.01
    ) -> pd.DataFrame:
        """
        Generate mock technical indicator data based on price data
        
        Args:
            df: DataFrame with OHLCV data
            indicator_name: Name for the indicator
            window: Window size for the indicator
            add_noise: Whether to add noise to the indicator
            noise_level: Level of noise to add
            
        Returns:
            DataFrame with the indicator column added
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # Simple moving average
        if indicator_name.lower() in ['sma', 'ma', 'moving_average']:
            result_df[indicator_name] = df['close'].rolling(window=window).mean()
            
        # Exponential moving average
        elif indicator_name.lower() in ['ema', 'exponential_moving_average']:
            result_df[indicator_name] = df['close'].ewm(span=window, adjust=False).mean()
            
        # Relative Strength Index (simplified calculation)
        elif indicator_name.lower() in ['rsi', 'relative_strength_index']:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=window).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
            rs = gain / loss
            result_df[indicator_name] = 100 - (100 / (1 + rs))
            
        # MACD (Moving Average Convergence Divergence)
        elif indicator_name.lower() in ['macd', 'moving_average_convergence_divergence']:
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            result_df[indicator_name] = ema12 - ema26
            result_df[f"{indicator_name}_signal"] = result_df[indicator_name].ewm(span=9, adjust=False).mean()
            
        # Bollinger Bands
        elif indicator_name.lower() in ['bbands', 'bollinger_bands']:
            sma = df['close'].rolling(window=window).mean()
            std = df['close'].rolling(window=window).std()
            result_df[f"{indicator_name}_upper"] = sma + 2 * std
            result_df[f"{indicator_name}_middle"] = sma
            result_df[f"{indicator_name}_lower"] = sma - 2 * std
            
        # ATR (Average True Range)
        elif indicator_name.lower() in ['atr', 'average_true_range']:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            result_df[indicator_name] = true_range.rolling(window=window).mean()
            
        # Stochastic Oscillator
        elif indicator_name.lower() in ['stoch', 'stochastic']:
            low_min = df['low'].rolling(window=window).min()
            high_max = df['high'].rolling(window=window).max()
            k = 100 * ((df['close'] - low_min) / (high_max - low_min))
            result_df[f"{indicator_name}_k"] = k
            result_df[f"{indicator_name}_d"] = k.rolling(window=3).mean()
            
        # Generic oscillator if no specific indicator is matched
        else:
            # Create a sine wave oscillator between 0 and 100
            t = np.arange(len(df))
            period = window * 3  # Multiple of the window for a realistic period
            oscillator = 50 * (1 + np.sin(2 * np.pi * t / period))
            result_df[indicator_name] = oscillator
        
        # Add noise if requested
        if add_noise:
            np.random.seed(self.seed + 5)
            noise = np.random.normal(0, noise_level, size=len(df))
            
            # Add noise to all the newly added columns (those that start with indicator_name)
            for col in result_df.columns:
                if col.startswith(indicator_name) and col not in df.columns:
                    # For percentage indicators (like RSI), keep within bounds after adding noise
                    if 'rsi' in col.lower() or 'stoch' in col.lower():
                        result_df[col] = result_df[col] + noise * 10  # Scaled noise for percentage indicators
                        result_df[col] = np.clip(result_df[col], 0, 100)  # Keep within 0-100 range
                    else:
                        # For price-based indicators, scale noise relative to price level
                        scale = df['close'].mean() * noise_level
                        result_df[col] = result_df[col] + noise * scale
        
        return result_df
    
    def generate_crypto_data(
        self,
        symbol: str,
        market: str = 'USD',
        start_date: str = '2020-01-01',
        end_date: str = '2023-01-01',
        initial_price: float = 10000.0,
        volatility: float = 0.03,
        drift: float = 0.0003,
        freq: str = 'D'
    ) -> pd.DataFrame:
        """
        Generate mock cryptocurrency data with higher volatility than stocks
        
        Args:
            symbol: Cryptocurrency symbol
            market: Market (e.g., USD, EUR)
            start_date: Start date
            end_date: End date
            initial_price: Initial price
            volatility: Daily volatility (higher for crypto)
            drift: Daily drift
            freq: Frequency
            
        Returns:
            DataFrame with cryptocurrency data
        """
        df = self.generate_ohlcv_dataframe(
            symbol=f"{symbol}/{market}",
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_price,
            volatility=volatility,  # Higher volatility for crypto
            drift=drift,
            volume_mean=5000000,  # Higher volume
            volume_std=1000000,
            freq=freq
        )
        
        # Add additional cryptocurrency-specific columns
        df['market_cap'] = df['close'] * df['volume'] * 0.1
        df['supply'] = df['market_cap'] / df['close']
        
        return df
    
    def generate_forex_data(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str = '2020-01-01',
        end_date: str = '2023-01-01',
        initial_rate: float = 1.0,
        volatility: float = 0.005,
        drift: float = 0.0001,
        freq: str = 'D'
    ) -> pd.DataFrame:
        """
        Generate mock forex data
        
        Args:
            from_currency: Base currency
            to_currency: Quote currency
            start_date: Start date
            end_date: End date
            initial_rate: Initial exchange rate
            volatility: Daily volatility (lower for forex)
            drift: Daily drift
            freq: Frequency
            
        Returns:
            DataFrame with forex data
        """
        df = self.generate_ohlcv_dataframe(
            symbol=f"{from_currency}/{to_currency}",
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_rate,
            volatility=volatility,  # Lower volatility for forex
            drift=drift,
            volume_mean=10000000,  # Higher volume for forex
            volume_std=2000000,
            freq=freq
        )
        
        # Drop volume for forex data
        df = df.drop(columns=['volume'])
        
        return df 