import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest_visualizer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BacktestVisualizer:
    """
    Visualizes and analyzes backtest results from BacktestExecutor and BacktestIntegration
    """
    
    def __init__(self, results_dir="data/results"):
        """
        Initialize the BacktestVisualizer.
        
        Args:
            results_dir (str): Directory containing backtest results
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        
    def load_results(self, backtest_id=None, strategy=None, symbol=None):
        """
        Load backtest results from the results directory.
        
        Args:
            backtest_id (str): Specific backtest ID to load
            strategy (str): Filter results by strategy
            symbol (str): Filter results by symbol
            
        Returns:
            list: Loaded backtest results
        """
        results = []
        
        try:
            # If specific backtest_id is provided, load just that result
            if backtest_id:
                result_file = os.path.join(self.results_dir, f"{backtest_id}.json")
                if os.path.exists(result_file):
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        results.append(result)
                        logger.info(f"Loaded result for backtest ID: {backtest_id}")
                else:
                    logger.warning(f"No result file found for backtest ID: {backtest_id}")
                return results
            
            # Load all results and filter as needed
            for filename in os.listdir(self.results_dir):
                if filename.endswith('.json'):
                    result_file = os.path.join(self.results_dir, filename)
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        
                        # Apply filters if provided
                        if strategy and result.get('strategy') != strategy:
                            continue
                        if symbol and result.get('symbol') != symbol:
                            continue
                            
                        results.append(result)
            
            logger.info(f"Loaded {len(results)} backtest results")
            
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
        return results
    
    def save_results(self, results, integration_run=None):
        """
        Save backtest results to the results directory.
        
        Args:
            results (list or dict): Results to save
            integration_run (str): Optional identifier for the integration run
            
        Returns:
            int: Number of results saved
        """
        try:
            # Handle both single result or list of results
            if not isinstance(results, list):
                if isinstance(results, dict) and "results" in results:
                    # Handle integration result format
                    results_to_save = results["results"]
                else:
                    # Handle single result
                    results_to_save = [results]
            else:
                results_to_save = results
                
            # Create timestamp for this save batch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save each result to a file
            count = 0
            for result in results_to_save:
                if not result:
                    continue
                    
                backtest_id = result.get("backtest_id")
                if not backtest_id:
                    # Generate a backtest ID if none exists
                    symbol = result.get("symbol", "UNKNOWN")
                    strategy = result.get("strategy", "UNKNOWN")
                    backtest_id = f"{symbol}_{strategy}_{timestamp}_{count}"
                    result["backtest_id"] = backtest_id
                
                # Save to file
                result_file = os.path.join(self.results_dir, f"{backtest_id}.json")
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)
                    
                count += 1
                
            # If this is an integration run, save the summary separately
            if integration_run and isinstance(results, dict) and "stats" in results:
                summary_file = os.path.join(
                    self.results_dir, 
                    f"summary_{integration_run}_{timestamp}.json"
                )
                with open(summary_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
            logger.info(f"Saved {count} backtest results")
            return count
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def plot_performance_by_strategy(self, results=None, metric="pnl_percent", 
                                    sort=True, save_path=None):
        """
        Plot performance metrics by strategy.
        
        Args:
            results (list): Backtest results to visualize
            metric (str): Performance metric to plot
            sort (bool): Whether to sort results
            save_path (str): Path to save the plot
        """
        try:
            # Load results if not provided
            if results is None:
                results = self.load_results()
                
            if not results:
                logger.warning("No results to plot")
                return
            
            # Extract data for plotting
            strategy_data = {}
            
            for result in results:
                strategy = result.get("strategy")
                if not strategy:
                    continue
                    
                value = result.get(metric)
                if value is None:
                    continue
                    
                if strategy not in strategy_data:
                    strategy_data[strategy] = []
                    
                strategy_data[strategy].append(value)
            
            # Calculate statistics
            strategy_stats = {}
            for strategy, values in strategy_data.items():
                strategy_stats[strategy] = {
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "count": len(values)
                }
            
            # Sort by mean performance if requested
            if sort:
                strategies = sorted(
                    strategy_stats.keys(), 
                    key=lambda x: strategy_stats[x]["mean"],
                    reverse=True
                )
            else:
                strategies = list(strategy_stats.keys())
            
            # Prepare plot data
            means = [strategy_stats[s]["mean"] for s in strategies]
            stds = [strategy_stats[s]["std"] for s in strategies]
            counts = [strategy_stats[s]["count"] for s in strategies]
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Create bar chart with error bars
            bars = plt.bar(strategies, means, yerr=stds, capsize=5, 
                          alpha=0.7, color='skyblue')
            
            # Add labels and title
            plt.xlabel('Strategy')
            plt.ylabel(f'{metric.replace("_", " ").title()}')
            plt.title(f'Performance by Strategy ({metric})')
            
            # Add value labels on top of bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + stds[i] + 0.1,
                        f'{means[i]:.2f}', ha='center', va='bottom', rotation=0)
                
                # Add count at the bottom of each bar
                plt.text(bar.get_x() + bar.get_width()/2., 0,
                        f'n={counts[i]}', ha='center', va='bottom', rotation=90)
            
            # Adjust layout
            plt.tight_layout()
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved plot to {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting performance by strategy: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def plot_performance_by_symbol(self, results=None, metric="pnl_percent", 
                                 top_n=10, save_path=None):
        """
        Plot performance metrics by symbol.
        
        Args:
            results (list): Backtest results to visualize
            metric (str): Performance metric to plot
            top_n (int): Number of top symbols to show
            save_path (str): Path to save the plot
        """
        try:
            # Load results if not provided
            if results is None:
                results = self.load_results()
                
            if not results:
                logger.warning("No results to plot")
                return
            
            # Extract data for plotting
            symbol_data = {}
            
            for result in results:
                symbol = result.get("symbol")
                if not symbol:
                    continue
                    
                value = result.get(metric)
                if value is None:
                    continue
                    
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                    
                symbol_data[symbol].append(value)
            
            # Calculate statistics
            symbol_stats = {}
            for symbol, values in symbol_data.items():
                symbol_stats[symbol] = {
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "count": len(values)
                }
            
            # Sort by mean performance and get top N
            symbols = sorted(
                symbol_stats.keys(), 
                key=lambda x: symbol_stats[x]["mean"],
                reverse=True
            )[:top_n]
            
            # Prepare plot data
            means = [symbol_stats[s]["mean"] for s in symbols]
            stds = [symbol_stats[s]["std"] for s in symbols]
            counts = [symbol_stats[s]["count"] for s in symbols]
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Create bar chart with error bars
            bars = plt.bar(symbols, means, yerr=stds, capsize=5, 
                          alpha=0.7, color='lightgreen')
            
            # Add labels and title
            plt.xlabel('Symbol')
            plt.ylabel(f'{metric.replace("_", " ").title()}')
            plt.title(f'Top {top_n} Symbols by {metric}')
            
            # Add value labels on top of bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + stds[i] + 0.1,
                        f'{means[i]:.2f}', ha='center', va='bottom', rotation=0)
                
                # Add count at the bottom of each bar
                plt.text(bar.get_x() + bar.get_width()/2., 0,
                        f'n={counts[i]}', ha='center', va='bottom', rotation=90)
            
            # Adjust layout
            plt.tight_layout()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved plot to {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting performance by symbol: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def plot_correlation_matrix(self, results=None, metrics=None, save_path=None):
        """
        Plot correlation matrix between different performance metrics.
        
        Args:
            results (list): Backtest results to visualize
            metrics (list): Performance metrics to include
            save_path (str): Path to save the plot
        """
        try:
            # Load results if not provided
            if results is None:
                results = self.load_results()
                
            if not results:
                logger.warning("No results to plot")
                return
            
            # Default metrics if not provided
            if metrics is None:
                metrics = ["pnl_percent", "sharpe_ratio", "win_rate", "max_drawdown"]
            
            # Extract data into a DataFrame
            data = []
            for result in results:
                row = {}
                for metric in metrics:
                    row[metric] = result.get(metric)
                
                # Only add rows that have all metrics
                if all(v is not None for v in row.values()):
                    data.append(row)
            
            if not data:
                logger.warning("No complete results with all metrics")
                return
                
            df = pd.DataFrame(data)
            
            # Calculate correlation matrix
            corr = df.corr()
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Create heatmap
            cmap = plt.cm.RdBu_r
            plt.imshow(corr, cmap=cmap, vmin=-1, vmax=1)
            plt.colorbar(label='Correlation')
            
            # Add labels
            plt.xticks(range(len(metrics)), [m.replace("_", " ").title() for m in metrics], 
                      rotation=45, ha='right')
            plt.yticks(range(len(metrics)), [m.replace("_", " ").title() for m in metrics])
            
            # Add correlation values in each cell
            for i in range(len(metrics)):
                for j in range(len(metrics)):
                    plt.text(j, i, f'{corr.iloc[i, j]:.2f}', 
                           ha='center', va='center', color='black' if abs(corr.iloc[i, j]) < 0.7 else 'white')
            
            plt.title('Correlation Matrix of Performance Metrics')
            plt.tight_layout()
            
            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved correlation matrix to {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting correlation matrix: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def plot_parameter_sensitivity(self, results=None, parameter=None, metric="sharpe_ratio", 
                                 strategy=None, save_path=None):
        """
        Plot sensitivity of results to a specific parameter.
        
        Args:
            results (list): Backtest results to visualize
            parameter (str): Parameter to analyze
            metric (str): Performance metric to plot
            strategy (str): Filter by strategy
            save_path (str): Path to save the plot
        """
        try:
            # Load results if not provided
            if results is None:
                results = self.load_results(strategy=strategy)
                
            if not results:
                logger.warning("No results to plot")
                return
                
            if parameter is None:
                logger.warning("No parameter specified")
                return
            
            # Extract data points for the parameter and metric
            data_points = []
            for result in results:
                # Skip if strategy filter doesn't match
                if strategy and result.get("strategy") != strategy:
                    continue
                    
                # Extract parameter value
                params = result.get("params", {})
                param_value = params.get(parameter)
                
                if param_value is None:
                    continue
                    
                # Extract metric value
                metric_value = result.get(metric)
                if metric_value is None:
                    continue
                    
                data_points.append((param_value, metric_value))
            
            if not data_points:
                logger.warning(f"No data points found for parameter '{parameter}' and metric '{metric}'")
                return
                
            # Sort by parameter value
            data_points.sort(key=lambda x: x[0])
            
            # Extract x and y values
            x_values = [p[0] for p in data_points]
            y_values = [p[1] for p in data_points]
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Create scatter plot
            plt.scatter(x_values, y_values, alpha=0.7, s=50, color='purple')
            
            # Try to fit a trend line
            try:
                z = np.polyfit(x_values, y_values, 1)
                p = np.poly1d(z)
                plt.plot(x_values, p(x_values), "r--", alpha=0.8, 
                       label=f"Trend: y={z[0]:.4f}x+{z[1]:.4f}")
                plt.legend()
            except:
                pass
            
            # Add labels and title
            plt.xlabel(f'{parameter.replace("_", " ").title()}')
            plt.ylabel(f'{metric.replace("_", " ").title()}')
            
            strategy_text = f" for {strategy}" if strategy else ""
            plt.title(f'Sensitivity of {metric.replace("_", " ").title()} to {parameter.replace("_", " ").title()}{strategy_text}')
            
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved sensitivity plot to {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting parameter sensitivity: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def generate_summary_report(self, results=None, output_file=None):
        """
        Generate a comprehensive summary report of backtest results.
        
        Args:
            results (list): Backtest results to analyze
            output_file (str): File to save the report
            
        Returns:
            dict: Summary statistics
        """
        try:
            # Load results if not provided
            if results is None:
                results = self.load_results()
                
            if not results:
                logger.warning("No results to analyze")
                return {}
            
            # Initialize summary statistics
            summary = {
                "total_backtests": len(results),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "strategies": {},
                "symbols": {},
                "overall": {}
            }
            
            # Extract metrics
            pnls = []
            sharpes = []
            win_rates = []
            drawdowns = []
            
            # Process each result
            for result in results:
                strategy = result.get("strategy", "Unknown")
                symbol = result.get("symbol", "Unknown")
                
                # Initialize strategy and symbol entries if they don't exist
                if strategy not in summary["strategies"]:
                    summary["strategies"][strategy] = {
                        "count": 0,
                        "pnl_total": 0,
                        "pnl_avg": 0,
                        "sharpe_avg": 0,
                        "win_rate_avg": 0,
                        "drawdown_avg": 0
                    }
                    
                if symbol not in summary["symbols"]:
                    summary["symbols"][symbol] = {
                        "count": 0,
                        "pnl_total": 0,
                        "pnl_avg": 0,
                        "sharpe_avg": 0,
                        "win_rate_avg": 0,
                        "drawdown_avg": 0
                    }
                
                # Extract metrics
                pnl = result.get("pnl_percent", 0)
                sharpe = result.get("sharpe_ratio", 0)
                win_rate = result.get("win_rate", 0)
                drawdown = result.get("max_drawdown", 0)
                
                # Add to overall lists
                pnls.append(pnl)
                sharpes.append(sharpe)
                win_rates.append(win_rate)
                drawdowns.append(drawdown)
                
                # Update strategy statistics
                strategy_stats = summary["strategies"][strategy]
                strategy_stats["count"] += 1
                strategy_stats["pnl_total"] += pnl
                
                # Update symbol statistics
                symbol_stats = summary["symbols"][symbol]
                symbol_stats["count"] += 1
                symbol_stats["pnl_total"] += pnl
            
            # Calculate averages for strategies
            for strategy, stats in summary["strategies"].items():
                count = stats["count"]
                if count > 0:
                    strategy_results = [r for r in results if r.get("strategy") == strategy]
                    stats["pnl_avg"] = stats["pnl_total"] / count
                    stats["sharpe_avg"] = sum(r.get("sharpe_ratio", 0) for r in strategy_results) / count
                    stats["win_rate_avg"] = sum(r.get("win_rate", 0) for r in strategy_results) / count
                    stats["drawdown_avg"] = sum(r.get("max_drawdown", 0) for r in strategy_results) / count
                    stats["profitable_pct"] = len([r for r in strategy_results if r.get("pnl_percent", 0) > 0]) / count * 100
            
            # Calculate averages for symbols
            for symbol, stats in summary["symbols"].items():
                count = stats["count"]
                if count > 0:
                    symbol_results = [r for r in results if r.get("symbol") == symbol]
                    stats["pnl_avg"] = stats["pnl_total"] / count
                    stats["sharpe_avg"] = sum(r.get("sharpe_ratio", 0) for r in symbol_results) / count
                    stats["win_rate_avg"] = sum(r.get("win_rate", 0) for r in symbol_results) / count
                    stats["drawdown_avg"] = sum(r.get("max_drawdown", 0) for r in symbol_results) / count
                    stats["profitable_pct"] = len([r for r in symbol_results if r.get("pnl_percent", 0) > 0]) / count * 100
            
            # Calculate overall statistics
            count = len(results)
            if count > 0:
                summary["overall"] = {
                    "pnl_avg": sum(pnls) / count,
                    "pnl_median": np.median(pnls),
                    "pnl_std": np.std(pnls),
                    "pnl_min": min(pnls),
                    "pnl_max": max(pnls),
                    "sharpe_avg": sum(sharpes) / count,
                    "win_rate_avg": sum(win_rates) / count,
                    "drawdown_avg": sum(drawdowns) / count,
                    "profitable_pct": len([p for p in pnls if p > 0]) / count * 100
                }
            
            # Find best and worst performers
            if results:
                # Best strategy by PnL
                best_strategy = max(summary["strategies"].items(), 
                                  key=lambda x: x[1]["pnl_avg"])
                summary["best_strategy"] = {
                    "name": best_strategy[0],
                    "pnl_avg": best_strategy[1]["pnl_avg"],
                    "count": best_strategy[1]["count"]
                }
                
                # Best symbol by PnL
                best_symbol = max(summary["symbols"].items(), 
                                key=lambda x: x[1]["pnl_avg"])
                summary["best_symbol"] = {
                    "name": best_symbol[0],
                    "pnl_avg": best_symbol[1]["pnl_avg"],
                    "count": best_symbol[1]["count"]
                }
                
                # Best individual backtest
                best_backtest = max(results, key=lambda x: x.get("pnl_percent", 0))
                summary["best_backtest"] = {
                    "symbol": best_backtest.get("symbol"),
                    "strategy": best_backtest.get("strategy"),
                    "pnl": best_backtest.get("pnl_percent"),
                    "sharpe": best_backtest.get("sharpe_ratio"),
                    "win_rate": best_backtest.get("win_rate")
                }
            
            # Save report to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                logger.info(f"Saved summary report to {output_file}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {}


# Example usage
if __name__ == "__main__":
    # Create a visualizer
    visualizer = BacktestVisualizer()
    
    # Generate some sample results for demonstration
    from backtest_executor import BacktestExecutor
    
    # Create an executor and run some backtests
    executor = BacktestExecutor()
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    strategies = ["Momentum", "Mean Reversion", "Trend Following", "Breakout"]
    
    # Run backtests
    print("Running sample backtests...")
    results = []
    
    for symbol in symbols:
        for strategy in strategies:
            backtest_id = executor.execute_backtest(symbol, strategy)
            # Wait for backtest to complete
            import time
            time.sleep(0.5)
            # Get result
            result = executor.get_results(backtest_id)
            if result:
                results.append(result)
    
    # Save results
    print(f"Saving {len(results)} backtest results...")
    visualizer.save_results(results)
    
    # Generate visualizations
    print("Generating visualizations...")
    
    # Plot performance by strategy
    visualizer.plot_performance_by_strategy(results, metric="pnl_percent", 
                                           save_path="strategy_performance.png")
    
    # Plot performance by symbol
    visualizer.plot_performance_by_symbol(results, metric="sharpe_ratio", 
                                        save_path="symbol_performance.png")
    
    # Plot correlation matrix
    visualizer.plot_correlation_matrix(results, 
                                     save_path="metric_correlation.png")
    
    # Generate summary report
    print("Generating summary report...")
    summary = visualizer.generate_summary_report(results, 
                                               output_file="backtest_summary.json")
    
    print("Visualization demo complete!") 