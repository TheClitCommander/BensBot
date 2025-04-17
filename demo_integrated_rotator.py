#!/usr/bin/env python3
"""
Demo script for the IntegratedStrategyRotator.

This script demonstrates how the IntegratedStrategyRotator combines AI strategy rotation
with performance optimization and dynamic constraint handling.
"""

import os
import sys
import json
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm

# Add the parent directory to the path to allow importing trading_bot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.utils.market_context_fetcher import MarketContextFetcher
from trading_bot.ai_scoring.integrated_strategy_rotator import IntegratedStrategyRotator
from trading_bot.utils.db_models import AllocationDatabase
from trading_bot.utils.rotation_backtester import RotationBacktester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("demo_integrated_rotator")
console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="Demo for AI Strategy Rotation System")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real API calls")
    parser.add_argument("--scenario", type=str, default="volatile", choices=["bullish", "bearish", "volatile", "sideways"], help="Market scenario for mock mode")
    parser.add_argument("--reasoning", action="store_true", help="Display AI reasoning for allocation changes")
    parser.add_argument("--optimize-performance", action="store_true", help="Enable performance-based optimization")
    parser.add_argument("--dynamic-constraints", action="store_true", help="Enable dynamic constraint handling")
    parser.add_argument("--config", type=str, default="configs/strategy_config.json", help="Path to strategy configuration file")
    parser.add_argument("--backtest", action="store_true", help="Run backtest simulation")
    parser.add_argument("--backtest-days", type=int, default=180, help="Number of days to backtest")
    parser.add_argument("--save-results", action="store_true", help="Save rotation results to database")
    return parser.parse_args()

