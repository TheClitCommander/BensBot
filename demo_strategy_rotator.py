#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Rotation System Demo

This script demonstrates the AI-powered strategy rotation system
in a simple terminal interface with visualizations.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StrategyRotatorDemo")

# Try to load colorama for better terminal colors
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    print("Install colorama for colored output: pip install colorama")

# Try to load ASCII art for better visualizations
try:
    from pyfiglet import Figlet
    HAS_FIGLET = True
except ImportError:
    HAS_FIGLET = False
    print("Install pyfiglet for ASCII art: pip install pyfiglet")

# Load environment variables
load_dotenv()

# Import our modules
from trading_bot.ai_scoring.strategy_prioritizer import StrategyPrioritizer
from trading_bot.ai_scoring.strategy_rotator import StrategyRotator
from trading_bot.utils.market_context_fetcher import get_current_market_context, get_mock_market_context


def print_header(text):
    """Print a header with optional ASCII art."""
    if HAS_FIGLET:
        f = Figlet(font='slant')
        print(f.renderText(text))
    else:
        print("\n" + "=" * 60)
        print(f" {text} ".center(60, "="))
        print("=" * 60)


def print_colored(text, color=None, style=None):
    """Print colored and styled text if colorama is available."""
    if not HAS_COLORAMA:
        print(text)
        return

    color_map = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE
    }
    
    style_map = {
        "bold": Style.BRIGHT,
        "dim": Style.DIM,
        "normal": Style.NORMAL
    }
    
    color_code = color_map.get(color, "")
    style_code = style_map.get(style, "")
    
    print(f"{style_code}{color_code}{text}{Style.RESET_ALL}")


def print_bar_chart(data, title="", max_width=50):
    """Print a simple ASCII bar chart."""
    if not data:
        return
    
    print_colored(f"\n{title}", "cyan", "bold")
    
    # Find the maximum value and label length
    max_val = max(data.values())
    max_label_len = max(len(str(label)) for label in data.keys())
    
    # Print each bar
    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
        # Calculate bar width
        bar_width = int((value / max_val) * max_width) if max_val > 0 else 0
        
        # Choose color based on value
        if value >= max_val * 0.8:
            color = "green"
        elif value >= max_val * 0.4:
            color = "yellow"
        else:
            color = "red"
        
        # Format the label and value
        label_str = f"{label}:".ljust(max_label_len + 1)
        value_str = f" {value:.1f}%"
        
        # Print the bar
        print(f"{label_str} ", end="")
        print_colored("█" * bar_width + value_str, color)


def visualize_rotation_results(old_allocation, new_allocation):
    """Visualize the changes in allocations."""
    print_colored("\nAllocation Changes:", "cyan", "bold")
    
    # Find all strategies
    all_strategies = set(list(old_allocation.keys()) + list(new_allocation.keys()))
    
    # Calculate the maximum label length
    max_label_len = max(len(str(strategy)) for strategy in all_strategies)
    
    # Print each strategy's change
    for strategy in sorted(all_strategies):
        old_val = old_allocation.get(strategy, 0)
        new_val = new_allocation.get(strategy, 0)
        change = new_val - old_val
        
        # Format the label
        label_str = f"{strategy}:".ljust(max_label_len + 1)
        
        # Choose color based on change
        if change > 5:
            color = "green"
            arrow = "▲"
        elif change < -5:
            color = "red"
            arrow = "▼"
        elif change > 0:
            color = "green"
            arrow = "△"
        elif change < 0:
            color = "red"
            arrow = "▽"
        else:
            color = "white"
            arrow = "○"
        
        # Format the change
        change_str = f"{arrow} {old_val:.1f}% → {new_val:.1f}% ({change:+.1f}%)"
        
        # Print the change
        print(f"{label_str} ", end="")
        print_colored(change_str, color)


