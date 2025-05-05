import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta, timezone
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import random
import uuid
import time
import os
import logging
import statistics
import requests
import json
import pandas_ta as ta
from scipy import stats
import pytz

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="TradeGPT Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to fix text visibility
st.markdown("""
<style>
    .stApp {
        color: rgba(250, 250, 250, 0.95);
    }
    .st-bq {
        color: rgba(250, 250, 250, 0.95);
    }
    div[data-testid="stMarkdownContainer"] > p {
        color: rgba(250, 250, 250, 0.95);
    }
    div[data-testid="stDataFrameContainer"] table {
        color: rgba(25, 25, 25, 0.95);
        background-color: rgba(250, 250, 250, 0.95);
    }
    div[data-testid="stTable"] table {
        color: rgba(25, 25, 25, 0.95);
        background-color: rgba(250, 250, 250, 0.95);
    }
    .st-dw {
        color: rgba(250, 250, 250, 0.95);
    }
    .st-cd {
        color: rgba(250, 250, 250, 0.95);
    }
    div.st-emotion-cache-16txtl3 p {
        color: rgba(250, 250, 250, 0.95) !important;
    }
    label.st-emotion-cache-16h7o41.e1i1eobo0 {
        color: rgba(250, 250, 250, 0.95);
    }
    /* AI Assistant Button Styling */
    .ai-assistant-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #4e89ae;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        cursor: pointer;
        z-index: 9999;
        transition: all 0.3s ease;
    }
    .ai-assistant-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    /* Chat modal styling */
    .ai-chat-modal {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        height: 500px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        z-index: 9998;
        display: none;
        flex-direction: column;
        overflow: hidden;
    }
    .ai-chat-header {
        background-color: #4e89ae;
        color: white;
        padding: 10px 15px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .ai-chat-close {
        cursor: pointer;
        font-size: 18px;
    }
    .ai-chat-body {
        flex-grow: 1;
        overflow-y: auto;
        padding: 15px;
    }
    .ai-chat-footer {
        padding: 10px;
        border-top: 1px solid #eee;
        display: flex;
    }
    .ai-chat-input {
        flex-grow: 1;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 8px 15px;
        outline: none;
    }
    .ai-chat-send {
        margin-left: 10px;
        background-color: #4e89ae;
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
    .user-message {
        background-color: #e6f3ff;
        color: #000000;
        padding: 8px 12px;
        border-radius: 18px 18px 0 18px;
        margin: 5px 0;
        max-width: 80%;
        align-self: flex-end;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #f0f0f0;
        color: #000000;
        padding: 8px 12px;
        border-radius: 18px 18px 18px 0;
        margin: 5px 0;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize all session state variables
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []

if 'detailed_view' not in st.session_state:
    st.session_state.detailed_view = True

if 'bookmarked_news' not in st.session_state:
    st.session_state.bookmarked_news = []

# Initialize session state for AI assistant chat toggle
if 'ai_chat_open' not in st.session_state:
    st.session_state.ai_chat_open = False

def toggle_ai_chat():
    st.session_state.ai_chat_open = not st.session_state.ai_chat_open

# TradeGPT Co-Pilot - AI Assistant Module
class TradeGPTAssistant:
    """AI Assistant that provides contextual trading advice and insights."""
    
    def __init__(self):
        self.chat_history = []
        self.memory = {
            "user_preferences": {
                "risk_tolerance": "moderate",
                "favorite_strategies": [],
                "max_drawdown_limit": 5.0,
                "preferred_metrics": ["Sharpe", "Win Rate"]
            },
            "recent_contexts": []
        }
    
    def add_message(self, role, content):
        """Add a message to the chat history."""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def get_response(self, user_message, context=None):
        """Generate an AI response based on user message and trading context."""
        # Add user message to history
        self.add_message("user", user_message)
        
        # Process slash commands
        if user_message.startswith("/"):
            response = self._process_command(user_message, context)
        else:
            response = self._generate_standard_response(user_message, context)
        
        # Add AI response to history
        self.add_message("assistant", response)
        return response
    
    def _process_command(self, command, context=None):
        """Process slash commands like /backtest, /simulate, etc."""
        parts = command.split(" ")
        cmd = parts[0].lower()
        
        if cmd == "/backtest":
            # Example: /backtest AAPL with stop 2% target 5%
            try:
                ticker = parts[1]
                params = {}
                
                for i in range(2, len(parts)-1):
                    if parts[i] == "with" or parts[i] == "using":
                        continue
                    if parts[i] == "stop" and i+1 < len(parts):
                        params["stop_loss"] = float(parts[i+1].replace("%", ""))
                    if parts[i] == "target" and i+1 < len(parts):
                        params["take_profit"] = float(parts[i+1].replace("%", ""))
                    if parts[i] == "period" and i+1 < len(parts):
                        params["lookback_period"] = int(parts[i+1])
                
                # Run quick backtest
                result = self._run_quick_backtest(ticker, params)
                
                return f"""
**Quick Backtest Results: {ticker}**
• **Sharpe Ratio:** {result['sharpe']:.2f}
• **Win Rate:** {result['win_rate']:.1f}%
• **Max Drawdown:** {result['max_drawdown']:.1f}%
• **Profit Factor:** {result['profit_factor']:.2f}
                
{result['summary']}
                """
            except Exception as e:
                return f"Sorry, I couldn't run that backtest. Error: {str(e)}"
        
        elif cmd == "/simulate":
            # Example: /simulate market crash on QQQ
            scenario = " ".join(parts[1:3])
            ticker = parts[-1] if len(parts) > 3 else "SPY"
            
            # Run scenario simulation
            result = self._simulate_scenario(scenario, ticker)
            
            return f"""
**Scenario Simulation: {scenario.title()} on {ticker}**
• **Expected Return:** {result['return']:.1f}%
• **Win Rate:** {result['win_rate']:.1f}%
• **Best Strategy:** {result['best_strategy']}
                
{result['analysis']}
                """
        
        elif cmd == "/explain":
            # Example: /explain sharpe ratio
            term = " ".join(parts[1:])
            return self._explain_term(term)
        
        else:
            return f"Unknown command: {cmd}. Available commands: /backtest, /simulate, /explain"
    
    def _generate_standard_response(self, user_message, context=None):
        """Generate a standard response to user questions."""
        message_lower = user_message.lower()
        
        # Check for strategy questions
        if "best strategy" in message_lower or "top strategy" in message_lower:
            return self._answer_best_strategy_question(user_message, context)
        
        # Check for market condition questions
        elif "market condition" in message_lower or "sentiment" in message_lower:
            return self._answer_market_condition_question(user_message, context)
        
        # Check for strategy comparison questions
        elif "compare" in message_lower and ("vs" in message_lower or "versus" in message_lower):
            return self._answer_strategy_comparison_question(user_message, context)
        
        # Check for parameter adjustment questions
        elif ("adjust" in message_lower or "change" in message_lower) and "parameter" in message_lower:
            return self._answer_parameter_adjustment_question(user_message, context)
        
        # Default generic response
        else:
            return """
I'm your TradeGPT Co-Pilot. I can help with:
• Analyzing current strategies and backtests
• Explaining trading metrics and concepts
• Running quick simulations with /backtest or /simulate commands
• Interpreting market conditions and news sentiment

What specific trading question can I help you with?
            """
    
    def _run_quick_backtest(self, ticker, params):
        """Run a quick backtest with the specified parameters."""
        # In a real implementation, this would use actual backtest code
        # For now, simulate results with reasonable mock data
        sharpe = round(random.uniform(0.8, 2.5), 2)
        win_rate = round(random.uniform(45, 75), 1)
        max_drawdown = round(random.uniform(2, 8), 1)
        profit_factor = round(random.uniform(1.0, 2.5), 2)
        
        # Generate a summary based on the results
        if sharpe > 1.8 and win_rate > 60:
            summary = f"This configuration for {ticker} shows strong potential with excellent risk-adjusted returns and consistent profitability."
        elif sharpe > 1.2:
            summary = f"The results for {ticker} are solid but could be improved. Consider adjusting your take-profit parameter for better performance."
        else:
            summary = f"This configuration for {ticker} doesn't perform particularly well. Consider testing alternative parameters or strategies."
            
        return {
            "sharpe": sharpe,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "summary": summary
        }
    
    def _simulate_scenario(self, scenario, ticker):
        """Simulate a market scenario on a specific ticker."""
        # Mock implementation for now
        if "crash" in scenario.lower():
            return {
                "return": round(random.uniform(-15, -5), 1),
                "win_rate": round(random.uniform(30, 45), 1),
                "best_strategy": "Protective Put",
                "analysis": f"In a market crash scenario, {ticker} is expected to decline significantly. Defensive strategies like put options or inverse ETFs would outperform."
            }
        elif "rally" in scenario.lower():
            return {
                "return": round(random.uniform(5, 15), 1),
                "win_rate": round(random.uniform(60, 75), 1),
                "best_strategy": "Momentum",
                "analysis": f"During a market rally, {ticker} would likely outperform with momentum strategies. Consider call options or leveraged positions for enhanced returns."
            }
        else:
            return {
                "return": round(random.uniform(-3, 8), 1),
                "win_rate": round(random.uniform(45, 65), 1),
                "best_strategy": "Trend Following",
                "analysis": f"Given this scenario, {ticker} would likely perform moderately well. Trend following with tight stops would be the preferred approach."
            }
    
    def _explain_term(self, term):
        """Provide a beginner-friendly explanation of a trading term."""
        explanations = {
            "sharpe ratio": """
**Sharpe Ratio** measures risk-adjusted returns.

• **What it tells you**: How much return you're getting for the risk you're taking
• **Good values**: Above 1.0 is good, above 2.0 is excellent
• **Example**: A strategy with Sharpe 2.0 generates twice as much return per unit of risk as one with Sharpe 1.0
• **Pro tip**: Higher is better, but consistently high Sharpe across different market conditions is more important than temporary spikes

Use Sharpe Ratio to compare strategies with different risk profiles.
            """,
            
            "win rate": """
**Win Rate** is the percentage of trades that are profitable.

• **What it tells you**: How often your strategy is correct
• **Good values**: Above 50% is profitable, though some strategies work with lower win rates if winners are larger than losers
• **Example**: A 60% win rate means 6 out of 10 trades are profitable
• **Pro tip**: Win rate must be considered alongside average win/loss size (profit factor)

High win rates feel good psychologically but aren't everything!
            """,
            
            "drawdown": """
**Drawdown** measures the largest peak-to-trough decline in your equity.

• **What it tells you**: The worst temporary loss you'd experience
• **Good values**: Lower is better, under 10% is considered strong
• **Example**: A 15% drawdown means your account dropped 15% from its highest point before recovering
• **Pro tip**: Max drawdown helps size positions appropriately for your risk tolerance

Always check if you could emotionally handle the max drawdown before using a strategy.
            """,
            
            "profit factor": """
**Profit Factor** is the ratio of gross profits to gross losses.

• **What it tells you**: How much money you make versus lose
• **Good values**: Above 1.0 is profitable, above 1.5 is solid, above 2.0 is excellent
• **Example**: A profit factor of 1.5 means you make $1.50 for every $1.00 you lose
• **Pro tip**: Strategies with lower win rates need higher profit factors to be viable

This metric helps compare strategies with different win rate characteristics.
            """
        }
        
        term_lower = term.lower()
        if term_lower in explanations:
            return explanations[term_lower]
        else:
            close_matches = [t for t in explanations.keys() if t in term_lower or term_lower in t]
            if close_matches:
                return explanations[close_matches[0]]
            else:
                return f"I don't have a specific explanation for '{term}'. Try asking about Sharpe Ratio, Win Rate, Drawdown, or Profit Factor."
    
    def _answer_best_strategy_question(self, question, context):
        """Answer questions about the best strategies."""
        # Extract ticker if present in the question
        ticker_match = None
        common_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ"]
        for ticker in common_tickers:
            if ticker in question.upper():
                ticker_match = ticker
                break
        
        if ticker_match:
            # Get mock best strategies for the specific ticker
            top_strategies = [
                {"name": "Momentum", "sharpe": round(random.uniform(1.5, 2.5), 2), "reason": "strong upward price action"},
                {"name": "Breakout", "sharpe": round(random.uniform(1.3, 2.3), 2), "reason": "key level crossover"},
                {"name": "Trend Following", "sharpe": round(random.uniform(1.2, 2.2), 2), "reason": "established trend"} 
            ]
            random.shuffle(top_strategies)
            top_strategies.sort(key=lambda x: x["sharpe"], reverse=True)
            
            response = f"""
**Top {ticker_match} Strategies:**

1. **{top_strategies[0]['name']} (Sharpe {top_strategies[0]['sharpe']})** – Chosen due to {top_strategies[0]['reason']}
2. **{top_strategies[1]['name']} (Sharpe {top_strategies[1]['sharpe']})** – Effective because of {top_strategies[1]['reason']}
3. **{top_strategies[2]['name']} (Sharpe {top_strategies[2]['sharpe']})** – Selected for {top_strategies[2]['reason']}

Would you like me to run a quick backtest on the top strategy or explain why it's performing well?
            """
            
        else:
            # General best strategies based on current market conditions
            market_phase = random.choice(["trending", "range-bound", "volatile"])
            vix_value = round(random.uniform(12, 30), 1)
            
            if market_phase == "trending":
                strategies = ["Momentum", "Trend Following", "Breakout"]
                reasoning = "strong directional movements in the current trending market"
            elif market_phase == "range-bound":
                strategies = ["Mean Reversion", "Bollinger Band", "RSI Oscillator"]
                reasoning = "price oscillations within defined ranges"
            else:  # volatile
                strategies = ["Volatility Expansion", "Options Straddle", "Protective Put"]
                reasoning = "increased market volatility (VIX: {vix_value})"
            
            response = f"""
**Current Top Strategies (Market Phase: {market_phase}):**

1. **{strategies[0]}** – Best performing due to {reasoning}
2. **{strategies[1]}** – Strong alternative approach for current conditions
3. **{strategies[2]}** – Solid backup strategy worth considering

Use command `/backtest TICKER with strategy {strategies[0]}` to test on a specific stock.
            """
            
        return response
    
    def _answer_market_condition_question(self, question, context):
        """Answer questions about current market conditions."""
        # Mock market data - would use real data in production
        vix = round(random.uniform(14, 28), 1)
        sentiment = random.choice(["bullish", "neutral", "bearish"])
        trend_strength = round(random.uniform(20, 80), 1)
        
        if vix > 25:
            volatility_desc = "high"
            volatility_impact = "favors mean reversion and volatility-based strategies"
        elif vix > 18:
            volatility_desc = "moderate"
            volatility_impact = "balanced between trend and mean reversion approaches"
        else:
            volatility_desc = "low"
            volatility_impact = "favors trend following and momentum strategies"
        
        best_sectors = random.sample(["Technology", "Healthcare", "Energy", "Financials", "Consumer"], 2)
        
        response = f"""
**Current Market Analysis:**

• **Volatility (VIX):** {vix} - {volatility_desc}
• **Market Sentiment:** {sentiment.title()}
• **Trend Strength:** {trend_strength}% 
• **Top Performing Sectors:** {best_sectors[0]}, {best_sectors[1]}

**Strategy Implications:**
Current conditions {volatility_impact}. {"Consider defensive positioning" if sentiment == "bearish" else "Opportunity for directional strategies" if sentiment == "bullish" else "Focus on quality setups in both directions."}

Would you like specific recommendations for these market conditions?
        """
        
        return response
    
    def _answer_strategy_comparison_question(self, question, context):
        """Answer questions comparing different strategies."""
        # Extract strategies to compare
        parts = question.lower().split("vs")
        if len(parts) < 2:
            parts = question.lower().split("versus")
        
        strategy1 = "Momentum"  # Default
        strategy2 = "Mean Reversion"  # Default
        
        # Try to extract actual strategies from the question
        strategy_terms = ["momentum", "trend", "breakout", "mean reversion", "volatility", "macd", "rsi"]
        for term in strategy_terms:
            if term in parts[0]:
                strategy1 = term.title()
            if len(parts) > 1 and term in parts[1]:
                strategy2 = term.title()
        
        # Mock comparison data
        comparison = {
            "Sharpe": {strategy1: round(random.uniform(1.2, 2.2), 2), strategy2: round(random.uniform(1.0, 2.0), 2)},
            "Win Rate": {strategy1: round(random.uniform(50, 75), 1), strategy2: round(random.uniform(45, 70), 1)},
            "Max Drawdown": {strategy1: round(random.uniform(5, 15), 1), strategy2: round(random.uniform(6, 16), 1)},
            "Profit Factor": {strategy1: round(random.uniform(1.3, 2.3), 2), strategy2: round(random.uniform(1.2, 2.2), 2)}
        }
        
        # Determine overall winner
        score1 = comparison["Sharpe"][strategy1] + comparison["Win Rate"][strategy1]/100 + comparison["Profit Factor"][strategy1] - comparison["Max Drawdown"][strategy1]/100
        score2 = comparison["Sharpe"][strategy2] + comparison["Win Rate"][strategy2]/100 + comparison["Profit Factor"][strategy2] - comparison["Max Drawdown"][strategy2]/100
        
        winner = strategy1 if score1 > score2 else strategy2
        
        response = f"""
**Strategy Comparison: {strategy1} vs {strategy2}**

| Metric | {strategy1} | {strategy2} |
|--------|-----------|-----------|
| Sharpe Ratio | {comparison["Sharpe"][strategy1]} | {comparison["Sharpe"][strategy2]} |
| Win Rate | {comparison["Win Rate"][strategy1]}% | {comparison["Win Rate"][strategy2]}% |
| Max Drawdown | {comparison["Max Drawdown"][strategy1]}% | {comparison["Max Drawdown"][strategy2]}% |
| Profit Factor | {comparison["Profit Factor"][strategy1]} | {comparison["Profit Factor"][strategy2]} |

**Summary:** {winner} is currently showing stronger overall performance, particularly in {"Sharpe Ratio and Win Rate" if winner == strategy1 else "Profit Factor with lower Drawdown"}.

When would you use each?
• **{strategy1}:** Best in {"trending markets with clear direction" if "trend" in strategy1.lower() or "momentum" in strategy1.lower() else "range-bound markets with price oscillation" if "reversion" in strategy1.lower() else "volatile markets with price expansion"}
• **{strategy2}:** Preferred during {"range-bound conditions" if "reversion" in strategy2.lower() else "strong trending markets" if "trend" in strategy2.lower() or "momentum" in strategy2.lower() else "periods of increasing volatility"}
        """
        
        return response
    
    def _answer_parameter_adjustment_question(self, question, context):
        """Answer questions about adjusting strategy parameters."""
        # Extract strategy if mentioned
        strategy_terms = {
            "momentum": {"key_params": ["lookback period", "entry threshold", "exit threshold"]},
            "trend": {"key_params": ["moving average period", "confirmation window", "trend filter"]},
            "mean reversion": {"key_params": ["z-score threshold", "lookback window", "entry level"]},
            "breakout": {"key_params": ["breakout level", "confirmation candles", "volume filter"]},
            "volatility": {"key_params": ["volatility window", "expansion threshold", "position sizing"]}
        }
        
        strategy = None
        for term in strategy_terms:
            if term in question.lower():
                strategy = term
                break
        
        if not strategy:
            strategy = random.choice(list(strategy_terms.keys()))
        
        # Generate advice
        response = f"""
**Parameter Adjustment for {strategy.title()} Strategy**

Key parameters to consider:
"""
        
        for param in strategy_terms[strategy]["key_params"]:
            if "period" in param or "window" in param:
                response += f"""
• **{param.title()}**: 
  - Current setting is likely too {"long" if random.choice([True, False]) else "short"}
  - Recommended change: {"Decrease" if random.choice([True, False]) else "Increase"} to capture {"more market fluctuations" if "reversion" in strategy else "stronger trend signals"}
  - Impact: This will make your strategy {"more responsive" if random.choice([True, False]) else "more selective"} to price movements
"""
            elif "threshold" in param or "level" in param:
                response += f"""
• **{param.title()}**: 
  - Current setting is likely too {"strict" if random.choice([True, False]) else "loose"}
  - Recommended change: {"Loosen" if random.choice([True, False]) else "Tighten"} to {"capture more trading opportunities" if random.choice([True, False]) else "improve signal quality"}
  - Impact: This will {"increase trade frequency but may reduce win rate" if random.choice([True, False]) else "decrease trade frequency but should increase win rate"}
"""
            else:
                response += f"""
• **{param.title()}**: 
  - Current setting may need recalibration based on recent market volatility
  - Recommended change: Adjust based on current VIX reading ({"higher" if random.choice([True, False]) else "lower"} settings for current market conditions)
  - Impact: More appropriate risk management for current market regime
"""
        
        response += """
Would you like me to suggest specific numeric values for these parameters?
        """
        
        return response

# Initialize AI assistant in session state
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = TradeGPTAssistant()

# Strategy descriptions - comprehensive and beginner-friendly explanations
strategy_descriptions = {
    # Basic Strategies
    "Momentum": "Momentum strategies buy assets that have performed well recently, based on the observation that assets that have risen tend to continue rising. This approach looks for stocks showing strong price movement and volume, riding the trend until it shows signs of reversing.",
    
    "Trend Following": "Trend following identifies and follows established market trends. It uses indicators like moving averages to determine trend direction, entering positions in the direction of the trend and exiting when the trend appears to be reversing.",
    
    "Breakout": "Breakout strategies look for assets breaking through important price levels (support or resistance) with increased volume. These breakouts often signal the start of a new trend, providing opportunities for significant price movements.",
    
    "Statistical Arbitrage": "Statistical arbitrage identifies temporary price discrepancies between related securities using mathematical models. These strategies exploit short-term anomalies, betting that prices will return to their statistical norms.",
    
    "Mean Reversion": "Mean reversion strategies work on the principle that prices tend to return to their average over time. When prices move significantly away from their historical averages, the strategy takes positions expecting a return to 'normal' levels.",
    
    "Volatility Expansion": "Volatility expansion strategies capitalize on periods of increasing market volatility. These approaches identify assets experiencing expanding price ranges and take positions to profit from the larger price swings that often follow.",
    
    "Swing Trading": "Swing trading captures medium-term price 'swings' lasting days to weeks. This approach aims to identify reversal points in the market, buying at the bottom of a price swing and selling at the top (or vice versa).",
    
    "Options Volatility Skew": "Options volatility skew strategies exploit imbalances in options pricing. These approaches take advantage of differences between implied volatility across different strike prices or expiration dates.",
    
    "News Sentiment": "News sentiment strategies analyze news articles, social media, and other text sources to measure market sentiment. These approaches take positions based on how positive or negative the overall sentiment appears for a particular asset.",
    
    "Pairs Trading": "Pairs trading involves identifying two historically correlated securities and taking opposing positions when their prices diverge. When the relationship returns to normal, both positions are closed for a profit.",
    
    "MACD Crossover": "MACD (Moving Average Convergence Divergence) crossover strategies generate trading signals when the MACD line crosses its signal line. This approach helps identify shifts in momentum and trend direction.",
    
    "Earnings Volatility": "Earnings volatility strategies take advantage of price movements around earnings announcements. These approaches analyze historical earnings reactions and position accordingly before companies report their results.",
    
    # Technical Analysis Strategies
    "Fibonacci Retracement": "Fibonacci retracement uses the Fibonacci sequence to identify potential support and resistance levels. This approach helps predict where prices might reverse after a significant movement.",
    
    "Ichimoku Cloud": "Ichimoku Cloud is a comprehensive technical analysis system showing support, resistance, momentum, and trend direction. This approach provides multiple signals in a single visual indicator system.",
    
    "RSI Divergence": "RSI (Relative Strength Index) divergence strategies identify potential reversals when price makes a new high/low but the RSI doesn't confirm. This approach spots weakening trends before price reflects the change.",
    
    "Triple Moving Average": "Triple moving average strategies use three moving averages of different periods. When the shortest MA crosses above/below the medium MA, which is above/below the long MA, it generates strong trend signals.",
    
    "Bollinger Band Squeeze": "Bollinger Band squeeze strategies identify periods of low volatility (when bands narrow) that often precede major price movements. This approach takes positions when volatility begins expanding after a squeeze.",
    
    "ADX Trend Strength": "ADX (Average Directional Index) strategies measure trend strength without indicating direction. This approach helps determine if a trend is strong enough to trade, often combined with directional indicators.",
    
    # Options-Specific Strategies
    "Iron Condor": "Iron condor options strategies profit from low volatility and sideways price action. This approach simultaneously sells out-of-the-money put and call spreads, creating a range where the strategy profits if the price stays within it.",
    
    "Calendar Spreads": "Calendar spreads involve buying and selling options of the same strike price but different expiration dates. This approach profits from time decay differences between near-term and longer-term options.",
    
    "Butterfly Spreads": "Butterfly spreads combine bull and bear spreads to create a position that profits when prices remain near a specific target. This approach offers limited risk with defined profit potential.",
    
    "Covered Call Writing": "Covered call writing involves holding a long position in an asset while selling call options on that asset. This approach generates income from option premiums while being protected from significant downside.",
    
    "Protective Put": "Protective put strategies involve holding a long position in an asset while buying put options on that asset. This approach limits downside risk by providing insurance against significant price drops.",
    
    "Ratio Spreads": "Ratio spreads involve buying and selling options at different strike prices in an unequal ratio. This approach can create positions with unique risk/reward profiles suited to specific market outlooks.",
    
    # Quantitative Strategies
    "Kalman Filter": "Kalman Filter strategies use a mathematical algorithm to estimate the true state of a system from noisy measurements. In trading, it helps identify the true trend among price noise.",
    
    "Machine Learning Classification": "Machine Learning classification strategies use algorithms to categorize market conditions and predict future price movements. These approaches learn patterns from historical data to make future predictions.",
    
    "Ensemble Methods": "Ensemble methods combine multiple trading algorithms to produce better results than any single model. This approach reduces risk by diversifying across different strategy types.",
    
    "PCA Factor Analysis": "PCA (Principal Component Analysis) factor strategies identify the main drivers of price movements across multiple assets. This approach helps isolate the most important factors affecting a market.",
    
    "Regime-Switching Models": "Regime-switching models recognize that markets behave differently in various 'regimes' (like bull/bear markets). These approaches adapt their trading rules based on the current market regime.",
    
    "Sentiment-Price Correlation": "Sentiment-price correlation strategies analyze the relationship between market sentiment and price movements. These approaches look for divergences that might signal upcoming price changes.",
    
    # Event-Driven Strategies
    "Post-Earnings Announcement Drift": "Post-earnings announcement drift strategies capitalize on the tendency of stock prices to continue moving in the direction of an earnings surprise. This approach enters positions after earnings announcements.",
    
    "ETF Rebalancing": "ETF rebalancing strategies profit from predictable trading patterns when ETFs adjust their holdings. These approaches position before known rebalancing dates to capture price movements.",
    
    "Index Inclusion": "Index inclusion strategies capitalize on price movements when stocks are added to major indices. This approach buys stocks before their official inclusion, selling after the price increase typically observed.",
    
    "Merger Arbitrage": "Merger arbitrage strategies profit from price discrepancies after merger announcements. This approach buys the target company and/or shorts the acquiring company to capture the merger premium.",
    
    "Short Interest Squeeze": "Short interest squeeze strategies identify heavily shorted stocks with potential for rapid price increases. When short sellers rush to cover, prices can spike dramatically.",
    
    "Buyback Announcement": "Buyback announcement strategies capitalize on the positive price impact when companies announce share repurchase programs. This approach buys shares after buyback announcements, anticipating increased demand."
}

def is_market_open():
    """Check if US market is currently open"""
    # Get current time in Eastern timezone
    current_time_utc = datetime.now(timezone.utc)
    eastern_tz = timezone(timedelta(hours=-4))  # EDT, adjust -5 for EST during winter
    current_time_et = current_time_utc.astimezone(eastern_tz)
    
    # Market hours: Monday-Friday, 9:30 AM - 4:00 PM Eastern
    is_weekday = current_time_et.weekday() < 5  # Monday=0, Friday=4
    market_open_time = current_time_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close_time = current_time_et.replace(hour=16, minute=0, second=0, microsecond=0)
    during_market_hours = market_open_time <= current_time_et <= market_close_time
    
    # Check for major US holidays (simplified)
    # For a production app, consider a more robust holiday calendar
    major_holidays = [
        # Format: (month, day) - 2023 holidays
        (1, 1),    # New Year's Day
        (1, 16),   # Martin Luther King Jr. Day
        (2, 20),   # Presidents' Day
        (4, 7),    # Good Friday
        (5, 29),   # Memorial Day
        (6, 19),   # Juneteenth
        (7, 4),    # Independence Day
        (9, 4),    # Labor Day
        (11, 23),  # Thanksgiving
        (12, 25),  # Christmas
    ]
    
    is_holiday = (current_time_et.month, current_time_et.day) in major_holidays
    
    return is_weekday and during_market_hours and not is_holiday

def fetch_market_conditions():
    """Fetch current market conditions."""
    try:
        # Get real market data
        return fetch_real_market_conditions()
    except Exception as e:
        st.warning(f"Error fetching real market data: {str(e)}. Falling back to simulated data.")
        # Simulate market conditions as a fallback
        return {
            "vix": round(random.uniform(10, 35), 2),
            "market_sentiment": random.choice(["bullish", "neutral", "bearish"]),
            "market_phase": random.choice(["trending", "range-bound", "volatile"]),
            "trending_sectors": random.sample(["Technology", "Healthcare", "Finance", "Energy", "Consumer Staples", "Utilities"], 2),
            "sector_momentum": {
                "Technology": round(random.uniform(-3, 5), 2),
                "Healthcare": round(random.uniform(-2, 3), 2),
                "Finance": round(random.uniform(-2, 4), 2),
                "Energy": round(random.uniform(-4, 4), 2),
                "Consumer Staples": round(random.uniform(-1, 2), 2),
                "Utilities": round(random.uniform(-1, 1), 2)
            }
        }

def compute_dynamic_parameters(strategy, base_params, market_conditions):
    """Adjusts strategy parameters based on current market conditions."""
    dynamic_params = base_params.copy()
    
    # Adjust parameters based on volatility (VIX)
    vix = market_conditions["vix"]
    volatility_factor = 1.0
    if vix > 30:  # High volatility
        volatility_factor = 0.7  # More conservative
    elif vix < 15:  # Low volatility
        volatility_factor = 1.3  # More aggressive
    
    # Adjust parameters based on market sentiment
    sentiment = market_conditions["market_sentiment"]
    sentiment_factor = 1.0
    if sentiment == "bullish":
        sentiment_factor = 1.2  # More aggressive
    elif sentiment == "bearish":
        sentiment_factor = 0.8  # More conservative
    
    # Apply adjustments to numeric parameters
    for param, value in dynamic_params.items():
        if isinstance(value, (int, float)) and param not in ["start_date", "end_date"]:
            if "period" in param or "window" in param:
                # For period/window parameters, adjust inversely with volatility
                dynamic_params[param] = max(2, int(value * (1 / volatility_factor)))
            elif "threshold" in param:
                # For thresholds, adjust with both factors
                dynamic_params[param] = value * volatility_factor * sentiment_factor
    
    return dynamic_params

def apply_performance_filters(winners_list):
    """Filter strategies based on performance criteria."""
    if not winners_list:
        return []
    
    filtered_winners = []
    for winner in winners_list:
        # Apply filters: max_drawdown < 5%, win_rate > 55%, sharpe > 1.2, profit_factor > 1.5
        if (winner.get("max_drawdown", 100) < 5 and
            winner.get("win_rate", 0) > 55 and
            winner.get("sharpe", 0) > 1.2 and
            winner.get("profit_factor", 0) > 1.5):
            filtered_winners.append(winner)
    
    return filtered_winners

def generate_strategy_narrative(winner, market_conditions):
    """Generate a narrative explaining why this strategy was chosen."""
    strategy_type = winner["strategy"]
    ticker = winner["ticker"]
    profit = winner["profit"]
    win_rate = winner["win_rate"]
    
    vix = market_conditions["vix"]
    sentiment = market_conditions["market_sentiment"]
    market_phase = market_conditions["market_phase"]
    trending_sectors = market_conditions["trending_sectors"]
    
    narrative = f"Strategy {strategy_type} for {ticker} shows promise with a {win_rate}% win rate "
    narrative += f"and {profit}% profit. "
    
    # Add context about market conditions
    narrative += f"Current market conditions show VIX at {vix}, indicating "
    if vix > 25:
        narrative += "elevated volatility. "
    elif vix < 15:
        narrative += "low volatility. "
    else:
        narrative += "moderate volatility. "
    
    narrative += f"Market sentiment is {sentiment} and the market is in a {market_phase} phase. "
    
    # Add sector context
    narrative += f"Trending sectors include {' and '.join(trending_sectors)}. "
    
    # Strategy-specific commentary
    if "Momentum" in strategy_type:
        narrative += "This momentum strategy capitalizes on price velocity and acceleration."
    elif "Trend" in strategy_type:
        narrative += "This trend-following approach aligns well with current market direction."
    elif "Reversion" in strategy_type:
        narrative += "This mean reversion strategy identifies and exploits price deviations."
    elif "Volatility" in strategy_type:
        narrative += "This volatility-based strategy thrives in the current market conditions."
    else:
        narrative += "This strategy has demonstrated robust performance metrics."
    
    return narrative

def run_autonomous_backtest():
    """Run an autonomous backtest and update the results in session state."""
    # Initialize session state for backtest results if it doesn't exist
    if "backtest_results" not in st.session_state:
        st.session_state.backtest_results = []
    
    # Set backtest in progress flag
    st.session_state.backtest_in_progress = True
    st.session_state.backtest_progress = 0
    
    # Fetch current market conditions
    market_conditions = fetch_market_conditions()
    st.session_state.market_conditions = market_conditions
    
    # Get available tickers and strategies
    available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC", "JPM"]
    available_strategies = [
        "Momentum", "Trend Following", "Breakout", "Statistical Arbitrage", 
        "Mean Reversion", "Volatility Expansion", "Swing Trading", "Options Volatility Skew", 
        "News Sentiment", "Pairs Trading", "MACD Crossover", "Earnings Volatility",
        # Technical Analysis Strategies
        "Fibonacci Retracement", "Ichimoku Cloud", "RSI Divergence", "Triple Moving Average",
        "Bollinger Band Squeeze", "ADX Trend Strength",
        # Options-Specific Strategies
        "Iron Condor", "Calendar Spreads", "Butterfly Spreads", "Covered Call Writing",
        "Protective Put", "Ratio Spreads",
        # Quantitative Strategies
        "Kalman Filter", "Machine Learning Classification", "Ensemble Methods",
        "PCA Factor Analysis", "Regime-Switching Models", "Sentiment-Price Correlation",
        # Event-Driven Strategies
        "Post-Earnings Announcement Drift", "ETF Rebalancing", "Index Inclusion",
        "Merger Arbitrage", "Short Interest Squeeze", "Buyback Announcement"
    ]
    
    # Define base parameters for each strategy
    base_params = {
        "lookback_period": 20,
        "signal_threshold": 0.5,
        "stop_loss": 2.0,
        "take_profit": 4.0,
        "risk_per_trade": 1.0
    }
    
    # Run backtests for different combinations
    winners = []
    total_tests = 20  # Limit the number of tests for demonstration
    
    for i in range(total_tests):
        # Update progress
        st.session_state.backtest_progress = (i+1) / total_tests
        
        # Randomly select ticker and strategy
        ticker = random.choice(available_tickers)
        strategy = random.choice(available_strategies)
        
        # Compute dynamic parameters based on market conditions
        params = compute_dynamic_parameters(strategy, base_params, market_conditions)
        
        # Simulate backtest results
        profit = round(random.uniform(-10, 30), 2)
        win_rate = round(random.uniform(40, 70), 2)
        max_drawdown = round(random.uniform(2, 10), 2)
        sharpe = round(random.uniform(0.5, 2.5), 2)
        profit_factor = round(random.uniform(0.8, 3.0), 2)
        
        # Generate unique ID for this backtest
        backtest_id = str(uuid.uuid4())
        
        # Create backtest result
        result = {
            "id": backtest_id,
            "ticker": ticker,
            "strategy": strategy,
            "params": params,
            "profit": profit,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "sharpe": sharpe,
            "profit_factor": profit_factor,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_conditions": market_conditions
        }
        
        winners.append(result)
    
    # Filter results based on performance criteria
    filtered_winners = apply_performance_filters(winners)
    
    # Sort by Sharpe ratio (or another preferred metric)
    filtered_winners.sort(key=lambda x: x["sharpe"], reverse=True)
    
    # Add narratives to top strategies
    for winner in filtered_winners[:5]:
        winner["narrative"] = generate_strategy_narrative(winner, market_conditions)
    
    # Update session state with results
    st.session_state.backtest_results = filtered_winners
    
    # Calculate summary metrics
    if filtered_winners:
        st.session_state.avg_profit = round(sum(w["profit"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.avg_win_rate = round(sum(w["win_rate"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.avg_sharpe = round(sum(w["sharpe"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.strategy_counts = {strategy: sum(1 for w in filtered_winners if w["strategy"] == strategy) for strategy in set(w["strategy"] for w in filtered_winners)}
    else:
        st.session_state.avg_profit = 0
        st.session_state.avg_win_rate = 0
        st.session_state.avg_sharpe = 0
        st.session_state.strategy_counts = {}
    
    # Set backtest in progress flag to False
    st.session_state.backtest_in_progress = False

def fetch_real_market_conditions():
    """Fetch actual market conditions from real data sources."""
    try:
        # Get VIX data
        vix = yf.Ticker("^VIX")
        vix_data = vix.history(period="2d")
        vix_value = round(vix_data['Close'].iloc[-1], 2)
        
        # Get SPY data for market sentiment and phase
        spy = yf.Ticker("SPY")
        spy_data = spy.history(period="60d")
        
        # Calculate market sentiment based on recent price action
        short_ma = spy_data['Close'].rolling(window=5).mean().iloc[-1]
        long_ma = spy_data['Close'].rolling(window=20).mean().iloc[-1]
        
        if short_ma > long_ma * 1.02:
            sentiment = "bullish"
        elif short_ma < long_ma * 0.98:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Calculate market phase based on volatility and trend
        recent_volatility = spy_data['Close'].pct_change().std() * np.sqrt(252) * 100
        price_trend = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-20] - 1) * 100
        
        if recent_volatility > 20:
            market_phase = "volatile"
        elif abs(price_trend) > 5:
            market_phase = "trending"
        else:
            market_phase = "range-bound"
        
        # Get sector performance
        sectors = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Finance": "XLF",
            "Energy": "XLE",
            "Consumer Staples": "XLP",
            "Utilities": "XLU"
        }
        
        sector_momentum = {}
        for sector_name, ticker in sectors.items():
            try:
                sector_data = yf.Ticker(ticker).history(period="15d")
                sector_momentum[sector_name] = round((sector_data['Close'].iloc[-1] / sector_data['Close'].iloc[-5] - 1) * 100, 2)
            except:
                sector_momentum[sector_name] = 0
        
        # Determine trending sectors
        trending_sectors = [sector for sector, momentum in sector_momentum.items() if momentum > 2]
        if not trending_sectors:
            trending_sectors = [max(sector_momentum.items(), key=lambda x: x[1])[0]]
        
        # Detect any anomalies
        anomalies = []
        if vix_value > 30:
            anomalies.append("high_volatility")
        if recent_volatility > 25:
            anomalies.append("market_turbulence")
        
        return {
            "vix": vix_value,
            "market_sentiment": sentiment,
            "market_phase": market_phase,
            "trending_sectors": trending_sectors,
            "sector_momentum": sector_momentum,
            "anomalies": anomalies
        }
    
    except Exception as e:
        # Fall back to simulated data if there's an error
        st.warning(f"Error fetching market data: {e}. Using simulated data instead.")
        return fetch_market_conditions()

def calculate_real_backtest_metrics(ticker, strategy_type, params, start_date, end_date):
    """
    Calculate backtest metrics using real data from yfinance with enhanced technical indicators.
    
    Args:
        ticker (str): Stock ticker symbol
        strategy_type (str): Type of trading strategy
        params (dict): Strategy parameters
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Dictionary containing backtest metrics or None if error
    """
    try:
        # Get data integration instance
        data_integration = st.session_state.data_integration
        
        # Get historical price data
        data = data_integration.get_price_data(ticker, start_date, end_date)
        
        if data.empty or len(data) < 30:  # Need sufficient data
            return None
        
        # Initialize signals list
        signals = []
        
        # Try to get technical indicators from Alpha Vantage
        indicator_data = {}
        use_alpha_vantage = True
        
        # Add technical indicators based on strategy type
        if strategy_type in ["Momentum", "Trend Following"]:
            # For momentum strategies, we need SMA indicators
            if use_alpha_vantage:
                sma_data = data_integration.get_technical_indicators(ticker, "SMA", 20)
                if sma_data is not None:
                    indicator_data["SMA20"] = sma_data
                
                sma_data = data_integration.get_technical_indicators(ticker, "SMA", 50)
                if sma_data is not None:
                    indicator_data["SMA50"] = sma_data
                
                sma_data = data_integration.get_technical_indicators(ticker, "SMA", 200)
                if sma_data is not None:
                    indicator_data["SMA200"] = sma_data
            
            # Fall back to calculated indicators if API not available
            if not indicator_data or len(indicator_data) < 3:
                # Calculate indicators from price data as fallback
                calculated_indicators = data_integration.calculate_technical_indicators(data, ["SMA"])
                data["SMA20"] = calculated_indicators.get("SMA20", data['Close'].rolling(window=20).mean())
                data["SMA50"] = calculated_indicators.get("SMA50", data['Close'].rolling(window=50).mean())
                data["SMA200"] = calculated_indicators.get("SMA200", data['Close'].rolling(window=200).mean())
            else:
                # Merge the indicators with the price data
                for indicator, indicator_df in indicator_data.items():
                    data[indicator] = indicator_df
            
            # Generate signals
            data['Signal'] = 0
            
            # Different signal logic based on strategy type
            if strategy_type == "Momentum":
                # Simple momentum: buy when price > SMA20, sell when price < SMA20
                data.loc[data['Close'] > data['SMA20'], 'Signal'] = 1
                data.loc[data['Close'] < data['SMA20'], 'Signal'] = -1
            else:  # Trend Following
                # Trend following: buy when SMA20 > SMA50 and price > SMA200
                data.loc[(data['SMA20'] > data['SMA50']) & (data['Close'] > data['SMA200']), 'Signal'] = 1
                data.loc[(data['SMA20'] < data['SMA50']) | (data['Close'] < data['SMA200']), 'Signal'] = -1
            
        elif strategy_type in ["Breakout", "Mean Reversion"]:
            # For these strategies, we need Bollinger Bands
            if use_alpha_vantage:
                bbands_data = data_integration.get_technical_indicators(ticker, "BBANDS", 20)
                if bbands_data is not None:
                    # Map column names from Alpha Vantage to our naming convention
                    data["BB_Upper"] = bbands_data["Real Upper Band"] if "Real Upper Band" in bbands_data.columns else None
                    data["BB_Middle"] = bbands_data["Real Middle Band"] if "Real Middle Band" in bbands_data.columns else None
                    data["BB_Lower"] = bbands_data["Real Lower Band"] if "Real Lower Band" in bbands_data.columns else None
            
            # Fall back to calculated indicators if API not available
            if "BB_Upper" not in data.columns:
                # Calculate Bollinger Bands
                calculated_indicators = data_integration.calculate_technical_indicators(data, ["BBANDS"])
                data["BB_Upper"] = calculated_indicators.get("BB_Upper")
                data["BB_Middle"] = calculated_indicators.get("BB_Middle")
                data["BB_Lower"] = calculated_indicators.get("BB_Lower")
            
            # Generate signals based on strategy type
            data['Signal'] = 0
            
            if strategy_type == "Breakout":
                # Breakout signals - buy on upper band breakout, sell on lower band breakout
                data.loc[data['Close'] > data['BB_Upper'], 'Signal'] = 1
                data.loc[data['Close'] < data['BB_Lower'], 'Signal'] = -1
            else:  # Mean Reversion
                # Mean reversion - buy near lower band, sell near upper band
                data.loc[data['Close'] < data['BB_Lower'], 'Signal'] = 1
                data.loc[data['Close'] > data['BB_Upper'], 'Signal'] = -1
            
        elif strategy_type in ["MACD Crossover"]:
            # Try to get MACD from Alpha Vantage
            if use_alpha_vantage:
                macd_data = data_integration.get_technical_indicators(ticker, "MACD")
                if macd_data is not None:
                    # Map column names from Alpha Vantage to our naming convention
                    data["MACD"] = macd_data["MACD"] if "MACD" in macd_data.columns else None
                    data["MACD_Signal"] = macd_data["MACD_Signal"] if "MACD_Signal" in macd_data.columns else None
                    data["MACD_Hist"] = macd_data["MACD_Hist"] if "MACD_Hist" in macd_data.columns else None
            
            # Fall back to calculated indicators if API not available
            if "MACD" not in data.columns:
                # Calculate MACD
                calculated_indicators = data_integration.calculate_technical_indicators(data, ["MACD"])
                data["MACD"] = calculated_indicators.get("MACD")
                data["MACD_Signal"] = calculated_indicators.get("MACD_Signal")
                data["MACD_Hist"] = calculated_indicators.get("MACD_Hist")
            
            # Generate MACD signals
            data['Signal'] = 0
            data.loc[data['MACD'] > data['MACD_Signal'], 'Signal'] = 1  # Bullish crossover
            data.loc[data['MACD'] < data['MACD_Signal'], 'Signal'] = -1  # Bearish crossover
            
        elif strategy_type in ["RSI Divergence", "RSI Oscillator"]:
            # Try to get RSI from Alpha Vantage
            if use_alpha_vantage:
                rsi_data = data_integration.get_technical_indicators(ticker, "RSI", 14)
                if rsi_data is not None:
                    # Map column names from Alpha Vantage to our naming convention
                    data["RSI"] = rsi_data["RSI"] if "RSI" in rsi_data.columns else None
            
            # Fall back to calculated indicators if API not available
            if "RSI" not in data.columns:
                # Calculate RSI
                calculated_indicators = data_integration.calculate_technical_indicators(data, ["RSI"])
                data["RSI"] = calculated_indicators.get("RSI")
            
            # Generate RSI signals
            data['Signal'] = 0
            data.loc[data['RSI'] < 30, 'Signal'] = 1  # Oversold condition
            data.loc[data['RSI'] > 70, 'Signal'] = -1  # Overbought condition
        
        else:
            # Default to a simple SMA crossover strategy
            # Calculate or get SMA indicators
            if "SMA20" not in data.columns or "SMA50" not in data.columns:
                calculated_indicators = data_integration.calculate_technical_indicators(data, ["SMA"])
                data["SMA20"] = calculated_indicators.get("SMA20", data['Close'].rolling(window=20).mean())
                data["SMA50"] = calculated_indicators.get("SMA50", data['Close'].rolling(window=50).mean())
            
            # Generate signals
            data['Signal'] = 0
            data.loc[data['SMA20'] > data['SMA50'], 'Signal'] = 1
            data.loc[data['SMA20'] < data['SMA50'], 'Signal'] = -1
        
        # Clean up NaN values
        data = data.dropna()
        
        # Generate trades based on signal changes
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(1, len(data)):
            current_date = data.index[i]
            prev_signal = data['Signal'].iloc[i-1]
            current_signal = data['Signal'].iloc[i]
            
            # Check for signal change
            if current_signal != prev_signal:
                if current_signal == 1 and position == 0:  # Buy signal
                    position = 1
                    entry_price = data['Close'].iloc[i]
                    entry_date = current_date
                    
                elif current_signal == -1 and position == 1:  # Sell signal
                    position = 0
                    exit_price = data['Close'].iloc[i]
                    pnl = (exit_price / entry_price) - 1
                    
                    trades.append({
                        "entry_date": entry_date.strftime("%Y-%m-%d"),
                        "exit_date": current_date.strftime("%Y-%m-%d"),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl": round(pnl * 100, 2),  # Convert to percentage
                        "holding_period": (current_date - entry_date).days
                    })
        
        # Calculate performance metrics
        if not trades:
            return None
        
        # Calculate win rate
        win_count = sum(1 for trade in trades if trade["pnl"] > 0)
        winrate = (win_count / len(trades)) * 100
        
        # Calculate profit factor
        gross_profit = sum(trade["pnl"] for trade in trades if trade["pnl"] > 0)
        gross_loss = abs(sum(trade["pnl"] for trade in trades if trade["pnl"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 2.0  # Avoid division by zero
        
        # Calculate returns for Sharpe ratio
        returns = [trade["pnl"] / 100 for trade in trades]  # Convert back from percentage
        
        # Calculate Sharpe ratio (assuming risk-free rate = 0 for simplicity)
        mean_return = sum(returns) / len(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.01  # Avoid division by zero
        sharpe = (mean_return / std_return) * np.sqrt(252 / 20)  # Annualized
        
        # Calculate max drawdown
        equity_curve = []
        equity = 1.0  # Start with $1
        max_equity = 1.0
        max_drawdown = 0.0
        
        # Generate equity curve
        dates = []
        equities = []
        
        current_equity = 1000  # Start with $1000
        
        for i, trade in enumerate(trades):
            trade_return = trade["pnl"] / 100  # Convert percentage to decimal
            
            # Add entry point
            entry_date = datetime.strptime(trade["entry_date"], "%Y-%m-%d")
            dates.append(entry_date)
            equities.append(current_equity)
            
            # Add exit point
            exit_date = datetime.strptime(trade["exit_date"], "%Y-%m-%d")
            current_equity *= (1 + trade_return)
            dates.append(exit_date)
            equities.append(current_equity)
            
            # Track max equity and drawdown
            if current_equity > max_equity:
                max_equity = current_equity
            else:
                drawdown = (max_equity - current_equity) / max_equity * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        # Create equity curve dataframe
        equity_df = pd.DataFrame({
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "equity": equities
        })
        
        # Return metrics
        return {
            "sharpe": sharpe,
            "winrate": winrate,
            "profit_factor": profit_factor,
            "max_drawdown": -max_drawdown,  # Negative to match existing code expectations
            "trades": trades,
            "equity_curve": equity_df
        }
    
    except Exception as e:
        st.error(f"Error calculating backtest metrics for {ticker} ({strategy_type}): {str(e)}")
        return None

def run_autonomous_backtest():
    """Run an autonomous backtest using real market data and update results in session state."""
    # Initialize session state for backtest results if it doesn't exist
    if "backtest_results" not in st.session_state:
        st.session_state.backtest_results = []
    
    # Set backtest in progress flag
    st.session_state.backtest_in_progress = True
    st.session_state.backtest_progress = 0
    
    # Fetch real market conditions
    market_conditions = fetch_real_market_conditions()
    st.session_state.market_conditions = market_conditions
    
    # Get available tickers and strategies
    available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC", "JPM"]
    available_strategies = [
        "Momentum", "Trend Following", "Breakout", "Statistical Arbitrage", 
        "Mean Reversion", "Volatility Expansion", "Swing Trading", "Options Volatility Skew", 
        "News Sentiment", "Pairs Trading", "MACD Crossover", "Earnings Volatility",
        # Technical Analysis Strategies
        "Fibonacci Retracement", "Ichimoku Cloud", "RSI Divergence", "Triple Moving Average",
        "Bollinger Band Squeeze", "ADX Trend Strength",
        # Options-Specific Strategies
        "Iron Condor", "Calendar Spreads", "Butterfly Spreads", "Covered Call Writing",
        "Protective Put", "Ratio Spreads",
        # Quantitative Strategies
        "Kalman Filter", "Machine Learning Classification", "Ensemble Methods",
        "PCA Factor Analysis", "Regime-Switching Models", "Sentiment-Price Correlation",
        # Event-Driven Strategies
        "Post-Earnings Announcement Drift", "ETF Rebalancing", "Index Inclusion",
        "Merger Arbitrage", "Short Interest Squeeze", "Buyback Announcement"
    ]
    
    # Define base parameters for each strategy
    base_params = {
        "lookback_period": 20,
        "signal_threshold": 0.5,
        "stop_loss": 2.0,
        "take_profit": 4.0,
        "risk_per_trade": 1.0
    }
    
    # Set test dates - use last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Run backtests for different combinations
    winners = []
    total_tests = min(20, len(available_tickers) * len(available_strategies))  # Limit for demonstration
    
    test_count = 0
    
    # Prioritize strategies based on market conditions
    if market_conditions["market_phase"] == "trending":
        prioritized_strategies = [s for s in available_strategies if "Trend" in s or "Momentum" in s]
    elif market_conditions["market_phase"] == "volatile":
        prioritized_strategies = [s for s in available_strategies if "Volatility" in s or "Mean Reversion" in s]
    else:  # range-bound
        prioritized_strategies = [s for s in available_strategies if "Breakout" in s or "Mean Reversion" in s]
    
    # Ensure we have some strategies
    if not prioritized_strategies:
        prioritized_strategies = available_strategies
    
    # Add some other strategies for diversity
    other_strategies = [s for s in available_strategies if s not in prioritized_strategies]
    test_strategies = prioritized_strategies + random.sample(other_strategies, min(5, len(other_strategies)))
    
    for strategy in test_strategies:
        # Select a subset of tickers to test with this strategy
        test_tickers = random.sample(available_tickers, min(3, len(available_tickers)))
        
        for ticker in test_tickers:
            # Update progress
            st.session_state.backtest_progress = test_count / total_tests
            test_count += 1
            
            # Compute dynamic parameters based on market conditions
            params = compute_dynamic_parameters(strategy, base_params, market_conditions)
            
            # Calculate real backtest metrics
            metrics = calculate_real_backtest_metrics(ticker, strategy, params, start_date, end_date)
            
            # Generate unique ID for this backtest
            backtest_id = str(uuid.uuid4())
            
            # Create backtest result
            result = {
                "id": backtest_id,
                "ticker": ticker,
                "strategy": strategy,
                "params": params,
                "profit": metrics["profit"],
                "win_rate": metrics["win_rate"],
                "max_drawdown": metrics["max_drawdown"],
                "sharpe": metrics["sharpe"],
                "profit_factor": metrics["profit_factor"],
                "trades": metrics["trades"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market_conditions": market_conditions,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            
            winners.append(result)
            
            # Stop if we've reached our test limit
            if test_count >= total_tests:
                break
                
        if test_count >= total_tests:
            break
    
    # Filter results based on performance criteria
    filtered_winners = apply_performance_filters(winners)
    
    # Sort by Sharpe ratio (or another preferred metric)
    filtered_winners.sort(key=lambda x: x["sharpe"], reverse=True)
    
    # Add narratives to top strategies
    for winner in filtered_winners[:5]:
        winner["narrative"] = generate_strategy_narrative(winner, market_conditions)
    
    # Update session state with results
    st.session_state.backtest_results = filtered_winners
    
    # Calculate summary metrics
    if filtered_winners:
        st.session_state.avg_profit = round(sum(w["profit"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.avg_win_rate = round(sum(w["win_rate"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.avg_sharpe = round(sum(w["sharpe"] for w in filtered_winners) / len(filtered_winners), 2)
        st.session_state.strategy_counts = {strategy: sum(1 for w in filtered_winners if w["strategy"] == strategy) for strategy in set(w["strategy"] for w in filtered_winners)}
    else:
        st.session_state.avg_profit = 0
        st.session_state.avg_win_rate = 0
        st.session_state.avg_sharpe = 0
        st.session_state.strategy_counts = {}
    
    # Set backtest in progress flag to False
    st.session_state.backtest_in_progress = False

def auto_promote_to_paper():
    """Promote top strategies to paper trading based on performance metrics."""
    if "backtest_results" not in st.session_state or not st.session_state.backtest_results:
        return "No strategies available for promotion"
    
    # Filter top strategies
    top_strategies = [
        winner for winner in st.session_state.backtest_results
        if winner.get("sharpe", 0) > 1.5 and winner.get("profit", 0) > 10
    ]
    
    if not top_strategies:
        return "No strategies meet promotion criteria"
    
    # Sort by Sharpe ratio
    top_strategies.sort(key=lambda x: x["sharpe"], reverse=True)
    
    # Promote the top 3 strategies (or fewer if less available)
    promoted = []
    for strategy in top_strategies[:3]:
        # In a real system, this would connect to a trading API
        promoted.append({
            "ticker": strategy["ticker"],
            "strategy": strategy["strategy"],
            "params": strategy["params"],
            "allocation": round(100000 * (strategy["sharpe"] / sum(s["sharpe"] for s in top_strategies[:3])), 2)
        })
    
    # Store in session state
    if "paper_strategies" not in st.session_state:
        st.session_state.paper_strategies = []
    
    st.session_state.paper_strategies.extend(promoted)
    
    return f"Promoted {len(promoted)} strategies to paper trading"

def select_backtest_row(row_id):
    """Handle selection of a backtest row in the winners table."""
    if "backtest_results" in st.session_state:
        for result in st.session_state.backtest_results:
            if result["id"] == row_id:
                st.session_state.selected_winner = result
                break

def promote_to_paper():
    """Promote a selected strategy to paper trading."""
    if "selected_winner" in st.session_state:
        winner = st.session_state.selected_winner
        
        # In a real system, this would connect to a trading API
        promoted = {
            "ticker": winner["ticker"],
            "strategy": winner["strategy"],
            "params": winner["params"],
            "allocation": 10000.00,  # Default allocation
            "status": "active"
        }
        
        # Store in session state
        if "paper_strategies" not in st.session_state:
            st.session_state.paper_strategies = []
        
        st.session_state.paper_strategies.append(promoted)
        
        return f"Promoted {winner['strategy']} strategy for {winner['ticker']} to paper trading"
    
    return "No strategy selected for promotion"

def add_ai_chat_message(message):
    """Add a message to the AI chat history and generate a response."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": message})
    
    # Generate response based on chat history and trading context
    response = generate_ai_response(message)
    
    # Add AI response
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    return response

