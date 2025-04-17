#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common market types used across the trading bot system.
This centralizes definitions to avoid duplication and ensure consistency.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from datetime import datetime


class MarketRegime(str, Enum):
    """Market regime types."""
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOL = "HIGH_VOL"
    LOW_VOL = "LOW_VOL"
    CRISIS = "CRISIS"
    UNKNOWN = "UNKNOWN"


@dataclass
class MarketRegimeEvent:
    """Event representing a change in market regime."""
    timestamp: datetime
    old_regime: MarketRegime
    new_regime: MarketRegime
    confidence: float
    metadata: Optional[Any] = None
    
    def __init__(
        self,
        timestamp: datetime,
        previous_regime: MarketRegime,
        new_regime: MarketRegime,
        confidence: float,
        metrics: Dict[str, float],
        source: str = "MarketContextFetcher",
        old_regime: MarketRegime = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a market regime change event.
        
        Args:
            timestamp: When the regime change was detected
            previous_regime: The previous market regime
            new_regime: The newly detected market regime
            confidence: Confidence level in the regime detection (0.0-1.0)
            metrics: Dictionary of metrics that led to the regime detection
            source: Source component that generated this event
            old_regime: The previous market regime
            metadata: Additional metadata for the event
        """
        self.timestamp = timestamp
        self.previous_regime = previous_regime
        self.new_regime = new_regime
        self.confidence = confidence
        self.metrics = metrics
        self.source = source
        self.old_regime = old_regime
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        result = {
            "timestamp": self.timestamp.isoformat(),
            "previous_regime": self.previous_regime.name,
            "new_regime": self.new_regime.name,
            "confidence": self.confidence,
            "metrics": self.metrics,
            "source": self.source
        }
        
        if self.old_regime:
            result["old_regime"] = self.old_regime.name
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketRegimeEvent':
        """Create event from dictionary"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
            
        old_regime = data.get("old_regime")
        if old_regime:
            old_regime = MarketRegime[old_regime]
        
        return cls(
            timestamp=timestamp,
            previous_regime=MarketRegime[data["previous_regime"]],
            new_regime=MarketRegime[data["new_regime"]],
            confidence=data["confidence"],
            metrics=data["metrics"],
            source=data["source"],
            old_regime=old_regime,
            metadata=data.get("metadata")
        )
    
    def __str__(self) -> str:
        """String representation of event"""
        return (f"Market Regime Change: {self.previous_regime.name} → "
                f"{self.new_regime.name} (Confidence: {self.confidence:.2f})")


@dataclass
class MarketData:
    """Basic market data point."""
    symbol: str
    timestamp: datetime
    close: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "close": self.close,
        }
        
        # Add optional fields if available
        if self.open is not None:
            result["open"] = self.open
        if self.high is not None:
            result["high"] = self.high
        if self.low is not None:
            result["low"] = self.low
        if self.volume is not None:
            result["volume"] = self.volume
        if self.source:
            result["source"] = self.source
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create from dictionary"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
            
        return cls(
            symbol=data["symbol"],
            timestamp=timestamp,
            close=data["close"],
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            volume=data.get("volume"),
            source=data.get("source"),
            metadata=data.get("metadata", {})
        )


class MarketRegimeDetector:
    """
    Base class for market regime detectors.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the detector.
        
        Args:
            config: Configuration for the detector
        """
        self.config = config or {}
        self.current_regime = MarketRegime.UNKNOWN
        self.confidence = 0.0
        
    def detect_regime(self, data: Dict[str, Any]) -> MarketRegimeEvent:
        """
        Detect the current market regime based on the provided data.
        
        Args:
            data: Market data for regime detection
            
        Returns:
            MarketRegimeEvent with the detected regime
        """
        old_regime = self.current_regime
        metrics = self._calculate_metrics(data)
        regime, confidence = self._classify_regime(metrics)
        
        # Update current regime
        self.current_regime = regime
        self.confidence = confidence
        
        # Create event
        event = MarketRegimeEvent(
            timestamp=datetime.now(),
            old_regime=old_regime,
            new_regime=regime,
            confidence=confidence,
            metrics=metrics
        )
        
        return event
    
    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for regime detection.
        
        Args:
            data: Market data for metric calculation
            
        Returns:
            Dictionary of calculated metrics
        """
        # Base implementation returns empty metrics
        return {}
    
    def _classify_regime(self, metrics: Dict[str, Any]) -> tuple[MarketRegime, float]:
        """
        Classify the market regime based on metrics.
        
        Args:
            metrics: Calculated market metrics
            
        Returns:
            Tuple of (MarketRegime, confidence)
        """
        # Base implementation returns UNKNOWN with zero confidence
        return MarketRegime.UNKNOWN, 0.0 