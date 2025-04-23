import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.title("Controls")
    
    time_range = st.selectbox(
        "Time Period", 
        ["1 Day", "7 Days", "1 Month", "3 Months", "6 Months", "1 Year"]
    )
    
    # Define all strategies
    all_strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
    selected_strategies = all_strategies # Default to all
    
    # Define default risk level
    risk_level = "Moderate"
    current_risk_multiplier = 1.0
    
    # Add API usage monitor to the sidebar
    with st.expander("📊 API Usage Monitor"):
        st.info("No API calls recorded today.")

# Main dashboard content
st.markdown('<div style="font-size: 2.5rem; font-weight: 700; color: #1E88E5; margin-bottom: 1rem;">Trading Strategy Dashboard</div>', unsafe_allow_html=True)

# Create top row with summary metrics
metric_cols = st.columns(4)

# Metrics data
avg_win_rate = 67.8
avg_profit_factor = 1.87
avg_drawdown = -4.2
avg_sharpe = 1.93

with metric_cols[0]:
    st.metric(label="Total Win Rate", value=f"{avg_win_rate:.1f}%")
with metric_cols[1]:
    st.metric(label="Profit Factor", value=f"{avg_profit_factor:.2f}")
with metric_cols[2]:
    st.metric(label="Max Drawdown", value=f"{avg_drawdown:.1f}%", delta_color="inverse")
with metric_cols[3]:
    st.metric(label="Sharpe Ratio", value=f"{avg_sharpe:.2f}")

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Backtesting", "Paper Trading", "Strategy", "News"])

