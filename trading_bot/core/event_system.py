#!/usr/bin/env python3
"""
Event system for the trading bot.

This module provides an event bus implementation and re-exports the event types.
"""

from typing import Dict, List, Callable, Any, Optional
from trading_bot.core.events import EventType, Event

class EventSystem:
    """
    Simple event bus implementation for the trading bot.
    Allows components to subscribe to and publish events.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type with a callback function"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe a callback from an event type"""
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            
    def publish(self, event: Any):
        """Publish an event to all subscribers of its type"""
        if not hasattr(event, 'type'):
            raise ValueError(f"Event must have a 'type' attribute: {event}")
            
        event_type = event.type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event)
                
    def clear_all_subscriptions(self):
        """Clear all event subscriptions"""
        self._subscribers.clear()
        
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get the number of subscribers for a specific event type or all event types"""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        else:
            return sum(len(subscribers) for subscribers in self._subscribers.values())
