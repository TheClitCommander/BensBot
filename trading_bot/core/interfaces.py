"""
Core Interfaces

This module defines the interfaces for the core components of the trading system,
ensuring that different implementations can be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataProvider(ABC):
    """Interface for data providers that fetch market data."""
    
    @abstractmethod
    def get_market_data(self, symbols: List[str], start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get market data for a list of symbols.
        
        Args:
            symbols: List of symbols to fetch data for
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Dictionary mapping symbols to their market data
        """
        pass
    
    @abstractmethod
    def get_option_chain(self, symbol: str, expiration_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get option chain data for a symbol.
        
        Args:
            symbol: Symbol to fetch option chain for
            expiration_date: Optional specific expiration date
            
        Returns:
            Option chain data
        """
        pass

class Strategy(ABC):
    """Interface for trading strategies."""
    
    @abstractmethod
    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate indicators for the strategy based on market data.
        
        Args:
            data: Market data for calculation
            
        Returns:
            Calculated indicators
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on market data.
        
        Args:
            data: Market data for signal generation
            
        Returns:
            List of trading signals
        """
        pass

class RiskManager(ABC):
    """Interface for risk management."""
    
    @abstractmethod
    def validate_signal(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a trading signal against risk management rules.
        
        Args:
            signal: Trading signal to validate
            portfolio: Current portfolio state
            
        Returns:
            Validated signal (possibly modified) or None if rejected
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> int:
        """
        Calculate appropriate position size for a signal.
        
        Args:
            signal: Trading signal
            portfolio: Current portfolio state
            
        Returns:
            Position size (number of contracts/shares)
        """
        pass
    
    @abstractmethod
    def calculate_portfolio_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall portfolio risk metrics.
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            Dictionary of risk metrics
        """
        pass

class OrderManager(ABC):
    """Interface for order management."""
    
    @abstractmethod
    def place_order(self, order: Dict[str, Any]) -> str:
        """
        Place an order with the broker.
        
        Args:
            order: Order details
            
        Returns:
            Order ID
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            order_id: ID of the order
            
        Returns:
            Order status details
        """
        pass
    
    @abstractmethod
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Returns:
            List of open orders
        """
        pass

class PortfolioManager(ABC):
    """Interface for portfolio management."""
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions.
        
        Returns:
            Dictionary of positions
        """
        pass
    
    @abstractmethod
    def get_portfolio_value(self) -> float:
        """
        Get current portfolio value.
        
        Returns:
            Portfolio value
        """
        pass
    
    @abstractmethod
    def update_portfolio(self, transaction: Dict[str, Any]) -> None:
        """
        Update portfolio based on a transaction.
        
        Args:
            transaction: Transaction details
        """
        pass
    
    @abstractmethod
    def get_portfolio_history(self, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get portfolio history for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Portfolio history data
        """
        pass

class NotificationManager(ABC):
    """Interface for sending notifications."""
    
    @abstractmethod
    def send_notification(self, message: str, level: str = "info", 
                        category: str = "general") -> bool:
        """
        Send a notification.
        
        Args:
            message: Notification message
            level: Notification level (info, warning, error)
            category: Notification category
            
        Returns:
            True if successful, False otherwise
        """
        pass 