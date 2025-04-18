#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Order Module

This module provides the Order class and related enums for defining
trading orders and their properties.
"""

import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Enum for order types."""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()
    TRAILING_STOP = auto()

class OrderAction(Enum):
    """Enum for order actions."""
    BUY = auto()
    SELL = auto()
    BUY_TO_COVER = auto()  # For covering short positions
    SELL_SHORT = auto()    # For opening short positions

class OrderStatus(Enum):
    """Enum for order statuses."""
    CREATED = auto()       # Just created, not submitted
    SUBMITTED = auto()     # Submitted to broker
    ACCEPTED = auto()      # Accepted by broker
    REJECTED = auto()      # Rejected by broker
    PARTIAL = auto()       # Partially filled
    FILLED = auto()        # Completely filled
    CANCELLED = auto()     # Cancelled before completion
    EXPIRED = auto()       # Expired without being filled
    ERROR = auto()         # Order encountered an error

class Order:
    """
    Order class representing a trading order.
    
    This class encapsulates all the information needed for an order,
    including the symbol, quantity, price, type, and various identifiers.
    """
    
    def __init__(self, 
                symbol: str,
                order_type: OrderType,
                action: OrderAction,
                quantity: int,
                limit_price: Optional[float] = None,
                stop_price: Optional[float] = None,
                option_symbol: Optional[str] = None,
                trade_id: Optional[str] = None,
                order_id: Optional[str] = None,
                order_details: Optional[Dict[str, Any]] = None):
        """
        Initialize an Order.
        
        Args:
            symbol: The underlying symbol (e.g., "AAPL")
            order_type: Type of order (market, limit, etc.)
            action: Order action (buy, sell, etc.)
            quantity: Number of shares/contracts
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            option_symbol: Option symbol (for options orders)
            trade_id: ID for grouping related orders
            order_id: Unique order ID (generated if not provided)
            order_details: Additional order details
        """
        self.symbol = symbol
        self.order_type = order_type
        self.action = action
        self.quantity = quantity
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.option_symbol = option_symbol
        self.trade_id = trade_id if trade_id else str(uuid.uuid4())
        self.order_id = order_id if order_id else str(uuid.uuid4())
        self.order_details = order_details or {}
        
        self.status = OrderStatus.CREATED
        self.creation_time = datetime.now()
        self.submission_time = None
        self.fill_time = None
        self.filled_quantity = 0
        self.average_fill_price = None
        self.commission = 0.0
        self.fees = 0.0
        
        logger.info(f"Created order: {self}")
    
    def __str__(self) -> str:
        """Return string representation of the order."""
        order_str = (
            f"Order(id={self.order_id}, "
            f"{self.action.name} {self.quantity} {self.symbol}"
        )
        
        if self.option_symbol:
            order_str += f" option {self.option_symbol}"
            
        order_str += f", type={self.order_type.name}"
        
        if self.limit_price is not None:
            order_str += f", limit=${self.limit_price:.2f}"
            
        if self.stop_price is not None:
            order_str += f", stop=${self.stop_price:.2f}"
            
        order_str += f", status={self.status.name})"
        
        return order_str
    
    def update_status(self, new_status: OrderStatus) -> None:
        """
        Update the order status.
        
        Args:
            new_status: New order status
        """
        old_status = self.status
        self.status = new_status
        
        if new_status == OrderStatus.SUBMITTED and self.submission_time is None:
            self.submission_time = datetime.now()
            
        if new_status == OrderStatus.FILLED and self.fill_time is None:
            self.fill_time = datetime.now()
        
        logger.info(f"Order {self.order_id} status updated: {old_status.name} -> {new_status.name}")
    
    def update_fill(self, filled_quantity: int, fill_price: float) -> None:
        """
        Update the order fill information.
        
        Args:
            filled_quantity: Quantity filled in this update
            fill_price: Price at which the order was filled
        """
        # Update filled quantity
        old_filled = self.filled_quantity
        self.filled_quantity += filled_quantity
        
        # Update average fill price
        if self.average_fill_price is None:
            self.average_fill_price = fill_price
        else:
            # Weighted average of previous fills and new fill
            self.average_fill_price = (
                (old_filled * self.average_fill_price + filled_quantity * fill_price) /
                self.filled_quantity
            )
        
        # Update status based on fill
        if self.filled_quantity == self.quantity:
            self.update_status(OrderStatus.FILLED)
        elif self.filled_quantity > 0:
            self.update_status(OrderStatus.PARTIAL)
            
        logger.info(f"Order {self.order_id} filled: {filled_quantity} @ ${fill_price:.2f}, "
                  f"total filled: {self.filled_quantity}/{self.quantity}")
    
    def cancel(self) -> bool:
        """
        Cancel the order.
        
        Returns:
            True if cancellation is possible, False otherwise
        """
        if self.status in (OrderStatus.CREATED, OrderStatus.SUBMITTED, OrderStatus.ACCEPTED, 
                          OrderStatus.PARTIAL):
            self.update_status(OrderStatus.CANCELLED)
            return True
        
        logger.warning(f"Cannot cancel order {self.order_id} with status {self.status.name}")
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order to dictionary.
        
        Returns:
            Dictionary representation of the order
        """
        return {
            "order_id": self.order_id,
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "option_symbol": self.option_symbol,
            "order_type": self.order_type.name,
            "action": self.action.name,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "status": self.status.name,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "submission_time": self.submission_time.isoformat() if self.submission_time else None,
            "fill_time": self.fill_time.isoformat() if self.fill_time else None,
            "filled_quantity": self.filled_quantity,
            "average_fill_price": self.average_fill_price,
            "commission": self.commission,
            "fees": self.fees,
            "order_details": self.order_details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """
        Create an Order from a dictionary.
        
        Args:
            data: Dictionary representation of an order
            
        Returns:
            Order object
        """
        # Convert string enum values to actual enum values
        order_type = getattr(OrderType, data['order_type'])
        action = getattr(OrderAction, data['action'])
        
        # Create order with basic parameters
        order = cls(
            symbol=data['symbol'],
            order_type=order_type,
            action=action,
            quantity=data['quantity'],
            limit_price=data.get('limit_price'),
            stop_price=data.get('stop_price'),
            option_symbol=data.get('option_symbol'),
            trade_id=data.get('trade_id'),
            order_id=data.get('order_id'),
            order_details=data.get('order_details', {})
        )
        
        # Update status
        if 'status' in data:
            order.status = getattr(OrderStatus, data['status'])
        
        # Update timestamps
        if 'creation_time' in data and data['creation_time']:
            order.creation_time = datetime.fromisoformat(data['creation_time'])
        
        if 'submission_time' in data and data['submission_time']:
            order.submission_time = datetime.fromisoformat(data['submission_time'])
        
        if 'fill_time' in data and data['fill_time']:
            order.fill_time = datetime.fromisoformat(data['fill_time'])
        
        # Update fill information
        order.filled_quantity = data.get('filled_quantity', 0)
        order.average_fill_price = data.get('average_fill_price')
        order.commission = data.get('commission', 0.0)
        order.fees = data.get('fees', 0.0)
        
        return order 