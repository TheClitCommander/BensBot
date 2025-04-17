"""
Core interfaces for the trading system components.
These interfaces define the contracts that implementations must follow,
allowing for decoupling between components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime


class DataSourceInterface(ABC):
    """Interface for all data sources, regardless of provider or asset type."""
    
    @abstractmethod
    def get_data(self, symbol: str, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None, **kwargs) -> Dict[str, Any]:
        """
        Get data for a specific symbol and time range.
        
        Args:
            symbol: The symbol to get data for
            start_date: Start of the time range
            end_date: End of the time range
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing the requested data
        """
        pass
    
    @abstractmethod
    def get_latest(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get the latest data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing the latest data
        """
        pass


class IndicatorInterface(ABC):
    """Interface for all technical indicator providers."""
    
    @abstractmethod
    def calculate_indicators(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate technical indicators for the provided data.
        
        Args:
            data: Market data to calculate indicators for
            **kwargs: Additional parameters for calculations
            
        Returns:
            Dictionary with calculated indicators
        """
        pass
    
    @abstractmethod
    def get_indicator_metadata(self, indicator: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for available indicators.
        
        Args:
            indicator: Specific indicator name or None for all
            
        Returns:
            Dictionary with indicator metadata
        """
        pass
    
    @abstractmethod
    def update_parameters(self, params: Dict[str, Any]) -> None:
        """
        Update parameters for indicator calculations.
        
        Args:
            params: New parameter values
        """
        pass


class StrategyInterface(ABC):
    """Interface for all trading strategies."""
    
    @abstractmethod
    def generate_signal(self, data: Dict[str, Any]) -> float:
        """
        Generate a trading signal from the provided data.
        
        Args:
            data: Market and indicator data
            
        Returns:
            Signal value between -1.0 (strong sell) and 1.0 (strong buy)
        """
        pass
    
    @abstractmethod
    def update_parameters(self, params: Dict[str, Any]) -> None:
        """
        Update strategy parameters.
        
        Args:
            params: New parameter values
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the strategy name."""
        pass


class WebhookInterface(ABC):
    """Interface for webhook handlers."""
    
    @abstractmethod
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming webhook payload.
        
        Args:
            data: Webhook payload data
            
        Returns:
            Response data
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the webhook server."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the webhook server."""
        pass 