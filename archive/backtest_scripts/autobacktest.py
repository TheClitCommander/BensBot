#!/usr/bin/env python3
"""
AutoBacktest - Autonomous Backtesting System

A semi-autonomous alpha discovery system that intelligently selects symbols and
strategies to backtest based on news, technical indicators, and historical performance.

Usage:
  python autobacktest.py --mode scheduler --daily-limit 50
  python autobacktest.py --mode score --symbols AAPL,MSFT,GOOGL
  python autobacktest.py --mode analyze --results-dir data/results
"""

import os
import sys
import json
import argparse
import logging
import datetime
import pandas as pd
from symbol_scorer import SymbolScorer
from backtest_scheduler import BacktestScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autobacktest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_api_keys(config_file='config.json'):
    """Load API keys from configuration file."""
    if not os.path.exists(config_file):
        logger.warning("Config file %s not found. Using empty API keys.", config_file)
        return {}
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config.get('api_keys', {})
    except Exception as e:
        logger.error("Error loading config: %s", str(e))
        return {}

def run_scheduler(args):
    """Run the backtest scheduler in continuous mode."""
    logger.info("Starting backtest scheduler with daily limit: %d", args.daily_limit)
    
    # Load API keys
    api_keys = load_api_keys(args.config)
    
    # Initialize scheduler
    scheduler = BacktestScheduler(
        api_keys=api_keys,
        data_dir=args.data_dir,
        max_concurrent=args.concurrent,
        daily_limit=args.daily_limit,
        watchlist_size=args.watchlist_size,
        refresh_interval=args.refresh_interval
    )
    
    # Load custom watchlist if provided
    if args.watchlist:
        watchlist_path = args.watchlist
        if os.path.exists(watchlist_path):
            try:
                with open(watchlist_path, 'r') as f:
                    symbols = [line.strip() for line in f.readlines() if line.strip()]
                scheduler.watchlist = symbols
                scheduler.save_watchlist()
                logger.info("Loaded custom watchlist with %d symbols", len(symbols))
            except Exception as e:
                logger.error("Error loading custom watchlist: %s", str(e))
    
    # Run scheduler loop
    scheduler.run_scheduler_loop(interval=args.interval)

def score_symbols(args):
    """Score symbols against strategies and display results."""
    logger.info("Scoring symbols against strategies")
    
    # Load API keys
    api_keys = load_api_keys(args.config)
    
    # Initialize scorer
    scorer = SymbolScorer(api_keys=api_keys)
    
    # Parse symbols and strategies
    symbols = args.symbols.split(',')
    
    if args.strategies:
        strategies = args.strategies.split(',')
    else:
        # Use default strategies
        strategies = [
            "Momentum", 
            "Trend Following", 
            "Breakout", 
            "Mean Reversion"
        ]
    
    logger.info("Scoring %d symbols against %d strategies", len(symbols), len(strategies))
    
    # Get candidates
    candidates = scorer.get_backtest_candidates(symbols, strategies, limit=args.limit)
    
    # Display results
    print("\nTop Backtest Candidates:")
    print("========================\n")
    
    for i, candidate in enumerate(candidates):
        print(f"{i+1}. {candidate['symbol']} - {candidate['strategy']} (Score: {candidate['score']:.2f})")
        print(f"   Sector: {candidate['sector']}")
        
        # Show component scores
        components = candidate['component_scores']
        print(f"   News Sentiment: {components['news_sentiment']:.2f}, " +
              f"News Volume: {components['news_volume']:.2f}, " +
              f"Momentum: {components['price_momentum']:.2f}")
        print(f"   Volume: {components['volume_anomaly']:.2f}, " +
              f"Sector: {components['sector_relative']:.2f}, " +
              f"Vol Regime: {components['volatility_regime']:.2f}")
        print()
    
    # Optionally save results
    if args.output:
        result_df = pd.DataFrame([
            {
                "symbol": c["symbol"],
                "strategy": c["strategy"],
                "score": c["score"],
                "sector": c["sector"],
                "news_sentiment": c["component_scores"]["news_sentiment"],
                "news_volume": c["component_scores"]["news_volume"],
                "price_momentum": c["component_scores"]["price_momentum"],
                "volume_anomaly": c["component_scores"]["volume_anomaly"],
                "sector_relative": c["component_scores"]["sector_relative"],
                "volatility_regime": c["component_scores"]["volatility_regime"]
            }
            for c in candidates
        ])
        
        result_df.to_csv(args.output, index=False)
        print(f"Results saved to {args.output}")

