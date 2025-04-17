import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from trading_bot.brokers.tradier_client import TradierClient, TradierAPIError

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    Trade execution module for Tradier brokerage
    
    Handles position sizing, order execution, and trade management
    """
    
    def __init__(self, 
                tradier_client: TradierClient,
                max_position_pct: float = 0.05,
                max_risk_pct: float = 0.01,
                order_type: str = "market",
                order_duration: str = "day"):
        """
        Initialize the trade executor
        
        Args:
            tradier_client: Initialized Tradier client
            max_position_pct: Maximum position size as percentage of account equity
            max_risk_pct: Maximum risk per trade as percentage of account equity
            order_type: Default order type ('market', 'limit', 'stop', 'stop_limit')
            order_duration: Default order duration ('day', 'gtc')
        """
        self.client = tradier_client
        self.max_position_pct = max_position_pct
        self.max_risk_pct = max_risk_pct
        self.default_order_type = order_type
        self.default_order_duration = order_duration
        
        # Trade history
        self.trade_history = []
        
        # Active trades
        self.active_trades = {}
        
        # Initialize with account data
        self.refresh_account_data()
        
        logger.info(f"TradeExecutor initialized with max position: {max_position_pct:.1%}, max risk: {max_risk_pct:.1%}")
    
    def refresh_account_data(self):
        """Refresh account data from the broker"""
        try:
            # Get account summary
            account_summary = self.client.get_account_summary()
            
            # Extract key data
            self.account_equity = account_summary.get("equity", 0)
            self.cash_balance = account_summary.get("cash", 0)
            self.buying_power = account_summary.get("buying_power", 0)
            
            # Get existing positions
            self.positions = account_summary.get("positions", {}).get("details", [])
            
            # Calculate max position size in dollars
            self.max_position_dollars = self.account_equity * self.max_position_pct
            self.max_risk_dollars = self.account_equity * self.max_risk_pct
            
            logger.info(f"Account refreshed: equity=${self.account_equity:.2f}, "
                       f"max position=${self.max_position_dollars:.2f}, "
                       f"max risk=${self.max_risk_dollars:.2f}")
                       
            # Update active trades with current position data
            self._update_active_trades()
            
        except Exception as e:
            logger.error(f"Error refreshing account data: {str(e)}")
            raise
    
    def _update_active_trades(self):
        """Update active trades with current position data"""
        # Map positions by symbol
        position_map = {pos.get("symbol"): pos for pos in self.positions}
        
        # Update active trades with current position data
        for trade_id, trade in self.active_trades.items():
            symbol = trade.get("symbol")
            if symbol in position_map:
                # Update trade with current position data
                position = position_map[symbol]
                trade["current_price"] = float(position.get("last_price", 0))
                trade["current_value"] = float(position.get("market_value", 0))
                trade["unrealized_pl"] = float(position.get("gain_loss", 0))
                trade["unrealized_pl_pct"] = float(position.get("gain_loss_percent", 0))
                trade["updated_at"] = datetime.now().isoformat()
            else:
                # Position has been closed
                if trade.get("status") == "open":
                    trade["status"] = "closed"
                    trade["exit_date"] = datetime.now().isoformat()
                    # We don't know the exit price, will be updated when we get trade confirmation
    
    def calculate_position_size(self, 
                               entry_price: float, 
                               stop_price: Optional[float] = None,
                               risk_pct: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price per share
            stop_price: Stop loss price per share
            risk_pct: Risk percentage (overrides default max_risk_pct)
            
        Returns:
            Dictionary with position size details
        """
        # Use provided risk percentage or default
        risk_pct = risk_pct if risk_pct is not None else self.max_risk_pct
        
        # Calculate risk amount in dollars (account equity * risk percentage)
        risk_dollars = self.account_equity * risk_pct
        
        # Ensure risk doesn't exceed maximum
        risk_dollars = min(risk_dollars, self.max_risk_dollars)
        
        # Calculate position size
        if stop_price and stop_price < entry_price:
            # Calculate based on stop loss distance
            risk_per_share = entry_price - stop_price
            shares = int(risk_dollars / risk_per_share) if risk_per_share > 0 else 0
        else:
            # No stop loss provided, calculate based on max position size
            max_shares = int(self.max_position_dollars / entry_price) if entry_price > 0 else 0
            
            # Default to 1% loss without stop
            default_risk_per_share = entry_price * 0.01
            shares = int(risk_dollars / default_risk_per_share) if default_risk_per_share > 0 else 0
            
            # Cap at max position size
            shares = min(shares, max_shares)
        
        # Calculate total position value
        position_value = shares * entry_price
        
        # Ensure position doesn't exceed max position size
        if position_value > self.max_position_dollars:
            shares = int(self.max_position_dollars / entry_price) if entry_price > 0 else 0
            position_value = shares * entry_price
        
        # Ensure we have enough buying power
        if position_value > self.buying_power:
            logger.warning(f"Position size (${position_value:.2f}) exceeds buying power (${self.buying_power:.2f})")
            shares = int(self.buying_power / entry_price) if entry_price > 0 else 0
            position_value = shares * entry_price
        
        # Calculate actual risk
        actual_risk_dollars = risk_dollars if stop_price else position_value * 0.01
        actual_risk_pct = actual_risk_dollars / self.account_equity if self.account_equity > 0 else 0
        
        return {
            "shares": shares,
            "position_value": position_value,
            "position_pct_of_account": position_value / self.account_equity if self.account_equity > 0 else 0,
            "risk_dollars": actual_risk_dollars,
            "risk_pct_of_account": actual_risk_pct,
            "entry_price": entry_price,
            "stop_price": stop_price
        }
    
    def execute_trade(self, 
                     symbol: str, 
                     side: str, 
                     entry_price: Optional[float] = None,
                     stop_price: Optional[float] = None,
                     target_price: Optional[float] = None,
                     shares: Optional[int] = None,
                     risk_pct: Optional[float] = None,
                     order_type: Optional[str] = None,
                     duration: Optional[str] = None,
                     strategy_name: Optional[str] = None,
                     metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a trade
        
        Args:
            symbol: Symbol to trade
            side: Trade side ('buy' or 'sell')
            entry_price: Limit price (None for market orders)
            stop_price: Stop loss price
            target_price: Profit target price
            shares: Number of shares to trade (overrides position sizing calculation)
            risk_pct: Risk percentage (overrides default max_risk_pct)
            order_type: Order type (overrides default)
            duration: Order duration (overrides default)
            strategy_name: Name of the strategy that generated this signal
            metadata: Additional metadata for the trade record
            
        Returns:
            Dictionary with trade details
        """
        try:
            # Refresh account data to ensure we have the latest
            self.refresh_account_data()
            
            # Get current price if not provided for calculations
            if entry_price is None:
                quote = self.client.get_quote(symbol)
                if not quote:
                    raise ValueError(f"Could not get quote for symbol: {symbol}")
                entry_price = float(quote.get("last", 0))
                if entry_price <= 0:
                    raise ValueError(f"Invalid price for symbol {symbol}: {entry_price}")
            
            # Calculate position size if shares not specified
            if shares is None:
                position_size = self.calculate_position_size(entry_price, stop_price, risk_pct)
                shares = position_size["shares"]
                
                logger.info(f"Calculated position size: {shares} shares at ${entry_price:.2f}, "
                           f"risk: ${position_size['risk_dollars']:.2f} ({position_size['risk_pct_of_account']:.2%})")
            
            # Check if we have enough shares to execute
            if shares <= 0:
                raise ValueError(f"Invalid position size: {shares} shares")
            
            # Set order type and duration
            order_type = order_type or self.default_order_type
            duration = duration or self.default_order_duration
            
            # Generate unique trade ID
            trade_id = str(uuid.uuid4())
            
            # Create a trade record
            trade_record = {
                "id": trade_id,
                "symbol": symbol,
                "side": side,
                "shares": shares,
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "order_type": order_type,
                "duration": duration,
                "strategy": strategy_name,
                "status": "pending",
                "entry_date": datetime.now().isoformat(),
                "exit_date": None,
                "exit_price": None,
                "realized_pl": None,
                "realized_pl_pct": None,
                "metadata": metadata or {}
            }
            
            # Place the order
            logger.info(f"Placing {side} order for {shares} shares of {symbol} at ${entry_price:.2f}")
            
            order_result = self.client.place_equity_order(
                symbol=symbol,
                side=side,
                quantity=shares,
                order_type=order_type,
                duration=duration,
                price=entry_price if order_type in ["limit", "stop_limit"] else None,
                stop=stop_price if order_type in ["stop", "stop_limit"] else None
            )
            
            # Update trade record with order details
            trade_record["order_id"] = order_result.get("id")
            trade_record["status"] = order_result.get("status", "pending")
            
            # Add to active trades if the order was accepted
            if order_result.get("status") not in ["rejected", "canceled"]:
                self.active_trades[trade_id] = trade_record
            
            # Add to trade history
            self.trade_history.append(trade_record)
            
            # Place stop loss order if needed
            if stop_price and order_type not in ["stop", "stop_limit"]:
                try:
                    stop_side = "sell" if side == "buy" else "buy"
                    stop_order_result = self.client.place_equity_order(
                        symbol=symbol,
                        side=stop_side,
                        quantity=shares,
                        order_type="stop",
                        duration=duration,
                        stop=stop_price
                    )
                    
                    # Add stop order ID to trade record
                    trade_record["stop_order_id"] = stop_order_result.get("id")
                    
                    logger.info(f"Placed stop loss order at ${stop_price:.2f} (Order ID: {stop_order_result.get('id')})")
                except Exception as stop_error:
                    logger.error(f"Error placing stop loss order: {str(stop_error)}")
                    # Continue with the trade even if stop order fails
            
            # Return the trade record
            return trade_record
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            raise
    
    def exit_trade(self, 
                  trade_id: str, 
                  price: Optional[float] = None,
                  order_type: Optional[str] = None,
                  duration: Optional[str] = None,
                  exit_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Exit an existing trade
        
        Args:
            trade_id: ID of the trade to exit
            price: Exit price (None for market orders)
            order_type: Order type (overrides default)
            duration: Order duration (overrides default)
            exit_reason: Reason for exiting the trade
            
        Returns:
            Dictionary with trade details
        """
        try:
            # Check if trade exists
            if trade_id not in self.active_trades:
                raise ValueError(f"Trade not found: {trade_id}")
            
            # Get the trade
            trade = self.active_trades[trade_id]
            
            # Check if trade is already closed
            if trade.get("status") == "closed":
                logger.warning(f"Trade {trade_id} is already closed")
                return trade
            
            # Get symbol and shares
            symbol = trade.get("symbol")
            shares = trade.get("shares", 0)
            side = "sell" if trade.get("side") == "buy" else "buy"
            
            # Set order type and duration
            order_type = order_type or self.default_order_type
            duration = duration or self.default_order_duration
            
            # Get current price if not provided
            if price is None:
                quote = self.client.get_quote(symbol)
                if not quote:
                    raise ValueError(f"Could not get quote for symbol: {symbol}")
                price = float(quote.get("last", 0))
                if price <= 0:
                    raise ValueError(f"Invalid price for symbol {symbol}: {price}")
            
            # Place the exit order
            logger.info(f"Placing {side} order to exit {shares} shares of {symbol} at ${price:.2f}")
            
            exit_order_result = self.client.place_equity_order(
                symbol=symbol,
                side=side,
                quantity=shares,
                order_type=order_type,
                duration=duration,
                price=price if order_type in ["limit", "stop_limit"] else None
            )
            
            # Calculate profit/loss
            entry_price = trade.get("entry_price", 0)
            if side == "sell":
                realized_pl = (price - entry_price) * shares
            else:
                realized_pl = (entry_price - price) * shares
                
            realized_pl_pct = (realized_pl / (entry_price * shares)) if entry_price > 0 else 0
            
            # Update trade record
            trade["exit_order_id"] = exit_order_result.get("id")
            trade["exit_date"] = datetime.now().isoformat()
            trade["exit_price"] = price
            trade["realized_pl"] = realized_pl
            trade["realized_pl_pct"] = realized_pl_pct
            trade["status"] = "closing"  # Will be updated to "closed" when exit order is filled
            trade["exit_reason"] = exit_reason
            
            # Cancel any open stop loss orders
            if trade.get("stop_order_id"):
                try:
                    self.client.cancel_order(trade.get("stop_order_id"))
                    logger.info(f"Cancelled stop loss order (ID: {trade.get('stop_order_id')})")
                except Exception as cancel_error:
                    logger.warning(f"Error cancelling stop loss order: {str(cancel_error)}")
            
            # Log exit details
            logger.info(f"Exited trade {trade_id}: {shares} shares of {symbol} at ${price:.2f}, "
                       f"P/L: ${realized_pl:.2f} ({realized_pl_pct:.2%})")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error exiting trade: {str(e)}")
            raise
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get all open trades
        
        Returns:
            List of open trades
        """
        # Refresh to ensure we have the latest data
        self.refresh_account_data()
        
        # Return only open trades
        return [trade for trade in self.active_trades.values() 
                if trade.get("status") in ["open", "pending", "filled"]]
    
    def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trade
        
        Args:
            trade_id: ID of the trade to retrieve
            
        Returns:
            Trade details or None if not found
        """
        # Check active trades first
        if trade_id in self.active_trades:
            return self.active_trades[trade_id]
        
        # Check trade history
        for trade in self.trade_history:
            if trade.get("id") == trade_id:
                return trade
                
        return None
    
    def get_trade_history(self, 
                         symbol: Optional[str] = None, 
                         strategy: Optional[str] = None,
                         status: Optional[str] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade history with optional filtering
        
        Args:
            symbol: Filter by symbol
            strategy: Filter by strategy
            status: Filter by status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            List of trades matching the filter criteria
        """
        filtered_trades = self.trade_history.copy()
        
        # Apply filters
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get("symbol") == symbol]
        if strategy:
            filtered_trades = [t for t in filtered_trades if t.get("strategy") == strategy]
        if status:
            filtered_trades = [t for t in filtered_trades if t.get("status") == status]
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_trades = [t for t in filtered_trades if datetime.fromisoformat(t.get("entry_date")) >= start_dt]
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_trades = [t for t in filtered_trades if datetime.fromisoformat(t.get("entry_date")) <= end_dt]
        
        # Sort by entry date (newest first)
        filtered_trades.sort(key=lambda t: t.get("entry_date", ""), reverse=True)
        
        return filtered_trades
    
    def update_stop_loss(self, trade_id: str, new_stop_price: float) -> Dict[str, Any]:
        """
        Update stop loss for an existing trade
        
        Args:
            trade_id: ID of the trade to update
            new_stop_price: New stop loss price
            
        Returns:
            Updated trade details
        """
        try:
            # Check if trade exists
            if trade_id not in self.active_trades:
                raise ValueError(f"Trade not found: {trade_id}")
            
            # Get the trade
            trade = self.active_trades[trade_id]
            
            # Check if trade is already closed
            if trade.get("status") == "closed":
                logger.warning(f"Trade {trade_id} is already closed")
                return trade
            
            # Get old stop order ID
            old_stop_order_id = trade.get("stop_order_id")
            
            # Cancel old stop order if it exists
            if old_stop_order_id:
                try:
                    self.client.cancel_order(old_stop_order_id)
                    logger.info(f"Cancelled old stop loss order (ID: {old_stop_order_id})")
                except Exception as cancel_error:
                    logger.warning(f"Error cancelling old stop loss order: {str(cancel_error)}")
            
            # Place new stop order
            symbol = trade.get("symbol")
            shares = trade.get("shares", 0)
            side = "sell" if trade.get("side") == "buy" else "buy"
            
            new_stop_order_result = self.client.place_equity_order(
                symbol=symbol,
                side=side,
                quantity=shares,
                order_type="stop",
                duration=trade.get("duration", self.default_order_duration),
                stop=new_stop_price
            )
            
            # Update trade record
            trade["stop_price"] = new_stop_price
            trade["stop_order_id"] = new_stop_order_result.get("id")
            
            logger.info(f"Updated stop loss for trade {trade_id} to ${new_stop_price:.2f}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error updating stop loss: {str(e)}")
            raise
    
    def set_take_profit(self, trade_id: str, target_price: float) -> Dict[str, Any]:
        """
        Set a take profit order for an existing trade
        
        Args:
            trade_id: ID of the trade to update
            target_price: Take profit price
            
        Returns:
            Updated trade details
        """
        try:
            # Check if trade exists
            if trade_id not in self.active_trades:
                raise ValueError(f"Trade not found: {trade_id}")
            
            # Get the trade
            trade = self.active_trades[trade_id]
            
            # Check if trade is already closed
            if trade.get("status") == "closed":
                logger.warning(f"Trade {trade_id} is already closed")
                return trade
            
            # Get old target order ID
            old_target_order_id = trade.get("target_order_id")
            
            # Cancel old target order if it exists
            if old_target_order_id:
                try:
                    self.client.cancel_order(old_target_order_id)
                    logger.info(f"Cancelled old take profit order (ID: {old_target_order_id})")
                except Exception as cancel_error:
                    logger.warning(f"Error cancelling old take profit order: {str(cancel_error)}")
            
            # Place new target order
            symbol = trade.get("symbol")
            shares = trade.get("shares", 0)
            side = "sell" if trade.get("side") == "buy" else "buy"
            
            new_target_order_result = self.client.place_equity_order(
                symbol=symbol,
                side=side,
                quantity=shares,
                order_type="limit",
                duration=trade.get("duration", self.default_order_duration),
                price=target_price
            )
            
            # Update trade record
            trade["target_price"] = target_price
            trade["target_order_id"] = new_target_order_result.get("id")
            
            logger.info(f"Set take profit for trade {trade_id} to ${target_price:.2f}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error setting take profit: {str(e)}")
            raise
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate trading metrics
        
        Returns:
            Dictionary with trading metrics
        """
        # Get all closed trades
        closed_trades = [t for t in self.trade_history if t.get("status") == "closed" and t.get("realized_pl") is not None]
        
        if not closed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_pl": 0,
                "average_pl": 0,
                "average_win": 0,
                "average_loss": 0,
                "largest_win": 0,
                "largest_loss": 0
            }
        
        # Calculate metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.get("realized_pl", 0) > 0]
        losing_trades = [t for t in closed_trades if t.get("realized_pl", 0) <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t.get("realized_pl", 0) for t in winning_trades)
        total_loss = abs(sum(t.get("realized_pl", 0) for t in losing_trades))
        
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        total_pl = total_profit - total_loss
        average_pl = total_pl / total_trades if total_trades > 0 else 0
        
        average_win = total_profit / win_count if win_count > 0 else 0
        average_loss = total_loss / loss_count if loss_count > 0 else 0
        
        largest_win = max([t.get("realized_pl", 0) for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.get("realized_pl", 0) for t in losing_trades]) if losing_trades else 0
        
        return {
            "total_trades": total_trades,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_pl": total_pl,
            "average_pl": average_pl,
            "average_win": average_win,
            "average_loss": average_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss
        } 