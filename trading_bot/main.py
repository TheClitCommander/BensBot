#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot - Main application entry point
"""

import os
import logging
import time
import signal
import sys
import threading
import uvicorn
from typing import Dict, List, Any, Optional

# Import component modules
from trading_bot.strategy.strategy_rotator import StrategyRotator
from trading_bot.learning.continuous_learner import ContinuousLearner
from trading_bot.api.app import app, initialize_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("TradingBot")

# Global components
strategy_rotator = None
continuous_learner = None
api_server = None
should_exit = threading.Event()

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    logger.info("Received shutdown signal")
    should_exit.set()

def start_api_server():
    """Start the API server in a separate thread."""
    logger.info("Starting API server")
    
    # Configure Uvicorn server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Run server in blocking mode (this will be in a separate thread)
    server.run()

def main():
    """Main entry point for the trading bot application."""
    global strategy_rotator, continuous_learner, api_server
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Log startup
    logger.info("Starting Trading Bot")
    
    try:
        # Initialize components
        logger.info("Initializing StrategyRotator")
        strategy_rotator = StrategyRotator()
        
        logger.info("Initializing ContinuousLearner")
        continuous_learner = ContinuousLearner(
            strategy_rotator=strategy_rotator,
            evaluation_interval=3600  # 1 hour
        )
        
        # Initialize API with components
        initialize_api(strategy_rotator, continuous_learner)
        
        # Start API server in a separate thread
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Start continuous learning
        continuous_learner.start()
        
        logger.info("Trading Bot started successfully")
        
        # Main loop to keep the application running
        while not should_exit.is_set():
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Error starting Trading Bot: {e}")
        raise
    
    finally:
        # Clean shutdown
        logger.info("Shutting down Trading Bot")
        
        if continuous_learner:
            continuous_learner.stop()
        
        if strategy_rotator:
            strategy_rotator.save_state()
        
        logger.info("Trading Bot shutdown complete")

if __name__ == "__main__":
    main() 