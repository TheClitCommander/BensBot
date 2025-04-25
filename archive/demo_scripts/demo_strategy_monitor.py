#!/usr/bin/env python3
"""
Demo script for the Strategy Monitoring System.

This script demonstrates how the monitoring system tracks performance, 
generates alerts, and creates reports for the strategy rotation system.
"""

import os
import sys
import json
import argparse
import logging
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

# Add the parent directory to the path to allow importing trading_bot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.utils.market_context_fetcher import MarketContextFetcher
from trading_bot.ai_scoring.integrated_strategy_rotator import IntegratedStrategyRotator
from trading_bot.utils.performance_monitor import StrategyMonitor, PerformanceMonitor
from trading_bot.utils.db_models import AllocationDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("demo_strategy_monitor")
console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="Demo for Strategy Monitoring System")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real API calls")
    parser.add_argument("--config", type=str, default="configs/strategy_config.json", help="Path to strategy configuration file")
    parser.add_argument("--monitor-config", type=str, default="configs/monitor_config.json", help="Path to monitoring configuration file")
    parser.add_argument("--simulate-days", type=int, default=30, help="Number of days to simulate for demonstration")
    parser.add_argument("--generate-report", action="store_true", help="Generate a performance report")
    parser.add_argument("--plot-performance", action="store_true", help="Plot strategy performance")
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

def simulate_performance_data(strategies, days=30):
    """
    Simulate performance data for demonstration purposes.
    
    Args:
        strategies: List of strategy names
        days: Number of days to simulate
        
    Returns:
        Dictionary mapping strategies to daily performance metrics
    """
    import numpy as np
    
    # Strategy profiles (mean return, volatility)
    profiles = {
        "momentum": (0.0005, 0.012),
        "mean_reversion": (0.0004, 0.009),
        "trend_following": (0.0006, 0.015),
        "breakout_swing": (0.0007, 0.018),
        "volatility_breakout": (0.0008, 0.022),
        "option_spreads": (0.0003, 0.008)
    }
    
    # Start date
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate simulated data
    result = {}
    for strategy in strategies:
        if strategy not in profiles:
            # Use default profile
            mean, vol = 0.0005, 0.01
        else:
            mean, vol = profiles[strategy]
        
        # Generate daily returns with random walk
        np.random.seed(hash(strategy) % 10000)  # Different seed per strategy
        daily_returns = np.random.normal(mean, vol, days)
        
        # Calculate cumulative return and drawdown
        cum_returns = np.cumprod(1 + daily_returns) - 1
        peak = np.maximum.accumulate(cum_returns)
        drawdown = cum_returns - peak
        
        # Store metrics for each day
        strategy_data = []
        for i, date in enumerate(dates):
            # More negative drawdown on some days for demonstration
            special_drawdown = drawdown[i]
            if i % 7 == 0 and strategy == "volatility_breakout":
                special_drawdown = -0.15  # Trigger drawdown alert
            
            metrics = {
                "timestamp": date.isoformat(),
                "daily_return": daily_returns[i],
                "cumulative_return": cum_returns[i],
                "max_drawdown": special_drawdown,
                "volatility": vol * np.sqrt(252),  # Annualized
                "sharpe_ratio": mean / vol * np.sqrt(252) if vol > 0 else 0,
                "win_rate": 0.52  # Arbitrary win rate
            }
            strategy_data.append(metrics)
        
        result[strategy] = strategy_data
    
    return result

