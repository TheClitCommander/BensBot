#!/usr/bin/env python3
"""
Live Trading Dashboard

A Streamlit-based dashboard for monitoring trading system performance,
allocations, and trading decisions in real-time.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import time
import threading
import queue
from typing import Dict, List, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from collections import deque

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import local modules
from trading_bot.data.real_time_data_processor import RealTimeDataManager
from trading_bot.optimization.advanced_market_regime_detector import AdvancedMarketRegimeDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define color schemes for different market regimes
REGIME_COLORS = {
    'bull': '#4CAF50',     # Green
    'bear': '#F44336',     # Red
    'consolidation': '#2196F3',  # Blue
    'volatility': '#FF9800',  # Orange
    'recovery': '#9C27B0',  # Purple
    'unknown': '#9E9E9E'   # Grey
}

# Global state variables
class DashboardState:
    """Class to store global dashboard state that persists between Streamlit reruns"""
    def __init__(self):
        self.data_queue = queue.Queue()
        self.portfolio_history = deque(maxlen=1000)  # Store up to 1000 points
        self.trade_history = deque(maxlen=100)  # Store last 100 trades
        self.market_regime_history = deque(maxlen=100)  # Store last 100 regime changes
        self.last_update_time = datetime.now()
        self.streaming_active = False
        self.data_manager = None
        self.symbols = []
        
state = DashboardState()

def initialize_dashboard():
    """Configure the dashboard layout and settings"""
    st.set_page_config(
        page_title="Live Trading Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Set page header
    st.title("Live Trading Dashboard")
    st.markdown("Real-time monitoring of trading performance, allocations, and decisions")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Data source selection
        data_source = st.selectbox(
            "Data Source", 
            ["Alpaca", "Interactive Brokers", "Mock Data"],
            index=0
        )
        
        # Symbol configuration
        default_symbols = "SPY,QQQ,IWM,GLD"
        symbols_input = st.text_input("Symbols (comma-separated)", default_symbols)
        symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
        
        # Update frequency
        update_frequency = st.slider(
            "Update Frequency (seconds)", 
            min_value=1, 
            max_value=60, 
            value=5
        )
        
        # Time range for historical data
        time_range = st.selectbox(
            "Time Range",
            ["1 Hour", "4 Hours", "1 Day", "1 Week", "1 Month"],
            index=2
        )
        
        # Connect button
        connect_button = st.button("Connect" if not state.streaming_active else "Disconnect")
        
        if connect_button:
            if state.streaming_active:
                stop_data_streaming()
            else:
                start_data_streaming(symbols, data_source)
        
        # Display connection status
        connection_status = "Connected" if state.streaming_active else "Disconnected"
        status_color = "#4CAF50" if state.streaming_active else "#F44336"
        st.markdown(f"<h3 style='color: {status_color};'>Status: {connection_status}</h3>", unsafe_allow_html=True)
        
        # Display last update time
        st.write(f"Last Update: {state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # About section
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This dashboard connects to real-time market data and visualizes 
        trading performance, allocations, and decisions for your trading system.
        
        Use the controls above to configure the dashboard.
        """)
    
    return symbols, update_frequency, time_range, data_source

