#!/usr/bin/env python3
"""
Simple HTTP server to serve the dashboard.
"""

import http.server
import socketserver
import os
import json
import random
import datetime
import webbrowser
import threading
import time
import socket
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urlparse, parse_qs

PORT = 8082
DASHBOARD_FILE = "dashboard.html"

# Get API keys from environment variables - keep these secure!
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
COHERE_API_KEY = os.environ.get('COHERE_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Print AI service configuration status at startup
def print_api_status():
    if OPENAI_API_KEY:
        print("✅ OpenAI API key detected")
    if ANTHROPIC_API_KEY:
        print("✅ Anthropic/Claude API key detected")
    if MISTRAL_API_KEY:
        print("✅ Mistral API key detected")
    if COHERE_API_KEY:
        print("✅ Cohere API key detected")
    if GEMINI_API_KEY:
        print("✅ Gemini API key detected")
    
    if not any([OPENAI_API_KEY, ANTHROPIC_API_KEY, MISTRAL_API_KEY, COHERE_API_KEY, GEMINI_API_KEY]):
        print("ℹ️ No API keys found - using rule-based responses")

def find_available_port(host='localhost', start_port=PORT):
    """Find an available port starting from the specified port.
    
    Args:
        host: The host to check port availability on
        start_port: The starting port number to check
        
    Returns:
        int: An available port number
    """
    current_port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, current_port))
                return current_port
            except OSError:
                current_port += 1
                print(f"Port {current_port-1} is already in use, trying {current_port}...")

# Sample data generators for APIs
def generate_portfolio_data():
    return {
        "total_value": round(random.uniform(90000, 120000), 2),
        "cash": round(random.uniform(20000, 50000), 2),
        "pnl_total": round(random.uniform(-10000, 20000), 2),
        "pnl_pct": round(random.uniform(-10, 20), 2),
        "pnl_daily": round(random.uniform(-2000, 3000), 2),
        "pnl_daily_pct": round(random.uniform(-2, 3), 2),
        "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
        "drawdown": round(random.uniform(2, 15), 2),
        "win_rate": round(random.uniform(40, 75), 1)
    }

def generate_risk_data():
    return {
        "portfolio_beta": round(random.uniform(0.8, 1.4), 2),
        "var_daily": round(random.uniform(1000, 5000), 0),
        "portfolio_volatility": round(random.uniform(8, 18), 1),
        "market_exposure": round(random.uniform(60, 95), 0),
        "alerts": [
            {
                "level": "medium" if random.random() > 0.3 else "high",
                "message": "Portfolio concentration in Technology sector (45%) exceeds target threshold (35%)"
            },
            {
                "level": "low" if random.random() > 0.7 else "medium",
                "message": "Portfolio beta (1.15) is above market neutral target (1.0)"
            }
        ] if random.random() > 0.3 else []
    }

def generate_strategy_performance():
    strategies = [
        {"name": "Momentum", "allocation": 30, "return": round(random.uniform(5, 15), 1), "sharpe": round(random.uniform(1.5, 2.5), 1), "win_rate": round(random.uniform(55, 75), 0)},
        {"name": "Mean Reversion", "allocation": 25, "return": round(random.uniform(3, 12), 1), "sharpe": round(random.uniform(1.2, 2.2), 1), "win_rate": round(random.uniform(50, 65), 0)},
        {"name": "Trend Following", "allocation": 20, "return": round(random.uniform(8, 20), 1), "sharpe": round(random.uniform(1.4, 2.4), 1), "win_rate": round(random.uniform(45, 60), 0)},
        {"name": "Volatility", "allocation": 15, "return": round(random.uniform(-5, 10), 1), "sharpe": round(random.uniform(0.4, 1.6), 1), "win_rate": round(random.uniform(40, 55), 0)},
        {"name": "Breakout", "allocation": 10, "return": round(random.uniform(5, 18), 1), "sharpe": round(random.uniform(1.2, 2.0), 1), "win_rate": round(random.uniform(50, 65), 0)}
    ]
    return {"strategies": strategies}