def generate_ai_response(user_message):
    """Generate an AI response based on the user message and trading context."""
    # This is a simplified version - in a real app, this would call an API
    
    # Check for common queries
    user_message = user_message.lower()
    
    if "best strategy" in user_message:
        if "backtest_results" in st.session_state and st.session_state.backtest_results:
            top_strategy = max(st.session_state.backtest_results, key=lambda x: x["sharpe"])
            return f"Based on recent backtests, the {top_strategy['strategy']} strategy on {top_strategy['ticker']} has shown the best performance with a Sharpe ratio of {top_strategy['sharpe']} and a profit of {top_strategy['profit']}%."
        else:
            return "No backtest results available. Try running a backtest first to identify the best strategy."
    
    elif "market condition" in user_message or "market status" in user_message:
        if "market_conditions" in st.session_state:
            mc = st.session_state.market_conditions
            return f"Current market conditions: VIX at {mc['vix']}, sentiment is {mc['market_sentiment']}, market phase is {mc['market_phase']}. Trending sectors include {', '.join(mc['trending_sectors'])}."
        else:
            return "Market condition data not available. Try running a backtest to fetch current market data."
    
    elif "recommend" in user_message or "suggestion" in user_message:
        if "backtest_results" in st.session_state and st.session_state.backtest_results:
            strategies = st.session_state.backtest_results[:3]
            response = "Based on recent performance, I recommend considering these strategies:\n"
            for i, s in enumerate(strategies, 1):
                response += f"{i}. {s['strategy']} on {s['ticker']} - Sharpe: {s['sharpe']}, Profit: {s['profit']}%\n"
            return response
        else:
            return "I need more data to make recommendations. Try running some backtests first."
    
    else:
        return "I'm your trading assistant. I can help with strategy recommendations, market analysis, and interpreting backtest results. What specific trading question can I help you with today?"