def start_data_streaming(symbols, data_source):
    """Start streaming market data"""
    if state.streaming_active:
        return
    
    state.symbols = symbols
    logger.info(f"Starting data streaming for symbols: {symbols}")
    
    try:
        # Configure data manager based on selected data source
        config = {
            'data_source': data_source.lower().replace(" ", "_"),
            'timeframes': ['1min', '5min', '15min', '1hour', '1day'],
            'use_market_regimes': True,
        }
        
        # Add credentials for the selected data source
        if data_source == "Alpaca":
            config['alpaca_config'] = {
                'api_key': os.environ.get('ALPACA_API_KEY', 'demo-api-key'),
                'api_secret': os.environ.get('ALPACA_API_SECRET', 'demo-api-secret')
            }
        elif data_source == "Interactive Brokers":
            config['ib_config'] = {
                'host': os.environ.get('IB_HOST', '127.0.0.1'),
                'port': int(os.environ.get('IB_PORT', '7497')),
                'client_id': int(os.environ.get('IB_CLIENT_ID', '1'))
            }
        
        # Initialize data manager
        if data_source == "Mock Data":
            # Create mock data instead of connecting to real data source
            create_mock_data_thread(symbols, state.data_queue)
        else:
            state.data_manager = RealTimeDataManager(symbols, config)
            
            # Register callbacks
            state.data_manager.on_bar_update = on_bar_update
            state.data_manager.on_regime_change = on_regime_change
            state.data_manager.on_strategy_update = on_strategy_update
            
            # Start the data manager
            state.data_manager.start()
        
        state.streaming_active = True
        state.last_update_time = datetime.now()
        
        # Initialize portfolio history with some starting data
        if len(state.portfolio_history) == 0:
            state.portfolio_history.append({
                'timestamp': datetime.now(),
                'value': 100000.0,
                'cash': 100000.0,
                'invested': 0.0
            })
        
        logger.info("Data streaming started successfully")
        
    except Exception as e:
        logger.error(f"Error starting data streaming: {str(e)}")
        st.error(f"Failed to start data streaming: {str(e)}")

def stop_data_streaming():
    """Stop streaming market data"""
    if not state.streaming_active:
        return
    
    logger.info("Stopping data streaming")
    
    try:
        if state.data_manager:
            state.data_manager.stop()
            state.data_manager = None
        
        state.streaming_active = False
        logger.info("Data streaming stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping data streaming: {str(e)}")
        st.error(f"Failed to stop data streaming: {str(e)}")

def on_bar_update(data):
    """Handle new bar data from the data manager"""
    # Add data to queue for processing
    state.data_queue.put({
        'type': 'bar_update',
        'data': data,
        'timestamp': datetime.now()
    })
    
    # Update portfolio value (in a real system, this would use actual portfolio data)
    if datetime.now().second % 5 == 0:  # Update every 5 seconds to reduce computation
        update_mock_portfolio()

def on_regime_change(regime):
    """Handle market regime changes from the data manager"""
    # Add data to queue for processing
    state.data_queue.put({
        'type': 'regime_change',
        'regime': regime,
        'timestamp': datetime.now()
    })
    
    # Add to regime history
    state.market_regime_history.append({
        'timestamp': datetime.now(),
        'regime': regime,
        'duration': 0  # To be calculated
    })
    
    logger.info(f"Market regime changed to: {regime}")

def on_strategy_update(weights):
    """Handle strategy weight updates from the data manager"""
    # Add data to queue for processing
    state.data_queue.put({
        'type': 'strategy_update',
        'weights': weights,
        'timestamp': datetime.now()
    })
    
    # Simulate a trade based on the new weights
    simulate_trade(weights)
    
    logger.info(f"Strategy weights updated: {weights}")

def update_mock_portfolio():
    """Update mock portfolio data for demonstration purposes"""
    if not state.portfolio_history:
        return
    
    last_value = state.portfolio_history[-1]['value']
    
    # Generate random portfolio change
    random_change = np.random.normal(0, 0.001)  # Small random fluctuation
    
    # Add trend based on market regime
    current_regime = "unknown"
    if state.market_regime_history:
        current_regime = state.market_regime_history[-1]['regime']
    
    regime_factor = {
        'bull': 0.0002,
        'bear': -0.0002,
        'consolidation': 0.0,
        'volatility': np.random.choice([-0.0004, 0.0004]),
        'recovery': 0.0001,
        'unknown': 0.0
    }.get(current_regime, 0.0)
    
    # Calculate new portfolio value
    new_value = last_value * (1 + random_change + regime_factor)
    
    # Calculate cash and invested amounts (mockup)
    total_invested_percent = min(0.8, len(state.trade_history) * 0.1)  # Max 80% invested
    invested = new_value * total_invested_percent
    cash = new_value - invested
    
    # Add to portfolio history
    state.portfolio_history.append({
        'timestamp': datetime.now(),
        'value': new_value,
        'cash': cash,
        'invested': invested
    })
    
    state.last_update_time = datetime.now()

