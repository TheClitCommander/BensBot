#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone script to test GPT-4 trade evaluation with Telegram notifications.
This script simulates the GPT-4 evaluation and sends formatted notifications.
"""

import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TradeEvalTest")

def send_telegram_message(bot_token, chat_id, text, parse_mode="HTML"):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, data=data)
        response_json = response.json()
        
        if response.status_code == 200 and response_json.get("ok", False):
            logger.info(f"Message sent successfully to chat ID {chat_id}")
            return True
        else:
            logger.error(f"Failed to send message: {response_json}")
            return False
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return False

def mock_gpt4_evaluation(trade_data, context_data, strategy_perf):
    """Simulate a GPT-4 evaluation of a trade."""
    logger.info(f"Simulating GPT-4 evaluation for {trade_data['symbol']}")
    
    # In a real implementation, this would call the OpenAI API
    # For now, we'll return a mock response
    return {
        "confidence_score": 7.8,
        "bias_alignment": "Moderate",
        "reasoning": "This trade shows a strong setup with the price breaking above a key resistance level with increased volume. The RSI is not overbought yet, and there's room for further upside. The trade aligns well with the current bullish market regime, and the sector has been outperforming. The strategy has a good track record in similar market conditions.",
        "recommendation": "Proceed with trade",
        "should_execute": True
    }

def format_evaluation_message(trade_data, evaluation, context_data=None, strategy_perf=None):
    """Format the evaluation as a Telegram message."""
    # Extract key information
    symbol = trade_data.get('symbol', 'UNKNOWN')
    strategy = trade_data.get('strategy_name', 'UNKNOWN')
    direction = trade_data.get('direction', 'UNKNOWN').upper()
    entry = trade_data.get('entry', 0.0)
    target = trade_data.get('target', 0.0)
    stop = trade_data.get('stop', 0.0)
    
    # Calculate risk/reward ratio if possible
    risk_reward = "N/A"
    if stop and entry and target and stop != entry:
        if direction.lower() == 'long':
            risk = entry - stop
            reward = target - entry
        else:  # short
            risk = stop - entry
            reward = entry - target
            
        if risk > 0:
            risk_reward = f"{reward/risk:.2f}"
    
    # Determine recommendation emoji
    recommendation = evaluation.get('recommendation', 'Unknown')
    if 'proceed' in recommendation.lower():
        rec_emoji = "✅"
    elif 'reduce' in recommendation.lower():
        rec_emoji = "⚠️"
    else:  # skip
        rec_emoji = "❌"
        
    # Determine bias alignment emoji
    bias = evaluation.get('bias_alignment', 'None')
    if bias.lower() == 'strong':
        bias_emoji = "🔥"
    elif bias.lower() == 'moderate':
        bias_emoji = "👍"
    elif bias.lower() == 'weak':
        bias_emoji = "👌"
    else:  # None
        bias_emoji = "⚖️"
    
    # Build the message
    confidence = evaluation.get('confidence_score', 0)
    message = f"<b>🧠 GPT-4 TRADE EVALUATION</b>\n\n"
    
    # Trade details
    message += f"<b>Symbol:</b> {symbol}\n"
    message += f"<b>Direction:</b> {'🟢 LONG' if direction.lower() == 'long' else '🔴 SHORT'}\n"
    message += f"<b>Strategy:</b> {strategy}\n"
    message += f"<b>Entry:</b> ${entry:,.2f}\n"
    
    if stop:
        message += f"<b>Stop:</b> ${stop:,.2f}\n"
    
    if target:
        message += f"<b>Target:</b> ${target:,.2f}\n"
        
    if risk_reward != "N/A":
        message += f"<b>Risk/Reward:</b> {risk_reward}\n"
    
    # Evaluation results
    message += f"\n<b>GPT-4 Evaluation:</b>\n"
    message += f"<b>Confidence:</b> {confidence:.1f}/10.0\n"
    message += f"<b>Bias Alignment:</b> {bias_emoji} {bias}\n"
    message += f"<b>Recommendation:</b> {rec_emoji} {recommendation}\n"
    
    # Include reasoning if available
    if 'reasoning' in evaluation:
        message += f"\n<b>Reasoning:</b>\n<i>{evaluation['reasoning']}</i>\n"
        
    # Include market context if available
    if context_data:
        message += "\n<b>Market Context:</b>\n"
        
        # Add key market context data
        if 'market_regime' in context_data:
            message += f"• Market: {context_data['market_regime']}\n"
            
        if 'volatility_index' in context_data:
            message += f"• VIX: {context_data['volatility_index']}\n"
            
        # Add recent news if available
        if 'recent_news' in context_data and context_data['recent_news']:
            news = context_data['recent_news'][0]
            if isinstance(news, dict) and 'headline' in news:
                message += f"• News: {news['headline']}\n"
    
    # Include strategy performance if available
    if strategy_perf:
        message += "\n<b>Strategy Performance:</b>\n"
        
        if 'win_rate' in strategy_perf:
            message += f"• Win Rate: {strategy_perf['win_rate']*100:.1f}%\n"
            
        if 'profit_factor' in strategy_perf:
            message += f"• Profit Factor: {strategy_perf['profit_factor']:.2f}\n"
    
    # Add timestamp
    message += f"\n<i>Evaluated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    
    return message

def format_trade_execution_message(trade_data, evaluation):
    """Format a trade execution message."""
    symbol = trade_data.get('symbol', 'UNKNOWN')
    direction = trade_data.get('direction', 'UNKNOWN').upper()
    confidence = evaluation.get('confidence_score', 0)
    
    # Determine trade type based on direction
    trade_type = "BUY" if direction.lower() == 'long' else "SELL"
    emoji = "🟢" if trade_type == "BUY" else "🔴"
    
    message = f"<b>{emoji} TRADE ALERT: {trade_type} {symbol}</b>\n\n"
    message += f"<b>Type:</b> {trade_type}\n"
    message += f"<b>Symbol:</b> {symbol}\n"
    message += f"<b>Price:</b> ${trade_data.get('entry', 0.0):,.2f}\n"
    message += f"<b>Quantity:</b> {trade_data.get('quantity', 0.0):,.8f}\n"
    message += f"<b>Strategy:</b> {trade_data.get('strategy_name', 'Unknown')} (GPT: {confidence:.1f}/10)\n"
    message += f"\n<i>Executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    
    return message

def main():
    """Run the trade evaluation test."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not telegram_token or not telegram_chat_id:
        logger.error("Telegram credentials not found.")
        logger.error("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return
    
    logger.info("Starting GPT-4 trade evaluation simulation")
    
    # Sample trade data
    trade_data = {
        "symbol": "AAPL",
        "strategy_name": "breakout_momentum",
        "direction": "long",
        "entry": 186.50,
        "stop": 182.00,
        "target": 195.00,
        "timeframe": "4h",
        "setup_type": "cup_and_handle",
        "quantity": 10
    }
    
    # Sample market context
    context_data = {
        "market_regime": "bullish",
        "sector_performance": {"technology": 2.3},
        "volatility_index": 15.7,
        "recent_news": [
            {
                "headline": "Apple announces new AI features for iPhone",
                "sentiment": "positive",
                "date": "2023-06-05"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # Sample strategy performance data
    strategy_perf = {
        "win_rate": 0.72,
        "profit_factor": 3.2,
        "average_win": 2.5,
        "average_loss": -1.2,
        "regime_performance": {
            "bullish": {"win_rate": 0.80, "trades": 25},
            "bearish": {"win_rate": 0.45, "trades": 12},
            "neutral": {"win_rate": 0.65, "trades": 18}
        }
    }
    
    # Send starting message
    starting_message = f"🧠 <b>Starting GPT-4 Trade Evaluation</b>\n\nEvaluating {trade_data['symbol']} {trade_data['setup_type']} setup..."
    send_telegram_message(telegram_token, telegram_chat_id, starting_message)
    
    # Simulate GPT-4 evaluation
    evaluation = mock_gpt4_evaluation(trade_data, context_data, strategy_perf)
    logger.info(f"Trade evaluation result: {evaluation['recommendation']} with confidence {evaluation['confidence_score']}")
    
    # Format and send evaluation message
    evaluation_message = format_evaluation_message(trade_data, evaluation, context_data, strategy_perf)
    send_telegram_message(telegram_token, telegram_chat_id, evaluation_message)
    
    # If trade should be executed, send execution message
    if evaluation.get('should_execute', False):
        execution_message = format_trade_execution_message(trade_data, evaluation)
        send_telegram_message(telegram_token, telegram_chat_id, execution_message)
    
    logger.info("Trade evaluation test completed")


if __name__ == "__main__":
    main() 