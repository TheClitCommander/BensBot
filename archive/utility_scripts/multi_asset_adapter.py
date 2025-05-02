import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

import pandas as pd
import numpy as np

from forex_broker_adapter import ForexBrokerAdapter

logger = logging.getLogger(__name__)

class MultiAssetAdapter:
    """Adapter for connecting to multiple asset classes across different brokers."""
    
    ASSET_CLASSES = ["forex", "crypto", "stocks", "indices", "commodities", "bonds"]
    
    def __init__(self, config=None):
        """
        Initialize the multi-asset adapter.
        
        Args:
            config: Configuration dictionary with broker settings per asset class
                   Example: {
                       "forex": {"broker_id": "oanda", "api_key": "...", "account_id": "..."},
                       "crypto": {"broker_id": "binance", "api_key": "...", "api_secret": "..."},
                       "stocks": {"broker_id": "alpaca", "api_key": "...", "api_secret": "..."}
                   }
        """
        self.config = config or {}
        self.adapters = {}
        self.asset_class_map = {}  # Maps symbols to asset classes
        self.default_adapter = None
        
        # Initialize adapters for each configured asset class
        for asset_class, broker_config in self.config.items():
            if asset_class not in self.ASSET_CLASSES:
                logger.warning(f"Unknown asset class: {asset_class}")
                continue
                
            try:
                if asset_class == "forex":
                    self.adapters[asset_class] = ForexBrokerAdapter(
                        broker_id=broker_config.get("broker_id", "oanda"),
                        config=broker_config
                    )
                elif asset_class == "crypto":
                    self.adapters[asset_class] = self._create_crypto_adapter(broker_config)
                elif asset_class == "stocks":
                    self.adapters[asset_class] = self._create_stock_adapter(broker_config)
                elif asset_class == "indices":
                    self.adapters[asset_class] = self._create_indices_adapter(broker_config)
                elif asset_class == "commodities":
                    self.adapters[asset_class] = self._create_commodities_adapter(broker_config)
                elif asset_class == "bonds":
                    self.adapters[asset_class] = self._create_bonds_adapter(broker_config)
                    
                # Build symbol to asset class mapping
                self._build_symbol_mapping(asset_class)
                    
                logger.info(f"Initialized adapter for {asset_class} with broker {broker_config.get('broker_id')}")
                
                # Set first configured adapter as default
                if self.default_adapter is None:
                    self.default_adapter = asset_class
                    
            except Exception as e:
                logger.error(f"Error initializing adapter for {asset_class}: {str(e)}")
    
    def _create_crypto_adapter(self, config):
        """Create adapter for cryptocurrency markets."""
        broker_id = config.get("broker_id", "binance")
        
        if broker_id == "binance":
            try:
                from binance_adapter import BinanceAdapter
                return BinanceAdapter(config=config)
            except ImportError:
                # Fallback to generic implementation if custom adapter not available
                return CryptoAdapter(broker_id=broker_id, config=config)
        elif broker_id == "coinbase":
            try:
                from coinbase_adapter import CoinbaseAdapter
                return CoinbaseAdapter(config=config)
            except ImportError:
                return CryptoAdapter(broker_id=broker_id, config=config)
        else:
            return CryptoAdapter(broker_id=broker_id, config=config)
    
    def _create_stock_adapter(self, config):
        """Create adapter for stock markets."""
        broker_id = config.get("broker_id", "alpaca")
        
        if broker_id == "alpaca":
            try:
                from alpaca_adapter import AlpacaAdapter
                return AlpacaAdapter(config=config)
            except ImportError:
                return StockAdapter(broker_id=broker_id, config=config)
        elif broker_id == "ib":
            try:
                from interactive_brokers_adapter import IBAdapter
                return IBAdapter(config=config)
            except ImportError:
                return StockAdapter(broker_id=broker_id, config=config)
        else:
            return StockAdapter(broker_id=broker_id, config=config)
    
    def _create_indices_adapter(self, config):
        """Create adapter for indices markets."""
        # For indices, we can often use the same adapters as for stocks
        # or commodities depending on the broker
        broker_id = config.get("broker_id")
        
        if broker_id in ["ig", "oanda"]:
            # Some forex brokers also offer indices trading
            return ForexBrokerAdapter(broker_id=broker_id, config=config)
        else:
            # Default implementation
            return IndicesAdapter(broker_id=broker_id, config=config)
    
    def _create_commodities_adapter(self, config):
        """Create adapter for commodities markets."""
        broker_id = config.get("broker_id")
        
        if broker_id in ["ig", "oanda"]:
            # Some forex brokers also offer commodities trading
            return ForexBrokerAdapter(broker_id=broker_id, config=config)
        else:
            # Default implementation
            return CommoditiesAdapter(broker_id=broker_id, config=config)
    
    def _create_bonds_adapter(self, config):
        """Create adapter for bond markets."""
        broker_id = config.get("broker_id", "ib")
        
        if broker_id == "ib":
            try:
                from interactive_brokers_adapter import IBAdapter
                return IBAdapter(config=config)
            except ImportError:
                return BondsAdapter(broker_id=broker_id, config=config)
        else:
            return BondsAdapter(broker_id=broker_id, config=config)
    
    def _build_symbol_mapping(self, asset_class):
        """Build mapping from symbols to asset classes."""
        adapter = self.adapters[asset_class]
        
        if hasattr(adapter, 'instruments') and adapter.instruments:
            for symbol in adapter.instruments.keys():
                self.asset_class_map[symbol] = asset_class
                
                # Also add common variations of the symbol for ease of use
                if asset_class == "forex" and "_" in symbol:
                    # Map EUR_USD to EUR/USD
                    alt_symbol = symbol.replace("_", "/")
                    self.asset_class_map[alt_symbol] = asset_class
                elif asset_class == "crypto" and not "/" in symbol:
                    # Map BTCUSDT to BTC/USDT
                    for stable in ["USDT", "USD", "BUSD", "USDC"]:
                        if symbol.endswith(stable):
                            base = symbol[:-len(stable)]
                            alt_symbol = f"{base}/{stable}"
                            self.asset_class_map[alt_symbol] = asset_class
    
    def detect_asset_class(self, symbol):
        """
        Detect asset class from symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Detected asset class or None if unknown
        """
        # First, check if we have this symbol in our mapping
        if symbol in self.asset_class_map:
            return self.asset_class_map[symbol]
        
        # Common patterns for different asset classes
        if "/" in symbol:
            # EUR/USD format is typically forex
            # BTC/USDT format could be crypto
            quote = symbol.split("/")[1]
            if quote in ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]:
                return "forex"
            elif quote in ["USDT", "USDC", "BUSD", "BTC", "ETH"]:
                return "crypto"
        
        if "_" in symbol:
            # EUR_USD format is typically forex
            quote = symbol.split("_")[1]
            if quote in ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]:
                return "forex"
        
        # Common crypto patterns
        if symbol.endswith("USDT") or symbol.endswith("BTC"):
            return "crypto"
        
        # Stock symbols are typically 1-5 uppercase letters
        if symbol.isupper() and len(symbol) <= 5 and symbol.isalpha():
            return "stocks"
        
        # Common index symbols
        indices = ["SPX", "DJIA", "NDX", "FTSE", "DAX", "NIKKEI", "HSI"]
        if any(idx in symbol for idx in indices):
            return "indices"
        
        # Commodities often have specific prefixes
        commodities = ["GOLD", "SILVER", "OIL", "NATGAS", "CL", "GC", "XAU", "XAG"]
        if any(comm in symbol for comm in commodities):
            return "commodities"
        
        # If we can't detect, use default adapter
        return self.default_adapter
    
    def get_adapter(self, symbol=None, asset_class=None):
        """
        Get the appropriate adapter for a symbol or asset class.
        
        Args:
            symbol: Trading symbol (used to detect asset class if not specified)
            asset_class: Explicit asset class to use
            
        Returns:
            Broker adapter for the detected/specified asset class
        """
        # If asset class is specified directly, use it
        if asset_class and asset_class in self.adapters:
            return self.adapters[asset_class]
        
        # If symbol is provided, detect asset class
        if symbol:
            detected_class = self.detect_asset_class(symbol)
            if detected_class and detected_class in self.adapters:
                return self.adapters[detected_class]
        
        # Fallback to default adapter
        return self.adapters.get(self.default_adapter)
    
    def normalize_symbol(self, symbol, asset_class=None):
        """
        Normalize symbol for the appropriate asset class.
        
        Args:
            symbol: Symbol to normalize
            asset_class: Optional explicit asset class
            
        Returns:
            Normalized symbol for the broker
        """
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.normalize_symbol(symbol)
        return symbol
    
    def get_current_price(self, symbol, asset_class=None):
        """
        Get current price for a symbol across any supported asset class.
        
        Args:
            symbol: Trading symbol
            asset_class: Optional explicit asset class
            
        Returns:
            Price information
        """
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.get_current_price(symbol)
        else:
            logger.error(f"No adapter available for symbol: {symbol}")
            return {
                'symbol': symbol,
                'bid': None,
                'ask': None,
                'mid': None,
                'spread': None,
                'time': datetime.now().isoformat()
            }
    
    def get_historical_data(self, symbol, timeframe='H1', count=100, start=None, end=None, asset_class=None):
        """
        Get historical data for any supported asset.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe (M1, M5, M15, M30, H1, H4, D1, W1, etc.)
            count: Number of candles to fetch (if start/end not provided)
            start: Start time (if specified, count is ignored)
            end: End time (if not specified, current time is used)
            asset_class: Optional explicit asset class
            
        Returns:
            DataFrame with OHLC data
        """
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.get_historical_data(symbol, timeframe, count, start, end)
        else:
            logger.error(f"No adapter available for symbol: {symbol}")
            return pd.DataFrame()
    
    def place_market_order(self, symbol, units, stop_loss=None, take_profit=None, asset_class=None, **kwargs):
        """
        Place a market order for any supported asset.
        
        Args:
            symbol: Trading symbol
            units: Number of units (positive for buy, negative for sell)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            asset_class: Optional explicit asset class
            kwargs: Additional broker-specific parameters
            
        Returns:
            Order information
        """
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.place_market_order(symbol, units, stop_loss, take_profit, **kwargs)
        else:
            logger.error(f"No adapter available for symbol: {symbol}")
            return {
                'status': 'error',
                'message': f"No adapter available for symbol: {symbol}",
                'symbol': symbol
            }
    
    def place_limit_order(self, symbol, units, price, stop_loss=None, take_profit=None, asset_class=None, **kwargs):
        """
        Place a limit order for any supported asset.
        
        Args:
            symbol: Trading symbol
            units: Number of units (positive for buy, negative for sell)
            price: Limit price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            asset_class: Optional explicit asset class
            kwargs: Additional broker-specific parameters
            
        Returns:
            Order information
        """
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.place_limit_order(symbol, units, price, stop_loss, take_profit, **kwargs)
        else:
            logger.error(f"No adapter available for symbol: {symbol}")
            return {
                'status': 'error',
                'message': f"No adapter available for symbol: {symbol}",
                'symbol': symbol
            }
    
    def close_position(self, symbol=None, trade_id=None, units=None, asset_class=None):
        """
        Close a position for any supported asset.
        
        Args:
            symbol: Trading symbol (required if trade_id not provided)
            trade_id: Specific trade ID to close (optional)
            units: Number of units to close (optional, defaults to all)
            asset_class: Optional explicit asset class
            
        Returns:
            Close transaction information
        """
        # If we have a trade_id but no symbol, find the appropriate adapter
        if trade_id and not symbol:
            for asset_class, adapter in self.adapters.items():
                try:
                    result = adapter.close_position(trade_id=trade_id, units=units)
                    if result.get('status') != 'error':
                        return result
                except:
                    continue
            
            logger.error(f"Could not find adapter for trade_id: {trade_id}")
            return {
                'status': 'error',
                'message': f"Could not find adapter for trade_id: {trade_id}",
                'trade_id': trade_id
            }
        
        # If we have a symbol, use the appropriate adapter
        adapter = self.get_adapter(symbol, asset_class)
        if adapter:
            return adapter.close_position(symbol=symbol, trade_id=trade_id, units=units)
        else:
            logger.error(f"No adapter available for symbol: {symbol}")
            return {
                'status': 'error',
                'message': f"No adapter available for symbol: {symbol}",
                'symbol': symbol
            }
    
    def modify_position(self, trade_id, stop_loss=None, take_profit=None, asset_class=None, **kwargs):
        """
        Modify an existing position for any supported asset.
        
        Args:
            trade_id: Trade ID to modify
            stop_loss: New stop loss price (or None to leave unchanged)
            take_profit: New take profit price (or None to leave unchanged)
            asset_class: Optional explicit asset class
            kwargs: Additional broker-specific parameters
            
        Returns:
            Modification status
        """
        # If asset_class is specified, use that adapter
        if asset_class and asset_class in self.adapters:
            return self.adapters[asset_class].modify_position(
                trade_id, stop_loss, take_profit, **kwargs
            )
        
        # Otherwise, try each adapter until one works
        for asset_class, adapter in self.adapters.items():
            try:
                result = adapter.modify_position(trade_id, stop_loss, take_profit, **kwargs)
                if result.get('status') != 'error':
                    return result
            except:
                continue
        
        logger.error(f"Could not find adapter for trade_id: {trade_id}")
        return {
            'status': 'error',
            'message': f"Could not find adapter for trade_id: {trade_id}",
            'trade_id': trade_id
        }
    
    def get_open_positions(self, asset_class=None):
        """
        Get all open positions across all asset classes or for a specific asset class.
        
        Args:
            asset_class: Optional asset class to filter by
            
        Returns:
            List of open positions
        """
        positions = []
        
        if asset_class and asset_class in self.adapters:
            # Get positions for a specific asset class
            try:
                adapter_positions = self.adapters[asset_class].get_open_positions()
                for position in adapter_positions:
                    position['asset_class'] = asset_class
                positions.extend(adapter_positions)
            except Exception as e:
                logger.error(f"Error getting positions for {asset_class}: {str(e)}")
        else:
            # Get positions for all asset classes
            for asset_class, adapter in self.adapters.items():
                try:
                    adapter_positions = adapter.get_open_positions()
                    for position in adapter_positions:
                        position['asset_class'] = asset_class
                    positions.extend(adapter_positions)
                except Exception as e:
                    logger.error(f"Error getting positions for {asset_class}: {str(e)}")
        
        return positions
    
    def get_account_summary(self, asset_class=None):
        """
        Get account summary for all asset classes or a specific one.
        
        Args:
            asset_class: Optional asset class to filter by
            
        Returns:
            Dictionary with account information by asset class
        """
        summary = {}
        
        if asset_class and asset_class in self.adapters:
            # Get summary for a specific asset class
            try:
                summary[asset_class] = self.adapters[asset_class].get_account_summary()
            except Exception as e:
                logger.error(f"Error getting account summary for {asset_class}: {str(e)}")
                summary[asset_class] = {'error': str(e)}
        else:
            # Get summary for all asset classes
            for asset_class, adapter in self.adapters.items():
                try:
                    summary[asset_class] = adapter.get_account_summary()
                except Exception as e:
                    logger.error(f"Error getting account summary for {asset_class}: {str(e)}")
                    summary[asset_class] = {'error': str(e)}
        
        # Add a total row if we have multiple asset classes
        if len(summary) > 1:
            total = {
                'balance': 0,
                'unrealized_pl': 0,
                'margin_used': 0,
                'margin_available': 0
            }
            
            for asset_data in summary.values():
                # Only add if we have valid data
                if isinstance(asset_data, dict) and 'balance' in asset_data:
                    total['balance'] += asset_data.get('balance', 0)
                    total['unrealized_pl'] += asset_data.get('unrealized_pl', 0)
                    total['margin_used'] += asset_data.get('margin_used', 0)
                    total['margin_available'] += asset_data.get('margin_available', 0)
            
            summary['total'] = total
        
        return summary
    
    def get_pending_orders(self, asset_class=None):
        """
        Get pending orders across all asset classes or for a specific asset class.
        
        Args:
            asset_class: Optional asset class to filter by
            
        Returns:
            List of pending orders
        """
        orders = []
        
        if asset_class and asset_class in self.adapters:
            # Get orders for a specific asset class
            try:
                adapter_orders = self.adapters[asset_class].get_pending_orders()
                for order in adapter_orders:
                    order['asset_class'] = asset_class
                orders.extend(adapter_orders)
            except Exception as e:
                logger.error(f"Error getting pending orders for {asset_class}: {str(e)}")
        else:
            # Get orders for all asset classes
            for asset_class, adapter in self.adapters.items():
                try:
                    adapter_orders = adapter.get_pending_orders()
                    for order in adapter_orders:
                        order['asset_class'] = asset_class
                    orders.extend(adapter_orders)
                except Exception as e:
                    logger.error(f"Error getting pending orders for {asset_class}: {str(e)}")
        
        return orders
    
    def cancel_order(self, order_id, asset_class=None):
        """
        Cancel a pending order.
        
        Args:
            order_id: ID of the order to cancel
            asset_class: Optional asset class
            
        Returns:
            Cancellation status
        """
        if asset_class and asset_class in self.adapters:
            return self.adapters[asset_class].cancel_order(order_id)
        
        # If no asset class specified, try each adapter
        for asset_class, adapter in self.adapters.items():
            try:
                result = adapter.cancel_order(order_id)
                if result.get('status') != 'error':
                    return result
            except:
                continue
        
        logger.error(f"Could not find adapter for order_id: {order_id}")
        return {
            'status': 'error',
            'message': f"Could not find adapter for order_id: {order_id}",
            'order_id': order_id
        }
    
    def get_historical_market_data(self, symbols, timeframe='D1', start=None, end=None, count=100):
        """
        Get historical data for multiple symbols across different asset classes.
        
        Args:
            symbols: List of symbols to fetch
            timeframe: Candle timeframe (M1, M5, M15, M30, H1, H4, D1, W1, etc.)
            start: Start time (if specified, count is ignored)
            end: End time (if not specified, current time is used)
            count: Number of candles to fetch (if start/end not provided)
            
        Returns:
            Dictionary mapping symbols to their historical data DataFrames
        """
        result = {}
        
        for symbol in symbols:
            try:
                asset_class = self.detect_asset_class(symbol)
                adapter = self.get_adapter(symbol, asset_class)
                
                if adapter:
                    data = adapter.get_historical_data(
                        symbol, timeframe=timeframe, count=count, start=start, end=end
                    )
                    result[symbol] = data
                else:
                    logger.warning(f"No adapter available for symbol: {symbol}")
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        
        return result
    
    def get_calendar_events(self, symbols=None, start=None, end=None, event_types=None):
        """
        Get economic calendar events that might impact the market.
        
        Args:
            symbols: Optional list of symbols to filter events by related asset
            start: Start time for events
            end: End time for events
            event_types: Types of events to include (e.g., 'high_impact', 'fomc', 'earnings')
            
        Returns:
            DataFrame with calendar events
        """
        events = []
        
        # Economic calendar events usually from forex adapters
        if "forex" in self.adapters:
            try:
                if hasattr(self.adapters["forex"], 'get_economic_calendar'):
                    forex_events = self.adapters["forex"].get_economic_calendar(
                        start=start, end=end, importance=event_types
                    )
                    for event in forex_events:
                        event['asset_class'] = 'forex'
                    events.extend(forex_events)
            except Exception as e:
                logger.error(f"Error getting forex calendar events: {str(e)}")
        
        # Earnings events usually from stock adapters
        if "stocks" in self.adapters:
            try:
                if hasattr(self.adapters["stocks"], 'get_earnings_calendar'):
                    stock_events = self.adapters["stocks"].get_earnings_calendar(
                        symbols=symbols, start=start, end=end
                    )
                    for event in stock_events:
                        event['asset_class'] = 'stocks'
                        event['type'] = 'earnings'
                    events.extend(stock_events)
            except Exception as e:
                logger.error(f"Error getting stock earnings events: {str(e)}")
        
        # Convert to DataFrame for easier filtering and sorting
        if events:
            df = pd.DataFrame(events)
            
            # Sort by time
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values('time')
            
            # Filter by symbols if provided
            if symbols and 'currency' in df.columns:
                df = df[df['currency'].isin(symbols)]
            
            return df
        else:
            return pd.DataFrame()
    
    def calculate_portfolio_stats(self):
        """
        Calculate portfolio statistics across all asset classes.
        
        Returns:
            Dictionary with portfolio statistics
        """
        # Get all open positions
        positions = self.get_open_positions()
        
        if not positions:
            return {
                'total_positions': 0,
                'total_exposure': 0,
                'asset_class_exposure': {},
                'direction_exposure': {'long': 0, 'short': 0},
                'unrealized_pl': 0
            }
        
        # Calculate statistics
        total_exposure = 0
        asset_class_exposure = {}
        direction_exposure = {'long': 0, 'short': 0}
        unrealized_pl = 0
        
        for position in positions:
            # Get position value (use 'margin_used' if available, otherwise estimate)
            position_value = position.get('margin_used', 0)
            if position_value == 0 and 'units' in position:
                # Try to estimate position value
                asset_class = position.get('asset_class')
                adapter = self.adapters.get(asset_class)
                if adapter:
                    try:
                        position_value = adapter.calculate_position_value(
                            position['symbol'], position['units']
                        ) or 0
                    except:
                        # If calculation fails, use a simple estimate
                        position_value = abs(position['units'] * position.get('current_price', 0))
            
            # Update total exposure
            total_exposure += position_value
            
            # Update asset class exposure
            asset_class = position.get('asset_class')
            if asset_class:
                if asset_class not in asset_class_exposure:
                    asset_class_exposure[asset_class] = 0
                asset_class_exposure[asset_class] += position_value
            
            # Update direction exposure
            direction = position.get('direction', 'long' if position.get('units', 0) > 0 else 'short')
            direction_exposure[direction] += position_value
            
            # Update unrealized P/L
            unrealized_pl += position.get('unrealized_pl', 0)
        
        # Calculate percentages
        if total_exposure > 0:
            for asset_class in asset_class_exposure:
                asset_class_exposure[asset_class] = {
                    'value': asset_class_exposure[asset_class],
                    'percentage': (asset_class_exposure[asset_class] / total_exposure) * 100
                }
            
            direction_exposure = {
                'long': {
                    'value': direction_exposure['long'],
                    'percentage': (direction_exposure['long'] / total_exposure) * 100
                },
                'short': {
                    'value': direction_exposure['short'],
                    'percentage': (direction_exposure['short'] / total_exposure) * 100
                }
            }
        
        return {
            'total_positions': len(positions),
            'total_exposure': total_exposure,
            'asset_class_exposure': asset_class_exposure,
            'direction_exposure': direction_exposure,
            'unrealized_pl': unrealized_pl
        }
    
    def disconnect(self):
        """Disconnect from all brokers."""
        status = {}
        
        for asset_class, adapter in self.adapters.items():
            try:
                result = adapter.disconnect()
                status[asset_class] = result
            except Exception as e:
                logger.error(f"Error disconnecting from {asset_class} adapter: {str(e)}")
                status[asset_class] = {'status': 'error', 'message': str(e)}
        
        return status
    
    def __del__(self):
        """Class destructor - ensure clean disconnect from all brokers."""
        try:
            self.disconnect()
        except:
            pass


