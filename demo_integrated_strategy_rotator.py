#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for the IntegratedStrategyRotator.

This script demonstrates the functionality of the IntegratedStrategyRotator,
which combines AI strategy prioritization with performance optimization and
dynamic constraint management.

Example usage:
    python demo_integrated_strategy_rotator.py --mock --scenario volatile --reasoning
    python demo_integrated_strategy_rotator.py --mock --scenario bullish --reasoning
"""

import os
import sys
import json
import argparse
import logging
from decimal import Decimal
from tabulate import tabulate
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from trading_bot.ai_scoring.integrated_strategy_rotator import IntegratedStrategyRotator
from trading_bot.utils.market_context_fetcher import MarketContextFetcher
from trading_bot.utils.telegram_notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize rich console
console = Console()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Demo the IntegratedStrategyRotator.')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API calls')
    parser.add_argument('--scenario', type=str, choices=['bullish', 'bearish', 'volatile', 'sideways'], 
                       default='bullish', help='Market scenario for mock mode')
    parser.add_argument('--reasoning', action='store_true', help='Include AI reasoning in output')
    parser.add_argument('--capital', type=float, default=100000.0, help='Total capital to allocate')
    return parser.parse_args()

def format_allocation_table(allocations, capital):
    """Format allocations as a rich table."""
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Strategy", style="dim")
    table.add_column("Allocation %", justify="right")
    table.add_column("Capital", justify="right")
    
    for strategy, allocation in allocations.items():
        allocation_decimal = Decimal(str(allocation)).quantize(Decimal('0.1'))
        dollar_amount = Decimal(str(capital * allocation / 100)).quantize(Decimal('0.01'))
        
        # Choose color based on allocation percentage
        if allocation >= 25:
            percent_style = "bold green"
        elif allocation >= 15:
            percent_style = "green"
        elif allocation >= 5:
            percent_style = "yellow"
        else:
            percent_style = "red"
            
        table.add_row(
            strategy, 
            f"[{percent_style}]{allocation_decimal}%[/]", 
            f"${dollar_amount:,}"
        )
    
    return table

def visualize_allocations(allocations):
    """Create a visual representation of allocations using rich."""
    max_bar_width = 40
    table = Table(show_header=False, box=None, padding=(0, 1, 0, 1))
    table.add_column("Strategy", style="dim")
    table.add_column("Bar", ratio=1)
    table.add_column("Percent", justify="right")
    
    for strategy, allocation in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
        bar_width = int((float(allocation) / 100) * max_bar_width)
        
        # Choose color based on allocation percentage
        if allocation >= 25:
            bar_color = "green"
        elif allocation >= 15:
            bar_color = "blue"
        elif allocation >= 5:
            bar_color = "yellow"
        else:
            bar_color = "red"
            
        bar = Text("■" * bar_width)
        bar.stylize(f"bold {bar_color}")
        
        table.add_row(
            strategy,
            bar,
            f"{allocation:.1f}%"
        )
    
    return table

def create_performance_table(performance_data):
    """Create a rich table to display performance metrics."""
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Strategy", style="dim")
    table.add_column("Return %", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Max DD", justify="right")
    table.add_column("Win Rate", justify="right")
    
    for strategy, metrics in sorted(performance_data.items(), key=lambda x: x[1]['return'], reverse=True):
        # Style based on return
        if metrics['return'] >= 12:
            return_style = "bold green"
        elif metrics['return'] >= 8:
            return_style = "green"
        elif metrics['return'] >= 5:
            return_style = "yellow"
        else:
            return_style = "red"
            
        # Style based on Sharpe ratio
        if metrics['sharpe'] >= 1.7:
            sharpe_style = "bold green"
        elif metrics['sharpe'] >= 1.3:
            sharpe_style = "green"
        elif metrics['sharpe'] >= 1.0:
            sharpe_style = "yellow"
        else:
            sharpe_style = "red"
            
        # Style based on max drawdown
        if metrics['max_drawdown'] <= 7:
            dd_style = "bold green"
        elif metrics['max_drawdown'] <= 9:
            dd_style = "green"
        elif metrics['max_drawdown'] <= 12:
            dd_style = "yellow"
        else:
            dd_style = "red"
            
        # Style based on win rate
        if metrics['win_rate'] >= 65:
            wr_style = "bold green"
        elif metrics['win_rate'] >= 58:
            wr_style = "green"
        elif metrics['win_rate'] >= 50:
            wr_style = "yellow"
        else:
            wr_style = "red"
        
        table.add_row(
            strategy,
            f"[{return_style}]{metrics['return']:.1f}%[/]",
            f"[{sharpe_style}]{metrics['sharpe']:.2f}[/]",
            f"[{dd_style}]{metrics['max_drawdown']:.1f}%[/]",
            f"[{wr_style}]{metrics['win_rate']:.1f}%[/]"
        )
    
    return table

def create_mock_performance_data(strategies):
    """Generate mock performance data for testing."""
    performance_data = {}
    # Simulating performance metrics for the last 30 days
    for strategy in strategies:
        # Different strategies have different performance profiles
        if strategy == 'momentum':
            return_val = 12.5
            sharpe = 1.8
            max_dd = 8.2
            win_rate = 65.0
        elif strategy == 'trend_following':
            return_val = 9.8
            sharpe = 1.5
            max_dd = 7.5
            win_rate = 62.0
        elif strategy == 'mean_reversion':
            return_val = 6.2
            sharpe = 1.1
            max_dd = 9.8
            win_rate = 55.0
        elif strategy == 'breakout_swing':
            return_val = 11.0
            sharpe = 1.6
            max_dd = 8.8
            win_rate = 60.0
        elif strategy == 'volatility_breakout':
            return_val = 14.2
            sharpe = 1.7
            max_dd = 10.2
            win_rate = 58.0
        elif strategy == 'option_spreads':
            return_val = 8.5
            sharpe = 1.9
            max_dd = 6.5
            win_rate = 70.0
        else:
            return_val = 7.0
            sharpe = 1.2
            max_dd = 9.0
            win_rate = 56.0
            
        performance_data[strategy] = {
            'return': return_val,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate
        }
    
    return performance_data

def create_allocation_change_table(previous, new, strategies):
    """Create a table showing allocation changes."""
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Strategy", style="dim")
    table.add_column("Previous", justify="right")
    table.add_column("New", justify="right")
    table.add_column("Change", justify="right")
    
    for strategy in strategies:
        old_alloc = previous.get(strategy, 0)
        new_alloc = new.get(strategy, 0)
        change = new_alloc - old_alloc
        
        # Style based on change direction and magnitude
        if change > 10:
            change_style = "bold green"
            arrow = "🔺"
        elif change > 0:
            change_style = "green"
            arrow = "▲"
        elif change < -10:
            change_style = "bold red"
            arrow = "🔻"
        elif change < 0:
            change_style = "red"
            arrow = "▼"
        else:
            change_style = "white"
            arrow = "◆"
            
        table.add_row(
            strategy,
            f"{old_alloc:.1f}%",
            f"{new_alloc:.1f}%",
            f"[{change_style}]{arrow} {change:+.1f}%[/]"
        )
    
    return table

def main():
    """Run the integrated strategy rotator demo."""
    args = parse_args()
    total_capital = args.capital
    
    # Define strategies and initial allocations
    strategies = [
        'momentum',
        'trend_following',
        'mean_reversion',
        'breakout_swing',
        'volatility_breakout',
        'option_spreads'
    ]
    
    # Initial equal allocation
    initial_allocations = {strategy: 100.0 / len(strategies) for strategy in strategies}
    
    # Create mock performance data
    performance_data = create_mock_performance_data(strategies)
    
    console.print(Panel.fit(
        Text("INTEGRATED AI STRATEGY ROTATOR DEMO", style="bold white"),
        border_style="cyan",
        padding=(1, 2)
    ))
    
    console.print("\n[bold]Initializing AI Strategy Rotator...[/]")
    if args.mock:
        console.print("📝 [yellow]Note:[/] Using mock responses for strategy prioritization")
        console.print(f"📊 Market scenario: [bold blue]{args.scenario}[/]")
    
    # Initialize with progress spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Initializing components..."),
        console=console
    ) as progress:
        task = progress.add_task("", total=None)
        
        # Initialize the IntegratedStrategyRotator
        rotator = IntegratedStrategyRotator(
            strategies=strategies,
            initial_allocations=initial_allocations,
            use_mock=args.mock,
            mock_scenario=args.scenario
        )
        
        # Set performance metrics
        rotator.update_performance_metrics(performance_data)
    
    console.print(f"\n✅ Initialized with [bold]{len(strategies)}[/] strategies")
    console.print(f"💰 Total capital to allocate: [bold green]${total_capital:,.2f}[/]")
    
    # Display performance metrics
    console.print("\n[bold magenta]📊 STRATEGY PERFORMANCE METRICS:[/]")
    console.print(create_performance_table(performance_data))
    
    # Display current allocations
    console.print("\n[bold cyan]📊 CURRENT ALLOCATIONS:[/]")
    console.print(format_allocation_table(rotator.current_allocations, total_capital))
    console.print("\n[cyan]Visualization:[/]")
    console.print(visualize_allocations(rotator.current_allocations))
    
    # Get current market context
    console.print("\n[bold green]🌎 CURRENT MARKET CONTEXT:[/]")
    market_context = rotator.market_context_fetcher.get_market_context()
    market_summary = rotator.market_context_fetcher.get_market_summary(market_context)
    console.print(Panel(market_summary, border_style="green"))
    
    # Perform strategy rotation
    console.print("\n[bold blue]🔄 PERFORMING STRATEGY ROTATION BASED ON MARKET CONDITIONS[/]")
    console.print("[dim]This may take a few seconds if using live evaluations...[/]")
    
    # Rotate strategies with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Rotating strategies..."),
        console=console
    ) as progress:
        task = progress.add_task("", total=None)
        
        # Rotate strategies
        new_allocations, reasoning = rotator.rotate_strategies(
            market_context=market_context,
            include_reasoning=args.reasoning
        )
    
    # Display results
    console.print("\n[bold green]✅ STRATEGY ROTATION COMPLETE[/]")
    
    # Display new allocations
    console.print("\n[bold cyan]📊 NEW STRATEGY ALLOCATIONS:[/]")
    console.print(format_allocation_table(new_allocations, total_capital))
    console.print("\n[cyan]Visualization:[/]")
    console.print(visualize_allocations(new_allocations))
    
    # Show allocation changes
    console.print("\n[bold cyan]📈 ALLOCATION CHANGES:[/]")
    console.print(create_allocation_change_table(rotator.previous_allocations, new_allocations, strategies))
    
    # Display AI reasoning if requested
    if args.reasoning and reasoning:
        console.print("\n[bold yellow]🧠 AI REASONING FOR NEW ALLOCATIONS:[/]")
        console.print(Panel(reasoning, border_style="yellow"))
    
    console.print(Panel(
        "\n".join([
            "✨ [bold]Demo complete![/] The AI has automatically adjusted strategy allocations",
            "based on current market conditions, performance metrics, and risk constraints.",
            "This system can be integrated into your trading platform to enable",
            "dynamic strategy rotation as market conditions evolve."
        ]),
        border_style="green",
        padding=(1, 2)
    ))

if __name__ == "__main__":
    main() 