#!/usr/bin/env python3
"""
Simple Portfolio Dashboard - A lightweight dashboard without complex dependencies
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('simple_dashboard')

# Create Flask app
app = Flask(__name__)

# Sample portfolio data
portfolio_data = {
    "portfolio": {
        "cash": 50000.0,
        "total_value": 100000.0,
        "positions": {
            "AAPL": {
                "quantity": 100,
                "avg_price": 150.0,
                "current_price": 170.25,
                "current_value": 17025.0,
                "unrealized_pnl": 2025.0,
                "unrealized_pnl_pct": 13.5
            },
            "MSFT": {
                "quantity": 50,
                "avg_price": 250.0,
                "current_price": 280.50,
                "current_value": 14025.0,
                "unrealized_pnl": 1525.0,
                "unrealized_pnl_pct": 6.1
            },
            "GOOGL": {
                "quantity": 30,
                "avg_price": 125.0,
                "current_price": 135.75,
                "current_value": 4072.5,
                "unrealized_pnl": 322.5,
                "unrealized_pnl_pct": 8.6
            }
        },
        "asset_allocation": {
            "Technology": 75.5,
            "Cash": 24.5
        }
    },
    "performance_metrics": {
        "cumulative_return": 15.2,
        "sharpe_ratio": 1.8,
        "max_drawdown": -8.5,
        "volatility": 12.3,
        "win_rate": 68.5,
        "profit_factor": 2.3,
        "recent_daily_returns": [0.8, -0.3, 1.2, 0.5, -0.2]
    },
    "recent_activity": {
        "trades": [
            {
                "timestamp": datetime.now().isoformat(),
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 25,
                "price": 168.75
            },
            {
                "timestamp": datetime.now().isoformat(),
                "symbol": "NFLX",
                "action": "SELL",
                "quantity": 15,
                "price": 410.25
            }
        ],
        "signals": [
            {
                "timestamp": datetime.now().isoformat(),
                "symbol": "TSLA",
                "signal_type": "BUY",
                "strength": 0.85,
                "source": "pattern_recognition"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "symbol": "MSFT",
                "signal_type": "HOLD",
                "strength": 0.62,
                "source": "fundamental"
            }
        ]
    },
    "strategy_data": {
        "active_strategies": ["momentum", "mean_reversion", "trend_following"],
        "strategy_allocations": {
            "momentum": 40,
            "mean_reversion": 30,
            "trend_following": 30
        },
        "strategy_performance": {
            "momentum": {
                "return": 12.5,
                "sharpe": 1.4
            },
            "mean_reversion": {
                "return": 8.2,
                "sharpe": 1.1
            },
            "trend_following": {
                "return": 15.8,
                "sharpe": 1.7
            }
        }
    },
    "system_status": {
        "is_market_open": True,
        "market_hours": "9:30 AM - 4:00 PM ET",
        "data_providers": ["alpha_vantage", "yahoo_finance"],
        "connected_brokers": ["paper_trading"],
        "system_health": {
            "cpu_usage": 35,
            "memory_usage": 42,
            "disk_space": 75
        }
    },
    "learning_status": {
        "training_in_progress": False,
        "models_status": {
            "price_predictor": {
                "accuracy": 0.72,
                "last_trained": datetime.now().isoformat()
            },
            "volatility_estimator": {
                "accuracy": 0.68,
                "last_trained": datetime.now().isoformat()
            }
        },
        "recent_learning_metrics": {
            "training_cycles": 15,
            "validation_loss": 0.082,
            "training_time_seconds": 450
        }
    },
    "last_updated": datetime.now().isoformat()
}

@app.route('/api/portfolio')
def get_portfolio():
    """Return portfolio state as JSON for API access."""
    return jsonify(portfolio_data)

@app.route('/')
def index():
    """Render main dashboard page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Trading Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
                color: #2c3e50;
            }
            
            /* Navigation Styles */
            .top-nav {
                background-color: #2c3e50;
                color: white;
                display: flex;
                justify-content: space-between;
                padding: 0 20px;
                height: 60px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .nav-brand {
                display: flex;
                align-items: center;
                font-size: 20px;
                font-weight: 600;
            }
            
            /* Card Styles */
            .card { 
                margin-bottom: 20px; 
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                padding: 25px;
                border: 1px solid #edf2f7;
            }
            
            .card h2 {
                color: #34495e;
                margin-top: 0;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #edf2f7;
            }
            
            .position-row:hover { background-color: #f8f9fa; }
            .positive { color: green; }
            .negative { color: red; }

            /* Main Content Styles */
            .main-content {
                max-width: 1200px;
                margin: 20px auto;
                padding: 0 20px;
            }
            
            .page-title {
                font-size: 24px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #ecf0f1;
            }
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-brand">Simple Trading Dashboard</div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <h1 class="page-title">Portfolio Overview</h1>
            
            <div class="row">
                <!-- Portfolio Overview -->
                <div class="col-md-6">
                    <div class="card">
                        <h2>Portfolio Summary</h2>
                        <div class="row">
                            <div class="col-md-6">
                                <h3>$<span id="total-value">0</span></h3>
                                <p class="text-muted">Total Portfolio Value</p>
                            </div>
                            <div class="col-md-6">
                                <h3>$<span id="cash">0</span></h3>
                                <p class="text-muted">Cash Available</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Positions -->
                    <div class="card">
                        <h2>Positions</h2>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Quantity</th>
                                        <th>Price</th>
                                        <th>Value</th>
                                        <th>P&L</th>
                                    </tr>
                                </thead>
                                <tbody id="positions-table">
                                    <!-- Positions will be populated here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- Performance Metrics -->
                <div class="col-md-6">
                    <div class="card">
                        <h2>Performance Metrics</h2>
                        <div class="row">
                            <div class="col-md-4">
                                <p><strong>Return:</strong> <span id="return">0</span>%</p>
                                <p><strong>Sharpe:</strong> <span id="sharpe">0</span></p>
                                <p><strong>Win Rate:</strong> <span id="win-rate">0</span>%</p>
                            </div>
                            <div class="col-md-4">
                                <p><strong>Drawdown:</strong> <span id="drawdown">0</span>%</p>
                                <p><strong>Volatility:</strong> <span id="volatility">0</span>%</p>
                                <p><strong>Profit Factor:</strong> <span id="profit-factor">0</span></p>
                            </div>
                            <div class="col-md-4">
                                <p><strong>Recent Returns:</strong></p>
                                <ul id="recent-returns" class="list-unstyled">
                                    <!-- Recent returns will be populated here -->
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recent Trades -->
                    <div class="card">
                        <h2>Recent Trades</h2>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Symbol</th>
                                        <th>Action</th>
                                        <th>Quantity</th>
                                        <th>Price</th>
                                    </tr>
                                </thead>
                                <tbody id="trades-table">
                                    <!-- Trades will be populated here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Function to fetch portfolio data and update the UI
            function updatePortfolioData() {
                fetch('/api/portfolio')
                    .then(response => response.json())
                    .then(data => {
                        // Update portfolio overview
                        document.getElementById('total-value').innerText = data.portfolio.total_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('cash').innerText = data.portfolio.cash.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        
                        // Update positions
                        const positionsTable = document.getElementById('positions-table');
                        positionsTable.innerHTML = '';
                        Object.entries(data.portfolio.positions).forEach(([symbol, position]) => {
                            const row = document.createElement('tr');
                            row.classList.add('position-row');
                            const pnlClass = position.unrealized_pnl >= 0 ? 'positive' : 'negative';
                            row.innerHTML = `
                                <td>${symbol}</td>
                                <td>${position.quantity}</td>
                                <td>$${position.current_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                                <td>$${position.current_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                                <td class="${pnlClass}">$${position.unrealized_pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} (${position.unrealized_pnl_pct.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}%)</td>
                            `;
                            positionsTable.appendChild(row);
                        });
                        
                        // Update performance metrics
                        document.getElementById('return').innerText = data.performance_metrics.cumulative_return.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('sharpe').innerText = data.performance_metrics.sharpe_ratio.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('win-rate').innerText = data.performance_metrics.win_rate.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('drawdown').innerText = data.performance_metrics.max_drawdown.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('volatility').innerText = data.performance_metrics.volatility.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        document.getElementById('profit-factor').innerText = data.performance_metrics.profit_factor.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        
                        // Update recent returns
                        const recentReturns = document.getElementById('recent-returns');
                        recentReturns.innerHTML = '';
                        data.performance_metrics.recent_daily_returns.forEach((ret, index) => {
                            const li = document.createElement('li');
                            const retClass = ret >= 0 ? 'positive' : 'negative';
                            li.classList.add(retClass);
                            li.innerText = `Day ${index + 1}: ${ret.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}%`;
                            recentReturns.appendChild(li);
                        });
                        
                        // Update recent trades
                        const tradesTable = document.getElementById('trades-table');
                        tradesTable.innerHTML = '';
                        data.recent_activity.trades.forEach(trade => {
                            const date = new Date(trade.timestamp);
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${date.toLocaleString()}</td>
                                <td>${trade.symbol}</td>
                                <td>${trade.action}</td>
                                <td>${trade.quantity}</td>
                                <td>$${trade.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                            `;
                            tradesTable.appendChild(row);
                        });
                    })
                    .catch(error => console.error('Error fetching portfolio data:', error));
            }
            
            // Update data on page load
            document.addEventListener('DOMContentLoaded', () => {
                updatePortfolioData();
            });
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = 8080
    
    print(f"\n🚀 Simple Dashboard is running at: http://localhost:{port}")
    print("📱 Try these URLs in your browser:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True) 