import pandas as pd
import numpy as np
import datetime
import time
import logging
import os
import json
import threading
import queue
from symbol_scorer import SymbolScorer
import math
import random
import requests
from collections import defaultdict
from threading import Thread, Lock, Event
from queue import Queue, PriorityQueue
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BacktestScheduler:
    """
    Manages the scheduling and prioritization of backtests based on SymbolScorer results.
    Handles the backtest queue, API rate limiting, and results storage.
    """
    
    def __init__(self, api_keys=None, data_dir="data", max_concurrent=5, daily_limit=100, watchlist_size=50, refresh_interval=12, market_analyzer=None, config=None):
        """
        Initialize the BacktestScheduler.
        
        Args:
            api_keys (dict, optional): Dictionary of API keys
            data_dir (str, optional): Directory to store data
            max_concurrent (int, optional): Maximum number of concurrent backtests
            daily_limit (int, optional): Maximum number of backtests per day
            watchlist_size (int, optional): Maximum size of the watchlist
            refresh_interval (int, optional): Hours between watchlist refreshes
            market_analyzer (MarketAnalyzer, optional): Market analyzer instance
            config (dict, optional): Configuration dictionary
        """
        self.market_analyzer = market_analyzer
        self.config = config or {}
        
        # Legacy parameters
        self.api_keys = api_keys or {}
        self.data_dir = data_dir
        self.max_concurrent = max_concurrent
        self.daily_limit = daily_limit
        self.watchlist_size = watchlist_size
        self.refresh_interval = refresh_interval
        
        # Configure from config
        self.alpha_vantage_api_key = self.config.get("alpha_vantage_api_key", self.api_keys.get("alpha_vantage", os.environ.get("ALPHA_VANTAGE_API_KEY", "")))
        self.vix_api_key = self.config.get("vix_api_key", self.alpha_vantage_api_key)  # Use Alpha Vantage key as default for VIX
        self.update_interval = self.config.get("update_interval", 3600)  # Default to hourly updates
        self.max_api_calls_per_minute = self.config.get("max_api_calls_per_minute", 5)  # Default API rate limit
        self.watchlist = self.config.get("watchlist", ["SPY", "QQQ", "AAPL", "MSFT", "AMZN"])
        
        # Tracking for rate limiting
        self.last_api_call_times = []
        
        logger.info("BacktestScheduler initialized with update interval of %s seconds", self.update_interval)
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "results"), exist_ok=True)
        
        # Initialize SymbolScorer
        self.scorer = SymbolScorer(api_keys=self.api_keys)
        
        # Initialize tracking variables
        self.backtest_queue = queue.PriorityQueue()
        self.active_backtests = set()
        self.completed_backtests = set()
        self.failed_backtests = {}
        self.daily_count = 0
        self.last_refresh = datetime.datetime.now() - datetime.timedelta(hours=self.refresh_interval)
        
        # Adaptive testing
        self.optimal_test_count = self.daily_limit
        self.last_count_update = datetime.datetime.now()
        
        # Statistical coverage tracking
        self.parameter_space_size = 0
        self.coverage_ratio = 0.0
        self.last_coverage_update = datetime.datetime.now()
        
        # Market anomaly tracking
        self.anomaly_status = {
            'detected': False,
            'severity': 1.0,
            'types': [],
            'last_check': datetime.datetime.now()
        }
        
        # Watchlist management
        self.strategies = []
        self.load_strategies()
        self.load_watchlist()
        
        # Threading resources
        self.worker_threads = []
        self.results_queue = queue.Queue()
        self.exit_event = threading.Event()
        
        logger.info("BacktestScheduler initialized with max concurrent=%d, daily limit=%d", 
                   self.max_concurrent, self.daily_limit)
    
    def load_watchlist(self):
        """Load watchlist from file or initialize with defaults."""
        watchlist_file = os.path.join(self.data_dir, "watchlist.json")
        
        if os.path.exists(watchlist_file):
            try:
                with open(watchlist_file, 'r') as f:
                    self.watchlist = json.load(f)
                logger.info("Loaded watchlist with %d symbols", len(self.watchlist))
            except Exception as e:
                logger.error("Error loading watchlist: %s", str(e))
                self._initialize_default_watchlist()
        else:
            self._initialize_default_watchlist()
    
    def _initialize_default_watchlist(self):
        """Initialize watchlist with default symbols."""
        # Default to major index components and liquid ETFs
        self.watchlist = [
            # Major tech stocks
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", 
            
            # Financial sector
            "JPM", "BAC", "GS", "V", "MA",
            
            # Healthcare 
            "JNJ", "PFE", "UNH", "ABT", "MRK",
            
            # Consumer
            "PG", "KO", "PEP", "WMT", "MCD",
            
            # Energy
            "XOM", "CVX", "COP",
            
            # ETFs
            "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "GLD", "SLV"
        ]
        logger.info("Initialized default watchlist with %d symbols", len(self.watchlist))
        self.save_watchlist()
    
    def save_watchlist(self):
        """Save watchlist to file."""
        watchlist_file = os.path.join(self.data_dir, "watchlist.json")
        
        try:
            with open(watchlist_file, 'w') as f:
                json.dump(self.watchlist, f)
            logger.info("Saved watchlist with %d symbols", len(self.watchlist))
        except Exception as e:
            logger.error("Error saving watchlist: %s", str(e))
    
    def load_strategies(self):
        """Load strategies from file or initialize with defaults."""
        strategies_file = os.path.join(self.data_dir, "strategies.json")
        
        if os.path.exists(strategies_file):
            try:
                with open(strategies_file, 'r') as f:
                    self.strategies = json.load(f)
                logger.info("Loaded %d strategies", len(self.strategies))
            except Exception as e:
                logger.error("Error loading strategies: %s", str(e))
                self._initialize_default_strategies()
        else:
            self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize with default strategies."""
        self.strategies = [
            "Momentum", 
            "Trend Following", 
            "Breakout", 
            "Statistical Arbitrage", 
            "Mean Reversion", 
            "Volatility Expansion", 
            "Swing Trading", 
            "Options Volatility Skew", 
            "News Sentiment", 
            "Pairs Trading", 
            "MACD Crossover", 
            "Earnings Volatility"
        ]
        logger.info("Initialized with %d default strategies", len(self.strategies))
        self.save_strategies()
    
    def save_strategies(self):
        """Save strategies to file."""
        strategies_file = os.path.join(self.data_dir, "strategies.json")
        
        try:
            with open(strategies_file, 'w') as f:
                json.dump(self.strategies, f)
            logger.info("Saved %d strategies", len(self.strategies))
        except Exception as e:
            logger.error("Error saving strategies: %s", str(e))
    
    def refresh_watchlist(self):
        """
        Refresh the dynamic watchlist based on market activity, news, and performance.
        """
        now = datetime.datetime.now()
        hours_since_refresh = (now - self.last_refresh).total_seconds() / 3600
        
        if hours_since_refresh < self.refresh_interval:
            remaining = self.refresh_interval - hours_since_refresh
            logger.info("Watchlist refresh not due yet. Next refresh in %.1f hours", remaining)
            return
        
        logger.info("Starting watchlist refresh")
        
        # Start with current watchlist
        current_symbols = set(self.watchlist)
        
        # 1. Get major index components to consider as candidates
        # This would typically come from an API or data provider
        # For demonstration, we'll use a small set of additional candidates
        candidate_symbols = [
            # Additional Tech
            "AMD", "INTC", "CRM", "ORCL", "IBM", "ADBE", 
            
            # Additional Financial
            "WFC", "C", "AXP", "BLK", "MS",
            
            # Additional Healthcare
            "LLY", "BMY", "AMGN", "GILD", "BIIB",
            
            # Additional Consumer
            "COST", "HD", "NKE", "SBUX", "DIS",
            
            # Additional Energy
            "BP", "SLB", "EOG", "MPC", "PSX",
            
            # Additional ETFs
            "EEM", "EFA", "TLT", "LQD", "HYG", "VNQ"
        ]
        
        # Filter out symbols already in watchlist
        candidate_symbols = [s for s in candidate_symbols if s not in current_symbols]
        
        # 2. Score all candidates
        # We'll use a small subset of our scoring factors for the watchlist refresh
        candidates_to_score = candidate_symbols[:min(len(candidate_symbols), 50)]
        candidate_scores = {}
        
        for symbol in candidates_to_score:
            scores = {
                "news_sentiment": self.scorer.calculate_news_sentiment_score(symbol),
                "news_volume": self.scorer.calculate_news_volume_score(symbol),
                "volume_anomaly": self.scorer.calculate_volume_anomaly_score(symbol)
            }
            
            # Calculate overall score (simple average for watchlist selection)
            overall_score = sum(scores.values()) / len(scores)
            candidate_scores[symbol] = overall_score
        
        # 3. Score current watchlist symbols to identify underperformers
        watchlist_scores = {}
        for symbol in self.watchlist:
            scores = {
                "news_sentiment": self.scorer.calculate_news_sentiment_score(symbol),
                "news_volume": self.scorer.calculate_news_volume_score(symbol),
                "volume_anomaly": self.scorer.calculate_volume_anomaly_score(symbol)
            }
            
            overall_score = sum(scores.values()) / len(scores)
            watchlist_scores[symbol] = overall_score
        
        # 4. Find bottom 20% of current watchlist to potentially replace
        replacement_count = min(10, int(len(self.watchlist) * 0.2))
        sorted_watchlist = sorted(watchlist_scores.items(), key=lambda x: x[1])
        symbols_to_replace = [s[0] for s in sorted_watchlist[:replacement_count]]
        
        # 5. Find top candidates to add to watchlist
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        symbols_to_add = [s[0] for s in sorted_candidates[:replacement_count]]
        
        # 6. Update watchlist
        new_watchlist = [s for s in self.watchlist if s not in symbols_to_replace]
        new_watchlist.extend(symbols_to_add)
        
        logger.info("Watchlist refresh: -Removed %d symbols, +Added %d symbols", 
                   len(symbols_to_replace), len(symbols_to_add))
        
        # Save changes
        self.watchlist = new_watchlist
        self.save_watchlist()
        
        # Update refresh timestamp
        self.last_refresh = now
    
    def determine_optimal_test_count(self):
        """
        Dynamically determines the optimal number of backtests to run based on:
        1. Current market volatility (VIX index)
        2. News volume and significance
        3. Recent market performance
        4. System resource availability
        
        Returns:
            int: The optimal number of backtests to run today
        """
        try:
            # Start with the base daily limit
            base_limit = self.daily_limit
            logger.info(f"Starting with base limit of {base_limit} backtests")
            
            # Factor 1: Market Volatility (VIX)
            vix_factor = 1.0
            try:
                # Get current VIX value
                vix_value = self._get_current_vix()
                
                # Adjust backtests based on VIX
                # Higher volatility (VIX > 20) = more tests
                # Lower volatility (VIX < 15) = fewer tests
                if vix_value > 30:
                    vix_factor = 1.5  # Significant volatility
                    logger.info(f"High volatility detected (VIX: {vix_value}). Increasing test count by 50%")
                elif vix_value > 20:
                    vix_factor = 1.25  # Moderate volatility
                    logger.info(f"Moderate volatility detected (VIX: {vix_value}). Increasing test count by 25%")
                elif vix_value < 15:
                    vix_factor = 0.8  # Low volatility
                    logger.info(f"Low volatility detected (VIX: {vix_value}). Reducing test count by 20%")
                else:
                    logger.info(f"Normal volatility levels (VIX: {vix_value}). No adjustment needed")
            except Exception as e:
                logger.warning(f"Error getting VIX data: {e}. Using default volatility factor")
            
            # Factor 2: News Volume Score
            news_factor = 1.0
            try:
                news_score = self._calculate_news_volume_score()
                
                if news_score > 8:
                    news_factor = 1.4  # High news volume
                    logger.info(f"High news volume detected (score: {news_score}). Increasing test count by 40%")
                elif news_score > 5:
                    news_factor = 1.2  # Moderate news volume
                    logger.info(f"Moderate news volume detected (score: {news_score}). Increasing test count by 20%")
                elif news_score < 3:
                    news_factor = 0.9  # Low news volume
                    logger.info(f"Low news volume detected (score: {news_score}). Reducing test count by 10%")
                else:
                    logger.info(f"Normal news volume (score: {news_score}). No adjustment needed")
            except Exception as e:
                logger.warning(f"Error calculating news volume score: {e}. Using default news factor")
            
            # Factor 3: System resource availability
            resource_factor = 1.0
            try:
                # Get system metrics
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                
                # Reduce backtests if system resources are constrained
                if cpu_usage > 80 or memory_usage > 85:
                    resource_factor = 0.6  # Significantly reduce tests
                    logger.warning(f"System resources constrained (CPU: {cpu_usage}%, Memory: {memory_usage}%). Reducing test count by 40%")
                elif cpu_usage > 60 or memory_usage > 70:
                    resource_factor = 0.8  # Moderately reduce tests
                    logger.info(f"System resources moderately loaded (CPU: {cpu_usage}%, Memory: {memory_usage}%). Reducing test count by 20%")
            except Exception as e:
                logger.warning(f"Error checking system resources: {e}. Using default resource factor")
            
            # Apply all factors to calculate optimal count
            optimal_count = int(base_limit * vix_factor * news_factor * resource_factor)
            
            # Ensure we stay within reasonable limits
            min_count = max(int(base_limit * 0.5), 10)  # At least 10 tests or half the base
            max_count = int(base_limit * 2)  # At most double the base limit
            
            optimal_count = max(min_count, min(optimal_count, max_count))
            
            logger.info(f"Determined optimal backtest count: {optimal_count} (Factors: VIX={vix_factor:.2f}, News={news_factor:.2f}, Resources={resource_factor:.2f})")
            
            return optimal_count
            
        except Exception as e:
            logger.error(f"Error in determine_optimal_test_count: {e}")
            # Return the default daily limit in case of errors
            return self.daily_limit
    
    def _get_current_vix(self):
        """
        Fetches the current VIX value from a market data API.
        
        Returns:
            float: Current VIX level or a default value if unavailable
        """
        try:
            if not self.vix_api_key:
                # No API key available, using simulated data
                return random.uniform(15, 30)
            
            # In a real implementation, this would use a market data API
            # Example with alpha vantage: 
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=VIX&interval=5min&apikey={self.vix_api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Extract latest VIX value
                # Note: The exact structure would depend on the API used
                time_series = data.get("Time Series (5min)", {})
                if time_series:
                    latest_time = sorted(time_series.keys())[-1]
                    latest_data = time_series[latest_time]
                    return float(latest_data.get("4. close", 20.0))
                
            # Fallback to default
            return 20.0
            
        except Exception as e:
            logger.warning(f"Error fetching VIX data: {str(e)}")
            return 20.0  # Default to moderate volatility
    
    def _calculate_news_volume_score(self):
        """
        Calculates a score (1-10) based on current news volume and significance
        
        Returns:
            float: News volume score from 1-10
        """
        # In a real implementation, this would call a news API or analyze internal news database
        # For this implementation, we'll use a simplified approach
        
        try:
            # Get the day of week (0 = Monday, 6 = Sunday)
            day_of_week = datetime.datetime.now().weekday()
            
            # Check if markets are open today
            if day_of_week >= 5:  # Weekend
                return 3.0  # Lower news volume on weekends
                
            # Check if it's earnings season (simplified)
            month = datetime.datetime.now().month
            if month in [1, 4, 7, 10]:  # Quarterly earnings months
                base_score = 7.0
            else:
                base_score = 5.0
                
            # Add some randomness to simulate daily fluctuations
            random_factor = random.uniform(-1.5, 1.5)
            
            # Calculate final score
            score = base_score + random_factor
            
            # Ensure score is within 1-10 range
            return max(1.0, min(10.0, score))
            
        except Exception as e:
            logger.warning(f"Error calculating news volume score: {e}")
            return 5.0  # Default moderate score
    
    def check_for_anomalies(self):
        """
        Check for significant market movements or anomalies that may warrant
        additional backtests beyond the daily limit.
        
        Returns:
            tuple: (bool: anomaly detected, int: additional tests to run)
        """
        try:
            logger.info("Checking for market anomalies...")
            
            # Check major indices for unusual movement
            anomaly_detected = False
            movement_threshold = 2.0  # 2% movement is significant
            volume_threshold = 1.5    # 50% above average volume is significant
            
            indices = ["SPY", "QQQ", "DIA", "IWM"]
            unusual_movements = []
            unusual_volumes = []
            
            for idx in indices:
                try:
                    # Get recent price data
                    price_data = self._get_price_data(idx, days=5)
                    
                    if len(price_data) >= 2:  # Need at least 2 days
                        # Check for significant price movement
                        latest_day = price_data.iloc[-1]
                        prev_day = price_data.iloc[-2]
                        
                        if 'Close' in latest_day and 'Close' in prev_day and prev_day['Close'] > 0:
                            pct_change = abs((latest_day['Close'] - prev_day['Close']) / prev_day['Close'] * 100)
                            
                            if pct_change > movement_threshold:
                                unusual_movements.append((idx, pct_change))
                        
                        # Check for unusual volume
                        if 'Volume' in latest_day:
                            # Calculate average volume (excluding latest day)
                            avg_volume = price_data[:-1]['Volume'].mean() if len(price_data) > 1 else price_data['Volume'].mean()
                            
                            if avg_volume > 0 and latest_day['Volume'] > avg_volume * volume_threshold:
                                volume_ratio = latest_day['Volume'] / avg_volume
                                unusual_volumes.append((idx, volume_ratio))
                except Exception as e:
                    logger.warning(f"Error checking anomalies for {idx}: {str(e)}")
            
            # Determine if we have anomalies
            if unusual_movements or unusual_volumes:
                anomaly_detected = True
                
                # Log findings
                if unusual_movements:
                    logger.info(f"Unusual price movements detected: {unusual_movements}")
                if unusual_volumes:
                    logger.info(f"Unusual trading volumes detected: {unusual_volumes}")
                
                # Calculate how many additional tests to run based on severity
                severity = 0
                
                # Price movement contributes to severity
                for _, pct in unusual_movements:
                    # Scale: 2% = 0.2, 5% = 0.5, 10% = 1.0
                    severity += min(1.0, pct / 10.0)
                
                # Volume contributes to severity
                for _, ratio in unusual_volumes:
                    # Scale: 1.5x = 0.1, 2x = 0.2, 3x = 0.3, 5x = 0.5
                    severity += min(0.5, (ratio - 1) / 8.0)
                
                # Cap total severity
                severity = min(2.0, severity)
                
                # Additional tests based on severity (as percentage of daily limit)
                # 0.5 severity = 25% more, 1.0 = 50% more, 2.0 = 100% more
                additional_tests = int(self.optimal_test_count * (severity / 2.0))
                
                logger.info(f"Market anomaly detected with severity {severity:.2f}, adding {additional_tests} additional backtests")
                
                return True, additional_tests
            
            logger.info("No market anomalies detected")
            return False, 0
            
        except Exception as e:
            logger.error(f"Error checking for market anomalies: {str(e)}")
            return False, 0
    
    def _get_price_data(self, ticker, days=5):
        """
        Get historical price data for a ticker.
        
        Args:
            ticker (str): The ticker symbol
            days (int): Number of days of history to retrieve
            
        Returns:
            list: List of closing prices or None if error
        """
        try:
            # In a real implementation, this would fetch actual price data
            # For this example, we'll generate synthetic data
            
            # Create a base price around $100, adjusted by ticker
            # Use sum of character values to create different base prices per ticker
            ticker_value = sum(ord(c) for c in ticker)
            base_price = 100 + (ticker_value % 50)
            
            # Seed random with ticker for consistent results per ticker
            random.seed(hash(ticker))
            
            # Generate price history with random daily changes (-2% to +2%)
            prices = [base_price]
            for _ in range(days - 1):
                daily_change = random.uniform(-0.02, 0.02)
                next_price = prices[-1] * (1 + daily_change)
                prices.append(next_price)
            
            # Reset random seed
            random.seed()
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting price data for {ticker}: {e}")
            return None
            
    def dynamic_test_allocation(self):
        """
        Determine the optimal number of backtests to run based on:
        1. Statistical coverage of the parameter space
        2. Current market volatility
        3. Computational resources available
        4. Time of day and market hours
        
        Returns:
            int: The optimal number of backtests to schedule
        """
        try:
            self.logger.info("Calculating dynamic test allocation...")
            
            # Base allocation - this would be determined by system capacity
            base_allocation = 200
            
            # --- 1. Adjust for parameter space coverage ---
            # Calculate total parameter space size
            total_param_space = self._calculate_parameter_space_size()
            
            # Statistical coverage factor: logarithmic scaling for diminishing returns
            # as we increase test count
            if total_param_space > 0:
                coverage_factor = math.log10(total_param_space) / 4  # Normalized factor
                coverage_factor = max(0.5, min(2.0, coverage_factor))  # Clamp between 0.5 and 2.0
            else:
                coverage_factor = 1.0
                
            self.logger.info(f"Parameter space size: {total_param_space}, coverage factor: {coverage_factor:.2f}")
            
            # --- 2. Adjust for market volatility ---
            # Get current VIX value as volatility indicator
            current_vix = self._get_vix_value()
            
            # Higher volatility = more tests needed
            if current_vix < 15:  # Low volatility
                volatility_factor = 0.8
            elif current_vix < 25:  # Normal volatility
                volatility_factor = 1.0
            elif current_vix < 35:  # High volatility
                volatility_factor = 1.5
            else:  # Extreme volatility
                volatility_factor = 2.0
                
            self.logger.info(f"Current VIX: {current_vix}, volatility factor: {volatility_factor:.2f}")
            
            # --- 3. Adjust for computational resources ---
            # Check system load
            try:
                cpu_load = psutil.cpu_percent(interval=0.5) / 100
                memory_available = psutil.virtual_memory().available / psutil.virtual_memory().total
                
                # Lower resources = fewer tests
                if cpu_load > 0.9 or memory_available < 0.1:  # Critical resources
                    resource_factor = 0.5
                elif cpu_load > 0.7 or memory_available < 0.2:  # High load
                    resource_factor = 0.7
                elif cpu_load > 0.5 or memory_available < 0.3:  # Moderate load
                    resource_factor = 0.9
                else:  # Sufficient resources
                    resource_factor = 1.0
                    
                self.logger.info(f"System load: CPU {cpu_load:.2f}, Memory available {memory_available:.2f}, " +
                               f"resource factor: {resource_factor:.2f}")
            except:
                # Default if we can't check resources
                resource_factor = 0.8
                self.logger.warning("Could not check system resources, using default factor")
            
            # --- 4. Adjust for time of day ---
            current_time = datetime.datetime.now().time()
            market_open = datetime.time(9, 30)
            market_close = datetime.time(16, 0)
            
            # More tests during market hours, fewer during off hours
            if market_open <= current_time <= market_close:
                # During market hours
                time_factor = 1.2
            else:
                # Outside market hours
                time_factor = 0.8
                
            self.logger.info(f"Current time: {current_time}, time factor: {time_factor:.2f}")
            
            # Calculate final allocation by applying all factors
            optimal_allocation = int(base_allocation * coverage_factor * volatility_factor * 
                                  resource_factor * time_factor)
            
            # Ensure reasonable bounds
            optimal_allocation = max(50, min(500, optimal_allocation))
            
            self.logger.info(f"Calculated optimal test allocation: {optimal_allocation}")
            return optimal_allocation
            
        except Exception as e:
            self.logger.error(f"Error in dynamic test allocation: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Return a conservative default
            return 100
            
    def _calculate_parameter_space_size(self):
        """
        Calculate the approximate size of the parameter space across all strategies.
        This helps determine how many tests are needed for adequate coverage.
        
        Returns:
            int: Approximate size of parameter space
        """
        try:
            # In a real implementation, this would analyze each strategy's parameter space
            # Here we'll simulate it with reasonable values
            
            # Get number of active strategies
            num_strategies = len(self._get_all_strategies())
            
            # Average parameters per strategy
            avg_params_per_strategy = 5
            
            # Average unique values per parameter (accounting for continuous parameters)
            avg_values_per_param = 10
            
            # Approximate parameter space size
            # We use a logarithmic scaling to avoid enormous numbers
            parameter_space_size = num_strategies * avg_params_per_strategy * avg_values_per_param
            
            return parameter_space_size
            
        except Exception as e:
            self.logger.error(f"Error calculating parameter space size: {str(e)}")
            return 100  # Default fallback
    
    def calculate_statistical_coverage(self):
        """
        Calculates the statistical coverage needed based on:
        1. The size of the parameter space across all strategies
        2. The current market complexity (volatility, correlation structures)
        3. Historical backtest efficiency metrics
        
        This approach ensures we run enough backtests to have statistically 
        significant coverage of the parameter space, while avoiding redundant tests.
        
        Returns:
            int: The optimal number of backtests to achieve statistical coverage
        """
        try:
            logger.info("Calculating statistical coverage for backtest optimization...")
            
            # Only recalculate if it's been more than 6 hours since the last update
            now = datetime.datetime.now()
            hours_since_update = (now - self.last_coverage_update).total_seconds() / 3600
            if hours_since_update < 6 and self.parameter_space_size > 0:
                logger.info(f"Using cached statistical coverage from {hours_since_update:.1f} hours ago")
                return int(self.parameter_space_size * self.coverage_ratio)
                
            # 1. Calculate parameter space size across strategies
            total_parameter_space = 0
            
            # Get all available strategies
            strategies = self.strategies
            
            # For each strategy, calculate the approximate parameter space
            for strategy in strategies:
                # This would ideally come from the strategy definition
                # For now we'll estimate based on strategy type
                
                # Base parameters present in most strategies
                base_parameter_count = 3  # e.g., entry/exit thresholds, holding period
                
                # Strategy-specific additional parameters
                if "Momentum" in strategy:
                    params = 2  # lookback period, strength threshold
                elif "Trend" in strategy:
                    params = 3  # fast/slow periods, signal threshold
                elif "Mean Reversion" in strategy:
                    params = 3  # mean period, standard deviation bands
                elif "Volatility" in strategy:
                    params = 4  # volatility window, threshold, adjustment factors
                elif "Options" in strategy:
                    params = 5  # strike selection, days to expiration, etc.
                else:
                    params = 2  # default for other strategies
                
                total_params = base_parameter_count + params
                
                # Typical parameter values to test (conservative estimate)
                # For continuous parameters, we discretize into a reasonable number of values
                values_per_param = 5
                
                # Each strategy's parameter space contribution
                strategy_space = values_per_param ** total_params
                total_parameter_space += strategy_space
            
            # Store for future reference
            self.parameter_space_size = total_parameter_space
            
            # 2. Determine current market complexity
            # Higher complexity = need more coverage
            market_complexity = self._assess_market_complexity()
            
            # 3. Calculate the coverage ratio needed based on market complexity
            # Market complexity scales from 0.1 (very simple) to 1.0 (extremely complex)
            # This affects what percentage of the parameter space we need to cover
            
            # Base coverage - logarithmically scaled because we don't need to test
            # the full parameter space for statistical significance
            base_coverage_ratio = max(0.01, min(0.2, 0.1 * math.log10(total_parameter_space) / 10))
            
            # Adjust based on market complexity
            adjusted_coverage_ratio = base_coverage_ratio * (0.5 + market_complexity)
            
            # Ensure reasonable bounds
            adjusted_coverage_ratio = max(0.005, min(0.3, adjusted_coverage_ratio))
            
            # Store for future reference
            self.coverage_ratio = adjusted_coverage_ratio
            self.last_coverage_update = now
            
            # Calculate optimal number of tests
            optimal_test_count = int(total_parameter_space * adjusted_coverage_ratio)
            
            # Apply constraints based on system capacity
            min_tests = 20
            max_tests = 500  # Upper bound for daily tests
            
            # Ensure within bounds
            optimal_test_count = max(min_tests, min(max_tests, optimal_test_count))
            
            logger.info(f"Statistical coverage analysis: parameter space size={total_parameter_space}, " +
                       f"market complexity={market_complexity:.2f}, coverage ratio={adjusted_coverage_ratio:.4f}")
            logger.info(f"Determined optimal test count for statistical coverage: {optimal_test_count}")
            
            return optimal_test_count
            
        except Exception as e:
            logger.error(f"Error calculating statistical coverage: {str(e)}")
            # Fall back to a conservative default
            return 50
    
    def _assess_market_complexity(self):
        """
        Assess the current market complexity based on several factors:
        1. Volatility regime
        2. Correlation structure complexity
        3. Macroeconomic uncertainty
        
        Returns:
            float: Market complexity score between 0.1 (simple) and 1.0 (complex)
        """
        try:
            # This is a simplified version - a real implementation would use
            # actual market data and sophisticated analysis
            
            # 1. Volatility component (0.1-0.4)
            try:
                vix = self._get_current_vix()
                if vix > 40:
                    vol_component = 0.4  # Extremely volatile
                elif vix > 30:
                    vol_component = 0.35  # Highly volatile
                elif vix > 20:
                    vol_component = 0.3  # Moderately volatile
                elif vix > 15:
                    vol_component = 0.2  # Normal volatility
                else:
                    vol_component = 0.1  # Low volatility
            except Exception:
                vol_component = 0.25  # Default if we can't get VIX
            
            # 2. Correlation complexity component (0.1-0.3)
            # In a real implementation, this would analyze actual correlation matrices
            try:
                # Simulate correlation complexity
                # In reality, would measure eigenvalue dispersion of correlation matrix
                correlation_component = random.uniform(0.1, 0.3)
            except Exception:
                correlation_component = 0.2  # Default
            
            # 3. Macroeconomic uncertainty (0.1-0.3)
            # In a real implementation, this would use economic surprise indices,
            # policy uncertainty metrics, etc.
            try:
                # Simulate macro uncertainty
                # Would be based on economic data in reality
                macro_component = random.uniform(0.1, 0.3)
            except Exception:
                macro_component = 0.2  # Default
            
            # Combine components
            market_complexity = vol_component + correlation_component + macro_component
            
            # Ensure within bounds (0.1-1.0)
            market_complexity = max(0.1, min(1.0, market_complexity))
            
            return market_complexity
            
        except Exception as e:
            logger.warning(f"Error assessing market complexity: {str(e)}")
            return 0.5  # Default moderate complexity
    
    def anomaly_detection_override(self):
        """
        Detects market anomalies and determines if the backtest schedule should
        be overridden to increase coverage during unusual market conditions.
        
        Features:
        1. Real-time monitoring of market signals for anomaly detection
        2. Adaptive response based on anomaly type and severity
        3. Temporary override of normal test limits during critical periods
        
        Returns:
            tuple: (additional_tests, reason)
                - additional_tests: Number of additional tests to perform
                - reason: String explaining the reason for override
        """
        try:
            # Check for anomalies at most once per hour
            now = datetime.datetime.now()
            hours_since_check = (now - self.anomaly_status['last_check']).total_seconds() / 3600
            
            if hours_since_check < 1 and self.anomaly_status['detected']:
                # Use cached anomaly status if recent and active
                logger.info(f"Using cached anomaly status from {hours_since_check:.1f} hours ago")
                additional_tests = int(self.daily_limit * (self.anomaly_status['severity'] - 1.0))
                return additional_tests, f"Cached anomaly: {', '.join(self.anomaly_status['types'])}"
            
            # Reset anomaly status
            self.anomaly_status = {
                'detected': False,
                'severity': 1.0,
                'types': [],
                'last_check': now
            }
            
            logger.info("Checking for market anomalies that may require additional testing...")
            
            # List to store detected anomalies
            anomalies = []
            
            # 1. Check for volatility regime shifts
            try:
                vix = self._get_current_vix()
                vix_5d_avg = self._get_vix_moving_average(5)
                vix_20d_avg = self._get_vix_moving_average(20)
                
                # Check for sudden volatility spike
                if vix > vix_5d_avg * 1.3 and vix > 20:
                    severity = min(2.0, 1.0 + (vix - vix_5d_avg) / vix_5d_avg)
                    anomalies.append({
                        'type': 'volatility_spike',
                        'severity': severity,
                        'description': f"VIX spike: {vix:.1f} vs 5-day avg {vix_5d_avg:.1f}"
                    })
                
                # Check for volatility regime shift
                if vix_5d_avg > vix_20d_avg * 1.4:
                    severity = min(1.5, 1.0 + (vix_5d_avg - vix_20d_avg) / vix_20d_avg)
                    anomalies.append({
                        'type': 'volatility_regime_shift',
                        'severity': severity,
                        'description': f"Volatility regime shift: 5d avg {vix_5d_avg:.1f} vs 20d avg {vix_20d_avg:.1f}"
                    })
            except Exception as e:
                logger.warning(f"Error checking volatility anomalies: {str(e)}")
            
            # 2. Check for correlation breakdowns across asset classes
            try:
                correlation_breakdown = self._check_correlation_breakdown()
                if correlation_breakdown:
                    anomalies.append({
                        'type': 'correlation_breakdown',
                        'severity': 1.7,
                        'description': "Unusual correlation breakdown between asset classes"
                    })
            except Exception as e:
                logger.warning(f"Error checking correlation anomalies: {str(e)}")
            
            # 3. Check for liquidity events or unusual trading volumes
            try:
                liquidity_event = self._check_liquidity_event()
                if liquidity_event:
                    anomalies.append({
                        'type': 'liquidity_event',
                        'severity': 1.9,
                        'description': "Unusual market liquidity conditions detected"
                    })
            except Exception as e:
                logger.warning(f"Error checking liquidity anomalies: {str(e)}")
            
            # 4. Check for significant macroeconomic or news events
            try:
                major_event = self._check_significant_news()
                if major_event:
                    anomalies.append({
                        'type': 'major_news_event',
                        'severity': 1.6,
                        'description': "Major market-moving news event detected"
                    })
            except Exception as e:
                logger.warning(f"Error checking news events: {str(e)}")
            
            # Determine if we need an override based on detected anomalies
            if anomalies:
                # Log all anomalies
                for anomaly in anomalies:
                    logger.warning(f"Market anomaly detected: {anomaly['type']} - {anomaly['description']}")
                
                # Calculate overall severity as the maximum of individual severities
                max_severity = max([a['severity'] for a in anomalies])
                
                # Store types of anomalies for reporting
                anomaly_types = [a['type'] for a in anomalies]
                
                # Update anomaly status
                self.anomaly_status = {
                    'detected': True,
                    'severity': max_severity,
                    'types': anomaly_types,
                    'last_check': now
                }
                
                # Calculate additional tests based on severity factor
                # Severity 1.0 = no additional tests
                # Severity 2.0 = 100% more tests (double)
                additional_tests = int(self.daily_limit * (max_severity - 1.0))
                
                reason = f"Market anomalies detected: {', '.join(anomaly_types)}"
                logger.info(f"Anomaly override: {additional_tests} additional tests authorized. Severity: {max_severity:.2f}")
                
                return additional_tests, reason
            
            logger.info("No market anomalies detected that require additional testing")
            return 0, "No anomalies detected"
            
        except Exception as e:
            logger.error(f"Error in anomaly detection override: {str(e)}")
            return 0, f"Error in anomaly detection: {str(e)}"
    
    def build_backtest_queue(self, backtest_limit=100):
        """
        Build a queue of backtests based on available tickers, strategies, and a dynamic backtest limit.
        
        Uses statistical coverage and anomaly detection to intelligently allocate computational resources.
        
        Args:
            backtest_limit (int): Maximum number of backtests to queue
            
        Returns:
            bool: Success status
        """
        try:
            logging.info(f"Building backtest queue with limit {backtest_limit}")
            
            # Reset the backtest queue
            self.backtest_queue = []
            
            # Get available tickers and strategies
            tickers = self.get_available_tickers()
            strategies = self.get_available_strategies()
            
            if not tickers or not strategies:
                logging.warning("No tickers or strategies available for backtesting")
                return False
                
            # Check for market anomalies
            anomalies = self._detect_market_anomalies()
            
            # Calculate a dynamic test limit based on market conditions
            dynamic_limit = backtest_limit
            market = self._calculate_market_conditions()
            
            # Adjust limit based on volatility - more tests during high volatility
            if market["volatility"] > 0.25:
                dynamic_limit = int(dynamic_limit * 1.3)
                logging.info(f"Increasing test limit to {dynamic_limit} due to high volatility")
            
            # Adjust limit based on anomalies - more tests during anomalies
            if anomalies["detected"]:
                dynamic_limit = int(dynamic_limit * 1.5)
                logging.info(f"Increasing test limit to {dynamic_limit} due to detected market anomalies")
                
                # Focus on affected sectors if applicable
                if anomalies["affected_sectors"]:
                    logging.info(f"Focusing on sectors: {anomalies['affected_sectors']}")
                    # This would filter tickers by sector in a real implementation
            
            # Apply statistical coverage approach
            allocation_plan = self._apply_statistical_coverage(
                strategies, tickers, dynamic_limit
            )
            
            # Build queue from allocation plan
            for strategy, ticker_allocation in allocation_plan.items():
                for ticker, count in ticker_allocation.items():
                    # Generate random parameters for each backtest
                    for _ in range(count):
                        # In a real implementation, these would be optimized parameters
                        # based on historical performance and current market conditions
                        params = self._generate_strategy_parameters(strategy)
                        
                        # Calculate priority score for sorting
                        priority = self._calculate_backtest_priority(ticker, strategy)
                        
                        # Add to queue
                        self.backtest_queue.append({
                            "ticker": ticker,
                            "strategy": strategy,
                            "params": params,
                            "priority": priority
                        })
            
            # Sort the queue by priority (higher priority first)
            self.backtest_queue.sort(key=lambda x: x["priority"], reverse=True)
            
            logging.info(f"Built backtest queue with {len(self.backtest_queue)} tests")
            return True
            
        except Exception as e:
            logging.error(f"Error building backtest queue: {e}")
            return False
            
    def _generate_strategy_parameters(self, strategy):
        """
        Generate appropriate parameters for a given strategy
        
        Args:
            strategy (str): Strategy name
            
        Returns:
            dict: Strategy parameters
        """
        # This would be expanded with strategy-specific logic
        params = {
            "lookback_period": random.randint(10, 60),
            "exit_threshold": round(random.uniform(0.02, 0.1), 3),
            "take_profit": round(random.uniform(0.05, 0.3), 3),
            "stop_loss": round(random.uniform(0.03, 0.15), 3)
        }
        
        # Add strategy-specific parameters
        if strategy in ["Momentum", "Trend Following", "MACD Crossover"]:
            params["fast_period"] = random.randint(5, 20)
            params["slow_period"] = random.randint(20, 50)
            params["signal_period"] = random.randint(5, 15)
            
        elif strategy in ["Mean Reversion", "Bollinger Band Squeeze"]:
            params["std_dev"] = round(random.uniform(1.5, 3.0), 1)
            params["mean_period"] = random.randint(10, 30)
            
        elif strategy in ["Volatility Expansion", "Options Volatility Skew"]:
            params["volatility_threshold"] = round(random.uniform(0.1, 0.5), 2)
            params["iv_percentile"] = round(random.uniform(0.5, 0.9), 2)
            
        elif strategy in ["Swing Trading", "Fibonacci Retracement"]:
            params["swing_threshold"] = round(random.uniform(0.03, 0.15), 3)
            params["retracement_level"] = random.choice([0.382, 0.5, 0.618, 0.786])
            
        elif strategy in ["News Sentiment", "Sentiment-Price Correlation"]:
            params["sentiment_threshold"] = round(random.uniform(0.3, 0.8), 2)
            params["sentiment_lookback"] = random.randint(1, 5)
            
        elif strategy in ["Pairs Trading", "Statistical Arbitrage"]:
            params["correlation_threshold"] = round(random.uniform(0.7, 0.95), 2)
            params["zscore_threshold"] = round(random.uniform(1.5, 3.0), 1)
            
        elif "Earnings" in strategy:
            params["entry_days_before"] = random.randint(2, 10)
            params["exit_days_after"] = random.randint(1, 5)
            
        return params
        
    def _calculate_backtest_priority(self, ticker, strategy):
        """
        Calculate a priority score for this backtest based on ticker and strategy
        
        Args:
            ticker (str): Ticker symbol
            strategy (str): Strategy name
            
        Returns:
            float: Priority score (higher is more important)
        """
        try:
            base_priority = 50  # Base priority
            
            # Add ticker importance (0-50 points)
            ticker_importance = self._get_ticker_importance(ticker)
            base_priority += ticker_importance * 0.5
            
            # Add strategy importance based on market conditions (0-50 points)
            market = self._calculate_market_conditions()
            strategy_weights = self._get_strategy_weights()
            
            # Normalize the weight for this strategy
            weight_sum = sum(strategy_weights.values())
            normalized_weight = 50 * strategy_weights.get(strategy, 1.0) / weight_sum
            base_priority += normalized_weight
            
            # Boost priority for anomaly-related strategies during anomalies
            anomalies = self._detect_market_anomalies()
            if anomalies["detected"]:
                # Boost ML and adaptive strategies during anomalies
                if strategy in ["Machine Learning Classification", "Ensemble Methods", 
                               "Regime-Switching Models", "Kalman Filter"]:
                    base_priority += 25
                
                # Boost volatility strategies during volatility spikes
                if anomalies["volatility_spike"] and strategy in ["Volatility Expansion", 
                                                                "Options Volatility Skew",
                                                                "Protective Put"]:
                    base_priority += 20
                
                # Boost sector rotation strategies
                if anomalies["sector_rotation"] and strategy in ["ETF Rebalancing",
                                                               "Sector Rotation"]:
                    base_priority += 20
            
            # Add some randomness (0-10 points)
            base_priority += random.uniform(0, 10)
            
            return base_priority
            
        except Exception as e:
            logging.warning(f"Error calculating backtest priority: {e}")
            return 50  # Default priority

    # ===== Statistical Coverage and Anomaly Detection Methods =====
    
    def calculate_dynamic_test_limit(self):
        """
        Dynamically calculate the optimal number of backtests based on market conditions,
        recent volatility, and statistical coverage needs.
        
        Returns:
            int: The dynamically calculated backtest limit
        """
        try:
            # Get current VIX as volatility indicator
            current_vix = self._get_current_vix()
            vix_ma = self._get_vix_moving_average(days=10)
            
            # Base case - standard coverage during normal conditions
            base_limit = self.daily_limit
            
            # Adjust based on volatility level (higher volatility = more tests)
            volatility_factor = 1.0
            if current_vix > 30:  # High volatility
                volatility_factor = 2.0
            elif current_vix > 20:  # Moderate volatility
                volatility_factor = 1.5
            elif current_vix < 15:  # Low volatility
                volatility_factor = 0.8
                
            # Adjust based on volatility trend (rising volatility = more tests)
            trend_factor = 1.0
            if current_vix > vix_ma * 1.1:  # Volatility rising
                trend_factor = 1.3
            elif current_vix < vix_ma * 0.9:  # Volatility falling
                trend_factor = 0.9
                
            # Calculate special conditions factor
            anomaly_factor = 1.0
            if self.check_market_anomalies():
                anomaly_factor = 1.5  # Increase tests during anomalous conditions
                
            # Calculate final dynamic limit
            dynamic_limit = int(base_limit * volatility_factor * trend_factor * anomaly_factor)
            
            # Set reasonable bounds
            dynamic_limit = max(base_limit // 2, min(base_limit * 3, dynamic_limit))
            
            logging.info(f"Dynamic test limit calculated: {dynamic_limit} (Base: {base_limit}, " 
                        f"VIX: {current_vix:.1f}, VIX MA: {vix_ma:.1f})")
            
            return dynamic_limit
            
        except Exception as e:
            logging.error(f"Error calculating dynamic test limit: {e}")
            return self.daily_limit  # Fallback to standard limit
    
    def check_market_anomalies(self):
        """
        Check for market anomalies that might warrant increased testing:
        - Correlation breakdowns
        - Liquidity events
        - Significant market-moving news
        
        Returns:
            bool: True if anomalies detected, False otherwise
        """
        try:
            # Check for various anomaly types
            correlation_breakdown = self._check_correlation_breakdown()
            liquidity_event = self._check_liquidity_event()
            significant_news = self._check_significant_news()
            
            # If any anomaly is detected
            if correlation_breakdown or liquidity_event or significant_news:
                reason = []
                if correlation_breakdown: reason.append("correlation breakdown")
                if liquidity_event: reason.append("liquidity event")
                if significant_news: reason.append("significant news")
                
                logging.warning(f"Market anomaly detected: {', '.join(reason)}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking market anomalies: {e}")
            return False  # Assume no anomalies on error

    def _get_ticker_importance(self, ticker):
        """
        Calculate the importance score for a ticker based on market cap, 
        liquidity, sector performance, and volatility.
        
        Args:
            ticker (str): Ticker symbol
            
        Returns:
            float: Importance score
        """
        try:
            # This would connect to market data APIs for real metrics
            # Placeholder scores for demonstration purposes
            base_importance = {
                "AAPL": 95, "MSFT": 94, "GOOGL": 92, "AMZN": 93, "META": 88,
                "NVDA": 90, "TSLA": 87, "JPM": 85, "V": 84, "JNJ": 82,
                "PG": 80, "WMT": 79, "BAC": 77, "DIS": 75, "NFLX": 82,
                "INTC": 72, "AMD": 79, "IBM": 70, "CSCO": 75, "VZ": 68,
                "T": 65, "PFE": 72, "MRK": 73, "KO": 71, "PEP": 73,
                "SPY": 98, "QQQ": 95, "IWM": 90, "DIA": 88, "GLD": 75,
                "SLV": 65, "USO": 60, "TLT": 70, "HYG": 65, "VIX": 50
            }
            
            # Default value for unknown tickers
            return base_importance.get(ticker, 50)
            
        except Exception as e:
            logging.warning(f"Error calculating ticker importance for {ticker}: {e}")
            return 50  # Default importance
    
    def _normalize_data_series(self, data, min_val=0, max_val=100):
        """
        Normalize a data series to a specific range
        
        Args:
            data (list): List of values to normalize
            min_val (float): Minimum value in output range
            max_val (float): Maximum value in output range
            
        Returns:
            list: Normalized data series
        """
        if not data:
            return []
            
        try:
            data_min = min(data)
            data_max = max(data)
            
            # Avoid division by zero
            if data_max == data_min:
                return [min_val + (max_val - min_val) / 2] * len(data)
                
            # Normalize to specified range
            normalized = [
                min_val + (max_val - min_val) * (x - data_min) / (data_max - data_min)
                for x in data
            ]
            
            return normalized
            
        except Exception as e:
            logging.warning(f"Error normalizing data series: {e}")
            return data
            
    def _detect_outliers(self, data, threshold=2.0):
        """
        Detect outliers in a data series using z-score method
        
        Args:
            data (list): List of values to check for outliers
            threshold (float): Z-score threshold for outlier detection
            
        Returns:
            list: Indices of outliers in the data series
        """
        if not data or len(data) < 3:
            return []
            
        try:
            # Calculate mean and standard deviation
            mean = sum(data) / len(data)
            std_dev = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
            
            # Avoid division by zero
            if std_dev == 0:
                return []
                
            # Find outliers using z-score
            outliers = [
                i for i, x in enumerate(data) 
                if abs(x - mean) / std_dev > threshold
            ]
            
            return outliers
            
        except Exception as e:
            logging.warning(f"Error detecting outliers: {e}")
            return []
    
    def get_sector_performance(self, sectors=None):
        """
        Get recent performance data for market sectors
        
        Args:
            sectors (list): Optional list of sectors to filter
            
        Returns:
            dict: Sector performance data
        """
        try:
            # This would connect to market data APIs for real metrics
            # Placeholder data for demonstration purposes
            sector_data = {
                "Technology": {"performance": 0.05, "volatility": 0.18, "trend": "up"},
                "Healthcare": {"performance": 0.02, "volatility": 0.14, "trend": "sideways"},
                "Financials": {"performance": 0.01, "volatility": 0.16, "trend": "down"},
                "Consumer Discretionary": {"performance": 0.03, "volatility": 0.20, "trend": "up"},
                "Consumer Staples": {"performance": 0.00, "volatility": 0.10, "trend": "sideways"},
                "Energy": {"performance": -0.02, "volatility": 0.22, "trend": "down"},
                "Materials": {"performance": 0.01, "volatility": 0.15, "trend": "sideways"},
                "Industrials": {"performance": 0.02, "volatility": 0.16, "trend": "up"},
                "Utilities": {"performance": -0.01, "volatility": 0.12, "trend": "down"},
                "Real Estate": {"performance": -0.03, "volatility": 0.17, "trend": "down"}
            }
            
            if sectors:
                return {k: v for k, v in sector_data.items() if k in sectors}
            return sector_data
            
        except Exception as e:
            logging.warning(f"Error retrieving sector performance: {e}")
            return {}

    def _calculate_market_conditions(self):
        """
        Calculate current market conditions based on volatility, trends, and macro indicators
        
        Returns:
            dict: Market conditions data
        """
        try:
            # This would connect to market data APIs for real metrics
            # Placeholder data for demonstration purposes
            market_conditions = {
                "volatility": 0.15,  # VIX-like measure
                "trend_strength": 0.60,  # 0-1 scale, higher means stronger trend
                "market_regime": "bull",  # bull, bear, sideways
                "liquidity": 0.75,  # 0-1 scale, higher means more liquid
                "macro_risk": 0.40,  # 0-1 scale, higher means more risk
                "sector_rotation": 0.30,  # 0-1 scale, higher means more rotation
                "corr_breakdown": False,  # Boolean, True if correlations breaking down
                "anomaly_detected": False,  # Boolean, True if market anomaly detected
                "earnings_season": False,  # Boolean, True during earnings season
                "fed_meeting_week": False  # Boolean, True during Fed meeting weeks
            }
            return market_conditions
            
        except Exception as e:
            logging.warning(f"Error calculating market conditions: {e}")
            return {
                "volatility": 0.2,
                "trend_strength": 0.5,
                "market_regime": "unknown"
            }
    
    def _get_strategy_weights(self):
        """
        Calculate strategy weights based on current market conditions
        
        Returns:
            dict: Strategy weights dictionary
        """
        try:
            market = self._calculate_market_conditions()
            
            # Base weights - will be adjusted based on market conditions
            weights = {
                # Basic Strategies
                "Momentum": 1.0,
                "Trend Following": 1.0,
                "Breakout": 1.0,
                "Statistical Arbitrage": 1.0,
                "Mean Reversion": 1.0,
                "Volatility Expansion": 1.0,
                "Swing Trading": 1.0,
                "Options Volatility Skew": 1.0,
                "News Sentiment": 1.0,
                "Pairs Trading": 1.0,
                "MACD Crossover": 1.0,
                "Earnings Volatility": 1.0,
                
                # Technical Analysis Strategies
                "Fibonacci Retracement": 1.0,
                "Ichimoku Cloud": 1.0,
                "RSI Divergence": 1.0,
                "Triple Moving Average": 1.0,
                "Bollinger Band Squeeze": 1.0,
                "ADX Trend Strength": 1.0,
                
                # Options-Specific Strategies
                "Iron Condor": 1.0,
                "Calendar Spreads": 1.0,
                "Butterfly Spreads": 1.0,
                "Covered Call Writing": 1.0,
                "Protective Put": 1.0,
                "Ratio Spreads": 1.0,
                
                # Quantitative Strategies
                "Kalman Filter": 1.0,
                "Machine Learning Classification": 1.0,
                "Ensemble Methods": 1.0,
                "PCA Factor Analysis": 1.0,
                "Regime-Switching Models": 1.0,
                "Sentiment-Price Correlation": 1.0,
                
                # Event-Driven Strategies
                "Post-Earnings Announcement Drift": 1.0,
                "ETF Rebalancing": 1.0,
                "Index Inclusion": 1.0,
                "Merger Arbitrage": 1.0,
                "Short Interest Squeeze": 1.0,
                "Buyback Announcement": 1.0
            }
            
            # Adjust weights based on market conditions
            
            # Volatility adjustments
            if market["volatility"] > 0.25:  # High volatility
                weights["Mean Reversion"] *= 1.5
                weights["Options Volatility Skew"] *= 1.6
                weights["Volatility Expansion"] *= 1.7
                weights["Protective Put"] *= 1.5
                weights["Butterfly Spreads"] *= 1.3
                weights["Iron Condor"] *= 0.7  # Reduce in high volatility
            elif market["volatility"] < 0.1:  # Low volatility
                weights["Iron Condor"] *= 1.5
                weights["Covered Call Writing"] *= 1.4
                weights["Volatility Expansion"] *= 0.7
                weights["Calendar Spreads"] *= 1.3
            
            # Trend strength adjustments
            if market["trend_strength"] > 0.7:  # Strong trend
                weights["Trend Following"] *= 1.6
                weights["Momentum"] *= 1.5
                weights["MACD Crossover"] *= 1.4
                weights["ADX Trend Strength"] *= 1.5
                weights["Mean Reversion"] *= 0.7  # Reduce in strong trends
            elif market["trend_strength"] < 0.3:  # Weak trend
                weights["Mean Reversion"] *= 1.5
                weights["Pairs Trading"] *= 1.3
                weights["Statistical Arbitrage"] *= 1.4
                weights["Bollinger Band Squeeze"] *= 1.3
                weights["Trend Following"] *= 0.7  # Reduce in weak trends
            
            # Market regime adjustments
            if market["market_regime"] == "bull":
                weights["Momentum"] *= 1.4
                weights["Breakout"] *= 1.3
                weights["Covered Call Writing"] *= 1.3
                weights["Calendar Spreads"] *= 1.2
                weights["Short Interest Squeeze"] *= 1.4
            elif market["market_regime"] == "bear":
                weights["Protective Put"] *= 1.6
                weights["Mean Reversion"] *= 1.3
                weights["Pair Trading"] *= 1.4
                weights["Statistical Arbitrage"] *= 1.5
                weights["Ratio Spreads"] *= 1.3
            
            # Special conditions
            if market["earnings_season"]:
                weights["Earnings Volatility"] *= 2.0
                weights["Post-Earnings Announcement Drift"] *= 1.8
            
            if market["fed_meeting_week"]:
                weights["Options Volatility Skew"] *= 1.5
                weights["Protective Put"] *= 1.3
            
            if market["anomaly_detected"]:
                weights["Machine Learning Classification"] *= 1.5
                weights["Ensemble Methods"] *= 1.6
                weights["Regime-Switching Models"] *= 1.7
            
            # Normalize weights to sum to desired allocation
            return weights
            
        except Exception as e:
            logging.warning(f"Error calculating strategy weights: {e}")
            return {s: 1.0 for s in self.get_available_strategies()}
            
    def _detect_market_anomalies(self):
        """
        Detect anomalies in the current market data that might impact backtesting strategy selection
        
        Returns:
            dict: Detected anomalies with details
        """
        try:
            # This would connect to market data APIs for real metrics and run statistical tests
            # Placeholder data for demonstration purposes
            anomalies = {
                "detected": False,
                "volatility_spike": False,
                "correlation_breakdown": False,
                "sector_rotation": False,
                "unusual_volume": False,
                "patterns": [],
                "affected_sectors": [],
                "affected_tickers": []
            }
            
            # Example anomaly detection logic
            market = self._calculate_market_conditions()
            sector_data = self.get_sector_performance()
            
            # Check for volatility spike
            if market["volatility"] > 0.3:
                anomalies["detected"] = True
                anomalies["volatility_spike"] = True
                anomalies["patterns"].append("volatility_regime_change")
            
            # Check for unusual sector performance
            sector_returns = [data["performance"] for data in sector_data.values()]
            sector_outliers = self._detect_outliers(sector_returns)
            
            if sector_outliers:
                anomalies["detected"] = True
                anomalies["sector_rotation"] = True
                anomalies["affected_sectors"] = [list(sector_data.keys())[i] for i in sector_outliers]
            
            # Add more sophisticated anomaly detection as needed
            
            return anomalies
            
        except Exception as e:
            logging.warning(f"Error detecting market anomalies: {e}")
            return {"detected": False}
            
    def _apply_statistical_coverage(self, strategies, tickers, total_limit):
        """
        Apply statistical coverage to ensure diverse testing across strategies and tickers
        
        Args:
            strategies (list): Available strategies
            tickers (list): Available tickers
            total_limit (int): Total number of backtests to allocate
            
        Returns:
            dict: Allocation plan for backtests {strategy: {ticker: count}}
        """
        try:
            # Get strategy weights based on market conditions
            strategy_weights = self._get_strategy_weights()
            
            # Normalize weights to sum to 1.0
            weight_sum = sum(strategy_weights.get(s, 1.0) for s in strategies)
            if weight_sum == 0:
                weight_sum = len(strategies)  # Avoid division by zero
                
            normalized_weights = {}
            for s in strategies:
                normalized_weights[s] = strategy_weights.get(s, 1.0) / weight_sum
            
            # Allocate backtests by strategy
            strategy_allocation = {}
            remaining = total_limit
            
            # First pass: allocate based on weights
            for strategy in strategies:
                count = int(total_limit * normalized_weights[strategy])
                if count < 1:  # Ensure at least one test per strategy
                    count = 1
                strategy_allocation[strategy] = count
                remaining -= count
            
            # Second pass: allocate remaining tests to top strategies
            sorted_strategies = sorted(
                [(s, normalized_weights[s]) for s in strategies],
                key=lambda x: x[1],
                reverse=True
            )
            
            idx = 0
            while remaining > 0 and idx < len(sorted_strategies):
                strategy_allocation[sorted_strategies[idx][0]] += 1
                remaining -= 1
                idx = (idx + 1) % len(sorted_strategies)
            
            # Now distribute each strategy's allocation across tickers
            allocation_plan = {}
            for strategy, total_count in strategy_allocation.items():
                # Get ticker importance
                ticker_importance = {t: self._get_ticker_importance(t) for t in tickers}
                
                # Normalize ticker importance
                importance_sum = sum(ticker_importance.values())
                normalized_importance = {
                    t: imp / importance_sum for t, imp in ticker_importance.items()
                }
                
                # Allocate tickers for this strategy
                ticker_counts = {}
                remaining = total_count
                
                # First pass: allocate based on importance
                for ticker in tickers:
                    count = max(1, int(total_count * normalized_importance[ticker]))
                    if count > remaining:
                        count = remaining
                    ticker_counts[ticker] = count
                    remaining -= count
                    
                    if remaining <= 0:
                        break
                
                # Second pass: allocate remaining to top tickers
                sorted_tickers = sorted(
                    [(t, normalized_importance[t]) for t in tickers],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                idx = 0
                while remaining > 0 and idx < len(sorted_tickers):
                    ticker_counts[sorted_tickers[idx][0]] += 1
                    remaining -= 1
                    idx = (idx + 1) % len(sorted_tickers)
                
                allocation_plan[strategy] = ticker_counts
            
            return allocation_plan
            
        except Exception as e:
            logging.warning(f"Error applying statistical coverage: {e}")
            # Fallback to uniform distribution
            allocation_plan = {}
            per_strategy = max(1, total_limit // len(strategies))
            
            for strategy in strategies:
                tickers_per_strategy = min(len(tickers), per_strategy)
                allocation_plan[strategy] = {t: 1 for t in tickers[:tickers_per_strategy]}
                
            return allocation_plan

    def analyze_market_data(self, days_lookback=30):
        """
        Analyze recent market data to detect patterns and regime changes
        that should influence backtest allocation
        
        Args:
            days_lookback (int): Number of days to look back for analysis
            
        Returns:
            dict: Analysis results with identified patterns and recommendations
        """
        try:
            logging.info(f"Analyzing market data for the past {days_lookback} days")
            
            # This would retrieve real market data in production
            # For demonstration purposes, using mock data
            results = {
                "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "period_analyzed": f"{days_lookback} days",
                "patterns_detected": [],
                "regime_changes": [],
                "volatility_analysis": {},
                "correlation_analysis": {},
                "strategy_recommendations": [],
                "ticker_recommendations": []
            }
            
            # Get market conditions and sector performance
            market = self._calculate_market_conditions()
            sector_data = self.get_sector_performance()
            
            # Detect patterns
            if market["volatility"] > 0.25:
                results["patterns_detected"].append({
                    "name": "high_volatility",
                    "confidence": 0.85,
                    "description": "Market showing elevated volatility levels"
                })
                
                results["strategy_recommendations"].append({
                    "strategy": "Protective Put",
                    "reason": "Elevated volatility suggests hedging positions",
                    "priority": "high"
                })
                
                results["strategy_recommendations"].append({
                    "strategy": "Volatility Expansion",
                    "reason": "Current environment favorable for volatility-based strategies",
                    "priority": "high"
                })
                
            # Check for strong trends
            if market["trend_strength"] > 0.7:
                results["patterns_detected"].append({
                    "name": "strong_trend",
                    "confidence": 0.80,
                    "description": "Market showing strong directional trend"
                })
                
                trend_direction = "upward" if market["market_regime"] == "bull" else "downward"
                results["strategy_recommendations"].append({
                    "strategy": "Trend Following",
                    "reason": f"Strong {trend_direction} trend detected",
                    "priority": "high"
                })
            
            # Identify sector rotation if present
            outperforming_sectors = []
            underperforming_sectors = []
            
            for sector, data in sector_data.items():
                if data["performance"] > 0.03:
                    outperforming_sectors.append(sector)
                elif data["performance"] < -0.02:
                    underperforming_sectors.append(sector)
            
            if outperforming_sectors and underperforming_sectors:
                results["patterns_detected"].append({
                    "name": "sector_rotation",
                    "confidence": 0.75,
                    "description": "Significant performance divergence between sectors",
                    "details": {
                        "outperforming": outperforming_sectors,
                        "underperforming": underperforming_sectors
                    }
                })
                
                results["strategy_recommendations"].append({
                    "strategy": "Sector Rotation",
                    "reason": "Active sector rotation detected",
                    "priority": "high"
                })
                
                # Add tickers from outperforming sectors to recommendations
                # In real implementation, would select specific tickers from these sectors
                results["ticker_recommendations"].extend([
                    {"ticker": "XLK", "reason": "Technology sector outperformance", "priority": "high"} 
                    if "Technology" in outperforming_sectors else None,
                    {"ticker": "XLF", "reason": "Financial sector outperformance", "priority": "high"}
                    if "Financials" in outperforming_sectors else None,
                    {"ticker": "XLV", "reason": "Healthcare sector outperformance", "priority": "high"}
                    if "Healthcare" in outperforming_sectors else None
                ])
                results["ticker_recommendations"] = [r for r in results["ticker_recommendations"] if r is not None]
                
            # Check for potential regime changes
            if market["volatility"] > 0.25 and market["trend_strength"] < 0.3:
                results["regime_changes"].append({
                    "name": "volatility_regime_change",
                    "confidence": 0.70,
                    "description": "Possible transition to high volatility, low trend regime",
                    "implications": "Favor mean reversion and volatility-based strategies"
                })
                
                results["strategy_recommendations"].append({
                    "strategy": "Mean Reversion",
                    "reason": "Regime change to high volatility, low trend environment",
                    "priority": "high"
                })
            
            # Perform volatility analysis
            results["volatility_analysis"] = {
                "current_level": market["volatility"],
                "historical_percentile": 65,  # Mock data, would be calculated
                "term_structure": "contango",  # Mock data, would be calculated
                "expected_direction": "stable"
            }
            
            # Perform correlation analysis
            results["correlation_analysis"] = {
                "average_correlation": 0.45,  # Mock data
                "correlation_trend": "decreasing",
                "anomalous_correlations": False
            }
            
            # If correlations are decreasing, recommend pair trading
            if results["correlation_analysis"]["correlation_trend"] == "decreasing":
                results["strategy_recommendations"].append({
                    "strategy": "Pairs Trading",
                    "reason": "Decreasing cross-asset correlations create opportunities",
                    "priority": "medium"
                })
            
            logging.info(f"Market analysis complete. Detected {len(results['patterns_detected'])} patterns and {len(results['regime_changes'])} regime changes")
            return results
            
        except Exception as e:
            logging.error(f"Error in market data analysis: {e}")
            return {
                "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "error": str(e),
                "patterns_detected": [],
                "strategy_recommendations": []
            }

    def generate_performance_report(self, timeframe="daily"):
        """
        Generate a performance report for completed backtests
        
        Args:
            timeframe (str): Time frame for the report ('daily', 'weekly', 'monthly')
            
        Returns:
            dict: Performance report with metrics and insights
        """
        try:
            logging.info(f"Generating {timeframe} performance report")
            
            # This would query a database of backtest results in production
            # For demonstration purposes, using mock data
            report = {
                "report_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "timeframe": timeframe,
                "summary_metrics": {},
                "top_performers": [],
                "strategy_insights": [],
                "market_correlation": {},
                "performance_by_sector": {},
                "recommendations": []
            }
            
            # Mock data for strategy performance
            strategy_performance = {
                "Momentum": {"win_rate": 0.65, "sharpe": 1.4, "max_drawdown": 0.12},
                "Trend Following": {"win_rate": 0.58, "sharpe": 1.2, "max_drawdown": 0.15},
                "Breakout": {"win_rate": 0.52, "sharpe": 1.1, "max_drawdown": 0.18},
                "Mean Reversion": {"win_rate": 0.62, "sharpe": 1.5, "max_drawdown": 0.08},
                "Volatility Expansion": {"win_rate": 0.55, "sharpe": 1.3, "max_drawdown": 0.14},
                "Protective Put": {"win_rate": 0.48, "sharpe": 0.9, "max_drawdown": 0.05},
                "Iron Condor": {"win_rate": 0.72, "sharpe": 1.1, "max_drawdown": 0.07},
                "Pairs Trading": {"win_rate": 0.60, "sharpe": 1.3, "max_drawdown": 0.09},
                "MACD Crossover": {"win_rate": 0.54, "sharpe": 1.0, "max_drawdown": 0.13},
                "RSI Divergence": {"win_rate": 0.59, "sharpe": 1.2, "max_drawdown": 0.11}
            }
            
            # Calculate summary metrics
            win_rates = [data["win_rate"] for data in strategy_performance.values()]
            sharpes = [data["sharpe"] for data in strategy_performance.values()]
            drawdowns = [data["max_drawdown"] for data in strategy_performance.values()]
            
            report["summary_metrics"] = {
                "avg_win_rate": round(sum(win_rates) / len(win_rates), 2),
                "avg_sharpe": round(sum(sharpes) / len(sharpes), 2),
                "avg_max_drawdown": round(sum(drawdowns) / len(drawdowns), 2),
                "best_sharpe": round(max(sharpes), 2),
                "worst_drawdown": round(max(drawdowns), 2),
                "strategies_analyzed": len(strategy_performance)
            }
            
            # Get top performers by Sharpe ratio
            top_by_sharpe = sorted(
                [(s, data["sharpe"]) for s, data in strategy_performance.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for strategy, sharpe in top_by_sharpe:
                report["top_performers"].append({
                    "strategy": strategy,
                    "sharpe": strategy_performance[strategy]["sharpe"],
                    "win_rate": strategy_performance[strategy]["win_rate"],
                    "max_drawdown": strategy_performance[strategy]["max_drawdown"]
                })
            
            # Generate insights for each strategy
            for strategy, metrics in strategy_performance.items():
                # Only include detailed insights for strategies with good performance
                if metrics["sharpe"] >= 1.2:
                    insight = {
                        "strategy": strategy,
                        "performance": "good" if metrics["sharpe"] > 1.3 else "average",
                        "key_metrics": metrics,
                        "observations": []
                    }
                    
                    # Add strategy-specific observations
                    if strategy == "Mean Reversion" and metrics["win_rate"] > 0.6:
                        insight["observations"].append(
                            "Strong performance in current market regime"
                        )
                    elif strategy == "Momentum" and metrics["sharpe"] > 1.3:
                        insight["observations"].append(
                            "Effective in capturing recent market trends"
                        )
                    elif strategy == "Volatility Expansion" and metrics["sharpe"] > 1.2:
                        insight["observations"].append(
                            "Benefiting from current volatility environment"
                        )
                    
                    report["strategy_insights"].append(insight)
            
            # Market correlation analysis
            # This would use actual correlation data in production
            report["market_correlation"] = {
                "highest_correlation": {"strategy": "Momentum", "correlation": 0.75},
                "lowest_correlation": {"strategy": "Pairs Trading", "correlation": 0.15},
                "avg_correlation": 0.42
            }
            
            # Performance by sector
            # This would use actual sector performance data in production
            report["performance_by_sector"] = {
                "Technology": {"avg_return": 0.08, "best_strategy": "Momentum"},
                "Healthcare": {"avg_return": 0.05, "best_strategy": "Mean Reversion"},
                "Financials": {"avg_return": 0.03, "best_strategy": "Breakout"},
                "Consumer Discretionary": {"avg_return": 0.06, "best_strategy": "MACD Crossover"},
                "Energy": {"avg_return": -0.02, "best_strategy": "Protective Put"}
            }
            
            # Generate recommendations
            market = self._calculate_market_conditions()
            
            # Recommend strategies that perform well in current conditions
            if market["volatility"] > 0.25:
                report["recommendations"].append({
                    "type": "strategy_focus",
                    "recommendation": "Increase allocation to Mean Reversion strategies",
                    "reason": "Strong performance in current high volatility environment"
                })
            
            if market["trend_strength"] > 0.7:
                report["recommendations"].append({
                    "type": "strategy_focus",
                    "recommendation": "Maintain allocation to Momentum strategies",
                    "reason": "Effective in capturing strong market trends"
                })
            
            # Look for underperforming strategies to reduce
            min_sharpe = min(sharpes)
            worst_strategy = next(s for s, data in strategy_performance.items() 
                              if data["sharpe"] == min_sharpe)
            
            report["recommendations"].append({
                "type": "strategy_reduction",
                "recommendation": f"Reduce allocation to {worst_strategy} strategies",
                "reason": f"Underperforming with Sharpe ratio of {min_sharpe}"
            })
            
            # Recommend sector focus
            best_sector = max(report["performance_by_sector"].items(), 
                           key=lambda x: x[1]["avg_return"])
            
            report["recommendations"].append({
                "type": "sector_focus",
                "recommendation": f"Increase focus on {best_sector[0]} sector",
                "reason": f"Sector showing strong returns ({best_sector[1]['avg_return']*100:.1f}%) with {best_sector[1]['best_strategy']} strategies"
            })
            
            logging.info(f"Generated performance report with {len(report['recommendations'])} recommendations")
            return report
            
        except Exception as e:
            logging.error(f"Error generating performance report: {e}")
            return {
                "report_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "error": str(e),
                "summary_metrics": {},
                "recommendations": []
            }

    def get_available_tickers(self):
        """
        Get the list of available tickers for backtesting
        
        Returns:
            list: List of ticker symbols
        """
        try:
            # Check if we have a watchlist
            if hasattr(self, 'watchlist') and self.watchlist:
                return self.watchlist
                
            # If no watchlist, return default tickers
            default_tickers = [
                # Major tech stocks
                "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", 
                
                # Financial sector
                "JPM", "BAC", "GS", "V", "MA",
                
                # Healthcare 
                "JNJ", "PFE", "UNH", "ABT", "MRK",
                
                # Consumer
                "PG", "KO", "PEP", "WMT", "MCD",
                
                # Energy
                "XOM", "CVX", "COP",
                
                # ETFs
                "SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "GLD", "SLV"
            ]
            
            logging.info(f"Using {len(default_tickers)} default tickers")
            return default_tickers
            
        except Exception as e:
            logging.error(f"Error getting available tickers: {e}")
            # Return a minimal default set if something goes wrong
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY", "QQQ"]
    
    def get_available_strategies(self):
        """
        Get the list of available strategies for backtesting
        
        Returns:
            list: List of strategy names
        """
        try:
            # Check if we have strategies loaded
            if hasattr(self, 'strategies') and self.strategies:
                return self.strategies
                
            # If no strategies loaded, return default strategies
            default_strategies = [
                "Momentum", 
                "Trend Following", 
                "Breakout", 
                "Statistical Arbitrage", 
                "Mean Reversion", 
                "Volatility Expansion", 
                "Swing Trading", 
                "Options Volatility Skew", 
                "News Sentiment", 
                "Pairs Trading", 
                "MACD Crossover", 
                "Earnings Volatility"
            ]
            
            logging.info(f"Using {len(default_strategies)} default strategies")
            return default_strategies
            
        except Exception as e:
            logging.error(f"Error getting available strategies: {e}")
            # Return a minimal default set if something goes wrong
            return ["Momentum", "Trend Following", "Mean Reversion"]

    def get_technical_indicator(self, symbol, indicator_type, time_period=20, series_type="close"):
        """
        Get technical indicators from Alpha Vantage API.
        
        Args:
            symbol (str): Stock ticker symbol
            indicator_type (str): Type of indicator (SMA, EMA, RSI, MACD, BBANDS, etc.)
            time_period (int): Time period for indicator calculation
            series_type (str): Type of price data to use (close, open, high, low)
            
        Returns:
            pd.DataFrame: DataFrame containing indicator values or None if error
        """
        try:
            # Check if Alpha Vantage API key is available
            api_key = self.api_keys.get("alpha_vantage")
            if not api_key:
                logger.warning(f"Alpha Vantage API key not set. Unable to fetch {indicator_type} for {symbol}.")
                return None
                
            base_url = "https://www.alphavantage.co/query"
            
            # Set parameters based on indicator type
            params = {
                "function": indicator_type,
                "symbol": symbol,
                "interval": "daily",
                "time_period": time_period,
                "series_type": series_type,
                "apikey": api_key
            }
            
            # Special case for MACD which has different parameters
            if indicator_type == "MACD":
                params.pop("time_period", None)
                params["fastperiod"] = 12
                params["slowperiod"] = 26
                params["signalperiod"] = 9
            
            # Special case for BBANDS which needs additional parameters
            if indicator_type == "BBANDS":
                params["nbdevup"] = 2
                params["nbdevdn"] = 2
                params["matype"] = 0  # Simple Moving Average
            
            # Rate limiting for API calls - sleep if needed
            # For free tier (5 calls per minute)
            now = time.time()
            if hasattr(self, 'last_av_call') and now - self.last_av_call < 12.0:  # Allow 5 calls per minute
                sleep_time = 12.0 - (now - self.last_av_call)
                logger.debug(f"Rate limiting Alpha Vantage API: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Make API request
            logger.info(f"Requesting {indicator_type} for {symbol} from Alpha Vantage")
            response = requests.get(base_url, params=params)
            self.last_av_call = time.time()  # Update last call time
            
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if "Note" in data:  # API limit reached
                logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
            
            # Parse the response based on indicator type
            df = None
            
            # Most indicators return in this format with "Technical Analysis: X"
            for key in data.keys():
                if key.startswith("Technical Analysis"):
                    indicator_data = data[key]
                    df = pd.DataFrame.from_dict(indicator_data, orient="index")
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index()
                    
                    # Convert string values to numeric
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col])
                    
                    break
            
            # Special case for MACD which has a different structure
            if indicator_type == "MACD" and df is not None:
                # Rename columns to more descriptive names
                if len(df.columns) >= 3:
                    df.columns = ["MACD", "MACD_Signal", "MACD_Hist"]
            
            # Special case for BBANDS which has a different structure
            if indicator_type == "BBANDS" and df is not None:
                # Rename columns to more descriptive names
                if len(df.columns) >= 3:
                    df.columns = ["Real Upper Band", "Real Middle Band", "Real Lower Band"]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {indicator_type} for {symbol}: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, price_data, indicators=None):
        """
        Calculate technical indicators from price data when API calls are not available or as fallback.
        
        Args:
            price_data (pd.DataFrame): DataFrame with OHLCV data
            indicators (list): List of indicators to calculate
            
        Returns:
            dict: Dictionary containing calculated indicators
        """
        if price_data is None or price_data.empty:
            return {}
            
        if indicators is None:
            indicators = ["SMA", "EMA", "RSI", "MACD", "BBANDS"]
            
        result = {}
        
        # Make sure we have the necessary price data
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        available_cols = [col for col in required_cols if col in price_data.columns]
        if len(available_cols) < 4:  # Need at least OHLC data
            logger.warning(f"Insufficient price data columns: {available_cols}")
            return {}
            
        # Simple Moving Average (SMA)
        if "SMA" in indicators:
            result["SMA20"] = price_data["Close"].rolling(window=20).mean()
            result["SMA50"] = price_data["Close"].rolling(window=50).mean()
            result["SMA200"] = price_data["Close"].rolling(window=200).mean()
            
        # Exponential Moving Average (EMA)
        if "EMA" in indicators:
            result["EMA12"] = price_data["Close"].ewm(span=12, adjust=False).mean()
            result["EMA26"] = price_data["Close"].ewm(span=26, adjust=False).mean()
            
        # Relative Strength Index (RSI)
        if "RSI" in indicators:
            delta = price_data["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            result["RSI"] = 100 - (100 / (1 + rs))
            
        # Moving Average Convergence Divergence (MACD)
        if "MACD" in indicators:
            ema12 = price_data["Close"].ewm(span=12, adjust=False).mean()
            ema26 = price_data["Close"].ewm(span=26, adjust=False).mean()
            result["MACD"] = ema12 - ema26
            result["MACD_Signal"] = result["MACD"].ewm(span=9, adjust=False).mean()
            result["MACD_Hist"] = result["MACD"] - result["MACD_Signal"]
            
        # Bollinger Bands
        if "BBANDS" in indicators:
            sma20 = price_data["Close"].rolling(window=20).mean()
            std20 = price_data["Close"].rolling(window=20).std()
            result["BB_Upper"] = sma20 + (std20 * 2)
            result["BB_Middle"] = sma20
            result["BB_Lower"] = sma20 - (std20 * 2)
            
        return result

    def _get_current_vix(self):
        """
        Fetches the current VIX value from a market data API.
        
        Returns:
            float: Current VIX level or a default value if unavailable
        """
        try:
            if not self.vix_api_key:
                # No API key available, using simulated data
                return random.uniform(15, 30)
            
            # In a real implementation, this would use a market data API
            # Example with alpha vantage: 
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=VIX&interval=5min&apikey={self.vix_api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Extract latest VIX value
                # Note: The exact structure would depend on the API used
                time_series = data.get("Time Series (5min)", {})
                if time_series:
                    latest_time = sorted(time_series.keys())[-1]
                    latest_data = time_series[latest_time]
                    return float(latest_data.get("4. close", 20.0))
                
            # Fallback to default
            return 20.0
            
        except Exception as e:
            logger.warning(f"Error fetching VIX data: {str(e)}")
            return 20.0  # Default to moderate volatility
    
    def analyze_market_conditions(self, symbols=None):
        """
        Analyze market conditions for a list of symbols using technical indicators.
        
        Args:
            symbols (list, optional): List of symbols to analyze. If None, uses self.watchlist.
            
        Returns:
            dict: Analysis results with overall market conditions and individual symbol analyses
        """
        if symbols is None:
            symbols = self.watchlist[:5]  # Use top 5 symbols from watchlist for overall market analysis
        
        if not symbols:
            logger.warning("No symbols provided for market analysis")
            return {"overall": {"trend": "neutral", "strength": 0.5, "volatility": "medium"}}
        
        results = {}
        all_analyses = []
        
        for symbol in symbols:
            try:
                # Rate limit Alpha Vantage API calls
                self._rate_limit_api_call()
                
                # Get technical indicators from Alpha Vantage
                analysis = self._get_technical_indicators(symbol)
                
                if analysis:
                    results[symbol] = analysis
                    all_analyses.append(analysis)
                    logger.debug(f"Market analysis for {symbol}: {analysis}")
            except Exception as e:
                logger.error(f"Error analyzing market conditions for {symbol}: {str(e)}")
                continue
        
        # Assess overall market conditions
        if all_analyses:
            results["overall"] = self._assess_overall_market(all_analyses)
        else:
            results["overall"] = {"trend": "neutral", "strength": 0.5, "volatility": "medium", "momentum": "neutral"}
        
        logger.info(f"Overall market conditions: {results['overall']}")
        return results
    
    def _rate_limit_api_call(self):
        """Rate limit API calls to comply with Alpha Vantage restrictions"""
        now = time.time()
        
        # Remove timestamps older than 1 minute
        self.last_api_call_times = [t for t in self.last_api_call_times if now - t < 60]
        
        # If we've hit the limit, wait
        if len(self.last_api_call_times) >= self.max_api_calls_per_minute:
            sleep_time = 60 - (now - self.last_api_call_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limiting API calls, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.last_api_call_times.append(time.time())
    
    def _get_technical_indicators(self, symbol):
        """
        Get technical indicators for a symbol using Alpha Vantage API
        
        Args:
            symbol (str): Stock symbol to analyze
            
        Returns:
            dict: Technical analysis results
        """
        try:
            base_url = "https://www.alphavantage.co/query"
            
            # Get SMA data (50-day and 200-day)
            params_sma_50 = {
                "function": "SMA",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 50,
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key
            }
            
            params_sma_200 = {
                "function": "SMA",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 200,
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key
            }
            
            # Get RSI data (14-day)
            params_rsi = {
                "function": "RSI",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key
            }
            
            # Get MACD data
            params_macd = {
                "function": "MACD",
                "symbol": symbol,
                "interval": "daily",
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key,
                "fastperiod": 12,
                "slowperiod": 26,
                "signalperiod": 9
            }
            
            # Get BBANDS data
            params_bbands = {
                "function": "BBANDS",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 20,
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key,
                "nbdevup": 2,
                "nbdevdn": 2,
                "matype": 0
            }
            
            # Get VIX data if symbol is an index
            vix_value = None
            if symbol in ["SPY", "QQQ", "DIA", "IWM"]:
                self._rate_limit_api_call()  # Rate limit before VIX call
                params_vix = {
                    "function": "TIME_SERIES_INTRADAY",
                    "symbol": "^VIX",
                    "interval": "5min",
                    "apikey": self.vix_api_key
                }
                
                response = requests.get(base_url, params=params_vix)
                if response.status_code == 200:
                    data = response.json()
                    if "Time Series (5min)" in data:
                        latest_time = sorted(data["Time Series (5min)"].keys(), reverse=True)[0]
                        vix_value = float(data["Time Series (5min)"][latest_time]["4. close"])
            
            # Make API calls with rate limiting
            self._rate_limit_api_call()
            response_sma_50 = requests.get(base_url, params=params_sma_50)
            
            self._rate_limit_api_call()
            response_sma_200 = requests.get(base_url, params=params_sma_200)
            
            self._rate_limit_api_call()
            response_rsi = requests.get(base_url, params=params_rsi)
            
            self._rate_limit_api_call()
            response_macd = requests.get(base_url, params=params_macd)
            
            self._rate_limit_api_call()
            response_bbands = requests.get(base_url, params=params_bbands)
            
            # Process responses
            sma_50_data = response_sma_50.json().get("Technical Analysis: SMA", {})
            sma_200_data = response_sma_200.json().get("Technical Analysis: SMA", {})
            rsi_data = response_rsi.json().get("Technical Analysis: RSI", {})
            macd_data = response_macd.json().get("Technical Analysis: MACD", {})
            bbands_data = response_bbands.json().get("Technical Analysis: BBANDS", {})
            
            # Get latest data points
            latest_date_sma_50 = sorted(sma_50_data.keys(), reverse=True)[0] if sma_50_data else None
            latest_date_sma_200 = sorted(sma_200_data.keys(), reverse=True)[0] if sma_200_data else None
            latest_date_rsi = sorted(rsi_data.keys(), reverse=True)[0] if rsi_data else None
            latest_date_macd = sorted(macd_data.keys(), reverse=True)[0] if macd_data else None
            latest_date_bbands = sorted(bbands_data.keys(), reverse=True)[0] if bbands_data else None
            
            # Calculate indicator values
            sma_50 = float(sma_50_data[latest_date_sma_50]["SMA"]) if latest_date_sma_50 else None
            sma_200 = float(sma_200_data[latest_date_sma_200]["SMA"]) if latest_date_sma_200 else None
            rsi = float(rsi_data[latest_date_rsi]["RSI"]) if latest_date_rsi else None
            
            macd_value = None
            macd_signal = None
            macd_hist = None
            if latest_date_macd:
                macd_value = float(macd_data[latest_date_macd]["MACD"])
                macd_signal = float(macd_data[latest_date_macd]["MACD_Signal"])
                macd_hist = float(macd_data[latest_date_macd]["MACD_Hist"])
            
            bbands_upper = None
            bbands_middle = None
            bbands_lower = None
            if latest_date_bbands:
                bbands_upper = float(bbands_data[latest_date_bbands]["Real Upper Band"])
                bbands_middle = float(bbands_data[latest_date_bbands]["Real Middle Band"])
                bbands_lower = float(bbands_data[latest_date_bbands]["Real Lower Band"])
            
            # Analyze data
            trend = "neutral"
            if sma_50 is not None and sma_200 is not None:
                if sma_50 > sma_200 * 1.05:  # 5% above 200-day SMA
                    trend = "strong_bullish"
                elif sma_50 > sma_200:
                    trend = "bullish"
                elif sma_50 < sma_200 * 0.95:  # 5% below 200-day SMA
                    trend = "strong_bearish"
                elif sma_50 < sma_200:
                    trend = "bearish"
            
            momentum = "neutral"
            if rsi is not None:
                if rsi > 70:
                    momentum = "overbought"
                elif rsi > 60:
                    momentum = "bullish"
                elif rsi < 30:
                    momentum = "oversold"
                elif rsi < 40:
                    momentum = "bearish"
            
            volatility = "medium"
            if bbands_upper is not None and bbands_lower is not None and bbands_middle is not None:
                band_width = (bbands_upper - bbands_lower) / bbands_middle
                if band_width > 0.1:  # 10% width relative to price
                    volatility = "high"
                elif band_width < 0.05:  # 5% width relative to price
                    volatility = "low"
            
            # Calculate signal strength (0-1)
            strength = 0.5  # Default neutral
            if rsi is not None:
                # Scale RSI from 0-100 to 0-1
                rsi_strength = rsi / 100
                
                # Adjust for extremes (more meaningful around extremes)
                if rsi > 70 or rsi < 30:
                    strength = rsi_strength
                else:
                    # More neutral in the middle range
                    strength = 0.4 + (rsi_strength * 0.2)
            
            # Adjust strength based on MACD histogram
            if macd_hist is not None:
                # Normalize MACD hist influence
                macd_influence = min(max(abs(macd_hist) / 2, 0), 0.2)  # Cap at ±0.2
                if macd_hist > 0:
                    strength = min(strength + macd_influence, 1.0)
                else:
                    strength = max(strength - macd_influence, 0.0)
            
            return {
                "trend": trend,
                "momentum": momentum, 
                "volatility": volatility,
                "strength": strength,
                "rsi": rsi,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "macd_hist": macd_hist,
                "bbands_upper": bbands_upper,
                "bbands_middle": bbands_middle,
                "bbands_lower": bbands_lower,
                "vix": vix_value
            }
            
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {str(e)}")
            return None
     
    def _assess_overall_market(self, analyses):
        """
        Assess overall market conditions based on individual symbol analyses
        
        Args:
            analyses (list): List of symbol analyses
            
        Returns:
            dict: Overall market assessment
        """
        if not analyses:
            return {"trend": "neutral", "strength": 0.5, "volatility": "medium", "momentum": "neutral"}
        
        # Count trend distributions
        trend_counts = {"strong_bullish": 0, "bullish": 0, "neutral": 0, "bearish": 0, "strong_bearish": 0}
        volatility_counts = {"low": 0, "medium": 0, "high": 0}
        momentum_counts = {"overbought": 0, "bullish": 0, "neutral": 0, "bearish": 0, "oversold": 0}
        
        total_strength = 0
        vix_values = []
        
        for analysis in analyses:
            if "trend" in analysis:
                trend_counts[analysis["trend"]] += 1
            
            if "volatility" in analysis:
                volatility_counts[analysis["volatility"]] += 1
            
            if "momentum" in analysis:
                momentum_counts[analysis["momentum"]] += 1
            
            if "strength" in analysis:
                total_strength += analysis["strength"]
            
            if "vix" in analysis and analysis["vix"] is not None:
                vix_values.append(analysis["vix"])
        
        # Determine overall trend
        bullish_count = trend_counts["strong_bullish"] + trend_counts["bullish"]
        bearish_count = trend_counts["strong_bearish"] + trend_counts["bearish"]
        
        if bullish_count > len(analyses) * 0.6:  # 60% or more bullish signals
            overall_trend = "bullish"
            if trend_counts["strong_bullish"] > trend_counts["bullish"]:
                overall_trend = "strong_bullish"
        elif bearish_count > len(analyses) * 0.6:  # 60% or more bearish signals
            overall_trend = "bearish"
            if trend_counts["strong_bearish"] > trend_counts["bearish"]:
                overall_trend = "strong_bearish"
        else:
            overall_trend = "neutral"
        
        # Determine overall volatility
        if volatility_counts["high"] > len(analyses) * 0.5:
            overall_volatility = "high"
        elif volatility_counts["low"] > len(analyses) * 0.5:
            overall_volatility = "low"
        else:
            overall_volatility = "medium"
        
        # Determine overall momentum
        bullish_momentum = momentum_counts["overbought"] + momentum_counts["bullish"]
        bearish_momentum = momentum_counts["oversold"] + momentum_counts["bearish"]
        
        if bullish_momentum > len(analyses) * 0.6:
            overall_momentum = "bullish"
            if momentum_counts["overbought"] > momentum_counts["bullish"]:
                overall_momentum = "overbought"
        elif bearish_momentum > len(analyses) * 0.6:
            overall_momentum = "bearish"
            if momentum_counts["oversold"] > momentum_counts["bearish"]:
                overall_momentum = "oversold"
        else:
            overall_momentum = "neutral"
        
        # Calculate average strength
        average_strength = total_strength / len(analyses) if analyses else 0.5
        
        # Incorporate VIX for fear assessment
        fear_level = "normal"
        if vix_values:
            avg_vix = sum(vix_values) / len(vix_values)
            if avg_vix > 30:
                fear_level = "extreme"
                # Adjust strength for high VIX (market fear)
                average_strength = max(average_strength - 0.2, 0)
            elif avg_vix > 20:
                fear_level = "elevated"
                average_strength = max(average_strength - 0.1, 0)
        
        return {
            "trend": overall_trend,
            "strength": average_strength,
            "volatility": overall_volatility,
            "momentum": overall_momentum,
            "fear_level": fear_level,
            "vix_average": sum(vix_values) / len(vix_values) if vix_values else None
        }

    def prioritize_backtests(self, symbols=None, strategies=None):
        """
        Prioritize backtests based on market conditions and strategy characteristics
        
        Args:
            symbols (list): List of symbols to prioritize (defaults to watchlist)
            strategies (list): List of strategies to evaluate (defaults to all available)
            
        Returns:
            list: Prioritized list of (symbol, strategy) tuples
        """
        if symbols is None:
            symbols = self.watchlist
            
        if strategies is None:
            strategies = self.get_available_strategies()
            
        logger.info(f"Prioritizing backtests for {len(symbols)} symbols and {len(strategies)} strategies")
        
        # Analyze current market conditions
        market_conditions = self.analyze_market_conditions(["SPY", "QQQ"])
        overall_market = market_conditions.get("overall", {})
        
        # Create all symbol-strategy combinations
        combinations = [(symbol, strategy) for symbol in symbols for strategy in strategies]
        
        # Score each combination based on market conditions and strategy characteristics
        scored_combinations = []
        
        for symbol, strategy in combinations:
            score = 0
            
            # Base score - all combinations start with same priority
            score += 50
            
            # Score based on market trend
            market_trend = overall_market.get("trend", "neutral")
            if market_trend == "bullish" or market_trend == "strong_bullish":
                if strategy == "Trend Following":
                    score += 20  # Trend following does well in bullish markets
                elif strategy == "Mean Reversion":
                    score -= 10  # Mean reversion might not be optimal in strong trends
            elif market_trend == "bearish" or market_trend == "strong_bearish":
                if strategy == "Mean Reversion":
                    score += 15  # Mean reversion can work in bearish markets with bounces
                elif strategy == "Momentum":
                    score -= 10  # Momentum might struggle in bearish markets
            
            # Score based on volatility
            volatility = overall_market.get("volatility", "medium")
            if volatility == "high":
                if strategy == "Mean Reversion":
                    score += 20  # Mean reversion works well in high volatility
                elif strategy == "Trend Following":
                    score -= 5  # Trend following can get whipsawed in high volatility
            elif volatility == "low":
                if strategy == "Trend Following":
                    score += 15  # Trend following works well in low volatility trending markets
                elif strategy == "Mean Reversion":
                    score -= 10  # Mean reversion needs volatility to work well
            
            # Score based on momentum
            momentum = overall_market.get("momentum", "neutral")
            if momentum == "bullish" or momentum == "overbought":
                if strategy == "Momentum":
                    score += 25  # Momentum strategies work best with strong momentum
            elif momentum == "bearish" or momentum == "oversold":
                if strategy == "Momentum":
                    score -= 15  # Momentum strategies struggle with weak momentum
            
            # Add custom logic for individual symbol indicators
            # Get symbol-specific analysis if available in market_conditions
            symbol_analysis = next((a for a in market_conditions.get("analyses", []) if a.get("symbol") == symbol), None)
            
            if symbol_analysis:
                # Score based on RSI 
                rsi_value = symbol_analysis.get("rsi")
                if rsi_value is not None:
                    if rsi_value < 30 and strategy == "Mean Reversion":
                        score += 25  # Oversold conditions favor mean reversion strategies
                    elif rsi_value > 70 and strategy == "Mean Reversion":
                        score += 20  # Overbought conditions also favor mean reversion (for shorts)
                    elif 40 <= rsi_value <= 60 and strategy == "Trend Following":
                        score += 15  # Neutral RSI in middle range can indicate steady trend
            
            # Add VIX influence
            fear_level = overall_market.get("fear_level", "normal")
            if fear_level == "extreme":  # High fear
                if strategy == "Mean Reversion":
                    score += 20  # High VIX often precedes bounces
            elif fear_level == "normal":  # Low fear
                if strategy == "Trend Following":
                    score += 15  # Low VIX often accompanies steady trends
            
            scored_combinations.append((symbol, strategy, score))
        
        # Sort by score in descending order
        scored_combinations.sort(key=lambda x: x[2], reverse=True)
        
        # Return prioritized list without scores
        return [(symbol, strategy) for symbol, strategy, _ in scored_combinations]
        
    def get_available_strategies(self):
        """
        Get list of available backtesting strategies
        
        Returns:
            list: Available strategy names
        """
        # This would typically scan strategy directory or database
        # For now, return hardcoded list of example strategies
        return [
            "Trend Following",
            "Mean Reversion", 
            "Momentum",
            "Breakout",
            "Moving Average Crossover",
            "RSI Strategy",
            "MACD Strategy",
            "Bollinger Band Strategy"
        ]
        
    def schedule_backtests(self, max_concurrent=3, schedule_interval_hours=24):
        """
        Schedule backtests based on prioritization
        
        Args:
            max_concurrent (int): Maximum number of concurrent backtests to run
            schedule_interval_hours (int): How often to re-prioritize and schedule
            
        Returns:
            bool: Success status
        """
        logger.info(f"Scheduling backtests with max_concurrent={max_concurrent}")
        
        try:
            # Get prioritized list of backtests
            prioritized_backtests = self.prioritize_backtests()
            
            if not prioritized_backtests:
                logger.warning("No backtests to schedule")
                return False
                
            logger.info(f"Found {len(prioritized_backtests)} prioritized backtests")
            
            # Take top N based on max_concurrent
            scheduled_backtests = prioritized_backtests[:max_concurrent]
            
            # Here you would integrate with your backtesting system
            # This is a placeholder for the actual integration
            for symbol, strategy in scheduled_backtests:
                logger.info(f"Scheduling backtest for {symbol} with {strategy} strategy")
                
                # Example of how you might call your backtester
                # self.backtest_client.submit_job(
                #     symbol=symbol,
                #     strategy=strategy,
                #     start_date=datetime.now() - timedelta(days=365),
                #     end_date=datetime.now(),
                #     priority="high"
                # )
                
                # For demonstration, we'll just log that we would schedule it
                logger.info(f"Would execute: backtest_client.submit_job(symbol={symbol}, strategy={strategy})")
            
            # Schedule next run
            logger.info(f"Scheduling next backtest prioritization in {schedule_interval_hours} hours")
            # In a real system, you would use a task scheduler like Celery or APScheduler
            # scheduler.add_job(self.schedule_backtests, 'interval', hours=schedule_interval_hours)
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling backtests: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create scheduler
    scheduler = BacktestScheduler(
        data_client=None,  # Would connect to your data client in production
        market_analyzer=None  # Would connect to your market analyzer in production
    )
    
    # Print available strategies
    strategies = scheduler.get_available_strategies()
    logger.info(f"Available strategies: {strategies}")
    
    # Get prioritized backtests for specific symbols and strategies
    sample_symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
    sample_strategies = ["Momentum", "Mean Reversion", "RSI Strategy"]
    
    prioritized = scheduler.prioritize_backtests(
        symbols=sample_symbols,
        strategies=sample_strategies
    )
    
    logger.info("Prioritized backtests (symbol, strategy):")
    for i, (symbol, strategy) in enumerate(prioritized):
        logger.info(f"{i+1}. {symbol} - {strategy}")
    
    # Schedule backtests with default parameters
    scheduler.schedule_backtests(max_concurrent=2) 