def format_market_context(market_context):
    """Format the market context data for display."""
    if not market_context:
        return "No market context available."
    
    output = []
    
    # Add market summary
    if "market_summary" in market_context:
        output.append(f"Market Summary: {market_context['market_summary']}")
    
    # Add volatility information
    if "volatility_index" in market_context:
        output.append(f"VIX: {market_context['volatility_index']:.2f}")
    
    # Add market regime
    if "market_regime" in market_context:
        output.append(f"Market Regime: {market_context['market_regime']}")
    
    # Add sector information
    if "top_sectors" in market_context and market_context["top_sectors"]:
        output.append(f"Top Sectors: {', '.join(market_context['top_sectors'])}")
    
    return "\n".join(output)


def run_demo(args):
    """Run the strategy rotation demo."""
    print_header("AI Strategy Rotator")
    print_colored("This demo shows how AI can automatically adjust trading strategy allocations based on market conditions.", "cyan")
    
    # Available strategies
    strategies = [
        "breakout_swing",
        "momentum",
        "mean_reversion",
        "trend_following",
        "volatility_breakout",
        "option_spreads"
    ]
    
    # Initial allocations
    initial_allocations = {
        "breakout_swing": 20,
        "momentum": 20,
        "mean_reversion": 15,
        "trend_following": 25,
        "volatility_breakout": 10,
        "option_spreads": 10
    }
    
    # Use mock data if specified or if we don't have API keys
    use_mock = args.mock or os.getenv("OPENAI_API_KEY") is None
    
    # Initialize the strategy prioritizer
    print_colored("\nInitializing AI Strategy Prioritizer...", "blue")
    prioritizer = StrategyPrioritizer(
        available_strategies=strategies,
        use_mock=use_mock
    )
    
    # Initialize the strategy rotator
    print_colored("Initializing Strategy Rotator...", "blue")
    config_path = args.config if args.config else None
    rotator = StrategyRotator(
        strategies=strategies,
        initial_allocations=initial_allocations,
        strategy_prioritizer=prioritizer,
        portfolio_value=args.portfolio,
        enable_guardrails=args.guardrails,
        config_path=config_path
    )
    
    config_status = f"with config from {args.config}" if args.config else "with default config"
    guardrails_status = "enabled" if args.guardrails else "disabled"
    print_colored(f"✓ Initialization complete. Using {'mock' if use_mock else 'live'} data with risk guardrails {guardrails_status} {config_status}.", "green")
    
    # Get current market context
    print_colored("\nFetching current market context...", "blue")
    if use_mock:
        market_context = get_mock_market_context(args.scenario)
        print_colored(f"Using mock {args.scenario} market scenario.", "yellow")
    else:
        market_context = get_current_market_context()
        print_colored("Using live market data.", "green")
    
    # Print market context
    print_colored("\nCurrent Market Context:", "cyan", "bold")
    print(format_market_context(market_context))
    
    # Get current allocations
    current_allocations = rotator.get_allocations()
    
    # Print current allocations
    print_colored("\nCurrent Strategy Allocations:", "cyan", "bold")
    for strategy, allocation in current_allocations.items():
        dollar_allocation = (allocation / 100.0) * rotator.portfolio_value
        print(f"{strategy}: {allocation:.1f}% (${dollar_allocation:,.2f})")
    
    # Print bar chart
    print_bar_chart(current_allocations, "Current Allocations")
    
    # Perform rotation
    print_colored("\nPerforming strategy rotation based on market conditions...", "blue")
    print_colored("(This may take a few seconds if using live GPT-4 evaluations)\n", "yellow")
    
    # Simulate a portfolio drawdown if specified
    if args.drawdown > 0:
        original_value = rotator.portfolio_value
        drawdown_value = original_value * (1 - args.drawdown / 100)
        print_colored(f"Simulating a {args.drawdown:.1f}% portfolio drawdown (${original_value:,.2f} → ${drawdown_value:,.2f})", "yellow")
        rotator.update_portfolio_value(drawdown_value)
    
    # Start timer
    start_time = time.time()
    
    # Perform rotation
    result = rotator.rotate_strategies(market_context, force_rotation=True)
    
    # End timer
    end_time = time.time()
    elapsed = end_time - start_time
    
    if result["status"] == "success":
        print_colored(f"✓ Rotation completed successfully in {elapsed:.2f} seconds.", "green")
        
        # If guardrails are enabled, show the risk assessment
        if args.guardrails:
            risk_level = result["results"]["risk_level"]
            risk_color = "green" if risk_level == "low" else "yellow" if risk_level == "medium" else "red"
            print_colored(f"\nRisk Assessment: {risk_level.upper()}", risk_color, "bold")
            
            if hasattr(rotator, "portfolio_drawdown") and rotator.portfolio_drawdown > 0:
                print_colored(f"Portfolio Drawdown: {rotator.portfolio_drawdown:.2f}%", 
                             "yellow" if rotator.portfolio_drawdown < 10 else "red")
        
        # Get target allocations (before constraints)
        target_allocations = result["results"]["target_allocations"]
        
        # Get new allocations (after constraints)
        new_allocations = rotator.get_allocations()
        
        # Print new allocations
        print_colored("\nNew Strategy Allocations:", "cyan", "bold")
        for strategy, allocation in new_allocations.items():
            dollar_allocation = (allocation / 100.0) * rotator.portfolio_value
            print(f"{strategy}: {allocation:.1f}% (${dollar_allocation:,.2f})")
        
        # Print bar chart
        print_bar_chart(new_allocations, "New Allocations")
        
        # Visualize changes
        visualize_rotation_results(current_allocations, new_allocations)
        
        # If guardrails were applied, show the differences between target and constrained allocations
        if args.guardrails:
            print_colored("\nGuardrail Adjustments:", "cyan", "bold")
            any_adjustments = False
            
            for strategy in strategies:
                target = target_allocations.get(strategy, 0)
                actual = new_allocations.get(strategy, 0)
                
                if abs(target - actual) > 0.5:  # Only show meaningful differences
                    any_adjustments = True
                    adjustment = actual - target
                    adjustment_str = f"{strategy}: {target:.1f}% → {actual:.1f}% ({adjustment:+.1f}%)"
                    print_colored(adjustment_str, "yellow")
            
            if not any_adjustments:
                print_colored("No significant guardrail adjustments were needed.", "green")
        
        # Print reasoning if available
        if args.reasoning:
            prioritization = prioritizer.prioritize_strategies(market_context)
            if "reasoning" in prioritization:
                print_colored("\nAI Reasoning:", "cyan", "bold")
                for strategy, reasoning in prioritization["reasoning"].items():
                    print_colored(f"{strategy}:", "yellow", "bold")
                    print(f"  {reasoning}")
                    print()
    else:
        print_colored(f"✗ Rotation failed: {result['message']}", "red")
    
    print_colored("\nDemo completed!", "green", "bold")
    print("You've seen how AI can automatically adjust strategy allocations based on market conditions.")
    if args.guardrails:
        print("The allocation guardrails provided risk management to ensure safer allocations.")
    print("This same technology can be integrated into your trading platform for dynamic strategy rotation.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Demo of AI-powered strategy rotation")
    
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real API calls")
    parser.add_argument("--scenario", choices=["bullish", "bearish", "volatile", "sideways"], default="sideways", 
                        help="Market scenario to simulate when using mock data")
    parser.add_argument("--portfolio", type=float, default=100000.0, help="Portfolio value")
    parser.add_argument("--reasoning", action="store_true", help="Show detailed reasoning from the AI")
    parser.add_argument("--guardrails", action="store_true", default=True, 
                        help="Enable allocation guardrails for risk management")
    parser.add_argument("--no-guardrails", dest="guardrails", action="store_false", 
                        help="Disable allocation guardrails")
    parser.add_argument("--drawdown", type=float, default=0.0, 
                        help="Simulate a portfolio drawdown percentage (e.g., 10 for 10%)")
    parser.add_argument("--config", type=str, 
                        help="Path to strategy rotator configuration file")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_demo(args) 