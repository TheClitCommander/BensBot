#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to test Telegram notifications without dependencies.
"""

import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TelegramTest")

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

def main():
    """Run the Telegram test."""
    # Load environment variables
    load_dotenv()
    
    # Get Telegram credentials
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.error("Telegram credentials not found. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return
    
    logger.info(f"Sending test message to chat ID: {chat_id}")
    
    # Send a test message
    message = f"""
🚀 <b>Trading Bot Test Message</b>

This is a test message from your trading bot.
• <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• <b>Bot Status:</b> Online

<i>If you received this message, your Telegram notifications are working correctly!</i>
"""
    
    success = send_telegram_message(bot_token, chat_id, message)
    
    if success:
        # Send a trade alert example
        trade_message = f"""
🟢 <b>TRADE ALERT: BUY BTC/USD</b>

<b>Type:</b> BUY
<b>Symbol:</b> BTC/USD
<b>Price:</b> $45,000.50
<b>Quantity:</b> 0.25000000
<b>Strategy:</b> RSI_Divergence

<i>Executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        send_telegram_message(bot_token, chat_id, trade_message)
        
        # Send an error notification example
        error_message = f"""
🚨 <b>ConnectionError Alert</b>

<b>Error:</b> Failed to connect to exchange API

<i>Occurred at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        send_telegram_message(bot_token, chat_id, error_message)
        
        logger.info("All test messages sent successfully")
    else:
        logger.error("Failed to send test message")

if __name__ == "__main__":
    main() 