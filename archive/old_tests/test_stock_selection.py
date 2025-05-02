#!/usr/bin/env python3
import os
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# First, import the necessary components
try:
    from trading_bot.stock_selection.stock_selector import StockSelector
    from trading_bot.stock_selection.sentiment_analyzer import SentimentAnalyzer
    from trading_bot.news.api_manager import NewsApiManager
    from trading_bot.data.data_providers import AlpacaDataProvider
    logger.info("Successfully imported required modules")
except Exception as e:
    logger.error(f"Failed to import modules: {str(e)}")
    exit(1)

def test_news_api():
    """Test the news API integration"""
    logger.info("Testing News API Manager...")
    
    # Initialize news API manager
    news_api = NewsApiManager()
    
    # Test with some stocks
    test_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    
    for ticker in test_tickers:
        logger.info(f"Fetching news for {ticker}")
        articles = news_api.fetch_news(ticker, max_results=3)
        
        if articles:
            logger.info(f"✅ Retrieved {len(articles)} articles for {ticker}")
            if len(articles) > 0:
                # Print first article
                first = articles[0]
                logger.info(f"  Title: {first.get('title', 'No title')[:50]}...")
                logger.info(f"  Source: {first.get('source', 'Unknown')}")
                logger.info(f"  Sentiment: {first.get('sentiment', 0):.2f}")
        else:
            logger.warning(f"❌ No articles found for {ticker}")
    
    # Report usage stats
    usage_stats = news_api.get_usage_stats()
    logger.info(f"API Usage: {usage_stats}")
    
    return True

def test_sentiment_analyzer():
    """Test the sentiment analyzer"""
    logger.info("Testing Sentiment Analyzer...")
    
    # Initialize sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    # Test with sample text
    sample_texts = [
        "Company reports strong earnings, beating analyst expectations",
        "Stock price dropped after poor quarterly results",
        "New product announcement receives mixed reviews",
        "CEO resigns amid accounting scandal investigation",
        "Company announces major acquisition to expand market share"
    ]
    
    for text in sample_texts:
        sentiment = analyzer.analyze_text(text)
        compound = sentiment['compound']
        logger.info(f"Text: {text[:40]}... | Sentiment: {compound:.2f}")
    
    return True

def test_stock_selection():
    """Test the stock selection workflow"""
    logger.info("Testing Stock Selection Module...")
    
    # Initialize data provider
    try:
        data_provider = AlpacaDataProvider()
        logger.info("Initialized AlpacaDataProvider")
    except Exception as e:
        logger.error(f"Failed to initialize data provider: {str(e)}")
        # Create a simple mock data provider for testing
        class MockDataProvider:
            def get_historical_data(self, *args, **kwargs):
                return pd.DataFrame({
                    'open': [150, 152, 153, 155, 153, 152, 154, 156, 155, 153],
                    'high': [153, 154, 155, 157, 154, 153, 156, 158, 156, 155],
                    'low': [149, 151, 152, 154, 152, 151, 153, 155, 154, 152],
                    'close': [152, 153, 154, 153, 152, 154, 156, 155, 153, 154],
                    'volume': [10000, 12000, 15000, 11000, 9000, 12500, 13000, 14000, 11500, 10500]
                })
            
            def get_fundamental_data(self, ticker):
                return {
                    'pe_ratio': 25.5,
                    'eps_growth': 15.2,
                    'revenue_growth': 10.5,
                    'profit_margin': 22.3,
                    'debt_to_equity': 0.8
                }
        
        data_provider = MockDataProvider()
        logger.info("Using mock data provider for testing")
    
    # Initialize stock selector
    selector = StockSelector(data_provider)
    logger.info("Initialized StockSelector")
    
    # Test stock scoring
    test_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
    
    try:
        scores = selector.scorer.score_stocks(test_tickers)
        logger.info("Stock scoring successful")
        
        if not scores.empty:
            logger.info("\nStock Scores:")
            for ticker, row in scores.iterrows():
                logger.info(f"{ticker}: {row.get('total_score', 0):.3f}")
        else:
            logger.warning("No scores returned")
    except Exception as e:
        logger.error(f"Error in stock scoring: {str(e)}")
    
    # Test portfolio generation
    try:
        portfolio = selector.generate_portfolio(
            universe=test_tickers,
            total_capital=100000.0,
            max_stocks=3,
            risk_profile='moderate'
        )
        
        logger.info("\nGenerated Portfolio:")
        if not portfolio.empty:
            for _, row in portfolio.iterrows():
                ticker = row.get('ticker', 'Unknown')
                allocation = row.get('allocation', 0)
                dollar_amount = row.get('dollar_amount', 0)
                logger.info(f"{ticker}: {allocation:.1f}% (${dollar_amount:.2f})")
        else:
            logger.warning("Empty portfolio generated")
    except Exception as e:
        logger.error(f"Error in portfolio generation: {str(e)}")
    
    return True

if __name__ == "__main__":
    logger.info("Starting Stock Selection Module tests")
    
    # Test news API integration
    if test_news_api():
        logger.info("✅ News API test completed")
    else:
        logger.error("❌ News API test failed")
    
    # Test sentiment analyzer
    if test_sentiment_analyzer():
        logger.info("✅ Sentiment analyzer test completed")
    else:
        logger.error("❌ Sentiment analyzer test failed")
    
    # Test stock selection workflow
    if test_stock_selection():
        logger.info("✅ Stock selection test completed")
    else:
        logger.error("❌ Stock selection test failed")
    
    logger.info("All tests completed") 