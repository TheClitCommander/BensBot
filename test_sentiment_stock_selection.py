#!/usr/bin/env python3
import os
import logging
import pandas as pd
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set environment variables for the API keys
os.environ['MEDIASTACK_API_KEY'] = "3ff958493e0f1d8cf9af5e8425c8f5a3"

class MockDataProvider:
    """Mock data provider for testing the stock selection system"""
    def get_historical_data(self, *args, **kwargs):
        # Return a simple DataFrame with mock price data
        return pd.DataFrame({
            'open': [150, 152, 153, 155, 153, 152, 154, 156, 155, 153],
            'high': [153, 154, 155, 157, 154, 153, 156, 158, 156, 155],
            'low': [149, 151, 152, 154, 152, 151, 153, 155, 154, 152],
            'close': [152, 153, 154, 153, 152, 154, 156, 155, 153, 154],
            'volume': [10000, 12000, 15000, 11000, 9000, 12500, 13000, 14000, 11500, 10500]
        })
    
    def get_fundamental_data(self, ticker):
        # Return mock fundamental data
        return {
            'pe_ratio': 25.5,
            'eps_growth': 15.2,
            'revenue_growth': 10.5,
            'profit_margin': 22.3,
            'debt_to_equity': 0.8
        }
        
    def get_sector(self, ticker):
        # Return a mock sector
        sectors = {
            'AAPL': 'Technology', 
            'MSFT': 'Technology',
            'GOOGL': 'Technology',
            'AMZN': 'Consumer Cyclical',
            'META': 'Communication Services'
        }
        return sectors.get(ticker, 'Technology')
    
    def get_current_price(self, ticker):
        # Return a mock current price
        prices = {'AAPL': 175.50, 'MSFT': 340.25, 'GOOGL': 158.75, 'AMZN': 178.30, 'META': 485.15}
        return prices.get(ticker, 100.0)

def test_sentiment_analysis():
    """Test the sentiment analyzer with a single ticker"""
    try:
        from trading_bot.stock_selection.sentiment_analyzer import SentimentAnalyzer
        logger.info("Testing basic sentiment analyzer...")
        
        # Create sentiment analyzer
        analyzer = SentimentAnalyzer()
        
        # Test with sample text
        sample_texts = [
            "Apple reports strong quarterly results with iPhone sales exceeding expectations",
            "Microsoft's cloud services revenue declined, causing concern among investors",
            "Google faces regulatory challenges but maintains strong market position",
            "Amazon announces plans to expand into new markets, shares up 3%",
            "Meta's VR division continues to lose money despite technological advances"
        ]
        
        for text in sample_texts:
            sentiment = analyzer.analyze_text(text)
            logger.info(f"Text: '{text[:40]}...' | Sentiment score: {sentiment['compound']:.2f}")
            
        logger.info("Basic sentiment analysis test completed\n")
        return True
        
    except Exception as e:
        logger.error(f"Sentiment analyzer test failed: {str(e)}")
        return False

def test_enhanced_sentiment():
    """Test the enhanced sentiment analyzer with API integration"""
    try:
        from trading_bot.stock_selection.sentiment_enhancer import EnhancedSentimentAnalyzer
        logger.info("Testing enhanced sentiment analyzer with API integration...")
        
        # Create enhanced sentiment analyzer
        enhancer = EnhancedSentimentAnalyzer()
        
        # Test with a small set of tickers to conserve API calls
        tickers = ["AAPL"]
        
        for ticker in tickers:
            logger.info(f"Analyzing sentiment for {ticker}...")
            start_time = time.time()
            sentiment = enhancer.analyze_ticker_sentiment(ticker, news_days=5)
            end_time = time.time()
            
            logger.info(f"Sentiment analysis for {ticker} completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Sentiment classification: {sentiment.get('classification', 'N/A')}")
            logger.info(f"Composite score: {sentiment.get('composite_score', 0):.3f}")
            logger.info(f"Confidence: {sentiment.get('confidence', 0):.2f}")
            logger.info(f"News count: {sentiment.get('news_count', 0)}")
            
            # Brief pause to avoid hammering APIs
            time.sleep(1)
            
        logger.info("Enhanced sentiment analysis test completed\n")
        return True
        
    except Exception as e:
        logger.error(f"Enhanced sentiment test failed: {str(e)}")
        return False

