"""
Core components for the trading bot system.
Contains base classes, interfaces, and common abstractions.
"""

from trading_bot.core.interfaces import (
    DataSourceInterface,
    IndicatorInterface,
    StrategyInterface,
    WebhookInterface
)

from trading_bot.core.service_registry import ServiceRegistry

__all__ = [
    'DataSourceInterface',
    'IndicatorInterface',
    'StrategyInterface',
    'WebhookInterface',
    'ServiceRegistry'
] 