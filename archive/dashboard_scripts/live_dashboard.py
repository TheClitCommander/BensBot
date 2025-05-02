import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import logging
import plotly.express as px
import plotly.graph_objects as go
import time
import threading
import requests
import json

# Set page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Live Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("live_dashboard")

# Import LiveDataManager
try:
    from live_data_manager import LiveDataManager
    LIVE_DATA_MANAGER_AVAILABLE = True
except ImportError:
    LIVE_DATA_MANAGER_AVAILABLE = False
    logger.warning("LiveDataManager not available. Creating a local implementation.")
    
    # Create a simplified version if import fails
    class LiveDataManager:
        def __init__(self):
            # Initialize session state for real-time data
            if 'last_update_time' not in st.session_state:
                st.session_state.last_update_time = datetime.now()
            if 'auto_refresh' not in st.session_state:
                st.session_state.auto_refresh = True
            if 'refresh_interval' not in st.session_state:
                st.session_state.refresh_interval = 60  # default to 60 seconds
            if 'message_queue' not in st.session_state:
                st.session_state.message_queue = []
            if 'real_time_data' not in st.session_state:
                st.session_state.real_time_data = {}
            if 'update_counter' not in st.session_state:
                st.session_state.update_counter = 0
            if 'watched_symbols' not in st.session_state:
                st.session_state.watched_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY", "QQQ"]
        
        def check_auto_refresh(self):
            if st.session_state.auto_refresh:
                time_since_update = (datetime.now() - st.session_state.last_update_time).total_seconds()
                if time_since_update >= st.session_state.refresh_interval:
                    self.fetch_latest_data()
                    st.experimental_rerun()
        
        def fetch_latest_data(self, **kwargs):
            # Use mock data
            symbols = st.session_state.watched_symbols
            current_time = datetime.now()
            
            for symbol in symbols:
                if symbol not in st.session_state.real_time_data:
                    # Initialize with random starting price
                    base_price = np.random.uniform(100, 500)
                    st.session_state.real_time_data[symbol] = {
                        'price_history': [base_price],
                        'volume_history': [np.random.randint(10000, 1000000)],
                        'timestamps': [current_time]
                    }
                else:
                    # Add small random change to previous price
                    last_price = st.session_state.real_time_data[symbol]['price_history'][-1]
                    change_pct = np.random.uniform(-0.002, 0.002)  # Small percent change
                    new_price = last_price * (1 + change_pct)
                    
                    # Add new data point
                    st.session_state.real_time_data[symbol]['price_history'].append(new_price)
                    st.session_state.real_time_data[symbol]['volume_history'].append(np.random.randint(10000, 1000000))
                    st.session_state.real_time_data[symbol]['timestamps'].append(current_time)
                    
                    # Keep only last 100 data points
                    if len(st.session_state.real_time_data[symbol]['price_history']) > 100:
                        st.session_state.real_time_data[symbol]['price_history'] = st.session_state.real_time_data[symbol]['price_history'][-100:]
                        st.session_state.real_time_data[symbol]['volume_history'] = st.session_state.real_time_data[symbol]['volume_history'][-100:]
                        st.session_state.real_time_data[symbol]['timestamps'] = st.session_state.real_time_data[symbol]['timestamps'][-100:]
                    
                    # Add message to queue
                    st.session_state.message_queue.append({
                        'type': 'price_update',
                        'symbol': symbol,
                        'price': new_price,
                        'change': change_pct * 100,
                        'timestamp': current_time,
                        'source': 'Mock Data'
                    })
            
            # Limit message queue size
            if len(st.session_state.message_queue) > 50:
                st.session_state.message_queue = st.session_state.message_queue[-50:]
            
            # Update timestamp
            st.session_state.last_update_time = current_time
            st.session_state.update_counter += 1
            
            return True
        
        def display_real_time_feed(self):
            if not st.session_state.message_queue:
                st.info("No real-time updates available yet. Data will appear here when available.")
                return
            
            messages = st.session_state.message_queue.copy()
            messages.reverse()  # Show newest first
            
            for i, msg in enumerate(messages[:10]):  # Show only the latest 10 messages
                if msg['type'] == 'price_update':
                    change_color = "green" if msg['change'] >= 0 else "red"
                    change_sign = "+" if msg['change'] >= 0 else ""
                    message = f"""
                    <div style="padding: 8px 12px; margin-bottom: 8px; border-left: 3px solid {change_color}; background-color: rgba(0,0,0,0.03); border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold;">{msg['symbol']}</span>
                            <span style="color: {change_color};">${msg['price']:.2f} ({change_sign}{msg['change']:.2f}%)</span>
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            {msg['timestamp'].strftime("%H:%M:%S")} • {msg['source']}
                        </div>
                    </div>
                    """
                    st.markdown(message, unsafe_allow_html=True)
        
        def create_live_data_section(self, chart_library=None):
            st.markdown('<div style="font-size: 1.5rem; font-weight: 600; color: #0D47A1; margin-top: 1rem;">📊 Live Market Data</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Symbol management
                symbols_input = st.text_input(
                    "Watched Symbols (comma-separated)", 
                    ", ".join(st.session_state.watched_symbols)
                )
                if symbols_input:
                    new_symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
                    if new_symbols != st.session_state.watched_symbols:
                        st.session_state.watched_symbols = new_symbols
                        # Clear existing data for symbols that are no longer watched
                        current_symbols = list(st.session_state.real_time_data.keys())
                        for symbol in current_symbols:
                            if symbol not in new_symbols:
                                if symbol in st.session_state.real_time_data:
                                    del st.session_state.real_time_data[symbol]
            
            with col2:
                # Auto-refresh controls
                st.checkbox("Auto-refresh data", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
                st.session_state.auto_refresh = st.session_state.auto_refresh_toggle
                
                # Only show interval selector if auto-refresh is enabled
                if st.session_state.auto_refresh:
                    st.selectbox(
                        "Refresh interval (seconds)", 
                        [10, 30, 60, 120, 300],
                        index=[10, 30, 60, 120, 300].index(st.session_state.refresh_interval),
                        key="refresh_interval_select"
                    )
                    st.session_state.refresh_interval = st.session_state.refresh_interval_select
            
            with col3:
                # Manual refresh button and time display
                refresh_col, time_col = st.columns([1, 2])
                with refresh_col:
                    if st.button("Refresh Now"):
                        self.fetch_latest_data()
                        st.experimental_rerun()
                
                with time_col:
                    st.markdown(f"""
                    <div style="padding: 21px 0;">
                        Last updated: <span style="color: #1E88E5;">{st.session_state.last_update_time.strftime('%H:%M:%S')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display real-time updates feed
            st.markdown("### Real-time Updates")
            self.display_real_time_feed()
            
            # Display live price charts if we have any data
            if st.session_state.real_time_data:
                st.markdown("### Price Charts")
                if chart_library:
                    self.display_live_charts(chart_library)
                else:
                    # Simple line charts using Streamlit's built-in chart
                    for symbol in st.session_state.watched_symbols:
                        if symbol in st.session_state.real_time_data and len(st.session_state.real_time_data[symbol]['price_history']) > 1:
                            data = st.session_state.real_time_data[symbol]
                            
                            # Create DataFrame for plotting
                            df = pd.DataFrame({
                                'timestamp': data['timestamps'],
                                'price': data['price_history']
                            })
                            
                            # Calculate price change
                            first_price = df['price'].iloc[0]
                            last_price = df['price'].iloc[-1]
                            price_change = last_price - first_price
                            price_change_pct = (price_change / first_price) * 100
                            
                            # Create chart title with latest price and change
                            chart_title = f"{symbol}: ${last_price:.2f} "
                            if price_change >= 0:
                                chart_title += f"(+{price_change:.2f}, +{price_change_pct:.2f}%)"
                            else:
                                chart_title += f"({price_change:.2f}, {price_change_pct:.2f}%)"
                            
                            st.subheader(chart_title)
                            st.line_chart(df.set_index('timestamp')['price'])
        
        def display_live_charts(self, chart_library):
            try:
                for symbol in st.session_state.watched_symbols:
                    if symbol in st.session_state.real_time_data and len(st.session_state.real_time_data[symbol]['price_history']) > 1:
                        data = st.session_state.real_time_data[symbol]
                        
                        # Create DataFrame for plotting
                        df = pd.DataFrame({
                            'timestamp': data['timestamps'],
                            'price': data['price_history'],
                            'volume': data['volume_history']
                        })
                        
                        # Calculate price change
                        first_price = df['price'].iloc[0]
                        last_price = df['price'].iloc[-1]
                        price_change = last_price - first_price
                        price_change_pct = (price_change / first_price) * 100
                        
                        # Set chart color based on price change
                        chart_color = "green" if price_change >= 0 else "red"
                        
                        # Create chart title with latest price and change
                        chart_title = f"{symbol}: ${last_price:.2f} "
                        if price_change >= 0:
                            chart_title += f"<span style='color:green;'>+{price_change:.2f} (+{price_change_pct:.2f}%)</span>"
                        else:
                            chart_title += f"<span style='color:red;'>{price_change:.2f} ({price_change_pct:.2f}%)</span>"
                        
                        st.markdown(f"### {chart_title}", unsafe_allow_html=True)
                        
                        # Create the line chart
                        fig = go.Figure()
                        
                        # Add price line
                        fig.add_trace(go.Scatter(
                            x=df['timestamp'],
                            y=df['price'],
                            mode='lines',
                            name='Price',
                            line=dict(color=chart_color, width=2)
                        ))
                        
                        # Configure layout
                        fig.update_layout(
                            height=300,
                            margin=dict(l=0, r=0, t=30, b=0),
                            xaxis=dict(
                                title=None,
                                showgrid=True,
                                gridcolor='rgba(230, 230, 230, 0.8)'
                            ),
                            yaxis=dict(
                                title=None,
                                showgrid=True,
                                gridcolor='rgba(230, 230, 230, 0.8)',
                                tickformat='$,.2f'
                            ),
                            plot_bgcolor='rgba(255, 255, 255, 0.9)',
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Error displaying charts: {e}")
                # Fall back to simple line charts
                for symbol in st.session_state.watched_symbols:
                    if symbol in st.session_state.real_time_data and len(st.session_state.real_time_data[symbol]['price_history']) > 1:
                        data = st.session_state.real_time_data[symbol]
                        
                        # Create DataFrame for plotting
                        df = pd.DataFrame({
                            'timestamp': data['timestamps'],
                            'price': data['price_history']
                        })
                        
                        st.subheader(f"{symbol}")
                        st.line_chart(df.set_index('timestamp')['price'])

# Initialize the LiveDataManager
live_data_manager = LiveDataManager()
# Check for auto-refresh
live_data_manager.check_auto_refresh()

# Add custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0D47A1;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .highlight {
        color: #2E7D32;
        font-weight: 600;
    }
    .warning {
        color: #C62828;
        font-weight: 600;
    }
    .neutral {
        color: #F57C00;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Dashboard Header
st.markdown('<div class="main-header">Live Trading Dashboard</div>', unsafe_allow_html=True)
st.markdown("Real-time market data and trading signals")

# Create top row with summary metrics
metric_cols = st.columns(4)

# Sample metrics data
current_portfolio_value = 127845.67
daily_pnl = 1243.82
daily_pnl_pct = 0.98
open_positions = 8
win_rate = 67.8
avg_profit_factor = 1.87
max_drawdown = -4.2
sharpe_ratio = 1.93

with metric_cols[0]:
    st.metric(label="Portfolio Value", value=f"${current_portfolio_value:,.2f}", delta=f"${daily_pnl:,.2f} ({daily_pnl_pct}%)")
with metric_cols[1]:
    st.metric(label="Open Positions", value=f"{open_positions}")
with metric_cols[2]:
    st.metric(label="Win Rate", value=f"{win_rate:.1f}%")
with metric_cols[3]:
    st.metric(label="Sharpe Ratio", value=f"{sharpe_ratio:.2f}")

# Create live data section
live_data_manager.create_live_data_section(chart_library=go)

# Portfolio Distribution
st.markdown('<div class="sub-header">Portfolio Allocation</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    # Asset allocation by strategy
    st.subheader("Allocation by Strategy")
    strategies = ["Momentum", "Mean Reversion", "Trend Following", "Volatility Breakout"]
    allocations = [40, 25, 20, 15]
    
    fig = px.pie(
        values=allocations,
        names=strategies,
        title="Current Capital Allocation",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Recent trades
    st.subheader("Recent Trades")
    trades_data = {
        "Symbol": ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA"],
        "Strategy": ["Momentum", "Trend Following", "Volatility Breakout", "Mean Reversion", "Momentum"],
        "Entry Time": ["10:30", "09:45", "11:15", "14:20", "15:01"],
        "Status": ["Open", "Open", "Closed", "Closed", "Open"],
        "P&L (%)": [1.2, 0.8, -0.5, 2.1, 1.5]
    }
    
    trades_df = pd.DataFrame(trades_data)
    
    # Function to color P&L
    def pnl_color(val):
        if val > 0:
            return 'color: green; font-weight: bold'
        elif val < 0:
            return 'color: red; font-weight: bold'
        return ''
    
    # Display with styling
    st.dataframe(
        trades_df.style.applymap(pnl_color, subset=['P&L (%)']),
        use_container_width=True
    )

# Market Data
st.markdown('<div class="sub-header">Market Conditions</div>', unsafe_allow_html=True)

# Market conditions visualization
market_conditions = {
    "Condition": ["Bullish Trend", "Sideways/Range", "Bearish Trend", "High Volatility"],
    "Probability": [0.65, 0.20, 0.05, 0.10]
}

df_market = pd.DataFrame(market_conditions)

fig = px.bar(
    df_market,
    y="Condition",
    x="Probability",
    orientation='h',
    color="Probability",
    color_continuous_scale=["#C62828", "#FFAB91", "#A5D6A7", "#2E7D32"],
    title="Current Market Regime Probability"
)

fig.update_layout(
    xaxis_title="Probability",
    yaxis_title="",
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Dashboard refreshes automatically every 60 seconds. Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# If running as a script
if __name__ == "__main__":
    pass 