def analyze_results(args):
    """Analyze backtest results and generate performance reports."""
    logger.info("Analyzing backtest results from %s", args.results_dir)
    
    # Check if directory exists
    if not os.path.exists(args.results_dir):
        logger.error("Results directory %s not found", args.results_dir)
        return
    
    # Find all result files
    result_files = [f for f in os.listdir(args.results_dir) if f.endswith('.json')]
    
    if not result_files:
        logger.warning("No result files found in %s", args.results_dir)
        return
    
    logger.info("Found %d result files", len(result_files))
    
    # Load results
    results = []
    for filename in result_files:
        try:
            with open(os.path.join(args.results_dir, filename), 'r') as f:
                result = json.load(f)
            
            # Parse key from filename (format: symbol_strategy_timestamp.json)
            parts = filename.split('_')
            if len(parts) >= 2:
                result['symbol'] = parts[0]
                result['strategy'] = parts[1]
            
            results.append(result)
        except Exception as e:
            logger.error("Error loading result file %s: %s", filename, str(e))
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Print summary statistics
    print("\nBacktest Results Summary")
    print("=======================\n")
    
    # Overall metrics
    print(f"Total backtests: {len(df)}")
    print(f"Average Sharpe: {df['sharpe'].mean():.2f}")
    print(f"Average Win Rate: {df['winrate'].mean():.1f}%")
    print(f"Average Profit Factor: {df['profit_factor'].mean():.2f}")
    print(f"Average Max Drawdown: {df['max_drawdown'].mean():.1f}%")
    print()
    
    # Best performers by Sharpe
    print("Top 5 Strategies by Sharpe Ratio:")
    top_sharpe = df.sort_values('sharpe', ascending=False).head(5)
    for _, row in top_sharpe.iterrows():
        print(f"  {row['symbol']} - {row['strategy']}: Sharpe {row['sharpe']:.2f}, "
              f"Win Rate {row['winrate']:.1f}%, Max DD {row['max_drawdown']:.1f}%")
    print()
    
    # Strategy performance
    print("Performance by Strategy Type:")
    strategy_perf = df.groupby('strategy').agg({
        'sharpe': 'mean',
        'winrate': 'mean',
        'profit_factor': 'mean',
        'max_drawdown': 'mean',
        'symbol': 'count'
    }).rename(columns={'symbol': 'count'}).sort_values('sharpe', ascending=False)
    
    for strategy, row in strategy_perf.iterrows():
        print(f"  {strategy} ({row['count']} tests): "
              f"Sharpe {row['sharpe']:.2f}, Win Rate {row['winrate']:.1f}%, "
              f"Profit Factor {row['profit_factor']:.2f}")
    
    # Save analysis if requested
    if args.output:
        # Strategy performance to CSV
        strategy_perf.to_csv(args.output)
        
        # Create summary file
        summary_file = os.path.splitext(args.output)[0] + "_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("AutoBacktest Analysis Summary\n")
            f.write("============================\n\n")
            f.write(f"Generated: {datetime.datetime.now()}\n\n")
            
            f.write(f"Total backtests: {len(df)}\n")
            f.write(f"Average Sharpe: {df['sharpe'].mean():.2f}\n")
            f.write(f"Average Win Rate: {df['winrate'].mean():.1f}%\n")
            f.write(f"Average Profit Factor: {df['profit_factor'].mean():.2f}\n")
            f.write(f"Average Max Drawdown: {df['max_drawdown'].mean():.1f}%\n\n")
            
            f.write("Top 5 Strategies by Sharpe Ratio:\n")
            for _, row in top_sharpe.iterrows():
                f.write(f"  {row['symbol']} - {row['strategy']}: Sharpe {row['sharpe']:.2f}, "
                      f"Win Rate {row['winrate']:.1f}%, Max DD {row['max_drawdown']:.1f}%\n")
        
        print(f"Analysis saved to {args.output} and {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="AutoBacktest - Autonomous Backtesting System")
    parser.add_argument('--mode', choices=['scheduler', 'score', 'analyze'], default='scheduler',
                      help='Operation mode')
    
    # General options
    parser.add_argument('--config', default='config.json',
                      help='Configuration file path')
    parser.add_argument('--data-dir', default='data',
                      help='Data directory for results and settings')
    
    # Scheduler options
    parser.add_argument('--daily-limit', type=int, default=50,
                      help='Maximum number of backtests per day')
    parser.add_argument('--concurrent', type=int, default=3,
                      help='Maximum number of concurrent backtests')
    parser.add_argument('--interval', type=int, default=300,
                      help='Scheduler loop interval in seconds')
    parser.add_argument('--watchlist-size', type=int, default=40,
                      help='Size of dynamic watchlist')
    parser.add_argument('--refresh-interval', type=int, default=12,
                      help='Hours between watchlist refreshes')
    parser.add_argument('--watchlist', 
                      help='Path to file with custom watchlist (one symbol per line)')
    
    # Scoring options
    parser.add_argument('--symbols', default='AAPL,MSFT,GOOGL,AMZN,TSLA',
                      help='Comma-separated list of symbols to score')
    parser.add_argument('--strategies',
                      help='Comma-separated list of strategies to score against')
    parser.add_argument('--limit', type=int, default=10,
                      help='Maximum number of results to show for scoring')
    
    # Analysis options
    parser.add_argument('--results-dir', default='data/results',
                      help='Directory containing backtest results')
    
    # Output options
    parser.add_argument('--output', 
                      help='Output file path for analysis or scoring results')
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(os.path.join(args.data_dir, 'results'), exist_ok=True)
    
    # Execute selected mode
    if args.mode == 'scheduler':
        run_scheduler(args)
    elif args.mode == 'score':
        score_symbols(args)
    elif args.mode == 'analyze':
        analyze_results(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unhandled exception: %s", str(e), exc_info=True)
        sys.exit(1) 