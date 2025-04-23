import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import logging
from pathlib import Path

from trading.data.alpha_vantage_client import AlphaVantageClient
from trading.config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Backtester')

class Position:
    """Class representing a trading position"""
    
    def __init__(self, symbol: str, entry_date: datetime, entry_price: float, 
                shares: int, stop_loss_pct: Optional[float] = None, take_profit_pct: Optional[float] = None):
        """
        Initialize a trading position
        
        Parameters:
        -----------
        symbol : str
            Symbol of the traded asset
        entry_date : datetime
            Date and time of position entry
        entry_price : float
            Entry price
        shares : int
            Number of shares (positive for long, negative for short)
        stop_loss_pct : float, optional
            Stop loss percentage (optional)
        take_profit_pct : float, optional
            Take profit percentage (optional)
        """
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0.0
        self.is_open = True
        self.exit_reason = None
        
        # Calculate stop loss and take profit prices if percentages are provided
        if stop_loss_pct:
            self.stop_loss_price = entry_price * (1 - stop_loss_pct)
        else:
            self.stop_loss_price = None
            
        if take_profit_pct:
            self.take_profit_price = entry_price * (1 + take_profit_pct)
        else:
            self.take_profit_price = None
    
    def close(self, exit_date: datetime, exit_price: float, reason: str = "signal"):
        """
        Close the position
        
        Parameters:
        -----------
        exit_date : datetime
            Date and time of position exit
        exit_price : float
            Exit price
        reason : str
            Reason for closing the position (signal, stop_loss, take_profit, etc.)
        """
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_reason = reason
        self.is_open = False
        
        # Calculate profit/loss
        self.pnl = (exit_price - self.entry_price) * self.shares
        
        return self.pnl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'entry_date': self.entry_date.strftime('%Y-%m-%d %H:%M:%S') if self.entry_date else None,
            'entry_price': self.entry_price,
            'shares': self.shares,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'exit_date': self.exit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_date else None,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'is_open': self.is_open,
            'exit_reason': self.exit_reason
        }
    
    def __repr__(self) -> str:
        """String representation of the position"""
        status = "OPEN" if self.exit_price is None else "CLOSED"
        return (
            f"{self.symbol} Position ({status}): {self.shares} shares @ ${self.entry_price:.2f} "
            f"[Entry: {self.entry_date.strftime('%Y-%m-%d')}] "
            f"{f'[Exit: {self.exit_date.strftime('%Y-%m-%d')}, ${self.exit_price:.2f}, {self.exit_reason}]' if self.exit_price else ''} "
            f"Return: ${self.pnl:.2f}"
        )