def load_config(config_path):
    """Load strategy configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        console.print(f"[bold red]Configuration file not found: {config_path}[/bold red]")
        console.print(f"[yellow]Creating a default configuration file...[/yellow]")
        
        # Create default config
        default_config = {
            "strategies": [
                "momentum", "mean_reversion", "trend_following", 
                "breakout_swing", "volatility_breakout", "option_spreads"
            ],
            "initial_allocations": {
                "momentum": 20.0, "mean_reversion": 15.0, "trend_following": 25.0,
                "breakout_swing": 20.0, "volatility_breakout": 10.0, "option_spreads": 10.0
            }
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

def print_strategies_table(title, allocations, dollar_amount=100000):
    """Print a table of strategy allocations with dollar amounts."""
    table = Table(title=title)
    table.add_column("Strategy", style="cyan")
    table.add_column("Allocation %", style="magenta")
    table.add_column("Dollar Amount", style="green")
    
    for strategy, allocation in allocations.items():
        dollar_value = dollar_amount * allocation / 100
        table.add_row(
            strategy,
            f"{allocation:.1f}%",
            f"${dollar_value:.2f}"
        )
    
    console.print(table)

def print_allocation_changes(old_allocations, new_allocations):
    """Print a table showing the changes in allocations."""
    table = Table(title="Allocation Changes")
    table.add_column("Strategy", style="cyan")
    table.add_column("Change", style="yellow")
    
    for strategy in old_allocations:
        old_alloc = old_allocations[strategy]
        new_alloc = new_allocations.get(strategy, 0)
        change = new_alloc - old_alloc
        change_str = f"{old_alloc:.1f}% → {new_alloc:.1f}% ({'▲' if change > 0 else '▼'} {abs(change):.1f}%)"
        table.add_row(strategy, change_str)
    
    console.print(table)

def print_dynamic_constraints(constraint_manager):
    """Print the current dynamic constraints."""
    if not constraint_manager:
        return
        
    try:
        constraints = constraint_manager.get_constraints()
        
        table = Table(title="Dynamic Allocation Constraints")
        table.add_column("Strategy", style="cyan")
        table.add_column("Min %", style="red")
        table.add_column("Max %", style="green")
        table.add_column("Max Change %", style="yellow")
        
        for strategy in constraints.get("min_allocation", {}):
            min_allocation = constraints.get("min_allocation", {}).get(strategy, 0)
            max_allocation = constraints.get("max_allocation", {}).get(strategy, 100)
            max_change = constraints.get("max_change", {}).get(strategy, 0)
            
            table.add_row(
                strategy,
                f"{min_allocation:.1f}%",
                f"{max_allocation:.1f}%",
                f"{max_change:.1f}%"
            )
        
        console.print(table)
    except Exception as e:
        logger.error(f"Error displaying constraints: {str(e)}")
        console.print("[bold red]Error displaying constraints[/bold red]")

def print_performance_metrics(performance_optimizer):
    """Print the performance metrics used for optimization."""
    if not performance_optimizer:
        return
        
    try:
        metrics = performance_optimizer.get_performance_metrics()
        scores = performance_optimizer.get_performance_scores()
        
        table = Table(title="Strategy Performance Metrics")
        table.add_column("Strategy", style="cyan")
        table.add_column("Sharpe Ratio", style="yellow")
        table.add_column("Win Rate", style="green")
        table.add_column("Drawdown", style="red")
        table.add_column("Performance Score", style="magenta")
        
        for strategy, metric in metrics.items():
            table.add_row(
                strategy,
                f"{metric.get('sharpe_ratio', 0):.2f}",
                f"{metric.get('win_rate', 0) * 100:.1f}%",
                f"{metric.get('max_drawdown', 0) * 100:.1f}%",
                f"{scores.get(strategy, 0):.2f}"
            )
        
        console.print(table)
    except Exception as e:
        logger.error(f"Error displaying performance metrics: {str(e)}")
        console.print("[bold red]Error displaying performance metrics[/bold red]")

def save_allocation_results(db, market_regime, allocations, reasoning=""):
    """Save allocation results to the database."""
    try:
        # Save current allocations
        db.save_current_allocations(allocations)
        
        # Add to allocation history
        db.add_allocation_history(market_regime, allocations, reasoning)
        
        console.print("[green]Successfully saved allocation results to database[/green]")
        return True
    except Exception as e:
        logger.error(f"Error saving allocation results: {str(e)}")
        console.print("[bold red]Error saving allocation results to database[/bold red]")
        return False

def run_backtest(config, days=180):
    """Run a backtest simulation of the strategy rotation."""
    try:
        console.print(Panel.fit("[bold]Starting Strategy Rotation Backtest[/bold]"))
        
        # Get strategies and initial allocations from config
        strategies = config.get("strategies", [])
        initial_allocations = config.get("initial_allocations", {})
        
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create backtester
        backtester = RotationBacktester(
            strategies=strategies,
            initial_allocations=initial_allocations,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            initial_capital=100000.0
        )
        
        # Run the backtest
        with Progress() as progress:
            task = progress.add_task("[cyan]Running backtest...", total=1)
            
            results = backtester.run_backtest(
                rotation_interval_days=7,
                use_optimization=True,
                use_dynamic_constraints=True
            )
            
            progress.update(task, completed=1)
        
        # Display results
        metrics = results["metrics"]
        console.print("\n[bold]Backtest Results:[/bold]")
        
        metrics_table = Table(title="Performance Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="yellow")
        
        metrics_table.add_row("Total Return", f"{metrics.get('total_return', 0):.2%}")
        metrics_table.add_row("Annualized Return", f"{metrics.get('annualized_return', 0):.2%}")
        metrics_table.add_row("Annualized Volatility", f"{metrics.get('annualized_volatility', 0):.2%}")
        metrics_table.add_row("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
        metrics_table.add_row("Maximum Drawdown", f"{metrics.get('max_drawdown', 0):.2%}")
        metrics_table.add_row("Win Rate", f"{metrics.get('win_rate', 0):.2%}")
        
        console.print(metrics_table)
        
        # Ask if user wants to plot results
        if Confirm.ask("Would you like to plot the backtest results?"):
            plot_path = f"backtest_results/backtest_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(plot_path), exist_ok=True)
            backtester.plot_performance(save_path=plot_path)
            console.print(f"[green]Plot saved to {plot_path}[/green]")
        
        # Ask if user wants to export results
        if Confirm.ask("Would you like to export the backtest results to CSV?"):
            daily_path, alloc_path = backtester.export_results_to_csv()
            console.print(f"[green]Results exported to:[/green]")
            console.print(f"[green]- Daily values: {daily_path}[/green]")
            console.print(f"[green]- Allocation history: {alloc_path}[/green]")
        
        return results
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        console.print(f"[bold red]Error running backtest: {str(e)}[/bold red]")
        console.print(Panel(traceback.format_exc(), title="Backtest Error", border_style="red"))
        return None

def main():
    try:
        args = parse_args()
        
        # Load configuration
        config = load_config(args.config)
        strategies = config.get("strategies", [])
        initial_allocations = config.get("initial_allocations", {})
        
        # Check if we should run a backtest
        if args.backtest:
            run_backtest(config, days=args.backtest_days)
            return
        
        # Initialize database if saving results
        db = None
        if args.save_results:
            db = AllocationDatabase()
            
            # Check if we have saved allocations
            saved_allocations = db.get_current_allocations()
            if saved_allocations:
                use_saved = Confirm.ask("Found saved allocations. Would you like to use them?")
                if use_saved:
                    initial_allocations = saved_allocations
                    console.print("[green]Using saved allocations from database[/green]")
        
        # Initialize the market context fetcher
        market_fetcher = MarketContextFetcher(
            use_mock=args.mock, 
            cache_duration=60,
            mock_scenario=args.scenario
        )
        
        # Initialize the integrated strategy rotator
        rotator = IntegratedStrategyRotator(
            strategies=strategies,
            initial_allocations=initial_allocations,
            use_mock=args.mock,
            optimize_performance=args.optimize_performance,
            dynamic_constraints=args.dynamic_constraints
        )
        
        # Display header
        console.print(Panel.fit(
            "[bold green]AI Strategy Rotation System Demo[/bold green]\n"
            f"[italic]Using {'mock' if args.mock else 'live'} strategy prioritization with "
            f"{'performance optimization' if args.optimize_performance else 'no performance optimization'} "
            f"and {'dynamic' if args.dynamic_constraints else 'static'} constraints.[/italic]"
        ))
        
        # Display initial allocations
        console.print("\n[bold]Starting with initial strategy allocations:[/bold]")
        print_strategies_table("Current Strategy Allocations", rotator.get_current_allocations())
        
        # Display performance metrics if enabled
        if args.optimize_performance:
            console.print("\n[bold]Current Performance Metrics:[/bold]")
            print_performance_metrics(rotator.performance_optimizer)
        
        # Display constraints if dynamic constraints enabled
        if args.dynamic_constraints:
            console.print("\n[bold]Current Allocation Constraints:[/bold]")
            print_dynamic_constraints(rotator.constraint_manager)
        
        # Get market context
        console.print("\n[bold]Fetching current market context...[/bold]")
        try:
            market_context = market_fetcher.get_market_context()
            market_summary = market_fetcher.get_market_summary(market_context)
            console.print(f"[green]Market summary:[/green] {market_summary}")
        except Exception as e:
            logger.error(f"Error fetching market context: {str(e)}")
            console.print(f"[bold red]Error fetching market context: {str(e)}[/bold red]")
            if not args.mock:
                console.print("[yellow]Switching to mock mode as fallback...[/yellow]")
                args.mock = True
                market_context = market_fetcher.get_mock_market_context(scenario=args.scenario)
                market_summary = market_fetcher.get_market_summary(market_context)
                console.print(f"[green]Mock market summary:[/green] {market_summary}")
            else:
                console.print("[bold red]Cannot fetch market context even in mock mode. Exiting.[/bold red]")
                return
        
        # Perform strategy rotation
        console.print("\n[bold]Performing strategy rotation based on market conditions...[/bold]")
        console.print("[italic](This may take a few seconds if using live evaluations)[/italic]")
        
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Rotating strategies...", total=1)
                
                # Perform the rotation
                rotation_result = rotator.rotate_strategies(
                    market_context=market_context,
                    force_rotation=True
                )
                
                progress.update(task, completed=1)
            
            # Check if rotation was successful
            if not rotation_result.get("rotated", False):
                console.print(f"[yellow]{rotation_result.get('message', 'No rotation performed')}[/yellow]")
                return
            
            # Get rotation results
            new_allocations = rotation_result.get("new_allocations", {})
            reasoning = rotation_result.get("reasoning", "")
            regime = rotation_result.get("regime", "unknown")
        
            # Display new allocations
            console.print("\n[bold]New strategy allocations after rotation:[/bold]")
            print_strategies_table("New Strategy Allocations", new_allocations)
            
            # Display allocation changes
            console.print("\n[bold]Allocation changes:[/bold]")
            print_allocation_changes(rotator.get_current_allocations(), new_allocations)
            
            # Display updated constraints if dynamic constraints enabled
            if args.dynamic_constraints:
                console.print("\n[bold]Updated Allocation Constraints:[/bold]")
                print_dynamic_constraints(rotator.constraint_manager)
            
            # Display AI reasoning if requested
            if args.reasoning and reasoning:
                console.print("\n[bold]AI Reasoning for New Allocations:[/bold]")
                console.print(Panel.fit(reasoning, title="AI Reasoning", border_style="green"))
            
            # Save results if requested
            if args.save_results and db:
                save_allocation_results(db, regime, new_allocations, reasoning)
            
            console.print("\n[bold green]Strategy rotation completed successfully![/bold green]")
        except Exception as e:
            logger.error(f"Error during strategy rotation: {str(e)}")
            console.print(f"[bold red]Error during strategy rotation: {str(e)}[/bold red]")
            console.print(Panel(traceback.format_exc(), title="Rotation Error", border_style="red"))
            return
        
        console.print("\n[bold green]Demo completed successfully![/bold green]")
        console.print("[italic]AI can automatically adjust strategy allocations based on market conditions,[/italic]")
        console.print("[italic]optimizing for performance while respecting allocation constraints.[/italic]")
        console.print("[italic]This can be integrated into your trading platform for dynamic strategy rotation.[/italic]")
        
        # Suggest next steps
        console.print("\n[bold]Suggested next steps:[/bold]")
        console.print("1. [cyan]Run a backtest[/cyan] to see how these allocations would have performed historically:")
        console.print("   [dim]python demo_integrated_rotator.py --backtest --backtest-days 365[/dim]")
        console.print("2. [cyan]Connect to a live trading system[/cyan] to execute trades based on allocations")
        console.print("3. [cyan]Set up automated rotation[/cyan] on a schedule (e.g., weekly)")
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        console.print(Panel(traceback.format_exc(), title="Error", border_style="red"))

if __name__ == "__main__":
    main() 