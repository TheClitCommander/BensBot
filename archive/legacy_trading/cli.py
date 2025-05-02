#!/usr/bin/env python3
import argparse
import json
import logging
import os
from pathlib import Path
from datetime import datetime

from trading.backtester import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cli')

def main():
    """Main entry point for the trading backtester CLI"""
    parser = argparse.ArgumentParser(description='Trading Strategy Backtester')
    
    parser.add_argument('--config', type=str, default='test_config.json',
                        help='Path to configuration file (default: test_config.json)')
    parser.add_argument('--results-dir', type=str, default='results',
                        help='Directory to save results (default: results)')
    parser.add_argument('--plot', action='store_true',
                        help='Plot the backtest results')
    parser.add_argument('--use-mock-data', action='store_true',
                        help='Use mock data instead of real data')
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        return
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    logger.info(f"Loaded configuration from {args.config}")
    
    # Extract configuration parameters
    initial_capital = config.get('initial_capital', 100000.0)
    position_size = config.get('position_size', 0.2)
    commission = config.get('commission', 0.001)
    stop_loss_pct = config.get('stop_loss_pct')
    take_profit_pct = config.get('take_profit_pct')
    symbols = config.get('symbols', ['AAPL'])
    start_date = config.get('start_date', '2023-01-01')
    end_date = config.get('end_date', '2023-03-01')
    strategy = config.get('strategy', 'sma_crossover')
    strategy_params = config.get('strategy_params', {}).get(strategy, {})
    alpha_vantage_api_key = config.get('alpha_vantage_api_key')
    
    # Create backtester
    backtester = Backtester(
        initial_capital=initial_capital,
        position_size=position_size,
        commission=commission,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        api_key=alpha_vantage_api_key,
        use_mock_data=args.use_mock_data
    )
    
    # Create results directory if it doesn't exist
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Run backtest
    logger.info(f"Running backtest for {strategy} strategy on {len(symbols)} symbols")
    results = backtester.run_backtest(
        strategy_name=strategy,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strategy_params=strategy_params
    )
    
    # Generate timestamp for results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save results
    results_file = results_dir / f"{strategy}_{timestamp}.json"
    backtester.save_results(str(results_file))
    
    # Plot results if requested
    if args.plot:
        plot_file = results_dir / f"{strategy}_{timestamp}.png"
        backtester.plot_results(save_path=str(plot_file))
    
    # Print summary
    print("\n===== Backtest Results =====")
    print(f"Strategy: {strategy}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Equity: ${results['final_equity']:,.2f}")
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Annualized Return: {results['annualized_return_pct']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate_pct']:.2f}%")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    print(f"Results saved to: {results_file}")
    if args.plot:
        print(f"Plot saved to: {plot_file}")
    print("============================\n")

if __name__ == "__main__":
    main() 