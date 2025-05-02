#!/usr/bin/env python3
"""
Example script demonstrating the usage of the RiskManager with the MultiAssetAdapter.

This example shows how to initialize the risk manager, check trades for risk compliance,
calculate position sizes, and generate risk reports across multiple asset classes.
"""

import os
import json
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our adapter and risk manager
from trading_bot.adapters.multi_asset_adapter import MultiAssetAdapter, AssetClass
from trading_bot.risk_manager import RiskManager

# Create rich console for nice output
console = Console()

def main():
    """Main function to demonstrate risk management functionality."""
    # Intro banner
    console.print(Panel("[bold blue]Multi-Asset Risk Management Demo[/bold blue]", 
                       border_style="blue", expand=False))
    
    # Initialize the multi-asset adapter
    console.print("[bold cyan]Initializing Multi-Asset Adapter...[/bold cyan]")
    
    adapter_config = {
        "multipliers": {
            "ES": 50,    # E-mini S&P 500
            "NQ": 20,    # E-mini Nasdaq-100
            "GC": 100,   # Gold
            "CL": 1000,  # Crude Oil
        },
        "margin_requirements": {
            "futures": {
                "ES": 12000,
                "NQ": 15000,
                "GC": 9900,
                "CL": 6600
            },
            "forex": 0.02,  # 50:1 leverage
            "crypto": 0.5   # 2:1 leverage
        }
    }
    
    adapter = MultiAssetAdapter(asset_class=AssetClass.FUTURES, config_path=None)
    adapter.config = adapter_config  # Override with our config
    
    # Initialize the risk manager
    console.print("[bold cyan]Initializing Risk Manager...[/bold cyan]")
    
    risk_config = {
        "risk_profile": {
            "profile_name": "conservative",
            "max_risk_per_trade": 1.0,   # 1% risk per trade
            "max_daily_risk": 3.0,       # 3% max daily risk
            "max_portfolio_risk": 10.0,  # 10% max portfolio risk
            "position_size_multiplier": 0.8,  # Reduce all positions by 20%
            "current_regime": "neutral"  # Current market regime
        },
        "global_limits": {
            "max_drawdown": 10.0,        # 10% max drawdown
            "max_leverage": 1.5,         # 1.5x max leverage
            "max_correlated_positions": 2,  # Max correlated positions
            "min_reward_risk_ratio": 2.0    # Minimum 2:1 reward:risk
        }
    }
    
    risk_manager = RiskManager(adapter, config_path=None)
    risk_manager.config = risk_config  # Override with our config
    risk_manager.risk_profile = risk_config["risk_profile"]
    risk_manager.global_risk_limits = risk_config["global_limits"]
    
    # Mock account value for the demo
    risk_manager.portfolio_metrics["account_value"] = 100000
    
    # Example 1: Calculate position size for futures trade
    console.print("\n[bold green]Example 1: Calculate Position Size for Futures Trade[/bold green]")
    
    futures_sizing = risk_manager.calculate_position_size(
        symbol="ES",
        entry_price=4500,
        stop_price=4480,
        target_price=4550,
        asset_class="futures"
    )
    
    print_sizing_results("ES Futures", futures_sizing)
    
    # Example 2: Calculate position size for forex trade
    console.print("\n[bold green]Example 2: Calculate Position Size for Forex Trade[/bold green]")
    
    forex_sizing = risk_manager.calculate_position_size(
        symbol="EUR/USD",
        entry_price=1.0850,
        stop_price=1.0800,
        target_price=1.0950,
        asset_class="forex"
    )
    
    print_sizing_results("EUR/USD Forex", forex_sizing)
    
    # Example 3: Calculate position size for crypto trade
    console.print("\n[bold green]Example 3: Calculate Position Size for Crypto Trade[/bold green]")
    
    crypto_sizing = risk_manager.calculate_position_size(
        symbol="BTC-USD",
        entry_price=35000,
        stop_price=34000,
        target_price=38000,
        asset_class="crypto"
    )
    
    print_sizing_results("BTC-USD Crypto", crypto_sizing)
    
    # Example 4: Check trade for risk compliance
    console.print("\n[bold green]Example 4: Check Trade for Risk Compliance[/bold green]")
    
    trade_check = risk_manager.check_trade_risk(
        symbol="AAPL",
        direction="long",
        quantity=100,
        entry_price=175.0,
        stop_price=165.0,
        target_price=195.0,
        asset_class="equity"
    )
    
    print_risk_check_results(trade_check)
    
    # Example 5: Record trade entry
    console.print("\n[bold green]Example 5: Record Trade Entry[/bold green]")
    
    trade_entry = risk_manager.record_trade_entry(
        symbol="ES",
        direction="long",
        quantity=2,
        entry_price=4500,
        stop_price=4480,
        target_price=4550,
        asset_class="futures",
        strategy="trend_following"
    )
    
    print_trade_record(trade_entry)
    
    # Example 6: Generate Risk Report
    console.print("\n[bold green]Example 6: Generate Risk Report[/bold green]")
    
    risk_report = risk_manager.get_risk_report()
    print_risk_report(risk_report)
    
    # Example 7: Update Risk Profile
    console.print("\n[bold green]Example 7: Update Risk Profile[/bold green]")
    
    updated_profile = risk_manager.update_risk_profile({
        "max_risk_per_trade": 0.5,  # Reduce risk per trade to 0.5%
        "current_regime": "bearish"  # Change market regime to bearish
    })
    
    console.print("[bold yellow]Updated Risk Profile:[/bold yellow]")
    console.print(f"Max risk per trade: [green]{updated_profile['max_risk_per_trade']}%[/green]")
    console.print(f"Market regime: [green]{updated_profile['current_regime']}[/green]")
    
    # Example 8: Record trade exit
    console.print("\n[bold green]Example 8: Record Trade Exit[/bold green]")
    
    trade_exit = risk_manager.record_trade_exit(
        symbol="ES",
        exit_price=4550,
        exit_reason="Target reached"
    )
    
    print_trade_exit(trade_exit)


