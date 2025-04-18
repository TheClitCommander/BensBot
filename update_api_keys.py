#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_api_keys():
    """Update API keys in both config file and environment variables"""
    
    # Path to the API configuration file
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config', 
        'news_api_config.json'
    )
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return False
    
    # Load the current configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded API configuration from {config_path}")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False
    
    # API keys to set
    api_keys = {
        'NYTIMES_API_KEY': config['apis']['nytimes']['api_key'],
        'FINNHUB_API_KEY': config['apis']['finnhub']['api_key'],
        'MARKETAUX_API_KEY': config['apis']['marketaux']['api_key'],
        'NEWSDATA_API_KEY': config['apis']['newsdata']['api_key'],
        'GNEWS_API_KEY': config['apis']['gnews']['api_key'],
        'MEDIASTACK_API_KEY': config['apis'].get('mediastack', {}).get('api_key', ''),
        'CURRENTS_API_KEY': config['apis'].get('currents', {}).get('api_key', '')
    }
    
    # Set environment variables
    for key, value in api_keys.items():
        if value:
            os.environ[key] = value
            logger.info(f"Set environment variable: {key}")
    
    # Reset API error counts
    for api_name in config['apis']:
        config['apis'][api_name]['error_count'] = 0
        config['apis'][api_name]['enabled'] = True
    
    # Update current usage counters
    config['date'] = datetime.now().strftime('%Y-%m-%d')
    for api_name in config['apis']:
        config['apis'][api_name]['current_usage'] = 0
    
    # Save the updated configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated API configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def test_apis():
    """Test API connectivity with the new keys"""
    try:
        # Import here to avoid circular imports
        from trading_bot.news.api_manager import NewsApiManager
        
        # Initialize news API manager
        news_api = NewsApiManager()
        
        # List of test queries
        test_queries = ["AAPL", "MSFT", "market news"]
        
        # Test first query
        query = test_queries[0]
        logger.info(f"Testing API with query: {query}")
        
        # Try to fetch news using the newly configured APIs
        results = news_api.fetch_news(query, max_results=2)
        
        if results:
            logger.info(f"✅ Successfully fetched {len(results)} articles for '{query}'")
            return True
        else:
            logger.warning(f"⚠️ No results for '{query}' from any API")
            return False
            
    except Exception as e:
        logger.error(f"Error testing APIs: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting API key update process")
    
    # Update API keys
    if update_api_keys():
        logger.info("API keys updated successfully")
        
        # Test APIs
        if test_apis():
            logger.info("API test successful, all systems ready")
        else:
            logger.warning("API test returned no results, keys may still have issues")
    else:
        logger.error("Failed to update API keys")
    
    logger.info("API key update process completed") 