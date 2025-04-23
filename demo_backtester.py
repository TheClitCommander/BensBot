#!/usr/bin/env python3
"""
Demo Backtester

This script demonstrates the historical backtesting engine with realistic market data,
allowing evaluation of different trading strategies across various market regimes.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import backtester and data providers
from trading_bot.backtesting.historical_backtester import HistoricalBacktester
from trading_bot.data.market_data_provider import create_data_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("demo_backtester")

# Initialize Rich console
console = Console()

def run_backtest_demo():
    """Run a comprehensive backtest demonstration."""
    console.print(Panel("[bold green]Historical Backtesting Engine Demo[/bold green]", 
                         subtitle="Testing trading strategies across different market regimes"))
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create cache directory
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Get configuration (API keys would go here)
    config = {}
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Configure data provider type
    data_provider_type = "alpaca"  # Default
    if "DATA_PROVIDER" in os.environ:
        data_provider_type = os.environ["DATA_PROVIDER"]
    
    # Check if we should use mock data
    use_mock_data = True
    if "data_provider" in config and "api_key" in config["data_provider"]:
        use_mock_data = False
    
    if use_mock_data:
        console.print("[yellow]No API credentials found. Using mock market data.[/yellow]")
        data_provider_type = "mock"
    
    # Set up backtester with chosen data provider
    with console.status("[bold green]Initializing backtester...[/bold green]"):
        if data_provider_type == "mock":
            # Initialize backtester with mock data
            backtest_data = generate_mock_data()
            backtester = MockHistoricalBacktester(
                mock_data=backtest_data,
                initial_capital=100000.0
            )
        else:
            # Initialize backtester with real data provider
            backtester = HistoricalBacktester(
                config_path=config_path,
                data_provider_type=data_provider_type,
                initial_capital=100000.0
            )
    
    # Define trading universe
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "SPY"]
    
    # Define strategies to test
    strategies = [
        "momentum", 
        "trend_following", 
        "breakout_swing", 
        "mean_reversion", 
        "volatility_breakout",
        "option_spreads"
    ]
    
    # Define backtest period
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # One year
    
    console.print(f"[bold]Backtest Configuration:[/bold]")
    console.print(f"Period: {start_date} to {end_date}")
    console.print(f"Symbols: {', '.join(symbols)}")
    console.print(f"Strategies: {', '.join(strategies)}")
    console.print(f"Initial Capital: ${backtester.initial_capital:,.2f}")
    
    # Run the backtest
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task("[cyan]Running backtest...", total=None)
        
        results = backtester.run_backtest(
            symbols=symbols,
            strategies=strategies,
            start_date=start_date,
            end_date=end_date,
            timeframe="day",
            rebalance_frequency="week",
            regime_lookback_days=60,
            use_regime_aware=True,
            cache_dir=cache_dir
        )
    
    # Check if backtest completed successfully
    if "error" in results:
        console.print(f"[bold red]Error during backtest: {results['error']}[/bold red]")
        return
    
    # Display results summary
    display_backtest_results(results)
    
    # Save results
    save_dir = os.path.join(os.path.dirname(__file__), "backtest_results")
    result_files = backtester.save_results(output_dir=save_dir)
    
    console.print(f"\n[bold green]Results saved to:[/bold green]")
    for file_type, file_path in result_files.items():
        console.print(f"[green]✓[/green] {file_type}: {file_path}")
    
    # Generate performance chart
    output_file = os.path.join(save_dir, "performance_chart.png")
    fig = backtester.plot_performance(output_file=output_file)
    console.print(f"[green]✓[/green] Performance chart: {output_file}")
    
    console.print("\n[bold green]Backtest completed successfully![/bold green]")

def display_backtest_results(results):
    """Display backtest results in a structured format."""
    # Display performance metrics
    metrics = results.get('metrics', {})
    
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    
    metrics_table.add_row("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
    metrics_table.add_row("Annualized Return", f"{metrics.get('annualized_return', 0)*100:.2f}%")
    metrics_table.add_row("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
    metrics_table.add_row("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.2f}")
    metrics_table.add_row("Max Drawdown", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
    metrics_table.add_row("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
    metrics_table.add_row("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
    
    console.print(metrics_table)
    
    # Display strategy allocations over time
    if 'strategy_allocations' in results:
        allocations = results['strategy_allocations']
        
        # Display last allocation
        if allocations:
            last_allocation = allocations[-1]
            
            alloc_table = Table(title=f"Final Strategy Allocations ({last_allocation['date']})")
            alloc_table.add_column("Strategy", style="blue")
            alloc_table.add_column("Allocation %", style="green")
            
            for strategy, alloc in sorted(last_allocation['allocations'].items(), key=lambda x: x[1], reverse=True):
                alloc_table.add_row(strategy, f"{alloc:.2f}%")
            
            console.print(alloc_table)
    
    # Display trade statistics
    closed_positions = results.get('closed_positions', [])
    if closed_positions:
        trades_table = Table(title="Trade Statistics")
        trades_table.add_column("Category", style="cyan")
        trades_table.add_column("Count", style="green")
        trades_table.add_column("Win Rate", style="green")
        trades_table.add_column("Avg P&L", style="green")
        
        # Overall stats
        total_trades = len(closed_positions)
        winning_trades = [p for p in closed_positions if p.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_pnl = sum(p.get('pnl', 0) for p in closed_positions) / total_trades if total_trades > 0 else 0
        
        trades_table.add_row("All Trades", str(total_trades), f"{win_rate*100:.2f}%", f"${avg_pnl:.2f}")
        
        # Stats by strategy
        strategies = {}
        for pos in closed_positions:
            strategy = pos.get('strategy', 'unknown')
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(pos)
        
        for strategy, positions in strategies.items():
            count = len(positions)
            win_rate = len([p for p in positions if p.get('pnl', 0) > 0]) / count if count > 0 else 0
            avg_pnl = sum(p.get('pnl', 0) for p in positions) / count if count > 0 else 0
            
            trades_table.add_row(strategy, str(count), f"{win_rate*100:.2f}%", f"${avg_pnl:.2f}")
        
        console.print(trades_table)

def generate_mock_data() -> dict:
    """Generate mock historical data for backtesting."""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "SPY"]
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    # Base prices for symbols
    base_prices = {
        "AAPL": 150.0, "MSFT": 300.0, "GOOGL": 130.0, "AMZN": 120.0, 
        "META": 300.0, "TSLA": 200.0, "NVDA": 700.0, "JPM": 170.0, 
        "V": 240.0, "SPY": 450.0
    }
    
    # Generate market regimes
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create mock price data
    mock_data = {}
    for symbol in symbols:
        # Create DataFrame for symbol
        df = pd.DataFrame(index=dates)
        df['date'] = df.index
        
        # Generate price series with realistic patterns
        price = base_prices[symbol]
        prices = []
        
        # Add overall market trend with some randomness
        for i in range(len(dates)):
            if i == 0:
                prices.append(price)
                continue
            
            # Day-to-day change
            daily_return = np.random.normal(0.0003, 0.015)  # Mean slightly positive with realistic volatility
            
            # Add some autocorrelation (momentum)
            if i > 1:
                prev_return = (prices[i-1] / prices[i-2]) - 1
                daily_return += prev_return * 0.1  # Some momentum effect
            
            # Add seasonal pattern and trends
            day_of_year = dates[i].dayofyear
            # Slight seasonal effect
            seasonal = 0.1 * np.sin(day_of_year / 365 * 2 * np.pi)
            daily_return += seasonal / 100
            
            # Calculate new price
            new_price = prices[i-1] * (1 + daily_return)
            prices.append(new_price)
        
        # Add to DataFrame
        df['close'] = prices
        
        # Generate realistic OHLC and volume
        df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.003, len(df)))
        df['high'] = df.apply(lambda x: max(x['open'], x['close']) * (1 + abs(np.random.normal(0, 0.005))), axis=1)
        df['low'] = df.apply(lambda x: min(x['open'], x['close']) * (1 - abs(np.random.normal(0, 0.005))), axis=1)
        df['volume'] = np.random.normal(1000000, 200000, len(df))
        
        # Fill first row NaN values
        df['open'].iloc[0] = prices[0] * 0.995
        
        # Store in mock data
        mock_data[symbol] = df.dropna()
    
    return mock_data

class MockHistoricalBacktester(HistoricalBacktester):
    """Extended backtester class that uses pre-generated mock data."""
    
    def __init__(self, mock_data, initial_capital=100000.0):
        """
        Initialize with mock data.
        
        Args:
            mock_data: Dictionary of mock price data by symbol
            initial_capital: Initial capital for backtesting
        """
        # Initialize parent class with minimal settings
        super().__init__(
            initial_capital=initial_capital
        )
        
        # Store mock data
        self.mock_data = mock_data
    
    def run_backtest(self, **kwargs):
        """
        Override to use mock data instead of data provider.
        
        Args:
            **kwargs: Arguments for original run_backtest method
            
        Returns:
            Backtest results dictionary
        """
        # Get symbols and date range
        symbols = kwargs.get('symbols', [])
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        # Convert mock data to format expected by backtester
        historical_data = {}
        
        for symbol in symbols:
            if symbol in self.mock_data:
                df = self.mock_data[symbol].copy()
                # Filter by date range
                if start_date:
                    df = df[df['date'] >= start_date]
                if end_date:
                    df = df[df['date'] <= end_date]
                
                historical_data[symbol] = df
        
        # Create DatetimeIndex for the backtest
        all_dates = set()
        for symbol, df in historical_data.items():
            all_dates.update(df['date'].dt.date)
        
        # Sort dates and convert to datetime
        backtest_dates = sorted(all_dates)
        backtest_dates = [datetime.combine(date, datetime.min.time()) for date in backtest_dates]
        
        # Follow the original method pattern but with our historical data
        self.results = None
        self.metrics = None
        self.signals_history = []
        self.trades_history = []
        self.portfolio_history = []
        
        # Run the backtest day by day following the parent class logic
        # This is a simplified version - in a real implementation you would follow
        # the parent class implementation more closely
        
        # Call the main backtest method with our data
        # This is a hack - we're replacing the data provider's get_historical_data method
        original_get_historical_data = getattr(self.data_provider, 'get_historical_data', None)
        
        def mock_get_historical_data(*args, **kwargs):
            return historical_data
        
        if hasattr(self.data_provider, 'get_historical_data'):
            self.data_provider.get_historical_data = mock_get_historical_data
        
        try:
            # Call parent method with our kwargs
            results = super().run_backtest(**kwargs)
            return results
        finally:
            # Restore original method if it existed
            if original_get_historical_data:
                self.data_provider.get_historical_data = original_get_historical_data

if __name__ == "__main__":
    run_backtest_demo() 