def main():
    args = parse_args()
    
    # Load configurations
    strategy_config = load_config(args.config)
    monitor_config = load_config(args.monitor_config)
    
    if not strategy_config:
        console.print("[bold red]Error: Strategy configuration could not be loaded.[/bold red]")
        return
    
    # Get strategies and initial allocations
    strategies = strategy_config.get("strategies", [])
    initial_allocations = strategy_config.get("initial_allocations", {})
    
    if not strategies:
        console.print("[bold red]Error: No strategies defined in configuration.[/bold red]")
        return
    
    # Initialize components
    console.print(Panel.fit("[bold green]Strategy Monitoring System Demo[/bold green]"))
    console.print("\n[bold]Initializing components...[/bold]")
    
    # Initialize the strategy rotator
    rotator = IntegratedStrategyRotator(
        strategies=strategies,
        initial_allocations=initial_allocations,
        use_mock=args.mock
    )
    
    # Initialize the strategy monitor
    monitor = StrategyMonitor(
        strategy_rotator=rotator,
        config_path=args.monitor_config
    )
    
    console.print("[green]Components initialized successfully.[/green]")
    
    # Simulate performance data
    console.print("\n[bold]Simulating strategy performance data...[/bold]")
    simulated_data = simulate_performance_data(strategies, days=args.simulate_days)
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Simulating performance data...", total=args.simulate_days)
        
        # Feed data to monitor day by day
        for day in range(args.simulate_days):
            # Update metrics for each strategy
            for strategy, data in simulated_data.items():
                if day < len(data):
                    monitor.monitor.update_metrics(strategy, data[day])
            
            # Simulate a rotation every 7 days
            if day % 7 == 0 and day > 0:
                console.print(f"[yellow]Day {day}: Simulating strategy rotation[/yellow]")
                
                # Simulate allocation changes
                prev_allocations = rotator.get_current_allocations()
                new_allocations = {}
                
                for strategy in strategies:
                    # Some basic logic to simulate changes
                    prev = prev_allocations.get(strategy, 0)
                    # Adjust based on recent performance
                    recent_return = simulated_data[strategy][day]["daily_return"]
                    adjustment = 5.0 if recent_return > 0 else -5.0
                    new_allocations[strategy] = max(0, min(40, prev + adjustment))
                
                # Normalize to ensure sum is 100%
                total = sum(new_allocations.values())
                new_allocations = {k: (v / total) * 100 for k, v in new_allocations.items()}
                
                # Create a simulated rotation result
                rotation_result = {
                    "rotated": True,
                    "previous_allocations": prev_allocations,
                    "new_allocations": new_allocations,
                    "regime": "bullish" if day % 14 < 7 else "bearish",
                    "reasoning": "Simulated rotation for demonstration"
                }
                
                # Monitor the rotation
                monitor.monitor_rotation(rotation_result)
            
            progress.update(task, advance=1)
            
            # Brief pause for demonstration
            time.sleep(0.1)
    
    console.print("[green]Simulation completed successfully.[/green]")
    
    # Generate a performance report if requested
    if args.generate_report:
        console.print("\n[bold]Generating performance report...[/bold]")
        report_path = "reports/performance_report.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        report = monitor.monitor.generate_performance_report(days=args.simulate_days, save_path=report_path)
        
        if report:
            console.print(f"[green]Performance report saved to: {report_path}[/green]")
            
            # Display the report
            with open(report_path, 'r') as f:
                console.print(Panel.fit(f.read(), title="Performance Report", border_style="green"))
        else:
            console.print("[red]Failed to generate performance report.[/red]")
    
    # Plot performance if requested
    if args.plot_performance:
        console.print("\n[bold]Plotting strategy performance...[/bold]")
        plot_path = "reports/performance_plot.png"
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        
        monitor.monitor.plot_strategy_performance(days=args.simulate_days, save_path=plot_path)
        console.print(f"[green]Performance plot saved to: {plot_path}[/green]")
    
    # Display threshold alerts
    console.print("\n[bold]Performance Monitoring Thresholds:[/bold]")
    
    table = Table(title="Monitoring Thresholds")
    table.add_column("Threshold", style="cyan")
    table.add_column("Value", style="yellow")
    
    for threshold, value in monitor.monitor.thresholds.items():
        table.add_row(threshold, str(value))
    
    console.print(table)
    
    # Summary
    console.print("\n[bold green]Demo completed successfully![/bold green]")
    console.print("[italic]The Strategy Monitoring System tracks performance, generates alerts,[/italic]")
    console.print("[italic]and creates performance reports for the strategy rotation system.[/italic]")
    
    # Suggested next steps
    console.print("\n[bold]Suggested next steps:[/bold]")
    console.print("1. [cyan]Configure alert thresholds[/cyan] in the monitoring configuration file")
    console.print("2. [cyan]Set up automated monitoring[/cyan] on a schedule (e.g., daily)")
    console.print("3. [cyan]Connect to a notification system[/cyan] for real-time alerts")

if __name__ == "__main__":
    main() 