def print_sizing_results(title, sizing):
    """Print position sizing results in a formatted table."""
    table = Table(title=title, box=box.ROUNDED)
    
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    # Add common sizing parameters
    if "position_size" in sizing:
        table.add_row("Position Size", f"{sizing['position_size']:.4f}")
    
    if "risk_amount" in sizing:
        table.add_row("Risk Amount", f"${sizing['risk_amount']:.2f}")
    
    if "risk_percentage" in sizing:
        table.add_row("Risk Percentage", f"{sizing['risk_percentage']:.2f}%")
    
    # Add asset-specific parameters
    if "contracts" in sizing:
        table.add_row("Contracts", str(sizing['contracts']))
        
    if "margin_requirement" in sizing:
        table.add_row("Margin Required", f"${sizing['margin_requirement']:.2f}")
    
    if "lots" in sizing:
        table.add_row("Lots", f"{sizing['lots']:.2f}")
        
    if "units" in sizing:
        table.add_row("Units", f"{sizing['units']:.2f}")
    
    if "reward_risk_ratio" in sizing:
        table.add_row("Reward:Risk Ratio", f"{sizing['reward_risk_ratio']:.2f}")
    
    if "position_size_multiplier" in sizing:
        table.add_row("Position Size Multiplier", f"{sizing['position_size_multiplier']:.2f}")
    
    console.print(table)


def print_risk_check_results(risk_check):
    """Print risk check results in a formatted panel."""
    passed = risk_check["risk_checks_passed"]
    color = "green" if passed else "red"
    
    # Create a summary panel
    summary = f"[bold {color}]Risk Check {'PASSED' if passed else 'FAILED'}[/bold {color}]\n\n"
    summary += f"Symbol: {risk_check['symbol']} ({risk_check['asset_class']})\n"
    summary += f"Direction: {risk_check['direction']}\n"
    summary += f"Quantity: {risk_check['quantity']}\n"
    summary += f"Entry Price: ${risk_check['entry_price']:.2f}\n"
    summary += f"Stop Price: ${risk_check['stop_price']:.2f}\n"
    
    if risk_check['target_price']:
        summary += f"Target Price: ${risk_check['target_price']:.2f}\n"
    
    if "risk_details" in risk_check and "risk_percentage" in risk_check["risk_details"]:
        summary += f"Risk Percentage: {risk_check['risk_details']['risk_percentage']:.2f}%\n"
    
    if "risk_details" in risk_check and "reward_risk_ratio" in risk_check["risk_details"]:
        summary += f"Reward:Risk Ratio: {risk_check['risk_details']['reward_risk_ratio']:.2f}\n"
    
    console.print(Panel(summary, title="Risk Check Summary", border_style=color))
    
    # Print errors if any
    if risk_check["errors"]:
        console.print("[bold red]Errors:[/bold red]")
        for error in risk_check["errors"]:
            console.print(f"- {error}", style="red")
    
    # Print warnings if any
    if risk_check["warnings"]:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in risk_check["warnings"]:
            console.print(f"- {warning}", style="yellow")


def print_trade_record(trade):
    """Print trade record in a formatted panel."""
    trade_details = f"[bold]Trade ID:[/bold] {trade['trade_id']}\n"
    trade_details += f"[bold]Symbol:[/bold] {trade['symbol']} ({trade['asset_class']})\n"
    trade_details += f"[bold]Direction:[/bold] {trade['direction']}\n"
    trade_details += f"[bold]Quantity:[/bold] {trade['quantity']}\n"
    trade_details += f"[bold]Entry Price:[/bold] ${trade['entry_price']:.2f}\n"
    trade_details += f"[bold]Stop Price:[/bold] ${trade['stop_price']:.2f}\n"
    
    if "target_price" in trade and trade["target_price"]:
        trade_details += f"[bold]Target Price:[/bold] ${trade['target_price']:.2f}\n"
    
    trade_details += f"[bold]Entry Time:[/bold] {trade['entry_time']}\n"
    trade_details += f"[bold]Strategy:[/bold] {trade['strategy']}\n"
    trade_details += f"[bold]Risk Amount:[/bold] ${trade['risk_amount']:.2f}\n"
    trade_details += f"[bold]Risk Percentage:[/bold] {trade['risk_percentage']:.2f}%\n"
    
    if "reward_risk_ratio" in trade:
        trade_details += f"[bold]Reward:Risk Ratio:[/bold] {trade['reward_risk_ratio']:.2f}\n"
    
    console.print(Panel(trade_details, title="Trade Entry Recorded", border_style="green"))