def generate_positions():
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ"]
    strategies = ["Momentum", "Mean Reversion", "Trend Following", "Volatility", "Breakout"]
    
    positions = []
    for i in range(min(len(symbols), random.randint(3, 8))):
        is_long = random.random() > 0.3
        entry_price = round(random.uniform(100, 500), 2)
        current_price = entry_price * (1 + random.uniform(-0.1, 0.2))
        pnl_pct = ((current_price / entry_price) - 1) * 100
        if not is_long:
            pnl_pct = -pnl_pct
            
        positions.append({
            "symbol": symbols[i],
            "strategy": random.choice(strategies),
            "type": "Long" if is_long else "Short",
            "entry_price": entry_price,
            "current_price": round(current_price, 2),
            "pnl_pct": round(pnl_pct, 2)
        })
    
    return {"positions": positions}

# Call OpenAI API with basic HTTP - no extra libraries needed
def call_openai_api(messages, max_tokens=150):
    if not OPENAI_API_KEY:
        return None
        
    try:
        # Prepare request data
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        # Convert payload to JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Set up request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        # Create request
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        # Send request
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return response_data["choices"][0]["message"]["content"]
            
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None

# Call Anthropic/Claude API with basic HTTP - no extra libraries needed
def call_anthropic_api(system_prompt, messages, max_tokens=150):
    if not ANTHROPIC_API_KEY:
        return None
        
    try:
        # Format messages for Claude API
        message_text = ""
        for msg in messages:
            if msg["role"] == "user":
                message_text += f"\n\nHuman: {msg['content']}"
            elif msg["role"] == "assistant":
                message_text += f"\n\nAssistant: {msg['content']}"
        
        message_text = message_text.strip()
        if not message_text.startswith("Human:"):
            message_text = f"Human: {message_text}"
            
        # Prepare request data
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": message_text}
            ]
        }
        
        # Convert payload to JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Set up request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        # Create request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers=headers,
            method="POST"
        )
        
        # Send request
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return response_data["content"][0]["text"]
            
    except Exception as e:
        print(f"Anthropic API error: {str(e)}")
        return None

# Call Mistral API with basic HTTP - no extra libraries needed
def call_mistral_api(messages, max_tokens=150):
    if not MISTRAL_API_KEY:
        return None
        
    try:
        # Prepare request data
        payload = {
            "model": "mistral-tiny",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        # Convert payload to JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Set up request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MISTRAL_API_KEY}"
        }
        
        # Create request
        req = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        # Send request
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return response_data["choices"][0]["message"]["content"]
            
    except Exception as e:
        print(f"Mistral API error: {str(e)}")
        return None

# Enhanced bot response system with context awareness
CONVERSATION_HISTORY = []
PORTFOLIO_CONTEXT = {}

