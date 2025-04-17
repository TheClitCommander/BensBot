import os
import json
import logging
import datetime
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import Flask-CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Placeholder for real data that would come from the trading system
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
    
    def get_performance_data(self, period='1m'):
        """Get performance data for the specified period"""
        # Map period to number of days
        days_map = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '1y': 365,
            'all': len(self.history['portfolio'])
        }
        
        days = days_map.get(period, 30)
        
        # Get data for the specified period
        portfolio_data = self.history['portfolio'][-days:]
        benchmark_data = self.history['benchmark'][-days:]
        
        # Calculate metrics
        start_value = portfolio_data[0]['y']
        end_value = portfolio_data[-1]['y']
        pnl = end_value - start_value
        pnl_percentage = (pnl / start_value) * 100
        
        # Calculate daily change
        today_value = portfolio_data[-1]['y']
        yesterday_value = portfolio_data[-2]['y'] if len(portfolio_data) > 1 else today_value
        daily_change = ((today_value / yesterday_value) - 1) * 100
        
        # Mock Sharpe ratio calculation
        portfolio_returns = np.diff([p['y'] for p in portfolio_data]) / [p['y'] for p in portfolio_data[:-1]]
        benchmark_returns = np.diff([b['y'] for b in benchmark_data]) / [b['y'] for b in benchmark_data[:-1]]
        
        portfolio_sharpe = np.mean(portfolio_returns) / np.std(portfolio_returns) if np.std(portfolio_returns) > 0 else 0
        benchmark_sharpe = np.mean(benchmark_returns) / np.std(benchmark_returns) if np.std(benchmark_returns) > 0 else 0
        sharpe_diff = portfolio_sharpe - benchmark_sharpe
        
        # Mock drawdown calculation
        rolling_max = np.maximum.accumulate([p['y'] for p in portfolio_data])
        drawdowns = (rolling_max - [p['y'] for p in portfolio_data]) / rolling_max * 100
        max_drawdown = np.max(drawdowns)
        
        # Calculate average drawdown for comparison
        avg_drawdown = np.mean(drawdowns)
        drawdown_change = max_drawdown - avg_drawdown
        
        # Mock volatility calculation
        volatility = np.std(portfolio_returns) * 100 * np.sqrt(252)  # Annualized
        avg_volatility = volatility * 0.9  # Mock average volatility (slightly lower)
        volatility_change = volatility - avg_volatility
        
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


# Initialize data simulator
data_simulator = TradingDataSimulator()


# Define routes
@app.route('/')
def index():
    return render_template('dashboard.html')


# API endpoints
@app.route('/api/performance')
def performance():
    period = request.args.get('period', '1m')
    ensemble = request.args.get('ensemble', 'default')
    
    # Get performance data from simulator
    data = data_simulator.get_performance_data(period)
    
    return jsonify(data)


@app.route('/api/weights')
def weights():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get weights data from simulator
    data = data_simulator.get_weights_data()
    
    return jsonify({'weights': data})


@app.route('/api/signals')
def signals():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get signals data from simulator
    data = data_simulator.get_signals_data()
    
    return jsonify({'signals': data})


@app.route('/api/positions')
def positions():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get positions data from simulator
    data = data_simulator.get_positions_data()
    
    return jsonify({'positions': data})


@app.route('/api/strategy_performance')
def strategy_performance():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get strategy performance data from simulator
    data = data_simulator.get_strategy_performance_data()
    
    return jsonify({'strategies': data})


@app.route('/api/correlation')
def correlation():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get correlation data from simulator
    data = data_simulator.get_correlation_data()
    
    return jsonify({'correlation': data})


@app.route('/api/risk_alerts')
def risk_alerts():
    ensemble = request.args.get('ensemble', 'default')
    
    # Get risk alerts data from simulator
    data = data_simulator.get_risk_alerts_data()
    
    return jsonify({'alerts': data})


# WebSocket events
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connect', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')


@socketio.on('subscribe')
def handle_subscribe(data):
    ensemble = data.get('ensemble', 'default')
    logger.info(f'Client subscribed to ensemble: {ensemble}')
    emit('subscription_confirmed', {'ensemble': ensemble})


# Simulate real-time updates
def send_updates():
    # Update data
    data_simulator.update_data()
    
    # Send performance update
    performance_data = data_simulator.get_performance_data('1d')
    socketio.emit('message', {
        'type': 'performance_update',
        'performance': performance_data['performance'],
        'metrics': performance_data['metrics']
    })
    
    # Send weights update
    weights_data = data_simulator.get_weights_data()
    socketio.emit('message', {
        'type': 'weights_update',
        'weights': weights_data
    })
    
    # Send signals update
    signals_data = data_simulator.get_signals_data()
    socketio.emit('message', {
        'type': 'signals_update',
        'signals': signals_data
    })
    
    # Send positions update
    positions_data = data_simulator.get_positions_data()
    socketio.emit('message', {
        'type': 'positions_update',
        'positions': positions_data
    })
    
    # Send strategy performance update
    strategy_data = data_simulator.get_strategy_performance_data()
    socketio.emit('message', {
        'type': 'strategy_performance_update',
        'strategies': strategy_data
    })
    
    # Send correlation update
    correlation_data = data_simulator.get_correlation_data()
    socketio.emit('message', {
        'type': 'correlation_update',
        'correlation': correlation_data
    })
    
    # Send risk alerts update
    alerts_data = data_simulator.get_risk_alerts_data()
    socketio.emit('message', {
        'type': 'risk_alerts_update',
        'alerts': alerts_data
    })
    
    # Send regime update
    socketio.emit('message', {
        'type': 'regime_update',
        'regime': data_simulator.current_regime
    })


if __name__ == '__main__':
    from threading import Thread
    import time
    
    # Start update thread
    def update_thread():
        while True:
            send_updates()
            time.sleep(5)  # Send updates every 5 seconds
    
    thread = Thread(target=update_thread)
    thread.daemon = True
    thread.start()
    
    # Start Flask app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 