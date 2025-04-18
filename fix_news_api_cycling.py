#!/usr/bin/env python3
"""
News API cycling script to prevent rate limiting issues
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsApiManager:
    """
    Manages multiple news API providers with intelligent cycling to prevent rate limiting
    """
    
    def __init__(self, config_path: str = "news_api_config.json"):
        """
        Initialize the news API manager
        
        Args:
            config_path: Path to the API configuration file
        """
        self.config_path = config_path
        self.api_data = self._load_or_create_config()
        self._update_usage_stats()
        
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load or create API configuration"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded API configuration from {self.config_path}")
                    return config
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading config: {e}, creating new configuration")
        
        # Create default configuration
        default_config = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'apis': {
                'nytimes': {
                    'api_key': os.environ.get('NYTIMES_API_KEY', ''),
                    'base_url': 'https://api.nytimes.com/svc/search/v2/articlesearch.json',
                    'daily_limit': 500,
                    'current_usage': 0,
                    'cooldown_minutes': 5,
                    'priority': 1,
                    'last_used': 0,
                    'enabled': True
                },
                'finnhub': {
                    'api_key': os.environ.get('FINNHUB_API_KEY', ''),
                    'base_url': 'https://finnhub.io/api/v1/company-news',
                    'daily_limit': 250,
                    'current_usage': 0,
                    'cooldown_minutes': 10,
                    'priority': 2,
                    'last_used': 0,
                    'enabled': True
                },
                'newsapi': {
                    'api_key': os.environ.get('NEWSAPI_API_KEY', ''),
                    'base_url': 'https://newsapi.org/v2/everything',
                    'daily_limit': 100,
                    'current_usage': 0,
                    'cooldown_minutes': 15,
                    'priority': 3,
                    'last_used': 0,
                    'enabled': True
                },
                'marketaux': {
                    'api_key': os.environ.get('MARKETAUX_API_KEY', ''),
                    'base_url': 'https://api.marketaux.com/v1/news/all',
                    'daily_limit': 100,
                    'current_usage': 0,
                    'cooldown_minutes': 300,  # 5 minutes
                    'priority': 3,
                    'last_used': 0,
                    'enabled': True
                },
                'newsdata': {
                    'api_key': os.environ.get('NEWSDATA_API_KEY', ''),
                    'base_url': 'https://newsdata.io/api/1/news',
                    'daily_limit': 200,
                    'current_usage': 0,
                    'cooldown_minutes': 3600,  # 1 hour
                    'priority': 4,
                    'last_used': 0,
                    'enabled': True
                },
                'gnews': {
                    'api_key': os.environ.get('GNEWS_API_KEY', ''),
                    'base_url': 'https://gnews.io/api/v4/search',
                    'daily_limit': 100,
                    'current_usage': 0,
                    'cooldown_minutes': 900,  # 15 minutes
                    'priority': 5,
                    'last_used': 0,
                    'enabled': True
                },
                'mediastack': {
                    'api_key': os.environ.get('MEDIASTACK_API_KEY', ''),
                    'base_url': 'http://api.mediastack.com/v1/news',
                    'daily_limit': 1000,
                    'current_usage': 0,
                    'cooldown_minutes': 60,  # 1 minute
                    'priority': 6,
                    'last_used': 0,
                    'enabled': True
                },
                'currents': {
                    'api_key': os.environ.get('CURRENTS_API_KEY', ''),
                    'base_url': 'https://api.currentsapi.services/v1/search',
                    'daily_limit': 600,
                    'current_usage': 0,
                    'cooldown_minutes': 120,  # 2 minutes
                    'priority': 7,
                    'last_used': 0,
                    'enabled': True
                }
            },
            'cache': {
                'max_age_minutes': 60,
                'entries': {}
            },
            'settings': {
                'use_cache': True,
                'max_retries': 3,
                'timeout_seconds': 10,
                'auto_disable_on_error': True,
                'error_threshold': 3
            }
        }
        
        self._save_config(default_config)
        logger.info(f"Created new API configuration at {self.config_path}")
        return default_config
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save API configuration to file"""
        if config is None:
            config = self.api_data
            
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _update_usage_stats(self) -> None:
        """Reset usage counters if it's a new day"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        if self.api_data.get('date') != current_date:
            logger.info("New day detected, resetting API usage counters")
            for api_name in self.api_data['apis']:
                self.api_data['apis'][api_name]['current_usage'] = 0
            
            # Clear old cache entries
            self.api_data['cache']['entries'] = {}
            self.api_data['date'] = current_date
            self._save_config()
    
    def select_api(self, query_type: str = 'stock_news') -> Optional[str]:
        """
        Select the best API to use for the current request
        
        Args:
            query_type: Type of news query ('stock_news', 'market_news', etc.)
            
        Returns:
            Name of the API to use, or None if no APIs are available
        """
        # Update stats first
        self._update_usage_stats()
        
        # Get all available APIs
        available_apis = []
        current_time = time.time()
        
        for api_name, api_info in self.api_data['apis'].items():
            # Skip disabled APIs
            if not api_info.get('enabled', True):
                continue
                
            # Check if API has a valid key
            if not api_info.get('api_key'):
                continue
            
            # Check if API is under usage limit
            usage_percent = api_info['current_usage'] / api_info['daily_limit']
            if usage_percent >= 0.95:
                logger.debug(f"API {api_name} usage at {usage_percent*100:.1f}%, skipping")
                continue
            
            # Check if cooldown period has passed
            last_used = api_info.get('last_used', 0)
            time_since_last_call = current_time - last_used
            cooldown_time = api_info['cooldown_minutes'] * 60
            
            if time_since_last_call < cooldown_time:
                logger.debug(f"API {api_name} in cooldown, {cooldown_time - time_since_last_call:.1f}s remaining")
                continue
            
            # API is available
            available_apis.append({
                'name': api_name,
                'priority': api_info['priority'],
                'usage_percent': usage_percent
            })
        
        if not available_apis:
            logger.warning("No APIs available - all at limit or in cooldown")
            return None
        
        # Sort by priority first, then by usage percentage
        available_apis.sort(key=lambda x: (x['priority'], x['usage_percent']))
        selected_api = available_apis[0]['name']
        
        logger.info(f"Selected API: {selected_api}")
        return selected_api
    
    def fetch_news(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a query using the best available API
        
        Args:
            query: Search query (ticker symbol, company name, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of news articles as dictionaries
        """
        # Check cache first if enabled
        if self.api_data['settings']['use_cache']:
            cached_results = self._get_from_cache(query)
            if cached_results:
                logger.info(f"Using cached results for '{query}'")
                return cached_results[:max_results]
        
        # Select API to use
        api_name = self.select_api()
        if not api_name:
            logger.warning("No available APIs, returning empty results")
            return []
        
        # Get API config
        api_config = self.api_data['apis'][api_name]
        
        # Make the API request
        try:
            # Different API implementations
            if api_name == 'nytimes':
                results = self._fetch_from_nytimes(query, api_config, max_results)
            elif api_name == 'finnhub':
                results = self._fetch_from_finnhub(query, api_config, max_results)
            elif api_name == 'newsapi':
                results = self._fetch_from_newsapi(query, api_config, max_results)
            elif api_name == 'marketaux':
                results = self._fetch_from_marketaux(query, api_config, max_results)
            elif api_name == 'newsdata':
                results = self._fetch_from_newsdata(query, api_config, max_results)
            elif api_name == 'gnews':
                results = self._fetch_from_gnews(query, api_config, max_results)
            elif api_name == 'mediastack':
                results = self._fetch_from_mediastack(query, api_config, max_results)
            elif api_name == 'currents':
                results = self._fetch_from_currents(query, api_config, max_results)
            else:
                logger.warning(f"Unknown API: {api_name}")
                return []
            
            # Update usage stats
            self._log_api_call(api_name)
            
            # Cache results if we got any
            if results and self.api_data['settings']['use_cache']:
                self._add_to_cache(query, results)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error fetching news from {api_name}: {str(e)}")
            self._handle_api_error(api_name)
            return []
    
    def _get_from_cache(self, query: str) -> List[Dict[str, Any]]:
        """Get results from cache if they exist and are not expired"""
        cache = self.api_data['cache']
        query_key = query.lower().strip()
        
        if query_key not in cache['entries']:
            return []
        
        entry = cache['entries'][query_key]
        timestamp = entry.get('timestamp', 0)
        max_age = cache['max_age_minutes'] * 60
        
        # Check if entry is expired
        if time.time() - timestamp > max_age:
            logger.debug(f"Cache entry for '{query}' expired")
            return []
        
        return entry.get('results', [])
    
    def _add_to_cache(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Add results to cache"""
        query_key = query.lower().strip()
        
        self.api_data['cache']['entries'][query_key] = {
            'timestamp': time.time(),
            'results': results
        }
        
        # Save the updated cache
        self._save_config()
    
    def _log_api_call(self, api_name: str) -> None:
        """Log an API call and update usage statistics"""
        if api_name not in self.api_data['apis']:
            return
        
        api_info = self.api_data['apis'][api_name]
        api_info['current_usage'] += 1
        api_info['last_used'] = time.time()
        
        logger.info(f"API call to {api_name}. Total today: {api_info['current_usage']}")
        self._save_config()
    
    def _handle_api_error(self, api_name: str) -> None:
        """Handle API error by updating error counters and disabling if needed"""
        if api_name not in self.api_data['apis']:
            return
        
        api_info = self.api_data['apis'][api_name]
        error_count = api_info.get('error_count', 0) + 1
        api_info['error_count'] = error_count
        
        # Automatically disable API if it exceeds error threshold
        if (self.api_data['settings']['auto_disable_on_error'] and 
            error_count >= self.api_data['settings']['error_threshold']):
            logger.warning(f"Disabling {api_name} API due to repeated errors")
            api_info['enabled'] = False
        
        self._save_config()
    
    def _fetch_from_nytimes(self, query: str, api_config: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Fetch news from New York Times API"""
        params = {
            'q': query,
            'api-key': api_config['api_key'],
            'sort': 'newest',
            'page': 0
        }
        
        response = requests.get(
            api_config['base_url'],
            params=params,
            timeout=self.api_data['settings']['timeout_seconds']
        )
        
        if response.status_code != 200:
            logger.warning(f"NY Times API error: {response.status_code}")
            raise Exception(f"API error: {response.status_code}")
        
        data = response.json()
        articles = data.get('response', {}).get('docs', [])
        
        # Transform to standard format
        results = []
        for article in articles:
            results.append({
                'title': article.get('headline', {}).get('main', ''),
                'description': article.get('abstract', ''),
                'url': article.get('web_url', ''),
                'source': 'The New York Times',
                'published_at': article.get('pub_date', ''),
                'image_url': self._get_nytimes_image(article),
                'sentiment': self._calculate_sentiment(article.get('abstract', '')),
                'categories': [section.get('name', '') for section in article.get('section_name', [])]
            })
        
        return results
    
    def _fetch_from_finnhub(self, ticker: str, api_config: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Fetch news from Finnhub API"""
        # Format dates for Finnhub (requires YYYY-MM-DD format)
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        params = {
            'symbol': ticker,
            'from': week_ago.strftime('%Y-%m-%d'),
            'to': today.strftime('%Y-%m-%d'),
            'token': api_config['api_key']
        }
        
        response = requests.get(
            api_config['base_url'],
            params=params,
            timeout=self.api_data['settings']['timeout_seconds']
        )
        
        if response.status_code != 200:
            logger.warning(f"Finnhub API error: {response.status_code}")
            raise Exception(f"API error: {response.status_code}")
        
        articles = response.json()
        
        # Transform to standard format
        results = []
        for article in articles:
            results.append({
                'title': article.get('headline', ''),
                'description': article.get('summary', ''),
                'url': article.get('url', ''),
                'source': article.get('source', 'Finnhub'),
                'published_at': article.get('datetime', ''),
                'image_url': article.get('image', ''),
                'sentiment': self._calculate_sentiment(article.get('summary', '')),
                'categories': [article.get('category', '')]
            })
        
        return results
    
    # Add other API methods as needed (newsapi, marketaux, etc.)
    
    def _fetch_from_newsapi(self, query: str, api_config: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """Fetch news from News API"""
        params = {
            'q': query,
            'apiKey': api_config['api_key'],
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': max_results
        }
        
        response = requests.get(
            api_config['base_url'],
            params=params,
            timeout=self.api_data['settings']['timeout_seconds']
        )
        
        if response.status_code != 200:
            logger.warning(f"News API error: {response.status_code}")
            raise Exception(f"API error: {response.status_code}")
        
        data = response.json()
        articles = data.get('articles', [])
        
        # Transform to standard format
        results = []
        for article in articles:
            results.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'NewsAPI'),
                'published_at': article.get('publishedAt', ''),
                'image_url': article.get('urlToImage', ''),
                'sentiment': self._calculate_sentiment(article.get('description', '')),
                'categories': []  # News API doesn't provide categories
            })
        
        return results
    
    def _get_nytimes_image(self, article: Dict[str, Any]) -> str:
        """Extract image URL from NY Times article"""
        multimedia = article.get('multimedia', [])
        if multimedia:
            for media in multimedia:
                if media.get('type') == 'image':
                    return f"https://www.nytimes.com/{media.get('url', '')}"
        return ''
    
    def _calculate_sentiment(self, text: str) -> float:
        """
        Calculate a simple sentiment score for text
        
        This is a very basic implementation. In production, you would use
        a proper NLP library like TextBlob, VADER, or a machine learning model.
        
        Returns a score between -1.0 (negative) and 1.0 (positive)
        """
        # Simple word lists for demonstration
        positive_words = [
            'up', 'gain', 'gains', 'positive', 'profit', 'profits', 'growth', 'increase',
            'increases', 'increased', 'higher', 'bull', 'bullish', 'opportunity', 'opportunities',
            'success', 'successful', 'win', 'winning', 'advantage', 'advantages', 'strong',
            'strength', 'strengthen', 'strengthened', 'grow', 'growing', 'grew', 'risen',
            'rises', 'rise', 'outperform', 'outperforms', 'outperformed', 'beat', 'beats'
        ]
        
        negative_words = [
            'down', 'loss', 'losses', 'negative', 'deficit', 'decline', 'declines', 'decreased',
            'lower', 'bear', 'bearish', 'risk', 'risks', 'risky', 'fail', 'fails', 'failed',
            'failure', 'weak', 'weakness', 'weakened', 'fall', 'falling', 'fell', 'drop',
            'drops', 'dropped', 'shrink', 'shrinks', 'shrinking', 'shrank', 'underperform',
            'underperforms', 'underperformed', 'miss', 'misses', 'missed'
        ]
        
        if not text:
            return 0.0
            
        text = text.lower()
        words = text.split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate sentiment score (-1 to 1)
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
            
        return (positive_count - negative_count) / total_count
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get current API usage statistics"""
        return {
            api_name: api_info['current_usage'] 
            for api_name, api_info in self.api_data['apis'].items()
        }
    
    def reset_api_errors(self, api_name: Optional[str] = None) -> None:
        """
        Reset error count for specific API or all APIs
        
        Args:
            api_name: Name of API to reset, or None to reset all
        """
        if api_name:
            if api_name in self.api_data['apis']:
                self.api_data['apis'][api_name]['error_count'] = 0
                self.api_data['apis'][api_name]['enabled'] = True
                logger.info(f"Reset errors for {api_name} API")
        else:
            # Reset all APIs
            for name in self.api_data['apis']:
                self.api_data['apis'][name]['error_count'] = 0
                self.api_data['apis'][name]['enabled'] = True
            logger.info("Reset errors for all APIs")
        
        self._save_config()

def main():
    """Test the news API manager"""
    api_manager = NewsApiManager()
    
    # Print current API usage
    logger.info(f"Current API usage: {api_manager.get_usage_stats()}")
    
    # Test fetching news for a ticker
    ticker = "AAPL"
    logger.info(f"Fetching news for {ticker}...")
    
    articles = api_manager.fetch_news(ticker, max_results=5)
    
    logger.info(f"Found {len(articles)} articles for {ticker}")
    for i, article in enumerate(articles):
        logger.info(f"{i+1}. {article['title']} ({article['source']})")
    
    # Print updated API usage
    logger.info(f"Updated API usage: {api_manager.get_usage_stats()}")

if __name__ == "__main__":
    main() 