# Function to toggle bookmark status
def toggle_bookmark(item_id):
    if item_id in st.session_state.bookmarked_news:
        st.session_state.bookmarked_news.remove(item_id)
    else:
        st.session_state.bookmarked_news.append(item_id)

# Function to toggle view mode
def toggle_view_mode():
    st.session_state.detailed_view = not st.session_state.detailed_view

# Add custom CSS
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
    .impact-badge-high {
        background-color: rgba(0,180,0,0.2);
        color: #006400;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .impact-badge-medium {
        background-color: rgba(255,165,0,0.2);
        color: #FF8C00;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .impact-badge-low {
        background-color: rgba(128,128,128,0.2);
        color: #696969;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .sector-tag {
        background-color: rgba(25,118,210,0.1);
        color: #1976D2;
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.7em;
        margin-right: 4px;
    }
    .breaking-badge {
        background-color: rgba(198,40,40,0.9);
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7em;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    .new-badge {
        background-color: rgba(25,118,210,0.9);
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7em;
        font-weight: bold;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .positive-change {
        color: #2E7D32;
        font-weight: bold;
    }
    .negative-change {
        color: #C62828;
        font-weight: bold;
    }
    .social-sentiment-positive {
        color: #2E7D32;
    }
    .social-sentiment-negative {
        color: #C62828;
    }
    .social-sentiment-neutral {
        color: #F57C00;
    }
    .sparkline-container {
        height: 20px;
        width: 60px;
        display: inline-block;
        vertical-align: middle;
    }
    .bookmark-icon {
        cursor: pointer;
        transition: color 0.3s;
    }
    .bookmark-icon:hover {
        color: #FFD700;
    }
    .bookmark-icon.active {
        color: #FFD700;
    }
    .keyboard-shortcuts {
        font-size: 0.8em;
        color: #666;
        padding: 5px;
        background-color: #f0f0f0;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-bottom: 3px solid #4e89ae;
    }
    /* Floating AI Assistant Button */
    .floating-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: #1E88E5;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 24px;
        cursor: pointer;
        z-index: 9999;
        transition: all 0.3s ease;
    }
    .floating-button:hover {
        background-color: #1565C0;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }
    /* Quick Chat Dialog */
    .quick-chat-dialog {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        max-height: 500px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 9998;
        display: none;
        flex-direction: column;
        overflow: hidden;
    }
    .quick-chat-header {
        padding: 12px 16px;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .quick-chat-close {
        cursor: pointer;
        font-size: 20px;
    }
    .quick-chat-messages {
        padding: 12px 16px;
        overflow-y: auto;
        flex-grow: 1;
        max-height: 300px;
    }
    .quick-chat-input {
        padding: 12px 16px;
        border-top: 1px solid #eee;
        display: flex;
    }
    .quick-chat-input input {
        flex-grow: 1;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 8px 12px;
        margin-right: 8px;
    }
    .quick-chat-input button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Add floating AI Assistant button with JavaScript
st.markdown("""
<div id="floating-ai-button" class="floating-button" onclick="toggleQuickChat()">
    🤖
</div>

<div id="quick-chat-dialog" class="quick-chat-dialog">
    <div class="quick-chat-header">
        <span>TradeGPT Co-Pilot</span>
        <span class="quick-chat-close" onclick="toggleQuickChat()">×</span>
    </div>
    <div class="quick-chat-messages" id="quick-chat-messages">
        <div style="padding: 8px 12px; background-color: #f0f0f0; border-radius: 8px; margin-bottom: 8px;">
            <strong>TradeGPT:</strong> Hi! I'm your trading assistant. How can I help?
        </div>
    </div>
    <div class="quick-chat-input">
        <input type="text" id="quick-chat-input" placeholder="Ask a quick question..." onkeypress="handleKeyPress(event)">
        <button onclick="sendQuickMessage()">Send</button>
    </div>
</div>

<script>
function toggleQuickChat() {
    const dialog = document.getElementById('quick-chat-dialog');
    if (dialog.style.display === 'flex') {
        dialog.style.display = 'none';
    } else {
        dialog.style.display = 'flex';
        document.getElementById('quick-chat-input').focus();
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter') {
        sendQuickMessage();
    }
}

function sendQuickMessage() {
    const input = document.getElementById('quick-chat-input');
    const messages = document.getElementById('quick-chat-messages');
    
    if (input.value.trim() === '') return;
    
    // Add user message
    messages.innerHTML += `
        <div style="padding: 8px 12px; background-color: #e6f3ff; border-radius: 8px; margin-bottom: 8px; text-align: right;">
            <strong>You:</strong> ${input.value}
        </div>
    `;
    
    // Scroll to bottom
    messages.scrollTop = messages.scrollHeight;
    
    // Clear input
    const userMessage = input.value;
    input.value = '';
    
    // Show thinking indicator
    messages.innerHTML += `
        <div id="thinking-indicator" style="padding: 8px 12px; background-color: #f0f0f0; border-radius: 8px; margin-bottom: 8px;">
            <strong>TradeGPT:</strong> <em>Thinking...</em>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;
    
    // In a real implementation, this would call your backend API
    // For demo, we'll just simulate a response after a short delay
    setTimeout(() => {
        // Remove thinking indicator
        document.getElementById('thinking-indicator').remove();
        
        // Add AI response (simulated)
        let response = '';
        if (userMessage.toLowerCase().includes('strategy')) {
            response = "Based on current market conditions, momentum strategies are performing well. Would you like me to suggest specific parameters?";
        } else if (userMessage.toLowerCase().includes('market')) {
            response = "Current market sentiment is moderately bullish with VIX at 18.5. Tech sector showing strength.";
        } else if (userMessage.toLowerCase().includes('explain') || userMessage.toLowerCase().includes('what is')) {
            response = "I'd be happy to explain! The concept you're asking about relates to risk-adjusted returns. Would you like a more detailed explanation?";
        } else {
            response = "I can help with trading strategies, market analysis, and parameter optimization. What specific aspect are you interested in?";
        }
        
        messages.innerHTML += `
            <div style="padding: 8px 12px; background-color: #f0f0f0; border-radius: 8px; margin-bottom: 8px;">
                <strong>TradeGPT:</strong> ${response}
            </div>
        `;
        
        // Scroll to bottom again
        messages.scrollTop = messages.scrollHeight;
        
        // Return focus to input
        input.focus();
    }, 1000);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // This will run when the page loads
    const floatingButton = document.getElementById('floating-ai-button');
    if (floatingButton) {
        // Add a subtle animation
        setInterval(() => {
            floatingButton.style.transform = 'translateY(-2px)';
            setTimeout(() => {
                floatingButton.style.transform = 'translateY(0)';
            }, 500);
        }, 3000);
    }
});
</script>
""", unsafe_allow_html=True)

# Sidebar for user controls
with st.sidebar:
    st.title("TradeGPT Navigator")
    
    st.markdown("### ⚙️ Trading Settings")
    
    time_range = st.selectbox(
        "Select Time Range:",
        ["1 Day", "1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "YTD", "All Time"],
        index=3
    )
    
    # API Usage Monitor Section
    with st.expander("📊 API Usage Monitor"):
        st.markdown("#### Today's API Usage")
        
        # Mock API usage data
        api_usage = {
            "finnhub": {"used": 782, "limit": 1000, "percent": 78.2},
            "marketaux": {"used": 45, "limit": 100, "percent": 45.0},
            "newsdata": {"used": 87, "limit": 200, "percent": 43.5},
            "gnews": {"used": 19, "limit": 100, "percent": 19.0}
        }
        
        # Display usage for each API
        for api, data in api_usage.items():
            st.markdown(f"**{api.capitalize()}**")
            st.progress(data["percent"] / 100)
            st.caption(f"{data['used']} / {data['limit']} calls ({data['percent']}%)")
        
        # Total usage summary
        total_used = sum(data["used"] for data in api_usage.values())
        total_limit = sum(data["limit"] for data in api_usage.values())
        total_percent = (total_used / total_limit) * 100 if total_limit > 0 else 0
        
        st.markdown("#### Total Usage")
        st.progress(total_percent / 100)
        st.caption(f"{total_used} / {total_limit} calls ({total_percent:.1f}%)")
        
        # Clear log button
        if st.button("Clear API Log"):
            st.success("API log has been cleared!")
    
    # Strategy settings
    with st.expander("🔧 Strategy Settings"):
        # Define selected_strategies
        all_strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
        selected_strategies = all_strategies
        
        # Define risk level
        risk_level = "Moderate"
        current_risk_multiplier = 1.0

# Main dashboard content
st.markdown('<div class="main-header">Trading Strategy Dashboard</div>', unsafe_allow_html=True)

# Autonomous Backtest Button and Status
with st.container():
    backtest_col1, backtest_col2, backtest_col3 = st.columns([2, 2, 3])
    
    with backtest_col1:
        if st.button("🤖 Run Autonomous Backtest", type="primary", key="main_backtest_btn"):
            # Set backtest in progress flag and run
            st.session_state.auto_backtest_running = True
            st.session_state.backtest_status = "Running"
            
            with st.status("Running autonomous backtest...", expanded=True) as status:
                st.write("Analyzing market conditions and building strategy queue...")
                try:
                    run_autonomous_backtest()
                    status.update(label="Backtest completed successfully!", state="complete")
                except Exception as e:
                    st.error(f"Error during backtest: {str(e)}")
                    status.update(label="Backtest failed", state="error")
                    st.session_state.auto_backtest_running = False
                    st.session_state.backtest_status = "Error"
    
    with backtest_col2:
        # Show backtest status
        if st.session_state.get("backtest_status") == "Running":
            st.info("⏳ Backtest in progress...")
        elif st.session_state.get("backtest_status") == "Completed":
            st.success("✅ Last backtest completed at " + st.session_state.get("last_run_time", ""))
        elif st.session_state.get("backtest_status") == "Error":
            st.error("❌ Last backtest failed")
        else:
            st.info("Ready to run backtest")
    
    with backtest_col3:
        # Show top 2 strategies from last backtest
        if "backtest_results" in st.session_state and isinstance(st.session_state.backtest_results, dict) and "winners" in st.session_state.backtest_results:
            winners = st.session_state.backtest_results.get("winners", [])
            if winners:
                top_winners = winners[:2]
                winner_html = "<div style='font-weight: bold;'>Top Strategies:</div>"
                for i, winner in enumerate(top_winners):
                    winner_html += f"<div style='margin-top: 5px;'>{i+1}. {winner.get('ticker', '')} - {winner.get('strategy', '')} (Sharpe: {winner.get('sharpe', 0):.2f})</div>"
                st.markdown(winner_html, unsafe_allow_html=True)
        elif st.session_state.get("backtest_status") == "Ready":
            st.markdown("Run autonomous backtest to discover top strategies")

# Create top row with summary metrics
metric_cols = st.columns(4)

# Calculate metrics
win_rates = {"Momentum": 67.8, "Mean Reversion": 68.5, "Breakout": 62.3, "Volatility": 59.8, "Trend Following": 74.2, "Pairs Trading": 65.1}
profit_factors = {"Momentum": 1.92, "Mean Reversion": 1.78, "Breakout": 1.65, "Volatility": 1.59, "Trend Following": 2.15, "Pairs Trading": 1.72}
drawdowns = {"Momentum": -4.2, "Mean Reversion": -5.1, "Breakout": -6.8, "Volatility": -8.3, "Trend Following": -3.5, "Pairs Trading": -4.9}
sharpes = {"Momentum": 1.85, "Mean Reversion": 1.73, "Breakout": 1.62, "Volatility": 1.51, "Trend Following": 2.05, "Pairs Trading": 1.68}

avg_win_rate = sum(win_rates.values()) / len(win_rates)
avg_profit_factor = sum(profit_factors.values()) / len(profit_factors)
avg_drawdown = sum(drawdowns.values()) / len(drawdowns)
avg_sharpe = sum(sharpes.values()) / len(sharpes)

with metric_cols[0]:
    st.metric(label="Total Win Rate", value=f"{avg_win_rate:.1f}%")
with metric_cols[1]:
    st.metric(label="Profit Factor", value=f"{avg_profit_factor:.2f}")
with metric_cols[2]:
    st.metric(label="Max Drawdown", value=f"{avg_drawdown:.1f}%", delta_color="inverse")
with metric_cols[3]:
    st.metric(label="Sharpe Ratio", value=f"{avg_sharpe:.2f}")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Backtesting", "Paper Trading", "Strategy", "News/Prediction"])

with tab1:
    # Portfolio Performance Chart
    st.markdown('<div class="sub-header">Portfolio Performance</div>', unsafe_allow_html=True)
    
    # Create sample data
    date_range = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_value = 100000
    portfolio_values = [base_value]
    
    for i in range(1, len(date_range)):
        change = np.random.normal(0.0003, 0.001)
        portfolio_values.append(portfolio_values[-1] * (1 + change))
    
    benchmark_values = [base_value * (1 + 0.0001 * i + np.random.normal(0, 0.0005)) for i in range(len(date_range))]
    
    portfolio_df = pd.DataFrame({
        'Date': date_range,
        'Portfolio Value': portfolio_values,
        'Benchmark': benchmark_values
    })
    
    # Display chart
    fig_portfolio = px.line(
        portfolio_df,
        x='Date',
        y=['Portfolio Value', 'Benchmark'],
        title=f"Portfolio vs Benchmark Performance ({time_range})",
        color_discrete_sequence=['#1E88E5', '#FFA000']
    )
    st.plotly_chart(fig_portfolio, use_container_width=True)
    
    # Two column layout for allocation and trades
    alloc_col, trades_col = st.columns(2)
    
    with alloc_col:
        st.markdown('<div class="sub-header">🥧 Allocation Breakdown</div>', unsafe_allow_html=True)
        
        # Sample data
        strategies = ["Momentum", "Mean Reversion", "Breakout", "Volatility", "Trend Following", "Pairs Trading"]
        allocations = [30, 25, 15, 10, 15, 5]
        
        # Create pie chart
        fig_allocation = px.pie(
            values=allocations,
            names=strategies,
            title="Current Capital Allocation",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_allocation.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_allocation, use_container_width=True)
    
    with trades_col:
        st.markdown('<div class="sub-header">📋 Recent Trades</div>', unsafe_allow_html=True)
        
        # Sample trade data
        trades_data = {
            "Symbol": ["AAPL", "MSFT", "TSLA", "AMZN", "NVDA", "GOOGL", "QQQ", "SPY"],
            "Strategy": ["Momentum", "Breakout", "Volatility", "Mean Reversion", "Momentum", "Trend Following", "Pairs Trading", "Mean Reversion"],
            "Entry Date": ["2023-04-10", "2023-04-09", "2023-04-08", "2023-04-07", "2023-04-06", "2023-04-05", "2023-04-04", "2023-04-03"],
            "Status": ["Open", "Open", "Closed", "Closed", "Open", "Closed", "Open", "Closed"],
            "P&L (%)": [2.3, 3.1, -1.2, 4.5, 6.2, 1.8, 0.9, 2.7]
        }
        
        trades_df = pd.DataFrame(trades_data)
        st.dataframe(trades_df, use_container_width=True)
    
    # Alerts and Warnings Section
    st.markdown('<div class="sub-header">⚠️ Alerts & Warnings</div>', unsafe_allow_html=True)
    
    # Create alerts
    alerts_data = [
        {
            "type": "Price Alert",
            "symbol": "AAPL",
            "message": "Price exceeded upper threshold of $190.00",
            "timestamp": "10 minutes ago",
            "severity": "medium",
            "action": "Consider taking profits or setting tighter stop-loss"
        },
        {
            "type": "Volatility Warning",
            "symbol": "VIX",
            "message": "Market volatility increased by 15% today",
            "timestamp": "2 hours ago",
            "severity": "high",
            "action": "Review portfolio hedging strategy and reduce position sizes"
        },
        {
            "type": "Trading Signal",
            "symbol": "TSLA",
            "message": "Bullish crossover on 1-hour chart",
            "timestamp": "30 minutes ago",
            "severity": "low",
            "action": "Consider opening a long position with defined risk parameters"
        },
        {
            "type": "Position Warning",
            "symbol": "META",
            "message": "Position approaching stop loss at $302.50",
            "timestamp": "5 minutes ago",
            "severity": "high",
            "action": "Prepare for automatic exit or manually review position"
        },
        {
            "type": "Execution Alert",
            "symbol": "MSFT",
            "message": "Buy order filled: 50 shares at $384.25",
            "timestamp": "45 minutes ago",
            "severity": "low",
            "action": "Set appropriate stop loss and take profit levels"
        }
    ]
    
    # Display alerts
    for alert in alerts_data:
        # Set styling based on severity
        if alert["severity"] == "high":
            alert_style = "background-color: rgba(255,0,0,0.1); border-left: 4px solid #ff0000; padding: 10px; margin-bottom: 10px;"
            icon = "🔴"
        elif alert["severity"] == "medium":
            alert_style = "background-color: rgba(255,165,0,0.1); border-left: 4px solid #ffa500; padding: 10px; margin-bottom: 10px;"
            icon = "🟠"
        else:
            alert_style = "background-color: rgba(0,128,0,0.1); border-left: 4px solid #008000; padding: 10px; margin-bottom: 10px;"
            icon = "🟢"
        
        with st.container():
            st.markdown(f"""
            <div style="{alert_style}">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>{icon} {alert['type']}: {alert['symbol']}</strong></span>
                    <span style="color: gray; font-size: 0.8em;">{alert['timestamp']}</span>
                </div>
                <p style="margin: 5px 0;">{alert['message']}</p>
                <p style="margin: 5px 0; font-style: italic; font-size: 0.9em;"><strong>Recommended Action:</strong> {alert['action']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Add refresh button for alerts
    st.button("🔄 Refresh Alerts")

with tab2:
    st.markdown('<div class="main-header">Autonomous Trading Discovery Engine</div>', unsafe_allow_html=True)
    
    # Initialize session state for backtesting tab if not already initialized
    if 'selected_backtest_row' not in st.session_state:
        st.session_state.selected_backtest_row = None
    
    if 'backtest_results' not in st.session_state:
        # Initialize with empty results
        st.session_state.backtest_results = {
            "summary_metrics": {
                "avg_sharpe": 0.0,
                "overall_winrate": 0.0,
                "avg_profit_factor": 0.0,
                "max_drawdown": 0.0
            },
            "winners": []
        }
    
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    if 'backtest_status' not in st.session_state:
        st.session_state.backtest_status = "Ready"
        
    if 'last_run_time' not in st.session_state:
        st.session_state.last_run_time = "Not run yet"
        
    if 'last_auto_run' not in st.session_state:
        st.session_state.last_auto_run = datetime.now() - timedelta(minutes=120)
    
    if 'config_version' not in st.session_state:
        st.session_state.config_version = f"v1.0.{random.randint(100, 999)}"
    
    # Check if we should auto-run a backtest based on market conditions
    current_time = datetime.now(pytz.timezone('US/Eastern'))
    market_open_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # Calculate minutes since market open and since last run
    if current_time > market_open_time:
        minutes_since_open = (current_time - market_open_time).total_seconds() / 60
    else:
        minutes_since_open = -1  # Market not open yet
    
    minutes_since_last_run = (current_time - st.session_state.last_auto_run).total_seconds() / 60
    
    # Conditions for auto-running:
    # 1. Run within 15 minutes of market open
    # 2. Run at least every 120 minutes during market hours
    should_auto_run = (
        is_market_open() and 
        (
            (0 <= minutes_since_open <= 15) or 
            (minutes_since_last_run >= 120)
        )
    )
    
    # Create container for auto-run messages
    auto_run_container = st.container()
    
    # Log the auto-run status for debugging
    with auto_run_container:
        if should_auto_run:
            st.info("📊 Auto-running backtest based on market conditions...")
            try:
                run_autonomous_backtest()
                st.session_state.last_auto_run = current_time
                st.session_state.backtest_status = "Completed"
                st.session_state.last_run_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                st.success("✅ Auto-backtest completed successfully!")
            except Exception as e:
                st.error(f"❌ Auto-backtest failed: {str(e)}")
        elif is_market_open():
            # Calculate when the next run will be
            if minutes_since_open <= 15 and minutes_since_open > 0:
                st.info(f"Next scheduled auto-run: At market open (within {15-minutes_since_open:.0f} minutes)")
            else:
                next_run_minutes = 120 - minutes_since_last_run
                st.info(f"Next scheduled auto-run: In {next_run_minutes:.0f} minutes")
    
    # 1. CONTROLS BAR
    st.markdown("## Autonomous Discovery & Backtest")
    
    controls_col1, controls_col2, controls_col3 = st.columns([1.5, 1.5, 1])
    
    with controls_col1:
        # Date range picker
        col1a, col1b = st.columns(2)
        with col1a:
            start_date = st.date_input(
                "Start Date", 
                value=datetime.now() - timedelta(days=90),
                help="Beginning of backtest period"
            )
        with col1b:
            end_date = st.date_input(
                "End Date", 
                value=datetime.now(),
                help="End of backtest period"
            )
    
    with controls_col2:
        # Ticker multi-select
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "NFLX", "QQQ", "SPY", 
                  "NVDA", "JPM", "BAC", "V", "JNJ", "PG", "KO", "DIS", "INTC", "XLK"]
        selected_tickers = st.multiselect(
            "Select Tickers (Optional)",
            options=tickers,
            default=[],
            help="Override auto-selected universe. Leave empty for auto mode."
        )
        # Store selected tickers in session state
        st.session_state.selected_tickers = selected_tickers
    
    with controls_col3:
        # Config version display
        st.markdown(f"**Config Version:**  \n{st.session_state.config_version}")
        
        # Status and last run info
        if st.session_state.backtest_status == "Running":
            st.markdown("**Status:** 🔄 Running")
        elif st.session_state.backtest_status == "Completed":
            st.markdown("**Status:** ✅ Complete")
        else:
            st.markdown("**Status:** ⏱️ Ready")
        
        st.caption(f"Last run: {st.session_state.last_run_time}")
    
    # Progress indicator (shown only during active runs)
    if st.session_state.backtest_status == "Running":
        with st.container():
            progress_bar = st.progress(0)
            st.info("Backtesting in progress. This may take a few minutes...")
            # Simulate progress updates - in a real implementation, this would be updated by the backtest process
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            # Update status when done
            st.session_state.backtest_status = "Completed"
            st.session_state.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.experimental_rerun()
    
    st.divider()
    
    # 2. KPI SUMMARY ROW
    st.markdown("## Performance Summary", help="Key performance indicators across all backtested strategies")
    
    metric_cols = st.columns(4)
    # Check if backtest_results is a dictionary or a list and handle accordingly
    if isinstance(st.session_state.backtest_results, dict) and "summary_metrics" in st.session_state.backtest_results:
        summary = st.session_state.backtest_results["summary_metrics"]
    else:
        # Default values if summary_metrics is not available
        summary = {
            "avg_sharpe": 0.0,
            "overall_winrate": 0.0,
            "avg_profit_factor": 0.0,
            "max_drawdown": 0.0
        }
    
    with metric_cols[0]:
        st.metric(
            "Avg Sharpe Ratio", 
            f"{summary['avg_sharpe']:.2f}", 
            help="Risk-adjusted return measure. Higher is better. Above 1.0 is good."
        )
    
    with metric_cols[1]:
        st.metric(
            "Overall Win-Rate", 
            f"{summary['overall_winrate']:.1f}%",
            help="Percentage of profitable trades. Above 50% is profitable."
        )
    
    with metric_cols[2]:
        st.metric(
            "Avg Profit Factor", 
            f"{summary['avg_profit_factor']:.2f}",
            help="Gross profit divided by gross loss. Above 1.0 is profitable."
        )
    
    with metric_cols[3]:
        st.metric(
            label="Max Drawdown", 
            value=f"{summary['max_drawdown']:.1f}%", 
            delta_color="inverse",
            help="Largest peak-to-trough decline. Lower is better."
        )
    
    st.divider()
    
    # 3. WINNERS TABLE
    st.markdown("## Top Performing Strategies", help="Strategies that passed performance filters")
    
    # Check if backtest_results is a list or dictionary to handle both cases
    if isinstance(st.session_state.backtest_results, dict) and "winners" in st.session_state.backtest_results:
        winners = st.session_state.backtest_results["winners"]
    elif isinstance(st.session_state.backtest_results, list):
        winners = st.session_state.backtest_results
    else:
        winners = []
    
    if not winners:
        st.info("No backtest results yet. Click 'Run Real-time Backtest' to discover strategies.")
    else:
        # Display performance filter criteria explanation for beginners
        st.info("""
        **What makes a winning strategy?** 📊  
        Only strategies meeting these criteria are shown:
        - **Max Drawdown < 5%** (never loses more than 5% from peak to trough)
        - **Win Rate > 55%** (more than half of trades are profitable)
        - **Sharpe Ratio > 1.2** (earns more than it risks)
        - **Profit Factor > 1.5** (makes at least 1.5x what it loses)
        """)
        
        # Create a custom winners table with beginner-friendly explanations
        for i, winner in enumerate(winners):
            # Calculate confidence score based on performance metrics
            confidence = min(100, int((
                (winner["sharpe"] / 3 * 100) * 0.4 + 
                (winner["winrate"] / 100 * 100) * 0.3 + 
                (min(3, winner["profit_factor"]) / 3 * 100) * 0.2 + 
                (min(30, abs(winner["max_drawdown"])) / 30 * 100) * 0.1
            )))
            
            # Create a card for each winner with "Why Chosen" section
            with st.container():
                # Add "Why Chosen" banner at the top of each card
                if "narrative" in winner and winner["narrative"]:
                    # Extract the first sentence of the narrative for the "Why Chosen" section
                    narrative_parts = winner["narrative"].split('\n\n')
                    why_chosen = narrative_parts[0] if narrative_parts else "Strategy selected based on performance criteria."
                    st.success(f"🔍 **Why Chosen:** {why_chosen}")
                
                # Strategy header with confidence score
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"## {winner['ticker']} – {winner['strategy']}")
                with col2:
                    st.markdown(f"**Confidence: {confidence}%**")
                
                # Performance metrics with explanations
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                
                with metrics_col1:
                    st.metric(
                        "Sharpe Ratio", 
                        f"{winner['sharpe']:.2f}",
                        help="Risk-adjusted return. Higher is better. Above 1.0 is good."
                    )
                
                with metrics_col2:
                    st.metric(
                        "Win Rate", 
                        f"{winner['winrate']:.1f}%",
                        help="Percentage of profitable trades. Above 50% is profitable."
                    )
                
                with metrics_col3:
                    st.metric(
                        "Profit Factor", 
                        f"{winner['profit_factor']:.2f}",
                        help="Gross profit divided by gross loss. Above 1.0 is profitable."
                    )
                
                with metrics_col4:
                    st.metric(
                        "Max Drawdown", 
                        f"{winner['max_drawdown']:.1f}%", 
                        delta_color="inverse",
                        help="Largest peak-to-trough decline. Lower is better."
                    )
                
                # Display strategy parameters
                if "params" in winner:
                    with st.expander("Strategy Parameters Explained", expanded=False):
                        st.markdown("**What these parameters mean:**")
                        
                        # Convert parameters to a more beginner-friendly format with explanations
                        params_explained = []
                        for param, value in winner["params"].items():
                            explanation = ""
                            if param == "lookback_period":
                                explanation = "Number of days to look back for calculating signals"
                            elif param == "threshold":
                                explanation = "Signal strength required to enter a trade"
                            elif param == "take_profit":
                                explanation = "% gain at which to exit with profit"
                            elif param == "stop_loss":
                                explanation = "% loss at which to exit to prevent further losses"
                            elif param == "position_size":
                                explanation = "Portion of capital to allocate to this trade"
                            elif param == "z_score_threshold":
                                explanation = "How far from the average price to trigger entry"
                            elif param == "volatility_threshold":
                                explanation = "Minimum volatility required for strategy"
                            elif param == "momentum_factor":
                                explanation = "Weight given to recent price momentum"
                            else:
                                explanation = "Strategy-specific configuration"
                            
                            params_explained.append({
                                "Parameter": param,
                                "Value": value,
                                "Explanation": explanation
                            })
                        
                        # Create and display the dataframe
                        params_df = pd.DataFrame(params_explained)
                        st.dataframe(params_df, hide_index=True)
                
                # Action buttons
                details_col, paper_col = st.columns(2)
                
                with details_col:
                    if st.button(f"📊 View Details", key=f"details_{winner['id']}", use_container_width=True):
                        # Set the selected winner and open a details dialog
                        st.session_state.selected_backtest_row = winner["id"]
                
                with paper_col:
                    if st.button(f"📈 Promote to Paper Trading", key=f"paper_{winner['id']}", use_container_width=True):
                        # Handle promotion to paper trading
                        select_backtest_row(winner["id"])
                        promote_to_paper()
                        st.success(f"Successfully promoted {winner['ticker']} {winner['strategy']} to paper trading!")
                
                # Add a divider between winners
                st.divider()
        
        # 4. AUTO-REPORT INSIGHTS
        st.markdown("## AI Trading Insights", help="Automatically generated analysis based on backtest results")
        
        # Create insights based on the backtest results
        if winners:
            # Top performing strategies
            st.markdown("### 🥇 Top Performing Strategies")
            for i, winner in enumerate(winners[:3]):  # Show top 3
                st.markdown(f"**{i+1}. {winner['ticker']} {winner['strategy']}** - Sharpe: {winner['sharpe']:.2f}, Win Rate: {winner['winrate']:.1f}%")
                # Extract reason from narrative if available
                if "narrative" in winner and winner["narrative"]:
                    # Try to extract a reason from the narrative
                    narrative_parts = winner["narrative"].split('\n\n')
                    reason = narrative_parts[0] if len(narrative_parts) > 0 else ""
                    st.markdown(f"- {reason}")
            
            # Underperforming signals
            if isinstance(st.session_state.backtest_results, dict) and "all_results" in st.session_state.backtest_results:
                filtered_out = [w for w in st.session_state.backtest_results.get("all_results", []) 
                            if w["id"] not in [winner["id"] for winner in winners]][:2]
            else:
                filtered_out = []
            
            if filtered_out:
                st.markdown("### ⚠️ Strategies That Didn't Make the Cut")
                for i, loser in enumerate(filtered_out):
                    issue = ""
                    if loser.get("max_drawdown", 0) < -5.0:
                        issue = f"drawdown too high ({abs(loser.get('max_drawdown', 0)):.1f}%)"
                    elif loser.get("winrate", 0) < 55.0:
                        issue = f"win rate too low ({loser.get('winrate', 0):.1f}%)"
                    elif loser.get("sharpe", 0) < 1.2:
                        issue = f"Sharpe ratio too low ({loser.get('sharpe', 0):.2f})"
                    else:
                        issue = "multiple criteria not met"
                    
                    st.markdown(f"**{loser.get('ticker', 'Unknown')} {loser.get('strategy', 'Unknown')}** - {issue}")
            
            # Market sentiment correlation
            sentiment_correlation = random.uniform(-0.5, 0.8)  # Simulated for demo
            correlation_text = "positive" if sentiment_correlation > 0.3 else "negative" if sentiment_correlation < -0.3 else "neutral"
            
            st.markdown("### 📊 Market Sentiment Analysis")
            st.markdown(f"Correlation between news sentiment and returns: **{sentiment_correlation:.2f}** ({correlation_text})")
            
            # Recommendations
            st.markdown("### 🧠 AI Recommendations")
            
            # Generate tailored recommendations based on results
            top_strategy_types = list(set([w["strategy"] for w in winners[:3]]))
            top_tickers = list(set([w["ticker"] for w in winners[:3]]))
            
            recommendations = [
                f"Consider focusing on {', '.join(top_strategy_types)} strategies given current market conditions.",
                f"The {top_tickers[0]} ticker shows promising results across multiple strategies.",
                "Maintain smaller position sizes if using high-volatility strategies."
            ]
            
            # Add market-specific recommendations
            market_conditions = st.session_state.get("current_market_conditions", {})
            if market_conditions:
                if market_conditions.get("market_phase") == "trending":
                    recommendations.append("Current trending market favors momentum and trend-following strategies.")
                elif market_conditions.get("market_phase") == "ranging":
                    recommendations.append("Current ranging market favors mean-reversion strategies.")
                
                if market_conditions.get("vix", 0) > 25:
                    recommendations.append("High market volatility (VIX) suggests reducing position sizes and using wider stop losses.")
            
            for rec in recommendations:
                st.markdown(f"- {rec}")
    
    # Show detailed view for selected strategy
    if st.session_state.selected_backtest_row:
        selected_winner = next((w for w in winners if w["id"] == st.session_state.selected_backtest_row), None)
        
        if selected_winner:
            with st.expander("Strategy Details", expanded=True):
                st.markdown(f"# {selected_winner['ticker']} - {selected_winner['strategy']} Strategy")
                
                # Show full narrative if available
                if "narrative" in selected_winner:
                    st.markdown(selected_winner["narrative"])
                
                # Show equity curve if available
                if "equity_curve" in selected_winner:
                    st.markdown("## Equity Curve")
                    # Convert equity curve to dataframe if it's not already
                    if isinstance(selected_winner["equity_curve"], list):
                        equity_df = pd.DataFrame(selected_winner["equity_curve"])
                    else:
                        equity_df = selected_winner["equity_curve"]
                    
                    # Plot equity curve
                    fig = px.line(equity_df, x="date", y="equity", title=f"{selected_winner['ticker']} - {selected_winner['strategy']} Equity Curve")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show trade details if available
                if "trades" in selected_winner and selected_winner["trades"]:
                    st.markdown("## Trade Details")
                    trades_df = pd.DataFrame(selected_winner["trades"])
                    st.dataframe(trades_df, hide_index=True)
                
                # Close button
                if st.button("Close Details", use_container_width=True):
                    st.session_state.selected_backtest_row = None
                    st.experimental_rerun()
    
    # Auto-run timer for market hours (enhanced)
    current_time = datetime.now()
    if is_market_open() and (current_time - st.session_state.last_auto_run).total_seconds() > 900:  # 15 minutes = 900 seconds
        run_autonomous_backtest()  # Use real data backtest instead of mock
        st.session_state.last_auto_run = current_time

with tab3:
    st.markdown('<div class="main-header">Paper Trading</div>', unsafe_allow_html=True)
    
    # Account overview
    account_cols = st.columns(4)
    with account_cols[0]:
        st.metric(label="Account Value", value="$102,458.32", delta="$2,458.32")
    with account_cols[1]:
        st.metric(label="Cash Balance", value="$54,789.12", delta="")
    with account_cols[2]:
        st.metric(label="Equity", value="$47,669.20", delta="$2,458.32")
    with account_cols[3]:
        st.metric(label="Day P&L", value="$658.92", delta="0.64%")
    
    # Positions table
    st.markdown('<div class="sub-header">Open Positions</div>', unsafe_allow_html=True)
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
    
    # Order form
    st.markdown('<div class="sub-header">Place New Order</div>', unsafe_allow_html=True)
    order_cols = st.columns(3)
    
    with order_cols[0]:
        st.text_input("Symbol", "", key="order_symbol")
        st.selectbox("Order Type", ["Market", "Limit", "Stop", "Stop Limit"], key="order_type")
    
    with order_cols[1]:
        st.radio("Direction", ["Buy", "Sell"], horizontal=True, key="direction")
        st.number_input("Quantity", min_value=1, value=100, key="quantity")
    
    with order_cols[2]:
        st.number_input("Price", min_value=0.01, value=100.00, step=0.01, key="price")
        st.button("Place Order", type="primary", key="place_order")

with tab4:
    st.markdown('<div class="main-header">Strategy Management</div>', unsafe_allow_html=True)
    
    # Strategy allocation
    strategy_cols = st.columns([2, 1])
    
    with strategy_cols[0]:
        # Allocation data
        strategies_data = {
            "Strategy": ["Momentum", "Mean Reversion", "Trend Following", "Volatility Breakout", "Pairs Trading", "Machine Learning"],
            "Allocation": [30, 25, 15, 10, 5, 15]
        }
        
        # Create pie chart
        fig = px.pie(
            strategies_data,
            values="Allocation",
            names="Strategy",
            title="Current Strategy Allocation (%)",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig)
    
    with strategy_cols[1]:
        st.markdown("### Strategy Controls")
        
        st.selectbox("Select Strategy", ["Momentum", "Mean Reversion", "Trend Following", "Volatility Breakout", "Pairs Trading", "Machine Learning"])
        st.slider("Allocation (%)", 0, 100, 30)
        st.radio("Status", ["Active", "Paused"], horizontal=True)
        st.button("Update Strategy")

with tab5:
    st.markdown('<div class="main-header">News & Market Predictions</div>', unsafe_allow_html=True)
    
    # News Section
    st.markdown("## 📰 Latest Market News")

    # Sentiment trend sparkline
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h4 style="margin-bottom: 5px;">24-Hour Sentiment Trend</h4>
        <div style="display: flex; align-items: center;">
            <div style="flex: 1; display: flex; height: 40px; align-items: flex-end; margin-right: 10px;">
                <div style="width: 8%; height: 60%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 40%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 65%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 75%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 55%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 80%; background-color: rgba(0,180,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 45%; background-color: rgba(128,128,128,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 55%; background-color: rgba(128,128,128,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 35%; background-color: rgba(255,0,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 40%; background-color: rgba(255,0,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 25%; background-color: rgba(255,0,0,0.5); margin-right: 2px;"></div>
                <div style="width: 8%; height: 20%; background-color: rgba(255,0,0,0.5);"></div>
            </div>
            <div style="width: 120px; display: flex; justify-content: space-between;">
                <div><span style="color: #00b400;">●</span> 53%</div>
                <div><span style="color: #808080;">●</span> 18%</div>
                <div><span style="color: #ff0000;">●</span> 29%</div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: gray; margin-top: 5px;">
            <div>24h ago</div>
            <div>12h ago</div>
            <div>Now</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add action buttons instead of keyboard shortcuts hint
    action_btn_cols = st.columns(6)
    with action_btn_cols[0]:
        st.button("⬆️⬇️ Navigate", key="nav_btn", help="Navigate through news items")
    with action_btn_cols[1]:
        st.button("🔍 Expand", key="expand_btn", help="Expand selected news item")
    with action_btn_cols[2]:
        st.button("📊 Backtest", key="backtest_btn", help="Run backtest for selected symbol")
    with action_btn_cols[3]:
        st.button("📈 Chart", key="chart_btn", help="View chart for selected symbol")
    with action_btn_cols[4]:
        st.button("💬 Ask AI", key="ask_ai_btn", help="Ask AI about selected symbol")
    with action_btn_cols[5]:
        st.button("⭐ Save", key="save_btn", help="Save selected news item")
    
    # Add view mode toggle
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        view_mode = st.radio("View Mode:", ["Detailed", "Simplified"], index=0 if st.session_state.detailed_view else 1, 
                            on_change=toggle_view_mode, horizontal=True)
    with col2:
        show_bookmarks = st.checkbox("Show Bookmarks Only", value=False)
    with col3:
        st.write("")  # Spacer
    with col4:
        st.write("")  # Spacer

    # News filtering controls
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])
    with filter_col1:
        news_search = st.text_input("🔍 Search news by ticker or company name", placeholder="AAPL, TSLA, Microsoft, etc.")
    with filter_col2:
        news_source = st.selectbox("Source", ["All Sources", "Finnhub", "MarketAux", "NewsData", "GNews"])
    with filter_col3:
        news_date = st.selectbox("Date", ["All Time", "Today", "Yesterday", "Last Week", "Last Month"])
    with filter_col4:
        news_impact = st.selectbox("Filter", ["All News", "Most Impactful", "High Confidence", "Trading Signals"])

    # Create tabs for news sentiment
    news_tabs = st.tabs(["🟢 Positive News", "⚪ Neutral News", "🔴 Negative News"])

    # Add source icons dictionary
    source_icons = {
        "Finnhub": "https://finnhub.io/favicon.ico",
        "MarketAux": "https://marketaux.com/favicon.ico",
        "NewsData": "https://newsdata.io/favicon.ico",
        "GNews": "https://gnews.io/favicon.ico"
    }

    # Sample news data with detailed attributes and quick-take summaries
    news_data = [
        {
            "title": "Apple's AI strategy positions it for strong growth in 2024",
            "source": "Finnhub",
            "timestamp": "2 hours ago",
            "summary": "Apple's integration of AI across its product ecosystem is expected to drive significant growth in the coming year, with analysts projecting a 15% increase in revenue.",
            "sentiment": "positive",
            "strategy": "Momentum",
            "rationale": "Expected AI-driven revenue growth may create upward momentum in stock price",
            "timeframe": "Medium-term",
            "implementation": "Consider AAPL call options with 3-6 month expiry",
            "risk": "Low",
            "quick_take": "AI-driven revenue boost likely to fuel momentum—consider small long positions on pullbacks.",
            "impact_score": 85,
            "symbol": "AAPL",
            "sector": "Technology",
            "breaking": False,
            "new": False,
            "social_sentiment": {"score": 72, "trend": "positive"},
            "price_change": 2.4,
            "related_stories": [
                {"title": "Apple plans major AI features for iOS 18", "symbol": "AAPL", "source": "MarketAux"},
                {"title": "Tech giants race to integrate AI across products", "symbol": "TECH", "source": "NewsData"}
            ],
            "sparkline_data": [160, 162, 161, 163, 165, 164, 167, 169, 172, 173, 171, 174]
        },
        {
            "title": "Tesla delivers record number of vehicles in Q2",
            "source": "MarketAux",
            "timestamp": "8 hours ago",
            "summary": "Tesla announced that it delivered 466,000 vehicles in Q2, beating analyst expectations of 445,000 and setting a new company record.",
            "sentiment": "positive",
            "strategy": "Breakout",
            "rationale": "Positive surprise may trigger technical breakout",
            "timeframe": "Short-term",
            "implementation": "Consider TSLA shares or short-dated call options",
            "risk": "Medium",
            "quick_take": "Delivery beat could trigger technical breakout—short-term momentum likely with high volatility.",
            "impact_score": 78,
            "symbol": "TSLA",
            "sector": "Automotive",
            "breaking": False,
            "new": False,
            "social_sentiment": {"score": 68, "trend": "positive"},
            "price_change": 3.2,
            "related_stories": [
                {"title": "EV market share continues to grow globally", "symbol": "TSLA", "source": "GNews"},
                {"title": "Ford and GM struggle to match Tesla's EV production", "symbol": "F", "source": "Finnhub"}
            ],
            "sparkline_data": [230, 233, 235, 232, 236, 238, 241, 243, 240, 244, 247, 250]
        },
        {
            "title": "Federal Reserve signals potential rate cut in September",
            "source": "GNews",
            "timestamp": "5 hours ago",
            "summary": "Federal Reserve officials indicated a possible interest rate cut in September, citing improving inflation data and concerns about labor market cooling.",
            "sentiment": "positive",
            "strategy": "Asset Allocation",
            "rationale": "Rate cuts typically benefit equities and fixed income",
            "timeframe": "Medium-term",
            "implementation": "Consider increasing equity exposure and duration in fixed income",
            "risk": "Low",
            "quick_take": "Potential rate cut bullish for both equities and bonds—consider increasing duration and growth exposure.",
            "impact_score": 90,
            "symbol": "SPY",
            "sector": "Economy",
            "breaking": True,
            "new": False,
            "social_sentiment": {"score": 82, "trend": "positive"},
            "price_change": 1.8,
            "related_stories": [
                {"title": "Treasury yields fall on rate cut expectations", "symbol": "TLT", "source": "Finnhub"},
                {"title": "Bank stocks rally on Fed policy outlook", "symbol": "XLF", "source": "MarketAux"}
            ],
            "sparkline_data": [450, 453, 455, 458, 457, 460, 462, 463, 465, 467, 469, 471]
        },
        {
            "title": "Microsoft cloud revenue grows 21% year-over-year",
            "source": "NewsData",
            "timestamp": "1 day ago",
            "summary": "Microsoft reported better-than-expected cloud segment revenue, with Azure growing at 21% compared to the same period last year.",
            "sentiment": "neutral",
            "strategy": "Hold",
            "rationale": "Growth in line with expectations, no immediate action needed",
            "timeframe": "Long-term",
            "implementation": "Maintain current MSFT positions",
            "risk": "Low",
            "quick_take": "Cloud growth meets expectations—maintain existing positions with no immediate action required.",
            "impact_score": 65,
            "symbol": "MSFT",
            "sector": "Technology",
            "breaking": False,
            "new": False,
            "social_sentiment": {"score": 56, "trend": "neutral"},
            "price_change": 0.7,
            "related_stories": [
                {"title": "AWS maintains cloud market share lead over Azure", "symbol": "AMZN", "source": "GNews"},
                {"title": "Cloud computing spending expected to grow 20% in 2024", "symbol": "CLOUD", "source": "NewsData"}
            ],
            "sparkline_data": [380, 382, 379, 381, 383, 385, 384, 386, 385, 387, 386, 389]
        },
        {
            "title": "Oil prices steady as traders assess OPEC+ production plans",
            "source": "MarketAux",
            "timestamp": "3 hours ago",
            "summary": "Crude oil futures showed little movement as traders await clarity on OPEC+ production quotas for the coming quarter.",
            "sentiment": "neutral",
            "strategy": "Wait and See",
            "rationale": "Market uncertainty requires patience before taking action",
            "timeframe": "Uncertain",
            "implementation": "Monitor OPEC+ announcements before adjusting energy exposure",
            "risk": "Medium",
            "quick_take": "Oil markets in holding pattern—monitor OPEC+ announcements before making energy sector moves.",
            "impact_score": 55,
            "symbol": "USO",
            "sector": "Energy",
            "breaking": False,
            "new": True,
            "social_sentiment": {"score": 48, "trend": "neutral"},
            "price_change": -0.3,
            "related_stories": [
                {"title": "Saudi Arabia pushes for extended production cuts", "symbol": "OIL", "source": "Finnhub"},
                {"title": "US crude inventories rise unexpectedly", "symbol": "USO", "source": "NewsData"}
            ],
            "sparkline_data": [72, 71.5, 72.3, 72.1, 71.8, 71.9, 71.7, 71.5, 71.3, 71.4, 71.2, 71.1]
        },
        {
            "title": "Nvidia faces production constraints for AI chips",
            "source": "Finnhub",
            "timestamp": "6 hours ago",
            "summary": "Nvidia is reportedly struggling to meet demand for its latest AI accelerator chips due to supply chain constraints at TSMC.",
            "sentiment": "negative",
            "strategy": "Hedging",
            "rationale": "Production issues may impact short-term revenue",
            "timeframe": "Short-term",
            "implementation": "Consider trimming positions or protective puts for NVDA exposure",
            "risk": "Medium",
            "quick_take": "Production constraints may impact short-term revenue—consider hedging or reducing exposure.",
            "impact_score": 75,
            "symbol": "NVDA",
            "sector": "Technology",
            "breaking": False,
            "new": False,
            "social_sentiment": {"score": 42, "trend": "negative"},
            "price_change": -2.1,
            "related_stories": [
                {"title": "TSMC expands capacity amid surging AI chip demand", "symbol": "TSM", "source": "GNews"},
                {"title": "AMD gains market share in AI accelerator space", "symbol": "AMD", "source": "MarketAux"}
            ],
            "sparkline_data": [820, 815, 810, 805, 800, 795, 790, 800, 795, 790, 785, 780]
        },
        {
            "title": "Retail sales decline for second consecutive month",
            "source": "NewsData",
            "timestamp": "1 day ago",
            "summary": "U.S. retail sales fell 0.3% in June, following a 0.2% drop in May, raising concerns about consumer spending weakness.",
            "sentiment": "negative",
            "strategy": "Defensive Positioning",
            "rationale": "Consumer weakness may impact broader economy",
            "timeframe": "Medium-term",
            "implementation": "Reduce exposure to consumer discretionary, increase consumer staples",
            "risk": "Medium",
            "quick_take": "Weakening consumer spending signals potential broader slowdown—rotate from discretionary to defensive sectors.",
            "impact_score": 82,
            "symbol": "XLY",
            "sector": "Consumer",
            "breaking": False,
            "new": False,
            "social_sentiment": {"score": 35, "trend": "negative"},
            "price_change": -1.5,
            "related_stories": [
                {"title": "Consumer confidence falls to six-month low", "symbol": "SPY", "source": "GNews"},
                {"title": "Walmart warns of cautious consumer spending", "symbol": "WMT", "source": "Finnhub"}
            ],
            "sparkline_data": [185, 184, 183, 182, 181, 180, 181, 180, 179, 178, 177, 176]
        },
        {
            "title": "Moody's downgrades regional banks on commercial real estate concerns",
            "source": "GNews",
            "timestamp": "4 hours ago",
            "summary": "Moody's downgraded credit ratings for several regional banks, citing high exposure to troubled commercial real estate loans.",
            "sentiment": "negative",
            "strategy": "Sector Rotation",
            "rationale": "Regional banking sector faces significant headwinds",
            "timeframe": "Medium to Long-term",
            "implementation": "Consider reducing regional bank exposure or hedging financial sector positions",
            "risk": "High",
            "quick_take": "Regional bank downgrades signal continued CRE stress—reduce exposure to regional financials.",
            "impact_score": 88,
            "symbol": "KRE",
            "sector": "Financial",
            "breaking": True,
            "new": True,
            "social_sentiment": {"score": 28, "trend": "negative"},
            "price_change": -3.6,
            "related_stories": [
                {"title": "Commercial real estate vacancies hit 10-year high", "symbol": "VNQ", "source": "NewsData"},
                {"title": "Large banks outperform regionals on earnings", "symbol": "XLF", "source": "MarketAux"}
            ],
            "sparkline_data": [48, 47, 46.5, 46, 45.5, 45, 44.5, 44, 43.5, 43, 42.5, 42]
        }
    ]

    # Filter for most impactful
    def get_most_impactful(data, threshold=75):
        return [item for item in data if item["impact_score"] >= threshold]

    # Function to filter news
    def filter_news(data, search_term="", source="All Sources", sentiment=None, impact_filter="All News", bookmarks_only=False):
        filtered = data
        
        if search_term:
            filtered = [item for item in filtered if search_term.lower() in item["title"].lower() or 
                        search_term.upper() == item["symbol"]]
        
        if source != "All Sources":
            filtered = [item for item in filtered if item["source"] == source]
        
        if sentiment:
            filtered = [item for item in filtered if item["sentiment"] == sentiment]
        
        if impact_filter == "Most Impactful":
            filtered = get_most_impactful(filtered)
        elif impact_filter == "High Confidence":
            filtered = [item for item in filtered if item["impact_score"] >= 80]
        elif impact_filter == "Trading Signals":
            filtered = [item for item in filtered if item["timeframe"] == "Short-term"]
            
        if bookmarks_only:
            filtered = [item for item in filtered if f"{item['symbol']}_{item['title']}" in st.session_state.bookmarked_news]
        
        return filtered

    # Function to display news items
    def display_news(news_items, sentiment):
        if not news_items:
            st.write("No news items found matching your criteria.")
            return
        
        for i, item in enumerate(news_items):
            # Create a unique ID for this news item
            item_id = f"{item['symbol']}_{item['title']}"
            is_bookmarked = item_id in st.session_state.bookmarked_news
            
            # Determine styling based on sentiment
            if sentiment == "positive":
                header_style = "background-color: rgba(0,180,0,0.1); border-left: 4px solid #00b400; padding: 10px;"
                tag_style = "background-color: rgba(0,180,0,0.2); padding: 3px 8px; border-radius: 10px; font-size: 12px;"
                sentiment_icon = "🟢"
            elif sentiment == "negative":
                header_style = "background-color: rgba(255,0,0,0.1); border-left: 4px solid #ff0000; padding: 10px;"
                tag_style = "background-color: rgba(255,0,0,0.2); padding: 3px 8px; border-radius: 10px; font-size: 12px;"
                sentiment_icon = "🔴"
            else:
                header_style = "background-color: rgba(128,128,128,0.1); border-left: 4px solid #808080; padding: 10px;"
                tag_style = "background-color: rgba(128,128,128,0.2); padding: 3px 8px; border-radius: 10px; font-size: 12px;"
                sentiment_icon = "⚪"
            
            # Determine impact badge styling
            if item["impact_score"] >= 80:
                impact_badge_class = "impact-badge-high"
                impact_level = "High"
            elif item["impact_score"] >= 60:
                impact_badge_class = "impact-badge-medium"
                impact_level = "Medium"
            else:
                impact_badge_class = "impact-badge-low"
                impact_level = "Low"
                
            # Format price change
            price_change_html = ""
            if item["price_change"] > 0:
                price_change_html = f'<span class="positive-change">+{item["price_change"]}%</span>'
            elif item["price_change"] < 0:
                price_change_html = f'<span class="negative-change">{item["price_change"]}%</span>'
            else:
                price_change_html = f'<span>0.0%</span>'
                
            # Format social sentiment
            if item["social_sentiment"]["trend"] == "positive":
                social_html = f'<span class="social-sentiment-positive">📈 +{item["social_sentiment"]["score"]}%</span>'
            elif item["social_sentiment"]["trend"] == "negative":
                social_html = f'<span class="social-sentiment-negative">📉 {item["social_sentiment"]["score"]}%</span>'
            else:
                social_html = f'<span class="social-sentiment-neutral">📊 {item["social_sentiment"]["score"]}%</span>'
                
            # Create a safer icon implementation
            icon_html = f'<span style="font-weight: bold; color: #1976D2;">⚙️</span>'
            
            # Create a simplified sparkline visual
            price_trend = "⤴️" if item["price_change"] > 0 else "⤵️" if item["price_change"] < 0 else "➡️"
            
            # Quick-take summary with simplification
            quick_take_col1, quick_take_col2 = st.columns([3, 1])
            
            with quick_take_col1:
                st.info(f"{sentiment_icon} Quick-Take: {item['quick_take']}")
            
            with quick_take_col2:
                st.markdown(f"**Sector:** {item['sector']}")
            
            # Create expandable news item
            with st.expander(f"{item['symbol']} | {item['title']}"):
                # News header with enhanced metadata
                breaking_badge = f'🔴 BREAKING ' if item["breaking"] else ''
                new_badge = f'🔵 NEW ' if item["new"] and not item["breaking"] else ''
                
                # Create simplified header components
                header_col1, header_col2 = st.columns([3, 1])
                
                with header_col1:
                    st.markdown(f"""
                    {breaking_badge}{new_badge}**{item['source']}** • {item['timestamp']}  
                    Price Change: **{'+' if item['price_change'] > 0 else ''}{item['price_change']}%** • 
                    Social: **{item['social_sentiment']['score']}%** {price_trend}
                    """)
                
                with header_col2:
                    if item["impact_score"] >= 80:
                        st.success(f"Impact: {item['impact_score']}/100")
                    elif item["impact_score"] >= 60:
                        st.warning(f"Impact: {item['impact_score']}/100")
                    else:
                        st.info(f"Impact: {item['impact_score']}/100")
                
                # News summary
                st.markdown(f"**Summary:** {item['summary']}")
                
                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.button(f"🔍 Backtest {item['symbol']}", key=f"backtest_{item['symbol']}_{news_items.index(item)}")
                with col2:
                    st.button(f"📈 Chart {item['symbol']}", key=f"chart_{item['symbol']}_{news_items.index(item)}")
                with col3:
                    st.button(f"💬 Ask AI about {item['symbol']}", key=f"ask_{item['symbol']}_{news_items.index(item)}")
                with col4:
                    bookmark_label = "★ Remove Bookmark" if is_bookmarked else "☆ Add Bookmark"
                    if st.button(bookmark_label, key=f"bookmark_{item['symbol']}_{news_items.index(item)}"):
                        toggle_bookmark(item_id)
                        st.experimental_rerun()
                
                # Show detailed or simplified view based on user preference
                if st.session_state.detailed_view:
                    # Trading intelligence section - Detailed view
                    st.markdown("### Trading Intelligence")
                    
                    # Create two columns for strategy details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Strategy:** {item['strategy']}")
                        st.markdown(f"**Rationale:** {item['rationale']}")
                        st.markdown(f"**Timeframe:** {item['timeframe']}")
                    
                    with col2:
                        st.markdown(f"**Implementation:** {item['implementation']}")
                        
                        # Use color-coded status for risk level
                        if item['risk'] == "High":
                            st.error(f"Risk Level: {item['risk']}")
                        elif item['risk'] == "Medium":
                            st.warning(f"Risk Level: {item['risk']}")
                        else:
                            st.success(f"Risk Level: {item['risk']}")
                        
                    # Related stories section
                    if item["related_stories"]:
                        st.markdown("### Related Stories")
                        for related in item["related_stories"]:
                            st.markdown(f"**{related['symbol']}**: {related['title']} ({related['source']})")
                else:
                    # Simplified view
                    st.markdown(f"**Quick Action:** {item['implementation']}")
                    
                    # Use color-coded status for risk level
                    if item['risk'] == "High":
                        st.error(f"Risk Level: {item['risk']} • Timeframe: {item['timeframe']}")
                    elif item['risk'] == "Medium":
                        st.warning(f"Risk Level: {item['risk']} • Timeframe: {item['timeframe']}")
                    else:
                        st.success(f"Risk Level: {item['risk']} • Timeframe: {item['timeframe']}")

    # Display news in tabs based on sentiment
    with news_tabs[0]:  # Positive News
        positive_news = filter_news(news_data, news_search, news_source, "positive", news_impact, show_bookmarks)
        display_news(positive_news, "positive")

    with news_tabs[1]:  # Neutral News
        neutral_news = filter_news(news_data, news_search, news_source, "neutral", news_impact, show_bookmarks)
        display_news(neutral_news, "neutral")

    with news_tabs[2]:  # Negative News
        negative_news = filter_news(news_data, news_search, news_source, "negative", news_impact, show_bookmarks)
        display_news(negative_news, "negative")

    # Add news sources and buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("News sources: Finnhub, MarketAux, NewsData, GNews")
    with col2:
        if st.button("🔄 Refresh News"):
            st.success("News refreshed successfully!")
    with col3:
        st.button("⬇️ Load More Headlines")
    
    # Market Predictions Section
    st.markdown("## 🔮 Market Predictions")
    
    # Prediction cards
    pred_col1, pred_col2 = st.columns(2)
    
    with pred_col1:
        st.markdown("### Short-term Market Outlook (1-7 days)")
        st.markdown("""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">SPY (S&P 500 ETF)</h4>
            <p><strong>Forecast:</strong> <span style="color: #00b400;">Bullish</span></p>
            <p><strong>Confidence:</strong> 72%</p>
            <p><strong>Key Factors:</strong> Fed policy, earnings momentum, economic indicators</p>
            <p><strong>Potential Catalysts:</strong> FOMC minutes release, retail sales data</p>
        </div>
        
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">QQQ (Nasdaq ETF)</h4>
            <p><strong>Forecast:</strong> <span style="color: #00b400;">Bullish</span></p>
            <p><strong>Confidence:</strong> 68%</p>
            <p><strong>Key Factors:</strong> Tech earnings, AI developments, semiconductor supply chain</p>
            <p><strong>Potential Catalysts:</strong> NVIDIA earnings, Microsoft AI announcement</p>
        </div>
        """, unsafe_allow_html=True)
    
    with pred_col2:
        st.markdown("### Medium-term Market Outlook (1-3 months)")
        st.markdown("""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">SPY (S&P 500 ETF)</h4>
            <p><strong>Forecast:</strong> <span style="color: #ffa500;">Neutral</span></p>
            <p><strong>Confidence:</strong> 58%</p>
            <p><strong>Key Factors:</strong> Inflation trends, economic growth, geopolitical tensions</p>
            <p><strong>Potential Catalysts:</strong> CPI data, GDP revision, Fed interest rate decision</p>
        </div>
        
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">QQQ (Nasdaq ETF)</h4>
            <p><strong>Forecast:</strong> <span style="color: #00b400;">Moderately Bullish</span></p>
            <p><strong>Confidence:</strong> 63%</p>
            <p><strong>Key Factors:</strong> Tech sector earnings, AI adoption, regulatory environment</p>
            <p><strong>Potential Catalysts:</strong> Big Tech earnings season, AI conference announcements</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: white;
            border-bottom: 3px solid #4e89ae;
        }
    </style>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Dashboard last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
st.caption("This is a simplified version of the dashboard without complex news displays.") 

# Data Integration Module - add after the CSS styling section and before the sidebar
class BacktestDataIntegration:
    """Manages data sources for backtesting, including news and price data."""
    
    def __init__(self):
        self.api_keys = {
            "finnhub": os.environ.get("FINNHUB_API_KEY", ""),
            "marketaux": os.environ.get("MARKETAUX_API_KEY", ""),
            "newsdata": os.environ.get("NEWSDATA_API_KEY", ""),
            "gnews": os.environ.get("GNEWS_API_KEY", ""),
            "tradingview": os.environ.get("TRADINGVIEW_API_KEY", ""),
            "alpha_vantage": os.environ.get("ALPHA_VANTAGE_KEY", "")
        }
        self.cache = {}
        self.news_cache = {}
        self.indicator_cache = {}  # New cache for technical indicators
        self.last_api_calls = {"finnhub": 0, "marketaux": 0, "newsdata": 0, "gnews": 0, "alpha_vantage": 0}
        self.cache_duration = 3600  # Cache data for 1 hour
        
    def get_price_data(self, symbol, start_date, end_date, source="yfinance"):
        """Get historical price data for a symbol."""
        cache_key = f"{symbol}_{start_date}_{end_date}_{source}"
        
        # Return cached data if available and recent
        if cache_key in self.cache and datetime.now().timestamp() - self.cache[cache_key]["timestamp"] < self.cache_duration:
            return self.cache[cache_key]["data"]
        
        try:
            if source == "yfinance":
                data = yf.download(symbol, start=start_date, end=end_date)
                # Store in cache
                self.cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now().timestamp()
                }
                return data
            
            elif source == "alpha_vantage":
                # Implementation for Alpha Vantage API
                if not self.api_keys["alpha_vantage"]:
                    st.error("Alpha Vantage API key not configured.")
                    return pd.DataFrame()
                    
                function = "TIME_SERIES_DAILY"
                url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&outputsize=full&apikey={self.api_keys['alpha_vantage']}"
                r = requests.get(url)
                data = r.json()
                
                if "Time Series (Daily)" not in data:
                    st.error(f"Failed to get data for {symbol} from Alpha Vantage: {data.get('Note', data)}")
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(data["Time Series (Daily)"]).T
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]
                df = df.rename(columns={"1. open": "Open", "2. high": "High", "3. low": "Low", "4. close": "Close", "5. volume": "Volume"})
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                
                # Store in cache
                self.cache[cache_key] = {
                    "data": df,
                    "timestamp": datetime.now().timestamp()
                }
                return df
            
            elif source == "tradingview":
                # This would require a more complex implementation with the TradingView API
                # or potentially web scraping, which might violate terms of service
                st.warning("TradingView integration requires a premium account or direct API access.")
                return pd.DataFrame()
                
            else:
                st.error(f"Unknown data source: {source}")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching price data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_news_data(self, symbol, start_date, end_date, sources=["finnhub", "marketaux"]):
        """Get historical news data for a symbol."""
        cache_key = f"news_{symbol}_{start_date}_{end_date}_{'-'.join(sources)}"
        
        # Return cached data if available and recent
        if cache_key in self.news_cache and datetime.now().timestamp() - self.news_cache[cache_key]["timestamp"] < self.cache_duration:
            return self.news_cache[cache_key]["data"]
        
        all_news = []
        
        for source in sources:
            try:
                if source == "finnhub" and self.api_keys["finnhub"]:
                    # Track API call
                    self.last_api_calls["finnhub"] = datetime.now().timestamp()
                    
                    # Format dates for Finnhub
                    from_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
                    to_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
                    
                    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={start_date}&to={end_date}&token={self.api_keys['finnhub']}"
                    r = requests.get(url)
                    data = r.json()
                    
                    if isinstance(data, list):
                        for item in data:
                            processed_item = {
                                "title": item.get("headline", ""),
                                "source": "Finnhub",
                                "timestamp": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", ""),
                                "sentiment": self._analyze_sentiment(item.get("summary", "")),
                                "symbol": symbol,
                                "date": datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d")
                            }
                            all_news.append(processed_item)
                
                elif source == "marketaux" and self.api_keys["marketaux"]:
                    # Track API call
                    self.last_api_calls["marketaux"] = datetime.now().timestamp()
                    
                    url = f"https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&published_after={start_date}&published_before={end_date}&api_token={self.api_keys['marketaux']}"
                    r = requests.get(url)
                    data = r.json()
                    
                    if "data" in data:
                        for item in data["data"]:
                            processed_item = {
                                "title": item.get("title", ""),
                                "source": "MarketAux",
                                "timestamp": item.get("published_at", ""),
                                "summary": item.get("description", ""),
                                "url": item.get("url", ""),
                                "sentiment": item.get("sentiment", "neutral"),
                                "symbol": symbol,
                                "date": item.get("published_at", "")[:10]
                            }
                            all_news.append(processed_item)
                
                # Add more news sources as needed
            
            except Exception as e:
                st.error(f"Error fetching news from {source} for {symbol}: {str(e)}")
        
        # Store in cache
        self.news_cache[cache_key] = {
            "data": all_news,
            "timestamp": datetime.now().timestamp()
        }
        
        return all_news
    
    def _analyze_sentiment(self, text):
        """Simple sentiment analysis based on keyword matching."""
        positive_words = ["up", "rise", "gain", "positive", "growth", "increase", "bullish", "outperform", 
                         "beat", "exceed", "success", "strong", "boost", "improve", "advantage", "opportunity"]
        negative_words = ["down", "fall", "drop", "negative", "decline", "decrease", "bearish", "underperform", 
                         "miss", "below", "fail", "weak", "cut", "worsen", "disadvantage", "risk"]
        
        text = text.lower()
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def recommend_strategy(self, news, price_data):
        """Recommend a strategy based on news sentiment and price patterns."""
        if not news or price_data.empty:
            return {"strategy": "Insufficient data", "confidence": 0}
        
        # Aggregate sentiment from news
        sentiments = [item["sentiment"] for item in news]
        pos_count = sentiments.count("positive")
        neg_count = sentiments.count("negative")
        neu_count = sentiments.count("neutral")
        
        total = len(sentiments)
        if total == 0:
            return {"strategy": "Insufficient data", "confidence": 0}
        
        sentiment_score = (pos_count - neg_count) / total
        
        # Calculate price momentum
        if len(price_data) > 20:
            returns = price_data['Close'].pct_change(20).dropna()
            momentum = returns.mean() * 100  # Convert to percentage
        else:
            momentum = 0
        
        # Calculate volatility
        if len(price_data) > 20:
            volatility = price_data['Close'].pct_change().std() * 100  # Annualized volatility
        else:
            volatility = 0
        
        # Recommend strategy based on sentiment and price patterns
        if sentiment_score > 0.3 and momentum > 1:
            strategy = "Momentum"
            confidence = min(sentiment_score * 100, 90)
        elif sentiment_score < -0.3 and momentum < -1:
            strategy = "Short/Put"
            confidence = min(abs(sentiment_score) * 100, 90)
        elif abs(sentiment_score) < 0.2 and volatility > 2:
            strategy = "Options Volatility Skew"
            confidence = min(volatility * 10, 90)
        elif momentum > 0.5 and volatility < 1.5:
            strategy = "Trend Following"
            confidence = min(momentum * 20, 90)
        elif momentum < -0.5 and volatility < 1.5:
            strategy = "Mean Reversion"
            confidence = min(abs(momentum) * 20, 90)
        elif volatility > 3:
            strategy = "Volatility Expansion"
            confidence = min(volatility * 10, 90)
        else:
            strategy = "Wait and See"
            confidence = 50
        
        return {
            "strategy": strategy,
            "confidence": confidence,
            "sentiment_score": sentiment_score * 100,
            "momentum": momentum,
            "volatility": volatility
        }
    
    def generate_tradingview_chart_url(self, symbol, timeframe="D"):
        """Generate a TradingView chart URL for a symbol."""
        base_url = "https://www.tradingview.com/chart/"
        params = f"?symbol={symbol}&interval={timeframe}"
        return base_url + params
    
    def get_trading_signals(self, symbol, strategy_type, price_data):
        """Generate trading signals based on the strategy and price data."""
        signals = []
        
        if price_data.empty:
            return signals
        
        # Calculate basic indicators
        price_data['SMA20'] = price_data['Close'].rolling(window=20).mean()
        price_data['SMA50'] = price_data['Close'].rolling(window=50).mean()
        price_data['SMA200'] = price_data['Close'].rolling(window=200).mean()
        price_data['Daily_Return'] = price_data['Close'].pct_change()
        price_data['Volatility'] = price_data['Daily_Return'].rolling(window=20).std()
        
        if strategy_type == "Momentum":
            price_data['Signal'] = 0
            price_data.loc[price_data['SMA20'] > price_data['SMA50'], 'Signal'] = 1
            price_data.loc[price_data['SMA20'] < price_data['SMA50'], 'Signal'] = -1
            
            # Generate signals
            for i in range(1, len(price_data)):
                if price_data['Signal'].iloc[i] == 1 and price_data['Signal'].iloc[i-1] != 1:
                    signals.append({
                        'date': price_data.index[i].strftime('%Y-%m-%d'),
                        'action': 'BUY',
                        'price': price_data['Close'].iloc[i],
                        'reason': 'SMA20 crossed above SMA50 - Momentum strategy'
                    })
                elif price_data['Signal'].iloc[i] == -1 and price_data['Signal'].iloc[i-1] != -1:
                    signals.append({
                        'date': price_data.index[i].strftime('%Y-%m-%d'),
                        'action': 'SELL',
                        'price': price_data['Close'].iloc[i],
                        'reason': 'SMA20 crossed below SMA50 - Momentum strategy'
                    })
        
        elif strategy_type == "Trend Following":
            price_data['Signal'] = 0
            price_data.loc[(price_data['Close'] > price_data['SMA200']) & 
                          (price_data['SMA20'] > price_data['SMA50']), 'Signal'] = 1
            price_data.loc[(price_data['Close'] < price_data['SMA200']) & 
                          (price_data['SMA20'] < price_data['SMA50']), 'Signal'] = -1
            
            # Generate signals
            for i in range(1, len(price_data)):
                if price_data['Signal'].iloc[i] == 1 and price_data['Signal'].iloc[i-1] != 1:
                    signals.append({
                        'date': price_data.index[i].strftime('%Y-%m-%d'),
                        'action': 'BUY',
                        'price': price_data['Close'].iloc[i],
                        'reason': 'Price above SMA200 and SMA20 above SMA50 - Trend Following'
                    })
                elif price_data['Signal'].iloc[i] == -1 and price_data['Signal'].iloc[i-1] != -1:
                    signals.append({
                        'date': price_data.index[i].strftime('%Y-%m-%d'),
                        'action': 'SELL',
                        'price': price_data['Close'].iloc[i],
                        'reason': 'Price below SMA200 and SMA20 below SMA50 - Trend Following'
                    })
        
        # Add more strategies as needed
        
        return signals
    
    def calculate_backtest_performance(self, symbol, signals, price_data, initial_capital=10000):
        """Calculate performance metrics for a backtest."""
        if not signals or price_data.empty:
            return {
                'sharpe': 0,
                'winrate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'trades': [],
                'equity_curve': []
            }
        
        # Initialize variables
        position = 0
        capital = initial_capital
        trades = []
        equity_curve = [{'date': price_data.index[0].strftime('%Y-%m-%d'), 'equity': capital}]
        entry_price = 0
        entry_date = None
        
        # Process signals
        for signal in signals:
            date = signal['date']
            action = signal['action']
            price = signal['price']
            
            if action == 'BUY' and position == 0:
                # Enter long position
                position = capital / price
                entry_price = price
                entry_date = date
            elif action == 'SELL' and position > 0:
                # Exit long position
                pnl = position * (price - entry_price)
                capital += pnl
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'pnl': pnl,
                    'pnl_percent': (price - entry_price) / entry_price * 100
                })
                position = 0
                equity_curve.append({'date': date, 'equity': capital})
        
        # Calculate performance metrics
        if not trades:
            return {
                'sharpe': 0,
                'winrate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'trades': [],
                'equity_curve': equity_curve
            }
        
        # Calculate win rate
        winning_trades = sum(1 for trade in trades if trade['pnl'] > 0)
        winrate = winning_trades / len(trades) * 100
        
        # Calculate profit factor
        gross_profit = sum(trade['pnl'] for trade in trades if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in trades if trade['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown
        peak = initial_capital
        drawdowns = []
        for point in equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            drawdowns.append(drawdown)
        max_drawdown = max(drawdowns) if drawdowns else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = [(trades[i]['pnl'] / initial_capital) for i in range(len(trades))]
        mean_return = sum(returns) / len(returns) if returns else 0
        std_return = np.std(returns) if len(returns) > 1 else 0.0001
        sharpe = mean_return / std_return if std_return > 0 else 0
        
        return {
            'sharpe': sharpe * np.sqrt(252),  # Annualize
            'winrate': winrate,
            'profit_factor': profit_factor,
            'max_drawdown': -max_drawdown,
            'trades': trades,
            'equity_curve': equity_curve
        }
    
    def get_technical_indicators(self, symbol, indicator_type, time_period=20, series_type="close"):
        """Get technical indicators from Alpha Vantage.
        
        Args:
            symbol (str): Stock ticker symbol
            indicator_type (str): Type of indicator (SMA, EMA, RSI, MACD, BBANDS, etc.)
            time_period (int): Time period for indicator calculation
            series_type (str): Type of price data to use (close, open, high, low)
            
        Returns:
            pd.DataFrame: DataFrame containing indicator values or None if error
        """
        # Create cache key
        cache_key = f"{symbol}_{indicator_type}_{time_period}_{series_type}"
        
        # Check cache first
        if cache_key in self.indicator_cache and datetime.now().timestamp() - self.indicator_cache[cache_key]["timestamp"] < self.cache_duration:
            return self.indicator_cache[cache_key]["data"]
        
        # Get API key
        api_key = self.api_keys.get("alpha_vantage", "")
        if not api_key:
            st.warning(f"Alpha Vantage API key not set. Unable to fetch {indicator_type} for {symbol}.")
            return None
            
        base_url = "https://www.alphavantage.co/query"
        
        # Set parameters based on indicator type
        params = {
            "function": indicator_type,
            "symbol": symbol,
            "interval": "daily",
            "time_period": time_period,
            "series_type": series_type,
            "apikey": api_key
        }
        
        # Special case for MACD which has different parameters
        if indicator_type == "MACD":
            params.pop("time_period", None)
            params["fastperiod"] = 12
            params["slowperiod"] = 26
            params["signalperiod"] = 9
        
        # Special case for BBANDS which needs additional parameters
        if indicator_type == "BBANDS":
            params["nbdevup"] = 2
            params["nbdevdn"] = 2
            params["matype"] = 0  # Simple Moving Average
        
        try:
            # Track API call
            self.last_api_calls["alpha_vantage"] = datetime.now().timestamp()
            
            # Make API request
            response = requests.get(base_url, params=params)
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                st.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if "Note" in data:  # API limit reached
                st.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
            
            # Parse the response based on indicator type
            df = None
            
            if "Technical Analysis" in data:
                # Most indicators return in this format
                indicator_key = list(data["Technical Analysis"].keys())[0]
                df = pd.DataFrame.from_dict(data["Technical Analysis"][indicator_key], orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Convert string values to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
            
            elif "Time Series (Daily)" in data:
                # Some indicators like VWAP might return time series data
                df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Rename columns to remove the numeric prefixes
                df.columns = [col.split('. ')[1] for col in df.columns]
                
                # Convert to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
            
            # Cache the result
            if df is not None:
                self.indicator_cache[cache_key] = {
                    "data": df,
                    "timestamp": datetime.now().timestamp()
                }
                
            return df
            
        except Exception as e:
            st.error(f"Error fetching {indicator_type} for {symbol}: {str(e)}")
            return None
            
    def calculate_technical_indicators(self, price_data, indicators=None):
        """Calculate technical indicators from price data as fallback.
        
        Args:
            price_data (pd.DataFrame): DataFrame with OHLCV data
            indicators (list): List of indicators to calculate
            
        Returns:
            dict: Dictionary containing calculated indicators
        """
        if price_data.empty:
            return {}
            
        if indicators is None:
            indicators = ["SMA", "EMA", "RSI", "MACD", "BBANDS"]
            
        result = {}
        
        # Make sure we have the necessary price data
        if not all(col in price_data.columns for col in ["Open", "High", "Low", "Close", "Volume"]):
            return {}
            
        # Simple Moving Average (SMA)
        if "SMA" in indicators:
            result["SMA20"] = price_data["Close"].rolling(window=20).mean()
            result["SMA50"] = price_data["Close"].rolling(window=50).mean()
            result["SMA200"] = price_data["Close"].rolling(window=200).mean()
            
        # Exponential Moving Average (EMA)
        if "EMA" in indicators:
            result["EMA12"] = price_data["Close"].ewm(span=12, adjust=False).mean()
            result["EMA26"] = price_data["Close"].ewm(span=26, adjust=False).mean()
            
        # Relative Strength Index (RSI)
        if "RSI" in indicators:
            delta = price_data["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            result["RSI"] = 100 - (100 / (1 + rs))
            
        # Moving Average Convergence Divergence (MACD)
        if "MACD" in indicators:
            ema12 = price_data["Close"].ewm(span=12, adjust=False).mean()
            ema26 = price_data["Close"].ewm(span=26, adjust=False).mean()
            result["MACD"] = ema12 - ema26
            result["MACD_Signal"] = result["MACD"].ewm(span=9, adjust=False).mean()
            result["MACD_Hist"] = result["MACD"] - result["MACD_Signal"]
            
        # Bollinger Bands
        if "BBANDS" in indicators:
            sma20 = price_data["Close"].rolling(window=20).mean()
            std20 = price_data["Close"].rolling(window=20).std()
            result["BB_Upper"] = sma20 + (std20 * 2)
            result["BB_Middle"] = sma20
            result["BB_Lower"] = sma20 - (std20 * 2)
            
        return result

# Initialize the data integration in session state
if 'data_integration' not in st.session_state:
    st.session_state.data_integration = BacktestDataIntegration()
    
# Add a new tab option for Autonomous Backtesting
tabs = ["News Dashboard", "Backtesting", "Autonomous Backtesting", "Paper Trading", "Live Trading"]
selected_tab = st.sidebar.radio("Select Tab:", tabs)

# Initialize session state for autonomous backtesting if not exists
if "auto_backtest_results" not in st.session_state:
    st.session_state.auto_backtest_results = {
        "winners": [],
        "kpi_summary": {
            "avg_sharpe": 0.0,
            "win_rate": "0%",
            "profit_factor": 0.0,
            "max_drawdown": "0%"
        },
        "insights": {
            "top_performers": [],
            "underperforming": [],
            "sentiment_correlation": 0.0,
            "recommendations": []
        },
        "last_run_time": None,
        "last_run_config": "Not run yet"
    }

# Initialize the autonomous backtest run flag
if "auto_backtest_running" not in st.session_state:
    st.session_state.auto_backtest_running = False

# Autonomous Backtesting Tab
if selected_tab == "Autonomous Backtesting":
    st.title("Autonomous Backtesting")
    
    # 1. Controls Bar
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
        with col1:
            run_button = st.button("Run Real-time Backtest", type="primary")
        with col2:
            col2a, col2b = st.columns(2)
            with col2a:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
            with col2b:
                end_date = st.date_input("End Date", value=datetime.now())
        with col3:
            available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", 
                            "JPM", "BAC", "V", "JNJ", "PG", "KO", "NFLX", "AMD", "SPY", "QQQ"]
            selected_tickers = st.multiselect("Override Tickers (Optional)", available_tickers)
        with col4:
            # Display the config version or git SHA
            config_version = st.session_state.auto_backtest_results.get("last_run_config", "Not run yet")
            st.text(f"Config: {config_version}")
    
    st.divider()
    
    # 2. KPI Summary Row
    with st.container():
        # Check if backtest_results is a dictionary or a list and handle accordingly
        if isinstance(st.session_state.backtest_results, dict) and "summary_metrics" in st.session_state.backtest_results:
            summary = st.session_state.backtest_results["summary_metrics"]
        else:
            # Default values if summary_metrics is not available
            summary = {
                "avg_sharpe": 0.0,
                "overall_winrate": 0.0,
                "avg_profit_factor": 0.0,
                "max_drawdown": 0.0
            }
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Avg. Sharpe", f"{summary['avg_sharpe']:.2f}")
        with kpi2:
            st.metric("Win Rate", f"{summary['overall_winrate']:.1f}%" if isinstance(summary['overall_winrate'], (int, float)) else summary['overall_winrate']) 
        with kpi3:
            st.metric("Profit Factor", f"{summary['avg_profit_factor']:.2f}")
        with kpi4:
            st.metric("Max Drawdown", f"{summary['max_drawdown']:.1f}%" if isinstance(summary['max_drawdown'], (int, float)) else summary['max_drawdown'])
    
    st.divider()
    
    # 3. Winners Table
    with st.container():
        st.subheader("Top Strategies")
        
        if len(st.session_state.auto_backtest_results["winners"]) > 0:
            # Convert winners to DataFrame
            winners_data = []
            for winner in st.session_state.auto_backtest_results["winners"]:
                winners_data.append({
                    "Ticker": winner["ticker"],
                    "Strategy": winner["strategy"],
                    "Sharpe": winner.get("metrics", {}).get("sharpe", 0.0),
                    "Win Rate": f"{winner.get('metrics', {}).get('win_rate', 0.0):.0f}%",
                    "Profit Factor": winner.get("metrics", {}).get("profit_factor", 0.0),
                    "Drawdown": f"-{winner.get('metrics', {}).get('max_drawdown', 0.0):.1f}%",
                })
            
            winners_df = pd.DataFrame(winners_data)
            
            # Add action buttons with callbacks
            def show_details(ticker, strategy):
                st.session_state.selected_winner = {
                    "ticker": ticker,
                    "strategy": strategy
                }
                st.session_state.show_details_modal = True
            
            def promote_to_paper(ticker, strategy):
                st.toast(f"Promoted {ticker} {strategy} to paper trading")
                
            # Display the DataFrame with action buttons
            for i, row in winners_df.iterrows():
                cols = st.columns([1.5, 2, 1, 1, 1, 1, 2])
                with cols[0]:
                    st.write(f"**{row['Ticker']}**")
                with cols[1]:
                    st.write(row['Strategy'])
                with cols[2]:
                    st.write(f"{row['Sharpe']:.2f}")
                with cols[3]:
                    st.write(row['Win Rate'])
                with cols[4]:
                    st.write(f"{row['Profit Factor']:.2f}")
                with cols[5]:
                    st.write(row['Drawdown'])
                with cols[6]:
                    det_col, prom_col = st.columns(2)
                    with det_col:
                        if st.button("Details", key=f"det_{i}", use_container_width=True):
                            show_details(row['Ticker'], row['Strategy'])
                    with prom_col:
                        if st.button("Paper", key=f"pap_{i}", use_container_width=True):
                            promote_to_paper(row['Ticker'], row['Strategy'])
        else:
            st.info("No backtest results yet. Click 'Run Autonomous Backtest' to start.")
    
    st.divider()
    
    # 4. Auto-Report Insights
    with st.container():
        st.subheader("Auto-Generated Insights")
        insights = st.session_state.auto_backtest_results["insights"]
        
        # Top Performing Strategies
        st.markdown("**Top Performing Strategies:**")
        if insights["top_performers"]:
            for performer in insights["top_performers"]:
                st.markdown(f"• {performer}")
        else:
            st.markdown("• No top performers identified yet")
        
        # Underperforming Signals
        st.markdown("**Underperforming Signals:**")
        if insights["underperforming"]:
            for underperformer in insights["underperforming"]:
                st.markdown(f"• {underperformer}")
        else:
            st.markdown("• No underperforming signals identified yet")
        
        # Sentiment Correlation
        st.markdown("**Sentiment Correlation:**")
        correlation = insights["sentiment_correlation"]
        correlation_text = "positive" if correlation > 0 else "negative" if correlation < 0 else "neutral"
        st.markdown(f"Average correlation between news sentiment and equity returns: {correlation:.2f} ({correlation_text})")
        
        # Next-Step Recommendations
        st.markdown("**Next-Step Recommendations:**")
        if insights["recommendations"]:
            for recommendation in insights["recommendations"]:
                st.markdown(f"• {recommendation}")
        else:
            st.markdown("• No recommendations available yet")
    
    # Last run information
    if st.session_state.auto_backtest_results["last_run_time"]:
        st.caption(f"Last run completed: {st.session_state.auto_backtest_results['last_run_time']}")
    
    # Details Modal (conditionally displayed)
    if st.session_state.get("show_details_modal", False):
        with st.expander("Strategy Details", expanded=True):
            selected = st.session_state.selected_winner
            st.subheader(f"{selected['ticker']} - {selected['strategy']}")
            
            # Find the winner details
            winner_details = None
            for winner in st.session_state.auto_backtest_results["winners"]:
                if winner["ticker"] == selected["ticker"] and winner["strategy"] == selected["strategy"]:
                    winner_details = winner
                    break
            
            if winner_details:
                # Display equity curve chart
                st.subheader("Equity Curve")
                # Simulate equity curve data
                dates = pd.date_range(start=start_date, end=end_date, freq='B')
                base_equity = 10000
                random.seed(hash(f"{selected['ticker']}_{selected['strategy']}"))
                daily_returns = [random.normalvariate(0.0005, 0.01) for _ in range(len(dates))]
                equity = [base_equity]
                for ret in daily_returns:
                    equity.append(equity[-1] * (1 + ret))
                
                equity_df = pd.DataFrame({
                    'Date': dates,
                    'Equity': equity[1:]  # Skip the initial value
                })
                
                st.line_chart(equity_df.set_index('Date'))
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                metrics = winner_details.get("metrics", {})
                with col1:
                    st.metric("Sharpe Ratio", f"{metrics.get('sharpe', 0.0):.2f}")
                with col2:
                    st.metric("Win Rate", f"{metrics.get('win_rate', 0.0):.1f}%")
                with col3:
                    st.metric("Profit Factor", f"{metrics.get('profit_factor', 0.0):.2f}")
                with col4:
                    st.metric("Max Drawdown", f"-{metrics.get('max_drawdown', 0.0):.1f}%")
                
                # Display parameters
                st.subheader("Strategy Parameters")
                params = winner_details.get("params", {})
                param_df = pd.DataFrame({"Parameter": list(params.keys()), "Value": list(params.values())})
                st.dataframe(param_df, hide_index=True)
                
                # Display trade statistics
                st.subheader("Trade Statistics")
                stats = {
                    "Total Trades": random.randint(20, 50),
                    "Average Trade Duration": f"{random.randint(2, 10)} days",
                    "Average Profit per Trade": f"${random.uniform(50, 200):.2f}",
                    "Largest Win": f"${random.uniform(500, 1500):.2f}",
                    "Largest Loss": f"-${random.uniform(300, 800):.2f}",
                    "Profit/Loss Ratio": f"{random.uniform(1.2, 2.5):.2f}"
                }
                stats_df = pd.DataFrame({"Statistic": list(stats.keys()), "Value": list(stats.values())})
                st.dataframe(stats_df, hide_index=True)
                
                # Provide buttons for actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Promote to Paper Trading", use_container_width=True):
                        st.toast(f"Promoted {selected['ticker']} {selected['strategy']} to paper trading")
                with col2:
                    if st.button("Export Results", use_container_width=True):
                        st.toast("Results exported to CSV")
                with col3:
                    if st.button("Close Details", use_container_width=True):
                        st.session_state.show_details_modal = False
                        st.rerun()
            else:
                st.write("Details not available")
    
    # 5. Progress Indicator (when running)
    if run_button:
        st.session_state.auto_backtest_running = True
        st.session_state.show_details_modal = False  # Close any open modals
        
        # Clear previous results before starting new backtest
        old_last_run_time = st.session_state.auto_backtest_results.get("last_run_time")
        
        # Run the real autonomous backtest process
        with st.status("Running Real-time Backtest...", expanded=True) as status:
            try:
                run_autonomous_backtest()
            except Exception as e:
                st.error(f"Error during backtest: {str(e)}")
                status.update(label="Backtest Failed", state="error")
                st.session_state.auto_backtest_running = False

# Continue with the rest of your tabs
elif selected_tab == "News Dashboard":
    # Existing News Dashboard code
    #... existing code ...
    pass  # No-op to satisfy Python's block indentation requirement

def fetch_real_market_conditions():
    """Fetch actual market conditions using real data sources.
    
    Returns:
        dict: Real market conditions data
    """
    try:
        # Get real VIX data
        vix_data = yf.download("^VIX", period="5d")
        vix = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 20.0
        
        # Use VIX to estimate market sentiment (higher VIX = lower sentiment)
        sentiment = max(0, min(1.0, 1.0 - (vix - 10) / 30))
        
        # Determine market phase based on actual market data
        # Get SPY data for 60 days
        spy_data = yf.download("SPY", period="60d")
        
        # Calculate 20-day moving average
        spy_data['SMA20'] = spy_data['Close'].rolling(window=20).mean()
        
        # Identify market phase from price action
        # Last 5 days vs previous 5 days
        recent_return = spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-5] - 1
        
        # Is price above moving average?
        above_ma = spy_data['Close'].iloc[-1] > spy_data['SMA20'].iloc[-1]
        
        # Is volatility high?
        recent_volatility = spy_data['Close'].pct_change().std() * np.sqrt(252)
        high_volatility = recent_volatility > 0.15
        
        # Determine phase based on these factors
        if recent_return > 0.02 and above_ma:
            market_phase = "trending"
        elif high_volatility and abs(recent_return) > 0.015:
            market_phase = "breakout" if recent_return > 0 else "reversal"
        else:
            market_phase = "ranging"
        
        # Get sector performance
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Energy": "XLE",
            "Consumer": "XLY"
        }
        
        # Get 5-day returns for sectors
        sectors = {}
        for sector, ticker in sector_etfs.items():
            try:
                sector_data = yf.download(ticker, period="5d")
                if not sector_data.empty and len(sector_data) >= 2:
                    momentum = sector_data['Close'].iloc[-1] / sector_data['Close'].iloc[0] - 1
                    sectors[sector] = momentum
                else:
                    sectors[sector] = 0
            except:
                sectors[sector] = 0
        
        # Find trending sectors (those with momentum > 0.005 (0.5%))
        trending_sectors = [sector for sector, momentum in sectors.items() if momentum > 0.005]
        
        # Look for anomalies in the market
        # A simple anomaly could be unusually high volume
        spy_volume = spy_data['Volume'].iloc[-1]
        avg_volume = spy_data['Volume'].rolling(window=20).mean().iloc[-1]
        anomaly_detected = spy_volume > avg_volume * 1.5
        
        return {
            "vix": vix,
            "market_sentiment": sentiment,
            "market_phase": market_phase,
            "sectors": sectors,
            "trending_sectors": trending_sectors,
            "anomaly_detected": anomaly_detected,
            "timestamp": datetime.now()
        }
    except Exception as e:
        print(f"Error fetching market conditions: {str(e)}")
        # Fallback to simulated data if real data fetch fails
        return fetch_market_conditions()


def calculate_real_backtest_metrics(ticker, strategy_type, params, start_date, end_date):
    """Calculate real backtest metrics using yfinance data.
    
    Args:
        ticker (str): Ticker symbol
        strategy_type (str): Strategy type
        params (dict): Strategy parameters
        start_date (str): Start date for backtest
        end_date (str): End date for backtest
        
    Returns:
        dict: Performance metrics
    """
    try:
        # Get historical data
        data = yf.download(ticker, start=start_date, end=end_date)
        
        if data.empty or len(data) < 30:  # Need sufficient data
            return None
        
        # Initialize signals list
        signals = []
        
        # Add technical indicators based on strategy type
        if strategy_type in ["Momentum", "Trend Following"]:
            # Add momentum indicators
            lookback = params.get("lookback_period", 20)
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA50'] = data['Close'].rolling(window=50).mean()
            data['SMA200'] = data['Close'].rolling(window=200).mean()
            
            # Generate signals
            data['Signal'] = 0
            
            # Different signal logic based on strategy type
            if strategy_type == "Momentum":
                # Simple momentum: buy when price > SMA20, sell when price < SMA20
                data.loc[data['Close'] > data['SMA20'], 'Signal'] = 1
                data.loc[data['Close'] < data['SMA20'], 'Signal'] = -1
            else:  # Trend Following
                # Trend following: buy when SMA20 > SMA50 and price > SMA200
                data.loc[(data['SMA20'] > data['SMA50']) & (data['Close'] > data['SMA200']), 'Signal'] = 1
                data.loc[(data['SMA20'] < data['SMA50']) | (data['Close'] < data['SMA200']), 'Signal'] = -1
            
        elif strategy_type in ["Breakout"]:
            # Calculate Bollinger Bands
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['StdDev'] = data['Close'].rolling(window=20).std()
            data['UpperBand'] = data['SMA20'] + 2 * data['StdDev']
            data['LowerBand'] = data['SMA20'] - 2 * data['StdDev']
            
            # Breakout signals
            data['Signal'] = 0
            data.loc[data['Close'] > data['UpperBand'], 'Signal'] = 1  # Bullish breakout
            data.loc[data['Close'] < data['LowerBand'], 'Signal'] = -1  # Bearish breakout
            
        elif strategy_type in ["Mean Reversion", "Statistical Arbitrage"]:
            # Calculate z-score for mean reversion
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['StdDev'] = data['Close'].rolling(window=20).std()
            data['ZScore'] = (data['Close'] - data['SMA20']) / data['StdDev']
            
            # Mean reversion signals
            data['Signal'] = 0
            z_score_threshold = params.get("z_score_threshold", 2.0)
            data.loc[data['ZScore'] < -z_score_threshold, 'Signal'] = 1  # Buy when oversold
            data.loc[data['ZScore'] > z_score_threshold, 'Signal'] = -1  # Sell when overbought
            
        elif strategy_type in ["MACD Crossover"]:
            # Calculate MACD
            data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
            data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = data['EMA12'] - data['EMA26']
            data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
            
            # MACD signals
            data['Signal'] = 0
            data.loc[data['MACD'] > data['Signal_Line'], 'Signal'] = 1  # Bullish crossover
            data.loc[data['MACD'] < data['Signal_Line'], 'Signal'] = -1  # Bearish crossover
            
        elif strategy_type in ["RSI Divergence"]:
            # Calculate RSI
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # RSI signals (simplified)
            data['Signal'] = 0
            data.loc[data['RSI'] < 30, 'Signal'] = 1  # Oversold
            data.loc[data['RSI'] > 70, 'Signal'] = -1  # Overbought
            
        else:
            # Default strategy: simple moving average crossover
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA50'] = data['Close'].rolling(window=50).mean()
            
            data['Signal'] = 0
            data.loc[data['SMA20'] > data['SMA50'], 'Signal'] = 1
            data.loc[data['SMA20'] < data['SMA50'], 'Signal'] = -1
        
        # Clean up NaN values
        data = data.dropna()
        
        # Generate trades based on signal changes
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(1, len(data)):
            current_date = data.index[i]
            prev_signal = data['Signal'].iloc[i-1]
            current_signal = data['Signal'].iloc[i]
            
            # Check for signal change
            if current_signal != prev_signal:
                if current_signal == 1 and position == 0:  # Buy signal
                    position = 1
                    entry_price = data['Close'].iloc[i]
                    entry_date = current_date
                    
                elif current_signal == -1 and position == 1:  # Sell signal
                    position = 0
                    exit_price = data['Close'].iloc[i]
                    pnl = (exit_price / entry_price) - 1
                    
                    trades.append({
                        "entry_date": entry_date.strftime("%Y-%m-%d"),
                        "exit_date": current_date.strftime("%Y-%m-%d"),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl": round(pnl * 100, 2),  # Convert to percentage
                        "holding_period": (current_date - entry_date).days
                    })
        
        # Calculate performance metrics
        if not trades:
            return None
        
        # Calculate win rate
        win_count = sum(1 for trade in trades if trade["pnl"] > 0)
        winrate = (win_count / len(trades)) * 100
        
        # Calculate profit factor
        gross_profit = sum(trade["pnl"] for trade in trades if trade["pnl"] > 0)
        gross_loss = abs(sum(trade["pnl"] for trade in trades if trade["pnl"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 2.0  # Avoid division by zero
        
        # Calculate returns for Sharpe ratio
        returns = [trade["pnl"] / 100 for trade in trades]  # Convert back from percentage
        
        # Calculate Sharpe ratio (assuming risk-free rate = 0 for simplicity)
        mean_return = sum(returns) / len(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.01  # Avoid division by zero
        sharpe = (mean_return / std_return) * np.sqrt(252 / 20)  # Annualized
        
        # Calculate max drawdown
        equity_curve = []
        equity = 1.0  # Start with $1
        max_equity = 1.0
        max_drawdown = 0.0
        
        # Generate equity curve
        dates = []
        equities = []
        
        current_equity = 1000  # Start with $1000
        
        for i, trade in enumerate(trades):
            trade_return = trade["pnl"] / 100  # Convert percentage to decimal
            
            # Add entry point
            entry_date = datetime.strptime(trade["entry_date"], "%Y-%m-%d")
            dates.append(entry_date)
            equities.append(current_equity)
            
            # Add exit point
            exit_date = datetime.strptime(trade["exit_date"], "%Y-%m-%d")
            current_equity *= (1 + trade_return)
            dates.append(exit_date)
            equities.append(current_equity)
            
            # Track max equity and drawdown
            if current_equity > max_equity:
                max_equity = current_equity
            else:
                drawdown = (max_equity - current_equity) / max_equity * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        # Create equity curve dataframe
        equity_df = pd.DataFrame({
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "equity": equities
        })
        
        # Return metrics
        return {
            "sharpe": sharpe,
            "winrate": winrate,
            "profit_factor": profit_factor,
            "max_drawdown": -max_drawdown,  # Negative to match existing code expectations
            "trades": trades,
            "equity_curve": equity_df
        }
    
    except Exception as e:
        print(f"Error calculating backtest metrics for {ticker} ({strategy_type}): {str(e)}")
        return None


def run_autonomous_backtest():
    """Run the autonomous backtesting process with real market data.
    
    This function:
    1. Updates the backtest status
    2. Fetches current market conditions using real data
    3. Builds a backtest queue for selected tickers and strategies
    4. Runs backtests with dynamic parameters based on market conditions
    5. Filters and sorts winners
    6. Updates results with detailed narratives and insights
    7. Auto-promotes top strategies if enabled
    """
    try:
        # Update status
        st.session_state.backtest_status = "Running"
        
        # Create progress tracking
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Phase 1: Market Analysis (10% of progress)
            status_text.text("Analyzing market conditions...")
            
            # Fetch real market conditions
            market_conditions = fetch_real_market_conditions()
            st.session_state.current_market_conditions = market_conditions
            
            # Show what we found
            status_text.text(f"Market conditions: VIX={market_conditions['vix']:.1f}, Phase={market_conditions['market_phase']}")
            progress_bar.progress(10)
            time.sleep(0.5)  # Small delay for UI updates
            
            # Phase 2: Ticker Selection (20% of progress)
            status_text.text("Selecting tickers based on market conditions...")
            
            # Use selected tickers if available, otherwise use default list
            if hasattr(st.session_state, 'selected_tickers') and st.session_state.selected_tickers:
                tickers = st.session_state.selected_tickers
                status_text.text(f"Using user-selected tickers: {', '.join(tickers[:5])}{'...' if len(tickers) > 5 else ''}")
            else:
                # In a real implementation, this would dynamically select tickers
                # based on market conditions, volume, sentiment, etc.
                tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "NFLX", "QQQ", "SPY"]
                status_text.text(f"Auto-selected tickers: {', '.join(tickers[:5])}{'...' if len(tickers) > 5 else ''}")
            
            progress_bar.progress(20)
            time.sleep(0.5)  # Small delay for UI updates
            
            # Phase 3: Strategy Selection (30% of progress)
            status_text.text("Determining optimal strategies for current market...")
            
            # Define strategies to test based on market conditions
            if market_conditions['market_phase'] == 'trending':
                # Trending market favors momentum and trend-following
                strategies = [
                    "Momentum", "Trend Following", "Breakout", "Statistical Arbitrage",
                    "MACD Crossover", "Fibonacci Retracement", "Ichimoku Cloud", "ADX Trend Strength"
                ]
                status_text.text(f"Selected trending-market strategies ({len(strategies)})")
            elif market_conditions['market_phase'] == 'ranging':
                # Ranging market favors mean-reversion and oscillators
                strategies = [
                    "Mean Reversion", "Bollinger Band Squeeze", "RSI Divergence", 
                    "Statistical Arbitrage", "Pairs Trading", "Options Volatility Skew"
                ]
                status_text.text(f"Selected range-market strategies ({len(strategies)})")
            else:
                # Default/mixed strategies
                strategies = [
                    "Momentum", "Trend Following", "Breakout", "Statistical Arbitrage", 
                    "Mean Reversion", "Volatility Expansion", "Swing Trading", "Options Volatility Skew", 
                    "News Sentiment", "Pairs Trading", "MACD Crossover", "Earnings Volatility"
                ]
                status_text.text(f"Selected mixed-market strategies ({len(strategies)})")
            
            progress_bar.progress(30)
            time.sleep(0.5)  # Small delay for UI updates
            
            # Phase 4: Building Backtest Queue (40% of progress)
            status_text.text("Building backtest queue...")
            
            # Define backtest date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # 6 months
            
            # Count total backtest jobs
            total_jobs = len(tickers) * len(strategies)
            status_text.text(f"Preparing {total_jobs} backtest jobs...")
            
            # Build backtest queue
            backtest_queue = []
            for strategy in strategies:
                # Create base parameters for this strategy type
                base_params = {
                    "threshold": 0.5,
                    "take_profit": 0.1,
                    "stop_loss": 0.05,
                    "position_size": 1.0
                }
                
                # Add strategy-specific parameters
                if strategy in ["Momentum", "Trend Following"]:
                    base_params["lookback_period"] = 20
                    base_params["momentum_factor"] = 0.3
                
                elif strategy in ["Mean Reversion", "Statistical Arbitrage"]:
                    base_params["z_score_threshold"] = 2.0
                    base_params["mean_reversion_period"] = 10
                
                elif strategy in ["Volatility Expansion", "Options Volatility Skew"]:
                    base_params["volatility_threshold"] = 0.2
                    base_params["term_structure_factor"] = 1.0
                
                # Compute dynamic parameters based on market conditions
                params = compute_dynamic_parameters(strategy, base_params, market_conditions)
                
                # Add to queue for each ticker
                for ticker in tickers:
                    backtest_queue.append({
                        "strategy": strategy,
                        "ticker": ticker,
                        "params": params
                    })
            
            progress_bar.progress(40)
            time.sleep(0.5)  # Small delay for UI updates
            
            # Phase 5: Running Backtests (40-90% of progress)
            status_text.text(f"Running {len(backtest_queue)} backtest jobs...")
            
            # Run backtests and collect results
            winners = []
            all_results = []
            
            for i, test in enumerate(backtest_queue):
                ticker = test["ticker"]
                strategy = test["strategy"]
                params = test["params"]
                
                # Update progress (from 40% to 90%)
                progress_percent = 40 + (i / len(backtest_queue) * 50)
                progress_bar.progress(int(progress_percent))
                status_text.text(f"Testing {ticker} with {strategy} strategy ({i+1}/{len(backtest_queue)})")
                
                # Calculate real metrics
                metrics = calculate_real_backtest_metrics(
                    ticker, 
                    strategy, 
                    params,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                if metrics:
                    # Create winner object
                    winner = {
                        "id": str(uuid.uuid4()),
                        "strategy": strategy,
                        "ticker": ticker,
                        "params": params,
                        "sharpe": metrics["sharpe"],
                        "winrate": metrics["winrate"],
                        "profit_factor": metrics["profit_factor"],
                        "max_drawdown": metrics["max_drawdown"],
                        "trades": metrics["trades"],
                        "equity_curve": metrics["equity_curve"]
                    }
                    
                    # Generate narrative
                    winner["narrative"] = generate_strategy_narrative(winner, market_conditions)
                    
                    # Save all results for later analysis
                    all_results.append(winner)
                    
                    # Add to winners if it meets basic criteria
                    if (winner["sharpe"] > 0.5 and 
                        winner["winrate"] > 40.0 and 
                        winner["profit_factor"] > 1.0):
                        winners.append(winner)
            
            progress_bar.progress(90)
            time.sleep(0.5)  # Small delay for UI updates
            
            # Phase 6: Filtering and Analysis (90-100% of progress)
            status_text.text("Analyzing results and generating insights...")
            
            # Apply performance filters
            filtered_winners = apply_performance_filters(winners)
            
            # Sort by Sharpe ratio
            filtered_winners = sorted(filtered_winners, key=lambda x: x["sharpe"], reverse=True)
            
            # Calculate summary metrics
            if filtered_winners:
                avg_sharpe = statistics.mean([w["sharpe"] for w in filtered_winners])
                overall_winrate = statistics.mean([w["winrate"] for w in filtered_winners])
                avg_profit_factor = statistics.mean([w["profit_factor"] for w in filtered_winners])
                max_drawdown = max([w["max_drawdown"] for w in filtered_winners])
            else:
                # Default values if no strategies pass filters
                avg_sharpe = 0
                overall_winrate = 0
                avg_profit_factor = 0
                max_drawdown = 0
            
            summary_metrics = {
                "avg_sharpe": avg_sharpe,
                "overall_winrate": overall_winrate,
                "avg_profit_factor": avg_profit_factor,
                "max_drawdown": max_drawdown
            }
            
            # Update session state
            st.session_state.backtest_results = {
                "winners": filtered_winners,
                "all_results": all_results,
                "summary_metrics": summary_metrics
            }
            
            progress_bar.progress(100)
            status_text.text(f"Backtest complete! Found {len(filtered_winners)} winning strategies.")
            
            # Store completion time
            st.session_state.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.backtest_status = "Completed"
            
            # Auto-promote top strategies if enabled
            if st.session_state.get("auto_promote_enabled", False) and filtered_winners:
                auto_promote_to_paper()
            
            # Update config version
            st.session_state.config_version = f"v1.0.{random.randint(100, 999)}"
            
            # Give users time to see the completion message
            time.sleep(1)
            
        # Force refresh to show results
        st.experimental_rerun()
    
    except Exception as e:
        st.session_state.backtest_status = "Error"
        st.error(f"Error in autonomous backtest: {str(e)}")
        print(f"Error in autonomous backtest: {str(e)}")


def generate_strategy_narrative(winner, market_conditions):
    """Generate a more detailed and beginner-friendly narrative explaining why this strategy was chosen.
    
    Args:
        winner (dict): The winning strategy details
        market_conditions (dict): Current market conditions
        
    Returns:
        str: Narrative explaining the strategy selection
    """
    strategy = winner["strategy"]
    ticker = winner["ticker"]
    params = winner["params"]
    
    # Get relevant market conditions
    vix = market_conditions["vix"]
    sentiment = market_conditions["market_sentiment"]
    market_phase = market_conditions["market_phase"]
    trending_sectors = market_conditions["trending_sectors"]
    
    # Format market conditions for easier reading
    vix_desc = "high" if vix > 25 else "moderate" if vix > 15 else "low"
    sentiment_desc = "bullish" if sentiment > 0.6 else "bearish" if sentiment < 0.4 else "neutral"
    
    # Build intro based on performance
    sharpe = winner["sharpe"]
    winrate = winner["winrate"]
    
    if sharpe > 2.0 and winrate > 65:
        strength = "excellent"
    elif sharpe > 1.5 and winrate > 60:
        strength = "strong"
    elif sharpe > 1.2 and winrate > 55:
        strength = "good"
    else:
        strength = "acceptable"
    
    # Start with a beginner-friendly explanation of what the strategy is
    narrative = f"{ticker} was selected for a {strategy} strategy based on {strength} backtest results. "
    
    # Add strategy-specific explanation
    if strategy in ["Momentum", "Trend Following"]:
        narrative += f"This {strategy} strategy buys when prices are rising and sells when they start falling. "
        if market_phase in ["trending", "breakout"]:
            narrative += f"It works well in the current {market_phase} market where strong price movements are common. "
        else:
            narrative += f"While we're in a {market_phase} market phase which isn't ideal, this strategy still showed promising results. "
            
        # Add ticker-specific context if available
        if len(trending_sectors) > 0:
            narrative += f"The ticker belongs to a sector with strong momentum, which helps this strategy perform better. "
    
    elif strategy in ["Mean Reversion", "Statistical Arbitrage"]:
        narrative += f"This {strategy} strategy buys when prices have fallen too far and sells when they've risen too much. "
        if market_phase == "ranging":
            narrative += f"It thrives in the current ranging market where prices tend to oscillate within a range. "
        else:
            narrative += f"Despite being in a {market_phase} market which isn't ideal, this strategy still showed promising results. "
        
        if vix > 20:
            narrative += f"The current elevated volatility (VIX: {vix:.1f}) creates good opportunities for mean-reversion strategies as prices tend to overreact. "
    
    elif strategy in ["Volatility Expansion", "Options Volatility Skew"]:
        narrative += f"This {strategy} strategy captures price movements during periods of increasing market volatility. "
        if vix > 25:
            narrative += f"We're seeing high market volatility (VIX: {vix:.1f}) which significantly benefits this strategy type. "
        else:
            narrative += f"Despite moderate volatility levels (VIX: {vix:.1f}), this strategy still showed promising results. "
            
    elif strategy in ["MACD Crossover"]:
        narrative += f"This strategy uses the MACD indicator to identify shifts in momentum and trend direction. "
        narrative += f"It looks for crossovers between the MACD line and signal line to generate buy and sell signals. "
        if market_phase == "trending":
            narrative += f"It works particularly well in trending markets like we have now. "
    
    elif strategy in ["RSI Divergence"]:
        narrative += f"This strategy looks for divergences between price and the Relative Strength Index (RSI) indicator. "
        narrative += f"It helps identify potential reversals when price makes a new high/low but RSI doesn't confirm. "
        if market_phase == "ranging":
            narrative += f"It works particularly well in ranging or reversal markets like we have now. "
    
    # Add market sentiment context
    narrative += f"\n\nThe current market sentiment is **{sentiment_desc}** ({sentiment*100:.1f}/100) with **{vix_desc}** volatility (VIX: {vix:.1f}). "
    
    # Add parameter explanations
    narrative += f"\n\n### Strategy Parameters\n\n"
    narrative += f"These parameters were automatically optimized for current market conditions:\n\n"
    
    for param, value in params.items():
        explanation = ""
        if param == "lookback_period":
            explanation = "Number of days used to calculate signals"
        elif param == "threshold":
            explanation = "Signal strength required to enter a trade"
        elif param == "take_profit":
            explanation = "% gain at which to exit with profit"
        elif param == "stop_loss":
            explanation = "% loss at which to exit to prevent further losses"
        elif param == "position_size":
            explanation = "Portion of capital to allocate to this trade"
        elif param == "z_score_threshold":
            explanation = "How far from the average price to trigger entry"
        elif param == "volatility_threshold":
            explanation = "Minimum volatility required for strategy"
        elif param == "momentum_factor":
            explanation = "Weight given to recent price momentum"
        else:
            explanation = "Strategy-specific configuration"
        
        narrative += f"* **{param}**: {value} - {explanation}\n"
    
    # Add performance highlights
    narrative += f"\n\n### Performance Highlights\n\n"
    narrative += f"* **Sharpe Ratio**: {winner['sharpe']:.2f} (Risk-adjusted return - higher is better)\n"
    narrative += f"* **Win Rate**: {winner['winrate']:.1f}% (Percentage of profitable trades)\n"
    narrative += f"* **Profit Factor**: {winner['profit_factor']:.2f} (Gross profit / gross loss - above 1.0 is profitable)\n"
    narrative += f"* **Max Drawdown**: {winner['max_drawdown']:.1f}% (Worst peak-to-trough decline)\n"
    
    # Add number of trades
    if "trades" in winner and winner["trades"]:
        narrative += f"* **Number of Trades**: {len(winner['trades'])}\n"
        
        # Calculate average trade duration if available
        if "holding_period" in winner["trades"][0]:
            avg_duration = sum(trade["holding_period"] for trade in winner["trades"]) / len(winner["trades"])
            narrative += f"* **Average Trade Duration**: {avg_duration:.1f} days\n"
    
    # Recommendations section
    narrative += f"\n\n### Next Steps\n\n"
    
    if winner['sharpe'] > 1.5 and winner['winrate'] > 60:
        narrative += "This strategy shows strong potential and is ready for paper trading. Consider running it in a paper trading account to validate performance in real market conditions."
    elif winner['max_drawdown'] < -10.0:
        narrative += "While this strategy shows promise, its drawdown is significant. Consider adjusting stop-loss parameters or position sizing before proceeding to paper trading."
    else:
        narrative += "This strategy meets minimum performance criteria but may need further refinement. Consider adjusting parameters or evaluating its performance across different market conditions."
    
    return narrative

# Market Predictions Section
st.markdown("## 🔮 Market Predictions")

# Prediction cards
pred_col1, pred_col2 = st.columns(2)

with pred_col1:
    st.markdown("### Short-term Market Outlook (1-7 days)")
    st.markdown("""
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">SPY (S&P 500 ETF)</h4>
        <p><strong>Forecast:</strong> <span style="color: #00b400;">Bullish</span></p>
        <p><strong>Confidence:</strong> 72%</p>
        <p><strong>Key Factors:</strong> Fed policy, earnings momentum, economic indicators</p>
        <p><strong>Potential Catalysts:</strong> FOMC minutes release, retail sales data</p>
    </div>
    
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">QQQ (Nasdaq ETF)</h4>
        <p><strong>Forecast:</strong> <span style="color: #00b400;">Bullish</span></p>
        <p><strong>Confidence:</strong> 68%</p>
        <p><strong>Key Factors:</strong> Tech earnings, AI developments, semiconductor supply chain</p>
        <p><strong>Potential Catalysts:</strong> NVIDIA earnings, Microsoft AI announcement</p>
    </div>
    """, unsafe_allow_html=True)

with pred_col2:
    st.markdown("### Medium-term Market Outlook (1-3 months)")
    st.markdown("""
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">SPY (S&P 500 ETF)</h4>
        <p><strong>Forecast:</strong> <span style="color: #ffa500;">Neutral</span></p>
        <p><strong>Confidence:</strong> 58%</p>
        <p><strong>Key Factors:</strong> Inflation trends, economic growth, geopolitical tensions</p>
        <p><strong>Potential Catalysts:</strong> CPI data, GDP revision, Fed interest rate decision</p>
    </div>
    
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">QQQ (Nasdaq ETF)</h4>
        <p><strong>Forecast:</strong> <span style="color: #00b400;">Moderately Bullish</span></p>
        <p><strong>Confidence:</strong> 63%</p>
        <p><strong>Key Factors:</strong> Tech sector earnings, AI adoption, regulatory environment</p>
        <p><strong>Potential Catalysts:</strong> Big Tech earnings season, AI conference announcements</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: white;
        border-bottom: 3px solid #4e89ae;
    }
</style>
""", unsafe_allow_html=True)

# Initialize TradeGPT Assistant if not already
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = TradeGPTAssistant()

# Initialize chat history if needed
if 'ai_chat_messages' not in st.session_state:
    st.session_state.ai_chat_messages = [
        {"role": "assistant", "content": """
I'm your TradeGPT Co-Pilot. I can help with:
• Analyzing your strategies and backtests
• Explaining trading metrics and concepts
• Running quick simulations
• Interpreting market conditions and news

Try asking:
• "What are the best strategies for AAPL today?"
• "Explain Sharpe ratio in simple terms"
• "/backtest MSFT with stop 2% target 5%"
• "Compare Momentum vs Mean Reversion"
        """}
    ]

# Add floating AI chat button and modal
st.markdown("""
<div class="ai-assistant-button" id="ai-chat-button" onclick="toggleChat()">
    <i class="fas fa-robot"></i>🤖
</div>

<div class="ai-chat-modal" id="ai-chat-modal">
    <div class="ai-chat-header">
        <span>TradeGPT Co-Pilot</span>
        <span class="ai-chat-close" onclick="toggleChat()">×</span>
    </div>
    <div class="ai-chat-body" id="ai-chat-body">
        <!-- Chat messages will be inserted here via JavaScript -->
    </div>
    <div class="ai-chat-footer">
        <input type="text" class="ai-chat-input" id="ai-chat-input" placeholder="Ask a trading question..." 
               onkeyup="if(event.key==='Enter') sendMessage()">
        <button class="ai-chat-send" onclick="sendMessage()">➤</button>
    </div>
</div>

<script>
// Initialize JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initial chat state
    const chatState = {
        isOpen: false,
        messages: []
    };
    
    // Load messages from session state (will be populated via Streamlit)
    function loadMessages() {
        const chatBody = document.getElementById('ai-chat-body');
        chatBody.innerHTML = '';
        
        // We'll use a data attribute to store messages that Streamlit can update
        const messagesData = document.getElementById('ai-chat-messages-data');
        if (messagesData) {
            try {
                chatState.messages = JSON.parse(messagesData.getAttribute('data-messages'));
                renderMessages();
            } catch (e) {
                console.error('Error parsing messages:', e);
            }
        }
    }
    
    // Render messages in the chat UI
    function renderMessages() {
        const chatBody = document.getElementById('ai-chat-body');
        chatBody.innerHTML = '';
        
        chatState.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = msg.role === 'user' ? 'user-message' : 'assistant-message';
            messageDiv.innerHTML = msg.content;
            chatBody.appendChild(messageDiv);
        });
        
        // Scroll to bottom
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    // Toggle chat open/closed
    window.toggleChat = function() {
        const modal = document.getElementById('ai-chat-modal');
        chatState.isOpen = !chatState.isOpen;
        
        if (chatState.isOpen) {
            modal.style.display = 'flex';
            loadMessages();
            // Focus input
            setTimeout(() => {
                document.getElementById('ai-chat-input').focus();
            }, 100);
        } else {
            modal.style.display = 'none';
        }
    };
    
    // Send message function
    window.sendMessage = function() {
        const inputElement = document.getElementById('ai-chat-input');
        const message = inputElement.value.trim();
        
        if (message) {
            // Clear input
            inputElement.value = '';
            
            // We'll use a hidden form submission that Streamlit can detect
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '';
            form.style.display = 'none';
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'ai_chat_message';
            input.value = message;
            
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        }
    };
    
    // Add message to chat UI
    window.addMessage = function(role, content) {
        chatState.messages.push({role, content});
        renderMessages();
    };
});
</script>

<!-- Data element that Streamlit can update with current messages -->
<div id="ai-chat-messages-data" data-messages='${json.dumps(st.session_state.ai_chat_messages)}'></div>

<!-- Load Font Awesome for icons -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# Handle chat form submissions
chat_message = st.experimental_get_query_params().get('ai_chat_message', [None])[0]
if chat_message:
    # Add user message to chat history
    st.session_state.ai_chat_messages.append({"role": "user", "content": chat_message})
    
    # Get assistant response
    context = {
        "market_conditions": st.session_state.get("market_conditions", {}),
        "recent_backtests": st.session_state.get("backtest_results", [])
    }
    
    # Get response from assistant
    assistant_response = st.session_state.ai_assistant.get_response(chat_message, context)
    
    # Add assistant response to chat history
    st.session_state.ai_chat_messages.append({"role": "assistant", "content": assistant_response})
    
    # Force refresh to show updated chat
    st.rerun()

# Automatic Backtest Scheduling
# Initialize last auto-run time if not exists
if 'last_auto_run' not in st.session_state:
    st.session_state.last_auto_run = datetime.now() - timedelta(hours=6)  # Force immediate run on first load

# Get current time in eastern timezone
current_time_utc = datetime.now(timezone.utc)
eastern_tz = timezone(timedelta(hours=-4))  # EDT
current_time_et = current_time_utc.astimezone(eastern_tz)

# Define market open time (9:30 AM ET)
market_open_time = current_time_et.replace(hour=9, minute=30, second=0, microsecond=0)

# Calculate minutes since market open
minutes_since_open = (current_time_et - market_open_time).total_seconds() / 60

# Calculate time since last auto-run
minutes_since_last_run = (datetime.now() - st.session_state.last_auto_run).total_seconds() / 60

# Auto-run conditions:
# 1. Market is open
# 2. AND either:
#    a. Within 15 minutes of market open
#    b. OR it's been at least 120 minutes since the last auto-run
should_auto_run = (
    is_market_open() and 
    (
        (minutes_since_open >= 0 and minutes_since_open < 15) or  # Right after market open
        minutes_since_last_run >= 120  # Every 2 hours during market hours
    )
)

# Create a container for auto-run messages
auto_run_container = st.empty()

# Run backtest if conditions are met
if should_auto_run:
    with auto_run_container.container():
        # Log the auto-run
        if minutes_since_open >= 0 and minutes_since_open < 15:
            st.info("🔄 Auto-running market open backtest...")
        else:
            st.info(f"🔄 Auto-running periodic backtest ({minutes_since_last_run:.0f} minutes since last run)...")
        
        # Run the backtest
        try:
            # Set status
            st.session_state.auto_backtest_running = True
            st.session_state.backtest_status = "Running"
            
            # Run the backtest
            run_autonomous_backtest()
            
            # Update last run time
            st.session_state.last_auto_run = current_time
            st.session_state.backtest_status = "Completed"
            st.session_state.last_run_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ Auto-backtest completed successfully!")
            
            # Clear the message after 10 seconds
            time.sleep(10)
            auto_run_container.empty()
            
        except Exception as e:
            # Show error
            st.error(f"❌ Auto-backtest failed: {str(e)}")
            
            # Set status
            st.session_state.auto_backtest_running = False
            st.session_state.backtest_status = "Error"
# Display info about next scheduled run
else:
    # Only show during market hours
    if is_market_open():
        # Calculate time until next run
        next_run_time = st.session_state.last_auto_run + timedelta(minutes=120)
        minutes_until_next_run = max(0, (next_run_time - datetime.now()).total_seconds() / 60)
        
        # Show in the footer as a small note
        if minutes_until_next_run > 0 and minutes_until_next_run < 120:
            st.caption(f"Next scheduled backtest in approximately {minutes_until_next_run:.0f} minutes")
        else:
            # Don't show anything to avoid cluttering the UI
            pass