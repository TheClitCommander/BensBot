#!/usr/bin/env python3
"""
Demo script for the Enhanced Backtester.

This script demonstrates how to use the enhanced backtester with proper signal generation
and trade execution to test the strategy rotation system.
"""

import os
import sys
import json
import argparse
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm

# Add the parent directory to the path to allow importing trading_bot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.backtesting.enhanced_backtester import EnhancedBacktester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("demo_enhanced_backtester")
console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="Demo for Enhanced Backtester")
    parser.add_argument("--config", type=str, default="configs/backtest_config.json", help="Path to backtest configuration file")
    parser.add_argument("--days", type=int, default=180, help="Number of days to backtest")
    parser.add_argument("--save-results", action="store_true", help="Save backtest results")
    parser.add_argument("--plot", action="store_true", help="Plot backtest results")
    return parser.parse_args()

def load_config(config_path):
    """Load backtest configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        console.print(f"[bold red]Configuration file not found: {config_path}[/bold red]")
        console.print(f"[yellow]Creating a default configuration file...[/yellow]")
        
        # Calculate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Create default config
        default_config = {
            "strategies": [
                "trend_following", "momentum", "mean_reversion",
                "breakout_swing", "volatility_breakout", "option_spreads"
            ],
            "initial_allocations": {
                "trend_following": 25.0, "momentum": 20.0, "mean_reversion": 15.0,
                "breakout_swing": 20.0, "volatility_breakout": 10.0, "option_spreads": 10.0
            },
            "initial_capital": 100000.0,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "commission_rate": 0.001,
            "slippage": 0.001,
            "rebalance_frequency": "weekly",
            "use_mock": True
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save default config
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        return default_config
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        console.print(f"[bold red]Invalid JSON in configuration file: {config_path}[/bold red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        console.print(f"[bold red]Error loading configuration: {str(e)}[/bold red]")
        sys.exit(1)

def print_backtest_summary(results):
    """Print a summary of backtest results."""
    summary = results.get('summary', {})
    
    # Create performance metrics table
    metrics_table = Table(title="Backtest Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    
    metrics_table.add_row("Initial Capital", f"${summary.get('initial_capital', 0):,.2f}")
    metrics_table.add_row("Final Capital", f"${summary.get('final_capital', 0):,.2f}")
    metrics_table.add_row("Total Return", f"{summary.get('total_return_pct', 0):.2f}%")
    metrics_table.add_row("Annualized Return", f"{summary.get('annual_return_pct', 0):.2f}%")
    metrics_table.add_row("Annualized Volatility", f"{summary.get('volatility_pct', 0):.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{summary.get('sharpe_ratio', 0):.2f}")
    metrics_table.add_row("Maximum Drawdown", f"{summary.get('max_drawdown_pct', 0):.2f}%")
    metrics_table.add_row("Win Rate", f"{summary.get('win_rate_pct', 0):.2f}%")
    metrics_table.add_row("Number of Trades", f"{summary.get('num_trades', 0)}")
    metrics_table.add_row("Backtest Days", f"{summary.get('backtest_days', 0)}")
    
    console.print(metrics_table)
    
    # If trades were executed, show strategy performance
    trade_history = results.get('trade_history', [])
    if trade_history:
        # Group trades by strategy
        strategy_trades = {}
        for trade in trade_history:
            if 'pnl' not in trade:
                continue
                
            strategy = trade.get('strategy', 'unknown')
            if strategy not in strategy_trades:
                strategy_trades[strategy] = []
            strategy_trades[strategy].append(trade)
        
        # Calculate strategy performance
        strategy_table = Table(title="Strategy Performance")
        strategy_table.add_column("Strategy", style="cyan")
        strategy_table.add_column("Trades", style="magenta")
        strategy_table.add_column("Win Rate", style="green")
        strategy_table.add_column("Average P/L", style="yellow")
        strategy_table.add_column("Total P/L", style="red")
        
        for strategy, trades in strategy_trades.items():
            num_trades = len(trades)
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0
            avg_pnl = sum(t['pnl'] for t in trades) / num_trades if num_trades > 0 else 0
            total_pnl = sum(t['pnl'] for t in trades)
            
            strategy_table.add_row(
                strategy,
                f"{num_trades}",
                f"{win_rate * 100:.2f}%",
                f"${avg_pnl:.2f}",
                f"${total_pnl:.2f}"
            )
        
        console.print(strategy_table)

def main():
    try:
        args = parse_args()
        
        # Display header
        console.print(Panel.fit(
            "[bold green]Enhanced Backtester Demo[/bold green]\n"
            "[italic]Backtesting the AI Strategy Rotation System with proper signal generation and trade execution.[/italic]"
        ))
        
        # Load configuration
        config = load_config(args.config)
        
        # Update backtest days if specified
        if args.days:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            config['start_date'] = start_date.strftime("%Y-%m-%d")
            config['end_date'] = end_date.strftime("%Y-%m-%d")
        
        # Display configuration
        console.print("\n[bold]Backtest Configuration:[/bold]")
        console.print(f"Period: {config['start_date']} to {config['end_date']} ({args.days} days)")
        console.print(f"Initial Capital: ${config['initial_capital']:,.2f}")
        console.print(f"Strategies: {', '.join(config['strategies'])}")
        console.print(f"Rebalance Frequency: {config['rebalance_frequency']}")
        
        # Initialize backtester
        with Progress() as progress:
            task = progress.add_task("[cyan]Initializing backtester...", total=1)
            
            backtester = EnhancedBacktester(config)
            
            progress.update(task, completed=1)
        
        # Run backtest
        console.print("\n[bold]Running backtest...[/bold]")
        console.print("[italic](This may take a few minutes for longer periods)[/italic]")
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Backtesting...", total=1)
            
            # Run the backtest
            results = backtester.run_backtest()
            
            progress.update(task, completed=1)
        
        # Print backtest summary
        console.print("\n[bold]Backtest Results:[/bold]")
        print_backtest_summary(results)
        
        # Plot results if requested
        if args.plot:
            console.print("\n[bold]Generating performance plot...[/bold]")
            
            plot_path = f"backtest_results/backtest_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(plot_path), exist_ok=True)
            
            backtester.plot_results(save_path=plot_path)
            console.print(f"[green]Plot saved to {plot_path}[/green]")
        
        # Export results if requested
        if args.save_results:
            console.print("\n[bold]Exporting backtest results...[/bold]")
            
            results_dir = "backtest_results"
            os.makedirs(results_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            portfolio_path = f"{results_dir}/portfolio_values_{timestamp}.csv"
            trades_path = f"{results_dir}/trade_history_{timestamp}.csv"
            allocations_path = f"{results_dir}/allocation_history_{timestamp}.csv"
            
            backtester.export_results_to_csv(
                portfolio_path=portfolio_path,
                trades_path=trades_path,
                allocations_path=allocations_path
            )
            
            console.print(f"[green]Results exported to:[/green]")
            console.print(f"[green]- Portfolio values: {portfolio_path}[/green]")
            console.print(f"[green]- Trade history: {trades_path}[/green]")
            console.print(f"[green]- Allocation history: {allocations_path}[/green]")
        
        console.print("\n[bold green]Backtest completed successfully![/bold green]")
        
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        console.print(Panel(traceback.format_exc(), title="Error", border_style="red"))

if __name__ == "__main__":
    main() 