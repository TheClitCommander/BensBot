import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class TradierClient:
    """
    Client for interacting with the Tradier Brokerage API
    
    Handles authentication, account data, market data and order execution
    """
    
    # API endpoints for sandbox and production
    SANDBOX_BASE_URL = "https://sandbox.tradier.com/v1"
    PRODUCTION_BASE_URL = "https://api.tradier.com/v1"
    
    def __init__(self, api_key: str, account_id: str, sandbox: bool = True):
        """
        Initialize the Tradier client
        
        Args:
            api_key: Tradier API access token
            account_id: Tradier account ID
            sandbox: Whether to use the sandbox environment (default: True)
        """
        self.api_key = api_key
        self.account_id = account_id
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL
        
        # Standard headers for all requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        # Cache for market data to reduce API calls
        self.quote_cache = {}
        self.quote_cache_expiry = {}
        self.quote_cache_duration = 10  # seconds
        
        logger.info(f"Tradier client initialized for account {account_id} in {'sandbox' if sandbox else 'production'} mode")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the Tradier API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters (for GET requests)
            data: Form data (for POST requests)
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, data=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, data=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error making request to Tradier API: {str(e)}"
            logger.error(error_msg)
            
            # Try to parse error response if available
            try:
                error_details = e.response.json()
                logger.error(f"Tradier API error details: {json.dumps(error_details)}")
            except:
                pass
                
            raise TradierAPIError(error_msg)
    
    # --- Account Methods ---
    
    def get_account_balances(self) -> Dict:
        """
        Get account balances
        
        Returns:
            Dictionary with account balance information
        """
        endpoint = f"/accounts/{self.account_id}/balances"
        response = self._make_request("GET", endpoint)
        return response.get("balances", {})
    
    def get_positions(self) -> List[Dict]:
        """
        Get current positions
        
        Returns:
            List of positions
        """
        endpoint = f"/accounts/{self.account_id}/positions"
        response = self._make_request("GET", endpoint)
        positions_data = response.get("positions", {})
        
        # Handle the case when there are no positions
        if positions_data == "null" or not positions_data:
            return []
            
        positions = positions_data.get("position", [])
        # If there's only one position, the API returns it as a dict, not a list
        if isinstance(positions, dict):
            positions = [positions]
            
        return positions
    
    def get_orders(self, status: str = None) -> List[Dict]:
        """
        Get orders for the account
        
        Args:
            status: Filter by order status (open, filled, canceled, expired, rejected, pending)
            
        Returns:
            List of orders
        """
        endpoint = f"/accounts/{self.account_id}/orders"
        response = self._make_request("GET", endpoint)
        orders_data = response.get("orders", {})
        
        # Handle the case when there are no orders
        if orders_data == "null" or not orders_data:
            return []
            
        orders = orders_data.get("order", [])
        # If there's only one order, the API returns it as a dict, not a list
        if isinstance(orders, dict):
            orders = [orders]
            
        # Filter by status if specified
        if status:
            orders = [order for order in orders if order.get("status") == status]
            
        return orders
    
    def get_order(self, order_id: str) -> Dict:
        """
        Get a specific order by ID
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details
        """
        endpoint = f"/accounts/{self.account_id}/orders/{order_id}"
        response = self._make_request("GET", endpoint)
        return response.get("order", {})
    
    def get_account_history(self, limit: int = 25) -> List[Dict]:
        """
        Get account history
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of account activities
        """
        endpoint = f"/accounts/{self.account_id}/history"
        params = {"limit": limit}
        response = self._make_request("GET", endpoint, params=params)
        history_data = response.get("history", {})
        
        if history_data == "null" or not history_data:
            return []
            
        events = history_data.get("event", [])
        # If there's only one event, the API returns it as a dict, not a list
        if isinstance(events, dict):
            events = [events]
            
        return events
    
    # --- Market Data Methods ---
    
    def get_quotes(self, symbols: Union[str, List[str]], greeks: bool = False) -> Dict:
        """
        Get quotes for multiple symbols
        
        Args:
            symbols: Single symbol or list of symbols
            greeks: Include Greeks for options (default: False)
            
        Returns:
            Dictionary of quotes keyed by symbol
        """
        # Convert symbols to comma-separated string if list
        if isinstance(symbols, list):
            symbols_str = ",".join(symbols)
        else:
            symbols_str = symbols
        
        # Check cache first
        current_time = datetime.now()
        cached_quotes = {}
        missing_symbols = []
        
        for symbol in symbols_str.split(","):
            if symbol in self.quote_cache and self.quote_cache_expiry.get(symbol, datetime.min) > current_time:
                # Use cached quote
                cached_quotes[symbol] = self.quote_cache[symbol]
            else:
                # Need to fetch this symbol
                missing_symbols.append(symbol)
        
        # If all quotes are cached, return them
        if not missing_symbols:
            return cached_quotes
        
        # Otherwise, fetch the missing quotes
        endpoint = "/markets/quotes"
        params = {
            "symbols": ",".join(missing_symbols),
            "greeks": "true" if greeks else "false"
        }
        
        response = self._make_request("GET", endpoint, params=params)
        quotes_data = response.get("quotes", {})
        
        # If no quotes, return empty dict or cached quotes
        if quotes_data == "null" or not quotes_data:
            return cached_quotes
        
        quotes = quotes_data.get("quote", [])
        # If there's only one quote, the API returns it as a dict, not a list
        if isinstance(quotes, dict):
            quotes = [quotes]
        
        # Update cache and add to results
        cache_expiry = current_time + timedelta(seconds=self.quote_cache_duration)
        for quote in quotes:
            symbol = quote.get("symbol")
            if symbol:
                self.quote_cache[symbol] = quote
                self.quote_cache_expiry[symbol] = cache_expiry
                cached_quotes[symbol] = quote
        
        return cached_quotes
    
    def get_quote(self, symbol: str, greeks: bool = False) -> Dict:
        """
        Get quote for a single symbol
        
        Args:
            symbol: Symbol to get quote for
            greeks: Include Greeks for options (default: False)
            
        Returns:
            Quote data
        """
        quotes = self.get_quotes(symbol, greeks)
        return quotes.get(symbol, {})
    
    def get_option_chain(self, symbol: str, expiration: str = None, greeks: bool = True) -> List[Dict]:
        """
        Get option chain for a symbol
        
        Args:
            symbol: Underlying symbol
            expiration: Option expiration date in YYYY-MM-DD format
            greeks: Include Greeks in the response
            
        Returns:
            List of options
        """
        endpoint = "/markets/options/chains"
        params = {
            "symbol": symbol,
            "greeks": "true" if greeks else "false"
        }
        
        if expiration:
            params["expiration"] = expiration
        
        response = self._make_request("GET", endpoint, params=params)
        options_data = response.get("options", {})
        
        if options_data == "null" or not options_data:
            return []
            
        options = options_data.get("option", [])
        # If there's only one option, the API returns it as a dict, not a list
        if isinstance(options, dict):
            options = [options]
            
        return options
    
    def get_option_expirations(self, symbol: str, include_all_roots: bool = False) -> List[str]:
        """
        Get available option expirations for a symbol
        
        Args:
            symbol: Underlying symbol
            include_all_roots: Include all options roots
            
        Returns:
            List of expiration dates (YYYY-MM-DD)
        """
        endpoint = "/markets/options/expirations"
        params = {
            "symbol": symbol,
            "includeAllRoots": "true" if include_all_roots else "false"
        }
        
        response = self._make_request("GET", endpoint, params=params)
        expirations_data = response.get("expirations", {})
        
        if expirations_data == "null" or not expirations_data:
            return []
            
        expirations = expirations_data.get("date", [])
        # If there's only one expiration, the API returns it as a string, not a list
        if isinstance(expirations, str):
            expirations = [expirations]
            
        return expirations
    
    def get_market_calendar(self, month: Optional[int] = None, year: Optional[int] = None) -> List[Dict]:
        """
        Get market calendar
        
        Args:
            month: Calendar month (1-12)
            year: Calendar year (YYYY)
            
        Returns:
            List of market calendar days
        """
        endpoint = "/markets/calendar"
        params = {}
        
        if month:
            params["month"] = month
        if year:
            params["year"] = year
        
        response = self._make_request("GET", endpoint, params=params)
        calendar_data = response.get("calendar", {})
        
        if calendar_data == "null" or not calendar_data:
            return []
            
        days = calendar_data.get("days", {}).get("day", [])
        # If there's only one day, the API returns it as a dict, not a list
        if isinstance(days, dict):
            days = [days]
            
        return days
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open
        
        Returns:
            True if market is open, False otherwise
        """
        endpoint = "/markets/clock"
        response = self._make_request("GET", endpoint)
        clock_data = response.get("clock", {})
        
        if clock_data == "null" or not clock_data:
            return False
            
        return clock_data.get("state") == "open"
    
    # --- Order Methods ---
    
    def place_equity_order(self, 
                           symbol: str, 
                           side: str, 
                           quantity: int, 
                           order_type: str = "market",
                           duration: str = "day",
                           price: float = None,
                           stop: float = None) -> Dict:
        """
        Place an equity order
        
        Args:
            symbol: Symbol to trade
            side: Order side ('buy' or 'sell')
            quantity: Number of shares
            order_type: Order type ('market', 'limit', 'stop', 'stop_limit')
            duration: Time in force ('day', 'gtc', 'pre', 'post')
            price: Limit price (required for 'limit' and 'stop_limit' orders)
            stop: Stop price (required for 'stop' and 'stop_limit' orders)
            
        Returns:
            Dictionary with order details
        """
        endpoint = f"/accounts/{self.account_id}/orders"
        
        # Validate required fields
        if order_type in ["limit", "stop_limit"] and price is None:
            raise ValueError("Price is required for limit orders")
        if order_type in ["stop", "stop_limit"] and stop is None:
            raise ValueError("Stop price is required for stop orders")
        
        # Prepare order data
        data = {
            "class": "equity",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "duration": duration
        }
        
        # Add price and stop if applicable
        if price is not None:
            data["price"] = price
        if stop is not None:
            data["stop"] = stop
        
        logger.info(f"Placing {side} order for {quantity} shares of {symbol} at {price if price else 'market price'}")
        response = self._make_request("POST", endpoint, data=data)
        return response.get("order", {})
    
    def place_option_order(self,
                          option_symbol: str,
                          side: str,
                          quantity: int,
                          order_type: str = "market",
                          duration: str = "day",
                          price: float = None,
                          stop: float = None) -> Dict:
        """
        Place an option order
        
        Args:
            option_symbol: OCC option symbol (e.g., 'AAPL220121C00150000')
            side: Order side ('buy_to_open', 'buy_to_close', 'sell_to_open', 'sell_to_close')
            quantity: Number of contracts
            order_type: Order type ('market', 'limit', 'stop', 'stop_limit')
            duration: Time in force ('day', 'gtc')
            price: Limit price (required for 'limit' and 'stop_limit' orders)
            stop: Stop price (required for 'stop' and 'stop_limit' orders)
            
        Returns:
            Dictionary with order details
        """
        endpoint = f"/accounts/{self.account_id}/orders"
        
        # Validate required fields
        if order_type in ["limit", "stop_limit"] and price is None:
            raise ValueError("Price is required for limit orders")
        if order_type in ["stop", "stop_limit"] and stop is None:
            raise ValueError("Stop price is required for stop orders")
        
        # Prepare order data
        data = {
            "class": "option",
            "symbol": option_symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "duration": duration
        }
        
        # Add price and stop if applicable
        if price is not None:
            data["price"] = price
        if stop is not None:
            data["stop"] = stop
        
        logger.info(f"Placing {side} order for {quantity} contracts of {option_symbol} at {price if price else 'market price'}")
        response = self._make_request("POST", endpoint, data=data)
        return response.get("order", {})
    
    def modify_order(self,
                    order_id: str,
                    order_type: str = None,
                    duration: str = None,
                    price: float = None,
                    stop: float = None) -> Dict:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID to modify
            order_type: New order type
            duration: New time in force
            price: New limit price
            stop: New stop price
            
        Returns:
            Dictionary with modified order details
        """
        endpoint = f"/accounts/{self.account_id}/orders/{order_id}"
        
        # Prepare order data
        data = {}
        if order_type:
            data["type"] = order_type
        if duration:
            data["duration"] = duration
        if price is not None:
            data["price"] = price
        if stop is not None:
            data["stop"] = stop
        
        logger.info(f"Modifying order {order_id}")
        response = self._make_request("PUT", endpoint, data=data)
        return response.get("order", {})
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Dictionary with cancellation details
        """
        endpoint = f"/accounts/{self.account_id}/orders/{order_id}"
        logger.info(f"Cancelling order {order_id}")
        response = self._make_request("DELETE", endpoint)
        return response.get("order", {})
    
    # --- Helper Methods ---
    
    def get_option_symbol(self, 
                         underlying: str, 
                         expiration: str, 
                         option_type: str, 
                         strike: float) -> str:
        """
        Generate an OCC option symbol
        
        Args:
            underlying: Underlying symbol (e.g., 'AAPL')
            expiration: Expiration date in YYYY-MM-DD format
            option_type: 'call' or 'put'
            strike: Strike price
            
        Returns:
            OCC option symbol (e.g., 'AAPL220121C00150000')
        """
        # Pad the underlying symbol to 6 characters
        padded_underlying = underlying.ljust(6)
        
        # Format the expiration date (YYMMDD)
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        exp_formatted = exp_date.strftime("%y%m%d")
        
        # Format the option type (C or P)
        option_type_code = "C" if option_type.lower() == "call" else "P"
        
        # Format the strike price (multiply by 1000 and pad to 8 digits)
        strike_formatted = f"{int(strike * 1000):08d}"
        
        # Combine to create the OCC symbol
        return f"{padded_underlying}{exp_formatted}{option_type_code}{strike_formatted}"
    
    def get_account_summary(self) -> Dict:
        """
        Get a comprehensive account summary including balances,
        positions, and open orders
        
        Returns:
            Dictionary with account summary
        """
        # Get account balances
        balances = self.get_account_balances()
        
        # Get positions
        positions = self.get_positions()
        
        # Get open orders
        open_orders = self.get_orders(status="open")
        
        # Calculate some additional metrics
        total_position_value = sum(float(position.get("market_value", 0)) for position in positions)
        cash = float(balances.get("cash", 0))
        equity = float(balances.get("equity", 0))
        
        return {
            "account_number": self.account_id,
            "type": balances.get("account_type", ""),
            "cash": cash,
            "equity": equity,
            "buying_power": float(balances.get("buying_power", 0)),
            "day_trades_remaining": balances.get("day_trading_buying_power", 0),
            "positions": {
                "count": len(positions),
                "total_value": total_position_value,
                "percentage_of_equity": (total_position_value / equity * 100) if equity > 0 else 0,
                "details": positions
            },
            "open_orders": {
                "count": len(open_orders),
                "details": open_orders
            },
            "market_hours": {
                "is_open": self.is_market_open()
            }
        }
    
    def get_historical_data(self, 
                          symbol: str, 
                          interval: str = "daily", 
                          start_date: str = None, 
                          end_date: str = None,
                          days_back: int = None) -> Dict:
        """
        Get historical market data for a symbol
        
        Args:
            symbol: Symbol to get data for
            interval: Data interval (daily, weekly, monthly)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            days_back: Alternative to start_date, get X days back from end_date or today
            
        Returns:
            Dictionary with historical price data
        """
        endpoint = "/markets/history"
        
        # Set dates
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        if days_back and not start_date:
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
        # Required parameters
        params = {
            "symbol": symbol,
            "interval": interval
        }
        
        # Add dates if provided
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        
        response = self._make_request("GET", endpoint, params=params)
        history_data = response.get("history", {})
        
        if history_data == "null" or not history_data:
            return {"day": []}
            
        return history_data


class TradierAPIError(Exception):
    """Exception raised when Tradier API returns an error"""
    pass 