def print_trade_exit(trade):
    """Print trade exit record in a formatted panel."""
    if "error" in trade:
        console.print(Panel(f"Error: {trade['error']}", title="Trade Exit Failed", border_style="red"))
        return
    
    trade_details = f"[bold]Trade ID:[/bold] {trade['trade_id']}\n"
    trade_details += f"[bold]Symbol:[/bold] {trade['symbol']} ({trade['asset_class']})\n"
    trade_details += f"[bold]Direction:[/bold] {trade['direction']}\n"
    trade_details += f"[bold]Entry Price:[/bold] ${trade['entry_price']:.2f}\n"
    trade_details += f"[bold]Exit Price:[/bold] ${trade['exit_price']:.2f}\n"
    trade_details += f"[bold]Exit Time:[/bold] {trade['exit_time']}\n"
    
    pnl_color = "green" if trade.get('pnl', 0) >= 0 else "red"
    trade_details += f"[bold]P&L:[/bold] [{pnl_color}]${trade.get('pnl', 0):.2f}[/{pnl_color}]\n"
    
    if "pnl_percentage" in trade:
        trade_details += f"[bold]P&L %:[/bold] [{pnl_color}]{trade['pnl_percentage']:.2f}%[/{pnl_color}]\n"
        
    if "pnl_risk_ratio" in trade:
        trade_details += f"[bold]P&L/Risk Ratio:[/bold] [{pnl_color}]{trade['pnl_risk_ratio']:.2f}[/{pnl_color}]\n"
    
    if "trade_duration" in trade and trade["trade_duration"]:
        hours = trade["trade_duration"] // 60
        minutes = trade["trade_duration"] % 60
        trade_details += f"[bold]Duration:[/bold] {hours}h {minutes}m\n"
    
    if "exit_reason" in trade and trade["exit_reason"]:
        trade_details += f"[bold]Exit Reason:[/bold] {trade['exit_reason']}\n"
    
    console.print(Panel(trade_details, title="Trade Exit Recorded", border_style="blue"))


def print_risk_report(report):
    """Print risk report summary in a formatted table."""
    # Create portfolio metrics table
    metrics_table = Table(title="Portfolio Risk Metrics", box=box.ROUNDED)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    
    account_value = report["portfolio_metrics"].get("account_value", 0)
    metrics_table.add_row("Account Value", f"${account_value:,.2f}")
    
    total_exposure = report["portfolio_metrics"].get("total_exposure", 0)
    metrics_table.add_row("Total Exposure", f"${total_exposure:,.2f}")
    
    exposure_pct = report["portfolio_metrics"].get("total_exposure_pct", 0)
    metrics_table.add_row("Exposure %", f"{exposure_pct:.2f}%")
    
    leverage = report["portfolio_metrics"].get("leverage", 0)
    metrics_table.add_row("Current Leverage", f"{leverage:.2f}x")
    
    max_leverage = report["global_limits"].get("max_leverage", 0)
    metrics_table.add_row("Max Leverage", f"{max_leverage:.2f}x")
    
    open_positions = report.get("open_trades", 0)
    metrics_table.add_row("Open Positions", str(open_positions))
    
    daily_risk = report.get("daily_risk_usage", {}).get("total_risk", 0)
    metrics_table.add_row("Daily Risk Used", f"{daily_risk:.2f}%")
    
    remaining_risk = report.get("remaining_risk_capacity", 0)
    metrics_table.add_row("Remaining Risk Capacity", f"{remaining_risk:.2f}%")
    
    drawdown = report["portfolio_metrics"].get("current_drawdown_pct", 0)
    metrics_table.add_row("Current Drawdown", f"{drawdown:.2f}%")
    
    console.print(metrics_table)
    
    # Create asset class exposure table if available
    if "risk_distribution" in report and report["risk_distribution"]:
        exposure_table = Table(title="Asset Class Exposure", box=box.ROUNDED)
        exposure_table.add_column("Asset Class", style="cyan")
        exposure_table.add_column("Current %", style="yellow")
        exposure_table.add_column("Max %", style="green")
        exposure_table.add_column("Available %", style="blue")
        exposure_table.add_column("Utilization", style="magenta")
        
        for asset_class, data in report["risk_distribution"].items():
            utilization = data.get("utilization_percentage", 0)
            util_style = "green" if utilization < 70 else "yellow" if utilization < 90 else "red"
            
            exposure_table.add_row(
                asset_class,
                f"{data.get('current_allocation', 0):.2f}%",
                f"{data.get('max_allocation', 0):.2f}%",
                f"{data.get('available_allocation', 0):.2f}%",
                f"[{util_style}]{utilization:.1f}%[/{util_style}]"
            )
        
        console.print(exposure_table)


if __name__ == "__main__":
    main() 