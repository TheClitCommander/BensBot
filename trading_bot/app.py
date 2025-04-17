from flask import Flask
import os
from dotenv import load_dotenv
import logging
import threading

# Load environment variables
load_dotenv()

# Import API routes
from trading_bot.api.context_routes import context_bp

# Import market context analyzer and scheduler
from trading_bot.market_context.context_analyzer import MarketContextAnalyzer
from trading_bot.market_context.adaptive_context_scheduler import AdaptiveContextScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app(start_scheduler=True):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', os.urandom(24).hex()),
        MARKETAUX_API_KEY=os.getenv('MARKETAUX_API_KEY', '7PgROm6BE4m6ejBW8unmZnnYS6kIygu5lwzpfd9K'),
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'),
        STRATEGY_LIST=[
            "iron_condor", "gap_fill_daytrade", "theta_spread",
            "breakout_swing", "pullback_to_moving_average",
            "volatility_squeeze", "earnings_strangle"
        ],
        MARKET_HOURS_START=os.getenv('MARKET_HOURS_START', '05:00'),
        MARKET_HOURS_END=os.getenv('MARKET_HOURS_END', '16:00'),
        MARKET_HOURS_INTERVAL=int(os.getenv('MARKET_HOURS_INTERVAL', '15')),
        AFTER_HOURS_INTERVAL=int(os.getenv('AFTER_HOURS_INTERVAL', '60')),
        CONTEXT_OUTPUT_DIR=os.getenv('CONTEXT_OUTPUT_DIR', 'data/market_context')
    )
    
    # Initialize context analyzer
    context_analyzer = MarketContextAnalyzer({
        "MARKETAUX_API_KEY": app.config['MARKETAUX_API_KEY'],
        "OPENAI_API_KEY": app.config['OPENAI_API_KEY'],
        "STRATEGY_LIST": app.config['STRATEGY_LIST'],
        "CACHE_EXPIRY_MINUTES": 30
    })
    
    # Initialize adaptive context scheduler
    scheduler_config = {
        "MARKETAUX_API_KEY": app.config['MARKETAUX_API_KEY'],
        "OPENAI_API_KEY": app.config['OPENAI_API_KEY'],
        "STRATEGY_LIST": app.config['STRATEGY_LIST'],
        "OUTPUT_DIR": app.config['CONTEXT_OUTPUT_DIR'],
        "MARKET_HOURS_START": app.config['MARKET_HOURS_START'],
        "MARKET_HOURS_END": app.config['MARKET_HOURS_END'],
        "MARKET_HOURS_INTERVAL": app.config['MARKET_HOURS_INTERVAL'],
        "AFTER_HOURS_INTERVAL": app.config['AFTER_HOURS_INTERVAL']
    }
    
    context_scheduler = AdaptiveContextScheduler(scheduler_config)
    
    # Add components to app config for use in routes
    app.config['MARKET_CONTEXT_ANALYZER'] = context_analyzer
    app.config['CONTEXT_SCHEDULER'] = context_scheduler
    
    # Start the scheduler if requested
    if start_scheduler:
        # Start the scheduler in a separate thread
        def start_scheduler():
            logger.info("Starting adaptive context scheduler from Flask app")
            context_scheduler.start()
        
        # Start in a background thread to not block app startup
        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    # Register blueprints
    app.register_blueprint(context_bp)
    
    @app.route('/health')
    def health_check():
        """Simple health check endpoint"""
        scheduler_status = "running" if context_scheduler.is_running else "stopped"
        market_hours = "active" if context_scheduler.is_market_hours() else "inactive"
        
        return {
            'status': 'healthy', 
            'version': '1.0.0',
            'scheduler': scheduler_status,
            'market_hours': market_hours
        }
    
    # Cleanup on app shutdown
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        scheduler = app.config.get('CONTEXT_SCHEDULER')
        if scheduler and scheduler.is_running:
            logger.info("Stopping context scheduler on app shutdown")
            scheduler.stop()
    
    # Log startup
    logger.info("Trading bot application initialized")
    
    return app

# Run app if executed directly
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True) 