def get_bot_response(message, context):
    # Generate fresh data each time to simulate real-time data
    portfolio_data = generate_portfolio_data()
    risk_data = generate_risk_data()
    strategy_data = generate_strategy_performance()
    positions_data = generate_positions()
    
    # Store in global context for reference
    global PORTFOLIO_CONTEXT
    PORTFOLIO_CONTEXT = {
        "portfolio": portfolio_data,
        "risk": risk_data,
        "strategies": strategy_data["strategies"],
        "positions": positions_data["positions"]
    }
    
    # Track conversation history (limited to last 10 messages)
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.append({"role": "user", "content": message})
    if len(CONVERSATION_HISTORY) > 10:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-10:]
    
    # Create system message with context for any API
    system_message = f"""
    You are BenBot, an AI trading assistant integrated into a trading dashboard.
    
    Current portfolio metrics:
    - Total Value: ${portfolio_data['total_value']}
    - Total P&L: ${portfolio_data['pnl_total']} ({portfolio_data['pnl_pct']}%)
    - Sharpe Ratio: {portfolio_data['sharpe_ratio']}
    - Drawdown: {portfolio_data['drawdown']}%
    - Win Rate: {portfolio_data['win_rate']}%
    
    Current risk metrics:
    - Portfolio Beta: {risk_data['portfolio_beta']}
    - Value at Risk (VaR): ${risk_data['var_daily']}
    - Portfolio Volatility: {risk_data['portfolio_volatility']}%
    - Market Exposure: {risk_data['market_exposure']}%
    
    Strategy allocation:
    {', '.join([f"{s['name']}: {s['allocation']}% ({'+' if s['return'] >= 0 else ''}{s['return']}% return)" for s in strategy_data['strategies']])}
    
    The user is currently viewing the {context} section of the dashboard.
    
    Provide concise, professional advice about trading and portfolio management.
    Keep responses under 3 sentences for quick reading in a chat interface.
    Be direct and specific with any recommendations.
    """
    
    # Create messages array for OpenAI/Mistral format
    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": message}]
    
    # Add recent conversation history for context
    if len(CONVERSATION_HISTORY) > 1:
        history_messages = []
        for i in range(min(4, len(CONVERSATION_HISTORY)-1)):
            idx = len(CONVERSATION_HISTORY) - 2 - i
            if idx >= 0:
                history_messages.append({"role": "user", "content": CONVERSATION_HISTORY[idx]["content"]})
        
        if history_messages:
            messages = [{"role": "system", "content": system_message}] + history_messages + [{"role": "user", "content": message}]
    
    # Try calling different AI APIs in order of preference
    
    # 1. Try Claude/Anthropic first (generally best performance)
    if ANTHROPIC_API_KEY:
        ai_response = call_anthropic_api(system_message, messages)
        if ai_response:
            print("Using Claude/Anthropic for response")
            return ai_response
    
    # 2. Try OpenAI next
    if OPENAI_API_KEY:
        ai_response = call_openai_api(messages)
        if ai_response:
            print("Using OpenAI for response")
            return ai_response
    
    # 3. Try Mistral next
    if MISTRAL_API_KEY:
        ai_response = call_mistral_api(messages)
        if ai_response:
            print("Using Mistral for response")
            return ai_response
    
    # If all API calls fail, fall back to rule-based responses
    print("Using rule-based fallback for response")
            
    # Find best performing and worst performing strategies
    strategies = strategy_data["strategies"]
    best_strategy = max(strategies, key=lambda x: x["return"])
    worst_strategy = min(strategies, key=lambda x: x["return"])
    
    # Find positions with biggest gains and losses
    positions = positions_data["positions"]
    best_position = max(positions, key=lambda x: x["pnl_pct"]) if positions else None
    worst_position = min(positions, key=lambda x: x["pnl_pct"]) if positions else None
    
    # Check for questions in conversation
    lower_msg = message.lower()
    
    # Specific context-based responses
    if "dashboard-overview" in context:
        if "performance" in lower_msg or "how am i doing" in lower_msg:
            if portfolio_data["pnl_total"] > 0:
                return f"Your portfolio is up ${portfolio_data['pnl_total']:.2f} ({portfolio_data['pnl_pct']:.2f}%). Your win rate of {portfolio_data['win_rate']}% is solid, and your Sharpe ratio of {portfolio_data['sharpe_ratio']:.2f} indicates good risk-adjusted returns."
            else:
                return f"Your portfolio is down ${abs(portfolio_data['pnl_total']):.2f} ({portfolio_data['pnl_pct']:.2f}%). Your win rate of {portfolio_data['win_rate']}% is still decent, but your Sharpe ratio of {portfolio_data['sharpe_ratio']:.2f} suggests you might need to adjust your risk management."
        
        elif "strategy" in lower_msg or "best" in lower_msg:
            return f"Your best performing strategy is {best_strategy['name']} with a return of {best_strategy['return']}%. Consider increasing allocation to this strategy if the performance persists."
        
        elif "risk" in lower_msg:
            return f"Your portfolio has a drawdown of {portfolio_data['drawdown']}% and volatility of {risk_data['portfolio_volatility']}%. Your Value at Risk (VaR) is ${risk_data['var_daily']}, meaning there's a 5% chance of losing this amount or more in a day."
        
        else:
            return f"I see your current portfolio value is ${portfolio_data['total_value']:.2f} with a P&L of {'+' if portfolio_data['pnl_total'] >= 0 else ''}{portfolio_data['pnl_total']:.2f} ({portfolio_data['pnl_pct']:.2f}%). How can I help you analyze your performance further?"
    
    elif "dashboard-strategy-performance" in context:
        if "allocate" in lower_msg or "allocation" in lower_msg:
            return f"Based on recent performance, you might consider increasing allocation to {best_strategy['name']} ({best_strategy['return']}% return) and decreasing exposure to {worst_strategy['name']} ({worst_strategy['return']}% return). This could improve your overall portfolio returns."
        
        elif "momentum" in lower_msg:
            momentum = next((s for s in strategies if s["name"] == "Momentum"), None)
            if momentum:
                return f"Your Momentum strategy has a {momentum['return']}% return with a Sharpe ratio of {momentum['sharpe']} and win rate of {momentum['win_rate']}%. It currently has a {momentum['allocation']}% allocation in your portfolio."
            
        elif "mean reversion" in lower_msg:
            mr = next((s for s in strategies if s["name"] == "Mean Reversion"), None)
            if mr:
                return f"Your Mean Reversion strategy has a {mr['return']}% return with a Sharpe ratio of {mr['sharpe']} and win rate of {mr['win_rate']}%. It currently has a {mr['allocation']}% allocation in your portfolio."
        
        elif "trend" in lower_msg:
            trend = next((s for s in strategies if s["name"] == "Trend Following"), None)
            if trend:
                return f"Your Trend Following strategy has a {trend['return']}% return with a Sharpe ratio of {trend['sharpe']} and win rate of {trend['win_rate']}%. It currently has a {trend['allocation']}% allocation in your portfolio."
        
        else:
            return f"Looking at your strategy performance, {best_strategy['name']} is your top performer with {best_strategy['return']}% return. {worst_strategy['name']} is underperforming at {worst_strategy['return']}% return. What specific aspect would you like to analyze?"
    
    elif "dashboard-positions" in context:
        if best_position and "best" in lower_msg:
            return f"Your best position is {best_position['symbol']} ({best_position['type']}) with a profit of {best_position['pnl_pct']:.2f}%. You entered at ${best_position['entry_price']} and the current price is ${best_position['current_price']}."
        
        elif worst_position and ("worst" in lower_msg or "losing" in lower_msg):
            return f"Your worst position is {worst_position['symbol']} ({worst_position['type']}) with a loss of {abs(worst_position['pnl_pct']):.2f}%. You entered at ${worst_position['entry_price']} and the current price is ${worst_position['current_price']}."
        
        elif any(sym.lower() in lower_msg for sym in ["aapl", "apple"]):
            apple = next((p for p in positions if p["symbol"] == "AAPL"), None)
            if apple:
                return f"Your AAPL position is {apple['pnl_pct']:.2f}% {'profitable' if apple['pnl_pct'] > 0 else 'down'}. You entered at ${apple['entry_price']} and the current price is ${apple['current_price']}."
            else:
                return "You don't currently have a position in AAPL."
        
        elif any(sym.lower() in lower_msg for sym in ["tsla", "tesla"]):
            tesla = next((p for p in positions if p["symbol"] == "TSLA"), None)
            if tesla:
                return f"Your TSLA position is {tesla['pnl_pct']:.2f}% {'profitable' if tesla['pnl_pct'] > 0 else 'down'}. You entered at ${tesla['entry_price']} and the current price is ${tesla['current_price']}."
            else:
                return "You don't currently have a position in TSLA."
        
        else:
            profitable_count = sum(1 for p in positions if p["pnl_pct"] > 0)
            losing_count = len(positions) - profitable_count
            return f"You have {len(positions)} open positions: {profitable_count} profitable and {losing_count} losing. Your most profitable position is {best_position['symbol']} (+{best_position['pnl_pct']:.2f}%) and your worst is {worst_position['symbol']} ({worst_position['pnl_pct']:.2f}%)."
    
    elif "dashboard-risk-monitor" in context:
        if "alert" in lower_msg or "warning" in lower_msg:
            if risk_data["alerts"]:
                alerts_text = " ".join([f"{a['level'].capitalize()} risk: {a['message']}" for a in risk_data["alerts"]])
                return f"You have {len(risk_data['alerts'])} active risk alerts: {alerts_text}"
            else:
                return "You don't have any active risk alerts at the moment. Your portfolio risk levels are within acceptable thresholds."
        
        elif "beta" in lower_msg:
            if risk_data["portfolio_beta"] > 1.1:
                return f"Your portfolio beta is {risk_data['portfolio_beta']}, which is higher than the market. This means your portfolio is more volatile than the market and will likely amplify both gains and losses during market movements."
            elif risk_data["portfolio_beta"] < 0.9:
                return f"Your portfolio beta is {risk_data['portfolio_beta']}, which is lower than the market. This indicates a more conservative positioning that should help reduce losses during market downturns."
            else:
                return f"Your portfolio beta is {risk_data['portfolio_beta']}, which is close to the market beta of 1.0. This suggests your portfolio will generally move in line with the broader market."
        
        elif "var" in lower_msg or "value at risk" in lower_msg:
            return f"Your daily Value at Risk (VaR) is ${risk_data['var_daily']}. This means there's a 95% probability that your portfolio won't lose more than this amount in a single trading day."
        
        elif "volatility" in lower_msg:
            if risk_data["portfolio_volatility"] > 15:
                return f"Your portfolio volatility is {risk_data['portfolio_volatility']}%, which is relatively high. Consider adding more uncorrelated assets or reducing position sizes to bring this down."
            else:
                return f"Your portfolio volatility is {risk_data['portfolio_volatility']}%, which is within a reasonable range. This indicates your risk management approach is working effectively."
        
        elif "exposure" in lower_msg:
            if risk_data["market_exposure"] > 80:
                return f"Your market exposure is {risk_data['market_exposure']}%, which is quite high. Consider taking some profits or hedging to reduce risk if you're concerned about a market downturn."
            else:
                return f"Your market exposure is {risk_data['market_exposure']}%, which leaves you with sufficient buffer in case of market stress events."
        
        else:
            alert_count = len(risk_data["alerts"])
            alert_text = f"You have {alert_count} active risk alerts. " if alert_count > 0 else "No active risk alerts. "
            return f"{alert_text}Your portfolio has a beta of {risk_data['portfolio_beta']}, volatility of {risk_data['portfolio_volatility']}%, and market exposure of {risk_data['market_exposure']}%. Your daily VaR is ${risk_data['var_daily']}."
    
    # General responses based on user message content
    elif "help" in lower_msg:
        return "I can help you analyze your trading performance, manage risk, optimize your portfolio allocation, or provide information about specific strategies and positions. Just ask me what you'd like to know!"
    
    elif "recommendation" in lower_msg or "suggest" in lower_msg:
        if portfolio_data["sharpe_ratio"] < 1.0:
            return f"Given your Sharpe ratio of {portfolio_data['sharpe_ratio']:.2f}, I'd recommend focusing on improving risk-adjusted returns. Consider reducing exposure to more volatile assets and increasing allocation to strategies like {best_strategy['name']} which has shown better performance."
        else:
            return f"Your portfolio is performing well with a Sharpe ratio of {portfolio_data['sharpe_ratio']:.2f}. I'd suggest increasing allocation to {best_strategy['name']} while gradually reducing exposure to {worst_strategy['name']} to further optimize returns."
    
    elif "market" in lower_msg:
        return "Based on current market conditions, maintain discipline with your risk management rules. Don't chase performance, and remember that consistency beats occasional big wins. Consider the impacts of recent Fed policy and earnings reports on your positions."
    
    elif "thank" in lower_msg:
        return "You're welcome! Let me know if you need any other trading insights or assistance with your portfolio management."
    
    elif "hello" in lower_msg or "hey" in lower_msg or "hi" in lower_msg:
        return f"Hello! I'm analyzing your current portfolio metrics. Your P&L is {'positive' if portfolio_data['pnl_total'] > 0 else 'negative'} at {portfolio_data['pnl_pct']:.2f}%. How can I help with your trading decisions today?"
    
    # Default response with some portfolio insight
    else:
        responses = [
            f"Looking at your portfolio data, your current P&L is {'+' if portfolio_data['pnl_total'] >= 0 else ''}{portfolio_data['pnl_total']:.2f} ({portfolio_data['pnl_pct']:.2f}%). Your best performing strategy is {best_strategy['name']} at {best_strategy['return']}% return. What specific insights would you like?",
            f"I notice your portfolio has a win rate of {portfolio_data['win_rate']}% and a Sharpe ratio of {portfolio_data['sharpe_ratio']:.2f}. How can I help you improve these metrics?",
            f"Your portfolio metrics show a drawdown of {portfolio_data['drawdown']}% and a beta of {risk_data['portfolio_beta']}. Would you like me to suggest ways to optimize your risk-adjusted returns?",
            f"Based on your current positions, {best_position['symbol'] if best_position else 'your best position'} is up {best_position['pnl_pct']:.2f if best_position else 0}%. How can I help you capitalize on this performance?"
        ]
        return random.choice(responses)

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Handle OPTIONS method (preflight requests)
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
        
        # API endpoints
        if path == "/api/portfolio":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(generate_portfolio_data()).encode())
            return
        
        elif path == "/api/risk":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(generate_risk_data()).encode())
            return
        
        elif path == "/api/strategies":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(generate_strategy_performance()).encode())
            return
        
        elif path == "/api/positions":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(generate_positions()).encode())
            return
            
        # Serve the dashboard HTML file for the root path or direct requests
        elif path == "/" or path == f"/{DASHBOARD_FILE}":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(DASHBOARD_FILE, 'rb') as file:
                self.wfile.write(file.read())
            return
        
        # Default to the standard behavior for other files
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Handle OPTIONS method (preflight requests)
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
        
        # Handle chat API
        if path == "/api/chat":
            print(f"Received chat request from {self.client_address[0]}")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                message = data.get("message", "")
                context = data.get("context", "")
                
                print(f"Chat message: '{message}', Context: '{context}'")
                
                response = get_bot_response(message, context)
                
                # If response is already a dict, use it directly
                if isinstance(response, dict):
                    response_data = response
                else:
                    # Otherwise, format it as a dict
                    response_data = {
                        "response": response,
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response_json = json.dumps(response_data)
                print(f"Sending response: {response_json[:100]}...")
                
                self.wfile.write(response_json.encode())
                print("Response sent successfully")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}, Data: {post_data[:100]}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON: {str(e)}"}).encode())
            except Exception as e:
                print(f"Error processing chat request: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Server error: {str(e)}"}).encode())
            
            return
        
        # Default behavior for other POST requests
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

def start_server(host='localhost', port=PORT):
    handler = DashboardHandler
    
    # Print API configuration status
    print_api_status()
    
    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"Server started at http://{host}:{port}")
            
            # Start the server
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped by user")

if __name__ == "__main__":
    start_server() 