with tab1:
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600; color: #0D47A1; margin-top: 1rem;">Portfolio Performance</div>', unsafe_allow_html=True)
    
    # Generate portfolio data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_value = 100000
    portfolio_values = [base_value]
    
    for i in range(1, len(dates)):
        change = np.random.normal(0.0003, 0.001)
        portfolio_values.append(portfolio_values[-1] * (1 + change))
    
    benchmark_values = [base_value * (1 + 0.0001 * i + np.random.normal(0, 0.0005)) for i in range(len(dates))]
    
    portfolio_df = pd.DataFrame({
            'Date': dates,
        'Portfolio Value': portfolio_values,
        'Benchmark': benchmark_values
    })
    
    # Display chart
    fig_portfolio = px.line(
        portfolio_df,
        x='Date',
        y=['Portfolio Value', 'Benchmark'],
        title="Portfolio vs Benchmark Performance",
        color_discrete_sequence=['#1E88E5', '#FFA000']
    )
    st.plotly_chart(fig_portfolio, use_container_width=True)
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div style="font-size: 1.5rem; font-weight: 600; color: #0D47A1;">Allocation Breakdown</div>', unsafe_allow_html=True)
    
        # Allocation data
        strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
        allocations = [30, 25, 15, 10, 15, 5]
        
        # Create pie chart
        fig_allocation = px.pie(
            values=allocations,
            names=strategies,
            title="Current Capital Allocation",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_allocation, use_container_width=True)
    
    with col2:
        st.markdown('<div style="font-size: 1.5rem; font-weight: 600; color: #0D47A1;">Recent Trades</div>', unsafe_allow_html=True)
        
        # Sample trade data
        trades_data = {
            "Symbol": ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA"],
            "Strategy": ["Momentum", "Breakout", "Volatility", "Mean Reversion", "Momentum"],
            "Entry Date": ["2023-04-10", "2023-04-09", "2023-04-08", "2023-04-07", "2023-04-06"],
            "Status": ["Open", "Open", "Closed", "Closed", "Open"],
            "P&L (%)": [2.3, 3.1, -1.2, 4.5, 6.2]
        }
        
        trades_df = pd.DataFrame(trades_data)
        st.dataframe(trades_df, use_container_width=True)
    
    # News section
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600; color: #0D47A1;">Financial News</div>', unsafe_allow_html=True)
    
    # Search input
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("Search any ticker or company name:", placeholder="AAPL, MSFT, Apple, Microsoft, etc.")
    with search_col2:
        search_button = st.button("Search News", use_container_width=True)
    
    # News results
    news_data = [
            {
            "title": "Apple Reports Strong Quarterly Earnings",
            "source": "Financial Times",
            "timestamp": "2023-04-16",
            "summary": "Apple Inc. reported quarterly earnings that exceeded analyst estimates, with record revenue from services.",
            "sentiment": "Positive"
            },
            {
            "title": "Tesla Faces Production Challenges in New Markets",
            "source": "Bloomberg",
            "timestamp": "2023-04-15",
            "summary": "Tesla is experiencing challenges ramping up production in its new European and Asian facilities amid supply chain disruptions.",
            "sentiment": "Negative"
            },
            {
            "title": "Microsoft Cloud Business Shows Steady Growth",
            "source": "Reuters",
            "timestamp": "2023-04-14",
            "summary": "Microsoft's Azure cloud services continue to see steady growth in the enterprise segment, maintaining market position.",
            "sentiment": "Neutral"
        }
        ]

    # Create columns for news by sentiment
    sentiment_cols = st.columns(3)
    
    with sentiment_cols[0]:
        st.markdown("#### 📈 Positive News")
        for news in [n for n in news_data if n["sentiment"] == "Positive"]:
            st.markdown(f"""
            <div style="border-left: 5px solid green; padding: 10px; margin-bottom: 10px;">
                <strong>{news['title']}</strong><br>
                {news['summary']}<br>
                <small>{news['source']} • {news['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with sentiment_cols[1]:
        st.markdown("#### 📊 Neutral News")
        for news in [n for n in news_data if n["sentiment"] == "Neutral"]:
            st.markdown(f"""
            <div style="border-left: 5px solid orange; padding: 10px; margin-bottom: 10px;">
                <strong>{news['title']}</strong><br>
                {news['summary']}<br>
                <small>{news['source']} • {news['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
            
    with sentiment_cols[2]:
        st.markdown("#### 📉 Negative News")
        for news in [n for n in news_data if n["sentiment"] == "Negative"]:
            st.markdown(f"""
            <div style="border-left: 5px solid red; padding: 10px; margin-bottom: 10px;">
                <strong>{news['title']}</strong><br>
                {news['summary']}<br>
                <small>{news['source']} • {news['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div style="font-size: 2rem; font-weight: 700;">Backtesting</div>', unsafe_allow_html=True)
    
    # Configuration section
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Backtest Configuration</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        strategy_select = st.selectbox(
            "Select Strategy",
            ["Momentum", "Mean Reversion", "Trend Following", "Volatility Breakout", "Custom Strategy"]
        )
        
        symbol = st.text_input("Symbol", "AAPL")
        timeframe = st.selectbox("Timeframe", ["1D", "4H", "1H", "30min", "15min", "5min"])
        
    with col2:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
        end_date = st.date_input("End Date", datetime.now())
        initial_capital = st.number_input("Initial Capital", min_value=1000, value=100000, step=1000)
    
    # Strategy parameters
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Strategy Parameters</div>', unsafe_allow_html=True)
    
    params_col1, params_col2, params_col3 = st.columns(3)
    
    with params_col1:
        param1 = st.slider("Fast MA Period", min_value=5, max_value=50, value=20)
    with params_col2:
        param2 = st.slider("Slow MA Period", min_value=20, max_value=200, value=50)
    with params_col3:
        param3 = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        run_backtest = st.button("Run Backtest", type="primary")
    
    # Sample backtest results
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Backtest Results</div>', unsafe_allow_html=True)
    
    # Performance metrics
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric(label="Total Return", value="32.8%", delta="22.3% vs Benchmark")
    with metric_cols[1]:
        st.metric(label="Sharpe Ratio", value="1.87", delta="0.42 vs Benchmark")
    with metric_cols[2]:
        st.metric(label="Max Drawdown", value="-14.2%", delta="-3.5% vs Benchmark", delta_color="inverse")
    with metric_cols[3]:
        st.metric(label="Win Rate", value="62.3%", delta="")

    # Equity curve
    st.markdown("### Equity Curve")
    
    # Generate equity data
    dates = pd.date_range(start=start_date, end=end_date)
    np.random.seed(42)
    equity = [initial_capital]
    
    for i in range(1, len(dates)):
        daily_return = np.random.normal(0.0005, 0.01)
        equity.append(equity[-1] * (1 + daily_return))
    
    equity_df = pd.DataFrame({
        'Date': dates,
        'Strategy': equity,
        'Benchmark': [initial_capital * (1 + 0.0003 * i + np.random.normal(0, 0.005)) for i in range(len(dates))]
    })
    
    fig = px.line(equity_df, x='Date', y=['Strategy', 'Benchmark'], 
                  title='Strategy vs Benchmark Performance',
                  color_discrete_sequence=['#1E88E5', '#FFA000'])
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown('<div style="font-size: 2rem; font-weight: 700;">Paper Trading</div>', unsafe_allow_html=True)
    
    # Account overview
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Account Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Account Value", value="$102,458.32", delta="$2,458.32")
    with col2:
        st.metric(label="Cash Balance", value="$54,789.12", delta="")
    with col3:
        st.metric(label="Equity", value="$47,669.20", delta="$2,458.32")
    with col4:
        st.metric(label="Day P&L", value="$658.92", delta="0.64%")
    
    # Open positions
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Open Positions</div>', unsafe_allow_html=True)
    
    positions_data = {
        "Symbol": ["AAPL", "MSFT", "TSLA"],
        "Quantity": [50, 25, 10],
        "Entry Price": ["$175.23", "$395.40", "$164.87"],
        "Current Price": ["$182.45", "$415.28", "$172.56"],
        "Market Value": ["$9,122.50", "$10,382.00", "$1,725.60"],
        "Unrealized P&L": ["$361.00", "$497.00", "$76.90"],
        "P&L (%)": ["4.11%", "5.03%", "4.66%"]
    }
    
    positions_df = pd.DataFrame(positions_data)
    st.dataframe(positions_df, use_container_width=True)
    
    # Order management
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Order Management</div>', unsafe_allow_html=True)
    
    order_col1, order_col2 = st.columns(2)
    
    with order_col1:
        st.markdown("### Place New Order")
        
        # Order form
        symbol = st.text_input("Symbol", "", key="order_symbol")
        order_type = st.selectbox("Order Type", ["Market", "Limit", "Stop", "Stop Limit"])
        direction = st.radio("Direction", ["Buy", "Sell"], horizontal=True)
    
        # Base quantity input
        quantity = st.number_input("Quantity", min_value=1, value=100)
        
        if order_type != "Market":
            price = st.number_input("Price", min_value=0.01, value=100.00, step=0.01)
        
        place_order = st.button("Place Order", type="primary")
        
        if place_order and symbol:
            if order_type == "Market":
                order_details = f"{direction} {quantity} {symbol} at Market"
            else:
                order_details = f"{direction} {quantity} {symbol} at ${price:.2f}"
                
            st.success(f"Order placed: {order_details}")
    
    with order_col2:
        st.markdown("### Open Orders")
        
        # Sample open orders
        orders_data = {
            "Order ID": ["ORD-001", "ORD-002"],
            "Symbol": ["AMZN", "GOOGL"],
            "Type": ["Limit Buy", "Stop Sell"],
            "Quantity": [10, 15],
            "Price": ["$175.50", "$140.25"],
            "Status": ["Open", "Open"],
            "Created": ["Today 09:45 AM", "Today 10:12 AM"]
        }
        
        orders_df = pd.DataFrame(orders_data)
        st.dataframe(orders_df, use_container_width=True)
        
        cancel_order = st.button("Cancel Selected Order")
        if cancel_order:
            st.info("Order cancelled successfully")

with tab4:
    st.markdown('<div style="font-size: 2rem; font-weight: 700;">Strategy Management</div>', unsafe_allow_html=True)
    
    # Strategy allocation
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Strategy Allocation</div>', unsafe_allow_html=True)
    
    # Sample strategies
    strategies = {
        "Momentum": {"allocation": 30, "status": "Active", "performance": 18.5},
        "Mean Reversion": {"allocation": 25, "status": "Active", "performance": 12.3},
        "Trend Following": {"allocation": 15, "status": "Active", "performance": 22.1},
        "Volatility Breakout": {"allocation": 10, "status": "Paused", "performance": -5.2},
        "Pairs Trading": {"allocation": 5, "status": "Active", "performance": 8.7},
        "Machine Learning": {"allocation": 15, "status": "Active", "performance": 15.9}
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get allocation data
        alloc_data = pd.DataFrame({
            "Strategy": list(strategies.keys()),
            "Allocation": [s["allocation"] for s in strategies.values()]
        })
        
        fig = px.pie(
            alloc_data,
            values="Allocation",
            names="Strategy",
            title="Current Strategy Allocation (%)",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig)
    
    with col2:
        st.markdown("### Strategy Controls")
        
        # Strategy selector
        strategy_to_modify = st.selectbox("Select Strategy", list(strategies.keys()))
        new_allocation = st.slider("Allocation (%)", 0, 100, strategies[strategy_to_modify]["allocation"])
        
        status = st.radio("Status", ["Active", "Paused"], index=0 if strategies[strategy_to_modify]["status"] == "Active" else 1)
        
        update_strategy = st.button("Update Strategy")
        if update_strategy:
            st.success(f"Strategy {strategy_to_modify} updated: {new_allocation}% allocation, {status} status")

with tab5:
    st.markdown('<div style="font-size: 2rem; font-weight: 700;">News & Analysis</div>', unsafe_allow_html=True)
    
    # Market news
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Market News</div>', unsafe_allow_html=True)
    
    # Extended news data
    extended_news = [
        {
            "title": "Fed Signals Potential Rate Cut in Next Meeting",
            "source": "Financial Times",
            "timestamp": "2023-04-16",
            "summary": "Federal Reserve officials have indicated they may consider cutting interest rates at their next meeting amid signs of cooling inflation and slowing economic growth.",
            "sentiment": "Positive"
        },
        {
            "title": "S&P 500 Reaches New All-Time High",
            "source": "Wall Street Journal",
            "timestamp": "2023-04-15", 
            "summary": "The S&P 500 index reached a new record high today, driven by strong performance in technology and healthcare sectors.",
            "sentiment": "Positive"
        },
        {
            "title": "Oil Prices Stabilize After Recent Volatility",
            "source": "Reuters",
            "timestamp": "2023-04-15",
            "summary": "Crude oil prices have stabilized following a period of heightened volatility, as supply concerns ease and demand forecasts remain steady.",
            "sentiment": "Neutral"
        },
        {
            "title": "Global Supply Chain Disruptions Ease",
            "source": "Bloomberg",
            "timestamp": "2023-04-14",
            "summary": "Major shipping routes are reporting improved throughput as global supply chain bottlenecks continue to ease, potentially reducing inflationary pressures.",
            "sentiment": "Positive"
        },
        {
            "title": "Tech Giant Announces Layoffs Amid Restructuring",
            "source": "CNBC",
            "timestamp": "2023-04-14",
            "summary": "A major technology company announced it will cut 8% of its workforce as part of a strategic restructuring aimed at focusing on AI and cloud services.",
            "sentiment": "Negative"
        }
    ]
    
    # Display news in a more organized way
    for news in extended_news:
        # Set color based on sentiment
        color = "green" if news["sentiment"] == "Positive" else "red" if news["sentiment"] == "Negative" else "orange"
        
        st.markdown(f"""
        <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 15px; background-color: #f8f9fa;">
            <h3 style="margin-top: 0;">{news['title']}</h3>
            <p>{news['summary']}</p>
            <p style="color: #666; margin-bottom: 0;"><strong>{news['source']}</strong> • {news['timestamp']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Market predictions
    st.markdown('<div style="font-size: 1.5rem; font-weight: 600;">Market Predictions</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Market Regime Forecast")
        
        # Market regime predictions
        regime_data = {
            "Regime": ["Bullish Trend", "Sideways/Consolidation", "Bearish Trend", "High Volatility"],
            "Probability": [0.65, 0.20, 0.05, 0.10]
        }
        
        fig = px.bar(
            regime_data,
            y="Regime",
            x="Probability",
            orientation='h',
            title="Market Regime Probability (7-Day Forecast)",
            color="Probability",
            color_continuous_scale=["#C62828", "#FFAB91", "#A5D6A7", "#2E7D32"],
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Symbol Price Predictions")
        
        # Price predictions
        prediction_data = [
            {
                "Symbol": "AAPL",
                "Current Price": "$182.45",
                "7-Day Prediction": "$187.92",
                "Change (%)": 3.0,
                "Confidence": 76.5
            },
            {
                "Symbol": "MSFT",
                "Current Price": "$415.28",
                "7-Day Prediction": "$428.74",
                "Change (%)": 3.2,
                "Confidence": 82.1
            },
            {
                "Symbol": "TSLA",
                "Current Price": "$172.56",
                "7-Day Prediction": "$168.34",
                "Change (%)": -2.4,
                "Confidence": 67.3
            },
            {
                "Symbol": "AMZN",
                "Current Price": "$178.35",
                "7-Day Prediction": "$183.70",
                "Change (%)": 3.0,
                "Confidence": 71.8
            }
        ]
        
        predictions_df = pd.DataFrame(prediction_data)
        st.dataframe(predictions_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Dashboard last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")) 