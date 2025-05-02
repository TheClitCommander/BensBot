#!/usr/bin/env python3
"""
Risk Management Demo Script

This script demonstrates the risk management features of the backtesting system,
including circuit breakers, dynamic position sizing, and stress testing.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("risk_management_demo")
console = Console()

# Import backtester and risk components
from trading_bot.backtesting.unified_backtester import UnifiedBacktester
from trading_bot.risk import RiskManager, RiskMonitor

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Risk Management Backtester Demo")
    
    parser.add_argument("--days", type=int, default=365, 
                        help="Number of days to backtest")
    
    parser.add_argument("--strategies", type=str, 
                        default="trend_following,momentum,mean_reversion,volatility_breakout",
                        help="Comma-separated list of strategies")
    
    parser.add_argument("--initial_capital", type=float, default=100000.0,
                        help="Initial capital")
    
    parser.add_argument("--rebalance", type=str, default="weekly",
                        choices=["daily", "weekly", "monthly"],
                        help="Rebalance frequency")
    
    parser.add_argument("--output", type=str, default="backtest_results",
                        help="Output directory for results")
    
    parser.add_argument("--risk_file", type=str, default="configs/risk_config.json",
                        help="Risk configuration file")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    
    parser.add_argument("--no_risk", action="store_true",
                        help="Disable risk management")
    
    parser.add_argument("--no_circuit_breakers", action="store_true",
                        help="Disable circuit breakers")
    
    parser.add_argument("--scenario", type=str, choices=["normal", "crash", "volatile"],
                        default="normal", help="Market scenario to simulate")
    
    parser.add_argument("--save_plots", action="store_true",
                        help="Save plots")
    
    return parser.parse_args()

def load_risk_config(args):
    """Load risk configuration."""
    try:
        with open(args.risk_file, "r") as f:
            config = json.load(f)
            logger.info(f"Loaded risk configuration from {args.risk_file}")
            return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading risk config file: {e}")
        logger.warning("Using default risk configuration")
        return {}

def modify_market_scenario(scenario, mock_data):
    """Modify mock data to simulate different market scenarios."""
    if scenario == "normal":
        return mock_data  # No modifications needed
    
    # Create a copy of the data
    modified_data = mock_data.copy()
    
    # Get a range of dates to modify
    dates = modified_data.index
    mid_point = len(dates) // 2
    start_idx = mid_point - 10
    end_idx = mid_point + 40
    
    if scenario == "crash":
        # Simulate a market crash
        logger.info("Simulating market crash scenario")
        
        # Gradually decrease index value
        for i in range(start_idx, end_idx):
            if i < len(dates):
                date = dates[i]
                if i < start_idx + 5:
                    # Initial decline
                    modified_data.loc[date, 'return'] = -0.01  # -1% daily
                elif i < start_idx + 10:
                    # Accelerated decline
                    modified_data.loc[date, 'return'] = -0.02  # -2% daily
                elif i < start_idx + 15:
                    # Crash
                    modified_data.loc[date, 'return'] = -0.05  # -5% daily
                elif i < start_idx + 25:
                    # Continued volatility
                    modified_data.loc[date, 'return'] = np.random.normal(-0.01, 0.02)  # Negative with high volatility
                else:
                    # Recovery phase
                    modified_data.loc[date, 'return'] = np.random.normal(0.005, 0.015)  # Slightly positive
        
        # Update equity curve
        returns = modified_data['return'].values
        equity_curve = np.cumprod(1 + returns)
        modified_data['equity_curve'] = equity_curve
                
    elif scenario == "volatile":
        # Simulate high volatility market
        logger.info("Simulating high volatility scenario")
        
        # Increase volatility
        for i in range(start_idx, end_idx):
            if i < len(dates):
                date = dates[i]
                # Generate highly volatile returns
                modified_data.loc[date, 'return'] = np.random.normal(0.0, 0.03)  # 3% daily volatility
        
        # Update equity curve
        returns = modified_data['return'].values
        equity_curve = np.cumprod(1 + returns)
        modified_data['equity_curve'] = equity_curve
    
    return modified_data

def run_backtest_comparison(args):
    """Run backtests with and without risk management for comparison."""
    # Load risk configuration
    risk_config = load_risk_config(args)
    
    # Parse strategies
    strategies = [s.strip() for s in args.strategies.split(",")]
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    console.print(f"[bold blue]Risk Management Demo[/bold blue]")
    console.print(f"Running backtest with {len(strategies)} strategies over {args.days} days")
    console.print(f"Market scenario: [bold]{args.scenario}[/bold]")
    
    # Initialize backtests
    with_risk = UnifiedBacktester(
        initial_capital=args.initial_capital,
        strategies=strategies,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        rebalance_frequency=args.rebalance,
        use_mock=True,
        risk_config=risk_config,
        enable_risk_management=not args.no_risk,
        enable_circuit_breakers=not args.no_circuit_breakers,
        debug_mode=args.debug,
        results_path=os.path.join(args.output, "with_risk")
    )
    
    without_risk = UnifiedBacktester(
        initial_capital=args.initial_capital,
        strategies=strategies,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        rebalance_frequency=args.rebalance,
        use_mock=True,
        enable_risk_management=False,  # Explicitly disable risk management
        debug_mode=args.debug,
        results_path=os.path.join(args.output, "without_risk")
    )
    
    # Load data for both backtests
    with_risk.load_strategy_data()
    without_risk.load_strategy_data()
    
    with_risk.load_market_data()
    without_risk.load_market_data()
    
    with_risk.load_regime_data()
    without_risk.load_regime_data()
    
    # Modify data for scenario if needed
    if args.scenario != "normal":
        console.print(f"[yellow]Modifying market data for {args.scenario} scenario[/yellow]")
        
        # Apply scenario to all strategies
        for strategy in strategies:
            with_risk.strategy_data[strategy] = modify_market_scenario(args.scenario, with_risk.strategy_data[strategy])
            without_risk.strategy_data[strategy] = modify_market_scenario(args.scenario, without_risk.strategy_data[strategy])
    
    # Run backtests with progress display
    results = {}
    
    with Progress() as progress:
        # Run backtest with risk management
        task1 = progress.add_task("[green]Running backtest with risk management...", total=100)
        
        # Generate rebalance dates
        rebalance_dates = with_risk._generate_rebalance_dates()
        
        # Initialize portfolio
        with_risk.portfolio_history = [{
            'date': with_risk.start_date,
            'capital': with_risk.initial_capital,
            'positions': {strategy: 0.0 for strategy in with_risk.strategies},
            'daily_return': 0.0
        }]
        
        # Set initial positions based on initial allocations
        initial_positions = {}
        for strategy, allocation in with_risk.initial_allocations.items():
            initial_positions[strategy] = with_risk.initial_capital * (allocation / 100.0)
        with_risk.portfolio_history[0]['positions'] = initial_positions
            
        # Record initial allocations
        with_risk.allocation_history = [{
            'date': with_risk.start_date,
            'allocations': with_risk.initial_allocations.copy()
        }]
        
        # Track trades
        with_risk.trades = []
        with_risk.total_costs = 0.0
        with_risk.min_trade_value = with_risk.initial_capital * 0.001  # 0.1% of capital
        
        # Run day by day
        current_date = with_risk.start_date
        step_count = 0
        total_steps = (with_risk.end_date - with_risk.start_date).days
        
        while current_date <= with_risk.end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # 0-4 are weekdays
                with_risk.step(current_date)
                step_count += 1
                progress.update(task1, completed=step_count / total_steps * 100)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Process results
        with_risk._process_backtest_results()
        results["with_risk"] = with_risk.get_performance_summary()
        
        # Run backtest without risk management
        task2 = progress.add_task("[red]Running backtest without risk management...", total=100)
        
        # Initialize portfolio
        without_risk.portfolio_history = [{
            'date': without_risk.start_date,
            'capital': without_risk.initial_capital,
            'positions': {strategy: 0.0 for strategy in without_risk.strategies},
            'daily_return': 0.0
        }]
        
        # Set initial positions based on initial allocations
        initial_positions = {}
        for strategy, allocation in without_risk.initial_allocations.items():
            initial_positions[strategy] = without_risk.initial_capital * (allocation / 100.0)
        without_risk.portfolio_history[0]['positions'] = initial_positions
            
        # Record initial allocations
        without_risk.allocation_history = [{
            'date': without_risk.start_date,
            'allocations': without_risk.initial_allocations.copy()
        }]
        
        # Track trades
        without_risk.trades = []
        without_risk.total_costs = 0.0
        without_risk.min_trade_value = without_risk.initial_capital * 0.001  # 0.1% of capital
        
        # Run day by day
        current_date = without_risk.start_date
        step_count = 0
        
        while current_date <= without_risk.end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # 0-4 are weekdays
                without_risk.step(current_date)
                step_count += 1
                progress.update(task2, completed=step_count / total_steps * 100)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Process results
        without_risk._process_backtest_results()
        results["without_risk"] = without_risk.get_performance_summary()
    
    # Display circuit breaker events
    if hasattr(with_risk.risk_manager, 'circuit_breaker_history') and with_risk.risk_manager.circuit_breaker_history:
        console.print("\n[bold red]Circuit Breaker Events:[/bold red]")
        for i, event in enumerate(with_risk.risk_manager.circuit_breaker_history):
            console.print(f"Event {i+1}:")
            console.print(f"  Date: {event['timestamp'].strftime('%Y-%m-%d')}")
            console.print(f"  Reason: {event['reason']}")
            console.print(f"  Exposure Reduction: {event['reduction_pct']}%")
            console.print(f"  Cooldown Until: {event['end_date'].strftime('%Y-%m-%d')}")
            console.print("")
    
    # Display comparative results
    display_comparative_results(results)
    
    # Generate and save plots
    if args.save_plots:
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
        
        console.print("\n[bold]Generating Performance Comparison Plots[/bold]")
        
        # Portfolio value comparison
        plot_portfolio_comparison(
            with_risk.portfolio_df['portfolio_value'], 
            without_risk.portfolio_df['portfolio_value'],
            "Portfolio Value Comparison",
            os.path.join(output_dir, "portfolio_comparison.png") if args.save_plots else None
        )
        
        # Drawdown comparison
        with_drawdown, _ = with_risk.calculate_drawdowns(with_risk.portfolio_df['portfolio_value'])
        without_drawdown, _ = without_risk.calculate_drawdowns(without_risk.portfolio_df['portfolio_value'])
        
        plot_drawdown_comparison(
            with_drawdown,
            without_drawdown,
            "Drawdown Comparison",
            os.path.join(output_dir, "drawdown_comparison.png") if args.save_plots else None
        )
        
        # Plot allocation changes over time
        plot_allocations(
            with_risk.allocation_df,
            "Strategy Allocations with Risk Management",
            os.path.join(output_dir, "allocations_with_risk.png") if args.save_plots else None
        )
        
        plot_allocations(
            without_risk.allocation_df,
            "Strategy Allocations without Risk Management",
            os.path.join(output_dir, "allocations_without_risk.png") if args.save_plots else None
        )
    
    return with_risk, without_risk, results

def display_comparative_results(results):
    """Display comparative results between backtests with and without risk management."""
    with_risk = results["with_risk"]
    without_risk = results["without_risk"]
    
    # Create a comparison table
    table = Table(title="Backtest Performance Comparison", title_style="bold blue")
    table.add_column("Metric", style="cyan")
    table.add_column("With Risk Mgmt", style="green")
    table.add_column("Without Risk Mgmt", style="red")
    table.add_column("Difference", style="yellow")
    
    # Helper function to calculate difference
    def calculate_diff(a, b, percentage=False):
        diff = a - b
        if percentage:
            return f"{diff:+.2f}%"
        return f"{diff:+.2f}"
    
    # Add key metrics
    table.add_row(
        "Final Capital",
        f"${with_risk['final_capital']:.2f}",
        f"${without_risk['final_capital']:.2f}",
        calculate_diff(with_risk['final_capital'], without_risk['final_capital'])
    )
    
    table.add_row(
        "Total Return",
        f"{with_risk['total_return_pct']:.2f}%",
        f"{without_risk['total_return_pct']:.2f}%",
        calculate_diff(with_risk['total_return_pct'], without_risk['total_return_pct'], True)
    )
    
    table.add_row(
        "Annualized Return",
        f"{with_risk['annual_return_pct']:.2f}%",
        f"{without_risk['annual_return_pct']:.2f}%",
        calculate_diff(with_risk['annual_return_pct'], without_risk['annual_return_pct'], True)
    )
    
    table.add_row(
        "Volatility",
        f"{with_risk['volatility_pct']:.2f}%",
        f"{without_risk['volatility_pct']:.2f}%",
        calculate_diff(with_risk['volatility_pct'], without_risk['volatility_pct'], True)
    )
    
    table.add_row(
        "Sharpe Ratio",
        f"{with_risk['sharpe_ratio']:.2f}",
        f"{without_risk['sharpe_ratio']:.2f}",
        calculate_diff(with_risk['sharpe_ratio'], without_risk['sharpe_ratio'])
    )
    
    table.add_row(
        "Max Drawdown",
        f"{with_risk['max_drawdown_pct']:.2f}%",
        f"{without_risk['max_drawdown_pct']:.2f}%",
        calculate_diff(with_risk['max_drawdown_pct'], without_risk['max_drawdown_pct'], True)
    )
    
    table.add_row(
        "Sortino Ratio",
        f"{with_risk.get('sortino_ratio', 0):.2f}",
        f"{without_risk.get('sortino_ratio', 0):.2f}",
        calculate_diff(with_risk.get('sortino_ratio', 0), without_risk.get('sortino_ratio', 0))
    )
    
    table.add_row(
        "Calmar Ratio",
        f"{with_risk.get('calmar_ratio', 0):.2f}",
        f"{without_risk.get('calmar_ratio', 0):.2f}",
        calculate_diff(with_risk.get('calmar_ratio', 0), without_risk.get('calmar_ratio', 0))
    )
    
    table.add_row(
        "Total Trades",
        f"{with_risk['num_trades']}",
        f"{without_risk['num_trades']}",
        calculate_diff(with_risk['num_trades'], without_risk['num_trades'])
    )
    
    console.print("\n")
    console.print(table)
    console.print("\n")
    
    # Print risk management effectiveness
    if with_risk['total_return_pct'] > without_risk['total_return_pct']:
        console.print("[bold green]Risk management improved returns[/bold green]")
    else:
        diff = without_risk['total_return_pct'] - with_risk['total_return_pct']
        console.print(f"[yellow]Risk management reduced returns by {diff:.2f}%, but may have protected from larger losses[/yellow]")
    
    if with_risk['max_drawdown_pct'] > without_risk['max_drawdown_pct']:
        console.print("[red]Risk management did not reduce maximum drawdown[/red]")
    else:
        diff = without_risk['max_drawdown_pct'] - with_risk['max_drawdown_pct']
        console.print(f"[bold green]Risk management reduced maximum drawdown by {abs(diff):.2f}%[/bold green]")
    
    if with_risk['sharpe_ratio'] > without_risk['sharpe_ratio']:
        console.print("[bold green]Risk management improved risk-adjusted returns (Sharpe ratio)[/bold green]")
    else:
        console.print("[yellow]Risk management reduced risk-adjusted returns (Sharpe ratio)[/yellow]")

def plot_portfolio_comparison(with_risk_values, without_risk_values, title, save_path=None):
    """Plot comparison of portfolio values with and without risk management."""
    plt.figure(figsize=(12, 6))
    
    plt.plot(with_risk_values.index, with_risk_values, label="With Risk Management", color="green")
    plt.plot(without_risk_values.index, without_risk_values, label="Without Risk Management", color="red")
    
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        console.print(f"  Saved to {save_path}")
    
    plt.show()

def plot_drawdown_comparison(with_risk_drawdown, without_risk_drawdown, title, save_path=None):
    """Plot comparison of drawdowns with and without risk management."""
    plt.figure(figsize=(12, 6))
    
    plt.plot(with_risk_drawdown.index, with_risk_drawdown, label="With Risk Management", color="green")
    plt.plot(without_risk_drawdown.index, without_risk_drawdown, label="Without Risk Management", color="red")
    
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Fill areas under curves
    plt.fill_between(with_risk_drawdown.index, with_risk_drawdown, 0, color="green", alpha=0.1)
    plt.fill_between(without_risk_drawdown.index, without_risk_drawdown, 0, color="red", alpha=0.1)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        console.print(f"  Saved to {save_path}")
    
    plt.show()

def plot_allocations(allocation_df, title, save_path=None):
    """Plot strategy allocations over time."""
    plt.figure(figsize=(12, 6))
    
    # Extract allocation columns
    allocation_cols = [col for col in allocation_df.columns if col.endswith('_allocation')]
    
    # Plot stacked area chart
    allocation_df[allocation_cols].plot.area(stacked=True)
    
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Allocation (%)")
    plt.legend(title="Strategy", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        console.print(f"  Saved to {save_path}")
    
    plt.show()

def main():
    """Main function to run the demo."""
    args = parse_args()
    
    try:
        os.makedirs(args.output, exist_ok=True)
        with_risk, without_risk, results = run_backtest_comparison(args)
        
        console.print("\n[bold green]Risk management demo completed successfully![/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        if args.debug:
            import traceback
            console.print(traceback.format_exc())

if __name__ == "__main__":
    main() 