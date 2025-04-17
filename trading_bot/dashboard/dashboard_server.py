import os
import json
import logging
import datetime
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import threading
import traceback

# Add the parent directory to sys.path to support imports
import sys
from pathlib import Path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import our data provider and portfolio state manager
from trading_bot.data.market_data_provider import create_data_provider
from trading_bot.portfolio_state import PortfolioStateManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'trading_dashboard_secret!'  # Change this in production
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global variables for the background thread
thread = None
DASHBOARD_THREAD_RUNNING = False
UPDATE_INTERVAL = 5  # Number of seconds between updates

# Configuration paths
CONFIG_DIR = os.path.join(current_dir.parent, "config")
DATA_PROVIDER_CONFIG = os.path.join(CONFIG_DIR, "data_providers.json")
PORTFOLIO_STATE_FILE = os.path.join(CONFIG_DIR, "portfolio_state.json")

# Initialize data provider and portfolio state manager
try:
    # Try to initialize with real data
    data_provider = create_data_provider("alpaca", DATA_PROVIDER_CONFIG)
    portfolio_state = PortfolioStateManager(initial_cash=100000.0, state_file=PORTFOLIO_STATE_FILE)
    
    # Flag to track if we're using real data
    USING_REAL_DATA = True
    logger.info("Successfully initialized real data provider and portfolio state manager")