# Placeholder classes for other asset adapters
# These would be implemented in separate files

class CryptoAdapter:
    """Base adapter for cryptocurrency exchanges."""
    
    def __init__(self, broker_id="binance", config=None):
        self.broker_id = broker_id
        self.config = config or {}
        # Implementation would be similar to ForexBrokerAdapter
        logger.info(f"Initialized CryptoAdapter for {broker_id}")


class StockAdapter:
    """Base adapter for stock brokers."""
    
    def __init__(self, broker_id="alpaca", config=None):
        self.broker_id = broker_id
        self.config = config or {}
        # Implementation would be similar to ForexBrokerAdapter
        logger.info(f"Initialized StockAdapter for {broker_id}")


class IndicesAdapter:
    """Base adapter for indices."""
    
    def __init__(self, broker_id="ig", config=None):
        self.broker_id = broker_id
        self.config = config or {}
        # Implementation would be similar to ForexBrokerAdapter
        logger.info(f"Initialized IndicesAdapter for {broker_id}")


class CommoditiesAdapter:
    """Base adapter for commodities."""
    
    def __init__(self, broker_id="ig", config=None):
        self.broker_id = broker_id
        self.config = config or {}
        # Implementation would be similar to ForexBrokerAdapter
        logger.info(f"Initialized CommoditiesAdapter for {broker_id}")


class BondsAdapter:
    """Base adapter for bonds."""
    
    def __init__(self, broker_id="ib", config=None):
        self.broker_id = broker_id
        self.config = config or {}
        # Implementation would be similar to ForexBrokerAdapter
        logger.info(f"Initialized BondsAdapter for {broker_id}") 