def simulate_trade(weights):
    """Simulate a trade based on strategy weights for demonstration purposes"""
    # Calculate a random symbol from available symbols
    if not state.symbols:
        return
    
    symbol = np.random.choice(state.symbols)
    
    # Determine if it's a buy or sell
    action = np.random.choice(['BUY', 'SELL'])
    
    # Generate random quantity and price
    quantity = np.random.randint(10, 100)
    price = np.random.uniform(100, 500)
    
    # Calculate trade value
    value = quantity * price
    
    # Add to trade history
    state.trade_history.append({
        'timestamp': datetime.now(),
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'price': price,
        'value': value,
        'weights': weights
    })
    
    logger.info(f"Simulated trade: {action} {quantity} {symbol} @ {price}")

def create_mock_data_thread(symbols, data_queue):
    """Create a thread that generates mock data for demonstration purposes"""
    def mock_data_generator():
        """Generate mock market data"""
        regimes = ['bull', 'bear', 'consolidation', 'volatility', 'recovery']
        current_regime = np.random.choice(regimes)
        last_regime_change = datetime.now()
        
        # Add initial regime
        on_regime_change(current_regime)
        
        # Generate mock prices for each symbol
        prices = {symbol: np.random.uniform(100, 500) for symbol in symbols}
        
        while state.streaming_active:
            try:
                current_time = datetime.now()
                
                # Occasionally change market regime
                if (current_time - last_regime_change).total_seconds() > np.random.randint(60, 180):
                    current_regime = np.random.choice(regimes)
                    last_regime_change = current_time
                    on_regime_change(current_regime)
                
                # Update prices based on regime
                for symbol in symbols:
                    # Base random movement
                    random_change = np.random.normal(0, 0.002)
                    
                    # Add regime bias
                    regime_factor = {
                        'bull': 0.0005,
                        'bear': -0.0005,
                        'consolidation': 0.0,
                        'volatility': np.random.choice([-0.001, 0.001]),
                        'recovery': 0.0003
                    }[current_regime]
                    
                    # Update price
                    prices[symbol] *= (1 + random_change + regime_factor)
                    
                    # Create mock bar data
                    bar_data = {
                        'symbol': symbol,
                        'timestamp': current_time,
                        'price': prices[symbol],
                        'volume': np.random.randint(1000, 10000),
                        'type': 'bar'
                    }
                    
                    # Send to update handler
                    on_bar_update(bar_data)
                
                # Occasionally update strategy weights
                if np.random.random() < 0.05:  # 5% chance each iteration
                    strategy_names = ['MA_Trend', 'Mean_Reversion', 'Momentum', 'Volatility_Breakout']
                    weights = {name: np.random.random() for name in strategy_names}
                    # Normalize to sum to 1
                    total = sum(weights.values())
                    weights = {k: v/total for k, v in weights.items()}
                    
                    on_strategy_update(weights)
                
                # Simulate portfolio update
                update_mock_portfolio()
                
                time.sleep(1)  # Generate data every second
                
            except Exception as e:
                logger.error(f"Error in mock data generator: {str(e)}")
                time.sleep(1)
    
    # Start the mock data generator in a background thread
    thread = threading.Thread(target=mock_data_generator, daemon=True)
    thread.start()
    logger.info("Started mock data generator")

