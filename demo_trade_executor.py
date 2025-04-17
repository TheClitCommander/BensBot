#!/usr/bin/env python3
"""
Demo Trade Executor - Example of using the TradeExecutor with RegimeAwareStrategyPrioritizer

This demo shows how to integrate the regime-aware strategy prioritization with
the trade execution system to implement a complete trading workflow.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live

# Import our components
from trading_bot.ai_scoring.regime_aware_strategy_prioritizer import RegimeAwareStrategyPrioritizer
from trading_bot.utils.market_context_fetcher import MarketContextFetcher
from trading_bot.ai_scoring.trade_executor import TradeExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo_trade_executor")

# Initialize Rich console
console = Console()


def get_mock_market_data():
    """Generate mock market data for demonstration purposes."""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "V", "JPM", "SPY"]
    
    market_data = {}
    base_price = {
        "AAPL": 180.0, "MSFT": 320.0, "GOOGL": 140.0, "AMZN": 135.0, 
        "META": 370.0, "TSLA": 240.0, "NVDA": 850.0, "V": 270.0, 
        "JPM": 190.0, "SPY": 480.0
    }
    
    # Add some random price movement
    for symbol in symbols:
        change = np.random.normal(0, 0.015)  # Random price change with 1.5% standard deviation
        price = base_price[symbol] * (1 + change)
        market_data[symbol] = {
            "close": price,
            "volume": int(np.random.normal(5000000, 1000000)),
            "high": price * (1 + abs(np.random.normal(0, 0.005))),
            "low": price * (1 - abs(np.random.normal(0, 0.005))),
            "open": price * (1 + np.random.normal(0, 0.003))
        }
    
    # Add overall market data
    market_data["market_regime"] = "moderately_bullish"
    market_data["volatility_index"] = 15.7
    market_data["sector_performance"] = {
        "Technology": 0.8,
        "Consumer Cyclical": 0.3,
        "Financial Services": 0.5,
        "Healthcare": -0.2,
        "Energy": -0.5
    }
    
    return market_data


def generate_mock_signals(market_data, strategy_allocations):
    """Generate mock trading signals based on strategy allocations."""
    signals = []
    
    # Generate signals for top 3 strategies
    top_strategies = sorted(
        [(s, a) for s, a in strategy_allocations.items()],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    # Create potential trade symbols
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "V", "JPM"]
    
    for strategy, allocation in top_strategies:
        # Skip if allocation is too small
        if allocation < 5:
            continue
            
        # Number of signals based on allocation
        num_signals = min(3, max(1, int(allocation / 20)))
        
        for _ in range(num_signals):
            # Random symbol
            symbol = np.random.choice(symbols)
            current_price = market_data[symbol]["close"]
            
            # Direction based on strategy and market regime
            if strategy in ["momentum", "trend_following"] and market_data["market_regime"] in ["bullish", "moderately_bullish"]:
                direction = "long"
            elif strategy in ["mean_reversion"] and market_data["market_regime"] in ["sideways"]:
                direction = "long" if np.random.random() > 0.5 else "short"
            elif strategy in ["volatility_breakout"]:
                direction = "long" if np.random.random() > 0.4 else "short"
            else:
                direction = "long" if np.random.random() > 0.3 else "short"
            
            # Set stop loss and take profit
            if direction == "long":
                stop_loss = current_price * (1 - np.random.uniform(0.03, 0.08))
                take_profit = current_price * (1 + np.random.uniform(0.05, 0.15))
            else:
                stop_loss = current_price * (1 + np.random.uniform(0.03, 0.08))
                take_profit = current_price * (1 - np.random.uniform(0.05, 0.15))
            
            signal = {
                "symbol": symbol,
                "signal_type": strategy,
                "direction": direction,
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": np.random.uniform(0.6, 0.95),
                "trailing_stop_distance": current_price * 0.05
            }
            
            signals.append(signal)
    
    return signals


def display_portfolio_status(trade_executor, market_data):
    """Display current portfolio status in a rich table."""
    # Create table for portfolio summary
    portfolio_table = Table(title="Portfolio Summary")
    portfolio_table.add_column("Metric", style="cyan")
    portfolio_table.add_column("Value", style="green")
    
    # Get portfolio value and metrics
    portfolio_value = trade_executor.get_portfolio_value(market_data)
    allocations = trade_executor.get_current_allocations(market_data)
    metrics = trade_executor.get_performance_metrics()
    
    # Add rows to the table
    portfolio_table.add_row("Portfolio Value", f"${portfolio_value:,.2f}")
    portfolio_table.add_row("Cash", f"${trade_executor.cash:,.2f}")
    portfolio_table.add_row("Positions Value", f"${portfolio_value - trade_executor.cash:,.2f}")
    portfolio_table.add_row("Open Positions", str(len(trade_executor.positions)))
    portfolio_table.add_row("Total Return", f"{metrics['total_return']*100:.2f}%")
    portfolio_table.add_row("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
    portfolio_table.add_row("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%")
    
    # Table for positions
    positions_table = Table(title="Current Positions")
    positions_table.add_column("Symbol", style="blue")
    positions_table.add_column("Dir", style="cyan")
    positions_table.add_column("Quantity", style="green")
    positions_table.add_column("Entry", style="yellow")
    positions_table.add_column("Current", style="yellow")
    positions_table.add_column("P&L", style="green")
    positions_table.add_column("Strategy", style="magenta")
    
    # Add positions to table
    for symbol, position in trade_executor.positions.items():
        current_price = trade_executor._get_market_price(symbol, market_data)
        if not current_price:
            current_price = position['entry_price']
            
        if position['direction'] == 'long':
            pnl = (current_price - position['entry_price']) * position['quantity']
            pnl_color = "green" if pnl >= 0 else "red"
        else:  # short
            pnl = (position['entry_price'] - current_price) * position['quantity']
            pnl_color = "green" if pnl >= 0 else "red"
            
        positions_table.add_row(
            symbol,
            position['direction'],
            f"{position['quantity']:.2f}",
            f"${position['entry_price']:.2f}",
            f"${current_price:.2f}",
            f"[{pnl_color}]${pnl:.2f}[/{pnl_color}]",
            position['strategy']
        )
    
    # Table for strategy allocations
    allocations_table = Table(title="Strategy Allocations")
    allocations_table.add_column("Strategy", style="blue")
    allocations_table.add_column("Allocation", style="green")
    allocations_table.add_column("Value", style="yellow")
    
    # Sort allocations and add to table
    sorted_allocations = sorted(
        [(s, a) for s, a in allocations.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    for strategy, allocation in sorted_allocations:
        strategy_value = portfolio_value * (allocation / 100)
        allocations_table.add_row(
            strategy,
            f"{allocation:.2f}%",
            f"${strategy_value:.2f}"
        )
    
    # Display tables
    console.print(portfolio_table)
    console.print(positions_table)
    console.print(allocations_table)


def main():
    console.print(Panel("[bold green]Trade Executor Demo[/bold green]", 
                         subtitle="Integrating RegimeAwareStrategyPrioritizer with TradeExecutor"))
    
    # Available strategies
    strategies = [
        "momentum", 
        "trend_following", 
        "breakout_swing", 
        "mean_reversion", 
        "volatility_breakout", 
        "option_spreads"
    ]
    
    console.print("[bold]Initializing components...[/bold]")
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Initialize RegimeAwareStrategyPrioritizer
    with console.status("[bold green]Initializing strategy prioritizer...[/bold green]"):
        prioritizer = RegimeAwareStrategyPrioritizer(
            strategies=strategies,
            use_mock=True,  # Use mock for demo
            regime_lookback_days=60,
            cache_dir=cache_dir
        )
    
    # Initialize TradeExecutor
    executor = TradeExecutor(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001,
        position_size_limit=0.1
    )
    
    console.print("[bold green]✓[/bold green] Components initialized")
    
    # Simulate a few trading days
    num_days = 5
    console.print(f"\n[bold]Running {num_days} days trading simulation...[/bold]")
    
    for day in range(1, num_days + 1):
        # Create date for this simulation day
        sim_date = (datetime.now() - timedelta(days=num_days-day)).strftime("%Y-%m-%d")
        
        with console.status(f"[bold green]Day {day}/{num_days} ({sim_date}): Getting market data...[/bold green]"):
            # Get mock market data for this day
            market_data = get_mock_market_data()
        
        console.print(f"\n[bold cyan]Trading Day {day}/{num_days} - {sim_date}[/bold cyan]")
        console.print(f"Market Regime: {market_data['market_regime']}")
        console.print(f"VIX: {market_data['volatility_index']:.2f}")
        
        # Get sector performance table
        sector_table = Table(title="Sector Performance")
        sector_table.add_column("Sector", style="blue")
        sector_table.add_column("Performance", style="green")
        
        for sector, perf in market_data["sector_performance"].items():
            color = "green" if perf >= 0 else "red"
            sector_table.add_row(sector, f"[{color}]{perf:.2f}%[/{color}]")
        
        console.print(sector_table)
        
        # Step 1: Prioritize strategies based on market regime
        with console.status("[bold green]Prioritizing strategies based on market regime...[/bold green]"):
            # Enhance market context with regime information
            market_context = {
                "regime": market_data["market_regime"],
                "volatility": market_data["volatility_index"],
                "sector_performance": market_data["sector_performance"]
            }
            
            # Get strategy allocations
            prioritization = prioritizer.prioritize_strategies(market_context=market_context)
            allocations = prioritization["allocations"]
        
        # Display prioritized strategies
        strategy_table = Table(title="Prioritized Strategies")
        strategy_table.add_column("Strategy", style="blue")
        strategy_table.add_column("Allocation %", style="green")
        
        for strategy, allocation in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
            strategy_table.add_row(strategy, f"{allocation:.2f}%")
        
        console.print(strategy_table)
        
        # Step 2: Generate signals based on strategy allocations
        with console.status("[bold green]Generating trade signals...[/bold green]"):
            signals = generate_mock_signals(market_data, allocations)
        
        # Display signals
        if signals:
            signals_table = Table(title="Generated Signals")
            signals_table.add_column("Symbol", style="blue")
            signals_table.add_column("Strategy", style="cyan")
            signals_table.add_column("Direction", style="yellow")
            signals_table.add_column("Price", style="green")
            signals_table.add_column("Stop Loss", style="red")
            signals_table.add_column("Take Profit", style="green")
            
            for signal in signals:
                signals_table.add_row(
                    signal["symbol"],
                    signal["signal_type"],
                    signal["direction"],
                    f"${signal['price']:.2f}",
                    f"${signal['stop_loss']:.2f}",
                    f"${signal['take_profit']:.2f}"
                )
            
            console.print(signals_table)
        else:
            console.print("[yellow]No signals generated for this trading day[/yellow]")
        
        # Step A: Get current allocations before execution
        current_allocations = executor.get_current_allocations(market_data)
        
        # Step 3: Execute trades based on allocations and signals
        with console.status("[bold green]Executing trades...[/bold green]"):
            execution_results = executor.execute_allocations(
                new_allocations=allocations,
                current_allocations=current_allocations,
                market_data=market_data,
                signals=signals,
                date=sim_date
            )
        
        # Step 4: Manage existing positions (apply stops, etc.)
        with console.status("[bold green]Managing positions...[/bold green]"):
            closed_positions = executor.manage_positions(market_data, date=sim_date)
            
            if closed_positions:
                console.print(f"[bold red]Closed {len(closed_positions)} positions[/bold red]")
                for pos in closed_positions:
                    console.print(f"  - {pos['symbol']} ({pos['direction']}): ${pos['pnl']:.2f} ({pos['reason']})")
        
        # Step 5: Display portfolio status after execution
        console.print("\n[bold]Portfolio Status after Execution:[/bold]")
        display_portfolio_status(executor, market_data)
        
        console.print("\n" + "-" * 80 + "\n")
    
    # Display final performance metrics
    metrics = executor.get_performance_metrics()
    
    metrics_table = Table(title="Final Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    
    metrics_table.add_row("Total Return", f"{metrics['total_return']*100:.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
    metrics_table.add_row("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%")
    metrics_table.add_row("Win Rate", f"{metrics['win_rate']*100:.2f}%")
    metrics_table.add_row("Profit Factor", f"{metrics['profit_factor']:.2f}")
    
    console.print(metrics_table)
    
    # Save results to files
    console.print("\n[bold]Saving results to files...[/bold]")
    output_dir = os.path.join(os.path.dirname(__file__), "results")
    result_files = executor.save_results(output_dir=output_dir)
    
    for file_type, file_path in result_files.items():
        console.print(f"[green]✓[/green] {file_type}: {file_path}")


if __name__ == "__main__":
    main() 