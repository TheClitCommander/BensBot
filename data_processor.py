import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def load_strategy_allocation():
    """
    Load current strategy allocation data.
    In a real implementation, this would fetch from your database or API.
    """
    # Placeholder for demo - replace with actual data source
    strategies = {
        "Momentum": 30,
        "Mean Reversion": 25,
        "Breakout": 15,
        "Volatility": 10,
        "Trend Following": 15,
        "Pairs Trading": 5
    }
    
    return strategies

def load_historical_allocation(days=30):
    """
    Load historical strategy allocation data.
    """
    # Generate sample historical data for demo
    strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Create base allocations with some randomness
    base_values = {
        "Momentum": 30,
        "Mean Reversion": 25,
        "Breakout": 15,
        "Volatility": 10,
        "Trend Following": 15,
        "Pairs Trading": 5
    }
    
    data = {}
    for strategy in strategies:
        # Add some random variation to make it look realistic
        variation = np.random.normal(0, 2, size=len(dates))
        data[strategy] = np.clip(base_values[strategy] + np.cumsum(variation) * 0.1, 0, 50)
        
    df = pd.DataFrame(data, index=dates)
    
    # Normalize to ensure allocations sum to 100%
    df = df.div(df.sum(axis=1), axis=0) * 100
    
    return df

def load_market_context():
    """
    Load current market context data.
    """
    # Placeholder - replace with actual market data source
    market_context = {
        "regime": "Bullish",
        "vix": 18.76,
        "vix_change": -1.24,
        "sector_performance": {
            "Technology": 2.4,
            "Healthcare": 1.1, 
            "Financials": -0.5,
            "Energy": 3.2,
            "Materials": 0.3,
            "Utilities": -1.2
        },
        "sentiment": "Markets showing positive momentum with technology stocks leading. Potential volatility around upcoming Fed meeting. Energy sector seeing increased attention due to geopolitical developments."
    }
    
    return market_context

def load_trade_evaluations(start_date=None, end_date=None, strategies=None):
    """
    Load trade evaluations with GPT scores and reasoning.
    """
    # Sample data - replace with actual trade data
    trades_data = {
        "Symbol": ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "QQQ", "SPY", "META", "NFLX"],
        "Strategy": ["Momentum", "Breakout", "Volatility", "Mean Reversion", "Momentum", 
                    "Trend Following", "Pairs Trading", "Mean Reversion", "Breakout", "Volatility"],
        "Confidence": [87, 92, 65, 78, 94, 83, 71, 89, 76, 81],
        "Entry Date": [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)],
        "Status": ["Open", "Open", "Closed", "Closed", "Open", "Closed", "Open", "Closed", "Open", "Closed"],
        "P&L (%)": [2.3, 3.1, -1.2, 4.5, 6.2, 1.8, 0.9, 2.7, -0.8, 3.5],
        "AI Reasoning": [
            "Strong technical breakout with increasing volume and sector momentum.",
            "Clear resistance breakout with positive earnings surprise catalyst.",
            "Volatility play with upcoming product announcement, but mixed technical signals.",
            "Oversold conditions with positive RSI divergence and sector rotation.",
            "Strong momentum confirmed by multiple indicators and increasing institutional buying.",
            "Clear uptrend with higher lows and higher highs, supported by fundamental growth.",
            "Correlation breakdown between pairs creating arbitrage opportunity.",
            "Mean reversion trade on historically reliable support level with decreasing selling pressure.",
            "Breaking out of consolidation pattern but volume not confirming the move.",
            "Implied volatility skew indicating potential upside surprise."
        ]
    }
    
    df = pd.DataFrame(trades_data)
    
    # Apply filters if provided
    if start_date and end_date:
        df['Entry Date'] = pd.to_datetime(df['Entry Date'])
        df = df[(df['Entry Date'] >= start_date) & (df['Entry Date'] <= end_date)]
    
    if strategies:
        df = df[df['Strategy'].isin(strategies)]
    
    return df

