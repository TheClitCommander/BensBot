#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Strategy Prioritizer Demo

This script demonstrates the use of the EnhancedStrategyPrioritizer, which leverages
language models to analyze market conditions and optimize strategy selection
with contextual awareness, explainability, and risk management.
"""

import os
import json
import time
import logging
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live

from trading_bot.ai_scoring.enhanced_strategy_prioritizer import EnhancedStrategyPrioritizer
from trading_bot.ai_scoring.prioritizer_integration import PrioritizerIntegration
from trading_bot.utils.market_context_fetcher import MarketContextFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/enhanced_prioritizer_demo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class EnhancedPrioritizerDemo:
    """Demo for the Enhanced Strategy Prioritizer system."""
    
    def __init__(
        self,
        api_key: str = None,
        use_mock: bool = False,
        update_interval: int = 60,  # seconds
        simulate_market_changes: bool = True,
        record_allocations: bool = True
    ):
        """
        Initialize the demo.
        
        Args:
            api_key: API key for language model service
            use_mock: Whether to use mock responses
            update_interval: How often to update (seconds)
            simulate_market_changes: Whether to simulate market changes
            record_allocations: Whether to record allocations to CSV
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.use_mock = use_mock
        self.update_interval = update_interval
        self.simulate_market_changes = simulate_market_changes
        self.record_allocations = record_allocations
        
        # Set up paths
        self.data_dir = "demo_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Define strategies
        self.strategies = [
            "momentum",
            "trend_following",
            "breakout_swing",
            "mean_reversion",
            "volatility_breakout",
            "option_spreads"
        ]
        
        # Initialize integration
        self.integration = PrioritizerIntegration(
            strategies=self.strategies,
            api_key=self.api_key,
            use_mock=self.use_mock,
            data_dir=self.data_dir
        )
        
        # Initialize market context fetcher
        self.market_fetcher = MarketContextFetcher()
        
        # State variables
        self.market_context = None
        self.allocations = None
        self.allocation_history = []
        self.allocation_changes = {}
        self.simulated_performance = {}
        self.current_scenario = "normal"
        self.running = False
        
        # Rich layout
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=6)
        )
        self.layout["main"].split_row(
            Layout(name="allocations", ratio=2),
            Layout(name="explanation", ratio=3)
        )
        
        logger.info("EnhancedPrioritizerDemo initialized")
    
    def run(self):
        """Run the demo with live visualization."""
        self.running = True
        
        try:
            with Live(self.layout, refresh_per_second=4) as self.live:
                # Initial update
                self._update_display()
                
                while self.running:
                    # Update allocations
                    self._update_allocations()
                    
                    # Update display
                    self._update_display()
                    
                    # Sleep
                    time.sleep(self.update_interval)
        except KeyboardInterrupt:
            console.print("[yellow]Demo stopped by user[/yellow]")
            self.running = False
        
        # Final update
        self._save_results()
    
    def _update_allocations(self):
        """Update strategy allocations and market context."""
        try:
            # Simulate market changes if enabled
            if self.simulate_market_changes:
                self._simulate_market_changes()
            
            # Update allocations
            start_time = time.time()
            self.allocations = self.integration.get_allocations(force_refresh=True)
            end_time = time.time()
            
            logger.info(f"Updated allocations in {end_time - start_time:.2f} seconds")
            
            # Calculate allocation changes
            self.allocation_changes = {}
            if len(self.allocation_history) > 0:
                previous = self.allocation_history[-1]
                for strategy, allocation in self.allocations.items():
                    if strategy in previous:
                        self.allocation_changes[strategy] = allocation - previous[strategy]
            
            # Add to history
            self.allocation_history.append(self.allocations.copy())
            
            # Simulate performance metrics based on allocations
            self._simulate_performance()
            
            # Record performance feedback
            self.integration.record_performance(self.simulated_performance)
            
        except Exception as e:
            logger.error(f"Error updating allocations: {e}")
    
    def _simulate_market_changes(self):
        """Simulate market condition changes."""
        # Occasionally change market scenario
        if random.random() < 0.1:  # 10% chance of scenario change
            scenarios = ["normal", "bullish", "bearish", "volatile", "sideways"]
            self.current_scenario = random.choice(
                [s for s in scenarios if s != self.current_scenario]
            )
            logger.info(f"Market scenario changed to: {self.current_scenario}")
        
        # Use market context fetcher to get base context
        market_context = self.market_fetcher.get_market_context()
        
        # Modify based on scenario
        if self.current_scenario == "bullish":
            market_context["regime"] = {"primary_regime": "bullish"}
            market_context["vix"] = {"value": max(10, random.normalvariate(15, 2))}
            market_context["trend_strength"] = {"value": random.uniform(0.7, 0.9)}
        elif self.current_scenario == "bearish":
            market_context["regime"] = {"primary_regime": "bearish"}
            market_context["vix"] = {"value": random.normalvariate(25, 5)}
            market_context["trend_strength"] = {"value": random.uniform(0.6, 0.8)}
        elif self.current_scenario == "volatile":
            market_context["regime"] = {"primary_regime": "volatile"}
            market_context["vix"] = {"value": random.normalvariate(30, 5)}
            market_context["trend_strength"] = {"value": random.uniform(0.3, 0.6)}
        elif self.current_scenario == "sideways":
            market_context["regime"] = {"primary_regime": "sideways"}
            market_context["vix"] = {"value": random.normalvariate(18, 3)}
            market_context["trend_strength"] = {"value": random.uniform(0.1, 0.3)}
        else:  # normal
            market_context["regime"] = {"primary_regime": "neutral"}
            market_context["vix"] = {"value": random.normalvariate(20, 3)}
            market_context["trend_strength"] = {"value": random.uniform(0.4, 0.6)}
        
        # Store context
        self.market_context = market_context
    
    def _simulate_performance(self):
        """Simulate performance metrics for the current allocations."""
        # Create realistic-looking performance metrics
        # Return calculation based on strategy allocation and scenario
        base_returns = {
            "momentum": {
                "bullish": random.normalvariate(0.08, 0.05),
                "bearish": random.normalvariate(-0.06, 0.08),
                "volatile": random.normalvariate(-0.02, 0.15),
                "sideways": random.normalvariate(0.01, 0.05),
                "normal": random.normalvariate(0.03, 0.07)
            },
            "trend_following": {
                "bullish": random.normalvariate(0.07, 0.04),
                "bearish": random.normalvariate(0.04, 0.06),
                "volatile": random.normalvariate(-0.04, 0.12),
                "sideways": random.normalvariate(-0.02, 0.04),
                "normal": random.normalvariate(0.02, 0.05)
            },
            "breakout_swing": {
                "bullish": random.normalvariate(0.06, 0.07),
                "bearish": random.normalvariate(-0.04, 0.08),
                "volatile": random.normalvariate(0.08, 0.14),
                "sideways": random.normalvariate(-0.03, 0.06),
                "normal": random.normalvariate(0.02, 0.06)
            },
            "mean_reversion": {
                "bullish": random.normalvariate(0.02, 0.04),
                "bearish": random.normalvariate(-0.03, 0.07),
                "volatile": random.normalvariate(0.06, 0.10),
                "sideways": random.normalvariate(0.05, 0.03),
                "normal": random.normalvariate(0.03, 0.04)
            },
            "volatility_breakout": {
                "bullish": random.normalvariate(0.03, 0.06),
                "bearish": random.normalvariate(0.02, 0.08),
                "volatile": random.normalvariate(0.12, 0.18),
                "sideways": random.normalvariate(-0.04, 0.05),
                "normal": random.normalvariate(0.01, 0.07)
            },
            "option_spreads": {
                "bullish": random.normalvariate(0.04, 0.03),
                "bearish": random.normalvariate(0.03, 0.04),
                "volatile": random.normalvariate(0.08, 0.08),
                "sideways": random.normalvariate(0.06, 0.03),
                "normal": random.normalvariate(0.04, 0.03)
            }
        }
        
        # Calculate weighted return
        weighted_return = 0
        for strategy, allocation in self.allocations.items():
            if strategy in base_returns:
                scenario = self.current_scenario if self.current_scenario in base_returns[strategy] else "normal"
                strategy_return = base_returns[strategy][scenario]
                weighted_return += (strategy_return * allocation / 100)
        
        # Generate sharpe ratio based on return
        volatility = 0.1  # Assumed annual volatility
        sharpe = weighted_return / volatility * np.sqrt(252)  # Annualized
        
        # Generate other metrics
        self.simulated_performance = {
            "return": weighted_return,
            "sharpe_ratio": max(0, sharpe),
            "drawdown": -abs(min(0, weighted_return) * random.uniform(1.5, 3.0)),
            "win_rate": 50 + (weighted_return * 100),  # Higher returns mean higher win rate
            "volatility": volatility
        }
    
    def _update_display(self):
        """Update the rich display layout."""
        # Header
        self.layout["header"].update(
            Panel(
                f"[bold]Enhanced Strategy Prioritizer Demo[/bold] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="blue"
            )
        )
        
        # Allocations table
        if self.allocations:
            alloc_table = Table(title="Strategy Allocations")
            alloc_table.add_column("Strategy", style="cyan")
            alloc_table.add_column("Allocation %", style="green")
            alloc_table.add_column("Change", style="yellow")
            alloc_table.add_column("Simulated Return", style="magenta")
            
            for strategy in sorted(self.allocations.keys()):
                allocation = self.allocations[strategy]
                change = self.allocation_changes.get(strategy, 0)
                
                # Get strategy-specific return if available
                strategy_return = None
                if strategy in self.simulated_performance.get("strategy_returns", {}):
                    strategy_return = self.simulated_performance["strategy_returns"][strategy]
                
                # Format change with arrows
                change_str = ""
                if change > 0:
                    change_str = f"[green]↑ {change:.1f}%[/green]"
                elif change < 0:
                    change_str = f"[red]↓ {abs(change):.1f}%[/red]"
                else:
                    change_str = "[yellow]―[/yellow]"
                
                # Format return
                return_str = ""
                if strategy_return is not None:
                    color = "green" if strategy_return >= 0 else "red"
                    return_str = f"[{color}]{strategy_return:.2%}[/{color}]"
                
                alloc_table.add_row(
                    strategy,
                    f"{allocation:.1f}%",
                    change_str,
                    return_str
                )
                
            self.layout["allocations"].update(alloc_table)
        else:
            self.layout["allocations"].update(Panel("No allocations yet", title="Waiting for data..."))
        
        # Explanation panel
        annotated = self.integration.get_annotated_allocations()
        explanation_content = ""
        
        # Add market context
        if self.market_context:
            regime = self.market_context.get("regime", {}).get("primary_regime", "unknown")
            vix = self.market_context.get("vix", {}).get("value", 0)
            trend = self.market_context.get("trend_strength", {}).get("value", 0)
            
            explanation_content += f"[bold cyan]Market Context:[/bold cyan]\n"
            explanation_content += f"Regime: [yellow]{regime}[/yellow], "
            explanation_content += f"VIX: [yellow]{vix:.1f}[/yellow], "
            explanation_content += f"Trend Strength: [yellow]{trend:.2f}[/yellow]\n\n"
        
        # Add explanation
        if annotated.get("explanation"):
            explanation_content += f"[bold green]AI Explanation:[/bold green]\n"
            explanation_content += f"{annotated['explanation']}\n\n"
        
        # Add reasoning points
        if annotated.get("reasoning"):
            explanation_content += f"[bold blue]Reasoning:[/bold blue]\n"
            for point in annotated["reasoning"]:
                explanation_content += f"• {point}\n"
            explanation_content += "\n"
        
        # Add risk information
        risk_level = annotated.get("risk_level", "normal")
        risk_color = {
            "normal": "green",
            "elevated": "yellow",
            "high": "orange",
            "critical": "red"
        }.get(risk_level, "white")
        
        explanation_content += f"[bold {risk_color}]Risk Level: {risk_level.upper()}[/bold {risk_color}]\n"
        
        if annotated.get("risk_warnings"):
            explanation_content += "[bold red]Risk Warnings:[/bold red]\n"
            for warning in annotated["risk_warnings"]:
                explanation_content += f"• {warning}\n"
        
        # Add performance metrics
        if self.simulated_performance:
            explanation_content += "\n[bold magenta]Simulated Performance:[/bold magenta]\n"
            return_val = self.simulated_performance.get("return", 0)
            return_color = "green" if return_val >= 0 else "red"
            
            explanation_content += f"Return: [{return_color}]{return_val:.2%}[/{return_color}], "
            explanation_content += f"Sharpe: {self.simulated_performance.get('sharpe_ratio', 0):.2f}, "
            explanation_content += f"Drawdown: {self.simulated_performance.get('drawdown', 0):.2%}, "
            explanation_content += f"Win Rate: {self.simulated_performance.get('win_rate', 0):.1f}%"
        
        self.layout["explanation"].update(
            Panel(explanation_content, title="Strategy Analysis & Explanation")
        )
        
        # Footer with status and scenario info
        if self.running:
            status = f"Running - Update Interval: {self.update_interval}s - Scenario: {self.current_scenario.capitalize()}"
        else:
            status = "Stopped"
            
        footer_content = f"[bold]Status:[/bold] {status}\n"
        footer_content += f"[bold]API Mode:[/bold] {'Mock' if self.use_mock else 'Live'}\n"
        
        if self.simulated_performance:
            portfolio_value = 100000 * (1 + self.simulated_performance.get("return", 0))
            footer_content += f"[bold]Simulated Portfolio Value:[/bold] ${portfolio_value:,.2f}"
            
        self.layout["footer"].update(Panel(footer_content, style="dim"))
    
    def _save_results(self):
        """Save allocation history and results."""
        if self.record_allocations and self.allocation_history:
            # Export allocations to CSV
            csv_path = os.path.join(self.data_dir, "allocation_history.csv")
            
            # Create DataFrame
            results_data = []
            
            for i, alloc in enumerate(self.allocation_history):
                timestamp = datetime.now() - timedelta(seconds=i*self.update_interval)
                row = {"timestamp": timestamp}
                
                for strategy, allocation in alloc.items():
                    row[strategy] = allocation
                    
                results_data.append(row)
                
            # Save to CSV (in reverse order to have newest last)
            pd.DataFrame(results_data[::-1]).to_csv(csv_path, index=False)
            console.print(f"[green]Allocation history saved to {csv_path}[/green]")
            
            # Export explained allocations
            self.integration.export_allocations_to_csv(
                os.path.join(self.data_dir, "annotated_allocations.csv")
            )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demo for the Enhanced Strategy Prioritizer system"
    )
    
    parser.add_argument(
        "--use-mock",
        action="store_true",
        help="Use mock responses instead of calling LLM API"
    )
    
    parser.add_argument(
        "--update-interval",
        type=int, 
        default=60,
        help="Update interval in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--no-simulation",
        action="store_true",
        help="Disable market scenario simulation"
    )
    
    return parser.parse_args()


# Ensure we have random for simulation
import random

# Main function
def main():
    """Main function to run the demo."""
    # Parse command line arguments
    args = parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Print introduction
    console.print(Panel(
        "[bold green]Enhanced Strategy Prioritizer Demo[/bold green]\n\n"
        "This demo showcases the AI-driven strategy prioritization system "
        "that uses language models to analyze market conditions and optimize "
        "strategy selection with contextual awareness, explainability, and risk management.",
        title="Welcome",
        expand=False
    ))
    
    # Display configuration
    console.print("[cyan]Configuration:[/cyan]")
    console.print(f"• API Mode: {'Mock' if args.use_mock else 'Live'}")
    console.print(f"• Update Interval: {args.update_interval} seconds")
    console.print(f"• Market Simulation: {'Disabled' if args.no_simulation else 'Enabled'}")
    console.print("")
    
    # Create and run the demo
    demo = EnhancedPrioritizerDemo(
        use_mock=args.use_mock,
        update_interval=args.update_interval,
        simulate_market_changes=not args.no_simulation
    )
    
    # Start the demo
    console.print("[yellow]Starting demo... Press Ctrl+C to stop[/yellow]")
    demo.run()


if __name__ == "__main__":
    main() 