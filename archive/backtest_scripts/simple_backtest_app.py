import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

# Add the project root to the path so we can import from trading package
sys.path.insert(0, os.path.abspath("."))

# Set up page config
st.set_page_config(
    page_title="Trading Backtest Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard title
st.title("Trading Backtest Dashboard")

# Function to load backtest results
def load_backtest_results(results_dir="results"):
    """Load all backtest results from the results directory"""
    results = []
    results_path = Path(results_dir)
    
    if not results_path.exists():
        return results
    
    for file in results_path.glob("*.json"):
        try:
            with open(file, "r") as f:
                result = json.load(f)
                # Add file information
                result["filename"] = file.name
                result["file_path"] = str(file)
                result["timestamp"] = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                results.append(result)
        except Exception as e:
            st.warning(f"Error loading {file}: {e}")
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return results

# Sidebar for controls
st.sidebar.header("Run Backtest")

# Get strategies from config.json
strategy_options = ["sma_crossover", "rsi", "macd", "bollinger_bands"]
    
with st.sidebar.form("backtest_form"):
    strategy = st.selectbox("Strategy", strategy_options)
    
    # Strategy-specific parameters
    st.subheader("Strategy Parameters")
    
    if strategy == "sma_crossover":
        short_window = st.slider("Short Window", min_value=5, max_value=50, value=20)
        long_window = st.slider("Long Window", min_value=20, max_value=200, value=50)
        strategy_params = {"short_window": short_window, "long_window": long_window}
    
    elif strategy == "rsi":
        rsi_period = st.slider("RSI Period", min_value=2, max_value=30, value=14)
        oversold = st.slider("Oversold Level", min_value=10, max_value=40, value=30)
        overbought = st.slider("Overbought Level", min_value=60, max_value=90, value=70)
        strategy_params = {"rsi_period": rsi_period, "oversold": oversold, "overbought": overbought}
    
    elif strategy == "macd":
        fast_period = st.slider("Fast Period", min_value=5, max_value=30, value=12)
        slow_period = st.slider("Slow Period", min_value=10, max_value=50, value=26)
        signal_period = st.slider("Signal Period", min_value=2, max_value=20, value=9)
        strategy_params = {"fast_period": fast_period, "slow_period": slow_period, "signal_period": signal_period}
    
    elif strategy == "bollinger_bands":
        window = st.slider("Window", min_value=5, max_value=50, value=20)
        num_std = st.slider("Standard Deviations", min_value=1.0, max_value=4.0, value=2.0, step=0.1)
        strategy_params = {"window": window, "num_std": num_std}
    
    # Common parameters
    st.subheader("Backtest Parameters")
    
    symbols = st.text_input("Symbols (comma-separated)", "AAPL,MSFT,GOOGL")
    symbols_list = [s.strip() for s in symbols.split(",")]
    
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.date_input("End Date", datetime.now())
    
    initial_capital = st.number_input("Initial Capital", min_value=1000, value=100000, step=1000)
    position_size = st.slider("Position Size (%)", min_value=1, max_value=100, value=20)
    position_size_decimal = position_size / 100.0
    
    commission = st.slider("Commission (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
    commission_decimal = commission / 100.0
    
    stop_loss = st.slider("Stop Loss (%)", min_value=0, max_value=20, value=5, step=1)
    stop_loss_decimal = stop_loss / 100.0 if stop_loss > 0 else None
    
    take_profit = st.slider("Take Profit (%)", min_value=0, max_value=50, value=10, step=1)
    take_profit_decimal = take_profit / 100.0 if take_profit > 0 else None
    
    use_mock_data = st.checkbox("Use Mock Data", value=True)
    
    # Submit button
    submitted = st.form_submit_button("Run Backtest")

# If form is submitted, run the backtest
if submitted:
    # Create a config file
    config = {
        "initial_capital": initial_capital,
        "position_size": position_size_decimal,
        "commission": commission_decimal,
        "stop_loss_pct": stop_loss_decimal,
        "take_profit_pct": take_profit_decimal,
        "symbols": symbols_list,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "strategy": strategy,
        "strategy_params": {
            strategy: strategy_params
        },
        "output_dir": "results"
    }
    
    # Save config to temporary file
    config_path = "temp_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    
    # Show spinner while running backtest
    with st.spinner("Running backtest..."):
        # Run backtest using subprocess
        cmd = ["python", "run_backtest.py", "--config", config_path]
        if use_mock_data:
            cmd.append("--mock")
        
        # Show the command being run
        st.code(" ".join(cmd))
        
        # Run the backtest
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                st.error("Backtest failed")
                st.error(result.stderr)
            else:
                st.success("Backtest completed successfully")
                st.text(result.stdout)
                
                # Refresh the page to show the new results
                st.rerun()
        except Exception as e:
            st.error(f"Error running backtest: {e}")

# Display backtest results
st.header("Backtest Results")

# Load results
results = load_backtest_results()

if not results:
    st.info("No backtest results found in the results directory.")
else:
    # Create a dataframe for display
    summary_data = []
    for result in results:
        summary_data.append({
            "Strategy": result.get("strategy", "Unknown"),
            "Symbols": ", ".join(result.get("symbols", [])),
            "Period": f"{result.get('start_date', '')} to {result.get('end_date', '')}",
            "Total Return": f"{result.get('total_return_pct', 0):.2f}%",
            "Sharpe Ratio": f"{result.get('sharpe_ratio', 0):.2f}",
            "Win Rate": f"{result.get('win_rate_pct', 0):.2f}%",
            "Drawdown": f"{result.get('max_drawdown_pct', 0):.2f}%",
            "Trades": result.get('total_trades', 0),
            "Timestamp": result.get("timestamp", ""),
            "Filename": result.get("filename", "")
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Show results as a table
    st.dataframe(summary_df[["Strategy", "Symbols", "Period", "Total Return", "Sharpe Ratio", "Win Rate", "Drawdown", "Trades", "Timestamp"]], use_container_width=True)
    
    # Select a result to display in detail
    st.subheader("Detailed Results")
    selected_result_index = st.selectbox(
        "Select a backtest to view:",
        range(len(results)),
        format_func=lambda i: f"{results[i].get('strategy', 'Unknown')} - {', '.join(results[i].get('symbols', [''])[:2])} - {results[i].get('total_return_pct', 0):.2f}% - {results[i].get('timestamp', '')}"
    )
    
    # Get the selected result
    selected_result = results[selected_result_index]
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Return", f"{selected_result.get('total_return_pct', 0):.2f}%")
    with col2:
        st.metric("Sharpe Ratio", f"{selected_result.get('sharpe_ratio', 0):.2f}")
    with col3:
        st.metric("Win Rate", f"{selected_result.get('win_rate_pct', 0):.2f}%")
    with col4:
        st.metric("Max Drawdown", f"{selected_result.get('max_drawdown_pct', 0):.2f}%")
    
    # More details in expandable sections
    with st.expander("Portfolio Performance"):
        # Create equity curve
        if "equity_curve" in selected_result:
            equity_data = selected_result["equity_curve"]
            dates = list(equity_data.keys())
            equity_values = list(equity_data.values())
            
            # Convert date strings to datetime if needed
            if isinstance(dates[0], str):
                dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates]
            
            # Create DataFrame
            equity_df = pd.DataFrame({
                "Date": dates,
                "Equity": equity_values
            })
            
            # Plot equity curve
            fig = px.line(
                equity_df, 
                x="Date", 
                y="Equity", 
                title="Equity Curve",
                labels={"Equity": "Portfolio Value ($)", "Date": ""}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No equity curve data available.")
    
    with st.expander("Trade Analysis"):
        if "trade_log" in selected_result:
            trade_log = selected_result["trade_log"]
            
            # Convert to DataFrame
            trades_df = pd.DataFrame(trade_log)
            
            # Show trades table
            st.dataframe(trades_df, use_container_width=True)
            
            # Plot PnL by trade if available
            if "pnl" in trades_df.columns:
                fig = px.bar(
                    trades_df, 
                    x=trades_df.index, 
                    y="pnl", 
                    title="PnL by Trade",
                    labels={"pnl": "Profit/Loss ($)", "index": "Trade #"}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trade data available.")
    
    with st.expander("Strategy Parameters"):
        # Display strategy parameters
        if "params" in selected_result:
            params = selected_result["params"]
            st.json(params)
        else:
            st.info("No strategy parameters available.")
    
    # Display raw JSON data if requested
    with st.expander("Raw JSON Data"):
        st.json(selected_result)
    
    # Option to delete result
    if st.button(f"Delete Result: {selected_result.get('filename', '')}"):
        try:
            os.remove(selected_result.get("file_path"))
            st.success(f"Deleted {selected_result.get('filename', '')}")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting file: {e}")

# Add custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True) 