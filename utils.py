import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests
from io import StringIO
import re

def determine_market_regime(vix, sector_performance, recent_returns):
    """
    Determine current market regime based on various indicators.
    
    Args:
        vix (float): Current VIX value
        sector_performance (dict): Performance by sector
        recent_returns (list): Recent market returns
        
    Returns:
        str: Market regime ("Bullish", "Bearish", "Neutral", "Volatile")
    """
    # Simple heuristic for demo purposes
    # In a real implementation, this would use more sophisticated methods
    
    if vix > 25:
        return "Volatile"
    
    # Calculate average sector performance
    avg_sector_perf = sum(sector_performance.values()) / len(sector_performance)
    
    # Calculate recent market momentum
    momentum = sum(recent_returns) / len(recent_returns)
    
    if avg_sector_perf > 1.0 and momentum > 0.2:
        return "Bullish"
    elif avg_sector_perf < -1.0 and momentum < -0.2:
        return "Bearish"
    else:
        return "Neutral"

def get_ai_market_sentiment(recent_news=None):
    """
    Generate AI market sentiment summary from recent news.
    In a real implementation, this would call your GPT system.
    
    Args:
        recent_news (list): List of recent news headlines or articles
        
    Returns:
        str: AI-generated sentiment summary
    """
    # Placeholder - in production, this would call your GPT API
    # You can replace this with your actual API call to get real sentiment analysis
    
    sentiments = [
        "Markets showing positive momentum with technology stocks leading. Potential volatility around upcoming Fed meeting.",
        "Mixed signals as inflation concerns weigh on sentiment despite strong earnings reports from key companies.",
        "Defensive positioning recommended as technical indicators suggest potential market pullback in coming sessions.",
        "Strong bullish bias across all major indices with breadth indicators confirming the uptrend.",
        "Cautious outlook warranted despite recent gains as economic data points to slowing growth."
    ]
    
    # Return random sentiment for demo purposes
    import random
    return random.choice(sentiments)

def format_trade_confidence(confidence_score):
    """
    Format and colorize trade confidence score.
    
    Args:
        confidence_score (int): AI confidence score (0-100)
        
    Returns:
        tuple: (formatted_score, color)
    """
    if confidence_score >= 85:
        return f"{confidence_score}% ✓", "high"
    elif confidence_score >= 70:
        return f"{confidence_score}% ○", "medium"
    else:
        return f"{confidence_score}% ⚠", "low"

def telegram_connector(api_token=None, chat_id=None, action="get_messages", message=None, limit=10):
    """
    Connect to Telegram API to get or send messages.
    
    Args:
        api_token (str): Telegram Bot API token
        chat_id (str): Chat ID to interact with
        action (str): "get_messages" or "send_message"
        message (str): Message to send (if action is "send_message")
        limit (int): Number of messages to retrieve
        
    Returns:
        list or bool: List of messages or success status
    """
    # This is a placeholder function
    # In a real implementation, this would use the Telegram Bot API
    
    if action == "send_message" and message:
        # Simulate sending a message
        print(f"[Telegram] Sending message: {message}")
        return True
    
    elif action == "get_messages":
        # Simulate getting messages
        dummy_messages = [
            {"message_id": 1001, "date": datetime.now() - timedelta(minutes=15), "text": "New Trade: Bought AAPL at $182.45 (Momentum Strategy, 87% confidence)"},
            {"message_id": 1002, "date": datetime.now() - timedelta(minutes=30), "text": "Market Open: Bullish sentiment detected in Technology sector"},
            {"message_id": 1003, "date": datetime.now() - timedelta(hours=1), "text": "Daily allocation updated: +5% to Momentum, -5% from Pairs Trading"},
            {"message_id": 1004, "date": datetime.now() - timedelta(hours=2), "text": "API Error: Unable to fetch data for symbol XYZ"},
            {"message_id": 1005, "date": datetime.now() - timedelta(days=1), "text": "Trade Closed: Sold MSFT at $415.30, +3.1% profit"}
        ]
        
        return dummy_messages[:limit]
    
    return None

def calculate_drawdown(returns):
    """
    Calculate maximum drawdown from a series of returns.
    
    Args:
        returns (list or pandas.Series): Percentage returns
        
    Returns:
        float: Maximum drawdown as a percentage
    """
    # Convert to numpy array if needed
    if isinstance(returns, pd.Series):
        returns = returns.values
    
    # Calculate cumulative returns
    cum_returns = (1 + np.array(returns) / 100).cumprod()
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(cum_returns)
    
    # Calculate drawdown
    drawdown = (cum_returns / running_max - 1) * 100
    
    # Return the minimum (maximum drawdown)
    return np.min(drawdown)

def calculate_profit_factor(profits, losses):
    """
    Calculate profit factor (sum of profits / sum of losses).
    
    Args:
        profits (list): List of profit values (positive)
        losses (list): List of loss values (negative)
        
    Returns:
        float: Profit factor
    """
    total_profits = sum(profits)
    total_losses = abs(sum(losses))
    
    if total_losses == 0:
        return float('inf')  # No losses
    
    return total_profits / total_losses

