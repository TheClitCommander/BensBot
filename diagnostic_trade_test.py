#!/usr/bin/env python3
"""
Diagnostic script to test if the UnifiedBacktester is correctly executing trades
"""

from trading_bot.backtesting import UnifiedBacktester
import numpy as np
import pandas as pd
import datetime as dt

# Create mock price data
dates = pd.date_range(start='2023-01-01', end='2023-01-31')
prices = pd.DataFrame({
    'AAPL': 100 + np.cumsum(np.random.normal(0, 1, len(dates))),
    'MSFT': 200 + np.cumsum(np.random.normal(0, 1, len(dates))),
    'SPY': 400 + np.cumsum(np.random.normal(0, 1, len(dates)))
}, index=dates)

# Define a simple mock strategy that alternates between stocks
class MockStrategy:
    def __init__(self):
        self.name = 'MockStrategy'
    
    def generate_signal(self, prices, date):
        # Alternate between AAPL and MSFT based on day of month
        day_of_month = date.day
        if day_of_month % 2 == 0:
            return {'AAPL': 1.0, 'MSFT': 0.0, 'SPY': 0.0}
        else:
            return {'AAPL': 0.0, 'MSFT': 1.0, 'SPY': 0.0}

# Initialize and run the backtester
backtester = UnifiedBacktester(
    initial_capital=10000,
    prices=prices,
    strategies=[MockStrategy()],
    start_date=dates[0],
    end_date=dates[-1],
    debug=True  # Enable debug mode
)

# Run the backtest
results = backtester.run_backtest()

# Print diagnostic information
print(f"Number of trades executed: {len(backtester.trades)}")
print(f"Final capital: ${backtester.portfolio_value:.2f}")
print(f"Total return: {((backtester.portfolio_value/10000)-1)*100:.2f}%")

# Print the first few trades
print("\nTrade List:")
for i, trade in enumerate(backtester.trades[:5]):
    print(f"{i+1}. {trade}")

if len(backtester.trades) > 5:
    print("...")

# Print daily portfolio values to check for changes
print("\nDaily Portfolio Values:")
for i, (date, value) in enumerate(backtester.portfolio_values.items()[:5]):
    print(f"{date.strftime('%Y-%m-%d')}: ${value:.2f}")

if len(backtester.portfolio_values) > 5:
    print("...") 