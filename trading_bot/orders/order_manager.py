#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Order Manager Module

This module provides the OrderManager class for managing the lifecycle
of orders in the trading system.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from trading_bot.orders.order import Order, OrderStatus, OrderType, OrderAction

logger = logging.getLogger(__name__)

class OrderManager:
    """
    Order Manager for handling order operations.
    
    The OrderManager is responsible for:
    - Submitting orders
    - Tracking order status
    - Updating order information
    - Providing order history and analytics
    """
    
    def __init__(self, broker_connector=None):
        """
        Initialize the OrderManager.
        
        Args:
            broker_connector: Optional connector to a broker API
        """
        self.broker_connector = broker_connector
        self.orders: Dict[str, Order] = {}  # Order ID to Order mapping
        self.trades: Dict[str, List[Order]] = {}  # Trade ID to list of Orders
        
        logger.info("Initialized OrderManager")
    
    def submit_order(self, order: Order) -> bool:
        """
        Submit an order to the broker.
        
        Args:
            order: The order to submit
            
        Returns:
            True if successful, False otherwise
        """
        # Store order in our tracking collections
        self.orders[order.order_id] = order
        
        if order.trade_id not in self.trades:
            self.trades[order.trade_id] = []
        self.trades[order.trade_id].append(order)
        
        # If we have a broker connection, submit the order
        if self.broker_connector:
            try:
                success = self.broker_connector.submit_order(order)
                if success:
                    order.update_status(OrderStatus.SUBMITTED)
                else:
                    order.update_status(OrderStatus.ERROR)
                return success
            except Exception as e:
                logger.error(f"Error submitting order: {e}")
                order.update_status(OrderStatus.ERROR)
                return False
        else:
            # Mock submission (simulation mode)
            logger.info(f"Simulating order submission: {order}")
            order.update_status(OrderStatus.SUBMITTED)
            # Immediately set to FILLED in simulation mode for simplicity
            order.update_status(OrderStatus.FILLED)
            order.update_fill(order.quantity, order.limit_price or 0.0)
            return True
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot cancel unknown order ID: {order_id}")
            return False
            
        order = self.orders[order_id]
        
        # If we have a broker connection, cancel the order
        if self.broker_connector:
            try:
                success = self.broker_connector.cancel_order(order_id)
                if success:
                    order.cancel()
                return success
            except Exception as e:
                logger.error(f"Error cancelling order: {e}")
                return False
        else:
            # Mock cancellation
            logger.info(f"Simulating order cancellation: {order}")
            return order.cancel()
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get an order by its ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        return self.orders.get(order_id)
    
    def get_orders_by_trade(self, trade_id: str) -> List[Order]:
        """
        Get all orders for a specific trade.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            List of orders for the trade
        """
        return self.trades.get(trade_id, [])
    
    def get_all_orders(self) -> List[Order]:
        """
        Get all orders.
        
        Returns:
            List of all orders
        """
        return list(self.orders.values())
    
    def get_active_orders(self) -> List[Order]:
        """
        Get all active orders (not FILLED, CANCELLED, REJECTED, or ERROR).
        
        Returns:
            List of active orders
        """
        active_statuses = {
            OrderStatus.CREATED,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIAL
        }
        
        return [order for order in self.orders.values() if order.status in active_statuses]
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get orders with the specified status.
        
        Args:
            status: Order status to filter by
            
        Returns:
            List of orders with the specified status
        """
        return [order for order in self.orders.values() if order.status == status]
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        Get orders for a specific symbol.
        
        Args:
            symbol: Symbol to filter by
            
        Returns:
            List of orders for the symbol
        """
        return [order for order in self.orders.values() if order.symbol == symbol]
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update the status of an order.
        
        Args:
            order_id: Order ID
            status: New order status
            
        Returns:
            True if update successful, False otherwise
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot update status of unknown order ID: {order_id}")
            return False
            
        order = self.orders[order_id]
        order.update_status(status)
        return True
    
    def update_order_fill(self, order_id: str, filled_quantity: int, 
                        fill_price: float) -> bool:
        """
        Update the fill information of an order.
        
        Args:
            order_id: Order ID
            filled_quantity: Quantity filled
            fill_price: Price at which the order was filled
            
        Returns:
            True if update successful, False otherwise
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot update fill of unknown order ID: {order_id}")
            return False
            
        order = self.orders[order_id]
        order.update_fill(filled_quantity, fill_price)
        return True
    
    def to_json(self) -> str:
        """
        Convert order manager state to JSON.
        
        Returns:
            JSON string representation of the order manager state
        """
        state = {
            "orders": {order_id: order.to_dict() for order_id, order in self.orders.items()},
            "trades": {trade_id: [order.order_id for order in orders] 
                      for trade_id, orders in self.trades.items()}
        }
        
        return json.dumps(state, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str, order_factory: Callable = Order.from_dict) -> 'OrderManager':
        """
        Create an OrderManager from JSON.
        
        Args:
            json_str: JSON string representation of the order manager state
            order_factory: Function to create Order objects from dictionaries
            
        Returns:
            OrderManager object
        """
        manager = cls()
        state = json.loads(json_str)
        
        # Reconstruct orders
        for order_id, order_data in state.get("orders", {}).items():
            order = order_factory(order_data)
            manager.orders[order_id] = order
        
        # Reconstruct trades
        for trade_id, order_ids in state.get("trades", {}).items():
            manager.trades[trade_id] = [manager.orders.get(order_id) for order_id in order_ids 
                                      if order_id in manager.orders]
        
        return manager 