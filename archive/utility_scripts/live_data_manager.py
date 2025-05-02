import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import logging
import requests
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("live_data_manager")

class LiveDataManager:
    """Manages live data updates and auto-refresh functionality for the dashboard."""
    
    def __init__(self):
        """Initialize the LiveDataManager and setup session state variables."""
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
        """Check if it's time to auto-refresh data based on the refresh interval."""
        if st.session_state.auto_refresh:
            time_since_update = (datetime.now() - st.session_state.last_update_time).total_seconds()
            if time_since_update >= st.session_state.refresh_interval:
                self.fetch_latest_data()
                # Force a rerun of the app
                st.experimental_rerun()
    
    def fetch_latest_data(self, api_client=None, use_mock=False):
        """
        Fetch the latest market data and update session state.
        
        Args:
            api_client: The API client to use for fetching data (e.g., Finnhub)
            use_mock: Whether to use mock data instead of real API data
        
        Returns:
            bool: True if data was fetched successfully, False otherwise
        """
        if api_client is not None and not use_mock:
            try:
                # Update timestamp
                st.session_state.last_update_time = datetime.now()
                st.session_state.update_counter += 1
                
                # Get data for watched symbols
                symbols = st.session_state.watched_symbols
                
                # Fetch current prices
                for symbol in symbols:
                    try:
                        quote = api_client.get_quote(symbol)
                        if quote:
                            if symbol not in st.session_state.real_time_data:
                                st.session_state.real_time_data[symbol] = {
                                    'price_history': [],
                                    'volume_history': [],
                                    'timestamps': []
                                }
                            
                            # Add new data point
                            st.session_state.real_time_data[symbol]['price_history'].append(quote.get('c', 0))
                            st.session_state.real_time_data[symbol]['volume_history'].append(quote.get('v', 0))
                            st.session_state.real_time_data[symbol]['timestamps'].append(datetime.now())
                            
                            # Keep only last 100 data points
                            if len(st.session_state.real_time_data[symbol]['price_history']) > 100:
                                st.session_state.real_time_data[symbol]['price_history'] = st.session_state.real_time_data[symbol]['price_history'][-100:]
                                st.session_state.real_time_data[symbol]['volume_history'] = st.session_state.real_time_data[symbol]['volume_history'][-100:]
                                st.session_state.real_time_data[symbol]['timestamps'] = st.session_state.real_time_data[symbol]['timestamps'][-100:]
                            
                            # Add message to queue
                            st.session_state.message_queue.append({
                                'type': 'price_update',
                                'symbol': symbol,
                                'price': quote.get('c', 0),
                                'change': quote.get('dp', 0),
                                'timestamp': datetime.now(),
                                'source': 'Live API'
                            })
                        
                    except Exception as e:
                        logger.warning(f"Error fetching quote for {symbol}: {e}")
                
                # Limit message queue size
                if len(st.session_state.message_queue) > 50:
                    st.session_state.message_queue = st.session_state.message_queue[-50:]
                
                return True
            except Exception as e:
                logger.error(f"Error in fetch_latest_data: {e}")
                return False
        else:
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
        """Display the real-time message feed of price updates and other events."""
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
        """
        Create a section with live data controls, charts, and feed.
        
        Args:
            chart_library: The charting library to use (e.g., plotly)
        """
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
                    "Refresh interval", 
                    [10, 30, 60, 120, 300],  # seconds
                    index=[10, 30, 60, 120, 300].index(st.session_state.refresh_interval),
                    key="refresh_interval_select"
                )
                st.session_state.refresh_interval = st.session_state.refresh_interval_select
        
        with col3:
            # Manual refresh button and time display
            refresh_col, time_col = st.columns([1, 2])
            with refresh_col:
                if st.button("Refresh Now"):
                    self.fetch_latest_data(use_mock=True)
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
        """
        Display live price charts for watched symbols using the specified chart library.
        
        Args:
            chart_library: The charting library module (e.g., plotly.graph_objects)
        """
        try:
            import plotly.graph_objects as go
            
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
        except ImportError:
            st.warning("Plotly is not installed. Using basic charts instead.")
            # Fall back to simple line charts
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

# Example usage in a Streamlit app:
# 
# import streamlit as st
# from live_data_manager import LiveDataManager
# 
# # Initialize the LiveDataManager
# live_data_manager = LiveDataManager()
# 
# # Check for auto-refresh
# live_data_manager.check_auto_refresh()
# 
# # Create the main app layout
# st.title("Trading Dashboard")
# 
# # Create the live data section
# live_data_manager.create_live_data_section() 