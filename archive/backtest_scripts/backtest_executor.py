import logging
import time
import threading
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class BacktestExecutor:
    """
    Handles the execution of backtests for different trading strategies.
    Works in conjunction with the BacktestScheduler to run prioritized backtests.
    """
    
    def __init__(self, data_client=None):
        """
        Initialize the BacktestExecutor.
        
        Args:
            data_client: Data client for fetching market data (optional)
        """
        self.data_client = data_client
        self.running_backtests = {}
        self.completed_backtests = []
        self.backtest_results = {}
        self.lock = threading.Lock()
        
    def execute_backtest(self, symbol: str, strategy: str, params: Dict[str, Any] = None) -> str:
        """
        Execute a backtest for a specific symbol and strategy.
        
        Args:
            symbol: The trading symbol (e.g., "AAPL")
            strategy: The strategy name to backtest
            params: Additional parameters for the backtest
            
        Returns:
            backtest_id: Unique identifier for the backtest
        """
        backtest_id = f"{symbol}_{strategy}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        logger.info(f"Starting backtest {backtest_id} for {symbol} using {strategy} strategy")
        
        # In a real implementation, this would be a more sophisticated process
        # that loads historical data and runs the strategy against it
        
        with self.lock:
            self.running_backtests[backtest_id] = {
                "symbol": symbol,
                "strategy": strategy,
                "params": params or {},
                "start_time": datetime.now(),
                "status": "running"
            }
        
        # Start the backtest in a separate thread
        thread = threading.Thread(target=self._run_backtest, args=(backtest_id,))
        thread.start()
        
        return backtest_id
    
    def _run_backtest(self, backtest_id: str) -> None:
        """
        Internal method to run the backtest simulation.
        
        Args:
            backtest_id: The unique identifier for the backtest
        """
        try:
            # Get backtest details
            backtest = self.running_backtests[backtest_id]
            symbol = backtest["symbol"]
            strategy = backtest["strategy"]
            
            # Simulate backtest duration (3-10 seconds)
            execution_time = random.uniform(3, 10)
            time.sleep(execution_time)
            
            # Generate simulated results
            pnl = random.uniform(-5, 15)
            trades = random.randint(20, 200)
            win_rate = random.uniform(0.4, 0.7)
            sharpe = random.uniform(-0.5, 2.5)
            max_drawdown = random.uniform(-20, -5)
            
            results = {
                "backtest_id": backtest_id,
                "symbol": symbol,
                "strategy": strategy,
                "execution_time": execution_time,
                "pnl_percent": pnl,
                "total_trades": trades,
                "win_rate": win_rate,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_drawdown,
                "completion_time": datetime.now()
            }
            
            logger.info(f"Completed backtest {backtest_id} for {symbol} using {strategy} strategy. "
                        f"PnL: {pnl:.2f}%, Sharpe: {sharpe:.2f}")
            
            with self.lock:
                self.running_backtests[backtest_id]["status"] = "completed"
                self.completed_backtests.append(backtest_id)
                self.backtest_results[backtest_id] = results
                
        except Exception as e:
            logger.error(f"Error executing backtest {backtest_id}: {str(e)}")
            with self.lock:
                if backtest_id in self.running_backtests:
                    self.running_backtests[backtest_id]["status"] = "failed"
                    self.running_backtests[backtest_id]["error"] = str(e)
    
    def get_results(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the results of a completed backtest.
        
        Args:
            backtest_id: The unique identifier for the backtest
            
        Returns:
            The backtest results or None if not found
        """
        return self.backtest_results.get(backtest_id)
    
    def get_active_backtest_count(self) -> int:
        """
        Get the number of currently active backtests.
        
        Returns:
            The count of active backtests
        """
        return sum(1 for bt in self.running_backtests.values() if bt["status"] == "running")
    
    def get_all_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get results for all completed backtests.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of backtest result dictionaries
        """
        results = list(self.backtest_results.values())
        results.sort(key=lambda x: x.get("completion_time", datetime.min), reverse=True)
        return results[:limit]


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create executor
    executor = BacktestExecutor()
    
    # Run a few sample backtests
    backtest_ids = []
    for symbol in ["AAPL", "MSFT", "GOOGL"]:
        for strategy in ["Momentum", "Mean Reversion"]:
            backtest_id = executor.execute_backtest(symbol, strategy)
            backtest_ids.append(backtest_id)
    
    # Wait for all backtests to complete
    time.sleep(15)
    
    # Print results
    logger.info("Backtest Results:")
    for backtest_id in backtest_ids:
        result = executor.get_results(backtest_id)
        if result:
            logger.info(f"{result['symbol']} - {result['strategy']}: "
                       f"PnL: {result['pnl_percent']:.2f}%, "
                       f"Sharpe: {result['sharpe_ratio']:.2f}, "
                       f"Win Rate: {result['win_rate']:.2f}") 