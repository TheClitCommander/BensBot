#!/usr/bin/env python3
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_api_limits():
    """Update API configuration with realistic free tier limits"""
    # Path to the API configuration file
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config', 
        'news_api_config.json'
    )
    
    # Load configuration file
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded API configuration from {config_path}")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False
    
    # Reset usage counters and error counts
    config['date'] = datetime.now().strftime('%Y-%m-%d')
    for api_name in config['apis']:
        config['apis'][api_name]['current_usage'] = 0
        config['apis'][api_name]['error_count'] = 0
        
        # Only enable APIs we're confident about
        if api_name in ['mediastack', 'currents', 'newsdata']:
            config['apis'][api_name]['enabled'] = True
        else:
            config['apis'][api_name]['enabled'] = False
    
    # Save updated configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated API configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def test_mediastack_api():
    """Test Mediastack API to verify it's working"""
    api_key = "3ff958493e0f1d8cf9af5e8425c8f5a3"
    url = "http://api.mediastack.com/v1/news"
    
    params = {
        'access_key': api_key,
        'keywords': 'AAPL',
        'languages': 'en',
        'limit': 3,
        'sort': 'published_desc'
    }
    
    logger.info(f"Testing Mediastack API with 'AAPL' query...")
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('data', [])
            
            logger.info(f"✅ Mediastack API working: retrieved {len(articles)} articles")
            
            # Print first article if available
            if articles:
                logger.info(f"First article: {articles[0].get('title', 'No title')}")
            
            return True
        else:
            logger.error(f"❌ Mediastack API error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Mediastack API: {str(e)}")
        return False

def test_currents_api():
    """Test Currents API to verify it's working"""
    api_key = "O5_JjrWdlLN2v93iuKbhEhA9OSIYfChf4Cx9XE9xXgW1oYTC"
    url = "https://api.currentsapi.services/v1/search"
    
    params = {
        'apiKey': api_key,
        'keywords': 'MSFT',
        'language': 'en',
        'limit': 3
    }
    
    logger.info(f"Testing Currents API with 'MSFT' query...")
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('news', [])
            
            logger.info(f"✅ Currents API working: retrieved {len(articles)} articles")
            
            # Print first article if available
            if articles:
                logger.info(f"First article: {articles[0].get('title', 'No title')}")
            
            return True
        else:
            logger.error(f"❌ Currents API error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Currents API: {str(e)}")
        return False

def test_newsdata_api():
    """Test NewsData API to verify it's working"""
    api_key = "pub_81036c20e73907398317875951d4569722f2a"
    url = "https://newsdata.io/api/1/news"
    
    params = {
        'apikey': api_key,
        'q': 'AMZN',
        'language': 'en',
        'size': 3
    }
    
    logger.info(f"Testing NewsData API with 'AMZN' query...")
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('results', [])
            
            logger.info(f"✅ NewsData API working: retrieved {len(articles)} articles")
            
            # Print first article if available
            if articles:
                logger.info(f"First article: {articles[0].get('title', 'No title')}")
            
            return True
        else:
            logger.error(f"❌ NewsData API error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing NewsData API: {str(e)}")
        return False

def set_environment_variables():
    """Set API keys as environment variables"""
    os.environ['MEDIASTACK_API_KEY'] = "3ff958493e0f1d8cf9af5e8425c8f5a3"
    os.environ['CURRENTS_API_KEY'] = "O5_JjrWdlLN2v93iuKbhEhA9OSIYfChf4Cx9XE9xXgW1oYTC"
    os.environ['NEWSDATA_API_KEY'] = "pub_81036c20e73907398317875951d4569722f2a"
    logger.info("Set API keys as environment variables")

if __name__ == "__main__":
    logger.info("Starting API configuration update and testing")
    
    # Update API configuration
    if update_api_limits():
        logger.info("API configuration updated successfully")
    else:
        logger.error("Failed to update API configuration")
        exit(1)
    
    # Set environment variables
    set_environment_variables()
    
    # Test each enabled API
    mediastack_works = test_mediastack_api()
    time.sleep(1)  # Wait between API calls
    currents_works = test_currents_api()
    time.sleep(1)  # Wait between API calls
    newsdata_works = test_newsdata_api()
    
    # Summarize results
    logger.info("\n=== API Test Results ===")
    logger.info(f"Mediastack API: {'✅ Working' if mediastack_works else '❌ Failed'}")
    logger.info(f"Currents API: {'✅ Working' if currents_works else '❌ Failed'}")
    logger.info(f"NewsData API: {'✅ Working' if newsdata_works else '❌ Failed'}")
    
    # Overall status
    working_count = sum([mediastack_works, currents_works, newsdata_works])
    if working_count == 3:
        logger.info("✅ All APIs working correctly!")
    elif working_count > 0:
        logger.warning(f"⚠️ {working_count}/3 APIs working, but some failed")
    else:
        logger.error("❌ All APIs failed - check credentials and limits")
    
    logger.info("API configuration update and testing completed") 