class Portfolio:
    """Class representing a trading portfolio with multiple positions"""
    
    def __init__(self, initial_capital: float = 100000.0, position_size_pct: float = 0.1,
                max_positions: int = 5, commission: float = 0.0):
        """
        Initialize a trading portfolio
        
        Parameters:
        -----------
        initial_capital : float
            Initial capital in the portfolio
        position_size_pct : float
            Maximum position size as a percentage of the portfolio (0.0 to 1.0)
        max_positions : int
            Maximum number of concurrent positions
        commission : float
            Commission per trade as a percentage (0.0 to 1.0)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        self.commission = commission
        
        self.positions = []  # List of all positions (open and closed)
        self.open_positions = {}  # Dict of open positions by symbol
        
        # Performance tracking
        self.equity_curve = [(datetime.now(), initial_capital)]  # List of (date, equity) tuples
        self.cash_history = {}  # Dict of cash by date
        self.trades_history = []  # List of closed trades
    
    def calculate_shares(self, price: float) -> int:
        """
        Calculate number of shares to buy/sell based on position size
        
        Parameters:
        -----------
        price : float
            Current price of the asset
            
        Returns:
        --------
        int
            Number of shares to buy/sell
        """
        # Calculate maximum amount to invest based on position size
        max_amount = self.cash * self.position_size_pct
        
        # Calculate number of shares (floor to be conservative)
        shares = int(max_amount / price)
        
        return shares
    
    def open_position(self, symbol: str, date: datetime, price: float, 
                     shares: Optional[int] = None, is_long: bool = True,
                     stop_loss_pct: Optional[float] = None, take_profit_pct: Optional[float] = None) -> bool:
        """
        Open a new position
        
        Parameters:
        -----------
        symbol : str
            Symbol of the asset
        date : datetime
            Date and time of position entry
        price : float
            Entry price
        shares : int, optional
            Number of shares (if None, calculated based on position size)
        is_long : bool
            Whether this is a long position (True) or short position (False)
        stop_loss_pct : float, optional
            Stop loss percentage
        take_profit_pct : float, optional
            Take profit percentage
            
        Returns:
        --------
        bool
            True if position was opened successfully, False otherwise
        """
        # Check if we already have a position in this symbol
        if symbol in self.open_positions:
            logger.warning(f"Already have an open position in {symbol}")
            return False
        
        # Check if we've reached the maximum number of positions
        if len(self.open_positions) >= self.max_positions:
            logger.warning("Maximum number of positions reached")
            return False
        
        # Calculate shares if not provided
        if shares is None:
            shares = self.calculate_shares(price)
        
        # Adjust shares for short positions
        if not is_long:
            shares = -shares
        
        # Calculate cost including commission
        cost = price * abs(shares) * (1 + self.commission)
        
        # Check if we have enough cash
        if cost > self.cash:
            logger.warning(f"Not enough cash to open position (needed: {cost}, available: {self.cash})")
            return False
        
        # Create new position
        position = Position(
            symbol=symbol,
            entry_date=date,
            entry_price=price,
            shares=shares,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )
        
        # Update portfolio
        self.cash -= cost
        self.positions.append(position)
        self.open_positions[symbol] = position
        
        # Log position opening
        logger.info(f"Opened {position}")
        
        return True
    
    def close_position(self, position: Position, date: datetime, price: float, reason: str = "signal") -> bool:
        """
        Close an existing position
        
        Parameters:
        -----------
        position : Position
            Position to close
        date : datetime
            Date and time of position exit
        price : float
            Exit price
        reason : str
            Reason for closing the position (signal, stop_loss, take_profit, etc.)
            
        Returns:
        --------
        bool
            True if position was closed successfully, False otherwise
        """
        if not position.is_open:
            logger.warning(f"Position {position.symbol} is already closed")
            return False
        
        # Close the position
        pnl = position.close(date, price, reason)
        
        # Calculate proceeds including commission
        proceeds = price * abs(position.shares) * (1 - self.commission)
        
        # Update portfolio
        self.cash += proceeds
        self.open_positions.pop(position.symbol, None)
        
        # Add to trades history
        self.trades_history.append(position.to_dict())
        
        # Log position closing
        logger.info(f"Closed {position} with PnL: {pnl:.2f}")
        
        return True
    
    def update_equity(self, date: datetime, market_prices: Dict[str, float]):
        """
        Update portfolio equity based on current market prices
        
        Parameters:
        -----------
        date : datetime
            Current date
        market_prices : Dict[str, float]
            Current market prices by symbol
        """
        # Calculate total portfolio value (cash + positions)
        equity = self.cash
        
        for symbol, position in self.open_positions.items():
            # Skip if we don't have a price for this symbol
            if symbol not in market_prices:
                continue
                
            # Calculate position value
            position_value = position.shares * market_prices[symbol]
            equity += position_value
        
        # Update history
        self.equity_curve.append((date, equity))
        self.cash_history[date] = self.cash
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary statistics
        
        Returns:
        --------
        Dict[str, Any]
            Portfolio summary statistics
        """
        # Calculate key metrics
        total_trades = len(self.trades_history)
        winning_trades = sum(1 for trade in self.trades_history if trade['pnl'] > 0)
        losing_trades = sum(1 for trade in self.trades_history if trade['pnl'] < 0)
        
        if total_trades > 0:
            win_rate = winning_trades / total_trades
            
            # Calculate average return per trade
            avg_return = sum(trade['pnl'] for trade in self.trades_history) / total_trades
            
            # Calculate final equity
            final_equity = self.equity_curve[-1][1] if self.equity_curve else self.initial_capital
            
            # Calculate total return
            total_return = (final_equity - self.initial_capital) / self.initial_capital
            
            # Calculate maximum drawdown
            equity_values = [equity for _, equity in self.equity_curve]
            max_drawdown = 0
            peak = equity_values[0]
            
            for value in equity_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
        else:
            win_rate = 0
            avg_return = 0
            final_equity = self.initial_capital
            total_return = 0
            max_drawdown = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return,
            'max_drawdown': max_drawdown,
            'open_positions': len(self.open_positions)
        }


