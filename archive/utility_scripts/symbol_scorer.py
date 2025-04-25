import pandas as pd
import numpy as np
import datetime
import requests
import yfinance as yf
from collections import defaultdict
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("symbol_scorer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SymbolScorer:
    """
    Scores and ranks symbol-strategy pairs based on multiple factors, prioritizing backtests efficiently.
    Uses multiple factors including news sentiment, technical indicators, 
    volume analysis, and historical performance.
    """
    
    def __init__(self, api_keys=None, lookback_days=30, sector_etfs=None, data_dir="data"):
        """
        Initialize the SymbolScorer.
        
        Args:
            api_keys (dict): Dictionary of API keys for data sources
            lookback_days (int): Number of days to look back for historical data
            sector_etfs (dict): Dictionary mapping sectors to their ETF symbols
            data_dir (str): Directory to store data and caches
        """
        self.api_keys = api_keys or {}
        self.lookback_days = lookback_days
        self.sector_etfs = sector_etfs or {
            "Technology": "XLK",
            "Energy": "XLE", 
            "Financial": "XLF",
            "Healthcare": "XLV",
            "Consumer Discretionary": "XLY",
            "Utilities": "XLU",
            "Materials": "XLB",
            "Real Estate": "XLRE",
            "Consumer Staples": "XLP",
            "Industrial": "XLI",
            "Communication Services": "XLC"
        }
        
        # Cache for API results
        self.cache = {
            "price_data": {},
            "news_data": {},
            "volume_data": {},
            "sector_performance": {},
            "symbol_info": {}
        }
        
        # Store calculated scores
        self.scores = {}
        
        # Weights for scoring factors (can be adjusted)
        self.weights = {
            "news_sentiment": 0.25,
            "news_volume": 0.10,
            "price_momentum": 0.15,
            "volume_anomaly": 0.15,
            "sector_relative": 0.10,
            "volatility_regime": 0.15,
            "prev_backtest": 0.10
        }
        
        # Strategy-volatility regime compatibility
        self.strategy_regime_compatibility = {
            "Momentum": {"low": 0.3, "medium": 0.7, "high": 0.5},
            "Trend Following": {"low": 0.8, "medium": 0.9, "high": 0.4},
            "Breakout": {"low": 0.2, "medium": 0.6, "high": 0.9},
            "Statistical Arbitrage": {"low": 0.7, "medium": 0.6, "high": 0.3},
            "Mean Reversion": {"low": 0.4, "medium": 0.6, "high": 0.8},
            "Volatility Expansion": {"low": 0.1, "medium": 0.5, "high": 0.9},
            "Swing Trading": {"low": 0.5, "medium": 0.8, "high": 0.6},
            "Options Volatility Skew": {"low": 0.3, "medium": 0.7, "high": 0.9},
            "News Sentiment": {"low": 0.6, "medium": 0.7, "high": 0.5},
            "Pairs Trading": {"low": 0.8, "medium": 0.7, "high": 0.4},
            "MACD Crossover": {"low": 0.6, "medium": 0.8, "high": 0.5},
            "Earnings Volatility": {"low": 0.2, "medium": 0.5, "high": 0.9}
        }
        
        # Initialize results from previous backtests (will be populated from database)
        self.previous_backtest_results = {}
        
        self.data_dir = data_dir
        self.cache_dir = os.path.join(data_dir, "cache")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache for price data, news data, etc.
        self.price_cache = {}
        self.news_cache = {}
        self.cache_expiry = {}
        
        logger.info("SymbolScorer initialized with %d sectors", len(self.sector_etfs))
    
    def get_price_data(self, symbol, days=None):
        """
        Get historical price data for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            days (int): Number of days to look back (default: self.lookback_days)
            
        Returns:
            pandas.DataFrame: Price data
        """
        days = days or self.lookback_days
        cache_key = f"{symbol}_{days}"
        
        if cache_key in self.cache["price_data"]:
            return self.cache["price_data"][cache_key]
        
        try:
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            # Calculate additional features
            if len(data) > 0:
                data['Returns'] = data['Close'].pct_change()
                data['LogReturns'] = np.log(data['Close'] / data['Close'].shift(1))
                data['RollingVol20'] = data['Returns'].rolling(window=20).std()
                data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=20).mean()
                
                # Moving averages
                data['SMA20'] = data['Close'].rolling(window=20).mean()
                data['SMA50'] = data['Close'].rolling(window=50).mean()
                data['SMA200'] = data['Close'].rolling(window=200).mean()
                
                # RSI
                delta = data['Close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                data['RSI'] = 100 - (100 / (1 + rs))
            
            self.cache["price_data"][cache_key] = data
            return data
            
        except Exception as e:
            logger.error("Error fetching price data for %s: %s", symbol, str(e))
            return pd.DataFrame()
    
    def get_news_data(self, symbol, days=None):
        """
        Get news data for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            days (int): Number of days to look back (default: self.lookback_days)
            
        Returns:
            list: News data items
        """
        days = days or self.lookback_days
        cache_key = f"{symbol}_{days}"
        
        if cache_key in self.cache["news_data"]:
            return self.cache["news_data"][cache_key]
        
        # Implement news fetching from API or use mock data for testing
        # This is a placeholder. In a real implementation, you would connect to news APIs.
        
        if "finnhub" in self.api_keys:
            try:
                end_date = datetime.datetime.now()
                start_date = end_date - datetime.timedelta(days=days)
                
                url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&token={self.api_keys['finnhub']}"
                response = requests.get(url)
                data = response.json()
                
                if isinstance(data, list):
                    # Process the news data
                    news_items = []
                    for item in data:
                        news_items.append({
                            "title": item.get("headline", ""),
                            "summary": item.get("summary", ""),
                            "datetime": item.get("datetime", 0),
                            "source": item.get("source", ""),
                            "url": item.get("url", ""),
                            "sentiment": self._analyze_sentiment(item.get("headline", "") + " " + item.get("summary", ""))
                        })
                    
                    self.cache["news_data"][cache_key] = news_items
                    return news_items
                else:
                    logger.warning("Invalid news data format for %s", symbol)
                    return []
                    
            except Exception as e:
                logger.error("Error fetching news data for %s: %s", symbol, str(e))
                return []
        else:
            # Mock data for testing
            news_sentiment_map = {
                "AAPL": {"positive": 7, "neutral": 2, "negative": 1},
                "MSFT": {"positive": 6, "neutral": 3, "negative": 1},
                "AMZN": {"positive": 5, "neutral": 4, "negative": 1},
                "GOOGL": {"positive": 6, "neutral": 2, "negative": 2},
                "META": {"positive": 4, "neutral": 4, "negative": 2},
                "TSLA": {"positive": 4, "neutral": 3, "negative": 3},
                "NVDA": {"positive": 8, "neutral": 1, "negative": 1},
                "JPM": {"positive": 5, "neutral": 3, "negative": 2},
                "V": {"positive": 4, "neutral": 5, "negative": 1},
                "JNJ": {"positive": 3, "neutral": 6, "negative": 1}
            }
            
            sentiment_dist = news_sentiment_map.get(symbol, {"positive": 4, "neutral": 4, "negative": 2})
            news_items = []
            
            for i in range(sum(sentiment_dist.values())):
                sentiment = "positive"
                if i >= sentiment_dist["positive"]:
                    sentiment = "neutral"
                if i >= sentiment_dist["positive"] + sentiment_dist["neutral"]:
                    sentiment = "negative"
                
                news_items.append({
                    "title": f"Mock news title for {symbol} #{i+1}",
                    "summary": f"This is a mock news summary for {symbol} with {sentiment} sentiment.",
                    "datetime": int((datetime.datetime.now() - datetime.timedelta(days=i)).timestamp()),
                    "source": "Mock Source",
                    "url": "https://example.com",
                    "sentiment": sentiment
                })
            
            self.cache["news_data"][cache_key] = news_items
            return news_items
    
    def get_sector_performance(self, sector):
        """
        Get performance data for a sector ETF.
        
        Args:
            sector (str): Sector name
            
        Returns:
            float: Sector performance (return) over lookback period
        """
        if sector in self.cache["sector_performance"]:
            return self.cache["sector_performance"][sector]
        
        etf = self.sector_etfs.get(sector)
        if not etf:
            logger.warning("No ETF found for sector: %s", sector)
            return 0.0
        
        data = self.get_price_data(etf)
        if len(data) < 2:
            return 0.0
        
        # Calculate performance as percentage return
        first_price = data['Close'].iloc[0]
        last_price = data['Close'].iloc[-1]
        performance = (last_price - first_price) / first_price * 100
        
        self.cache["sector_performance"][sector] = performance
        return performance
    
    def get_symbol_info(self, symbol):
        """
        Get basic information about a symbol including sector, market cap, etc.
        
        Args:
            symbol (str): Ticker symbol
            
        Returns:
            dict: Symbol information
        """
        if symbol in self.cache["symbol_info"]:
            return self.cache["symbol_info"][symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            symbol_info = {
                "symbol": symbol,
                "name": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "average_volume": info.get("averageVolume", 0)
            }
            
            self.cache["symbol_info"][symbol] = symbol_info
            return symbol_info
            
        except Exception as e:
            logger.error("Error fetching symbol info for %s: %s", symbol, str(e))
            return {
                "symbol": symbol,
                "name": symbol,
                "sector": "Unknown",
                "industry": "Unknown",
                "market_cap": 0,
                "average_volume": 0
            }
    
    def _analyze_sentiment(self, text):
        """
        Analyze sentiment of text using a simple keyword-based approach.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Sentiment ("positive", "neutral", or "negative")
        """
        # Simple keyword-based sentiment analysis
        positive_words = [
            "up", "rise", "gain", "positive", "growth", "increase", "bullish", "outperform", 
            "beat", "exceed", "success", "strong", "boost", "improve", "advantage", "opportunity"
        ]
        
        negative_words = [
            "down", "fall", "drop", "negative", "decline", "decrease", "bearish", "underperform", 
            "miss", "below", "fail", "weak", "cut", "worsen", "disadvantage", "risk"
        ]
        
        text = text.lower()
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def calculate_news_sentiment_score(self, symbol):
        """
        Calculate news sentiment score for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            
        Returns:
            float: News sentiment score (0-1)
        """
        news = self.get_news_data(symbol)
        if not news:
            return 0.5  # Neutral if no news
        
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        recency_weights = []
        
        now = datetime.datetime.now().timestamp()
        max_age = self.lookback_days * 24 * 60 * 60  # Convert days to seconds
        
        for item in news:
            sentiment = item["sentiment"]
            sentiment_counts[sentiment] += 1
            
            # Calculate recency weight (more recent news has higher weight)
            age = now - item["datetime"]
            recency_weight = max(0, 1 - (age / max_age))
            recency_weights.append(recency_weight)
        
        if not recency_weights:
            return 0.5
            
        # Calculate weighted sentiment score
        total_items = len(news)
        sentiment_score = (
            (sentiment_counts["positive"] / total_items) - 
            (sentiment_counts["negative"] / total_items)
        )
        
        # Adjust for recency
        recency_factor = sum(recency_weights) / len(recency_weights)
        final_score = (sentiment_score * 0.5) + 0.5  # Normalize to 0-1
        
        # Apply recency adjustment
        final_score = (final_score * recency_factor) + (0.5 * (1 - recency_factor))
        
        return round(final_score, 2)
    
    def calculate_news_volume_score(self, symbol, days=5):
        """
        Calculate a score based on recent news volume for a symbol.
        Higher scores indicate unusual news activity.
        
        Args:
            symbol (str): Stock symbol to analyze
            days (int): Number of days to look back
            
        Returns:
            float: News volume score (0.0 to 1.0)
        """
        # Check cache first
        cache_key = f"{symbol}_news_volume_{days}"
        if cache_key in self.cache_expiry:
            # Use cached score if less than 4 hours old
            if (datetime.datetime.now() - self.cache_expiry[cache_key]).total_seconds() < 14400:
                logger.debug(f"Using cached news volume score for {symbol}")
                return self.news_cache.get(cache_key, 0.0)
        
        # Initialize score
        score = 0.0
        
        try:
            # Try multiple news sources based on available API keys
            news_items = []
            
            # Try Finnhub API if available
            if "finnhub" in self.api_keys:
                try:
                    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
                    
                    url = f"https://finnhub.io/api/v1/company-news"
                    params = {
                        "symbol": symbol,
                        "from": start_date,
                        "to": end_date,
                        "token": self.api_keys["finnhub"]
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        finnhub_news = response.json()
                        if isinstance(finnhub_news, list):
                            news_items.extend(finnhub_news)
                except Exception as e:
                    logger.warning(f"Finnhub API error for {symbol}: {str(e)}")
            
            # Try Alpha Vantage news sentiment if available
            if "alpha_vantage" in self.api_keys:
                try:
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "NEWS_SENTIMENT",
                        "tickers": symbol,
                        "apikey": self.api_keys["alpha_vantage"]
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if "feed" in data and isinstance(data["feed"], list):
                            news_items.extend(data["feed"])
                except Exception as e:
                    logger.warning(f"Alpha Vantage API error for {symbol}: {str(e)}")
            
            # Try Marketaux API if available
            if "marketaux" in self.api_keys:
                try:
                    url = "https://api.marketaux.com/v1/news/all"
                    params = {
                        "symbols": symbol,
                        "filter_entities": "true",
                        "language": "en",
                        "api_token": self.api_keys["marketaux"]
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and isinstance(data["data"], list):
                            news_items.extend(data["data"])
                except Exception as e:
                    logger.warning(f"Marketaux API error for {symbol}: {str(e)}")
            
            # Calculate score based on news volume 
            if news_items:
                # Get baseline news count (typical for this symbol)
                baseline_count = self.get_baseline_news_count(symbol)
                
                # Current count
                current_count = len(news_items)
                
                # Calculate ratio (handle zero baseline)
                if baseline_count > 0:
                    ratio = min(current_count / baseline_count, 5.0)  # Cap at 5x
                else:
                    # If no baseline, use absolute thresholds
                    if current_count > 20:
                        ratio = 5.0
                    elif current_count > 10:
                        ratio = 3.0
                    elif current_count > 5:
                        ratio = 1.5
                    else:
                        ratio = 1.0
                
                # Convert to 0-1 score 
                score = min(1.0, (ratio - 1) / 4)  # Scale 1x-5x to 0-1 range
                
                # Ensure non-negative
                score = max(0.0, score)
                
                logger.debug(f"News volume score for {symbol}: {score:.2f} (items: {current_count}, baseline: {baseline_count})")
            
            # Cache the result
            self.news_cache[cache_key] = score
            self.cache_expiry[cache_key] = datetime.datetime.now()
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating news volume score for {symbol}: {str(e)}")
            return 0.0
    
    def get_baseline_news_count(self, symbol):
        """
        Get the baseline (typical) news count for a symbol.
        Uses cached values or estimates based on market cap/sector.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float: Baseline news count
        """
        # Check if we have a stored baseline
        cache_file = os.path.join(self.cache_dir, "news_baselines.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    baselines = json.load(f)
                    if symbol in baselines:
                        return baselines[symbol]
        except Exception:
            pass
        
        # Estimate based on market cap/index membership
        try:
            # Major indices get more news
            if symbol in ["SPY", "QQQ", "DIA", "IWM"] or symbol.startswith("^"):
                return 20.0
            
            # Get price data to estimate size
            price_data = self.get_price_data(symbol, days=5)
            if len(price_data) > 0:
                # Higher volume symbols get more news
                avg_volume = price_data["Volume"].mean() if "Volume" in price_data else 0
                if avg_volume > 10000000:  # Large cap
                    return 15.0
                elif avg_volume > 1000000:  # Mid cap
                    return 10.0
                elif avg_volume > 100000:  # Small cap
                    return 5.0
                else:  # Micro cap
                    return 2.0
        except Exception:
            pass
        
        # Default fallback
        return 5.0
    
    def calculate_price_momentum_score(self, symbol):
        """
        Calculate price momentum score for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            
        Returns:
            float: Price momentum score (0-1)
        """
        data = self.get_price_data(symbol)
        if len(data) < 20:
            return 0.5
        
        # Calculate momentum using multiple timeframes
        returns = {
            "1d": float(data['Returns'].iloc[-1]) if len(data) > 1 else 0,
            "5d": float(data['Close'].pct_change(5).iloc[-1]) if len(data) > 5 else 0,
            "20d": float(data['Close'].pct_change(20).iloc[-1]) if len(data) > 20 else 0
        }
        
        # Calculate moving average signals
        ma_signals = 0
        if len(data) > 50:
            # SMA20 above SMA50 is bullish
            sma20 = float(data['SMA20'].iloc[-1])
            sma50 = float(data['SMA50'].iloc[-1])
            ma_signals += 1 if sma20 > sma50 else -1
            
        if len(data) > 200:
            # Price above SMA200 is bullish
            close = float(data['Close'].iloc[-1])
            sma200 = float(data['SMA200'].iloc[-1])
            ma_signals += 1 if close > sma200 else -1
        
        # Weighted average of returns
        momentum_value = (
            returns["1d"] * 0.2 + 
            returns["5d"] * 0.3 + 
            returns["20d"] * 0.5
        )
        
        # Convert to score (0-1)
        # Momentum of +5% or more is a score of 1, -5% or less is 0
        momentum_score = min(1.0, max(0.0, (momentum_value + 0.05) / 0.1))
        
        # Incorporate MA signals
        ma_score = (ma_signals + 2) / 4  # Convert -2...+2 to 0...1
        
        # Combine scores (70% momentum, 30% MA signals)
        final_score = momentum_score * 0.7 + ma_score * 0.3
        
        return round(final_score, 2)
    
    def calculate_volume_anomaly_score(self, symbol):
        """
        Calculate volume anomaly score for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            
        Returns:
            float: Volume anomaly score (0-1)
        """
        data = self.get_price_data(symbol)
        if len(data) < 20:
            return 0.5
        
        # Calculate average volume ratio over past 5 days
        if len(data) >= 5:
            recent_vol_ratios = data['Volume_Ratio'].iloc[-5:].values.tolist()
            recent_vol_ratio = sum(recent_vol_ratios) / len(recent_vol_ratios)
        else:
            recent_vol_ratio = 1.0
        
        # Convert to score
        # Volume ratio of 2.0+ (2x average) is score of 1
        # Normal volume (ratio of 1.0) is score of 0.5
        vol_score = min(1.0, max(0.0, (recent_vol_ratio - 0.5) / 1.5))
        
        return round(vol_score, 2)
    
    def calculate_sector_relative_score(self, symbol):
        """
        Calculate sector relative performance score for a symbol.
        
        Args:
            symbol (str): Ticker symbol
            
        Returns:
            float: Sector relative score (0-1)
        """
        symbol_info = self.get_symbol_info(symbol)
        sector = symbol_info["sector"]
        
        data = self.get_price_data(symbol)
        if len(data) < 20 or sector == "Unknown":
            return 0.5
        
        # Calculate symbol performance
        try:
            first_price = float(data['Close'].iloc[0])
            last_price = float(data['Close'].iloc[-1])
            symbol_performance = (last_price - first_price) / first_price * 100
        except Exception as e:
            logger.error("Error calculating performance for %s: %s", symbol, str(e))
            return 0.5
        
        # Get sector performance
        sector_performance = self.get_sector_performance(sector)
        
        # Calculate relative performance
        # If symbol outperforms sector by 5% or more, score is 1
        # If symbol underperforms sector by 5% or more, score is 0
        relative_performance = float(symbol_performance - sector_performance)
        rel_score = min(1.0, max(0.0, (relative_performance + 5) / 10))
        
        return round(rel_score, 2)
    
    def calculate_volatility_regime_score(self, symbol, strategy):
        """
        Calculate volatility regime compatibility score for a symbol-strategy pair.
        
        Args:
            symbol (str): Ticker symbol
            strategy (str): Strategy name
            
        Returns:
            float: Volatility regime score (0-1)
        """
        data = self.get_price_data(symbol)
        if len(data) < 20:
            return 0.5
        
        # Determine volatility regime
        try:
            recent_vol = float(data['RollingVol20'].iloc[-1]) * np.sqrt(252)  # Annualized
        except Exception as e:
            logger.error("Error calculating volatility for %s: %s", symbol, str(e))
            return 0.5
        
        # Define volatility regime thresholds (annualized)
        low_threshold = 0.15  # 15%
        high_threshold = 0.30  # 30%
        
        regime = "medium"
        if recent_vol < low_threshold:
            regime = "low"
        elif recent_vol > high_threshold:
            regime = "high"
        
        # Get strategy compatibility for this regime
        if strategy not in self.strategy_regime_compatibility:
            return 0.5
            
        compatibility = self.strategy_regime_compatibility[strategy].get(regime, 0.5)
        
        return round(compatibility, 2)
    
    def calculate_previous_backtest_score(self, symbol, strategy):
        """
        Calculate score based on previous backtest results.
        
        Args:
            symbol (str): Ticker symbol
            strategy (str): Strategy name
            
        Returns:
            float: Previous backtest score (0-1)
        """
        # Generate cache key
        key = f"{symbol}_{strategy}"
        
        # Check if we have previous backtest results
        if key not in self.previous_backtest_results:
            return 0.5  # Neutral if no previous results
        
        result = self.previous_backtest_results[key]
        
        # Calculate score based on Sharpe ratio
        # Sharpe of 2+ is score of 1, Sharpe of 0 or less is score of 0
        sharpe_score = min(1.0, max(0.0, result.get("sharpe", 0) / 2))
        
        # Calculate score based on win rate
        # Win rate of 70%+ is score of 1, win rate of 30% or less is score of 0
        winrate = result.get("winrate", 50)
        winrate_score = min(1.0, max(0.0, (winrate - 30) / 40))
        
        # Combine scores (70% Sharpe, 30% win rate)
        final_score = sharpe_score * 0.7 + winrate_score * 0.3
        
        return round(final_score, 2)
    
    def score_symbol_strategy_pair(self, symbol, strategy):
        """
        Calculate overall score for a symbol-strategy pair.
        
        Args:
            symbol (str): Ticker symbol
            strategy (str): Strategy name
            
        Returns:
            float: Overall score (0-1)
        """
        scores = {
            "news_sentiment": self.calculate_news_sentiment_score(symbol),
            "news_volume": self.calculate_news_volume_score(symbol),
            "price_momentum": self.calculate_price_momentum_score(symbol),
            "volume_anomaly": self.calculate_volume_anomaly_score(symbol),
            "sector_relative": self.calculate_sector_relative_score(symbol),
            "volatility_regime": self.calculate_volatility_regime_score(symbol, strategy),
            "prev_backtest": self.calculate_previous_backtest_score(symbol, strategy)
        }
        
        # Calculate weighted score
        weighted_score = sum(scores[factor] * self.weights[factor] for factor in scores)
        
        # Store scores for this pair
        key = f"{symbol}_{strategy}"
        self.scores[key] = {
            "symbol": symbol,
            "strategy": strategy,
            "overall_score": weighted_score,
            "component_scores": scores
        }
        
        return weighted_score
    
    def rank_pairs(self, symbols, strategies):
        """
        Rank symbol-strategy pairs by score.
        
        Args:
            symbols (list): List of ticker symbols
            strategies (list): List of strategies
            
        Returns:
            list: Ranked list of (symbol, strategy, score) tuples
        """
        results = []
        
        total_pairs = len(symbols) * len(strategies)
        logger.info("Ranking %d symbol-strategy pairs", total_pairs)
        
        count = 0
        for symbol in symbols:
            for strategy in strategies:
                score = self.score_symbol_strategy_pair(symbol, strategy)
                results.append((symbol, strategy, score))
                
                count += 1
                if count % 50 == 0:
                    logger.info("Processed %d/%d pairs", count, total_pairs)
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results
    
    def update_previous_backtest_results(self, results):
        """
        Update previous backtest results.
        
        Args:
            results (dict): Dictionary of backtest results
                           format: {symbol_strategy: {sharpe, winrate, etc.}}
        """
        self.previous_backtest_results.update(results)
        logger.info("Updated previous backtest results with %d entries", len(results))
    
    def get_backtest_candidates(self, symbols, strategies, limit=50):
        """
        Get top backtest candidates.
        
        Args:
            symbols (list): List of ticker symbols
            strategies (list): List of strategies
            limit (int): Maximum number of candidates to return
            
        Returns:
            list: List of dicts with candidate details
        """
        ranked_pairs = self.rank_pairs(symbols, strategies)
        
        # Convert to list of dictionaries with details
        candidates = []
        for symbol, strategy, score in ranked_pairs[:limit]:
            key = f"{symbol}_{strategy}"
            candidate = {
                "symbol": symbol,
                "strategy": strategy,
                "score": score,
                "component_scores": self.scores[key]["component_scores"],
                "sector": self.get_symbol_info(symbol)["sector"],
                "market_cap": self.get_symbol_info(symbol)["market_cap"],
            }
            candidates.append(candidate)
        
        logger.info("Selected %d backtest candidates from %d pairs", 
                   len(candidates), len(ranked_pairs))
        
        return candidates


# Example usage
if __name__ == "__main__":
    # Sample symbols and strategies
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "JPM", "META"]
    strategies = ["Momentum", "Trend Following", "Breakout", "Mean Reversion"]
    
    # Initialize scorer
    scorer = SymbolScorer()
    
    # Get backtest candidates
    candidates = scorer.get_backtest_candidates(symbols, strategies, limit=10)
    
    # Print results
    print("\nTop Backtest Candidates:")
    for i, candidate in enumerate(candidates):
        print(f"{i+1}. {candidate['symbol']} - {candidate['strategy']} (Score: {candidate['score']:.2f})")
        print(f"   News Sentiment: {candidate['component_scores']['news_sentiment']:.2f}, "
              f"Momentum: {candidate['component_scores']['price_momentum']:.2f}, "
              f"Volume: {candidate['component_scores']['volume_anomaly']:.2f}")
        print() 