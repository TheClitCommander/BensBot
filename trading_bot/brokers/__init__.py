"""
Brokerage API Integration

This package provides functionality for connecting to various brokerage APIs,
handling order execution, position management, and account monitoring.
"""

# Import key components for easy access
from .brokerage_client import (
    BrokerageClient,
    OrderType,
    OrderSide, 
    TimeInForce,
    BrokerConnectionStatus,
    BrokerAPIError,
    BrokerAuthError,
    BrokerConnectionError,
    OrderExecutionError,
    BROKER_IMPLEMENTATIONS
)

from .alpaca_client import AlpacaClient
from .connection_monitor import ConnectionMonitor, ConnectionAlert
from .order_selector import (
    OrderSelector, 
    MarketCondition, 
    ExecutionSpeed, 
    PriceAggression
)
from .broker_registry import BrokerRegistry, get_broker_registry

# Export key components
__all__ = [
    'BrokerageClient',
    'OrderType',
    'OrderSide',
    'TimeInForce',
    'BrokerConnectionStatus',
    'BrokerAPIError',
    'BrokerAuthError',
    'BrokerConnectionError',
    'OrderExecutionError',
    'AlpacaClient',
    'ConnectionMonitor',
    'ConnectionAlert',
    'OrderSelector',
    'MarketCondition',
    'ExecutionSpeed',
    'PriceAggression',
    'BrokerRegistry',
    'get_broker_registry',
    'BROKER_IMPLEMENTATIONS'
] 