class Backtester:
    """Class for backtesting trading strategies"""
    
    def __init__(self, initial_capital: float = 100000.0, position_size_pct: float = 0.2,
                commission: float = 0.001, stop_loss_pct: Optional[float] = 0.05,
                take_profit_pct: Optional[float] = 0.1, data_dir: str = 'data',
                api_key: Optional[str] = None, use_mock_data: bool = False):
        """
        Initialize the backtester
        
        Parameters:
        -----------
        initial_capital : float
            Initial capital for backtesting
        position_size_pct : float
            Position size as a percentage of portfolio (0.0 to 1.0)
        commission : float
            Commission per trade as a percentage (0.0 to 1.0)
        stop_loss_pct : float, optional
            Default stop loss percentage
        take_profit_pct : float, optional
            Default take profit percentage
        data_dir : str
            Directory to store data and results
        api_key : str, optional
            Alpha Vantage API key
        use_mock_data : bool
            Whether to use mock data instead of real data
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.commission = commission
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.use_mock_data = use_mock_data
        
        # Initialize data fetcher
        self.data_fetcher = AlphaVantageClient(api_key=api_key, cache_dir=f"{data_dir}/cache")
        
        # Initialize portfolio
        self.portfolio = None
        
        # Store market data
        self.market_data = {}
        
        # Store results
        self.results = {}
    
    def load_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Load market data for the given symbols and date range
        
        Parameters:
        -----------
        symbols : List[str]
            List of symbols to load data for
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str
            End date in YYYY-MM-DD format
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary of market data by symbol
        """
        logger.info(f"Loading market data for {len(symbols)} symbols from {start_date} to {end_date}")
        
        self.market_data = {}
        
        for symbol in symbols:
            try:
                if self.use_mock_data:
                    # Use mock data
                    df = get_mock_stock_data(symbol, start_date, end_date)
                    logger.info(f"Using mock data for {symbol}")
                else:
                    # Try to get real data using the daily method from AlphaVantageClient
                    df = self.data_fetcher.get_daily(
                        symbol=symbol,
                        adjusted=True,
                        outputsize='full',
                        start_date=start_date,
                        end_date=end_date,
                        use_cache=True
                    )
                    
                    # Fall back to mock data if real data is empty
                    if df.empty:
                        logger.warning(f"No real data found for {symbol}, using mock data instead")
                        df = get_mock_stock_data(symbol, start_date, end_date)
                
                if df.empty:
                    logger.warning(f"No data found for {symbol}")
                    continue
                
                logger.info(f"Loaded {len(df)} bars for {symbol}")
                self.market_data[symbol] = df
            except Exception as e:
                logger.error(f"Error loading data for {symbol}: {e}")
                logger.info(f"Falling back to mock data for {symbol}")
                try:
                    df = get_mock_stock_data(symbol, start_date, end_date)
                    self.market_data[symbol] = df
                    logger.info(f"Successfully loaded mock data for {symbol}")
                except Exception as mock_err:
                    logger.error(f"Error loading mock data for {symbol}: {mock_err}")
        
        return self.market_data
    
    def generate_signals(self, strategy_name: str, params: Dict[str, Any] = None) -> Dict[str, pd.DataFrame]:
        """
        Generate trading signals using the specified strategy
        
        Parameters:
        -----------
        strategy_name : str
            Name of the strategy to use
        params : Dict[str, Any], optional
            Strategy parameters
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary of signal DataFrames by symbol
        """
        if not self.market_data:
            raise ValueError("No market data loaded. Call load_data() first.")
        
        params = params or {}
        logger.info(f"Generating signals using {strategy_name} strategy with params: {params}")
        
        signals = {}
        
        for symbol, df in self.market_data.items():
            # Skip if dataframe is empty
            if df.empty:
                continue
                
            # Create a copy to avoid modifying the original
            signal_df = df.copy()
            
            # Generate signals based on the specified strategy
            if strategy_name == "sma_crossover":
                signals[symbol] = self._generate_sma_crossover_signals(signal_df, params)
            elif strategy_name == "rsi":
                signals[symbol] = self._generate_rsi_signals(signal_df, params)
            elif strategy_name == "macd":
                signals[symbol] = self._generate_macd_signals(signal_df, params)
            elif strategy_name == "bollinger_bands":
                signals[symbol] = self._generate_bollinger_bands_signals(signal_df, params)
            else:
                logger.warning(f"Unknown strategy: {strategy_name}")
                continue
                
            logger.info(f"Generated signals for {symbol}")
        
        return signals
    
    def _generate_sma_crossover_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate signals using SMA crossover strategy
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data DataFrame
        params : Dict[str, Any]
            Strategy parameters
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with signals
        """
        # Get parameters with defaults
        short_window = params.get("short_window", 20)
        long_window = params.get("long_window", 50)
        
        # Calculate short and long SMA if not already in the dataframe
        if f'sma_{short_window}' not in df.columns:
            df[f'sma_{short_window}'] = df['close'].rolling(window=short_window).mean()
        
        if f'sma_{long_window}' not in df.columns:
            df[f'sma_{long_window}'] = df['close'].rolling(window=long_window).mean()
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signal when short SMA crosses above long SMA
        df.loc[(df[f'sma_{short_window}'] > df[f'sma_{long_window}']) & 
              (df[f'sma_{short_window}'].shift() <= df[f'sma_{long_window}'].shift()), 'signal'] = 1
        
        # Generate sell signal when short SMA crosses below long SMA
        df.loc[(df[f'sma_{short_window}'] < df[f'sma_{long_window}']) & 
              (df[f'sma_{short_window}'].shift() >= df[f'sma_{long_window}'].shift()), 'signal'] = -1
        
        return df
    
    def _generate_rsi_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate signals using RSI strategy
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data DataFrame
        params : Dict[str, Any]
            Strategy parameters
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with signals
        """
        # Get parameters with defaults
        rsi_period = params.get("rsi_period", 14)
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)
        
        # If RSI is not already in the dataframe, calculate it
        if 'rsi' not in df.columns:
            # Calculate RSI using exponential moving average method
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period).mean()
            avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period).mean()
            
            rs = avg_gain / avg_loss
            df['rsi'] = 100 - (100 / (1 + rs))
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signal when RSI crosses above oversold threshold
        df.loc[(df['rsi'] > oversold) & (df['rsi'].shift() <= oversold), 'signal'] = 1
        
        # Generate sell signal when RSI crosses below overbought threshold
        df.loc[(df['rsi'] < overbought) & (df['rsi'].shift() >= overbought), 'signal'] = -1
        
        return df
    
    def _generate_macd_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate signals using MACD strategy
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data DataFrame
        params : Dict[str, Any]
            Strategy parameters
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with signals
        """
        # Get parameters with defaults
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)
        
        # Check if we have precomputed MACD
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            # Calculate MACD
            ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
            ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
            
            df['macd'] = ema_fast - ema_slow
            df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signal when MACD crosses above signal line
        df.loc[(df['macd'] > df['macd_signal']) & 
              (df['macd'].shift() <= df['macd_signal'].shift()), 'signal'] = 1
        
        # Generate sell signal when MACD crosses below signal line
        df.loc[(df['macd'] < df['macd_signal']) & 
              (df['macd'].shift() >= df['macd_signal'].shift()), 'signal'] = -1
        
        return df
    
    def _generate_bollinger_bands_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate signals using Bollinger Bands strategy
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data DataFrame
        params : Dict[str, Any]
            Strategy parameters
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with signals
        """
        # Get parameters with defaults
        window = params.get("window", 20)
        num_std = params.get("num_std", 2)
        
        # Check if we have precomputed Bollinger Bands
        if 'bb_upper' not in df.columns or 'bb_lower' not in df.columns:
            # Calculate Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=window).mean()
            rolling_std = df['close'].rolling(window=window).std()
            
            df['bb_upper'] = df['bb_middle'] + (rolling_std * num_std)
            df['bb_lower'] = df['bb_middle'] - (rolling_std * num_std)
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signal when price crosses below lower band
        df.loc[(df['close'] < df['bb_lower']) & 
              (df['close'].shift() >= df['bb_lower'].shift()), 'signal'] = 1
        
        # Generate sell signal when price crosses above upper band
        df.loc[(df['close'] > df['bb_upper']) & 
              (df['close'].shift() <= df['bb_upper'].shift()), 'signal'] = -1
        
        return df
    
    def run_backtest(self, strategy_name: str, symbols: List[str], start_date: str, 
                   end_date: str, strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a backtest for the given strategy, symbols, and date range
        
        Parameters:
        -----------
        strategy_name : str
            Name of the strategy to backtest
        symbols : List[str]
            List of symbols to backtest
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str
            End date in YYYY-MM-DD format
        strategy_params : Dict[str, Any], optional
            Strategy parameters
            
        Returns:
        --------
        Dict[str, Any]
            Backtest results
        """
        logger.info(f"Running backtest for {strategy_name} on {len(symbols)} symbols from {start_date} to {end_date}")
        
        # Load market data
        self.load_data(symbols, start_date, end_date)
        
        # Generate signals
        signals = self.generate_signals(strategy_name, strategy_params)
        
        # Initialize portfolio
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            position_size_pct=self.position_size_pct,
            commission=self.commission
        )
        
        # Initialize trade log
        trade_log = []
        
        # Sort market data by date
        dates = sorted(set(date for symbol_data in self.market_data.values() for date in symbol_data.index))
        
        # Run the backtest day by day
        for date in dates:
            # Process stop loss and take profit for open positions
            self._process_stop_loss_take_profit(date)
            
            # Process signals for each symbol
            for symbol, signal_df in signals.items():
                if date not in signal_df.index:
                    continue
                    
                signal = signal_df.loc[date, 'signal']
                price = signal_df.loc[date, 'close']
                
                # Process signals
                if signal == 1:  # Buy signal
                    # Check if we have an open position for this symbol
                    if symbol not in self.portfolio.open_positions:
                        # Calculate stop loss and take profit if enabled
                        stop_loss_pct = self.stop_loss_pct if self.stop_loss_pct else None
                        take_profit_pct = self.take_profit_pct if self.take_profit_pct else None
                        
                        # Open a long position
                        self.portfolio.open_position(
                            symbol=symbol,
                            date=date,
                            price=price,
                            is_long=True,
                            stop_loss_pct=stop_loss_pct,
                            take_profit_pct=take_profit_pct
                        )
                        
                        # Log trade
                        trade_log.append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'buy',
                            'price': price,
                            'shares': self.portfolio.open_positions[symbol].shares,
                            'value': price * self.portfolio.open_positions[symbol].shares,
                            'stop_loss_pct': stop_loss_pct,
                            'take_profit_pct': take_profit_pct
                        })
                
                elif signal == -1:  # Sell signal
                    # Check if we have an open position for this symbol
                    if symbol in self.portfolio.open_positions:
                        position = self.portfolio.open_positions[symbol]
                        
                        # Close the position
                        self.portfolio.close_position(
                            position=position,
                            date=date,
                            price=price,
                            reason="signal"
                        )
                        
                        # Log trade
                        trade_log.append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'sell',
                            'price': price,
                            'shares': position.shares,
                            'value': price * position.shares,
                            'pnl': position.pnl
                        })
            
            # Update portfolio equity
            market_prices = {
                symbol: df.loc[date, 'close'] if date in df.index else None 
                for symbol, df in self.market_data.items()
            }
            market_prices = {k: v for k, v in market_prices.items() if v is not None}
            
            self.portfolio.update_equity(date, market_prices)
        
        # Close any remaining positions at the end of the backtest
        for symbol, position in list(self.portfolio.open_positions.items()):
            # Get the last price
            last_date = self.market_data[symbol].index[-1]
            last_price = self.market_data[symbol].loc[last_date, 'close']
            
            # Close the position
            self.portfolio.close_position(
                position=position,
                date=last_date,
                price=last_price,
                reason="end_of_backtest"
            )
            
            # Log trade
            trade_log.append({
                'date': last_date,
                'symbol': symbol,
                'action': 'sell',
                'price': last_price,
                'shares': position.shares,
                'value': last_price * position.shares,
                'pnl': position.pnl
            })
        
        # Get portfolio summary
        summary = self.portfolio.get_portfolio_summary()
        
        # Calculate additional metrics
        equity_curve = pd.Series([equity for date, equity in self.portfolio.equity_curve])
        if len(equity_curve) > 1:
            # Calculate daily returns
            daily_returns = equity_curve.pct_change().dropna()
            
            # Calculate annualized return
            days = (equity_curve.index[-1] - equity_curve.index[0]).days
            annualized_return = (1 + summary['total_return']) ** (365.0 / days) - 1 if days > 0 else 0
            
            # Calculate Sharpe ratio (assuming risk-free rate of 0)
            sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        else:
            annualized_return = 0
            sharpe_ratio = 0
        
        # Store and return results
        self.results = {
            'strategy': strategy_name,
            'params': strategy_params,
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_equity': summary['final_equity'],
            'total_return': summary['total_return'],
            'total_return_pct': summary['total_return'] * 100,
            'annualized_return': annualized_return,
            'annualized_return_pct': annualized_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': summary['max_drawdown'],
            'max_drawdown_pct': summary['max_drawdown'] * 100,
            'total_trades': summary['total_trades'],
            'winning_trades': summary['winning_trades'],
            'losing_trades': summary['losing_trades'],
            'win_rate': summary['win_rate'],
            'win_rate_pct': summary['win_rate'] * 100,
            'equity_curve': equity_curve.to_dict(),
            'trade_log': trade_log
        }
        
        return self.results
    
    def _process_stop_loss_take_profit(self, date: datetime):
        """
        Process stop loss and take profit for open positions
        
        Parameters:
        -----------
        date : datetime
            Current date
        """
        for symbol, position in list(self.portfolio.open_positions.items()):
            # Skip if the symbol is not in the market data
            if symbol not in self.market_data:
                continue
                
            # Skip if the date is not in the market data
            if date not in self.market_data[symbol].index:
                continue
                
            # Get the current price
            price = self.market_data[symbol].loc[date, 'close']
            
            # Check stop loss
            if position.stop_loss_price is not None and position.shares > 0 and price <= position.stop_loss_price:
                # Close the position
                self.portfolio.close_position(
                    position=position,
                    date=date,
                    price=price,
                    reason="stop_loss"
                )
                
                # Log trade
                logger.info(f"Stop loss triggered for {symbol} at {price}")
            
            # Check take profit
            elif position.take_profit_price is not None and position.shares > 0 and price >= position.take_profit_price:
                # Close the position
                self.portfolio.close_position(
                    position=position,
                    date=date,
                    price=price,
                    reason="take_profit"
                )
                
                # Log trade
                logger.info(f"Take profit triggered for {symbol} at {price}")
    
    def plot_results(self, include_trades: bool = True, save_path: Optional[str] = None):
        """
        Plot backtest results
        
        Parameters:
        -----------
        include_trades : bool
            Whether to include trade markers on the equity curve
        save_path : str, optional
            Path to save the plot
        """
        if not self.results:
            raise ValueError("No backtest results. Call run_backtest() first.")
        
        # Convert equity curve from dict to Series
        equity_curve = pd.Series(self.results['equity_curve'])
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot equity curve
        equity_curve.plot(ax=ax)
        
        # Add trade markers if requested
        if include_trades and 'trade_log' in self.results:
            trade_log = pd.DataFrame(self.results['trade_log'])
            trade_log['date'] = pd.to_datetime(trade_log['date'])
            
            # Plot buy trades
            buy_trades = trade_log[trade_log['action'] == 'buy']
            if not buy_trades.empty:
                buy_dates = buy_trades['date']
                buy_equity = [equity_curve[date] if date in equity_curve.index else None for date in buy_dates]
                buy_equity = [e for e in buy_equity if e is not None]
                buy_dates = buy_dates[:len(buy_equity)]  # Ensure same length
                
                if len(buy_dates) > 0:
                    ax.scatter(buy_dates, buy_equity, color='green', marker='^', s=100, label='Buy')
            
            # Plot sell trades
            sell_trades = trade_log[trade_log['action'] == 'sell']
            if not sell_trades.empty:
                sell_dates = sell_trades['date']
                sell_equity = [equity_curve[date] if date in equity_curve.index else None for date in sell_dates]
                sell_equity = [e for e in sell_equity if e is not None]
                sell_dates = sell_dates[:len(sell_equity)]  # Ensure same length
                
                if len(sell_dates) > 0:
                    ax.scatter(sell_dates, sell_equity, color='red', marker='v', s=100, label='Sell')
        
        # Add title and labels
        strategy_name = self.results.get('strategy', 'Unknown')
        symbols = self.results.get('symbols', [])
        symbols_str = ', '.join(symbols) if len(symbols) <= 5 else f"{', '.join(symbols[:5])}... ({len(symbols)} total)"
        
        ax.set_title(f"{strategy_name} Strategy Backtest Results on {symbols_str}")
        ax.set_xlabel('Date')
        ax.set_ylabel('Equity')
        ax.grid(True)
        
        # Add legend
        ax.legend()
        
        # Add performance summary
        summary_text = (
            f"Initial Capital: ${self.results['initial_capital']:,.2f}\n"
            f"Final Equity: ${self.results['final_equity']:,.2f}\n"
            f"Total Return: {self.results['total_return_pct']:.2f}%\n"
            f"Annualized Return: {self.results['annualized_return_pct']:.2f}%\n"
            f"Sharpe Ratio: {self.results['sharpe_ratio']:.2f}\n"
            f"Max Drawdown: {self.results['max_drawdown_pct']:.2f}%\n"
            f"Win Rate: {self.results['win_rate_pct']:.2f}%\n"
            f"Total Trades: {self.results['total_trades']}"
        )
        
        # Position the summary box
        plt.figtext(0.15, 0.15, summary_text, fontsize=10, 
                  bbox=dict(facecolor='white', alpha=0.8))
        
        # Save if requested
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved plot to {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def save_results(self, save_path: str):
        """
        Save backtest results to file
        
        Parameters:
        -----------
        save_path : str
            Path to save the results
        """
        if not self.results:
            raise ValueError("No backtest results. Call run_backtest() first.")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Convert pandas objects to serializable format
        results_json = self.results.copy()
        
        # Save to file
        with open(save_path, 'w') as f:
            json.dump(results_json, f, indent=4, default=str)
        
        logger.info(f"Saved results to {save_path}")


# Example usage
if __name__ == "__main__":
    # Example parameters
    symbols = ["AAPL", "MSFT", "GOOGL"]
    start_date = "2022-01-01"
    end_date = "2023-01-01"
    strategy_name = "sma_crossover"
    strategy_params = {
        "short_window": 20,
        "long_window": 50
    }
    
    # Create backtester
    backtester = Backtester(
        initial_capital=100000.0,
        position_size_pct=0.2,
        commission=0.001,
        stop_loss_pct=0.05,
        take_profit_pct=0.1
    )
    
    # Run backtest
    results = backtester.run_backtest(
        strategy_name=strategy_name,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategy_params=strategy_params
    )
    
    # Plot results
    backtester.plot_results()
    
    # Save results
    backtester.save_results("results/sma_crossover_backtest.json") 