def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """
    Calculate Sharpe ratio from a series of returns.
    
    Args:
        returns (list or pandas.Series): Percentage returns
        risk_free_rate (float): Annual risk-free rate (default: 3%)
        
    Returns:
        float: Sharpe ratio
    """
    # Convert to numpy array if needed
    if isinstance(returns, pd.Series):
        returns = returns.values
    
    # Convert percentage returns to decimal
    returns_decimal = np.array(returns) / 100
    
    # Calculate average return and standard deviation
    avg_return = np.mean(returns_decimal)
    std_return = np.std(returns_decimal)
    
    # Calculate daily risk-free rate
    daily_rfr = risk_free_rate / 252
    
    # Calculate Sharpe ratio
    if std_return == 0:
        return 0
    
    # Annualize the Sharpe ratio (multiply by sqrt(252) for daily returns)
    sharpe = (avg_return - daily_rfr) / std_return * np.sqrt(252)
    
    return sharpe

def format_performance_metric(metric, value, type="numeric"):
    """
    Format performance metrics for display.
    
    Args:
        metric (str): Metric name
        value (float): Metric value
        type (str): Type of formatting ("numeric", "percentage", "currency")
        
    Returns:
        str: Formatted metric
    """
    if type == "percentage":
        formatted = f"{value:.2f}%"
    elif type == "currency":
        formatted = f"${value:.2f}"
    else:
        formatted = f"{value:.2f}"
    
    return formatted

def connect_to_broker_api(broker="demo", action="get_positions", symbol=None, quantity=None, order_type=None):
    """
    Connect to broker API for trading operations.
    
    Args:
        broker (str): Broker name or "demo" for simulation
        action (str): Action to perform ("get_positions", "place_order", etc.)
        symbol (str): Trading symbol (for orders)
        quantity (int): Order quantity
        order_type (str): Order type ("market", "limit", etc.)
        
    Returns:
        dict or list: API response
    """
    # This is a placeholder function for demo purposes
    # In a real implementation, this would connect to your broker's API
    
    if broker == "demo":
        if action == "get_positions":
            # Return dummy positions
            return [
                {"symbol": "AAPL", "quantity": 100, "average_price": 180.45, "current_price": 182.45, "pnl": 200.00},
                {"symbol": "MSFT", "quantity": 50, "average_price": 410.30, "current_price": 415.30, "pnl": 250.00},
                {"symbol": "TSLA", "quantity": -20, "average_price": 190.50, "current_price": 188.20, "pnl": 46.00}
            ]
        
        elif action == "place_order":
            # Simulate placing an order
            if symbol and quantity:
                return {
                    "order_id": "demo-" + str(int(datetime.now().timestamp())),
                    "symbol": symbol,
                    "quantity": quantity,
                    "order_type": order_type or "market",
                    "status": "submitted",
                    "timestamp": datetime.now().isoformat()
                }
    
    return None

def export_dashboard_data(format="csv"):
    """
    Export dashboard data for external use.
    
    Args:
        format (str): Export format ("csv", "json", "excel")
        
    Returns:
        str or bytes: Exported data
    """
    # Placeholder function
    # In a real implementation, this would gather all relevant data
    # and export it in the requested format
    
    # Sample data structure to export
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "strategies": {
            "Momentum": {
                "allocation": 30,
                "win_rate": 72,
                "profit_factor": 2.1,
                "drawdown": -3.1
            },
            "Mean Reversion": {
                "allocation": 25,
                "win_rate": 68,
                "profit_factor": 1.8,
                "drawdown": -3.8
            },
            # ... other strategies
        },
        "market_context": {
            "regime": "Bullish",
            "vix": 18.76,
            "sector_performance": {
                "Technology": 2.4,
                "Healthcare": 1.1,
                # ... other sectors
            }
        },
        "recent_trades": [
            {"symbol": "AAPL", "strategy": "Momentum", "confidence": 87, "pnl": 2.3},
            {"symbol": "MSFT", "strategy": "Breakout", "confidence": 92, "pnl": 3.1},
            # ... other trades
        ]
    }
    
    if format == "json":
        return json.dumps(export_data, indent=2)
    
    elif format == "csv":
        # Convert to CSV (simplified version)
        output = StringIO()
        
        # Write strategies section
        output.write("Strategies\n")
        output.write("Strategy,Allocation,Win Rate,Profit Factor,Drawdown\n")
        for strategy, data in export_data["strategies"].items():
            output.write(f"{strategy},{data['allocation']},{data['win_rate']},{data['profit_factor']},{data['drawdown']}\n")
        
        output.write("\nMarket Context\n")
        output.write(f"Regime,{export_data['market_context']['regime']}\n")
        output.write(f"VIX,{export_data['market_context']['vix']}\n")
        
        output.write("\nSector Performance\n")
        for sector, perf in export_data["market_context"]["sector_performance"].items():
            output.write(f"{sector},{perf}\n")
        
        output.write("\nRecent Trades\n")
        output.write("Symbol,Strategy,Confidence,P&L\n")
        for trade in export_data["recent_trades"]:
            output.write(f"{trade['symbol']},{trade['strategy']},{trade['confidence']},{trade['pnl']}\n")
        
        return output.getvalue()
    
    return None 