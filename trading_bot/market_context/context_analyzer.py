import requests
import json
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from trading_bot.security.security_utils import redact_sensitive_data
from trading_bot.utils.llm_client import analyze_with_gpt4

logger = logging.getLogger(__name__)

class MarketContextAnalyzer:
    """
    Analyzes market context by gathering news from multiple sources and processing with AI
    """
    
    def __init__(self, config):
        """
        Initialize with API keys and configuration
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.marketaux_api_key = config.get("MARKETAUX_API_KEY", "7PgROm6BE4m6ejBW8unmZnnYS6kIygu5lwzpfd9K")
        self.openai_api_key = config.get("OPENAI_API_KEY")
        self.marketaux_url = config.get("MARKETAUX_URL", "https://api.marketaux.com/v1/news/all")
        self.finviz_news_url = config.get("FINVIZ_NEWS_URL", "https://finviz.com/news.ashx")
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        # Default list of available trading strategies
        self.strategy_list = config.get("STRATEGY_LIST", [
            "iron_condor", "gap_fill_daytrade", "theta_spread",
            "breakout_swing", "pullback_to_moving_average",
            "volatility_squeeze", "earnings_strangle"
        ])
        
        # Cache for context data
        self.context_cache = {}
        self.cache_expiry = config.get("CACHE_EXPIRY_MINUTES", 30)
        
    def get_marketaux_headlines(self, limit=20, hours_back=24):
        """
        Fetch headlines from Marketaux API
        
        Args:
            limit: Maximum number of headlines to fetch
            hours_back: Hours to look back for news
            
        Returns:
            List of headlines and detailed article data
        """
        try:
            # Calculate time for published_after parameter
            published_after = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            
            params = {
                "api_token": self.marketaux_api_key,
                "limit": limit,
                "published_after": published_after,
                "language": "en",
                "filter_entities": "true"
            }
            
            response = requests.get(self.marketaux_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Log successful fetch
            article_count = len(data.get('data', []))
            logger.info(f"Successfully fetched {article_count} articles from Marketaux")
            
            # Extract headlines and detailed data
            headlines = []
            detailed_data = []
            
            for article in data.get('data', []):
                headlines.append(article['title'])
                
                # Extract entities (tickers, etc.) if available
                entities = []
                for entity in article.get('entities', []):
                    if entity.get('type') == 'ticker' and entity.get('symbol'):
                        entities.append(entity.get('symbol'))
                
                # Add detailed article info
                detailed_data.append({
                    'title': article['title'],
                    'description': article.get('description', ''),
                    'source': article.get('source', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('published_at', ''),
                    'entities': entities,
                    'sentiment': article.get('sentiment', ''),
                })
            
            return {
                'headlines': headlines,
                'detailed_data': detailed_data
            }
            
        except Exception as e:
            logger.error(f"Marketaux headlines fetch failed: {str(e)}")
            return {'headlines': [], 'detailed_data': []}
    
    def scrape_finviz_headlines(self, limit=20):
        """
        Scrape financial news headlines from Finviz
        
        Args:
            limit: Maximum number of headlines to fetch
            
        Returns:
            List of headlines and detailed article data
        """
        try:
            response = requests.get(self.finviz_news_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            news_table = soup.select("table.fullview-news-outer tr")
            
            headlines = []
            detailed_data = []
            
            for row in news_table[:limit]:
                try:
                    if len(row.find_all("td")) < 2:
                        continue
                        
                    time_cell, content_cell = row.find_all("td")
                    
                    # Extract time
                    time_text = time_cell.text.strip()
                    
                    # Extract title and link
                    link_element = content_cell.find("a")
                    if not link_element:
                        continue
                        
                    title = link_element.text.strip()
                    link = link_element["href"]
                    
                    # Extract source
                    source_element = content_cell.find("span", class_="news-link-right")
                    source = source_element.text.strip() if source_element else "Unknown"
                    
                    # Add headline to list
                    headlines.append(title)
                    
                    # Add detailed data
                    detailed_data.append({
                        'title': title,
                        'source': source,
                        'url': link,
                        'time': time_text
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing Finviz news row: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(headlines)} headlines from Finviz")
            return {
                'headlines': headlines,
                'detailed_data': detailed_data
            }
            
        except Exception as e:
            logger.error(f"Finviz scraping failed: {str(e)}")
            return {'headlines': [], 'detailed_data': []}
    
    def analyze_sentiment_with_ai(self, headlines, detailed_data=None, focus_symbols=None):
        """
        Analyze market sentiment using AI
        
        Args:
            headlines: List of news headlines
            detailed_data: Optional detailed article data
            focus_symbols: Optional list of ticker symbols to focus on
            
        Returns:
            Dictionary containing sentiment analysis
        """
        try:
            # Limit headlines to a reasonable number for analysis
            headlines_for_analysis = headlines[:20]
            joined_news = "\n".join(f"- {headline}" for headline in headlines_for_analysis)
            
            # Prepare additional context if available
            additional_context = ""
            if detailed_data and len(detailed_data) > 0:
                additional_context += "\n\nAdditional details about the news:"
                for i, article in enumerate(detailed_data[:5], 1):
                    source = article.get('source', 'Unknown')
                    published = article.get('published_at', '')
                    entities = ", ".join(article.get('entities', []))
                    
                    additional_context += f"\n{i}. [{source}] {article.get('title', '')}"
                    if entities:
                        additional_context += f"\n   Related symbols: {entities}"
            
            # Add focus symbols if provided
            symbol_context = ""
            if focus_symbols:
                symbol_list = ", ".join(focus_symbols)
                symbol_context = f"\n\nPay special attention to news related to these symbols: {symbol_list}"
            
            # Build the prompt
            prompt = f"""
            You are an expert financial market analyst with decades of experience in market sentiment analysis.
            
            Analyze the following recent financial news headlines:{joined_news}{additional_context}{symbol_context}
            
            Based on this news, provide:
            1. The current market sentiment (bullish, bearish, volatile, or neutral)
            2. A confidence score (0 to 1, where 1 is highest confidence)
            3. The top 3 market-moving news or trends (summarize briefly)
            4. The top 3 recommended trading strategies from this list: {', '.join(self.strategy_list)}
            
            Include reasoning for your sentiment assessment and strategy recommendations.
            Respond in the following JSON format:
            {{
                "bias": "bullish|bearish|volatile|neutral",
                "confidence": 0.75,
                "triggers": [
                    "Brief description of market driver 1",
                    "Brief description of market driver 2",
                    "Brief description of market driver 3"
                ],
                "suggested_strategies": [
                    "strategy_name_1",
                    "strategy_name_2",
                    "strategy_name_3"
                ],
                "reasoning": "Brief explanation of your analysis"
            }}
            """
            
            # Call GPT-4 for analysis
            result = analyze_with_gpt4(prompt)
            
            # Parse result
            analysis = json.loads(result)
            
            # Add timestamp and source data
            analysis['timestamp'] = datetime.utcnow().isoformat()
            analysis['data_sources'] = ['marketaux', 'finviz']
            analysis['headline_count'] = len(headlines)
            
            logger.info(f"AI analysis complete. Market bias: {analysis.get('bias')}, confidence: {analysis.get('confidence')}")
            return analysis
            
        except Exception as e:
            logger.error(f"GPT sentiment analysis failed: {str(e)}")
            return {
                "bias": "neutral",
                "confidence": 0.5,
                "triggers": ["AI analysis error"],
                "suggested_strategies": [],
                "reasoning": f"Error during analysis: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_market_context(self, force_refresh=False, focus_symbols=None):
        """
        Main method to get current market context
        
        Args:
            force_refresh: Force refresh instead of using cache
            focus_symbols: Optional list of ticker symbols to focus on
            
        Returns:
            Dictionary containing market context analysis
        """
        # Define cache key
        cache_key = "global"
        if focus_symbols:
            cache_key = f"symbols_{','.join(sorted(focus_symbols))}"
            
        # Check cache first unless force refresh
        if not force_refresh and cache_key in self.context_cache:
            cached_time, cached_data = self.context_cache[cache_key]
            cache_age_minutes = (datetime.utcnow() - cached_time).total_seconds() / 60
            
            if cache_age_minutes < self.cache_expiry:
                logger.info(f"Using cached market context (age: {cache_age_minutes:.1f} min)")
                return cached_data
        
        # Fetch fresh news data
        logger.info("Fetching fresh market news data")
        marketaux_data = self.get_marketaux_headlines()
        finviz_data = self.scrape_finviz_headlines()
        
        # Combine headlines from all sources
        all_headlines = marketaux_data['headlines'] + finviz_data['headlines']
        all_detailed_data = marketaux_data['detailed_data'] + finviz_data['detailed_data']
        
        # Check if we have enough data
        if not all_headlines:
            logger.warning("No headlines found for market context analysis")
            result = {
                "bias": "neutral",
                "confidence": 0.0,
                "triggers": ["Insufficient market data"],
                "suggested_strategies": [],
                "reasoning": "No recent market news available for analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Run AI analysis
            result = self.analyze_sentiment_with_ai(
                all_headlines, 
                all_detailed_data,
                focus_symbols
            )
        
        # Update cache
        self.context_cache[cache_key] = (datetime.utcnow(), result)
        
        # Redact sensitive data for logging
        safe_result = redact_sensitive_data(result)
        logger.info(f"Market context analysis complete: {json.dumps(safe_result)}")
        
        return result 