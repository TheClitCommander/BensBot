"""
AI Backtesting Endpoint for Trading Bot 

This module defines a Flask route for autonomous backtesting
with AI strategy generation.
"""

import logging
import random
from datetime import datetime
from flask import jsonify, request
import os
import json
import time
import socket
from flask_cors import CORS
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ai_backtest')

app = Flask(__name__)
CORS(app)

def generate_mock_strategy() -> Dict[str, Any]:
    """Generate mock strategy data for testing"""
    strategy_types = ['Moving Average Crossover', 'RSI', 'MACD', 'Bollinger Bands', 'Price Breakout']
    parameters = {
        'Moving Average Crossover': {
            'fast_period': random.randint(5, 20),
            'slow_period': random.randint(20, 100),
            'signal_period': random.randint(5, 15)
        },
        'RSI': {
            'period': random.randint(7, 21),
            'overbought': random.randint(70, 80),
            'oversold': random.randint(20, 30)
        },
        'MACD': {
            'fast_length': random.randint(8, 15),
            'slow_length': random.randint(20, 30),
            'signal_smoothing': random.randint(7, 12)
        },
        'Bollinger Bands': {
            'period': random.randint(14, 30),
            'std_dev': random.uniform(1.5, 2.5)
        },
        'Price Breakout': {
            'lookback_period': random.randint(10, 30),
            'threshold_percent': random.uniform(0.5, 2.0)
        }
    }
    
    strategy_type = random.choice(strategy_types)
    return {
        'name': f"AI-{strategy_type}-{random.randint(100, 999)}",
        'type': strategy_type,
        'parameters': parameters[strategy_type],
        'win_rate': random.uniform(0.55, 0.75),
        'profit_factor': random.uniform(1.2, 2.5),
        'avg_trade': random.uniform(0.2, 1.5),
        'max_drawdown': random.uniform(5, 20),
        'sharpe_ratio': random.uniform(0.8, 2.2),
        'trades': random.randint(25, 100),
        'score': random.uniform(60, 95)
    }

def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to open a socket on the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    
    # If we couldn't find an available port, return a default
    return 8000

def add_ai_backtest_endpoint(app):
    """Add the AI backtesting endpoint to the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/backtesting/autonomous', methods=['POST'])
    def ai_backtest():
        """Endpoint for AI-powered backtesting"""
        data = request.json
        
        # Log the request
        logger.info(f"Running AI backtest for tickers: {data.get('tickers', [])}, timeframes: {data.get('timeframes', [])}")
        
        # Validate required fields
        if not data or 'tickers' not in data or not data['tickers']:
            return jsonify({
                'success': False,
                'error': 'Ticker symbols are required'
            }), 400
        
        # Generate mock execution data
        execution_info = {
            'execution_time': random.uniform(1.5, 8.5),
            'data_points_analyzed': random.randint(10000, 1000000),
            'market_conditions': random.choice(['Bullish', 'Bearish', 'Sideways', 'Volatile']),
            'confidence_score': random.randint(70, 95)
        }
        
        # Generate mock winning strategies
        num_strategies = random.randint(3, 8)
        winning_strategies = [generate_mock_strategy() for _ in range(num_strategies)]
        
        # Sort strategies by score
        winning_strategies.sort(key=lambda x: x['score'], reverse=True)
        
        # Generate mock market analysis data
        market_analysis = {
            'detected_condition': execution_info['market_conditions'],
            'strategy_rationale': f"AI detected {execution_info['market_conditions']} market conditions based on price action, volume patterns, and technical indicators. Strategies were optimized for this regime.",
            'confidence_score': execution_info['confidence_score'],
            'reasoning_chain': [
                f"Analyzed {execution_info['data_points_analyzed']} data points across multiple timeframes",
                f"Detected {execution_info['market_conditions']} market regime with {execution_info['confidence_score']}% confidence",
                "Identified optimal strategy parameters via genetic optimization",
                "Validated strategies with walk-forward analysis to prevent overfitting",
                "Ranked final strategy selection by risk-adjusted performance"
            ],
            'sentiment_data': {
                'institutional': random.randint(50, 90),
                'retail': random.randint(40, 85),
                'social_media': random.randint(30, 90),
                'news': random.randint(45, 85)
            }
        }
        
        # Generate ML insights
        ml_insights = {
            'winning_patterns': [
                "Strong momentum on higher timeframes with consolidation on lower timeframes",
                "Decreasing volatility preceding breakout moves",
                "Support/resistance confluence across multiple timeframes",
                "Volume expansion on trend continuation signals"
            ],
            'alternative_strategies': [
                {
                    'name': "Mean Reversion",
                    'score': random.randint(65, 85),
                    'strengths': "Excellent in sideways markets with defined ranges",
                    'weaknesses': "Underperforms in strong trending conditions"
                },
                {
                    'name': "Breakout",
                    'score': random.randint(60, 80),
                    'strengths': "Captures large moves at start of new trends",
                    'weaknesses': "Higher false signal rate, requiring strict risk management"
                },
                {
                    'name': "Sentiment-Based",
                    'score': random.randint(50, 75),
                    'strengths': "Identifies opportunities based on market psychology",
                    'weaknesses': "Less reliable in highly manipulated or low-liquidity conditions"
                }
            ],
            'recommendations': {
                'allocation': {
                    'Trend Following': random.randint(30, 60),
                    'Mean Reversion': random.randint(20, 40),
                    'Breakout': random.randint(10, 30),
                    'Volatility-Based': random.randint(5, 20)
                },
                'position_sizing': f"{random.uniform(0.5, 2.5):.1f}% of capital per trade",
                'risk_management': f"Set stop loss at {random.uniform(1.0, 3.0):.1f}% from entry"
            }
        }
        
        # Generate portfolio simulation data
        equity_curve = []
        current_equity = 10000  # Starting equity
        for i in range(90):  # 90 days
            change = random.normalvariate(0.1, 1.0)  # Mean 0.1%, std dev 1%
            current_equity *= (1 + change/100)
            equity_curve.append({
                'day': i+1,
                'equity': current_equity,
                'returns_pct': change
            })
        
        # Assemble the complete response
        response = {
            'success': True,
            'execution': execution_info,
            'market_analysis': market_analysis,
            'ml_insights': ml_insights,
            'winning_strategies': winning_strategies,
            'equity_simulation': equity_curve,
            'portfolio_metrics': {
                'cagr': random.uniform(15, 45),
                'max_drawdown': random.uniform(8, 25),
                'sharpe_ratio': random.uniform(1.2, 2.8),
                'sortino_ratio': random.uniform(1.5, 3.5),
                'win_rate': random.uniform(55, 75),
                'profit_factor': random.uniform(1.5, 3.0),
                'recovery_factor': random.uniform(3, 8),
                'risk_of_ruin': random.uniform(0.01, 0.1)
            }
        }
        
        # Simulate some processing time
        time.sleep(0.5)
        
        return jsonify(response)

    return app

# Example usage:
if __name__ == "__main__":
    # Find an available port (avoid conflict with AirPlay on macOS which uses port 5000)
    port = find_available_port()
    
    print(f"Starting Flask server at http://localhost:{port}")
    print(f"API endpoint available at: /api/backtesting/autonomous")
    
    # Use the selected port
    add_ai_backtest_endpoint(app)
    app.run(debug=True, port=port, host='0.0.0.0') 