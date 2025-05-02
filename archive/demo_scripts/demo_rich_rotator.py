#!/usr/bin/env python3
"""
Demo for AI Strategy Rotation with Rich Visualizations
This script demonstrates the strategy rotation system with enhanced visualizations using rich.
"""

import argparse
import logging
import os
import sys
from decimal import Decimal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich import box

# Set up path to include trading_bot package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.ai_scoring.strategy_rotator import StrategyRotator
from trading_bot.utils.market_context_fetcher import MarketContextFetcher
from trading_bot.ai_scoring.integrated_strategy_rotator import IntegratedStrategyRotator

# Set up rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)

console = Console()

def format_percentage(value):
    """Format a decimal or float as a percentage string with color based on value."""
    if isinstance(value, Decimal):
        value = float(value)
    
    if isinstance(value, str):
        try:
            value = float(value.strip('%'))
        except:
            return value
    
    if not isinstance(value, (int, float)):
        return str(value)
    
    if value > 0:
        return f"[green]+{value:.1f}%[/green]"
    elif value < 0:
        return f"[red]{value:.1f}%[/red]"
    else:
        return f"{value:.1f}%"

def display_market_context(market_context):
    """Display market context in a rich panel with formatted data."""
    market_table = Table(box=box.ROUNDED)
    market_table.add_column("Indicator", style="cyan")
    market_table.add_column("Value", style="yellow")
    
    market_table.add_row("Market Regime", market_context.get("market_regime", "Unknown"))
    market_table.add_row("Volatility (VIX)", f"{market_context.get('vix_value', 'N/A')}")
    market_table.add_row("Trend Strength", market_context.get("trend_strength", "Unknown"))
    
    top_sectors = market_context.get("top_performing_sectors", [])
    if top_sectors:
        sector_text = ", ".join(top_sectors[:3])
        market_table.add_row("Top Sectors", sector_text)
    
    console.print(Panel(market_table, title="[bold blue]Market Context[/bold blue]", expand=False))

def display_allocations(strategies, allocations, title, capital=100000):
    """Display strategy allocations in a rich table with dollar amounts."""
    allocation_table = Table(title=title, box=box.ROUNDED)
    allocation_table.add_column("Strategy", style="cyan")
    allocation_table.add_column("Allocation %", style="yellow", justify="right")
    allocation_table.add_column("Amount ($)", style="green", justify="right")
    
    for strategy, allocation in zip(strategies, allocations):
        alloc_pct = allocation * 100
        amount = capital * allocation
        allocation_table.add_row(
            strategy, 
            f"{alloc_pct:.1f}%", 
            f"${amount:.2f}"
        )
    
    console.print(allocation_table)

def display_allocation_changes(strategies, old_allocations, new_allocations):
    """Display allocation changes with color-coded percentages."""
    changes_table = Table(title="Allocation Changes", box=box.ROUNDED)
    changes_table.add_column("Strategy", style="cyan")
    changes_table.add_column("Before", justify="right")
    changes_table.add_column("After", justify="right")
    changes_table.add_column("Change", justify="right")
    
    for strategy, old_alloc, new_alloc in zip(strategies, old_allocations, new_allocations):
        old_pct = old_alloc * 100
        new_pct = new_alloc * 100
        change = new_pct - old_pct
        changes_table.add_row(
            strategy,
            f"{old_pct:.1f}%",
            f"{new_pct:.1f}%",
            format_percentage(change)
        )
    
    console.print(changes_table)

def display_reasoning(reasoning):
    """Display AI reasoning for the allocation decisions."""
    console.print(Panel(reasoning, title="[bold blue]AI Reasoning[/bold blue]", 
                        expand=False, border_style="blue"))

def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="AI Strategy Rotation Demo with Rich Visualizations")
    parser.add_argument("--mock", action="store_true", help="Use mock responses for strategy prioritization")
    parser.add_argument("--scenario", choices=["bullish", "bearish", "volatile", "sideways"], 
                        default="bullish", help="Market scenario for mock data")
    parser.add_argument("--integrated", action="store_true", 
                        help="Use the IntegratedStrategyRotator instead of the basic StrategyRotator")
    parser.add_argument("--capital", type=float, default=100000,
                        help="Trading capital amount (default: $100,000)")
    args = parser.parse_args()
    
    # Print a welcome banner
    console.print(Panel.fit(
        "[bold yellow]AI Strategy Rotation System[/bold yellow]\n"
        "[cyan]Enhanced visualization demo using Rich[/cyan]",
        border_style="green"
    ))
    
    # List of strategies
    strategies = [
        "breakout_swing",
        "momentum",
        "mean_reversion",
        "trend_following",
        "volatility_breakout",
        "option_spreads"
    ]
    
    # Initial allocations (equal weighting)
    initial_allocations = [1/len(strategies)] * len(strategies)
    
    # Display initial allocations
    console.print("\n[bold]Initializing with equal allocations:[/bold]")
    display_allocations(strategies, initial_allocations, "Initial Allocations", args.capital)
    
    # Initialize rotator with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Initializing AI components...[/bold blue]"),
        transient=True
    ) as progress:
        task = progress.add_task("Initializing...", total=1)
        
        if args.integrated:
            rotator = IntegratedStrategyRotator(
                strategies=strategies,
                initial_allocations=initial_allocations,
                use_mock=args.mock,
                mock_scenario=args.scenario
            )
            console.print("[green]✓[/green] Initialized Integrated Strategy Rotator")
        else:
            rotator = StrategyRotator(
                strategies=strategies,
                initial_allocations=initial_allocations,
                use_mock=args.mock,
                mock_scenario=args.scenario
            )
            console.print("[green]✓[/green] Initialized Strategy Rotator")
        
        progress.update(task, completed=1)
    
    # Get market context
    console.print("\n[bold]Fetching current market context...[/bold]")
    market_context = rotator.market_context_fetcher.get_market_context()
    display_market_context(market_context)
    
    # Perform rotation with progress indicator
    console.print("\n[bold]Performing strategy rotation based on market conditions...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Evaluating strategies...[/bold blue]"),
        transient=True
    ) as progress:
        task = progress.add_task("Rotating...", total=1)
        old_allocations = rotator.get_current_allocations()
        
        rotation_result = rotator.rotate_strategies(
            market_context=market_context,
            add_reasoning=True
        )
        
        progress.update(task, completed=1)
    
    # Display results
    new_allocations = rotator.get_current_allocations()
    
    console.print("\n[bold]Rotation Complete![/bold]")
    display_allocations(strategies, new_allocations, "New Allocations", args.capital)
    display_allocation_changes(strategies, old_allocations, new_allocations)
    
    if rotation_result and "reasoning" in rotation_result:
        display_reasoning(rotation_result["reasoning"])
    
    console.print(Panel(
        "[bold green]Strategy rotation complete![/bold green]\n"
        "The AI has automatically adjusted strategy allocations based on current market conditions.",
        border_style="green"
    ))

if __name__ == "__main__":
    main() 