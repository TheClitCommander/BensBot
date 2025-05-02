#!/usr/bin/env python3
"""
Advanced Backtester Metrics Demo

This script demonstrates the enhanced backtesting capabilities with comprehensive
performance metrics, drawdown analysis, and strategy correlation visualization.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler
from rich.progress import Progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("advanced_metrics_demo")
console = Console()

# Import backtester
from trading_bot.backtesting.unified_backtester import UnifiedBacktester

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced Backtester Metrics Demo")
    
    parser.add_argument("--days", type=int, default=180, 
                        help="Number of days to backtest")
    
    parser.add_argument("--strategies", type=str, 
                        default="trend_following,momentum,mean_reversion,breakout_swing",
                        help="Comma-separated list of strategies")
    
    parser.add_argument("--initial_capital", type=float, default=100000.0,
                        help="Initial capital")
    
    parser.add_argument("--rebalance", type=str, default="weekly",
                        choices=["daily", "weekly", "monthly"],
                        help="Rebalance frequency")
    
    parser.add_argument("--output", type=str, default="backtest_results",
                        help="Output directory for results")
    
    parser.add_argument("--risk_free_rate", type=float, default=0.02,
                        help="Annual risk-free rate (default: 2%)")
    
    parser.add_argument("--save_plots", action="store_true",
                        help="Save plots to output directory")
    
    return parser.parse_args()

def display_metrics_summary(results):
    """Display a summary of key metrics"""
    # Create performance metrics table
    metrics_table = Table(title="Performance Metrics", title_style="bold blue")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    
    # Add key metrics
    metrics_table.add_row("Total Return", f"{results['total_return_pct']:.2f}%")
    metrics_table.add_row("Annualized Return", f"{results['annual_return_pct']:.2f}%")
    metrics_table.add_row("Volatility", f"{results['volatility_pct']:.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
    metrics_table.add_row("Sortino Ratio", f"{results.get('sortino_ratio', 0):.2f}")
    metrics_table.add_row("Calmar Ratio", f"{results.get('calmar_ratio', 0):.2f}")
    metrics_table.add_row("Max Drawdown", f"{results['max_drawdown_pct']:.2f}%")
    metrics_table.add_row("Win Rate", f"{results['win_rate_pct']:.2f}%")
    metrics_table.add_row("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
    
    console.print(metrics_table)

def display_risk_metrics(results):
    """Display risk metrics"""
    risk_table = Table(title="Risk Metrics", title_style="bold red")
    risk_table.add_column("Metric", style="cyan")
    risk_table.add_column("Value", style="yellow")
    
    # Add risk metrics
    risk_table.add_row("Value at Risk (95%)", f"{results.get('var_95_pct', 0):.2f}%")
    risk_table.add_row("Conditional VaR (95%)", f"{results.get('cvar_95_pct', 0):.2f}%")
    risk_table.add_row("Ulcer Index", f"{results.get('ulcer_index', 0):.4f}")
    risk_table.add_row("Martin Ratio", f"{results.get('martin_ratio', 0):.2f}")
    risk_table.add_row("Max Consecutive Wins", f"{results.get('max_consecutive_wins', 0)}")
    risk_table.add_row("Max Consecutive Losses", f"{results.get('max_consecutive_losses', 0)}")
    risk_table.add_row("Skewness", f"{results.get('skewness', 0):.2f}")
    risk_table.add_row("Kurtosis", f"{results.get('kurtosis', 0):.2f}")
    
    console.print(risk_table)

def display_strategy_metrics(results):
    """Display strategy-specific metrics"""
    if 'strategy_metrics' not in results:
        return
    
    strategy_table = Table(title="Strategy Metrics", title_style="bold green")
    strategy_table.add_column("Strategy", style="blue")
    strategy_table.add_column("Avg Allocation", style="cyan")
    strategy_table.add_column("Final Allocation", style="cyan")
    strategy_table.add_column("Trades", style="yellow")
    
    for strategy, metrics in results['strategy_metrics'].items():
        strategy_table.add_row(
            strategy,
            f"{metrics.get('avg_allocation', 0):.1f}%",
            f"{metrics.get('final_allocation', 0):.1f}%",
            f"{metrics.get('num_trades', 0)}"
        )
    
    console.print(strategy_table)

def display_trade_metrics(results):
    """Display trade metrics"""
    trade_table = Table(title="Trade Metrics", title_style="bold magenta")
    trade_table.add_column("Metric", style="cyan")
    trade_table.add_column("Value", style="yellow")
    
    num_trades = results.get('num_trades', 0)
    total_costs = results.get('total_costs', 0)
    
    trade_table.add_row("Total Trades", f"{num_trades}")
    trade_table.add_row("Trading Costs", f"${total_costs:.2f}")
    
    if 'avg_win_pct' in results and 'avg_loss_pct' in results:
        trade_table.add_row("Average Win", f"{results['avg_win_pct']:.2f}%")
        trade_table.add_row("Average Loss", f"{results['avg_loss_pct']:.2f}%")
        trade_table.add_row("Payoff Ratio", f"{results.get('payoff_ratio', 0):.2f}")
    
    console.print(trade_table)

def run_demo(args):
    """Run the advanced metrics demo"""
    # Parse strategies
    strategies = [s.strip() for s in args.strategies.split(",")]
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    console.print(Panel.fit(
        f"[bold]Advanced Backtester Metrics Demo[/bold]\n"
        f"Testing {len(strategies)} strategies over {args.days} days with {args.rebalance} rebalancing",
        title="Strategy Rotation System",
        border_style="blue"
    ))
    
    # Initialize backtester
    backtester = UnifiedBacktester(
        initial_capital=args.initial_capital,
        strategies=strategies,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        rebalance_frequency=args.rebalance,
        use_mock=True,  # Use mock data for demo
        risk_free_rate=args.risk_free_rate
    )
    
    # Run backtest with progress display
    with Progress() as progress:
        task = progress.add_task("[cyan]Running backtest...", total=100)
        
        # Run backtest
        results = backtester.run_backtest()
        
        # Update progress
        progress.update(task, completed=100)
    
    # Display metrics
    console.print("\n[bold]Backtest Results[/bold]")
    display_metrics_summary(results)
    
    console.print("\n[bold]Risk Analysis[/bold]")
    display_risk_metrics(results)
    
    console.print("\n[bold]Strategy Performance[/bold]")
    display_strategy_metrics(results)
    
    console.print("\n[bold]Trade Analysis[/bold]")
    display_trade_metrics(results)
    
    # Generate and save plots
    try:
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
        
        console.print("\n[bold]Generating Performance Visualizations[/bold]")
        
        # Portfolio performance plot
        console.print("Generating portfolio performance plot...")
        if args.save_plots:
            plot_path = os.path.join(output_dir, "portfolio_performance.png")
            backtester.plot_portfolio_performance(save_path=plot_path)
            console.print(f"  Saved to {plot_path}")
        else:
            backtester.plot_portfolio_performance()
        
        # Drawdown plot
        console.print("Generating drawdown plot...")
        if args.save_plots:
            plot_path = os.path.join(output_dir, "drawdowns.png")
            backtester.plot_drawdowns(save_path=plot_path)
            console.print(f"  Saved to {plot_path}")
        else:
            backtester.plot_drawdowns()
        
        # Strategy allocations plot
        console.print("Generating strategy allocations plot...")
        if args.save_plots:
            plot_path = os.path.join(output_dir, "strategy_allocations.png")
            backtester.plot_strategy_allocations(save_path=plot_path)
            console.print(f"  Saved to {plot_path}")
        else:
            backtester.plot_strategy_allocations()
        
        # Strategy correlations plot
        console.print("Generating strategy correlations plot...")
        if args.save_plots:
            plot_path = os.path.join(output_dir, "strategy_correlations.png")
            backtester.plot_strategy_correlations(save_path=plot_path)
            console.print(f"  Saved to {plot_path}")
        else:
            backtester.plot_strategy_correlations()
        
        # Rolling metrics plot
        console.print("Generating rolling metrics plot...")
        if args.save_plots:
            plot_path = os.path.join(output_dir, "rolling_metrics.png")
            backtester.plot_rolling_metrics(window=30, save_path=plot_path)
            console.print(f"  Saved to {plot_path}")
        else:
            backtester.plot_rolling_metrics(window=30)
        
    except Exception as e:
        console.print(f"[bold red]Error generating plots: {str(e)}[/bold red]")
    
    # Save full performance report
    try:
        if args.save_plots:
            report_path = backtester.save_performance_report(output_dir=args.output)
            console.print(f"\n[bold green]Full performance report saved to: {report_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error saving performance report: {str(e)}[/bold red]")
    
    console.print("\n[bold green]Advanced backtesting demo completed![/bold green]")
    
def main():
    """Main entry point"""
    args = parse_args()
    try:
        run_demo(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 