except Exception as e:
    logger.error(f"Error initializing real data components: {e}")
    logger.warning("Falling back to mock data for dashboard")
    USING_REAL_DATA = False
    
    # Initialize with mock data (TradingDataSimulator as fallback)
    class TradingDataSimulator:
        def __init__(self):
            # Initial account value
            self.initial_value = 100000.0
            self.current_value = self.initial_value
            
            # Initialize with some dummy data
            self.symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'SPY', 'QQQ', 'GLD', 'TLT']
            self.strategies = ['MacroTrend', 'MeanReversion', 'Momentum', 'RegimeAware', 'VolBreakout']
            self.current_prices = {
                'AAPL': 185.92, 'MSFT': 417.88, 'GOOGL': 175.53, 'AMZN': 178.75,
                'META': 474.99, 'TSLA': 175.68, 'SPY': 520.94, 'QQQ': 445.94,
                'GLD': 233.96, 'TLT': 95.29
            }
            
            # Generate some history for performance chart
            self.history = self._generate_history(365)  # 1 year of daily data
            
            # Mock strategy weights
            self.strategy_weights = {
                'MacroTrend': 0.30,
                'MeanReversion': 0.15,
                'Momentum': 0.25,
                'RegimeAware': 0.20,
                'VolBreakout': 0.10
            }
            
            # Mock positions
            self.positions = [
                {'symbol': 'AAPL', 'position': 50, 'entry': 179.65, 'current': 185.92},
                {'symbol': 'MSFT', 'position': 20, 'entry': 405.30, 'current': 417.88},
                {'symbol': 'SPY', 'position': -10, 'entry': 523.10, 'current': 520.94},
                {'symbol': 'GLD', 'position': 30, 'entry': 228.42, 'current': 233.96}
            ]
            
            # Mock signals
            self.signals = [
                {'symbol': 'AAPL', 'signal': 'BUY', 'strength': 0.85, 'timeframe': '1D', 'price': 185.92},
                {'symbol': 'TSLA', 'signal': 'SELL', 'strength': 0.72, 'timeframe': '4H', 'price': 175.68},
                {'symbol': 'GLD', 'signal': 'BUY', 'strength': 0.65, 'timeframe': '1W', 'price': 233.96},
                {'symbol': 'TLT', 'signal': 'SELL', 'strength': 0.58, 'timeframe': '1D', 'price': 95.29}
            ]
            
            # Mock strategy performance
            self.strategy_performance = [
                {'name': 'MacroTrend', 'weight': 0.30, 'return': 0.085, 'sharpe': 1.35, 'drawdown': 8.2, 'winRate': 0.62},
                {'name': 'MeanReversion', 'weight': 0.15, 'return': 0.042, 'sharpe': 0.98, 'drawdown': 5.1, 'winRate': 0.58},
                {'name': 'Momentum', 'weight': 0.25, 'return': 0.112, 'sharpe': 1.52, 'drawdown': 12.5, 'winRate': 0.55},
                {'name': 'RegimeAware', 'weight': 0.20, 'return': 0.075, 'sharpe': 1.21, 'drawdown': 7.8, 'winRate': 0.61},
                {'name': 'VolBreakout', 'weight': 0.10, 'return': -0.015, 'sharpe': -0.32, 'drawdown': 15.3, 'winRate': 0.48}
            ]
            
            # Mock correlation matrix
            self.correlation_matrix = self._generate_correlation_matrix()
            
            # Mock risk alerts
            self.risk_alerts = [
                {
                    'title': 'High Volatility',
                    'message': 'Market volatility is 35% above the 20-day average',
                    'severity': 'Medium',
                    'timestamp': datetime.datetime.now().isoformat()
                },
                {
                    'title': 'Correlation Warning',
                    'message': 'Strategy correlations have increased above 0.75',
                    'severity': 'Low',
                    'timestamp': (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
                }
            ]
            
            # Current market regime
            self.current_regime = 'HIGH_VOLATILITY'
        
        def _generate_history(self, days):
            """Generate mock price history for portfolio and benchmark"""
            np.random.seed(42)  # For reproducibility
            
            dates = pd.date_range(end=pd.Timestamp.now().date(), periods=days).tolist()
            
            # Portfolio performance with some randomness and trend
            portfolio_random_walk = np.random.normal(0, 0.01, days).cumsum()
            portfolio_trend = np.linspace(0, 0.15, days)  # Upward trend
            portfolio_values = self.initial_value * (1 + portfolio_random_walk + portfolio_trend)
            
            # Benchmark performance (less volatile)
            benchmark_random_walk = np.random.normal(0, 0.008, days).cumsum()
            benchmark_trend = np.linspace(0, 0.08, days)  # Slower upward trend
            benchmark_values = self.initial_value * (1 + benchmark_random_walk + benchmark_trend)
            
            # Convert to the format expected by Chart.js
            portfolio_data = [{'x': date.isoformat(), 'y': value} for date, value in zip(dates, portfolio_values)]
            benchmark_data = [{'x': date.isoformat(), 'y': value} for date, value in zip(dates, benchmark_values)]
            
            return {
                'portfolio': portfolio_data,
                'benchmark': benchmark_data
            }
        
        def _generate_correlation_matrix(self):
            """Generate mock correlation matrix for strategies"""
            np.random.seed(42)  # For reproducibility
            
            # Create a base correlation matrix (symmetric)
            n = len(self.strategies)
            base_matrix = np.random.uniform(-0.5, 0.5, (n, n))
            # Make it symmetric
            base_matrix = (base_matrix + base_matrix.T) / 2
            # Set diagonal to 1 (perfect self-correlation)
            np.fill_diagonal(base_matrix, 1)
            
            return {
                'matrix': base_matrix.tolist(),
                'labels': self.strategies
            }
        
        def get_performance_data(self, period='7d'):
            """Get performance data for the specified period"""
            # Map period to time span
            time_map = {
                # Minutes
                '1m': {'unit': 'minutes', 'value': 1},
                '5m': {'unit': 'minutes', 'value': 5},
                '15m': {'unit': 'minutes', 'value': 15},
                '30m': {'unit': 'minutes', 'value': 30},
                # Hours
                '1h': {'unit': 'hours', 'value': 1},
                '8h': {'unit': 'hours', 'value': 8},
                # Days
                '1d': {'unit': 'days', 'value': 1},
                '7d': {'unit': 'days', 'value': 7},
                # Months
                '1mo': {'unit': 'days', 'value': 30},
                '3mo': {'unit': 'days', 'value': 90},
                '6mo': {'unit': 'days', 'value': 180},
                '1y': {'unit': 'days', 'value': 365},
                'all': {'unit': 'all', 'value': len(self.history['portfolio'])}
            }
            
            # Default to 7 days if period not recognized
            time_span = time_map.get(period, {'unit': 'days', 'value': 7})
            
            # For 'all' we use the entire history
            if time_span['unit'] == 'all':
                days = time_span['value']
            # For minutes and hours, we need to simulate higher resolution data
            elif time_span['unit'] in ['minutes', 'hours']:
                # Generate more granular data for shorter timeframes
                if 'portfolio_minute' not in self.history:
                    # Create minute-by-minute data for the most recent day
                    minutes_in_day = 24 * 60
                    # Start with the last value from the daily data
                    start_value = self.history['portfolio'][-1]['y']
                    minute_data = []
                    
                    # Generate random minute data going back a day
                    now = pd.Timestamp.now()
                    for i in range(minutes_in_day):
                        timestamp = now - pd.Timedelta(minutes=minutes_in_day-i)
                        # Generate smaller random movements for minute data
                        change = np.random.normal(0, 0.0001)
                        start_value *= (1 + change)
                        minute_data.append({
                            'x': timestamp.isoformat(),
                            'y': start_value
                        })
                    self.history['portfolio_minute'] = minute_data
                    
                    # Also generate benchmark data at minute resolution
                    benchmark_minute = []
                    start_value = self.history['benchmark'][-1]['y']
                    for i in range(minutes_in_day):
                        timestamp = now - pd.Timedelta(minutes=minutes_in_day-i)
                        # Slightly different movement for benchmark
                        change = np.random.normal(0, 0.00008)
                        start_value *= (1 + change)
                        benchmark_minute.append({
                            'x': timestamp.isoformat(),
                            'y': start_value
                        })
                    self.history['benchmark_minute'] = benchmark_minute
                
                # Determine number of data points based on period
                if time_span['unit'] == 'minutes':
                    days = time_span['value'] / (24 * 60)  # Convert minutes to days
                    minutes = time_span['value']
                    # Get slice of minute data
                    portfolio_data = self.history['portfolio_minute'][-minutes:]
                    benchmark_data = self.history['benchmark_minute'][-minutes:]
                else:  # hours
                    days = time_span['value'] / 24  # Convert hours to days
                    minutes = time_span['value'] * 60
                    # Get slice of minute data
                    portfolio_data = self.history['portfolio_minute'][-minutes:]
                    benchmark_data = self.history['benchmark_minute'][-minutes:]
            else:
                # For days, we use the regular daily data
                days = time_span['value']
                # Get data for the specified period (limit to available data)
                portfolio_data = self.history['portfolio'][-min(days, len(self.history['portfolio'])):]
                benchmark_data = self.history['benchmark'][-min(days, len(self.history['benchmark'])):]
            
            # Calculate metrics based on the data we're displaying
            if len(portfolio_data) > 1:
                # Calculate metrics
                start_value = portfolio_data[0]['y']
                end_value = portfolio_data[-1]['y']
                pnl = end_value - start_value
                
                # Calculate daily change (or appropriate change for timeframe)
                today_value = portfolio_data[-1]['y']
                yesterday_value = portfolio_data[-2]['y'] if len(portfolio_data) > 1 else today_value
                daily_change = ((today_value / yesterday_value) - 1) * 100
                
                # Extract y values for calculations
                portfolio_values = [p['y'] for p in portfolio_data]
                benchmark_values = [b['y'] for b in benchmark_data]
                
                # Calculate returns
                portfolio_returns = np.diff(portfolio_values) / portfolio_values[:-1]
                if len(benchmark_values) > 1:
                    benchmark_returns = np.diff(benchmark_values) / benchmark_values[:-1]
                    # Calculate Sharpe ratio (simplified)
                    portfolio_sharpe = np.mean(portfolio_returns) / np.std(portfolio_returns) if np.std(portfolio_returns) > 0 else 0
                    benchmark_sharpe = np.mean(benchmark_returns) / np.std(benchmark_returns) if np.std(benchmark_returns) > 0 else 0
                    sharpe_diff = portfolio_sharpe - benchmark_sharpe
                else:
                    portfolio_sharpe = 0
                    sharpe_diff = 0
                
                # Calculate drawdown
                rolling_max = np.maximum.accumulate(portfolio_values)
                drawdowns = (rolling_max - portfolio_values) / rolling_max * 100
                max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
                
                # Calculate average drawdown for comparison
                avg_drawdown = np.mean(drawdowns) if len(drawdowns) > 0 else 0
                drawdown_change = max_drawdown - avg_drawdown
                
                # Calculate volatility (adjusted for timeframe)
                if time_span['unit'] == 'minutes':
                    annualization_factor = np.sqrt(252 * 6.5 * 60)  # ~252 trading days, 6.5 hours, 60 minutes
                elif time_span['unit'] == 'hours':
                    annualization_factor = np.sqrt(252 * 6.5)  # ~252 trading days, 6.5 hours
                else:
                    annualization_factor = np.sqrt(252)  # ~252 trading days
                    
                volatility = np.std(portfolio_returns) * 100 * annualization_factor
                avg_volatility = volatility * 0.9  # Mock average volatility (slightly lower)
                volatility_change = volatility - avg_volatility
            else:
                # Default values if not enough data
                pnl = 0
                daily_change = 0
                portfolio_sharpe = 0
                sharpe_diff = 0
                max_drawdown = 0
                drawdown_change = 0
                volatility = 0
                volatility_change = 0
            
            # Format metrics for front-end
            metrics = {
                'pnl': {
                    'value': pnl,
                    'change': daily_change
                },
                'sharpe': {
                    'value': portfolio_sharpe * np.sqrt(252),  # Annualized
                    'change': sharpe_diff * np.sqrt(252)  # Annualized
                },
                'drawdown': {
                    'value': max_drawdown,
                    'change': drawdown_change
                },
                'volatility': {
                    'value': volatility,
                    'change': volatility_change
                }
            }
            
            return {
                'performance': {
                    'portfolio': portfolio_data,
                    'benchmark': benchmark_data
                },
                'metrics': metrics
            }
        
        def get_weights_data(self):
            """Get strategy weights data"""
            return self.strategy_weights
        
        def get_signals_data(self):
            """Get latest trading signals"""
            return self.signals
        
        def get_positions_data(self):
            """Get current positions"""
            # Update current prices in positions
            for position in self.positions:
                position['current'] = self.current_prices.get(position['symbol'], position['current'])
            
            return self.positions
        
        def get_strategy_performance_data(self):
            """Get strategy performance metrics"""
            return self.strategy_performance
        
        def get_correlation_data(self):
            """Get correlation matrix data"""
            return self.correlation_matrix
        
        def get_risk_alerts_data(self):
            """Get risk alerts data"""
            return self.risk_alerts
        
        def update_data(self):
            """Update data with small random changes to simulate real-time updates"""
            # Update current prices with small random changes
            for symbol in self.current_prices:
                change_pct = np.random.normal(0, 0.001)  # Small random change
                self.current_prices[symbol] *= (1 + change_pct)
            
            # Update positions with new current prices
            for position in self.positions:
                position['current'] = self.current_prices.get(position['symbol'], position['current'])
            
            # Update signals with new prices
            for signal in self.signals:
                signal['price'] = self.current_prices.get(signal['symbol'], signal['price'])
            
            # Update portfolio value based on positions
            portfolio_change = sum([(pos['current'] - pos['entry']) * pos['position'] for pos in self.positions])
            self.current_value = self.initial_value + portfolio_change
            
            # Update performance history
            last_date = pd.Timestamp(self.history['portfolio'][-1]['x']) + pd.Timedelta(days=1)
            new_portfolio_value = self.history['portfolio'][-1]['y'] * (1 + np.random.normal(0, 0.005))
            new_benchmark_value = self.history['benchmark'][-1]['y'] * (1 + np.random.normal(0, 0.004))
            
            self.history['portfolio'].append({
                'x': last_date.isoformat(),
                'y': new_portfolio_value
            })
            self.history['benchmark'].append({
                'x': last_date.isoformat(),
                'y': new_benchmark_value
            })
            
            # Occasionally update risk alerts
            if np.random.random() < 0.1:  # 10% chance
                if len(self.risk_alerts) > 2:
                    self.risk_alerts.pop()  # Remove oldest alert
                
                severity_options = ['Low', 'Medium', 'High', 'Critical']
                new_alert = {
                    'title': f'New {np.random.choice(severity_options)} Alert',
                    'message': f'This is a simulated alert at {datetime.datetime.now().strftime("%H:%M:%S")}',
                    'severity': np.random.choice(severity_options),
                    'timestamp': datetime.datetime.now().isoformat()
                }
                self.risk_alerts.insert(0, new_alert)
            
            # Occasionally change market regime
            if np.random.random() < 0.05:  # 5% chance
                regimes = ['BULL_TREND', 'BEAR_TREND', 'HIGH_VOLATILITY', 'LOW_VOLATILITY', 'CONSOLIDATION']
                self.current_regime = np.random.choice(regimes)
                
        def get_market_data(self):
            """Get market overview data"""
            # Create mock market data
            market_indices = {
                'SPY': {
                    'price': self.current_prices.get('SPY', 520.94),
                    'change': np.random.normal(0, 0.5),
                    'volume': int(np.random.uniform(50000000, 100000000))
                },
                'QQQ': {
                    'price': self.current_prices.get('QQQ', 445.94),
                    'change': np.random.normal(0, 0.6),
                    'volume': int(np.random.uniform(40000000, 80000000))
                },
                'VIX': {
                    'price': np.random.uniform(15, 25),
                    'change': np.random.normal(0, 0.3),
                    'volume': int(np.random.uniform(10000000, 20000000))
                }
            }
            
            # Mock sector performance
            sectors = {
                'Technology': np.random.normal(0.2, 0.5),
                'Healthcare': np.random.normal(0.1, 0.4),
                'Financials': np.random.normal(-0.1, 0.3),
                'Consumer': np.random.normal(0.05, 0.3),
                'Energy': np.random.normal(-0.2, 0.6),
                'Utilities': np.random.normal(0.1, 0.2)
            }
            
            # Market breadth indicators
            breadth = {
                'advancers': int(np.random.uniform(200, 400)),
                'decliners': int(np.random.uniform(100, 300)),
                'unchanged': int(np.random.uniform(50, 150)),
                'new_highs': int(np.random.uniform(20, 100)),
                'new_lows': int(np.random.uniform(5, 50))
            }
            
            # Market status
            market_status = {
                'is_open': 9 <= datetime.datetime.now().hour < 16,  # Simple check for market hours
                'next_event': 'Market Close' if datetime.datetime.now().hour < 16 else 'Market Open',
                'next_event_time': '16:00:00' if datetime.datetime.now().hour < 16 else '09:30:00',
                'trading_day': datetime.datetime.now().strftime('%Y-%m-%d')
            }
            
            return {
                'indices': market_indices,
                'sectors': sectors,
                'breadth': breadth,
                'status': market_status,
                'regime': self.current_regime
            }

    # Initialize data simulator as fallback
    data_simulator = TradingDataSimulator()


# Define data access functions
def get_performance_data(period='7d', ensemble='default'):
    """Get performance data from the appropriate source"""
    if USING_REAL_DATA:
        try:
            # Get time span from period
            time_map = {
                # Minutes
                '1m': {'unit': 'minutes', 'value': 1},
                '5m': {'unit': 'minutes', 'value': 5},
                '15m': {'unit': 'minutes', 'value': 15},
                '30m': {'unit': 'minutes', 'value': 30},
                # Hours
                '1h': {'unit': 'hours', 'value': 1},
                '8h': {'unit': 'hours', 'value': 8},
                # Days
                '1d': {'unit': 'days', 'value': 1},
                '7d': {'unit': 'days', 'value': 7},
                # Months
                '1mo': {'unit': 'days', 'value': 30},
                '3mo': {'unit': 'days', 'value': 90},
                '6mo': {'unit': 'days', 'value': 180},
                '1y': {'unit': 'days', 'value': 365},
                'all': {'unit': 'days', 'value': 1000}  # Use a large number for "all"
            }
            
            # Default to 7 days if period not recognized
            time_span = time_map.get(period, {'unit': 'days', 'value': 7})
            
            # Set cutoff time based on unit and value
            now = datetime.datetime.now()
            if time_span['unit'] == 'minutes':
                cutoff_date = now - datetime.timedelta(minutes=time_span['value'])
                resolution = 'minute'
            elif time_span['unit'] == 'hours':
                cutoff_date = now - datetime.timedelta(hours=time_span['value'])
                resolution = 'minute' if time_span['value'] <= 8 else 'hour'
            else:  # days is the default
                cutoff_date = now - datetime.timedelta(days=time_span['value'])
                resolution = 'hour' if time_span['value'] <= 1 else 'day'
            
            # Get performance metrics from portfolio state
            metrics = portfolio_state.get_performance_metrics(time_span['value'])
            
            # Get historical portfolio values
            history = portfolio_state.performance_history
            
            # Convert to format expected by frontend
            filtered_history = {
                'timestamp': [],
                'portfolio_value': [],
                'cash': []
            }
            
            for i, ts in enumerate(history['timestamp']):
                if ts >= cutoff_date:
                    filtered_history['timestamp'].append(ts)
                    filtered_history['portfolio_value'].append(history['portfolio_value'][i])
                    filtered_history['cash'].append(history['cash'][i])
            
            # Convert to Chart.js format
            portfolio_data = [
                {'x': ts.isoformat(), 'y': val} 
                for ts, val in zip(filtered_history['timestamp'], filtered_history['portfolio_value'])
            ]
            
            # For benchmark, we'll use SPY data if available or generate mock data
            benchmark_data = []
            try:
                # For shorter timeframes, we might need higher resolution data
                spy_data = data_provider.get_historical_data(
                    ['SPY'], 
                    cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    resolution=resolution
                )
                
                if spy_data and 'SPY' in spy_data:
                    spy_df = spy_data['SPY']
                    # Normalize to start at the same value as the portfolio
                    start_value = filtered_history['portfolio_value'][0] if filtered_history['portfolio_value'] else 100000
                    spy_normalized = spy_df['close'] / spy_df['close'].iloc[0] * start_value
                    
                    benchmark_data = [
                        {'x': date.isoformat(), 'y': value} 
                        for date, value in zip(spy_df.index, spy_normalized)
                    ]
            except Exception as e:
                logger.warning(f"Error getting SPY data for benchmark: {e}")
                # Fall back to mock benchmark data
                if portfolio_data:
                    start_value = portfolio_data[0]['y']
                    benchmark_data = [
                        {'x': p['x'], 'y': start_value * (1 + i * 0.0005)} 
                        for i, p in enumerate(portfolio_data)
                    ]
            
            # Format metrics for front-end
            formatted_metrics = {
                'pnl': {
                    'value': portfolio_state.get_portfolio_value() - portfolio_state.initial_cash,
                    'change': metrics['cumulative_return']
                },
                'sharpe': {
                    'value': metrics['sharpe_ratio'],
                    'change': 0  # Change not easily available
                },
                'drawdown': {
                    'value': metrics['max_drawdown'],
                    'change': 0  # Change not easily available
                },
                'volatility': {
                    'value': metrics['volatility'],
                    'change': 0  # Change not easily available
                }
            }
            
            return {
                'performance': {
                    'portfolio': portfolio_data,
                    'benchmark': benchmark_data
                },
                'metrics': formatted_metrics
            }
        except Exception as e:
            logger.error(f"Error getting real performance data: {e}")
            # Fall back to mock data
            return data_simulator.get_performance_data(period)
    else:
        # Use mock data
        return data_simulator.get_performance_data(period)


def get_weights_data(ensemble='default'):
    """Get strategy weights data from the appropriate source"""
    if USING_REAL_DATA:
        try:
            # Get strategy allocations from portfolio state
            allocations = portfolio_state.strategy_allocations
            
            # If no allocations are set, return empty dict
            if not allocations:
                return {}
                
            return allocations
        except Exception as e:
            logger.error(f"Error getting real strategy weights: {e}")
            # Fall back to mock data
            return data_simulator.get_weights_data()
    else:
        # Use mock data
        return data_simulator.get_weights_data()


def get_positions_data(ensemble='default'):
    """Get positions data from the appropriate source"""
    if USING_REAL_DATA:
        try:
            # Get positions from portfolio state
            positions = portfolio_state.positions
            
            # Convert to format expected by frontend
            formatted_positions = []
            for symbol, pos in positions.items():
                formatted_positions.append({
                    'symbol': symbol,
                    'position': pos['quantity'],
                    'entry': pos['avg_price'],
                    'current': pos['current_price']
                })
                
            return formatted_positions
        except Exception as e:
            logger.error(f"Error getting real positions data: {e}")
            # Fall back to mock data
            return data_simulator.get_positions_data()
    else:
        # Use mock data
        return data_simulator.get_positions_data()


def get_signals_data(ensemble='default'):
    """Get signals data"""
    # Currently always using mock data for signals since we don't have a real signal generator
    return data_simulator.get_signals_data()


def get_strategy_performance_data(ensemble='default'):
    """Get strategy performance data from the appropriate source"""
    if USING_REAL_DATA:
        try:
            # Get strategy performance from portfolio state
            strategy_performance = portfolio_state.strategy_performance
            
            # Convert to format expected by frontend
            formatted_performance = []
            for strategy, metrics in strategy_performance.items():
                # Get allocation weight for this strategy
                weight = portfolio_state.strategy_allocations.get(strategy, 0)
                
                formatted_performance.append({
                    'name': strategy,
                    'weight': weight,
                    'return': metrics.get('return', 0),
                    'sharpe': metrics.get('sharpe', 0),
                    'drawdown': metrics.get('drawdown', 0),
                    'winRate': metrics.get('win_rate', 0)
                })
                
            return formatted_performance
        except Exception as e:
            logger.error(f"Error getting real strategy performance: {e}")
            # Fall back to mock data
            return data_simulator.get_strategy_performance_data()
    else:
        # Use mock data
        return data_simulator.get_strategy_performance_data()


def get_correlation_data(ensemble='default'):
    """Get correlation data"""
    # Currently always using mock data for correlation since we don't calculate it yet
    return data_simulator.get_correlation_data()


def get_risk_alerts_data(ensemble='default'):
    """Get risk alerts data"""
    # Currently always using mock data for risk alerts since we don't generate them yet
    return data_simulator.get_risk_alerts_data()


def update_real_data():
    """Update real data from market data provider"""
    if USING_REAL_DATA:
        try:
            # Get current prices for all positions
            symbols = list(portfolio_state.positions.keys())
            
            if symbols:
                # Get current prices from data provider
                current_prices = data_provider.get_current_price(symbols)
                
                # Update positions with current prices
                portfolio_state.update_prices(current_prices)
                
                # Save state to file
                portfolio_state.save_state(PORTFOLIO_STATE_FILE)
                
                logger.info(f"Updated real data for {len(symbols)} symbols")
            else:
                logger.info("No positions to update")
        except Exception as e:
            logger.error(f"Error updating real data: {e}")


# Define routes
@app.route('/')
def serve_dashboard():
    """Serve the main dashboard page."""
    logger.info("Serving dashboard page")
    return render_template('dashboard.html')


# API endpoints
@app.route('/api/performance')
def performance():
    period = request.args.get('period', '1m')
    ensemble = request.args.get('ensemble', 'default')
    
    # Get performance data
    data = get_performance_data(period, ensemble)
    
    return jsonify(data)


@app.route('/api/weights')
def weights():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get weights data
    data = get_weights_data(ensemble)
    
    return jsonify({'weights': data})


@app.route('/api/signals')
def signals():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get signals data
    data = get_signals_data(ensemble)
    
    return jsonify({'signals': data})


@app.route('/api/positions')
def positions():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get positions data
    data = get_positions_data(ensemble)
    
    return jsonify({'positions': data})


@app.route('/api/strategy_performance')
def strategy_performance():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get strategy performance data
    data = get_strategy_performance_data(ensemble)
    
    return jsonify({'strategies': data})


@app.route('/api/correlation')
def correlation():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get correlation data
    data = get_correlation_data(ensemble)
    
    return jsonify({'correlation': data})


@app.route('/api/risk_alerts')
def risk_alerts():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get risk alerts data
    data = get_risk_alerts_data(ensemble)
    
    return jsonify({'alerts': data})


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")
    
    global thread
    if thread is None or not thread.is_alive():
        thread = socketio.start_background_task(target=background_thread)
        logger.info("Started background thread for updates")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")
    # We don't stop the background thread here as other clients might be connected
    # The thread will be stopped when the server shuts down

@socketio.on('subscribe')
def handle_subscribe(data):
    ensemble = data.get('ensemble', 'default')
    logger.info(f'Client subscribed to ensemble: {ensemble}')
    emit('subscription_confirmed', {'ensemble': ensemble})


# Main function to run the app
def run_dashboard_server(debug=False, host='0.0.0.0', port=8090):
    """Run the dashboard server."""
    # Get port from environment variable if available
    port = int(os.environ.get('PORT', port))
    
    logger.info(f"Starting dashboard server on {host}:{port}")
    
    # Start background thread for updates
    if not DASHBOARD_THREAD_RUNNING:
        global thread
        thread = socketio.start_background_task(target=background_thread)
        logger.info("Started background thread for updates")
    
    # Run the app
    try:
        # In newer versions of Flask-SocketIO, socketio.run() has different parameters
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    except TypeError:
        # Fall back to older version syntax
        try:
            socketio.run(app, host=host, port=port, debug=debug)
        except Exception as e:
            logger.error(f"Error starting the server: {e}")
            # Last resort: try with basic Flask run
            app.run(host=host, port=port, debug=debug)

# Background thread function
def background_thread():
    """Background thread that sends data to clients."""
    count = 0
    while True:
        socketio.sleep(UPDATE_INTERVAL)
        count += 1
        
        # Every minute, update all data
        if count % (60 // UPDATE_INTERVAL) == 0:
            try:
                # Get all dashboard data
                update_data = get_dashboard_update()
                
                # Send comprehensive update to clients
                socketio.emit('dashboard_update', update_data)
                logger.debug("Sent full dashboard update")
            except Exception as e:
                logger.error(f"Error in background thread: {e}")
                logger.error(traceback.format_exc())
        
        # Every interval, just update market and portfolio data
        else:
            try:
                # Get only the frequently changing data
                market_data = {}
                if USING_REAL_DATA:
                    market_data = data_provider.get_market_overview()
                else:
                    market_data = data_simulator.get_market_data()
                
                socketio.emit('market_update', market_data)
                logger.debug("Sent market update")
            except Exception as e:
                logger.error(f"Error updating market data: {e}")


def get_dashboard_update():
    """Collect all dashboard data for a comprehensive update."""
    update_data = {}
    
    try:
        # Market data
        if USING_REAL_DATA:
            market_data = data_provider.get_market_overview()
        else:
            market_data = data_simulator.get_market_data()
        update_data['market'] = market_data
        
        # Portfolio data
        update_data['positions'] = get_positions_data()
        update_data['performance'] = get_performance_data('1d')
        
        # Strategy data
        update_data['strategies'] = get_strategy_performance_data()
        update_data['weights'] = get_weights_data()
        update_data['signals'] = get_signals_data()
        
        # Risk data
        update_data['risk_alerts'] = get_risk_alerts_data()
        update_data['correlation'] = get_correlation_data()
        
        if not USING_REAL_DATA:
            update_data['regime'] = data_simulator.current_regime
            
        return update_data
        
    except Exception as e:
        logger.error(f"Error collecting dashboard update data: {e}")
        logger.error(traceback.format_exc())
        return {'error': str(e)}


def start_background_thread():
    """Start the background update thread if it's not already running."""
    global thread, DASHBOARD_THREAD_RUNNING
    
    if thread is None or not DASHBOARD_THREAD_RUNNING:
        logger.info("Starting new background thread")
        thread = threading.Thread(target=background_thread)
        thread.daemon = True  # Thread will exit when main thread exits
        thread.start()
        return True
    else:
        logger.info("Background thread already running")
        return False


# Stop the background thread when the server shuts down
@app.before_request
def before_request():
    """Check if the background thread is running before each request."""
    global thread
    if thread is None or not thread.is_alive():
        thread = socketio.start_background_task(target=background_thread)
        logger.info("Started background thread for updates")


def update_market_data():
    """Update market data and emit to clients."""
    if USING_REAL_DATA:
        try:
            # Get current market data from data provider
            market_data = data_provider.get_market_overview()
            socketio.emit('market_update', market_data)
            logger.debug("Sent market data update")
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    else:
        # Use simulated data
        market_data = data_simulator.get_market_data()
        socketio.emit('market_update', market_data)
        logger.debug("Sent simulated market data update")

def update_portfolio_data():
    """Update portfolio data and emit to clients."""
    try:
        portfolio_data = get_positions_data()
        performance_data = get_performance_data('1d')
        
        # Combine data
        update_data = {
            'positions': portfolio_data,
            'performance': performance_data
        }
        
        socketio.emit('portfolio_update', update_data)
        logger.debug("Sent portfolio data update")
    except Exception as e:
        logger.error(f"Error updating portfolio data: {e}")

def update_strategy_data():
    """Update strategy data and emit to clients."""
    try:
        strategies_data = get_strategy_performance_data()
        weights_data = get_weights_data()
        signals_data = get_signals_data()
        
        # Combine data
        update_data = {
            'strategies': strategies_data,
            'weights': weights_data,
            'signals': signals_data
        }
        
        socketio.emit('strategy_update', update_data)
        logger.debug("Sent strategy data update")
    except Exception as e:
        logger.error(f"Error updating strategy data: {e}")

def update_risk_metrics():
    """Update risk metrics and emit to clients."""
    try:
        risk_alerts = get_risk_alerts_data()
        correlation_data = get_correlation_data()
        
        # Combine data
        update_data = {
            'alerts': risk_alerts,
            'correlation': correlation_data,
        }
        
        if not USING_REAL_DATA:
            update_data['regime'] = data_simulator.current_regime
        
        socketio.emit('risk_update', update_data)
        logger.debug("Sent risk metrics update")
    except Exception as e:
        logger.error(f"Error updating risk metrics: {e}")


if __name__ == '__main__':
    run_dashboard_server(debug=True, host='0.0.0.0', port=8090) 