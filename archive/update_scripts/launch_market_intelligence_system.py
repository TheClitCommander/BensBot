"""
Launch Market Intelligence System
This script demonstrates how to initialize and run the complete Market Intelligence system
with all components: context management, ML pipeline, triggers, and API access.
"""

import os
import sys
import time
import logging
import argparse
import threading
import uvicorn
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("market_intelligence.log")
    ]
)
logger = logging.getLogger("LaunchMarketIntelligence")

# Import our components
from trading_bot.market_intelligence_controller import get_market_intelligence_controller
from trading_bot.ml_pipeline.adaptive_trainer import get_adaptive_trainer
from trading_bot.ml_pipeline.backtest_feedback_loop import get_backtest_feedback_system, get_backtest_executor
from trading_bot.triggers.market_intelligence_triggers import get_timer_trigger, get_event_trigger, get_webhook_trigger
from trading_bot.api.market_intelligence_api import app as api_app

def initialize_system(args):
    """
    Initialize all components of the Market Intelligence system.
    
    Args:
        args: Command line arguments
    
    Returns:
        Dictionary with all system components
    """
    logger.info("Initializing Market Intelligence system")
    
    # Initialize controller (this will initialize MarketContext and SymbolRanker)
    controller = get_market_intelligence_controller()
    
    # Initialize ML pipeline
    trainer = get_adaptive_trainer()
    
    # Initialize backtest feedback system
    feedback_system = get_backtest_feedback_system()
    backtest_executor = get_backtest_executor()
    
    # Initialize triggers
    timer_trigger = get_timer_trigger()
    event_trigger = get_event_trigger()
    webhook_trigger = get_webhook_trigger()
    
    # Force initial update if requested
    if args.force_update:
        logger.info("Forcing initial update")
        controller.update(force=True)
    
    # Return all components
    return {
        "controller": controller,
        "trainer": trainer,
        "feedback_system": feedback_system,
        "backtest_executor": backtest_executor,
        "timer_trigger": timer_trigger,
        "event_trigger": event_trigger,
        "webhook_trigger": webhook_trigger
    }

def start_triggers(components, args):
    """
    Start the triggers for the Market Intelligence system.
    
    Args:
        components: Dictionary with system components
        args: Command line arguments
    """
    logger.info("Starting triggers")
    
    # Start timer trigger if enabled
    if args.enable_timer:
        logger.info("Starting timer trigger")
        components["timer_trigger"].start()
    
    # Start event trigger if enabled
    if args.enable_events:
        logger.info("Starting event trigger")
        components["event_trigger"].start()
        
        # Register some example callbacks
        components["event_trigger"].register_callback("vix_spike", lambda event: 
            logger.info(f"VIX spike detected: {event}")
        )
        
        components["event_trigger"].register_callback("major_price_change", lambda event: 
            logger.info(f"Major price change detected: {event}")
        )

def stop_triggers(components):
    """
    Stop the triggers for the Market Intelligence system.
    
    Args:
        components: Dictionary with system components
    """
    logger.info("Stopping triggers")
    
    # Stop timer trigger
    components["timer_trigger"].stop()
    
    # Stop event trigger
    components["event_trigger"].stop()

def run_api_server(args):
    """
    Run the FastAPI server in a separate thread.
    
    Args:
        args: Command line arguments
    """
    logger.info(f"Starting API server on port {args.api_port}")
    
    # Run in a separate thread
    thread = threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": api_app,
            "host": args.api_host,
            "port": args.api_port,
            "log_level": "info"
        }
    )
    thread.daemon = True
    thread.start()
    
    return thread

def run_backtest_demo(components):
    """
    Run a demo backtest to showcase the feedback loop.
    
    Args:
        components: Dictionary with system components
    """
    logger.info("Running backtest demo")
    
    # Get top pairs
    top_pairs = components["controller"].get_top_symbol_strategy_pairs(limit=3)
    
    # Run backtest for each pair
    for pair in top_pairs:
        symbol = pair.get("symbol")
        strategy = pair.get("strategy")
        
        logger.info(f"Backtesting {symbol} with {strategy}")
        
        # Run backtest
        result = components["backtest_executor"].backtest_pair(symbol, strategy)
        
        logger.info(f"Backtest result: {result}")
    
    # Get top performing pairs after backtests
    top_performing = components["feedback_system"].get_top_performing_pairs(limit=3)
    
    logger.info(f"Top performing pairs: {top_performing}")

def main():
    """Main function to run the Market Intelligence system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Launch Market Intelligence System")
    
    parser.add_argument("--force-update", action="store_true", help="Force initial update")
    parser.add_argument("--enable-timer", action="store_true", help="Enable timer trigger")
    parser.add_argument("--enable-events", action="store_true", help="Enable event trigger")
    parser.add_argument("--enable-api", action="store_true", help="Enable API server")
    parser.add_argument("--api-host", type=str, default="0.0.0.0", help="API server host")
    parser.add_argument("--api-port", type=int, default=8000, help="API server port")
    parser.add_argument("--run-backtest-demo", action="store_true", help="Run backtest demo")
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        components = initialize_system(args)
        
        # Start triggers
        start_triggers(components, args)
        
        # Run API server if enabled
        api_thread = None
        if args.enable_api:
            api_thread = run_api_server(args)
        
        # Run backtest demo if requested
        if args.run_backtest_demo:
            run_backtest_demo(components)
        
        logger.info("Market Intelligence system running. Press Ctrl+C to stop.")
        
        # Keep the script running until Ctrl+C
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down.")
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    
    finally:
        # Clean up
        try:
            # Stop triggers
            stop_triggers(components)
            
            logger.info("Market Intelligence system stopped")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    main()