def test_stock_scoring():
    """Test the stock scoring system"""
    try:
        from trading_bot.stock_selection.stock_scorer import StockScorer
        logger.info("Testing stock scoring system...")
        
        # Initialize with mock data provider
        data_provider = MockDataProvider()
        scorer = StockScorer(data_provider)
        
        # Test scoring with a small set of tickers
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        # Create mock sentiment data
        sentiment_data = {
            'AAPL': {'sentiment_score': 0.75},
            'MSFT': {'sentiment_score': 0.60},
            'GOOGL': {'sentiment_score': 0.50},
            'AMZN': {'sentiment_score': 0.80},
            'META': {'sentiment_score': 0.65}
        }
        
        # Score the stocks
        scores = scorer.score_stocks(tickers, sentiment_data=sentiment_data)
        
        if not scores.empty:
            logger.info("Stock scores:")
            for ticker, row in scores.iterrows():
                logger.info(f"{ticker} - Total score: {row.get('total_score', 0):.3f}")
                logger.info(f"  Trend: {row.get('trend_score', 0):.2f}, Momentum: {row.get('momentum_score', 0):.2f}, Sentiment: {row.get('sentiment_score', 0):.2f}")
        else:
            logger.warning("No scores generated")
            
        logger.info("Stock scoring test completed\n")
        return True
        
    except Exception as e:
        logger.error(f"Stock scoring test failed: {str(e)}")
        return False

def test_stock_selection():
    """Test the stock selection system with portfolio generation"""
    try:
        from trading_bot.stock_selection.stock_selector import StockSelector
        logger.info("Testing stock selection system...")
        
        # Initialize with mock data provider
        data_provider = MockDataProvider()
        selector = StockSelector(data_provider)
        
        # Test universe
        universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        # Generate portfolio
        logger.info("Generating test portfolio...")
        portfolio = selector.generate_portfolio(
            universe=universe,
            total_capital=100000.0,
            max_stocks=3,
            risk_profile='moderate'
        )
        
        if not portfolio.empty:
            logger.info("Generated portfolio:")
            for _, row in portfolio.iterrows():
                ticker = row.get('ticker', 'Unknown')
                allocation = row.get('allocation', 0)
                dollar_amount = row.get('dollar_amount', 0)
                logger.info(f"{ticker}: {allocation:.1f}% (${dollar_amount:.2f})")
        else:
            logger.warning("Empty portfolio generated")
            
        logger.info("Stock selection test completed\n")
        return True
        
    except Exception as e:
        logger.error(f"Stock selection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting sentiment and stock selection tests")
    
    # Test sentiment analyzer
    sentiment_basic = test_sentiment_analysis()
    
    # Test enhanced sentiment
    sentiment_enhanced = test_enhanced_sentiment()
    
    # Test stock scoring
    stock_scoring = test_stock_scoring()
    
    # Test stock selection
    stock_selection = test_stock_selection()
    
    # Summarize results
    logger.info("\n=== Test Results ===")
    logger.info(f"Basic Sentiment Analysis: {'✅ Passed' if sentiment_basic else '❌ Failed'}")
    logger.info(f"Enhanced Sentiment Analysis: {'✅ Passed' if sentiment_enhanced else '❌ Failed'}")
    logger.info(f"Stock Scoring: {'✅ Passed' if stock_scoring else '❌ Failed'}")
    logger.info(f"Stock Selection: {'✅ Passed' if stock_selection else '❌ Failed'}")
    
    # Overall status
    total_passed = sum([sentiment_basic, sentiment_enhanced, stock_scoring, stock_selection])
    logger.info(f"Total: {total_passed}/4 tests passed")
    
    logger.info("Tests completed") 