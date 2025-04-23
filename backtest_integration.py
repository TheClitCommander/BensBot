import logging
import time
import threading
import random
import os
from datetime import datetime

from backtest_scheduler import BacktestScheduler
from backtest_executor import BacktestExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest_integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BacktestIntegration:
    """
    Integrates the BacktestScheduler and BacktestExecutor to provide a complete
    backtest workflow from prioritization through execution and results analysis.
    """
    
    def __init__(self, data_dir="data", max_concurrent=2):
        """
        Initialize the BacktestIntegration.
        
        Args:
            data_dir (str): Directory to store data and results
            max_concurrent (int): Maximum number of concurrent backtests
        """
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "results"), exist_ok=True)
        
        # Initialize components
        logger.info("Initializing BacktestScheduler and BacktestExecutor")
        self.scheduler = BacktestScheduler(data_client=None, market_analyzer=None)
        self.executor = BacktestExecutor(data_client=None)
        
        # Configuration
        self.data_dir = data_dir
        self.max_concurrent = max_concurrent
        self.running = False
        self.backtest_results = {}
        self.lock = threading.Lock()
        
    def run_backtest_cycle(self, symbols=None, strategies=None, max_backtests=10):
        """
        Run a complete backtest cycle from prioritization through execution.
        
        Args:
            symbols (list): List of symbols to backtest (optional)
            strategies (list): List of strategies to backtest (optional)
            max_backtests (int): Maximum number of backtests to run
            
        Returns:
            dict: Summary of backtest results
        """
        try:
            # Start time for performance tracking
            start_time = datetime.now()
            logger.info(f"Starting backtest cycle at {start_time}")
            
            # If no symbols provided, use a default set
            if not symbols:
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
                         "JPM", "BAC", "V", "MA", "PFE"]
                logger.info(f"Using default symbols: {symbols}")
                
            # If no strategies provided, get available strategies
            if not strategies:
                strategies = self.scheduler.get_available_strategies()
                logger.info(f"Using available strategies: {strategies}")
            
            # Step 1: Prioritize backtests
            logger.info("Step 1: Prioritizing backtests...")
            prioritized_backtests = self.scheduler.prioritize_backtests(
                symbols=symbols, 
                strategies=strategies
            )
            
            logger.info(f"Prioritized {len(prioritized_backtests)} backtests")
            
            # Step 2: Select top N backtests based on priority
            selected_backtests = prioritized_backtests[:max_backtests]
            logger.info(f"Selected top {len(selected_backtests)} backtests for execution")
            
            # Step 3: Execute backtests
            logger.info("Step 3: Executing backtests...")
            executed_backtest_ids = []
            
            # Track active backtests
            active_backtests = 0
            backtest_queue = list(selected_backtests)
            all_backtest_ids = []
            
            # Process the queue until empty
            while backtest_queue or active_backtests > 0:
                # Start new backtests if we have capacity and backtests in queue
                while backtest_queue and active_backtests < self.max_concurrent:
                    backtest = backtest_queue.pop(0)
                    symbol = backtest.get("symbol")
                    strategy = backtest.get("strategy")
                    
                    logger.info(f"Starting backtest for {symbol} with {strategy} strategy")
                    backtest_id = self.executor.execute_backtest(symbol, strategy)
                    all_backtest_ids.append(backtest_id)
                    active_backtests += 1
                
                # Check status of running backtests
                active_backtests = self.executor.get_active_backtest_count()
                
                # Wait a bit before checking again
                time.sleep(0.5)
            
            # Step 4: Wait for all backtests to complete
            logger.info("Step 4: Waiting for all backtests to complete...")
            
            # Step 5: Collect and analyze results
            logger.info("Step 5: Collecting and analyzing results...")
            results = []
            
            for backtest_id in all_backtest_ids:
                result = self.executor.get_results(backtest_id)
                if result:
                    results.append(result)
                    logger.info(f"Result for {result['symbol']} - {result['strategy']}: "
                              f"PnL: {result['pnl_percent']:.2f}%, "
                              f"Sharpe: {result['sharpe_ratio']:.2f}")
            
            # Step 6: Generate summary
            execution_time = (datetime.now() - start_time).total_seconds()
            
            summary = {
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time_seconds": execution_time,
                "total_backtests": len(all_backtest_ids),
                "successful_backtests": len(results),
                "results": results
            }
            
            # Calculate aggregate statistics if we have results
            if results:
                pnls = [r["pnl_percent"] for r in results]
                sharpes = [r["sharpe_ratio"] for r in results]
                
                summary["stats"] = {
                    "avg_pnl": sum(pnls) / len(pnls),
                    "max_pnl": max(pnls),
                    "min_pnl": min(pnls),
                    "avg_sharpe": sum(sharpes) / len(sharpes),
                    "max_sharpe": max(sharpes),
                    "min_sharpe": min(sharpes),
                    "profitable_percentage": len([p for p in pnls if p > 0]) / len(pnls) * 100
                }
            
            logger.info(f"Backtest cycle completed in {execution_time:.2f} seconds")
            if "stats" in summary:
                stats = summary["stats"]
                logger.info(f"Average PnL: {stats['avg_pnl']:.2f}%, "
                          f"Average Sharpe: {stats['avg_sharpe']:.2f}, "
                          f"Profitable: {stats['profitable_percentage']:.1f}%")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in backtest cycle: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def find_best_strategies(self, symbols, test_all_strategies=True, top_n=3):
        """
        Find the best performing strategies for a list of symbols.
        
        Args:
            symbols (list): List of symbols to test
            test_all_strategies (bool): Whether to test all available strategies
            top_n (int): Number of top strategies to return per symbol
            
        Returns:
            dict: Symbol to best strategies mapping
        """
        try:
            logger.info(f"Finding best strategies for {len(symbols)} symbols")
            
            # Get all available strategies if requested
            if test_all_strategies:
                strategies = self.scheduler.get_available_strategies()
            else:
                # Use a subset of strategies for faster testing
                strategies = [
                    "Momentum", "Mean Reversion", "Trend Following", 
                    "Breakout", "Volatility Expansion"
                ]
                
            logger.info(f"Testing {len(strategies)} strategies: {strategies}")
            
            # Run a backtest cycle with all combinations
            max_backtests = len(symbols) * len(strategies)
            results = self.run_backtest_cycle(
                symbols=symbols,
                strategies=strategies,
                max_backtests=max_backtests
            )
            
            # Organize results by symbol
            symbol_results = {}
            for result in results.get("results", []):
                symbol = result["symbol"]
                if symbol not in symbol_results:
                    symbol_results[symbol] = []
                    
                symbol_results[symbol].append({
                    "strategy": result["strategy"],
                    "pnl_percent": result["pnl_percent"],
                    "sharpe_ratio": result["sharpe_ratio"],
                    "win_rate": result["win_rate"]
                })
            
            # Find top strategies for each symbol
            best_strategies = {}
            for symbol, strategies_results in symbol_results.items():
                # Sort by Sharpe ratio (could use PnL or a composite score)
                sorted_results = sorted(
                    strategies_results, 
                    key=lambda x: x["sharpe_ratio"], 
                    reverse=True
                )
                
                # Take top N strategies
                best_strategies[symbol] = sorted_results[:top_n]
                
                # Log results
                logger.info(f"Best strategies for {symbol}:")
                for i, strategy in enumerate(best_strategies[symbol]):
                    logger.info(f"  {i+1}. {strategy['strategy']}: Sharpe={strategy['sharpe_ratio']:.2f}, "
                              f"PnL={strategy['pnl_percent']:.2f}%, Win Rate={strategy['win_rate']:.2f}")
            
            return best_strategies
            
        except Exception as e:
            logger.error(f"Error finding best strategies: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
            
    def optimize_strategy_parameters(self, symbol, strategy, param_ranges=None, iterations=20):
        """
        Optimize parameters for a specific strategy and symbol.
        
        Args:
            symbol (str): Symbol to optimize for
            strategy (str): Strategy to optimize
            param_ranges (dict): Ranges for parameters to test
            iterations (int): Number of parameter combinations to test
            
        Returns:
            dict: Optimized parameters and results
        """
        try:
            logger.info(f"Optimizing parameters for {strategy} on {symbol}")
            
            # Default parameter ranges if none provided
            if not param_ranges:
                param_ranges = {
                    "lookback_period": (10, 60),
                    "exit_threshold": (0.02, 0.1),
                    "take_profit": (0.05, 0.3),
                    "stop_loss": (0.03, 0.15)
                }
                
                # Add strategy-specific parameters
                if strategy in ["Momentum", "Trend Following", "MACD Crossover"]:
                    param_ranges.update({
                        "fast_period": (5, 20),
                        "slow_period": (20, 50),
                        "signal_period": (5, 15)
                    })
                elif strategy in ["Mean Reversion", "Bollinger Band Squeeze"]:
                    param_ranges.update({
                        "std_dev": (1.5, 3.0),
                        "mean_period": (10, 30)
                    })
                elif strategy in ["Volatility Expansion", "Options Volatility Skew"]:
                    param_ranges.update({
                        "volatility_threshold": (0.1, 0.5),
                        "iv_percentile": (0.5, 0.9)
                    })
            
            logger.info(f"Testing {iterations} parameter combinations")
            
            # Generate parameter combinations
            parameter_sets = []
            for i in range(iterations):
                params = {}
                for param_name, (min_val, max_val) in param_ranges.items():
                    # Handle integer parameters
                    if param_name in ["lookback_period", "fast_period", "slow_period", 
                                    "signal_period", "mean_period"]:
                        params[param_name] = random.randint(min_val, max_val)
                    else:
                        params[param_name] = min_val + random.random() * (max_val - min_val)
                        # Round to 3 decimal places for readability
                        params[param_name] = round(params[param_name], 3)
                        
                parameter_sets.append(params)
            
            # Run backtests with each parameter set
            results = []
            for params in parameter_sets:
                # In a real implementation, this would pass the params to the backtest
                backtest_id = self.executor.execute_backtest(symbol, strategy, params)
                results.append({"backtest_id": backtest_id, "params": params})
            
            # Wait for all backtests to complete
            while self.executor.get_active_backtest_count() > 0:
                time.sleep(0.5)
            
            # Collect and analyze results
            optimization_results = []
            for entry in results:
                backtest_id = entry["backtest_id"]
                params = entry["params"]
                
                result = self.executor.get_results(backtest_id)
                if result:
                    optimization_results.append({
                        "params": params,
                        "pnl_percent": result["pnl_percent"],
                        "sharpe_ratio": result["sharpe_ratio"],
                        "win_rate": result["win_rate"],
                        "max_drawdown": result["max_drawdown"]
                    })
            
            # Sort by Sharpe ratio (could use other metrics or composite score)
            sorted_results = sorted(
                optimization_results, 
                key=lambda x: x["sharpe_ratio"], 
                reverse=True
            )
            
            # Log best results
            logger.info(f"Parameter optimization results for {strategy} on {symbol}:")
            for i, result in enumerate(sorted_results[:3]):
                logger.info(f"  {i+1}. Sharpe={result['sharpe_ratio']:.2f}, PnL={result['pnl_percent']:.2f}%, "
                          f"Win Rate={result['win_rate']:.2f}")
                logger.info(f"     Parameters: {result['params']}")
            
            # Return best parameters and all results
            return {
                "best_parameters": sorted_results[0]["params"] if sorted_results else None,
                "best_performance": {
                    "sharpe_ratio": sorted_results[0]["sharpe_ratio"],
                    "pnl_percent": sorted_results[0]["pnl_percent"],
                    "win_rate": sorted_results[0]["win_rate"],
                    "max_drawdown": sorted_results[0]["max_drawdown"]
                } if sorted_results else None,
                "all_results": sorted_results
            }
            
        except Exception as e:
            logger.error(f"Error optimizing strategy parameters: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Create the integration
    integration = BacktestIntegration(max_concurrent=3)
    
    # Run a simple backtest cycle
    print("Running backtest cycle...")
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    strategies = ["Momentum", "Mean Reversion", "Trend Following"]
    
    results = integration.run_backtest_cycle(
        symbols=symbols,
        strategies=strategies,
        max_backtests=10
    )
    
    # Find best strategies for a set of symbols
    print("\nFinding best strategies...")
    best_strategies = integration.find_best_strategies(
        symbols=["AAPL", "MSFT", "GOOGL"],
        test_all_strategies=False,
        top_n=2
    )
    
    # Optimize parameters for a specific strategy
    print("\nOptimizing strategy parameters...")
    optimization_results = integration.optimize_strategy_parameters(
        symbol="AAPL",
        strategy="Momentum",
        iterations=10
    )
    
    print("\nBacktest integration demo complete!") 