def load_performance_metrics(timeframe="30d"):
    """
    Load performance metrics by strategy and market condition.
    """
    # Sample performance data - replace with actual metrics
    strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
    
    if timeframe == "7d":
        win_rates = [74, 65, 62, 59, 78, 68]
        profit_factors = [2.3, 1.7, 1.6, 1.5, 2.4, 1.8]
        drawdowns = [-2.1, -3.2, -4.5, -5.1, -1.8, -2.9]
    elif timeframe == "30d":
        win_rates = [72, 68, 59, 62, 74, 65]
        profit_factors = [2.1, 1.8, 1.5, 1.6, 2.2, 1.7]
        drawdowns = [-3.1, -3.8, -5.2, -4.8, -2.7, -3.5]
    else:  # 90d
        win_rates = [70, 67, 63, 60, 72, 64]
        profit_factors = [2.0, 1.7, 1.6, 1.5, 2.1, 1.6]
        drawdowns = [-4.5, -4.2, -6.1, -5.7, -3.8, -4.1]
    
    # Create DataFrame
    perf_df = pd.DataFrame({
        "Strategy": strategies,
        "Win Rate": win_rates,
        "Profit Factor": profit_factors,
        "Max Drawdown": drawdowns
    })
    
    # Add market condition performance
    market_condition_perf = {
        "Bullish": {
            "Momentum": 82,
            "Mean Reversion": 59,
            "Breakout": 74,
            "Volatility": 51,
            "Trend Following": 80,
            "Pairs Trading": 65
        },
        "Bearish": {
            "Momentum": 45,
            "Mean Reversion": 72,
            "Breakout": 38,
            "Volatility": 68,
            "Trend Following": 41,
            "Pairs Trading": 63
        },
        "Neutral": {
            "Momentum": 58,
            "Mean Reversion": 73,
            "Breakout": 51,
            "Volatility": 62,
            "Trend Following": 57,
            "Pairs Trading": 71
        },
        "Volatile": {
            "Momentum": 48,
            "Mean Reversion": 55,
            "Breakout": 61,
            "Volatility": 78,
            "Trend Following": 52,
            "Pairs Trading": 59
        }
    }
    
    return perf_df, market_condition_perf

def load_notifications(limit=10, filter_type=None):
    """
    Load recent notifications and alerts.
    """
    # Sample notifications - replace with actual notification system data
    notifications = [
        {"type": "trade", "time": "09:45 AM", "message": "New Trade: Bought AAPL at $182.45 (Momentum Strategy, 87% confidence)"},
        {"type": "alert", "time": "09:30 AM", "message": "Market Open: Bullish sentiment detected in Technology sector"},
        {"type": "system", "time": "09:15 AM", "message": "Daily allocation updated: +5% to Momentum, -5% from Pairs Trading"},
        {"type": "error", "time": "08:50 AM", "message": "API Error: Unable to fetch data for symbol XYZ"},
        {"type": "trade", "time": "Yesterday", "message": "Trade Closed: Sold MSFT at $415.30, +3.1% profit"},
        {"type": "alert", "time": "Yesterday", "message": "Volatility Alert: VIX jumped above 20, adjusting position sizes"},
        {"type": "system", "time": "Yesterday", "message": "Model Update: GPT trade evaluation model updated to version 2.3"},
        {"type": "trade", "time": "2 days ago", "message": "New Trade: Short QQQ at $438.92 (Mean Reversion Strategy, 89% confidence)"},
        {"type": "error", "time": "2 days ago", "message": "Connection Error: Broker API timeout, retrying operations"},
        {"type": "alert", "time": "3 days ago", "message": "Economic Alert: FOMC minutes released, increased volatility expected"}
    ]
    
    # Apply filter if provided
    if filter_type and filter_type != "All":
        notifications = [n for n in notifications if n["type"].capitalize() == filter_type]
    
    return notifications[:limit]

def apply_manual_override(strategy, action, allocation_data):
    """
    Apply manual override to strategy allocation.
    
    Args:
        strategy (str): Strategy name to override
        action (str): "pause", "boost", or "reallocation"
        allocation_data (dict): Current allocation data
        
    Returns:
        dict: Updated allocation data
    """
    # Create a copy to avoid modifying the original
    updated_allocation = allocation_data.copy()
    
    if action == "pause":
        # Move allocation to cash/other strategies
        paused_value = updated_allocation.pop(strategy)
        
        # Distribute the paused allocation proportionally to other strategies
        total_remaining = sum(updated_allocation.values())
        for strat in updated_allocation:
            updated_allocation[strat] += (updated_allocation[strat] / total_remaining) * paused_value
            
        # Add back the paused strategy with 0 allocation
        updated_allocation[strategy] = 0
        
    elif action == "boost":
        # Increase allocation by 10% (taking proportionally from others)
        boost_amount = sum(updated_allocation.values()) * 0.1
        current = updated_allocation[strategy]
        
        # Reduce other strategies proportionally
        for strat in updated_allocation:
            if strat != strategy:
                reduction = (updated_allocation[strat] / (sum(updated_allocation.values()) - current)) * boost_amount
                updated_allocation[strat] -= reduction
        
        # Boost the target strategy
        updated_allocation[strategy] += boost_amount
    
    # Normalize to ensure allocations sum to 100%
    total = sum(updated_allocation.values())
    for strat in updated_allocation:
        updated_allocation[strat] = (updated_allocation[strat] / total) * 100
        
    return updated_allocation 