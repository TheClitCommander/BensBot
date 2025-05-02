#!/usr/bin/env python3
"""
Diagnostic Demo Backtester

This script demonstrates the enhanced backtester with all fixes applied.
It enables verbose debug mode and validates that trades are being properly executed.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("diagnostic_demo")
console = Console()

# Add parent directory to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import backtester components
try:
    from trading_bot.backtesting.unified_backtester import UnifiedBacktester
except ImportError:
    console.print("[bold red]Error importing UnifiedBacktester[/bold red]")
    console.print("Make sure you're running this script from the project root directory")
    console.print("Falling back to EnhancedBacktester...")
    try:
        from trading_bot.backtesting.enhanced_backtester import EnhancedBacktester
        unified_available = False
    except ImportError:
        console.print("[bold red]Error importing backtester components[/bold red]")
        console.print("Make sure you have the trading_bot module installed")
        sys.exit(1)
    else:
        unified_available = False
else:
    unified_available = True

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Diagnostic Backtester Demo with Fixes")
    parser.add_argument("--days", type=int, default=90, help="Number of days to backtest")
    parser.add_argument("--strategies", type=str, default="trend_following,momentum,mean_reversion",
                      help="Comma-separated list of strategies to test")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--rebalance", type=str, default="weekly", 
                      choices=["daily", "weekly", "monthly"], 
                      help="Rebalance frequency")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital")
    return parser.parse_args()

def create_default_config(args):
    """Create a default config dictionary from arguments."""
    # Set dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    # Parse strategies
    strategies = [s.strip() for s in args.strategies.split(",")]
    
    # Create equal allocations
    equal_allocation = 100.0 / len(strategies)
    initial_allocations = {strategy: equal_allocation for strategy in strategies}
    
    return {
        "initial_capital": args.capital,
        "strategies": strategies,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "rebalance_frequency": args.rebalance,
        "initial_allocations": initial_allocations,
        "use_mock": True,
        "debug_mode": True,  # Enable diagnostic mode
        "risk_free_rate": 0.02
    }

def run_diagnostic_backtest(config):
    """Run backtest with the given configuration."""
    console.print(Panel.fit(
        "[bold green]Running Diagnostic Backtester Demo[/bold green]\n"
        "[italic]Testing backtest behavior with all fixes applied[/italic]"
    ))
    
    # Display configuration
    console.print("[bold]Configuration:[/bold]")
    for key, value in config.items():
        if key != "initial_allocations":
            console.print(f"{key}: {value}")
    
    console.print("\n[bold]Strategy Allocations:[/bold]")
    for strategy, allocation in config.get("initial_allocations", {}).items():
        console.print(f"{strategy}: {allocation:.1f}%")
    
    # Initialize and run backtester based on availability
    if unified_available:
        console.print("\n[bold]Using UnifiedBacktester[/bold]")
        
        # Initialize backtester
        backtester = UnifiedBacktester(
            debug_mode=True,  # Enable diagnostic mode
            initial_capital=config["initial_capital"],
            strategies=config["strategies"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            rebalance_frequency=config["rebalance_frequency"],
            use_mock=config["use_mock"],
            risk_free_rate=config["risk_free_rate"]
        )
        
        # Load mock data if needed
        if config["use_mock"]:
            console.print("[yellow]Using mock data for backtesting[/yellow]")
        
        # Run the backtest
        console.print("\n[bold]Running backtest...[/bold]")
        results = backtester.run_backtest()
        
        # Check for trades
        trade_count = len(backtester.trades) if hasattr(backtester, "trades") else 0
        if trade_count > 0:
            console.print(f"[bold green]✓ {trade_count} trades executed[/bold green]")
        else:
            console.print("[bold red]✗ No trades executed[/bold red]")
        
        # Print summary
        print_performance_summary(results)
        
        # Save results if requested
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = "backtest_results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Save portfolio values
            if hasattr(backtester, "portfolio_df"):
                portfolio_path = f"{results_dir}/diagnostic_portfolio_{timestamp}.csv"
                backtester.portfolio_df.to_csv(portfolio_path)
                console.print(f"[green]Portfolio values saved to {portfolio_path}[/green]")
            
            # Save trades if available
            if hasattr(backtester, "trades") and backtester.trades:
                trades_path = f"{results_dir}/diagnostic_trades_{timestamp}.json"
                with open(trades_path, "w") as f:
                    json.dump(backtester.trades, f, indent=2)
                console.print(f"[green]Trades saved to {trades_path}[/green]")
        
        # Generate plots if supported
        if hasattr(backtester, "plot_portfolio_performance"):
            console.print("\n[bold]Generating performance plot...[/bold]")
            try:
                plot_path = "backtest_results/diagnostic_performance.png" if args.save else None
                backtester.plot_portfolio_performance(save_path=plot_path)
                if plot_path:
                    console.print(f"[green]Plot saved to {plot_path}[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not generate plot: {str(e)}[/yellow]")
                
    else:
        console.print("\n[bold]Using EnhancedBacktester[/bold]")
        
        # Copy config and add debug mode
        enhanced_config = config.copy()
        enhanced_config["debug_mode"] = True
        
        # Initialize backtester
        backtester = EnhancedBacktester(enhanced_config)
        
        # Run the backtest
        console.print("\n[bold]Running backtest...[/bold]")
        results = backtester.run_backtest()
        
        # Print summary
        print_enhanced_summary(results)
        
        # Generate plots if supported
        if hasattr(backtester, "plot_results"):
            console.print("\n[bold]Generating performance plot...[/bold]")
            try:
                plot_path = "backtest_results/diagnostic_performance.png" if args.save else None
                backtester.plot_results(save_path=plot_path)
                if plot_path:
                    console.print(f"[green]Plot saved to {plot_path}[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not generate plot: {str(e)}[/yellow]")
    
    console.print("\n[bold green]Diagnostic backtest completed![/bold green]")
    
    return results

def print_performance_summary(results):
    """Print a summary of the performance metrics."""
    # Create performance metrics table
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    
    # Add standard metrics
    metrics_table.add_row("Initial Capital", f"${results.get('initial_capital', 0):,.2f}")
    metrics_table.add_row("Final Capital", f"${results.get('final_capital', 0):,.2f}")
    metrics_table.add_row("Total Return", f"{results.get('total_return_pct', 0):.2f}%")
    metrics_table.add_row("Annualized Return", f"{results.get('annual_return_pct', 0):.2f}%")
    metrics_table.add_row("Volatility", f"{results.get('volatility_pct', 0):.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")
    metrics_table.add_row("Max Drawdown", f"{results.get('max_drawdown_pct', 0):.2f}%")
    metrics_table.add_row("Win Rate", f"{results.get('win_rate_pct', 0):.2f}%")
    
    # Add trade metrics if available
    if 'num_trades' in results:
        metrics_table.add_row("Number of Trades", f"{results.get('num_trades', 0)}")
    if 'total_costs' in results:
        metrics_table.add_row("Trading Costs", f"${results.get('total_costs', 0):,.2f}")
    
    console.print(metrics_table)
    
    # Print strategy metrics if available
    if 'strategy_metrics' in results:
        strategy_table = Table(title="Strategy Performance")
        strategy_table.add_column("Strategy", style="cyan")
        strategy_table.add_column("Avg Allocation", style="yellow")
        strategy_table.add_column("Trades", style="green")
        
        for strategy, metrics in results['strategy_metrics'].items():
            strategy_table.add_row(
                strategy,
                f"{metrics.get('avg_allocation', 0):.1f}%",
                f"{metrics.get('num_trades', 0)}"
            )
        
        console.print(strategy_table)

def print_enhanced_summary(results):
    """Print a summary for the enhanced backtester."""
    summary = results.get('summary', {})
    
    # Create performance metrics table
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    
    metrics_table.add_row("Initial Capital", f"${summary.get('initial_capital', 0):,.2f}")
    metrics_table.add_row("Final Capital", f"${summary.get('final_capital', 0):,.2f}")
    metrics_table.add_row("Total Return", f"{summary.get('total_return_pct', 0):.2f}%")
    metrics_table.add_row("Annualized Return", f"{summary.get('annual_return_pct', 0):.2f}%")
    metrics_table.add_row("Volatility", f"{summary.get('volatility_pct', 0):.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{summary.get('sharpe_ratio', 0):.2f}")
    metrics_table.add_row("Max Drawdown", f"{summary.get('max_drawdown_pct', 0):.2f}%")
    metrics_table.add_row("Win Rate", f"{summary.get('win_rate_pct', 0):.2f}%")
    metrics_table.add_row("Number of Trades", f"{summary.get('num_trades', 0)}")
    
    console.print(metrics_table)
    
    # Print trade counts
    trade_history = results.get('trade_history', [])
    if trade_history:
        trades_by_strategy = {}
        for trade in trade_history:
            strategy = trade.get('strategy', 'unknown')
            if strategy not in trades_by_strategy:
                trades_by_strategy[strategy] = []
            trades_by_strategy[strategy].append(trade)
        
        trade_table = Table(title="Trades by Strategy")
        trade_table.add_column("Strategy", style="cyan")
        trade_table.add_column("Trade Count", style="yellow")
        
        for strategy, trades in trades_by_strategy.items():
            trade_table.add_row(strategy, str(len(trades)))
        
        console.print(trade_table)

def main():
    """Main entry point."""
    global args
    args = parse_args()
    
    # Load config from file if provided, otherwise create from args
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
        console.print(f"[bold]Loaded configuration from {args.config}[/bold]")
    else:
        config = create_default_config(args)
    
    # Always enable debug mode
    config["debug_mode"] = True
    
    try:
        # Run the backtest
        results = run_diagnostic_backtest(config)
        
        # Validate results
        if unified_available:
            trade_count = results.get('num_trades', 0)
        else:
            trade_count = len(results.get('trade_history', []))
        
        if trade_count > 0:
            console.print("\n[bold green]✓ Backtesting fix validation successful![/bold green]")
            console.print("[green]The backtester is now properly executing trades.[/green]")
        else:
            console.print("\n[bold red]✗ Backtesting fix validation failed[/bold red]")
            console.print("[red]No trades were executed during the backtest.[/red]")
            console.print("[yellow]Try running the diagnostic_fix_backtester.py script to apply fixes.[/yellow]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Backtest interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error during backtest: {str(e)}[/bold red]")
        import traceback
        console.print(Panel(traceback.format_exc(), title="Error Details", border_style="red"))

if __name__ == "__main__":
    main() 