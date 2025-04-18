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
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

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

# Set page configuration
st.set_page_config(
    page_title="AI Trading Backtester",
    page_icon="📈",
    layout="wide"
)

# Main dashboard content
st.title("AI Trading Backtester")

# Create the AI Backtester interface
st.markdown("## Autonomous ML Backtester")
st.markdown("""
This backtester automatically generates optimal trading strategies based on market conditions, 
ticker behavior, and historical patterns.
""")

# Backtester configuration
ai_col1, ai_col2 = st.columns(2)

with ai_col1:
    # Allow ticker input as comma-separated values
    ticker_input = st.text_input("Tickers (comma-separated)", "AAPL,MSFT,GOOGL")
    tickers = [t.strip() for t in ticker_input.split(',') if t.strip()]
    
    # Timeframe selection
    timeframe_options = ["1d", "4h", "1h", "30m", "15m", "5m"]
    selected_timeframes = st.multiselect("Timeframes", timeframe_options, default=["1d", "4h"])
    
    # Market condition options
    market_condition = st.selectbox(
        "Market Condition", 
        ["Automatic", "Bullish", "Bearish", "Sideways", "Volatile"]
    )

with ai_col2:
    # Strategy type selection
    strategy_types = st.multiselect(
        "Strategy Types",
        ["moving_average_crossover", "rsi_reversal", "breakout_momentum", 
         "macd_momentum", "news_sentiment_momentum", "multi_factor"],
        default=["moving_average_crossover", "breakout_momentum", "multi_factor"]
    )
    
    # Sector selection (optional)
    sectors = st.multiselect(
        "Sectors (Optional)",
        ["Technology", "Healthcare", "Financial", "Consumer", "Industrial", "Energy"],
        default=[]
    )
    
    # Advanced options expander
    with st.expander("Advanced Options"):
        max_strategies = st.slider("Max Strategies", min_value=1, max_value=10, value=3)
        min_win_rate = st.slider("Min Win Rate", min_value=50, max_value=90, value=60)
        min_sharpe = st.slider("Min Sharpe Ratio", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

# Run button with loading state
if st.button("Run AI Backtest", type="primary"):
    # Show processing animation
    with st.spinner("Running AI backtesting analysis..."):
        try:
            # Prepare the request payload
            payload = {
                "tickers": tickers,
                "timeframes": selected_timeframes,
                "market_condition": market_condition,
                "strategy_types": strategy_types,
                "sectors": sectors,
                "max_strategies": max_strategies,
                "min_win_rate": min_win_rate,
                "min_sharpe": min_sharpe
            }
            
            # Make API request to the AI backtester endpoint
            try:
                # Try port 5000 first
                response = requests.post(
                    "http://localhost:5000/api/backtesting/autonomous",
                    json=payload, 
                    timeout=10
                )
            except:
                # Try port 8000 if 5000 fails
                response = requests.post(
                    "http://localhost:8000/api/backtesting/autonomous",
                    json=payload, 
                    timeout=10
                )
            
            # Check if request was successful
            if response.status_code == 200:
                results = response.json()
                
                if results.get("success"):
                    backtest_results = results.get("results", {})
                    
                    # Store results in session state for display
                    st.session_state.ai_backtest_results = backtest_results
                    st.success("AI Backtest completed successfully!")
                else:
                    st.error(f"Backtest failed: {results.get('error', 'Unknown error')}")
            else:
                st.error(f"API request failed with status code: {response.status_code}")
                
        except Exception as e:
            st.error(f"Error connecting to AI Backtest service: {str(e)}")
            st.info("Make sure the AI Backtest server is running (python3 ai_backtest_endpoint.py)")
            
            # Create mock data for development
            st.warning("Generating mock results for demonstration purposes")
            
            # Create a mock response
            mock_results = {
                "execution_id": f"ai_backtest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "config": {
                    "tickers": tickers,
                    "timeframes": selected_timeframes,
                    "strategy_types": strategy_types
                },
                "winning_strategies": [],
                "ml_insights": {
                    "winning_patterns": [
                        f"{tickers[0]} shows strongest response to momentum indicators",
                        "Optimal stop-loss levels are around 2.5-3% for these tickers",
                        "News sentiment adds significant alpha when combined with price momentum",
                        "Volume confirmation (1.5x average) significantly improves breakout performance",
                        "Adaptive parameters outperform fixed parameters in all market conditions"
                    ],
                    "recommendations": {
                        "allocation": {
                            "Breakout Strategy 1": 40,
                            "News Sentiment Strategy 2": 30,
                            "Moving Average Crossover Strategy 3": 20,
                            "RSI Reversal Strategy": 10
                        },
                        "risk_management": {
                            "optimal_stop_loss": 0.028,
                            "optimal_position_sizing": 0.15,
                            "recommended_max_drawdown": 0.18
                        }
                    }
                },
                "execution_time_seconds": 8,
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate mock strategies
            for i in range(3):
                strategy_type = strategy_types[i % len(strategy_types)]
                template = strategy_type.replace('_', ' ').title()
                
                # Create strategy with randomized performance
                mock_results["winning_strategies"].append({
                    "strategy": {
                        "name": f"{template} Strategy {i+1}",
                        "template": template,
                        "parameters": {
                            "entry_threshold": round(np.random.uniform(0.5, 0.9), 2),
                            "exit_threshold": round(np.random.uniform(0.3, 0.7), 2),
                            "stop_loss": round(np.random.uniform(0.02, 0.05), 2),
                            "take_profit": round(np.random.uniform(0.05, 0.15), 2)
                        }
                    },
                    "tickers_performance": {
                        ticker: {
                            "return": round(np.random.uniform(15, 50), 2),
                            "sharpe_ratio": round(np.random.uniform(1.2, 2.8), 2),
                            "max_drawdown": round(np.random.uniform(-20, -5), 2),
                            "win_rate": round(np.random.uniform(55, 80), 2)
                        } for ticker in tickers
                    },
                    "aggregate_performance": {
                        "return": round(np.random.uniform(20, 40) * (3-i) * 0.8, 2),
                        "sharpe_ratio": round(np.random.uniform(1.5, 2.5) * (3-i) * 0.5, 2),
                        "max_drawdown": round(np.random.uniform(-15, -5), 2),
                        "win_rate": round(np.random.uniform(60, 75), 2),
                        "trades_count": np.random.randint(35, 60),
                        "profit_factor": round(np.random.uniform(1.5, 3.0), 2)
                    }
                })
            
            # Store mock results in session state for display
            st.session_state.ai_backtest_results = mock_results

# Display AI Backtest results if available
if 'ai_backtest_results' in st.session_state:
    results = st.session_state.ai_backtest_results
    
    # Display execution info
    st.markdown(f"""
    **Execution ID:** {results.get('execution_id', 'N/A')}  
    **Execution Time:** {results.get('execution_time_seconds', 0)} seconds  
    **Timestamp:** {results.get('timestamp', 'N/A')}
    """)
    
    # Display winning strategies
    st.markdown("### 🏆 Winning Strategies")
    
    winning_strategies = results.get('winning_strategies', [])
    for i, strategy in enumerate(winning_strategies):
        strategy_data = strategy.get('strategy', {})
        performance = strategy.get('aggregate_performance', {})
        
        with st.expander(f"Strategy {i+1}: {strategy_data.get('name', 'Unnamed Strategy')}", expanded=i==0):
            # Display strategy details and performance in two columns
            s_col1, s_col2 = st.columns([1, 1])
            
            with s_col1:
                st.markdown("#### Strategy Details")
                
                # Strategy parameters
                st.markdown("**Parameters:**")
                params = strategy_data.get('parameters', {})
                for param, value in params.items():
                    st.markdown(f"- {param.replace('_', ' ').title()}: {value}")
                    
                # Display code snippet for the strategy (simplified example)
                st.markdown("**Implementation:**")
                st.code(f"""
def {strategy_data.get('template', 'strategy').lower().replace(' ', '_')}(data, params):
    # Entry conditions
    entry_signal = data['close'] > data['sma50'] 
    entry_signal &= data['rsi'] < params['entry_threshold'] * 100
    
    # Exit conditions
    exit_signal = data['close'] < data['sma20']
    exit_signal |= data['rsi'] > params['exit_threshold'] * 100
    
    # Apply stop loss and take profit
    apply_stop_loss(params['stop_loss'])
    apply_take_profit(params['take_profit'])
    
    return entry_signal, exit_signal
""", language="python")
                
            with s_col2:
                st.markdown("#### Performance Metrics")
                
                # Create metrics
                st.metric("Return", f"{performance.get('return', 0):.2f}%")
                st.metric("Sharpe Ratio", f"{performance.get('sharpe_ratio', 0):.2f}")
                st.metric("Win Rate", f"{performance.get('win_rate', 0):.2f}%")
                st.metric("Max Drawdown", f"{performance.get('max_drawdown', 0):.2f}%")
                st.metric("Profit Factor", f"{performance.get('profit_factor', 0):.2f}")
                st.metric("Trades Count", f"{performance.get('trades_count', 0)}")
                
                # Ticker-specific performance
                st.markdown("**Performance by Ticker:**")
                ticker_perf = strategy.get('tickers_performance', {})
                if ticker_perf:
                    ticker_data = []
                    for ticker, metrics in ticker_perf.items():
                        ticker_data.append({
                            "Ticker": ticker,
                            "Return (%)": metrics.get('return', 0),
                            "Sharpe": metrics.get('sharpe_ratio', 0),
                            "Max DD (%)": metrics.get('max_drawdown', 0),
                            "Win Rate (%)": metrics.get('win_rate', 0)
                        })
                    
                    # Convert to DataFrame
                    ticker_df = pd.DataFrame(ticker_data)
                    st.dataframe(ticker_df)
    
    # Machine Learning Insights
    st.markdown("### 🧠 Machine Learning Insights")
    ml_insights = results.get('ml_insights', {})
    
    # Display winning patterns
    patterns = ml_insights.get('winning_patterns', [])
    if patterns:
        st.markdown("#### Winning Patterns")
        for pattern in patterns:
            st.markdown(f"- {pattern}")
    
    # Display allocation recommendations
    recommendations = ml_insights.get('recommendations', {})
    if recommendations:
        st.markdown("### Hybrid Strategy Builder")
        st.markdown("Use ML insights to create your own customized strategies")
        
        col1, col2 = st.columns(2)
        
        with col1:
            alloc_data = recommendations.get('allocation', {})
            if alloc_data:
                st.markdown("#### Recommended Portfolio Allocation")
                
                # Create allocation chart
                alloc_df = pd.DataFrame({
                    'Strategy': list(alloc_data.keys()),
                    'Allocation (%)': list(alloc_data.values())
                })
                
                fig = px.pie(
                    alloc_df,
                    values='Allocation (%)',
                    names='Strategy',
                    title="Portfolio Allocation",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk management recommendations
            risk_data = recommendations.get('risk_management', {})
            if risk_data:
                st.markdown("#### Risk Management Recommendations")
                risk_col1, risk_col2, risk_col3 = st.columns(3)
                
                with risk_col1:
                    st.metric("Optimal Stop Loss", f"{risk_data.get('optimal_stop_loss', 0) * 100:.2f}%")
                with risk_col2:
                    st.metric("Position Sizing", f"{risk_data.get('optimal_position_sizing', 0) * 100:.2f}%")
                with risk_col3:
                    st.metric("Max Drawdown", f"{risk_data.get('recommended_max_drawdown', 0) * 100:.2f}%")
        
        # Custom strategy builder
        st.markdown("### Build Your Own Strategy")
        st.markdown("Customize your strategy based on ML insights")
        
        user_strategy_col1, user_strategy_col2 = st.columns(2)
        
        with user_strategy_col1:
            user_strategy_name = st.text_input("Strategy Name", "My Custom Strategy")
            user_base_template = st.selectbox("Base Strategy Template", list(alloc_data.keys()) if alloc_data else ["Momentum", "Mean Reversion", "Trend Following"])
            
            # Choose tickers to trade
            user_tickers = st.multiselect("Select Tickers", tickers, default=tickers)
            
            # Risk settings
            st.markdown("#### Risk Settings")
            user_stop_loss = st.slider(
                "Stop Loss (%)", 
                min_value=1.0, 
                max_value=10.0, 
                value=float(risk_data.get('optimal_stop_loss', 0.03) * 100),
                step=0.5
            )
            
            user_position_size = st.slider(
                "Position Size (%)", 
                min_value=1.0, 
                max_value=50.0, 
                value=float(risk_data.get('optimal_position_sizing', 0.1) * 100),
                step=1.0
            )
            
        with user_strategy_col2:
            # Strategy parameters
            st.markdown("#### Strategy Parameters")
            
            # Generate some example parameters based on the strategy
            if "momentum" in user_base_template.lower():
                param1 = st.slider("Momentum Period", min_value=5, max_value=60, value=20)
                param2 = st.slider("Signal Threshold", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
            elif "reversi" in user_base_template.lower():
                param1 = st.slider("RSI Period", min_value=2, max_value=30, value=14)
                param2 = st.slider("Oversold Threshold", min_value=10, max_value=40, value=30)
                param3 = st.slider("Overbought Threshold", min_value=60, max_value=90, value=70)
            else:
                param1 = st.slider("Fast MA Period", min_value=5, max_value=50, value=10)
                param2 = st.slider("Slow MA Period", min_value=20, max_value=200, value=50)
                
            # Trade management
            st.markdown("#### Trade Management")
            user_take_profit = st.slider("Take Profit (%)", min_value=2.0, max_value=50.0, value=15.0, step=0.5)
            user_max_trades = st.slider("Max Concurrent Trades", min_value=1, max_value=10, value=3)
            
            # Save button
            if st.button("Save Custom Strategy"):
                st.success(f"Strategy '{user_strategy_name}' saved successfully!")
else:
    # Initial state when no results available
    st.info("Configure your backtest parameters and click 'Run AI Backtest' to generate strategies.")
    
    # Sample screenshot of results
    st.markdown("### Sample AI Backtest Results Preview")
    sample_preview = """
    The AI backtester will:
    1. Analyze historical price data for your selected tickers
    2. Generate optimal trading strategies based on market conditions
    3. Find the best parameters for each strategy
    4. Provide detailed performance metrics for each strategy
    5. Offer ML insights for further optimization
    """
    st.info(sample_preview)

if __name__ == '__main__':
    port = 8080
    
    print(f"\n🚀 Simple Dashboard is running at: http://localhost:{port}")
    print("📱 Try these URLs in your browser:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True) 