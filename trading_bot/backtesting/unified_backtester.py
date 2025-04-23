import os
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
from trading_bot.risk import RiskManager, RiskMonitor
from trading_bot.strategy.strategy_rotator import StrategyRotator
from trading_bot.backtesting.plotting import (
    plot_equity_curve, plot_drawdowns, plot_monthly_returns, 
    plot_rolling_metrics, plot_returns_distribution, 
    plot_correlation_matrix, plot_strategy_allocations,
    plot_regime_analysis, create_performance_dashboard
)

# Initialize logger
logger = logging.getLogger(__name__)

class UnifiedBacktester:
    """
    Unified backtesting system for strategy rotation.
    
    This class provides backtesting capabilities for the strategy rotation system,
    simulating trading over a historical period and calculating performance metrics.
    """
    
    def __init__(
        self, 
        initial_capital: float = 100000.0,
        strategies: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        rebalance_frequency: str = "weekly",
        benchmark_symbol: str = "SPY",
        data_dir: str = "data",
        results_path: str = "data/backtest_results",
        use_mock: bool = False,
        risk_free_rate: float = 0.02,  # 2% annual risk-free rate
        trading_cost_pct: float = 0.1,  # 0.1% trading cost
        **kwargs
    ):
        """
        Initialize the backtester.
        
        Args:
            initial_capital: Starting capital for the backtest
            strategies: List of strategy names to include
            start_date: Start date for the backtest (YYYY-MM-DD)
            end_date: End date for the backtest (YYYY-MM-DD)
            rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly')
            benchmark_symbol: Symbol for benchmark comparison
            data_dir: Directory for data files
            results_path: Path to save backtest results
            use_mock: Whether to use mock data for strategies
            risk_free_rate: Annual risk-free rate (decimal form)
            trading_cost_pct: Trading cost as percentage
            **kwargs: Additional keyword arguments
        """
        self.initial_capital = initial_capital
        self.strategies = strategies or ["trend_following", "momentum", "mean_reversion"]
        
        # Set date range (default to last 1 year if not specified)
        today = datetime.now()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else today
        
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            self.start_date = today - timedelta(days=365)  # Default to 1 year
        
        self.benchmark_symbol = benchmark_symbol
        self.data_dir = Path(data_dir)
        self.results_path = results_path
        self.use_mock = use_mock
        self.risk_free_rate = risk_free_rate
        self.trading_cost_pct = trading_cost_pct
        
        # Set rebalance frequency
        self.rebalance_frequency = rebalance_frequency
        self.rebalance_days = self._get_rebalance_days(rebalance_frequency)
        
        # Initial allocations (equal weight by default)
        self.initial_allocations = kwargs.get("initial_allocations", {})
        if not self.initial_allocations:
            allocation = 100.0 / len(self.strategies) if self.strategies else 0
            self.initial_allocations = {strategy: allocation for strategy in self.strategies}
        
        # Initialize strategy rotator with risk management
        rotator_kwargs = {
            "initial_capital": initial_capital,
            "trading_cost_pct": trading_cost_pct,
            "risk_config": kwargs.get("risk_config", self._load_risk_config()),
            "enable_risk_management": kwargs.get("enable_risk_management", True),
            "enable_circuit_breakers": kwargs.get("enable_circuit_breakers", True),
            "enable_dynamic_sizing": kwargs.get("enable_dynamic_sizing", True)
        }
        
        self.strategy_rotator = StrategyRotator(
            strategies=self.strategies,
            initial_allocations=self.initial_allocations,
            **rotator_kwargs
        )
        
        # Initialize risk management components
        risk_config = kwargs.get("risk_config", self._load_risk_config())
        self.risk_manager = RiskManager(risk_config)
        self.risk_monitor = RiskMonitor(risk_config)
        
        # Risk management settings
        self.enable_risk_management = kwargs.get("enable_risk_management", True)
        
        # Initialize data containers
        self.strategy_data = {}
        self.market_data = pd.DataFrame()
        self.regime_data = pd.DataFrame()
        self.benchmark_data = pd.DataFrame()
        
        # Performance tracking
        self.portfolio_history = []
        self.allocation_history = []
        self.debug_data = []
        self.trades = []  # List to track all trades
        self.total_costs = 0.0  # Track total trading costs
        
        # Trade execution parameters
        self.min_trade_value = kwargs.get("min_trade_value", 100.0)  # Minimum $ value for a trade
        
        # Debug mode
        self.debug_mode = kwargs.get("debug_mode", False)
        
        # Order execution settings
        self.order_settings = kwargs.get("order_settings", {
            "order_type": "market",               # Options: market, limit, vwap, close
            "slippage_model": "percentage",       # Options: percentage, fixed, volume_based, volatility_based
            "slippage_value": 0.1,                # Default 0.1% slippage
            "limit_offset_pct": 0.2,              # For limit orders: 0.2% away from market
            "enable_market_impact": False,        # Whether to model market impact
            "market_impact_constant": 0.1         # Constant for market impact calculation
        })
    
    def _load_risk_config(self):
        """Load risk management configuration."""
        try:
            with open("configs/risk_config.json", "r") as f:
                config = json.load(f)
                logger.info("Loaded risk configuration file")
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Risk configuration file not found or invalid. Using defaults.")
            return {}
        
    def _get_rebalance_days(self, frequency: str) -> int:
        """
        Convert rebalance frequency string to number of days.
        
        Args:
            frequency: Frequency string ('daily', 'weekly', 'monthly')
            
        Returns:
            Number of days between rebalances
        """
        frequency_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90
        }
        
        return frequency_map.get(frequency.lower(), 7)  # Default to weekly
    
    def load_strategy_data(self) -> None:
        """
        Load historical strategy performance data.
        
        This method attempts to load strategy data from files.
        If use_mock is True or files aren't found, it generates mock data.
        """
        self.strategy_data = {}
        
        for strategy in self.strategies:
            try:
                if self.use_mock:
                    raise FileNotFoundError("Using mock data")
                
                # Attempt to load strategy data from file
                file_path = self.data_dir / f"strategy_{strategy}.csv"
                data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                
                # Filter to relevant date range
                mask = (data.index >= self.start_date.date()) & (data.index <= self.end_date.date())
                self.strategy_data[strategy] = data.loc[mask]
                
                logger.info(f"Loaded data for strategy {strategy} with {len(data.loc[mask])} data points")
                
            except (FileNotFoundError, pd.errors.EmptyDataError):
                logger.warning(f"No data found for strategy {strategy}. Using mock data.")
                self.strategy_data[strategy] = self._generate_mock_strategy_data(strategy)
    
    def load_market_data(self) -> None:
        """
        Load historical market data for context.
        
        This method attempts to load market data from files.
        If use_mock is True or files aren't found, it generates mock data.
        """
        try:
            if self.use_mock:
                raise FileNotFoundError("Using mock data")
            
            # Attempt to load market data from file
            file_path = self.data_dir / "market_data.csv"
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter to relevant date range
            mask = (data.index >= self.start_date.date()) & (data.index <= self.end_date.date())
            self.market_data = data.loc[mask]
            
            logger.info(f"Loaded market data with {len(data.loc[mask])} data points")
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            logger.warning("No market data found. Using mock data.")
            self.market_data = self._generate_mock_market_data()
    
    def load_regime_data(self) -> None:
        """
        Load historical market regime data.
        
        This method attempts to load regime data from files.
        If use_mock is True or files aren't found, it generates mock data.
        """
        try:
            if self.use_mock:
                raise FileNotFoundError("Using mock data")
            
            # Attempt to load regime data from file
            file_path = self.data_dir / "regime_data.csv"
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter to relevant date range
            mask = (data.index >= self.start_date.date()) & (data.index <= self.end_date.date())
            self.regime_data = data.loc[mask]
            
            logger.info(f"Loaded regime data with {len(data.loc[mask])} data points")
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            logger.warning("No regime data found. Using mock data.")
            self.regime_data = self._generate_mock_regime_data()
    
    def load_benchmark_data(self) -> None:
        """
        Load historical benchmark data.
        
        This method attempts to load benchmark data from files.
        If use_mock is True or files aren't found, it generates mock data.
        """
        try:
            if self.use_mock:
                raise FileNotFoundError("Using mock data")
            
            # Attempt to load benchmark data from file
            file_path = self.data_dir / f"benchmark_{self.benchmark_symbol}.csv"
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter to relevant date range
            mask = (data.index >= self.start_date.date()) & (data.index <= self.end_date.date())
            self.benchmark_data = data.loc[mask]
            
            logger.info(f"Loaded benchmark data with {len(data.loc[mask])} data points")
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            logger.warning(f"No benchmark data found for {self.benchmark_symbol}. Using mock data.")
            self.benchmark_data = self._generate_mock_benchmark_data()
    
    def _generate_rebalance_dates(self) -> List[datetime]:
        """
        Generate a list of rebalance dates based on frequency.
        
        Returns:
            List of datetime objects for rebalance dates
        """
        rebalance_dates = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # 0-4 are weekdays
                rebalance_dates.append(current_date)
            
            # Move to next rebalance date
            if self.rebalance_frequency == "daily":
                current_date += timedelta(days=1)
            elif self.rebalance_frequency == "weekly":
                # Find next Monday
                days_to_add = 7 - current_date.weekday() if current_date.weekday() > 0 else 7
                current_date += timedelta(days=days_to_add)
            elif self.rebalance_frequency == "monthly":
                # Move to 1st of next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
            else:
                # Default to weekly
                days_to_add = 7 - current_date.weekday() if current_date.weekday() > 0 else 7
                current_date += timedelta(days=days_to_add)
        
        return rebalance_dates
    
    def _get_historical_market_context(self, date: datetime) -> Dict[str, Any]:
        """
        Get historical market context for a specific date.
        
        Args:
            date: Date to get context for
            
        Returns:
            Dictionary with market context
        """
        context = {
            "date": date,
            "market_regime": "neutral",  # Default
            "volatility": 0.5,  # Default normalized volatility (0-1)
            "trend_strength": 0.5,  # Default trend strength (0-1)
            "interest_rate": self.risk_free_rate
        }
        
        # Try to get market regime from data
        if not self.regime_data.empty:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.regime_data.index:
                regime_row = self.regime_data.loc[date_str]
                context["market_regime"] = regime_row.get("regime", "neutral")
        
        # Try to get volatility and trend indicators from market data
        if not self.market_data.empty:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.market_data.index:
                market_row = self.market_data.loc[date_str]
                
                # Get VIX (normalize to 0-1 scale, assuming 10-40 range)
                if "vix" in market_row:
                    vix = market_row["vix"]
                    # Handle the case when vix is a Series
                    if isinstance(vix, pd.Series):
                        vix = vix.iloc[0] if not vix.empty else 15.0  # Default to 15 if empty
                    # Handle NaN values
                    if pd.isna(vix):
                        vix = 15.0  # Default value if NaN
                    context["volatility"] = min(1.0, max(0.0, (vix - 10) / 30))
                
                # Estimate trend strength
                if "index_value" in market_row and len(self.market_data) > 20:
                    # Use 20-day vs 200-day moving average ratio as trend indicator
                    current_idx = self.market_data.index.get_loc(date_str)
                    if current_idx >= 20:
                        ma_20 = self.market_data["index_value"].iloc[current_idx-20:current_idx].mean()
                        
                        if current_idx >= 200:
                            ma_200 = self.market_data["index_value"].iloc[current_idx-200:current_idx].mean()
                            ratio = ma_20 / ma_200
                            # Normalize to 0-1 (0.9-1.1 is typical range)
                            context["trend_strength"] = min(1.0, max(0.0, (ratio - 0.9) * 5))
        
        return context
    
    def _should_rebalance(self, date: datetime) -> bool:
        """
        Determine if rebalancing should occur on the given date.
        
        Args:
            date: Date to check
            
        Returns:
            Boolean indicating whether to rebalance
        """
        if self.rebalance_frequency == "daily":
            return True
        
        if self.rebalance_frequency == "weekly":
            return date.weekday() == 0  # Monday
        
        if self.rebalance_frequency == "monthly":
            return date.day == 1
        
        return False
    
    def _execute_trades(self, date_str: str, new_allocations: Dict[str, float], current_capital: float, current_positions: Dict[str, float]) -> None:
        """
        Execute trades to achieve new allocations.
        
        Args:
            date_str: Date string for the trades
            new_allocations: New target allocations
            current_capital: Current portfolio value
            current_positions: Current positions by strategy
        """
        if self.debug_mode:
            logger.info(f"Executing trades on {date_str}")
            logger.info(f"Current positions: {current_positions}")
            logger.info(f"New allocations: {new_allocations}")
            logger.info(f"Current capital: ${current_capital:.2f}")
        
        # Track portfolio value before trades
        pre_trade_value = sum(current_positions.values())
        
        # Convert date string to datetime for market data lookup
        trade_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Calculate target position values
        target_positions = {}
        for strategy in self.strategies:
            # Get allocation (default to 0 if not specified)
            allocation_pct = new_allocations.get(strategy, 0)
            # Calculate target position value
            target_positions[strategy] = (allocation_pct / 100.0) * current_capital
        
        # Track trades for analysis
        trades = []
        total_costs = 0.0
        
        # Execute trades to reach target positions
        for strategy in self.strategies:
            current_value = current_positions.get(strategy, 0)
            target_value = target_positions.get(strategy, 0)
            trade_value = target_value - current_value
            
            # Only trade if difference is significant
            if abs(trade_value) > self.min_trade_value:
                # Get market data for this strategy on this date for price information
                strategy_data = self._get_strategy_price_data(strategy, trade_date)
                
                # Determine trade direction
                direction = 'buy' if trade_value > 0 else 'sell'
                
                # Get order settings from backtest configuration
                order_type = self.order_settings.get('order_type', 'market')
                slippage_model = self.order_settings.get('slippage_model', 'percentage')
                
                # Calculate the fill price based on order type and market data
                fill_price, fill_ratio = self._calculate_fill_price(
                    strategy_data,
                    direction,
                    abs(trade_value),
                    order_type
                )
                
                # Apply slippage to the fill price
                fill_price = self._apply_slippage(
                    fill_price, 
                    direction,
                    slippage_model, 
                    abs(trade_value),
                    strategy_data
                )
                
                # Calculate the actual filled value (may be less than requested due to liquidity)
                filled_value = abs(trade_value) * fill_ratio
                
                # Calculate trading cost (commission + market impact)
                base_cost = filled_value * (self.trading_cost_pct / 100.0)
                market_impact_cost = self._calculate_market_impact(filled_value, strategy_data)
                total_cost = base_cost + market_impact_cost
                total_costs += total_cost
                
                # Record the trade with enhanced details
                trade = {
                    'date': date_str,
                    'strategy': strategy,
                    'direction': direction,
                    'requested_value': abs(trade_value),
                    'filled_value': filled_value,
                    'fill_ratio': fill_ratio,
                    'fill_price': fill_price,
                    'base_cost': base_cost,
                    'market_impact_cost': market_impact_cost,
                    'total_cost': total_cost,
                    'pre_trade_position': current_value,
                    'target_position': target_value,
                    'order_type': order_type
                }
                trades.append(trade)
                self.trades.append(trade)
                
                # Update position based on the actual filled amount and costs
                filled_value_with_direction = filled_value if direction == 'buy' else -filled_value
                current_positions[strategy] = current_value + filled_value_with_direction - total_cost
            else:
                # Position change too small, keep current position
                # Skip updating to avoid rounding errors
                pass
        
        # Update total trading costs
        self.total_costs += total_costs
        
        # Ensure all strategies are in current_positions
        for strategy in self.strategies:
            if strategy not in current_positions:
                current_positions[strategy] = 0
        
        # Calculate post-trade portfolio value
        post_trade_value = sum(current_positions.values())
        
        if trades and self.debug_mode:
            logger.info(f"Executed {len(trades)} trades with total cost ${total_costs:.2f}")
            logger.info(f"Pre-trade portfolio value: ${pre_trade_value:.2f}")
            logger.info(f"Post-trade portfolio value: ${post_trade_value:.2f}")
            logger.info(f"Portfolio value impact: ${post_trade_value - pre_trade_value:.2f}")
            logger.info(f"Updated positions: {current_positions}")
    
    def _get_strategy_price_data(self, strategy: str, date: datetime) -> Dict:
        """
        Get price and volume data for a strategy on a specific date.
        
        Args:
            strategy: Strategy name
            date: Trade date
        
        Returns:
            Dictionary with price and volume data
        """
        # Default values if data not available
        price_data = {
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 1000000,
            'avg_volume': 1000000,
            'volatility': 0.01
        }
        
        try:
            # Check if we have actual price data for this strategy
            if strategy in self.strategy_data and date.date() in self.strategy_data[strategy].index:
                data = self.strategy_data[strategy].loc[date.date()]
                
                # Only override default values for fields that exist in the data
                if hasattr(data, 'open'):
                    price_data['open'] = data.open
                if hasattr(data, 'high'):
                    price_data['high'] = data.high
                if hasattr(data, 'low'):
                    price_data['low'] = data.low
                if hasattr(data, 'close'):
                    price_data['close'] = data.close
                if hasattr(data, 'volume'):
                    price_data['volume'] = data.volume
                
                # Calculate average volume if we have a volume history
                if hasattr(data, 'volume'):
                    # Get historical volume for the past 20 days
                    try:
                        historical_vol = self.strategy_data[strategy]['volume'].rolling(window=20).mean()
                        if date.date() in historical_vol.index:
                            price_data['avg_volume'] = historical_vol.loc[date.date()]
                    except:
                        pass  # Use default if calculation fails
                
                # Calculate historical volatility if possible
                try:
                    returns = self.strategy_data[strategy]['return'].rolling(window=20).std()
                    if date.date() in returns.index:
                        price_data['volatility'] = returns.loc[date.date()] * np.sqrt(252)
                except:
                    pass  # Use default if calculation fails
        except Exception as e:
            if self.debug_mode:
                logger.warning(f"Error getting price data for {strategy} on {date}: {e}")
        
        return price_data
    
    def _calculate_fill_price(self, price_data: Dict, direction: str, trade_value: float, order_type: str = 'market') -> Tuple[float, float]:
        """
        Calculate the fill price and fill ratio based on order type and market data.
        
        Args:
            price_data: Dictionary with price information
            direction: 'buy' or 'sell'
            trade_value: Absolute value of the trade
            order_type: Type of order ('market', 'limit', etc.)
        
        Returns:
            Tuple of (fill_price, fill_ratio) where fill_ratio is between 0 and 1
        """
        # Get basic price levels
        open_price = price_data.get('open', 100.0)
        high_price = price_data.get('high', 101.0)
        low_price = price_data.get('low', 99.0)
        close_price = price_data.get('close', 100.0)
        volume = price_data.get('volume', 1000000)
        
        # Default to full fill
        fill_ratio = 1.0
        
        # Calculate fill price based on order type
        if order_type == 'market':
            # Market orders get executed at a price between open and close,
            # with a bias toward the direction of the day's movement
            if high_price > open_price and low_price < open_price:  # Normal intraday range
                # For buys, bias toward higher prices; for sells, bias toward lower prices
                if direction == 'buy':
                    # Weighted average of open and high, leaning toward high on up days
                    fill_price = open_price + (high_price - open_price) * 0.6
                else:  # sell
                    # Weighted average of open and low, leaning toward low on down days
                    fill_price = open_price - (open_price - low_price) * 0.6
            else:
                # If abnormal range (e.g., gap day), use midpoint
                fill_price = (open_price + close_price) / 2
        
        elif order_type == 'limit':
            # For a limit order simulation, we need a limit price
            limit_offset_pct = self.order_settings.get('limit_offset_pct', 0.2)
            
            if direction == 'buy':
                # Buy limit is set below the open price
                limit_price = open_price * (1 - limit_offset_pct / 100)
                
                # Only fills if the price went low enough to hit the limit
                if low_price <= limit_price:
                    fill_price = limit_price
                    
                    # Calculate what percentage of the day the price was below limit
                    # This is a simplification, but gives a reasonable approximation
                    price_range = high_price - low_price
                    below_limit_range = limit_price - low_price
                    time_below_limit = below_limit_range / price_range if price_range > 0 else 0
                    
                    # Adjust fill ratio based on time below limit and volume
                    fill_ratio = min(1.0, time_below_limit * 0.8 + 0.2)
                else:
                    # Limit not hit, no fill
                    fill_price = open_price  # Placeholder, not used
                    fill_ratio = 0.0
            else:  # sell
                # Sell limit is set above the open price
                limit_price = open_price * (1 + limit_offset_pct / 100)
                
                # Only fills if the price went high enough to hit the limit
                if high_price >= limit_price:
                    fill_price = limit_price
                    
                    # Calculate what percentage of the day the price was above limit
                    price_range = high_price - low_price
                    above_limit_range = high_price - limit_price
                    time_above_limit = above_limit_range / price_range if price_range > 0 else 0
                    
                    # Adjust fill ratio based on time above limit and volume
                    fill_ratio = min(1.0, time_above_limit * 0.8 + 0.2)
                else:
                    # Limit not hit, no fill
                    fill_price = open_price  # Placeholder, not used
                    fill_ratio = 0.0
        
        elif order_type == 'vwap':
            # Volume-weighted average price - typically between open and close
            # We simulate this with a point between open and close
            fill_price = (open_price + close_price) / 2
            
            # VWAP orders typically get good fills
            fill_ratio = 1.0
        
        elif order_type == 'close':
            # Market-on-close orders get the closing price
            fill_price = close_price
            fill_ratio = 1.0
        
        else:  # default fallback
            fill_price = close_price
            fill_ratio = 1.0
        
        # Adjust fill ratio based on trade size relative to volume
        # Large trades may not be fully filled
        if volume > 0:
            # Assume a trade value representing more than 5% of daily volume won't be fully filled
            max_fill_value = volume * close_price * 0.05
            if trade_value > max_fill_value:
                # Reduce fill ratio based on how much the trade exceeds the max fill value
                volume_based_fill_ratio = max_fill_value / trade_value
                # Combine with the order-type-based fill ratio
                fill_ratio = min(fill_ratio, volume_based_fill_ratio)
        
        return fill_price, fill_ratio
    
    def _apply_slippage(self, base_price: float, direction: str, slippage_model: str, trade_value: float, price_data: Dict) -> float:
        """
        Apply slippage to the base fill price.
        
        Args:
            base_price: Base fill price before slippage
            direction: 'buy' or 'sell'
            slippage_model: Type of slippage model to use
            trade_value: Absolute value of the trade
            price_data: Dictionary with price and volume information
        
        Returns:
            Adjusted price after slippage
        """
        # Get slippage parameters
        slippage_value = self.order_settings.get('slippage_value', 0.1)  # Default 0.1%
        
        # Adjust price based on slippage model
        if slippage_model == 'percentage':
            # Simple percentage of price
            slippage_amount = base_price * (slippage_value / 100.0)
            
            if direction == 'buy':
                # For buys, slippage increases price
                return base_price + slippage_amount
            else:
                # For sells, slippage decreases price
                return base_price - slippage_amount
        
        elif slippage_model == 'fixed':
            # Fixed amount per trade
            if direction == 'buy':
                return base_price + slippage_value
            else:
                return base_price - slippage_value
        
        elif slippage_model == 'volume_based':
            # Slippage increases with trade size relative to average volume
            avg_volume = price_data.get('avg_volume', 1000000)
            volume_ratio = trade_value / (avg_volume * base_price)
            
            # Square root model: slippage ~ sqrt(volume_ratio)
            volume_factor = min(3.0, np.sqrt(volume_ratio) * 10)
            slippage_amount = base_price * (slippage_value / 100.0) * volume_factor
            
            if direction == 'buy':
                return base_price + slippage_amount
            else:
                return base_price - slippage_amount
        
        elif slippage_model == 'volatility_based':
            # Slippage increases with volatility
            volatility = price_data.get('volatility', 0.01)
            vol_factor = min(3.0, volatility * 10)  # Cap at 3x multiplier
            
            slippage_amount = base_price * (slippage_value / 100.0) * vol_factor
            
            if direction == 'buy':
                return base_price + slippage_amount
            else:
                return base_price - slippage_amount
        
        else:  # default fallback
            return base_price
    
    def _calculate_market_impact(self, trade_value: float, price_data: Dict) -> float:
        """
        Calculate the market impact cost of a trade.
        
        Args:
            trade_value: Absolute value of the trade
            price_data: Dictionary with price and volume information
        
        Returns:
            Market impact cost
        """
        # Get parameters
        enable_market_impact = self.order_settings.get('enable_market_impact', False)
        
        if not enable_market_impact:
            return 0.0
        
        # Get volume data
        avg_volume = price_data.get('avg_volume', 1000000)
        close_price = price_data.get('close', 100.0)
        
        # Calculate volume in dollars
        avg_volume_value = avg_volume * close_price
        
        # Calculate market impact using square root rule
        # Impact = c * sigma * sqrt(Q/V)
        # where c is a constant, sigma is volatility, Q is trade size, V is avg volume
        c = self.order_settings.get('market_impact_constant', 0.1)
        volatility = price_data.get('volatility', 0.01)
        
        volume_ratio = trade_value / avg_volume_value
        impact_pct = c * volatility * np.sqrt(volume_ratio)
        
        # Convert percentage impact to dollar amount
        impact_cost = trade_value * impact_pct
        
        return impact_cost
    
    def step(self, current_date):
        """
        Simulate a single day in the backtest.
        
        Args:
            current_date: Current simulation date
        """
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Get current portfolio state from the most recent history entry
        latest_portfolio = self.portfolio_history[-1]
        current_capital = latest_portfolio['capital']
        current_positions = latest_portfolio['positions']
        
        # Get daily returns for each strategy
        daily_returns = {}
        for strategy in self.strategies:
            try:
                # Look up the return for this strategy on this date
                if current_date.date() in self.strategy_data[strategy].index:
                    daily_return = self.strategy_data[strategy].loc[current_date.date(), 'return']
                else:
                    # If no data for this date, assume no change
                    daily_return = 0.0
                
                daily_returns[strategy] = daily_return
            except Exception as e:
                logger.warning(f"No return data for {strategy} on {date_str}: {e}")
                daily_returns[strategy] = 0.0
        
        # Update portfolio value based on daily returns
        previous_value = current_capital
        for strategy, position in current_positions.items():
            # Apply daily return to position value
            current_positions[strategy] = position * (1 + daily_returns.get(strategy, 0))
        
        # Calculate new portfolio value
        current_capital = sum(current_positions.values())
        
        # Calculate daily portfolio return
        daily_portfolio_return = (current_capital / previous_value) - 1 if previous_value > 0 else 0.0
        
        # Update risk manager and monitor
        if self.enable_risk_management:
            # Update RiskManager
            self.risk_manager.update_portfolio_value(current_capital, current_date)
            
            # Update RiskMonitor with daily return for volatility tracking
            self.risk_monitor.update_portfolio(
                portfolio_id="main", 
                value=current_capital,
                return_value=daily_portfolio_return,
                timestamp=current_date
            )
            
            # Check for risk anomalies and record them
            anomalies = self.risk_monitor.detect_anomalies("main")
            if anomalies and len(anomalies) > 0:
                # Log the anomalies
                for anomaly in anomalies:
                    logger.warning(f"Risk anomaly detected on {date_str}: {anomaly['type']} - {anomaly['description']}")
                
                # Record anomaly in debug data
                self.debug_data.append({
                    "date": current_date,
                    "type": "risk_anomaly",
                    "anomalies": anomalies,
                    "portfolio_value": current_capital,
                    "daily_return": daily_portfolio_return
                })
                
                # If severe anomaly, trigger emergency risk controls
                if any(a.get('severity', 'medium') == 'high' for a in anomalies):
                    self._apply_emergency_risk_controls(current_date, current_positions, current_capital)
        
        # Perform rebalancing if necessary
        if self._should_rebalance(current_date):
            # Get market context for this date
            market_context = self._get_historical_market_context(current_date)
            
            # Apply risk management checks before rotation
            if self.enable_risk_management:
                # Check circuit breakers
                circuit_breaker_status = self.risk_manager.check_circuit_breakers(current_date)
                
                if circuit_breaker_status['active']:
                    logger.warning(f"Circuit breaker active on {date_str}. Level: {circuit_breaker_status['level']}. "
                                  f"Cause: {circuit_breaker_status['trigger_cause']}. "
                                  f"Limiting allocation changes.")
                    
                    # Record circuit breaker activation in debug data
                    self.debug_data.append({
                        "date": current_date,
                        "type": "circuit_breaker",
                        "status": circuit_breaker_status,
                        "portfolio_value": current_capital
                    })
                
                # Apply volatility-based position sizing
                volatility_adjustment = self._calculate_volatility_adjustment(market_context)
                
                # Run stress tests periodically or on high volatility days
                if current_date.day == 1 or market_context['volatility'] > 0.7 or circuit_breaker_status['active']:
                    strategy_profiles = self._get_strategy_profiles()
                    
                    # Get current allocations
                    current_allocations = {}
                    for strategy, position in current_positions.items():
                        current_allocations[strategy] = (position / current_capital) * 100 if current_capital > 0 else 0
                    
                    # Run stress test
                    stress_results = self.risk_monitor.run_stress_test(
                        "main", 
                        current_allocations,
                        strategy_profiles
                    )
                    
                    # Apply stress test results to adjust risk controls if necessary
                    if stress_results.get('risk_level', 'low') in ['high', 'extreme']:
                        logger.warning(f"Stress test indicates {stress_results['risk_level']} risk on {date_str}. "
                                      f"Max drawdown projection: {stress_results.get('projected_max_drawdown', 0):.2f}%")
                        
                        # Adjust volatility control based on stress test results
                        volatility_adjustment *= self._get_stress_test_adjustment(stress_results)
                    
                    if self.debug_mode:
                        logger.info(f"Stress test results for {date_str}: {stress_results}")
                        logger.info(f"Volatility adjustment factor: {volatility_adjustment:.2f}")
            
            # Update strategy rotator with current portfolio value
            self.strategy_rotator.update_portfolio_value(current_capital)
            
            # Add volatility adjustment to market context
            market_context['volatility_adjustment'] = volatility_adjustment
            
            # Perform strategy rotation
            rotation_result = self.strategy_rotator.rotate_strategies(market_context, force_rotation=True)
            
            # If rotation occurred, execute trades
            if rotation_result["rotated"]:
                new_allocations = rotation_result["new_allocations"]
                
                # Apply risk-based allocation limits if circuit breaker is active
                if self.enable_risk_management and self.risk_manager.circuit_breaker_active:
                    new_allocations = self._apply_circuit_breaker_limits(new_allocations, circuit_breaker_status)
                
                # Execute trades to achieve new allocations
                self._execute_trades(date_str, new_allocations, current_capital, current_positions)
                
                # Recalculate portfolio value after trades
                current_capital = sum(current_positions.values())
                
                # Record the new allocations
                self._record_allocations(current_date, new_allocations)
            else:
                # Record the current allocations (no change)
                current_allocations = {}
                for strategy, position in current_positions.items():
                    current_allocations[strategy] = (position / current_capital) * 100 if current_capital > 0 else 0
                
                self._record_allocations(current_date, current_allocations)
        
        # Record portfolio state for this day
        self.portfolio_history.append({
            'date': current_date,
            'capital': current_capital,
            'positions': current_positions.copy(),
            'daily_return': daily_portfolio_return
        })
        
        if self.debug_mode and abs(daily_portfolio_return) > 0.01:  # Log significant moves
            logger.info(f"Portfolio had a {daily_portfolio_return:.2%} move on {date_str}")
            
    def _apply_emergency_risk_controls(self, current_date, positions, capital):
        """
        Apply emergency risk controls when severe anomalies are detected.
        
        Args:
            current_date: Current date
            positions: Current strategy positions
            capital: Current portfolio capital
        """
        logger.warning(f"Applying emergency risk controls on {current_date.strftime('%Y-%m-%d')}")
        
        # Identify high-risk strategies based on recent performance
        high_risk_strategies = []
        
        # Use recent portfolio history to determine problematic strategies
        lookback = min(10, len(self.portfolio_history) - 1)
        if lookback > 0:
            strategy_returns = {strategy: [] for strategy in self.strategies}
            
            # Collect recent returns by strategy
            for i in range(1, lookback + 1):
                prev_positions = self.portfolio_history[-i].get('positions', {})
                
                for strategy in self.strategies:
                    current_pos = positions.get(strategy, 0)
                    prev_pos = prev_positions.get(strategy, 0)
                    
                    if prev_pos > 0:
                        daily_return = (current_pos / prev_pos) - 1
                        strategy_returns[strategy].append(daily_return)
            
            # Calculate volatility and drawdown for each strategy
            for strategy, returns in strategy_returns.items():
                if len(returns) >= 3:  # Need sufficient data
                    # Calculate volatility
                    volatility = np.std(returns) * np.sqrt(252)  # Annualized
                    
                    # Calculate drawdown
                    cum_returns = np.cumprod(np.array(returns) + 1)
                    peak = np.maximum.accumulate(cum_returns)
                    drawdown = (cum_returns / peak) - 1
                    max_drawdown = np.min(drawdown)
                    
                    # Add to high risk list if exceeds thresholds
                    if volatility > 0.30 or max_drawdown < -0.10:
                        high_risk_strategies.append({
                            'strategy': strategy,
                            'volatility': volatility,
                            'max_drawdown': max_drawdown,
                            'current_allocation': (positions.get(strategy, 0) / capital) * 100 if capital > 0 else 0
                        })
        
        # Apply risk reduction to high-risk strategies
        if high_risk_strategies:
            logger.warning(f"Identified {len(high_risk_strategies)} high-risk strategies for emergency reduction")
            
            # Prepare emergency allocation adjustments
            emergency_allocations = {}
            for strategy in self.strategies:
                current_alloc_pct = (positions.get(strategy, 0) / capital) * 100 if capital > 0 else 0
                
                # Check if this is a high-risk strategy
                is_high_risk = any(s['strategy'] == strategy for s in high_risk_strategies)
                
                if is_high_risk:
                    # Reduce allocation by 50-80% based on severity
                    strategy_info = next(s for s in high_risk_strategies if s['strategy'] == strategy)
                    severity = max(0.5, min(0.8, abs(strategy_info['max_drawdown']) * 4))  # Scale by drawdown
                    new_alloc = current_alloc_pct * (1 - severity)
                    
                    logger.warning(f"Emergency reduction for {strategy}: {current_alloc_pct:.1f}% -> {new_alloc:.1f}%")
                    emergency_allocations[strategy] = new_alloc
                else:
                    # Keep allocation the same
                    emergency_allocations[strategy] = current_alloc_pct
            
            # Add cash allocation for the reduced exposure
            total_alloc = sum(emergency_allocations.values())
            if total_alloc < 100:
                emergency_allocations['cash'] = 100 - total_alloc
            
            # Execute the emergency adjustments
            self._execute_trades(current_date.strftime('%Y-%m-%d'), emergency_allocations, capital, positions)
            
            # Record the emergency allocation change
            self._record_allocations(current_date, emergency_allocations)
            
            # Mark emergency action in debug data
            self.debug_data.append({
                "date": current_date,
                "type": "emergency_risk_control",
                "allocations_before": {s: (positions.get(s, 0) / capital) * 100 if capital > 0 else 0 
                                      for s in self.strategies},
                "allocations_after": emergency_allocations,
                "high_risk_strategies": high_risk_strategies
            })
            
    def _calculate_volatility_adjustment(self, market_context):
        """
        Calculate position sizing adjustment based on market volatility.
        
        Args:
            market_context: Dictionary with market context info
            
        Returns:
            Adjustment factor (1.0 = no adjustment, <1.0 = reduce size, >1.0 = increase size)
        """
        # Get market volatility (normalized 0-1 scale)
        volatility = market_context.get('volatility', 0.5)
        
        # Calculate volatility-based position sizing
        if volatility <= 0.3:  # Low volatility
            # Allow slight increase in position sizing
            adjustment = 1.1
        elif volatility <= 0.5:  # Normal volatility
            # No adjustment
            adjustment = 1.0
        elif volatility <= 0.7:  # Elevated volatility
            # Reduce position sizing by 10-30%
            adjustment = 0.9 - ((volatility - 0.5) * 0.4)
        else:  # High volatility
            # Significant reduction in position sizing (40-70%)
            adjustment = 0.7 - ((volatility - 0.7) * 1.0)
            adjustment = max(0.3, adjustment)  # Floor at 30%
        
        # Consider market regime for additional adjustments
        regime = market_context.get('market_regime', 'neutral')
        
        # Adjust based on market regime
        regime_multipliers = {
            'bullish': 1.05,  # Slightly more aggressive in bullish markets
            'bearish': 0.8,   # More conservative in bearish markets
            'volatile': 0.7,  # Much more conservative in volatile markets
            'sideways': 0.9,  # Somewhat conservative in sideways markets
            'neutral': 1.0    # No adjustment for neutral regime
        }
        
        adjustment *= regime_multipliers.get(regime, 1.0)
        
        return adjustment
        
    def _apply_circuit_breaker_limits(self, allocations, circuit_breaker_status):
        """
        Apply allocation limits based on active circuit breakers.
        
        Args:
            allocations: Dictionary of target allocations
            circuit_breaker_status: Status of circuit breakers
            
        Returns:
            Modified allocations dictionary
        """
        # Make a copy to avoid modifying the original
        modified_allocations = allocations.copy()
        
        # Get circuit breaker level and triggers
        level = circuit_breaker_status.get('level', 1)
        
        # Define maximum allocation changes based on circuit breaker level
        # Level 1: Mild restrictions
        # Level 2: Moderate restrictions
        # Level 3: Severe restrictions
        max_changes = {
            1: 0.15,  # 15% maximum change
            2: 0.10,  # 10% maximum change
            3: 0.05   # 5% maximum change
        }
        
        # Get maximum change based on level
        max_change = max_changes.get(level, 0.15)
        
        # Get current allocations
        current_allocations = {}
        latest_portfolio = self.portfolio_history[-1]
        current_capital = latest_portfolio['capital']
        current_positions = latest_portfolio['positions']
        
        for strategy in self.strategies:
            current_allocations[strategy] = (position / current_capital) * 100 if current_capital > 0 else 0
        
        # Apply limits to each allocation
        for strategy in self.strategies:
            current_alloc = current_allocations.get(strategy, 0)
            target_alloc = modified_allocations.get(strategy, 0)
            
            # Calculate absolute change and limit it
            change = abs(target_alloc - current_alloc)
            
            if change > max_change * 100:  # Convert to percentage points
                # Limit the change
                if target_alloc > current_alloc:
                    modified_allocations[strategy] = current_alloc + (max_change * 100)
                else:
                    modified_allocations[strategy] = current_alloc - (max_change * 100)
                
                logger.info(f"Circuit breaker limited {strategy} allocation change: "
                           f"{current_alloc:.1f}% -> {modified_allocations[strategy]:.1f}% "
                           f"(original target: {target_alloc:.1f}%)")
        
        # Ensure allocations sum to 100%
        total_alloc = sum(modified_allocations.values())
        if abs(total_alloc - 100) > 0.1:  # If more than 0.1% off
            # Scale allocations to sum to 100%
            scaling_factor = 100 / total_alloc if total_alloc > 0 else 1.0
            for strategy in modified_allocations:
                modified_allocations[strategy] *= scaling_factor
        
        return modified_allocations
    
    def _get_stress_test_adjustment(self, stress_results):
        """
        Calculate adjustment factor based on stress test results.
        
        Args:
            stress_results: Dictionary with stress test results
            
        Returns:
            Adjustment factor for position sizing
        """
        # Default adjustment is 1.0 (no change)
        adjustment = 1.0
        
        # Scale adjustment based on risk level
        risk_level = stress_results.get('risk_level', 'medium')
        risk_adjustments = {
            'low': 1.05,     # Slightly more aggressive
            'medium': 1.0,   # No change
            'high': 0.75,    # Reduce positions by 25%
            'extreme': 0.5   # Reduce positions by 50%
        }
        
        adjustment = risk_adjustments.get(risk_level, 1.0)
        
        # Further adjust based on projected drawdown
        projected_drawdown = abs(stress_results.get('projected_max_drawdown', 0))
        if projected_drawdown > 15:
            # Additional reduction for large projected drawdowns
            drawdown_factor = max(0.5, 1.0 - (projected_drawdown - 15) / 100)
            adjustment *= drawdown_factor
        
        # Ensure minimum adjustment factor
        adjustment = max(0.2, adjustment)  # Never go below 20% of original sizing
        
        return adjustment
        
    def simulate_risk_scenario(self, scenario_type='market_crash', duration_days=10, severity=0.8):
        """
        Simulate a risk scenario to test risk management systems.
        
        Args:
            scenario_type: Type of scenario ('market_crash', 'volatility_spike', 'correlation_breakdown')
            duration_days: Duration of the scenario in trading days
            severity: Severity factor from 0.0 to 1.0 (1.0 = maximum severity)
            
        Returns:
            Dictionary with scenario results
        """
        # Ensure we have run a backtest first
        if not hasattr(self, 'portfolio_df') or self.portfolio_df.empty:
            logger.error("Must run a backtest before simulating risk scenarios")
            return {"error": "No backtest data available"}
        
        logger.info(f"Simulating {scenario_type} scenario with {duration_days} days duration "
                   f"and {severity:.1f} severity")
        
        # Create a copy of the original data
        original_strategy_data = self.strategy_data.copy()
        original_market_data = self.market_data.copy()
        
        # Prepare scenario parameters based on type
        if scenario_type == 'market_crash':
            # Market crash: Large, persistent negative returns across most strategies
            scenario_params = {
                'trend_following': {'mean_return': -0.015 * severity, 'volatility': 0.025 * severity},
                'momentum': {'mean_return': -0.02 * severity, 'volatility': 0.03 * severity},
                'mean_reversion': {'mean_return': -0.005 * severity, 'volatility': 0.02 * severity},
                'market_regime': 'bearish',
                'volatility_factor': 2.5 * severity
            }
        elif scenario_type == 'volatility_spike':
            # Volatility spike: Elevated volatility with moderate negative returns
            scenario_params = {
                'trend_following': {'mean_return': -0.005 * severity, 'volatility': 0.04 * severity},
                'momentum': {'mean_return': -0.008 * severity, 'volatility': 0.05 * severity},
                'mean_reversion': {'mean_return': 0.002 * severity, 'volatility': 0.035 * severity},
                'market_regime': 'volatile',
                'volatility_factor': 3.0 * severity
            }
        elif scenario_type == 'correlation_breakdown':
            # Correlation breakdown: All strategies become highly correlated and negative
            scenario_params = {
                'trend_following': {'mean_return': -0.01 * severity, 'volatility': 0.03 * severity},
                'momentum': {'mean_return': -0.012 * severity, 'volatility': 0.03 * severity},
                'mean_reversion': {'mean_return': -0.009 * severity, 'volatility': 0.028 * severity},
                'market_regime': 'bearish',
                'volatility_factor': 2.0 * severity,
                'correlation_factor': 0.9 * severity  # High correlation
            }
        else:
            logger.error(f"Unknown scenario type: {scenario_type}")
            return {"error": f"Unknown scenario type: {scenario_type}"}
        
        # Choose a start date (preferably in middle of backtest)
        if len(self.portfolio_df) > duration_days * 2:
            scenario_start_idx = len(self.portfolio_df) // 2
            scenario_start_date = self.portfolio_df.index[scenario_start_idx]
        else:
            # Just use the first day if not enough data
            scenario_start_date = self.portfolio_df.index[0]
        
        # Modify data for the scenario duration
        try:
            scenario_end_date = scenario_start_date + pd.Timedelta(days=duration_days)
            
            # Modify strategy data
            for strategy in self.strategies:
                # Get date indices within scenario period
                scenario_mask = (self.strategy_data[strategy].index >= scenario_start_date) & \
                               (self.strategy_data[strategy].index <= scenario_end_date)
                scenario_dates = self.strategy_data[strategy].index[scenario_mask]
                
                # Skip if strategy not in parameters
                if strategy not in scenario_params:
                    continue
                
                # Get scenario parameters for this strategy
                params = scenario_params[strategy]
                mean_return = params.get('mean_return', -0.01 * severity)
                volatility = params.get('volatility', 0.02 * severity)
                
                # Generate new returns based on scenario
                new_returns = np.random.normal(mean_return, volatility, size=len(scenario_dates))
                
                # Apply correlation if specified
                if 'correlation_factor' in scenario_params:
                    # Use a common random factor to introduce correlation
                    common_factor = np.random.normal(mean_return * 1.2, volatility * 0.8, size=len(scenario_dates))
                    corr_factor = scenario_params['correlation_factor']
                    new_returns = (corr_factor * common_factor) + ((1 - corr_factor) * new_returns)
                
                # Update strategy returns
                self.strategy_data[strategy].loc[scenario_dates, 'return'] = new_returns
                
                # Update equity curve
                cum_returns = (1 + self.strategy_data[strategy]['return']).cumprod()
                self.strategy_data[strategy]['equity_curve'] = cum_returns
            
            # Modify market data for volatility and regime
            if 'market_data' in self.__dict__ and not self.market_data.empty:
                scenario_mask = (self.market_data.index >= scenario_start_date) & \
                               (self.market_data.index <= scenario_end_date)
                scenario_dates = self.market_data.index[scenario_mask]
                
                # Update VIX to reflect scenario volatility
                if 'vix' in self.market_data.columns:
                    volatility_factor = scenario_params.get('volatility_factor', 2.0)
                    self.market_data.loc[scenario_dates, 'vix'] *= volatility_factor
                
                # Update market regime if applicable
                if hasattr(self, 'regime_data') and not self.regime_data.empty:
                    regime_mask = (self.regime_data.index >= scenario_start_date) & \
                                 (self.regime_data.index <= scenario_end_date)
                    self.regime_data.loc[regime_mask, 'regime'] = scenario_params.get('market_regime', 'volatile')
            
            # Run the backtest with modified data
            results = self.run_backtest()
            
            # Analyze risk management responses during the scenario
            risk_responses = self._analyze_risk_responses(scenario_start_date, scenario_end_date)
            
            # Restore original data
            self.strategy_data = original_strategy_data
            self.market_data = original_market_data
            
            # Compile scenario results
            scenario_results = {
                "scenario_type": scenario_type,
                "start_date": scenario_start_date,
                "end_date": scenario_end_date,
                "severity": severity,
                "duration_days": duration_days,
                "performance": {
                    "scenario_return": results["performance_report"]["summary"]["total_return_pct"],
                    "scenario_max_drawdown": results["performance_report"]["risk_metrics"]["max_drawdown_pct"],
                    "scenario_volatility": results["performance_report"]["risk_metrics"]["volatility_pct"]
                },
                "risk_responses": risk_responses
            }
            
            return scenario_results
            
        except Exception as e:
            logger.error(f"Error simulating risk scenario: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Error simulating risk scenario: {str(e)}"}
        finally:
            # Ensure original data is restored even if exception occurs
            self.strategy_data = original_strategy_data
            self.market_data = original_market_data
            
    def _analyze_risk_responses(self, start_date, end_date):
        """
        Analyze risk management responses during a specific period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with risk response analysis
        """
        # Filter debug data for risk events during the specified period
        risk_events = []
        
        for event in self.debug_data:
            event_date = event.get('date')
            if event_date and start_date <= event_date <= end_date:
                if event.get('type') in ['risk_anomaly', 'circuit_breaker', 'emergency_risk_control']:
                    risk_events.append(event)
        
        # Count different types of risk responses
        response_counts = {
            'anomalies_detected': len([e for e in risk_events if e.get('type') == 'risk_anomaly']),
            'circuit_breakers_triggered': len([e for e in risk_events if e.get('type') == 'circuit_breaker']),
            'emergency_actions': len([e for e in risk_events if e.get('type') == 'emergency_risk_control'])
        }
        
        # Calculate average allocation changes during risk events
        allocation_changes = []
        
        for i in range(1, len(self.allocation_history)):
            alloc_date = self.allocation_history[i].get('date')
            prev_alloc = self.allocation_history[i-1]
            curr_alloc = self.allocation_history[i]
            
            if alloc_date and start_date <= alloc_date <= end_date:
                # Check if this date had a risk event
                had_risk_event = any(e.get('date') == alloc_date for e in risk_events)
                
                # Calculate total allocation change magnitude
                change_magnitude = 0
                for strategy in self.strategies:
                    prev_val = prev_alloc.get(f'{strategy}_allocation', 0)
                    curr_val = curr_alloc.get(f'{strategy}_allocation', 0)
                    change_magnitude += abs(curr_val - prev_val)
                
                if had_risk_event:
                    allocation_changes.append((alloc_date, change_magnitude, True))
                else:
                    allocation_changes.append((alloc_date, change_magnitude, False))
        
        # Calculate average allocation change sizes
        risk_event_changes = [c[1] for c in allocation_changes if c[2]]
        normal_changes = [c[1] for c in allocation_changes if not c[2]]
        
        avg_risk_change = np.mean(risk_event_changes) if risk_event_changes else 0
        avg_normal_change = np.mean(normal_changes) if normal_changes else 0
        
        # Calculate volatility adjustment effectiveness (if applicable)
        volatility_effectiveness = None
        high_vol_periods = []
        
        if hasattr(self, 'market_data') and 'vix' in self.market_data.columns:
            # Define high volatility threshold
            high_vol_threshold = self.market_data['vix'].quantile(0.75)
            
            # Find periods of high volatility
            for i in range(len(self.market_data)):
                date = self.market_data.index[i]
                if start_date <= date <= end_date and self.market_data['vix'].iloc[i] > high_vol_threshold:
                    high_vol_periods.append(date)
            
            # Calculate average position sizing during high vol periods vs. normal periods
            if high_vol_periods:
                high_vol_position_sizing = []
                normal_position_sizing = []
                
                for i, entry in enumerate(self.portfolio_history):
                    entry_date = entry.get('date')
                    if entry_date and start_date <= entry_date <= end_date:
                        # Calculate total position value (sum of absolute position values)
                        total_position = sum(abs(pos) for pos in entry['positions'].values())
                        position_pct = (total_position / entry['capital']) * 100 if entry['capital'] > 0 else 0
                        
                        if entry_date in high_vol_periods:
                            high_vol_position_sizing.append(position_pct)
                        else:
                            normal_position_sizing.append(position_pct)
                
                if high_vol_position_sizing and normal_position_sizing:
                    avg_high_vol_sizing = np.mean(high_vol_position_sizing)
                    avg_normal_sizing = np.mean(normal_position_sizing)
                    
                    # Reduction in position sizing during high vol (should be <1.0)
                    volatility_effectiveness = avg_high_vol_sizing / avg_normal_sizing if avg_normal_sizing > 0 else 1.0
        
        # Calculate performance during risk events vs. normal periods
        risk_event_dates = [e.get('date') for e in risk_events]
        risk_event_returns = []
        normal_returns = []
        
        for i, entry in enumerate(self.portfolio_history):
            entry_date = entry.get('date')
            if entry_date and start_date <= entry_date <= end_date:
                daily_return = entry.get('daily_return', 0)
                
                if entry_date in risk_event_dates:
                    risk_event_returns.append(daily_return)
                else:
                    normal_returns.append(daily_return)
        
        avg_risk_return = np.mean(risk_event_returns) if risk_event_returns else 0
        avg_normal_return = np.mean(normal_returns) if normal_returns else 0
        
        # Compile results
        return {
            "response_counts": response_counts,
            "total_risk_events": len(risk_events),
            "avg_allocation_change": {
                "during_risk_events": avg_risk_change,
                "during_normal_periods": avg_normal_change,
                "change_ratio": avg_risk_change / avg_normal_change if avg_normal_change > 0 else float('inf')
            },
            "volatility_adjustment": {
                "high_vol_days": len(high_vol_periods),
                "position_sizing_ratio": volatility_effectiveness,
                "effective": volatility_effectiveness < 0.9 if volatility_effectiveness is not None else None
            },
            "performance_impact": {
                "avg_return_during_risk_events": avg_risk_return * 100,  # Convert to percentage
                "avg_return_during_normal_periods": avg_normal_return * 100,  # Convert to percentage
                "return_differential": (avg_risk_return - avg_normal_return) * 100  # Convert to percentage
            },
            "risk_events": risk_events
        }
        
    def run_risk_scenarios(self):
        """
        Run a suite of risk scenarios to validate risk management functionality.
        
        Returns:
            Dictionary with scenario results
        """
        logger.info("Running risk scenario test suite")
        
        # Define scenario configurations
        scenarios = [
            {"type": "market_crash", "duration_days": 10, "severity": 0.8},
            {"type": "volatility_spike", "duration_days": 5, "severity": 0.9},
            {"type": "correlation_breakdown", "duration_days": 8, "severity": 0.7}
        ]
        
        # Run each scenario
        scenario_results = {}
        for scenario in scenarios:
            scenario_type = scenario["type"]
            result = self.simulate_risk_scenario(
                scenario_type=scenario_type,
                duration_days=scenario["duration_days"],
                severity=scenario["severity"]
            )
            scenario_results[scenario_type] = result
        
        # Calculate overall risk management effectiveness score
        effectiveness_scores = []
        
        for scenario_type, result in scenario_results.items():
            if "error" in result:
                continue
                
            # Calculate score based on performance preservation
            # A perfect score would be 0 (no loss) during a severe scenario
            # Normalize based on scenario severity
            severity = result["severity"]
            scenario_return = result["performance"]["scenario_return"]
            
            # Expected loss for a passive strategy with no risk management
            # More severe scenarios would have larger expected losses
            expected_loss = -20 * severity
            
            # Calculate how much better than expected the strategy performed
            # Score from 0 to 100, higher is better
            performance_score = min(100, max(0, 100 * (1 + (scenario_return - expected_loss) / expected_loss)))
            
            # Calculate responsiveness score based on risk events
            response_counts = result["risk_responses"]["response_counts"]
            total_events = sum(response_counts.values())
            expected_events = result["duration_days"] * severity
            responsiveness_score = min(100, max(0, 100 * (total_events / expected_events)))
            
            # Calculate position sizing effectiveness
            position_sizing_ratio = result["risk_responses"]["volatility_adjustment"]["position_sizing_ratio"]
            if position_sizing_ratio is not None:
                # Lower ratio is better (reduced position sizing during high vol)
                # Ideal ratio would be around 0.5-0.7 for high severity
                target_ratio = 1.0 - (0.5 * severity)
                position_sizing_score = min(100, max(0, 100 * (1 - abs(position_sizing_ratio - target_ratio))))
            else:
                position_sizing_score = 50  # Neutral if we couldn't calculate
            
            # Composite effectiveness score
            scenario_score = 0.5 * performance_score + 0.3 * responsiveness_score + 0.2 * position_sizing_score
            
            # Add to overall scores
            effectiveness_scores.append(scenario_score)
            
            # Add score to scenario results
            scenario_results[scenario_type]["effectiveness_score"] = scenario_score
        
        # Calculate overall effectiveness
        overall_effectiveness = np.mean(effectiveness_scores) if effectiveness_scores else 0
        
        # Final results
        return {
            "scenario_results": scenario_results,
            "overall_effectiveness": overall_effectiveness,
            "effectiveness_grade": self._get_effectiveness_grade(overall_effectiveness),
            "recommendations": self._generate_risk_recommendations(scenario_results)
        }
        
    def _get_effectiveness_grade(self, score):
        """Convert effectiveness score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 45:
            return "D+"
        elif score >= 40:
            return "D"
        elif score >= 35:
            return "D-"
        else:
            return "F"
        
    def _generate_risk_recommendations(self, scenario_results):
        """Generate recommendations based on scenario test results"""
        recommendations = []
        
        # Analyze market crash scenario
        if "market_crash" in scenario_results and "error" not in scenario_results["market_crash"]:
            crash_result = scenario_results["market_crash"]
            
            # Check drawdown vs severity
            crash_drawdown = abs(crash_result["performance"]["scenario_max_drawdown"])
            crash_severity = crash_result["severity"]
            expected_drawdown = 25 * crash_severity  # Expected drawdown based on severity
            
            if crash_drawdown > expected_drawdown:
                recommendations.append(
                    "Improve market crash protection: The drawdown during the market crash scenario "
                    f"was {crash_drawdown:.1f}%, higher than expected for the severity level. "
                    "Consider adding more aggressive circuit breakers or hedging strategies."
                )
            
            # Check position sizing effectiveness
            position_sizing = crash_result["risk_responses"]["volatility_adjustment"]["position_sizing_ratio"]
            if position_sizing and position_sizing > 0.8:
                recommendations.append(
                    "Enhance volatility-based position sizing: During the market crash, position sizing "
                    f"was only reduced to {position_sizing:.1f}x normal levels. "
                    "Consider more aggressive position size reductions during high volatility periods."
                )
        
        # Analyze correlation breakdown scenario
        if "correlation_breakdown" in scenario_results and "error" not in scenario_results["correlation_breakdown"]:
            corr_result = scenario_results["correlation_breakdown"]
            
            # Check if emergency actions were taken
            emergency_actions = corr_result["risk_responses"]["response_counts"]["emergency_actions"]
            
            if emergency_actions == 0:
                recommendations.append(
                    "Improve correlation breakdown detection: No emergency actions were triggered during "
                    "the correlation breakdown scenario. Consider implementing correlation monitoring "
                    "and add emergency responses when diversification benefits suddenly diminish."
                )
        
        # Analyze volatility spike scenario
        if "volatility_spike" in scenario_results and "error" not in scenario_results["volatility_spike"]:
            vol_result = scenario_results["volatility_spike"]
            
            # Check circuit breaker triggering
            circuit_breakers = vol_result["risk_responses"]["response_counts"]["circuit_breakers_triggered"]
            
            if circuit_breakers == 0:
                recommendations.append(
                    "Enhance volatility-based circuit breakers: No circuit breakers were triggered during "
                    "the volatility spike scenario. Consider adding circuit breakers that activate based "
                    "on sudden increases in realized or implied volatility."
                )
        
        # If no specific recommendations, give general advice
        if not recommendations:
            # Check overall effectiveness score
            scores = [s.get("effectiveness_score", 0) for s in scenario_results.values() 
                      if "error" not in s and "effectiveness_score" in s]
            avg_score = np.mean(scores) if scores else 0
            
            if avg_score >= 80:
                recommendations.append(
                    "The risk management system appears to be functioning well across all tested scenarios. "
                    "Consider testing with more extreme scenarios or adding more sophisticated risk controls "
                    "for further refinement."
                )
            elif avg_score >= 60:
                recommendations.append(
                    "The risk management system is adequate but has room for improvement. Consider adding "
                    "more responsive volatility controls and enhancing correlation monitoring."
                )
            else:
                recommendations.append(
                    "The risk management system needs significant improvement. Focus on implementing basic "
                    "circuit breakers, volatility-based position sizing, and emergency risk controls."
                )

    def run_backtest(self):
        """
        Run the backtesting simulation.
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest from {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        # Load required data
        self.load_strategy_data()
        self.load_market_data()
        self.load_regime_data()
        self.load_benchmark_data()
        
        # Reset performance tracking
        self.portfolio_history = []
        self.allocation_history = []
        self.trades = []
        self.total_costs = 0.0
        
        # Initialize portfolio with initial allocations
        initial_positions = {}
        for strategy, allocation in self.initial_allocations.items():
            position_value = (allocation / 100.0) * self.initial_capital
            initial_positions[strategy] = position_value
        
        # Initialize portfolio history
        self.portfolio_history.append({
            'date': self.start_date,
            'capital': self.initial_capital,
            'positions': initial_positions.copy(),
            'daily_return': 0.0
        })
        
        # Record initial allocations
        self._record_allocations(self.start_date, self.initial_allocations)
        
        # Generate simulation dates (business days only)
        simulation_dates = pd.date_range(
            start=self.start_date + timedelta(days=1),  # Start day after initialization
            end=self.end_date,
            freq='B'  # Business days
        )
        
        if self.debug_mode:
            logger.info(f"Running backtest with {len(simulation_dates)} trading days")
            logger.info(f"Initial portfolio: {initial_positions}")
        
        # Run simulation for each day
        for current_date in simulation_dates:
            if self.debug_mode and (current_date.day == 1 or current_date == simulation_dates[-1]):
                logger.info(f"Simulating {current_date.strftime('%Y-%m-%d')}")
            
            try:
                self.step(current_date)
            except Exception as e:
                logger.error(f"Error in simulation step for {current_date}: {str(e)}")
                if self.debug_mode:
                    import traceback
                    logger.error(traceback.format_exc())
        
        # Process results
        self._process_backtest_results()
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics()
        
        # Generate performance report
        performance_report = self.generate_performance_report(metrics)
        
        # Add trade info to results
        metrics['trade_count'] = len(self.trades)
        metrics['total_costs'] = self.total_costs
        metrics['trades'] = self.trades
        metrics['performance_report'] = performance_report
        
        # Log summary
        logger.info(f"Backtest completed. Final capital: ${metrics['final_capital']:,.2f}")
        logger.info(f"Total return: {metrics['total_return_pct']:.2f}%")
        logger.info(f"Number of trades: {len(self.trades)}")
        logger.info(f"Trading costs: ${self.total_costs:.2f}")
        
        return metrics

    def plot_allocation_history(self, save_path: Optional[str] = None):
        """
        Plot strategy allocations over time.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have allocation history
        if not hasattr(self, 'allocation_history') or len(self.allocation_history) == 0:
            logger.warning("No allocation history available")
            return None, None
        
        # Convert allocation history to DataFrame if needed
        if isinstance(self.allocation_history, list):
            allocation_df = pd.DataFrame(self.allocation_history)
            allocation_df.set_index('date', inplace=True)
        else:
            allocation_df = self.allocation_history
        
        # Plot strategy allocations
        fig, ax = plot_strategy_allocations(
            allocations=allocation_df,
            title="Strategy Allocations Over Time",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_regime_performance(self, save_path: Optional[str] = None):
        """
        Plot performance by market regime.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have regime data
        if not hasattr(self, 'regime_history') or len(self.regime_history) == 0:
            logger.warning("No market regime data available")
            return None, None
        
        # Convert regime history to DataFrame if needed
        if isinstance(self.regime_history, list):
            regime_df = pd.DataFrame(self.regime_history)
            regime_df.set_index('date', inplace=True)
        else:
            regime_df = self.regime_history
        
        # Make sure we have portfolio data
        if not hasattr(self, 'portfolio_df'):
            self._calculate_performance_metrics()
        
        # Get daily returns Series
        returns = pd.Series(
            data=self.portfolio_df['daily_return'].values,
            index=self.portfolio_df.index,
            name='Returns'
        )
        
        # Map regime data to returns
        regime_returns = {}
        regime_column = 'regime' if 'regime' in regime_df.columns else next(iter(regime_df.columns))
        
        # Get all unique regimes
        all_regimes = regime_df[regime_column].unique()
        
        # Calculate returns by regime
        for regime in all_regimes:
            # Get dates for this regime
            regime_dates = regime_df[regime_df[regime_column] == regime].index
            
            # Get returns for these dates
            regime_return_series = returns.loc[returns.index.isin(regime_dates)]
            
            if not regime_return_series.empty:
                regime_returns[f"Regime {regime}"] = regime_return_series
        
        # Plot regime analysis
        fig, ax = plot_regime_analysis(
            regime_returns=regime_returns,
            title="Performance by Market Regime",
            figsize=(12, 10),
            save_path=save_path
        )
        
        return fig, ax

    def create_performance_dashboard(self, save_path: Optional[str] = None):
        """
        Create a comprehensive performance dashboard with multiple plots.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure
        """
        # Calculate metrics if not done already
        if not hasattr(self, 'portfolio_df') or not hasattr(self, 'performance_metrics'):
            self._calculate_performance_metrics()
            self.calculate_advanced_metrics()
        
        # Create dashboard
        fig = create_performance_dashboard(
            equity_curve=pd.Series(
                data=self.portfolio_df['capital'].values,
                index=self.portfolio_df.index,
                name='Portfolio'
            ),
            returns=pd.Series(
                data=self.portfolio_df['daily_return'].values,
                index=self.portfolio_df.index,
                name='Returns'
            ),
            drawdowns=self.calculate_drawdowns()['drawdown'],
            metrics=self.performance_metrics,
            advanced_metrics=self.advanced_metrics if hasattr(self, 'advanced_metrics') else None,
            trade_history=self.trade_history if hasattr(self, 'trade_history') else None,
            title=f"Trading Performance Dashboard: {self.strategy_name}",
            figsize=(16, 12),
            save_path=save_path
        )
        
        return fig

    def save_performance_report(self, output_dir: str = None):
        """
        Generate and save a complete performance report with visualizations.
        
        Args:
            output_dir: Directory to save the report (default: results/reports/<strategy_name>)
            
        Returns:
            Dictionary with paths to saved files
        """
        # Set default output directory if not provided
        if output_dir is None:
            strategy_name_safe = re.sub(r'[^\w\-_]', '_', self.strategy_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/reports/{strategy_name_safe}_{timestamp}"
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Dictionary to store saved file paths
        saved_files = {}
        
        # Calculate metrics if needed
        if not hasattr(self, 'performance_metrics'):
            self._calculate_performance_metrics()
            self.calculate_advanced_metrics()
        
        # Generate performance report
        report_path = self.generate_performance_report(os.path.join(output_dir, "performance_report.html"))
        saved_files['performance_report'] = report_path
        
        # Save portfolio performance plot
        fig, _ = self.plot_portfolio_performance(save_path=os.path.join(output_dir, "portfolio_performance.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['portfolio_performance'] = os.path.join(output_dir, "portfolio_performance.png")
        
        # Save drawdowns plot
        fig, _ = self.plot_drawdowns(save_path=os.path.join(output_dir, "drawdowns.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['drawdowns'] = os.path.join(output_dir, "drawdowns.png")
        
        # Save monthly returns plot
        fig, _ = self.plot_monthly_returns(save_path=os.path.join(output_dir, "monthly_returns.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['monthly_returns'] = os.path.join(output_dir, "monthly_returns.png")
        
        # Save rolling metrics plot
        fig, _ = self.plot_rolling_risk_metrics(save_path=os.path.join(output_dir, "rolling_metrics.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['rolling_metrics'] = os.path.join(output_dir, "rolling_metrics.png")
        
        # Save returns distribution plot
        fig, _ = self.plot_returns_distribution(save_path=os.path.join(output_dir, "returns_distribution.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['returns_distribution'] = os.path.join(output_dir, "returns_distribution.png")
        
        # Save strategy correlations plot if applicable
        if hasattr(self, 'strategy_returns'):
            fig, _ = self.plot_strategy_correlations(save_path=os.path.join(output_dir, "strategy_correlations.png"))
            if fig is not None:
                plt.close(fig)
                saved_files['strategy_correlations'] = os.path.join(output_dir, "strategy_correlations.png")
        
        # Save allocation history plot if applicable
        if hasattr(self, 'allocation_history') and len(self.allocation_history) > 0:
            fig, _ = self.plot_allocation_history(save_path=os.path.join(output_dir, "allocation_history.png"))
            if fig is not None:
                plt.close(fig)
                saved_files['allocation_history'] = os.path.join(output_dir, "allocation_history.png")
        
        # Save regime performance plot if applicable
        if hasattr(self, 'regime_history') and len(self.regime_history) > 0:
            fig, _ = self.plot_regime_performance(save_path=os.path.join(output_dir, "regime_performance.png"))
            if fig is not None:
                plt.close(fig)
                saved_files['regime_performance'] = os.path.join(output_dir, "regime_performance.png")
        
        # Save performance dashboard
        fig = self.create_performance_dashboard(save_path=os.path.join(output_dir, "performance_dashboard.png"))
        if fig is not None:
            plt.close(fig)
            saved_files['performance_dashboard'] = os.path.join(output_dir, "performance_dashboard.png")
        
        # Save metrics as JSON
        metrics_combined = {
            **self.performance_metrics,
            **(self.advanced_metrics if hasattr(self, 'advanced_metrics') else {})
        }
        
        with open(os.path.join(output_dir, "metrics.json"), 'w') as f:
            json.dump(metrics_combined, f, indent=4, default=str)
        
        saved_files['metrics_json'] = os.path.join(output_dir, "metrics.json")
        
        # Log success message
        logger.info(f"Performance report saved to {output_dir}")
        
        return saved_files

    def plot_portfolio_performance(self, benchmark: bool = True, save_path: Optional[str] = None):
        """
        Plot the portfolio equity curve with optional benchmark comparison.
        
        Args:
            benchmark: Whether to include benchmark in the plot
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have portfolio history
        if not hasattr(self, 'portfolio_history') or len(self.portfolio_history) == 0:
            logger.warning("No portfolio history available")
            return None, None
        
        # Convert portfolio history to DataFrame if not done already
        if not hasattr(self, 'portfolio_df'):
            self._calculate_performance_metrics()
        
        # Create equity curve Series
        equity_curve = pd.Series(
            data=self.portfolio_df['capital'].values,
            index=self.portfolio_df.index,
            name='Portfolio'
        )
        
        # Get benchmark data if requested and available
        benchmark_series = None
        if benchmark and not self.benchmark_data.empty:
            # Normalize benchmark to match portfolio initial value
            benchmark_values = self.benchmark_data['close'].values
            initial_ratio = equity_curve.iloc[0] / benchmark_values[0] if len(benchmark_values) > 0 else 1
            normalized_benchmark = benchmark_values * initial_ratio
            
            benchmark_series = pd.Series(
                data=normalized_benchmark,
                index=self.benchmark_data.index,
                name=self.benchmark_symbol
            )
        
        # Plot equity curve
        fig, ax = plot_equity_curve(
            equity_curve=equity_curve,
            benchmark=benchmark_series,
            drawdowns=self.calculate_drawdowns()['drawdown'],
            title="Portfolio Performance",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_drawdowns(self, top_n: int = 5, save_path: Optional[str] = None):
        """
        Plot portfolio drawdowns over time.
        
        Args:
            top_n: Number of largest drawdowns to highlight
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Calculate drawdowns if not done already
        drawdown_info = self.calculate_drawdowns()
        
        # Plot drawdown curve
        fig, ax = plot_drawdowns(
            drawdowns=drawdown_info['drawdown'],
            equity_curve=pd.Series(
                data=self.portfolio_df['capital'].values,
                index=self.portfolio_df.index
            ),
            drawdown_table=drawdown_info['drawdown_periods'].head(top_n),
            title="Portfolio Drawdowns",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_rolling_risk_metrics(self, window: int = 63, save_path: Optional[str] = None):
        """
        Plot rolling risk-adjusted metrics over time.
        
        Args:
            window: Rolling window size in days
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have portfolio history
        if not hasattr(self, 'portfolio_df'):
            self._calculate_performance_metrics()
        
        # Get daily returns
        returns = pd.Series(
            data=self.portfolio_df['daily_return'].values,
            index=self.portfolio_df.index,
            name='Returns'
        )
        
        # Calculate rolling metrics
        rolling_sharpe = (returns.rolling(window=window).mean() * 252) / (returns.rolling(window=window).std() * np.sqrt(252))
        
        # Calculate rolling Sortino
        negative_returns = returns.copy()
        negative_returns[negative_returns > 0] = 0
        rolling_sortino = (returns.rolling(window=window).mean() * 252) / (negative_returns.rolling(window=window).std() * np.sqrt(252) + 1e-10)
        
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100  # annualized percentage
        
        # Plot rolling metrics
        fig, ax = plot_rolling_metrics(
            metrics={
                'Sharpe Ratio': rolling_sharpe,
                'Sortino Ratio': rolling_sortino,
                'Volatility (%)': rolling_vol
            },
            title=f"Rolling {window}-Day Risk Metrics",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_monthly_returns(self, save_path: Optional[str] = None):
        """
        Plot a heatmap of monthly returns.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have portfolio history
        if not hasattr(self, 'portfolio_df'):
            self._calculate_performance_metrics()
        
        # Get daily returns
        returns = pd.Series(
            data=self.portfolio_df['daily_return'].values,
            index=self.portfolio_df.index,
            name='Returns'
        )
        
        # Calculate monthly returns
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Create monthly returns table
        monthly_table = monthly_returns.to_frame().pivot_table(
            values='Returns',
            index=monthly_returns.index.month,
            columns=monthly_returns.index.year,
            aggfunc='sum'
        )
        
        # Convert month numbers to names
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        monthly_table.index = [month_names[m] for m in monthly_table.index]
        
        # Plot monthly returns heatmap
        fig, ax = plot_monthly_returns(
            monthly_returns=monthly_table,
            title="Monthly Returns (%)",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_strategy_correlations(self, save_path: Optional[str] = None):
        """
        Plot a correlation matrix of strategy returns.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Get strategy correlations
        corr_matrix = self.analyze_strategy_correlations()
        
        if corr_matrix is None or corr_matrix.empty:
            logger.warning("No strategy correlation data available")
            return None, None
        
        # Plot correlation matrix
        fig, ax = plot_correlation_matrix(
            correlation_matrix=corr_matrix,
            title="Strategy Return Correlations",
            figsize=(10, 8),
            save_path=save_path
        )
        
        return fig, ax

    def plot_returns_distribution(self, save_path: Optional[str] = None):
        """
        Plot the distribution of returns with overlays for VaR and normal distribution.
        
        Args:
            save_path: Optional path to save the figure
            
        Returns:
            Matplotlib figure and axes
        """
        # Check if we have portfolio history
        if not hasattr(self, 'portfolio_df'):
            self._calculate_performance_metrics()
        
        # Get daily returns
        returns = pd.Series(
            data=self.portfolio_df['daily_return'].values,
            index=self.portfolio_df.index,
            name='Returns'
        )
        
        # Calculate VaR and CVaR (95%)
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Plot returns distribution
        fig, ax = plot_returns_distribution(
            returns=returns,
            var_threshold=var_95,
            cvar_value=cvar_95,
            confidence_level=95,
            title="Daily Returns Distribution",
            figsize=(12, 8),
            save_path=save_path
        )
        
        return fig, ax

# Example usage
if __name__ == "__main__":
    # Initialize backtester
    backtester = UnifiedBacktester(
        initial_capital=100000.0,
        start_date="2022-01-01",
        end_date="2022-12-31",
        rebalance_frequency="monthly",
        use_mock=True  # Use mock data for example
    )
    
    # Run backtest
    results = backtester.run_backtest()
    
    # Display results
    print("\nBacktest Performance Summary:")
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Annualized Return: {results['annual_return_pct']:.2f}%")
    print(f"Volatility: {results['volatility_pct']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"Win Rate: {results['win_rate_pct']:.2f}%")
    
    # Plot results
    backtester.plot_portfolio_performance()
    backtester.plot_strategy_allocations()
    
    # Save results
    backtester.save_results() 