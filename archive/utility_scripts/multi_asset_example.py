#!/usr/bin/env python3
"""
Example script demonstrating the MultiAssetAdapter usage for trading across
multiple asset classes with a unified interface.
"""

import os
import sys
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import MultiAssetAdapter
from multi_asset_adapter import MultiAssetAdapter

def main():
    """Main function demonstrating multi-asset adapter usage."""
    
    # Initialize adapter with configuration for different asset classes
    adapter_config = {
        "forex": {
            "broker_id": "oanda",
            "api_key": os.environ.get("OANDA_API_KEY"),
            "account_id": os.environ.get("OANDA_ACCOUNT_ID"),
            "environment": "practice"
        },
        "crypto": {
            "broker_id": "binance",
            "api_key": os.environ.get("BINANCE_API_KEY"),
            "api_secret": os.environ.get("BINANCE_API_SECRET")
        },
        "stocks": {
            "broker_id": "alpaca",
            "api_key": os.environ.get("ALPACA_API_KEY"),
            "api_secret": os.environ.get("ALPACA_API_SECRET")
        }
    }
    
    # Create adapter
    multi_adapter = MultiAssetAdapter(config=adapter_config)
    
    # Example 1: Get current prices for assets across different classes
    print("\n===== Example 1: Getting current prices across asset classes =====")
    symbols = ["EUR/USD", "BTC/USDT", "AAPL"]
    
    for symbol in symbols:
        price_info = multi_adapter.get_current_price(symbol)
        asset_class = multi_adapter.detect_asset_class(symbol)
        print(f"{symbol} ({asset_class}): Mid = {price_info['mid']}, Spread = {price_info['spread']}")
    
    # Example 2: Get historical data for different assets
    print("\n===== Example 2: Getting historical data across asset classes =====")
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = datetime.now().isoformat()
    
    historical_data = multi_adapter.get_historical_market_data(
        symbols=symbols,
        timeframe="D1",
        start=start_date,
        end=end_date
    )
    
    for symbol, data in historical_data.items():
        if not data.empty:
            print(f"{symbol}: {len(data)} candles retrieved")
            # Print the last candle
            last_candle = data.iloc[-1]
            print(f"Last candle: Open={last_candle['open']}, High={last_candle['high']}, "
                  f"Low={last_candle['low']}, Close={last_candle['close']}")
    
    # Example 3: Display account summaries
    print("\n===== Example 3: Account summaries by asset class =====")
    account_info = multi_adapter.get_account_summary()
    
    for asset_class, summary in account_info.items():
        if asset_class != 'total' and isinstance(summary, dict) and 'balance' in summary:
            print(f"{asset_class.upper()}: Balance={summary['balance']}, "
                  f"Unrealized P/L={summary['unrealized_pl']}, "
                  f"Margin Available={summary['margin_available']}")
    
    if 'total' in account_info:
        total = account_info['total']
        print(f"\nTOTAL: Balance={total['balance']}, "
              f"Unrealized P/L={total['unrealized_pl']}")
    
    # Example 4: Place example orders (uncomment to execute)
    print("\n===== Example 4: Placing orders across asset classes =====")
    # WARNING: Uncommenting these lines will place real orders if connected to live accounts
    """
    # Forex order
    forex_order = multi_adapter.place_market_order(
        symbol="EUR/USD",
        units=1000,  # Buy 1000 units (0.01 lots)
        stop_loss=1.0900,
        take_profit=1.1000
    )
    print(f"Forex order placed: {forex_order}")
    
    # Crypto order
    crypto_order = multi_adapter.place_market_order(
        symbol="BTC/USDT",
        units=0.001,  # Buy 0.001 BTC
        stop_loss=30000,
        take_profit=35000
    )
    print(f"Crypto order placed: {crypto_order}")
    
    # Stock order
    stock_order = multi_adapter.place_market_order(
        symbol="AAPL",
        units=1,  # Buy 1 share
        stop_loss=170,
        take_profit=190
    )
    print(f"Stock order placed: {stock_order}")
    """
    
    # Example 5: Show open positions
    print("\n===== Example 5: Open positions across asset classes =====")
    positions = multi_adapter.get_open_positions()
    
    if positions:
        for position in positions:
            print(f"Position: {position['symbol']} ({position['asset_class']}), "
                  f"Units: {position['units']}, P/L: {position['unrealized_pl']}")
    else:
        print("No open positions found.")
    
    # Example 6: Portfolio statistics
    print("\n===== Example 6: Portfolio statistics =====")
    stats = multi_adapter.calculate_portfolio_stats()
    
    print(f"Total positions: {stats['total_positions']}")
    print(f"Total exposure: {stats['total_exposure']}")
    print(f"Unrealized P/L: {stats['unrealized_pl']}")
    
    if stats['asset_class_exposure']:
        print("\nAsset Class Exposure:")
        for asset_class, exposure in stats['asset_class_exposure'].items():
            if isinstance(exposure, dict):
                print(f"  {asset_class}: {exposure['value']} ({exposure['percentage']:.2f}%)")
            else:
                print(f"  {asset_class}: {exposure}")
    
    # Example 7: Get economic calendar events
    print("\n===== Example 7: Economic and earnings calendar =====")
    calendar_start = (datetime.now() - timedelta(days=7)).isoformat()
    calendar_end = (datetime.now() + timedelta(days=7)).isoformat()
    
    events = multi_adapter.get_calendar_events(
        start=calendar_start,
        end=calendar_end,
        event_types=["high_impact", "earnings"]
    )
    
    if not events.empty:
        print(f"Found {len(events)} upcoming events:")
        for _, event in events.head(5).iterrows():
            event_time = event.get('time', 'Unknown time')
            event_title = event.get('title', event.get('description', 'Unknown event'))
            asset_class = event.get('asset_class', 'Unknown')
            print(f"  {event_time}: {event_title} ({asset_class})")
        
        if len(events) > 5:
            print(f"  ... and {len(events) - 5} more events")
    else:
        print("No upcoming events found.")
    
    # Disconnect from all brokers
    multi_adapter.disconnect()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}", exc_info=True)
    finally:
        print("\nExecution completed.") 