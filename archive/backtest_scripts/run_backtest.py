#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Backtester with Alpha Vantage Data

This script runs a backtest for various trading strategies using data 
from the Alpha Vantage API.
"""

import os
import argparse
import json
import logging
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

from trading.backtester import Backtester

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_backtest')

def load_config(config_file: str = None) -> dict:
    """
    Load configuration from file or use defaults
    
    Parameters:
    -----------
    config_file : str, optional
        Path to configuration file
        
    Returns:
    --------
    dict
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        "initial_capital": 100000.0,
        "position_size": 0.2,
        "commission": 0.001,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.1,
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "start_date": (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        "end_date": datetime.now().strftime('%Y-%m-%d'),
        "strategy": "sma_crossover",
        "strategy_params": {
            "sma_crossover": {
                "short_window": 20,
                "long_window": 50
            },
            "rsi": {
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70
            },
            "macd": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "bollinger_bands": {
                "window": 20,
                "num_std": 2
            }
        },
        "output_dir": "results"
    }
    
    # Try to load configuration from file
    if config_file:
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                
            # Update default config with user config
            for key, value in user_config.items():
                if key == 'strategy_params' and key in default_config:
                    for strategy, params in value.items():
                        if strategy in default_config[key]:
                            default_config[key][strategy].update(params)
                        else:
                            default_config[key][strategy] = params
                else:
                    default_config[key] = value
                    
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            logger.info("Using default configuration")
    
    return default_config

def run_backtest(config: dict) -> dict:
    """
    Run a backtest with the given configuration
    
    Parameters:
    -----------
    config : dict
        Configuration dictionary
        
    Returns:
    --------
    dict
        Backtest results
    """
    # Create backtester
    backtester = Backtester(
        initial_capital=config['initial_capital'],
        position_size_pct=config['position_size'],
        commission=config['commission'],
        stop_loss_pct=config['stop_loss_pct'],
        take_profit_pct=config['take_profit_pct'],
        api_key=config.get('alpha_vantage_api_key'),
        use_mock_data=config.get('use_mock_data')
    )
    
    # Get strategy parameters
    strategy = config['strategy']
    strategy_params = config['strategy_params'].get(strategy, {})
    
    # Load market data
    backtester.load_data(
        symbols=config['symbols'],
        start_date=config['start_date'],
        end_date=config['end_date']
    )
    
    # Run backtest
    results = backtester.run_backtest(
        strategy_name=strategy,
        symbols=config['symbols'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        strategy_params=strategy_params
    )
    
    # Create output directory
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = output_dir / f"{strategy}_backtest_{timestamp}.json"
    backtester.save_results(save_path)
    
    # Plot results
    plot_path = output_dir / f"{strategy}_backtest_{timestamp}.png"
    backtester.plot_results(save_path=plot_path)
    
    return results

def print_results(results: dict):
    """
    Print a summary of the backtest results
    
    Parameters:
    -----------
    results : dict
        Backtest results
    """
    print("\n" + "="*80)
    print(f"BACKTEST RESULTS: {results['strategy']} Strategy")
    print("="*80)
    print(f"Symbols: {', '.join(results['symbols'])}")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print("-"*80)
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Equity: ${results['final_equity']:,.2f}")
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Annualized Return: {results['annualized_return_pct']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print("-"*80)
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']}")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Win Rate: {results['win_rate_pct']:.2f}%")
    print("="*80)
    print(f"Results saved to {results['output_dir']}")

def run_all_strategies(config: dict):
    """
    Run backtests for all available strategies
    
    Parameters:
    -----------
    config : dict
        Configuration dictionary
    """
    all_strategies = list(config['strategy_params'].keys())
    logger.info(f"Running backtests for all strategies: {all_strategies}")
    
    results = {}
    
    for strategy in all_strategies:
        logger.info(f"Running backtest for {strategy} strategy")
        
        # Update strategy in config
        config_copy = config.copy()
        config_copy['strategy'] = strategy
        
        # Run backtest
        results[strategy] = run_backtest(config_copy)
    
    # Compare results
    compare_strategies(results)
    
    return results

def compare_strategies(results: dict):
    """
    Compare the results of multiple strategies
    
    Parameters:
    -----------
    results : dict
        Dictionary of backtest results by strategy
    """
    # Create a new figure
    plt.figure(figsize=(12, 8))
    
    # Sort strategies by performance
    sorted_strategies = sorted(
        results.keys(),
        key=lambda s: results[s]['total_return_pct'],
        reverse=True
    )
    
    # Plot bars for each metric
    metrics = [
        ('total_return_pct', 'Total Return (%)'),
        ('sharpe_ratio', 'Sharpe Ratio'),
        ('win_rate_pct', 'Win Rate (%)'),
        ('max_drawdown_pct', 'Max Drawdown (%)')
    ]
    
    for i, (metric, label) in enumerate(metrics):
        plt.subplot(2, 2, i+1)
        
        values = [results[s][metric] for s in sorted_strategies]
        
        # For drawdown, negate values for better visualization (more negative is worse)
        if metric == 'max_drawdown_pct':
            values = [-v for v in values]
            
        plt.bar(sorted_strategies, values)
        plt.title(label)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path(results[sorted_strategies[0]]['output_dir'])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = output_dir / f"strategy_comparison_{timestamp}.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved strategy comparison to {save_path}")
    
    plt.show()
    
    # Print comparison table
    print("\n" + "="*100)
    print("STRATEGY COMPARISON")
    print("="*100)
    print(f"{'Strategy':<20} {'Return':<10} {'Sharpe':<10} {'Win Rate':<10} {'Drawdown':<10} {'# Trades':<10}")
    print("-"*100)
    
    for strategy in sorted_strategies:
        result = results[strategy]
        print(f"{strategy:<20} "
              f"{result['total_return_pct']:>8.2f}% "
              f"{result['sharpe_ratio']:>8.2f} "
              f"{result['win_rate_pct']:>8.2f}% "
              f"{result['max_drawdown_pct']:>8.2f}% "
              f"{result['total_trades']:>8}")
    
    print("="*100)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run a trading strategy backtest')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--all', action='store_true', help='Run all strategies')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real data')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Check for Alpha Vantage API key
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if api_key:
        config['alpha_vantage_api_key'] = api_key
        
    if 'alpha_vantage_api_key' not in config:
        logger.warning("No Alpha Vantage API key found in config or environment. "
                       "Set the ALPHA_VANTAGE_API_KEY environment variable.")
    
    # Add mock data flag to config
    config['use_mock_data'] = args.mock
    
    # Run backtests
    if args.all:
        results = run_all_strategies(config)
    else:
        results = run_backtest(config)
        print_results(results)
    
    logger.info("Backtest(s) completed successfully")

if __name__ == "__main__":
    main() 