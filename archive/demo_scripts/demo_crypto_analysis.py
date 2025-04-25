#!/usr/bin/env python3
"""
Demo script to showcase the enhanced crypto trading indicators and analytics.
This demonstrates the advanced features like on-chain analysis, cross-asset
correlation, sentiment analysis, and the composite health score.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import random
import ccxt

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.data.crypto_indicators import CryptoIndicatorProcessor

console = Console()

def load_market_data(exchange_id='binance', symbols=None, timeframe='1d', limit=365):
    """
    Load market data for the specified symbols.
    
    Args:
        exchange_id: Exchange to use (default: binance)
        symbols: List of symbols to fetch (default: top coins)
        timeframe: Timeframe to fetch (default: 1d)
        limit: Number of candles to fetch (default: 365)
        
    Returns:
        Dict of {symbol: dataframe} with OHLCV data
    """
    console.print(f"[bold cyan]Loading market data from {exchange_id}...[/bold cyan]")
    
    # Default symbols if none provided
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
    
    # Initialize exchange
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'enableRateLimit': True,
    })
    
    market_data = {}
    
    for symbol in symbols:
        try:
            console.print(f"  Fetching data for [green]{symbol}[/green]")
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Store in dict with base asset as key
            base = symbol.split('/')[0]
            market_data[base] = df
            
        except Exception as e:
            console.print(f"[bold red]Error fetching {symbol}: {str(e)}[/bold red]")
    
    return market_data

def generate_demo_onchain_data(df, asset='BTC'):
    """
    Generate demo on-chain data for testing.
    In a real implementation, this would fetch from blockchain explorers or APIs.
    
    Args:
        df: DataFrame with OHLCV data to match dates
        asset: Asset to generate data for
        
    Returns:
        Dict of {metric: series} with on-chain data
    """
    console.print(f"[bold cyan]Generating demo on-chain data for {asset}...[/bold cyan]")
    
    # Use price index for alignment
    index = df.index
    
    # Noise factor for randomization
    price = df['close'].values
    noise = np.random.normal(0, 1, len(index)) * 0.2
    
    # Random seed for reproducibility
    np.random.seed(42)
    
    # Generate realistic-looking on-chain metrics
    metrics = {}
    
    # 1. Active addresses - correlated with price + seasonal weekly pattern + noise
    weekly_pattern = np.sin(np.arange(len(index)) * (2 * np.pi / 7)) * 0.15
    price_factor = (price / price.mean()) * 0.5
    active_addresses = (price_factor + weekly_pattern + noise * 0.3 + 0.5) * 1000000
    metrics['active_addresses'] = pd.Series(active_addresses, index=index)
    
    # 2. Transaction volume (USD) - correlated with price but more volatile
    txn_noise = np.random.normal(0, 1, len(index)) * 0.4
    txn_volume_usd = (price_factor * 1.2 + txn_noise + 0.3) * 5000000000
    metrics['txn_volume_usd'] = pd.Series(txn_volume_usd, index=index)
    
    # 3. SOPR (Spent Output Profit Ratio)
    # Simulating a metric that crosses above/below 1 indicating profit/loss
    price_change = np.diff(price, prepend=price[0])
    price_roc = price_change / price
    sopr = 1 + (price_roc * 3) + np.random.normal(0, 0.05, len(index))
    metrics['sopr'] = pd.Series(sopr, index=index)
    
    # 4. Miner outflows - spikes occasionally
    miner_outflows = np.random.exponential(1, len(index)) * 0.5 + 0.5
    # Add occasional spikes
    spike_idx = np.random.choice(range(len(index)), size=10, replace=False)
    miner_outflows[spike_idx] *= 3
    metrics['miner_outflows'] = pd.Series(miner_outflows, index=index)
    
    # 5. Realized value
    # Smoothed price with lag
    realized_value = (df['close'].rolling(window=30).mean().shift(15).fillna(df['close']) * 
                     df['volume'].rolling(window=30).mean().shift(15).fillna(df['volume']))
    metrics['realized_value'] = realized_value
    
    # 6. Supply distribution (HODL waves)
    # Generate HODL wave data (% of supply last moved in time period)
    total = 21000000 if asset == 'BTC' else 100000000  # Total supply    
    
    # HODL waves (simulated)
    hodl_1d = np.random.normal(0.05, 0.01, len(index))  # 1 day
    hodl_1w = np.random.normal(0.10, 0.02, len(index))  # 1 week
    hodl_1m = np.random.normal(0.15, 0.03, len(index))  # 1 month
    hodl_3m = np.random.normal(0.20, 0.03, len(index))  # 3 months
    hodl_6m = np.random.normal(0.15, 0.02, len(index))  # 6 months
    hodl_1y = np.random.normal(0.20, 0.02, len(index))  # 1 year
    hodl_2y = np.random.normal(0.15, 0.02, len(index))  # 2+ years
    
    # Normalize to sum to 1
    for i in range(len(index)):
        total = (hodl_1d[i] + hodl_1w[i] + hodl_1m[i] + hodl_3m[i] + 
                hodl_6m[i] + hodl_1y[i] + hodl_2y[i])
        hodl_1d[i] /= total
        hodl_1w[i] /= total
        hodl_1m[i] /= total
        hodl_3m[i] /= total
        hodl_6m[i] /= total
        hodl_1y[i] /= total
        hodl_2y[i] /= total
    
    metrics['hodl_1d'] = pd.Series(hodl_1d, index=index)
    metrics['hodl_1w'] = pd.Series(hodl_1w, index=index)
    metrics['hodl_1m'] = pd.Series(hodl_1m, index=index)
    metrics['hodl_3m'] = pd.Series(hodl_3m, index=index)
    metrics['hodl_6m'] = pd.Series(hodl_6m, index=index)
    metrics['hodl_1y'] = pd.Series(hodl_1y, index=index)
    metrics['hodl_2y_plus'] = pd.Series(hodl_2y, index=index)
    
    # Add circulating supply for calculations
    if asset == 'BTC':
        # Simulate Bitcoin's emission schedule
        days_since_start = (index - pd.Timestamp('2009-01-03')).days.values
        halving_factor = np.floor(days_since_start / (365 * 4))  # Approx. halving every 4 years
        emission_factor = 50 / (2 ** halving_factor)
        emission_factor[emission_factor < 0] = 0
        
        # Calculate circulating supply
        supply = 50 * 144 * 365  # Initial year
        daily_supply = []
        for day in range(len(index)):
            if day > 0:
                supply += emission_factor[day] * 144  # 144 blocks per day
            daily_supply.append(supply)
        
        circulating_supply = np.array(daily_supply)
    else:
        # Generic supply curve
        max_supply = 100000000
        circulating_supply = max_supply * (1 - np.exp(-0.001 * np.arange(len(index))))
    
    metrics['circulating_supply'] = pd.Series(circulating_supply, index=index)
    
    return metrics

def generate_demo_sentiment_data(df):
    """
    Generate demo sentiment data for testing.
    In a real implementation, this would fetch from sentiment APIs or social media.
    
    Args:
        df: DataFrame with OHLCV data to match dates
        
    Returns:
        Dict of {source: series} with sentiment data
    """
    console.print(f"[bold cyan]Generating demo sentiment data...[/bold cyan]")
    
    # Use price index for alignment
    index = df.index
    
    # Noise factor for randomization
    price = df['close'].values
    noise = np.random.normal(0, 1, len(index)) * 0.2
    
    # Random seed for reproducibility
    np.random.seed(43)
    
    # Generate realistic-looking sentiment metrics
    sentiment = {}
    
    # 1. Fear & Greed Index (0-100)
    # Slightly inverse to price (contrarian indicator) + some randomness
    price_norm = (price - price.min()) / (price.max() - price.min())
    inverse_factor = 1 - price_norm
    fear_greed = 50 + (inverse_factor - 0.5) * 60 + np.random.normal(0, 10, len(index))
    fear_greed = np.clip(fear_greed, 0, 100)
    sentiment['fear_greed'] = pd.Series(fear_greed, index=index)
    
    # 2. Social media sentiment (-1 to 1)
    # More reactive to price changes
    price_change = np.diff(price, prepend=price[0])
    price_change_norm = np.clip(price_change / np.abs(price_change).max(), -1, 1)
    social_sentiment = price_change_norm * 0.7 + np.random.normal(0, 0.3, len(index))
    social_sentiment = np.clip(social_sentiment, -1, 1)
    sentiment['social'] = pd.Series(social_sentiment, index=index)
    
    # 3. News sentiment (0-100)
    # Less volatile, more smoothed
    news_sentiment = 50 + price_norm * 40 + np.random.normal(0, 10, len(index))
    news_sentiment = np.clip(news_sentiment, 0, 100)
    # Apply smoothing
    news_sentiment = pd.Series(news_sentiment).rolling(window=7).mean().fillna(method='bfill').values
    sentiment['news'] = pd.Series(news_sentiment, index=index)
    
    # 4. Twitter mention count (volume)
    # Correlated with big price moves
    abs_price_change = np.abs(price_change)
    normalized_change = abs_price_change / abs_price_change.max()
    twitter_mentions = 1000 + normalized_change * 9000 + np.random.exponential(500, len(index))
    sentiment['twitter_volume'] = pd.Series(twitter_mentions, index=index)
    
    return sentiment

def display_analysis_results(results, symbol):
    """
    Display analysis results in a rich formatted output.
    
    Args:
        results: Dict with analysis results
        symbol: Symbol being analyzed
    """
    # Get key metrics
    df = results['data']
    signals = results['signals']
    health_score = results['health_score']
    summary = results['summary']
    
    # Create title panel
    title = f"[bold white on blue] Crypto Analysis Results for {symbol} [/bold white on blue]"
    console.print(Panel(title, expand=False))
    
    # Display summary
    console.print(Panel(summary, title="[bold]Summary Analysis[/bold]", 
                       border_style="green", expand=False))
    
    # Display key signals in a table
    signal_table = Table(title="Trading Signals", box=box.ROUNDED)
    signal_table.add_column("Signal Type", style="cyan")
    signal_table.add_column("Direction", style="green")
    signal_table.add_column("Confidence", style="yellow")
    signal_table.add_column("Description", style="white")
    
    # Map signal values to readable text
    signal_map = {-1: "🔴 BEARISH", 0: "⚪ NEUTRAL", 1: "🟢 BULLISH"}
    
    # Add overall signal first
    overall = signals['overall']
    signal_table.add_row(
        "[bold]OVERALL[/bold]",
        signal_map[overall['signal']],
        f"{int(overall['confidence']*100)}%",
        overall['description']
    )
    
    # Add other signals
    for name, data in signals.items():
        if name == 'overall':
            continue
            
        signal_table.add_row(
            name.title(),
            signal_map[data['signal']],
            f"{int(data['confidence']*100)}%",
            data['description']
        )
    
    console.print(signal_table)
    
    # Display health score with colored gauge
    if health_score is not None:
        health_color = "green" if health_score > 60 else "yellow" if health_score > 40 else "red"
        health_gauge = f"[bold {health_color}]{health_score:.1f}/100[/bold {health_color}]"
        console.print(Panel(f"Asset Health Score: {health_gauge}", 
                           title="[bold]Health Assessment[/bold]", 
                           border_style=health_color, expand=False))
    
    # Display key metrics
    current = df.iloc[-1]
    
    metrics_table = Table(title="Key Metrics (Latest Values)", box=box.ROUNDED)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="yellow")
    metrics_table.add_column("Interpretation", style="white")
    
    # Add selected metrics based on availability
    metrics_to_show = [
        ('rsi', "RSI", lambda v: f"{'Overbought' if v > 70 else 'Oversold' if v < 30 else 'Neutral'}"),
        ('macd_histogram', "MACD Histogram", lambda v: f"{'Positive' if v > 0 else 'Negative'}"),
        ('vol_regime', "Volatility Regime", lambda v: f"{v.title()}"),
        ('bb_pct_b', "%B", lambda v: f"{'Overbought' if v > 1 else 'Oversold' if v < 0 else 'Normal Range'}"),
        ('squeeze_on', "Volatility Squeeze", lambda v: f"{'Active' if v else 'Inactive'}"),
        ('crypto_health_score', "Health Score", lambda v: f"{'Excellent' if v > 80 else 'Good' if v > 60 else 'Fair' if v > 40 else 'Poor' if v > 20 else 'Critical'}"),
    ]
    
    for col, label, interpret in metrics_to_show:
        if col in current.index:
            value = current[col]
            if not pd.isna(value):
                # Format value based on type
                if isinstance(value, bool):
                    formatted_value = str(value)
                elif isinstance(value, (int, np.integer)):
                    formatted_value = f"{value:,d}"
                elif isinstance(value, (float, np.float)):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                    
                metrics_table.add_row(label, formatted_value, interpret(value))
    
    console.print(metrics_table)
    
    # Show on-chain metrics if available
    onchain_cols = [col for col in df.columns if col.startswith('onchain_')]
    if onchain_cols:
        onchain_table = Table(title="On-Chain Metrics", box=box.ROUNDED)
        onchain_table.add_column("Metric", style="cyan")
        onchain_table.add_column("Value", style="yellow")
        
        for col in onchain_cols[:5]:  # Show top 5 metrics only
            if col in current.index and not pd.isna(current[col]):
                metric_name = col.replace('onchain_', '').replace('_', ' ').title()
                value = current[col]
                
                # Format value based on type
                if isinstance(value, (int, np.integer)):
                    formatted_value = f"{value:,d}"
                elif isinstance(value, (float, np.float)):
                    formatted_value = f"{value:.4f}"
                else:
                    formatted_value = str(value)
                    
                onchain_table.add_row(metric_name, formatted_value)
        
        console.print(onchain_table)
    
    # Show correlation data if available
    corr_cols = [col for col in df.columns if col.startswith('corr_')]
    if corr_cols:
        corr_table = Table(title="Asset Correlations (30d)", box=box.ROUNDED)
        corr_table.add_column("Asset", style="cyan")
        corr_table.add_column("Correlation", style="yellow")
        corr_table.add_column("Regime", style="white")
        
        for col in corr_cols:
            if '30d' in col and col in current.index and not pd.isna(current[col]):
                asset_name = col.split('_')[1]
                correlation = current[col]
                
                # Determine correlation regime
                if correlation > 0.7:
                    regime = "Very High"
                    style = "green"
                elif correlation > 0.3:
                    regime = "High"
                    style = "green"
                elif correlation > -0.3:
                    regime = "Neutral"
                    style = "yellow"
                elif correlation > -0.7:
                    regime = "Low"
                    style = "red"
                else:
                    regime = "Very Low"
                    style = "red"
                    
                corr_table.add_row(asset_name, f"{correlation:.4f}", f"[{style}]{regime}[/{style}]")
        
        console.print(corr_table)
    
    console.print("\n[italic cyan]Analysis complete. Use these insights for trading decisions.[/italic cyan]\n")

def main():
    """Main function to run the demo."""
    console.print(Panel("[bold]Crypto Trading Intelligence Demo[/bold]\n"
                       "This demo showcases the enhanced trading indicators and analytics",
                       border_style="blue", expand=False))
    
    # Asset to analyze
    symbol = "BTC/USDT"
    base_asset = symbol.split('/')[0]
    
    # Load market data
    try:
        market_data = load_market_data(symbols=[symbol, "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"])
        
        if not market_data or base_asset not in market_data:
            console.print(f"[bold red]Failed to load market data for {symbol}[/bold red]")
            return
            
        df = market_data[base_asset]
        console.print(f"[green]Successfully loaded {len(df)} candles for {symbol}[/green]")
        
        # Generate demo on-chain data
        onchain_data = generate_demo_onchain_data(df, asset=base_asset)
        
        # Generate demo sentiment data
        sentiment_data = generate_demo_sentiment_data(df)
        
        # Create reference assets dictionary
        reference_assets = {k: v for k, v in market_data.items() if k != base_asset}
        reference_assets[base_asset] = df  # Include the asset itself
        
        # Initialize indicator processor
        processor = CryptoIndicatorProcessor()
        
        # Run full analysis
        console.print("[bold cyan]Running full crypto intelligence analysis...[/bold cyan]")
        results = processor.run_full_analysis(
            df, 
            reference_assets=reference_assets,
            onchain_data=onchain_data,
            sentiment_data=sentiment_data
        )
        
        # Display results
        display_analysis_results(results, symbol)
        
    except Exception as e:
        console.print(f"[bold red]Error in analysis: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 