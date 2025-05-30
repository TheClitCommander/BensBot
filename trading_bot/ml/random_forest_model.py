#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random Forest model implementation.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any

try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    logging.warning("scikit-learn not available. Random Forest model will not work.")
    HAS_SKLEARN = False

from trading_bot.ml.base_model import BaseMLModel

logger = logging.getLogger(__name__)

class RandomForestModel(BaseMLModel):
    """
    Random Forest model implementation.
    """
    
    def __init__(
        self, 
        name: str,
        n_estimators: int = 100,
        max_depth: int = 10,
        features: Optional[List[str]] = None,
        target_column: str = "close",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the random forest model.
        
        Args:
            name: Unique identifier for this model
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of the trees
            features: List of feature columns to use
            target_column: Column to predict
            config: Additional configuration options
        """
        super().__init__(name, config)
        
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.features = features
        self.target_column = target_column
        self.model = None
        self.feature_columns = None
        
        # Check if scikit-learn is available
        if not HAS_SKLEARN:
            logger.warning(f"scikit-learn is not available, {name} will not work")
        
    def train(self, features: pd.DataFrame, targets: pd.DataFrame = None) -> None:
        """
        Train the random forest model.
        
        Args:
            features: Feature DataFrame
            targets: Target DataFrame (if None, will use target_column from features)
        """
        if not HAS_SKLEARN:
            logger.error("Cannot train model: scikit-learn is not available")
            return
            
        logger.info(f"Training random forest model {self.name}")
        
        # Determine feature columns if not set
        if self.feature_columns is None:
            if self.features is not None:
                self.feature_columns = [col for col in self.features if col in features.columns]
            else:
                self.feature_columns = features.columns.tolist()
                if self.target_column in self.feature_columns:
                    self.feature_columns.remove(self.target_column)
        
        # Get X and y
        X = features[self.feature_columns].values
        
        if targets is not None:
            y = targets.values
        else:
            y = features[self.target_column].values
        
        # Create and train model
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=42
        )
        self.model.fit(X, y)
        
        # Update model state
        self.is_trained = True
        
        logger.info(f"Random forest model {self.name} trained successfully")
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions from the random forest model.
        
        Args:
            features: Feature DataFrame
            
        Returns:
            Numpy array of predictions
        """
        if not self.is_trained or self.model is None:
            logger.error("Model not trained. Call train() first.")
            return np.array([])
            
        # Get features
        X = features[self.feature_columns].values
        
        # Make predictions
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from the random forest.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained, cannot calculate feature importance")
            return {}
            
        # Get feature importance
        importance = self.model.feature_importances_
        
        # Map to feature names
        feature_importance = {
            feature: float(importance[i]) 
            for i, feature in enumerate(self.feature_columns)
        }
        
        return feature_importance 