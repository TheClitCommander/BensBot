#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Machine Learning Strategy implementation.
"""

import logging
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

from trading_bot.strategies.strategy import Strategy

logger = logging.getLogger(__name__)

class MLStrategy(Strategy):
    """
    Strategy based on machine learning predictions.
    """
    
    def __init__(
        self,
        name: str,
        model=None,
        threshold: float = 0.0,
        position_sizing: str = "fixed",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the machine learning strategy.
        
        Args:
            name: Name of the strategy
            model: ML model to use for predictions
            threshold: Threshold for signal generation
            position_sizing: Method for position sizing
            stop_loss: Stop loss percentage
            take_profit: Take profit percentage
            config: Additional configuration
        """
        super().__init__(name, config)
        
        self.model = model
        self.threshold = threshold
        self.position_sizing = position_sizing
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def generate_signals(self, data: Any) -> Dict[str, Any]:
        """
        Generate trading signals based on model predictions.
        
        Args:
            data: Market data or other inputs
            
        Returns:
            Dictionary containing signal information
        """
        if self.model is None or not hasattr(self.model, 'predict'):
            logger.warning(f"No valid model available for {self.name}")
            return {'signal': 'NEUTRAL', 'strength': 0.0}
        
        try:
            # Convert data to a format suitable for prediction
            if isinstance(data, pd.DataFrame):
                # Use the model directly
                predictions = self.model.predict(data)
            else:
                # Try to interpret the data
                logger.warning(f"Unsupported data type for {self.name}: {type(data)}")
                return {'signal': 'NEUTRAL', 'strength': 0.0}
            
            # Simple signal logic based on predictions
            if len(predictions) == 0:
                return {'signal': 'NEUTRAL', 'strength': 0.0}
                
            # Get the most recent prediction
            prediction = predictions[-1]
            
            # Determine signal based on threshold
            signal = 'NEUTRAL'
            if prediction > self.threshold:
                signal = 'BUY'
            elif prediction < -self.threshold:
                signal = 'SELL'
                
            # Calculate signal strength (normalized)
            strength = min(1.0, abs(prediction) * 2)
            
            return {
                'signal': signal,
                'strength': strength,
                'prediction': float(prediction),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating signal for {self.name}: {str(e)}")
            return {'signal': 'ERROR', 'strength': 0.0}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert strategy to dictionary for serialization.
        
        Returns:
            Strategy as dictionary
        """
        return {
            "type": "ml_strategy",
            "name": self.name,
            "model": self.model,
            "threshold": self.threshold,
            "position_sizing": self.position_sizing,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any], model_factory=None) -> "MLStrategy":
        """
        Create strategy from dictionary.
        
        Args:
            config: Strategy configuration
            model_factory: MLModelFactory instance to load model
            
        Returns:
            MLStrategy instance
        """
        if model_factory is None:
            try:
                from trading_bot.ml.model_factory import MLModelFactory
                model_factory = MLModelFactory()
            except ImportError:
                raise ImportError("MLModelFactory not found. Please provide a model_factory.")
        
        # Load model
        model = model_factory.load_model(config["name"])
        
        if model is None:
            raise ValueError(f"Failed to load model: {config['name']}")
        
        # Create strategy
        return cls(
            name=config["name"],
            model=model,
            threshold=config.get("threshold", 0.0),
            position_sizing=config.get("position_sizing", "fixed"),
            stop_loss=config.get("stop_loss"),
            take_profit=config.get("take_profit")
        ) 