def display_portfolio_performance():
    """Display portfolio performance charts"""
    st.header("Portfolio Performance")
    
    if not state.portfolio_history:
        st.info("No portfolio data available. Connect to a data source to begin.")
        return
    
    # Convert portfolio history to DataFrame
    df = pd.DataFrame(list(state.portfolio_history))
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Portfolio Value", "Allocation", "Performance Metrics"])
    
    with tab1:
        # Portfolio value over time
        fig = px.line(
            df, 
            x='timestamp', 
            y='value',
            title='Portfolio Value Over Time',
            line_shape='spline'
        )
        
        # Add cash and invested areas
        if 'cash' in df.columns and 'invested' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['invested'],
                    fill='tozeroy',
                    name='Invested',
                    line=dict(color='rgba(0, 128, 0, 0.7)')
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cash'],
                    fill='tonexty',
                    name='Cash',
                    line=dict(color='rgba(0, 0, 255, 0.7)')
                )
            )
        
        # Format the chart
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Value ($)",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Current allocation pie chart
        if len(df) > 0 and 'cash' in df.columns and 'invested' in df.columns:
            last_row = df.iloc[-1]
            
            # Create a pie chart of current allocation
            labels = ['Cash', 'Invested']
            values = [last_row['cash'], last_row['invested']]
            
            fig = px.pie(
                values=values,
                names=labels,
                title='Current Portfolio Allocation',
                color_discrete_sequence=['rgba(0, 0, 255, 0.7)', 'rgba(0, 128, 0, 0.7)']
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # If we have trade data, show allocation by symbol
            if state.trade_history:
                # Calculate position by symbol
                positions = {}
                for trade in state.trade_history:
                    symbol = trade['symbol']
                    value = trade['value']
                    action = trade['action']
                    
                    if symbol not in positions:
                        positions[symbol] = 0
                    
                    if action == 'BUY':
                        positions[symbol] += value
                    else:  # SELL
                        positions[symbol] -= value
                
                # Filter out closed positions
                positions = {k: v for k, v in positions.items() if v > 0}
                
                if positions:
                    # Create a pie chart of symbol allocation
                    fig = px.pie(
                        values=list(positions.values()),
                        names=list(positions.keys()),
                        title='Allocation by Symbol'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Calculate performance metrics
        if len(df) > 1:
            # Calculate returns
            df['return'] = df['value'].pct_change()
            
            # Calculate cumulative return
            first_value = df['value'].iloc[0]
            last_value = df['value'].iloc[-1]
            total_return = (last_value / first_value) - 1
            
            # Calculate annualized metrics (assuming minutely data)
            minutes = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 60
            annualization_factor = np.sqrt(525600 / max(minutes, 1))  # 525600 minutes in a year
            
            volatility = df['return'].std() * annualization_factor
            sharpe = (df['return'].mean() / df['return'].std()) * annualization_factor if df['return'].std() > 0 else 0
            
            # Calculate drawdown
            df['cumulative_return'] = (1 + df['return']).cumprod()
            df['running_max'] = df['cumulative_return'].cummax()
            df['drawdown'] = df['cumulative_return'] / df['running_max'] - 1
            max_drawdown = df['drawdown'].min()
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Return", f"{total_return:.2%}")
                
            with col2:
                st.metric("Volatility (Ann.)", f"{volatility:.2%}")
                
            with col3:
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
                
            with col4:
                st.metric("Max Drawdown", f"{max_drawdown:.2%}")
            
            # Display drawdown chart
            fig = px.area(
                df, 
                x='timestamp', 
                y='drawdown',
                title='Portfolio Drawdown',
                color_discrete_sequence=['rgba(255, 0, 0, 0.5)']
            )
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Drawdown",
                hovermode="x unified",
                yaxis=dict(
                    tickformat=".1%",
                    range=[min(min(df['drawdown']*1.1, -0.01), -0.05), 0.01]
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display rolling performance metrics
            if len(df) > 20:
                # Calculate rolling metrics
                window = min(20, len(df) // 2)
                df['rolling_return'] = df['return'].rolling(window=window).mean() * window
                df['rolling_volatility'] = df['return'].rolling(window=window).std() * np.sqrt(window)
                df['rolling_sharpe'] = df['rolling_return'] / df['rolling_volatility']
                
                # Create subplots
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=["Rolling Return", "Rolling Sharpe Ratio"],
                    vertical_spacing=0.12
                )
                
                # Add rolling return
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['rolling_return'],
                        name='Rolling Return',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
                
                # Add rolling Sharpe
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['rolling_sharpe'],
                        name='Rolling Sharpe',
                        line=dict(color='green')
                    ),
                    row=2, col=1
                )
                
                # Format the chart
                fig.update_layout(
                    height=400,
                    hovermode="x unified",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_market_data():
    """Display real-time market data and price charts"""
    st.header("Market Data")
    
    if not state.streaming_active:
        st.info("Connect to a data source to view real-time market data.")
        return
    
    # Create tabs for different symbols
    if state.symbols:
        tabs = st.tabs(state.symbols)
        
        for i, symbol in enumerate(state.symbols):
            with tabs[i]:
                # Price chart for the symbol
                if state.data_manager:
                    # Get actual price data if available
                    df = state.data_manager.get_latest_bars(symbol, '1min', 100)
                    if not df.empty:
                        # Create candlestick chart
                        fig = go.Figure(data=[go.Candlestick(
                            x=df.index,
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close'],
                            name='Price'
                        )])
                        
                        # Add volume as a bar chart
                        if 'volume' in df.columns:
                            fig.add_trace(go.Bar(
                                x=df.index,
                                y=df['volume'],
                                name='Volume',
                                marker_color='rgba(0, 0, 255, 0.3)',
                                yaxis="y2"
                            ))
                            
                            fig.update_layout(
                                yaxis2=dict(
                                    title="Volume",
                                    overlaying="y",
                                    side="right",
                                    showgrid=False
                                )
                            )
                        
                        fig.update_layout(
                            title=f"{symbol} Price Chart",
                            xaxis_title="Time",
                            yaxis_title="Price",
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No price data available for {symbol}.")
                else:
                    # Show mock price chart for demonstration
                    if state.portfolio_history:
                        # Generate mock price data based on timestamp from portfolio data
                        timestamps = [entry['timestamp'] for entry in state.portfolio_history]
                        
                        # Generate random price with some correlation to portfolio
                        base_price = 100
                        price_data = []
                        
                        for i, ts in enumerate(timestamps):
                            if i == 0:
                                price = base_price
                            else:
                                # Get portfolio return
                                port_return = state.portfolio_history[i]['value'] / state.portfolio_history[i-1]['value'] - 1
                                
                                # Add correlated movement plus noise
                                correlation = 0.7 if symbol in ['SPY', 'QQQ'] else 0.3
                                price_return = correlation * port_return + (1-correlation) * np.random.normal(0, 0.001)
                                price = price_data[-1] * (1 + price_return)
                            
                            price_data.append(price)
                        
                        # Create DataFrame
                        df = pd.DataFrame({
                            'timestamp': timestamps,
                            'price': price_data
                        })
                        
                        # Create line chart
                        fig = px.line(
                            df, 
                            x='timestamp', 
                            y='price',
                            title=f"{symbol} Price (Mock Data)",
                            line_shape='spline'
                        )
                        
                        fig.update_layout(
                            xaxis_title="Time",
                            yaxis_title="Price",
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No price data available for {symbol}.")

def display_market_regime():
    """Display market regime information"""
    st.header("Market Regime Analysis")
    
    if not state.market_regime_history:
        st.info("No market regime data available. Connect to a data source to begin.")
        return
    
    # Get current regime
    current_regime = state.market_regime_history[-1]['regime']
    regime_color = REGIME_COLORS.get(current_regime, "#9E9E9E")
    
    # Display current regime
    st.markdown(f"<h2 style='color: {regime_color};'>Current Regime: {current_regime.title()}</h2>", unsafe_allow_html=True)
    
    # Create columns for regime metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Create regime history timeline
        if len(state.market_regime_history) > 1:
            # Convert to DataFrame
            df = pd.DataFrame(list(state.market_regime_history))
            
            # Calculate regime durations
            for i in range(len(df) - 1):
                df.at[i, 'duration'] = (df.at[i+1, 'timestamp'] - df.at[i, 'timestamp']).total_seconds() / 60  # minutes
            
            # For the last regime, duration is time since it started
            df.at[len(df)-1, 'duration'] = (datetime.now() - df.at[len(df)-1, 'timestamp']).total_seconds() / 60
            
            # Create timeline chart
            fig = px.timeline(
                df, 
                x_start="timestamp", 
                x_end=df['timestamp'] + pd.to_timedelta(df['duration'], unit='m'),
                y="regime",
                color="regime",
                color_discrete_map=REGIME_COLORS,
                title="Market Regime Timeline"
            )
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Regime",
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Regime duration metrics
            st.subheader("Regime Duration Statistics")
            
            # Calculate average duration by regime
            regime_stats = df.groupby('regime')['duration'].agg(['mean', 'count']).reset_index()
            regime_stats.columns = ['Regime', 'Avg. Duration (min)', 'Count']
            
            # Format for display
            regime_stats['Avg. Duration (min)'] = regime_stats['Avg. Duration (min)'].round(1)
            
            st.dataframe(regime_stats, use_container_width=True)
    
    with col2:
        # Create portfolio performance by regime
        if state.portfolio_history:
            # Convert to DataFrame
            portfolio_df = pd.DataFrame(list(state.portfolio_history))
            
            # Function to find regime for a given timestamp
            def find_regime(timestamp):
                for i in range(len(state.market_regime_history)-1, -1, -1):
                    if timestamp >= state.market_regime_history[i]['timestamp']:
                        return state.market_regime_history[i]['regime']
                return "unknown"
            
            # Add regime to portfolio data
            portfolio_df['regime'] = portfolio_df['timestamp'].apply(find_regime)
            
            # Calculate returns by regime
            portfolio_df['value_pct_change'] = portfolio_df['value'].pct_change()
            
            regime_returns = portfolio_df.groupby('regime')['value_pct_change'].agg(['mean', 'std', 'count']).reset_index()
            regime_returns.columns = ['Regime', 'Avg. Return', 'Volatility', 'Observations']
            
            # Calculate annualized metrics (assuming minutely data)
            regime_returns['Annualized Return'] = regime_returns['Avg. Return'] * 525600  # Minutes in a year
            regime_returns['Annualized Volatility'] = regime_returns['Volatility'] * np.sqrt(525600)
            regime_returns['Sharpe Ratio'] = regime_returns['Annualized Return'] / regime_returns['Annualized Volatility']
            
            # Format for display
            regime_returns['Avg. Return'] = regime_returns['Avg. Return'].apply(lambda x: f"{x:.4%}")
            regime_returns['Annualized Return'] = regime_returns['Annualized Return'].apply(lambda x: f"{x:.2%}")
            regime_returns['Annualized Volatility'] = regime_returns['Annualized Volatility'].apply(lambda x: f"{x:.2%}")
            regime_returns['Sharpe Ratio'] = regime_returns['Sharpe Ratio'].round(2)
            
            # Display stats
            st.subheader("Performance by Regime")
            st.dataframe(regime_returns, use_container_width=True)
            
            # Create comparison chart
            if len(regime_returns) > 1:
                # Filter out regimes with fewer than 5 observations
                chart_data = regime_returns[regime_returns['Observations'] > 5].copy()
                
                if not chart_data.empty:
                    # Convert percentage strings back to floats for the chart
                    chart_data['Annualized Return'] = chart_data['Annualized Return'].str.rstrip('%').astype(float) / 100
                    
                    # Create a bar chart
                    fig = px.bar(
                        chart_data,
                        x='Regime',
                        y='Annualized Return',
                        color='Regime',
                        color_discrete_map=REGIME_COLORS,
                        title="Annualized Return by Market Regime"
                    )
                    
                    fig.update_layout(
                        xaxis_title="Market Regime",
                        yaxis_title="Annualized Return",
                        yaxis=dict(tickformat=".0%")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

def display_trading_activity():
    """Display recent trades and strategy allocations"""
    st.header("Trading Activity")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Recent Trades", "Strategy Allocations"])
    
    with tab1:
        if not state.trade_history:
            st.info("No trade data available. Connect to a data source to begin.")
        else:
            # Convert trade history to DataFrame
            df = pd.DataFrame(list(state.trade_history))
            
            # Display recent trades
            st.subheader("Recent Trades")
            
            # Format the dataframe for display
            display_df = df[['timestamp', 'symbol', 'action', 'quantity', 'price', 'value']].copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df['price'] = display_df['price'].round(2)
            display_df['value'] = display_df['value'].round(2)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Create a chart of trade values over time
            fig = px.scatter(
                df,
                x='timestamp',
                y='value',
                size='value',
                color='action',
                hover_name='symbol',
                title="Trade Activity Over Time",
                color_discrete_map={'BUY': 'green', 'SELL': 'red'}
            )
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Trade Value ($)",
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a chart of trades by symbol
            trades_by_symbol = df.groupby('symbol')['value'].sum().reset_index()
            
            fig = px.bar(
                trades_by_symbol,
                x='symbol',
                y='value',
                title="Trading Volume by Symbol",
                color='symbol'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if not state.trade_history or 'weights' not in state.trade_history[-1]:
            st.info("No strategy allocation data available. Connect to a data source to begin.")
        else:
            # Get the latest strategy weights
            latest_weights = state.trade_history[-1]['weights']
            
            # Display current strategy allocations
            st.subheader("Current Strategy Allocations")
            
            # Create a pie chart
            fig = px.pie(
                values=list(latest_weights.values()),
                names=list(latest_weights.keys()),
                title="Strategy Weight Allocation"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display weights as a table
            weight_df = pd.DataFrame({
                'Strategy': list(latest_weights.keys()),
                'Weight': list(latest_weights.values())
            })
            
            weight_df['Weight'] = weight_df['Weight'].apply(lambda x: f"{x:.2%}")
            
            st.dataframe(weight_df, use_container_width=True)
            
            # If we have multiple weight updates, show the evolution
            if len(state.trade_history) > 1:
                # Extract weights history
                weights_history = []
                
                for trade in state.trade_history:
                    if 'weights' in trade:
                        weights_history.append({
                            'timestamp': trade['timestamp'],
                            **trade['weights']
                        })
                
                if weights_history:
                    weights_df = pd.DataFrame(weights_history)
                    
                    # Plot weights over time
                    fig = px.line(
                        weights_df,
                        x='timestamp',
                        y=weights_df.columns[1:],  # All columns except timestamp
                        title="Strategy Weights Over Time",
                        line_shape='spline'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Time",
                        yaxis_title="Weight",
                        hovermode="x unified",
                        yaxis=dict(tickformat=".0%")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

def create_dashboard():
    """Main function to create the dashboard"""
    # Initialize the dashboard
    symbols, update_frequency, time_range, data_source = initialize_dashboard()
    
    # Create a container for the dashboard
    dashboard_container = st.container()
    
    with dashboard_container:
        # Display performance metrics and charts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_portfolio_performance()
        
        with col2:
            # Display key metrics
            
            # Get the last portfolio value if available
            if state.portfolio_history:
                last_value = state.portfolio_history[-1]['value']
                first_value = state.portfolio_history[0]['value']
                daily_return = last_value / first_value - 1 if first_value > 0 else 0
                
                # Display current portfolio value
                st.metric(
                    "Portfolio Value", 
                    f"${last_value:,.2f}",
                    f"{daily_return:.2%}"
                )
            
            # Get the current market regime if available
            if state.market_regime_history:
                current_regime = state.market_regime_history[-1]['regime']
                st.metric("Current Market Regime", current_regime.title())
            
            # Get the last trade if available
            if state.trade_history:
                last_trade = state.trade_history[-1]
                st.metric(
                    "Last Trade", 
                    f"{last_trade['action']} {last_trade['quantity']} {last_trade['symbol']}",
                    f"${last_trade['value']:,.2f}"
                )
        
        # Display market data
        display_market_data()
        
        # Display market regime information
        display_market_regime()
        
        # Display trading activity
        display_trading_activity()
    
    # Schedule the next update
    if state.streaming_active:
        time.sleep(0.1)  # Small delay to prevent excessive updates
        st.experimental_rerun()

if __name__ == "__main__":
    create_dashboard() 