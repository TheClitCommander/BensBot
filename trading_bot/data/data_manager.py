#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Data Manager for backtesting and learning operations.
Consolidates functionality from multiple implementations into a single, consistent interface.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path
import pickle
from sklearn.preprocessing import StandardScaler, MinMaxScaler

logger = logging.getLogger(__name__)

class DataManager:
    """
    Unified data manager for handling data operations related to:
    - Market data loading and preprocessing
    - Feature generation and selection
    - Data splitting and scaling
    - Backtest result management
    - Learning result storage and retrieval
    """
    
    def __init__(
        self, 
        data_dir: str = "data",
        results_dir: str = "results",
        models_dir: str = "models"
    ):
        """
        Initialize the unified data manager.
        
        Args:
            data_dir: Directory for input data storage
            results_dir: Directory for results storage
            models_dir: Directory for model storage
        """
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.models_dir = Path(models_dir)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage dictionaries
        self.backtest_results = {}
        self.learning_results = {}
        self.current_data = {}
        
        # Initialize data transformers
        self.scalers = {}
        
        logger.info(f"Initialized Unified Data Manager with data_dir: {data_dir}")
    
    # -------------------------------------------------------------------------
    # Market Data Management
    # -------------------------------------------------------------------------
    
    def load_market_data(
        self,
        symbol: str,
        timeframe: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        custom_data_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load market data for a specific symbol and timeframe.
        
        Args:
            symbol: Market symbol to load data for
            timeframe: Data frequency (1d, 1h, etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            custom_data_path: Optional path to custom data file
            
        Returns:
            DataFrame with market data
        """
        # Use custom data if provided
        if custom_data_path and os.path.exists(custom_data_path):
            try:
                data = pd.read_csv(custom_data_path)
                logger.info(f"Loaded custom data from {custom_data_path}")
                
                # Convert date column if present
                date_col = next((col for col in data.columns if 'date' in col.lower() or 'time' in col.lower()), None)
                if date_col:
                    data[date_col] = pd.to_datetime(data[date_col])
                    data = data.rename(columns={date_col: 'datetime'})
                    data = data.set_index('datetime')
                
                # Filter by date range if provided
                if start_date:
                    data = data[data.index >= start_date]
                if end_date:
                    data = data[data.index <= end_date]
                
                return data
                
            except Exception as e:
                logger.error(f"Error loading custom data: {str(e)}")
                return pd.DataFrame()
        
        # Load standard data file
        file_name = f"{symbol}_{timeframe}.csv"
        file_path = self.data_dir / file_name
        
        try:
            # Load data from CSV
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
            logger.info(f"Loaded {len(data)} rows for {symbol} ({timeframe})")
            
            # Filter by date range if provided
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
                
            # Store in current data dictionary
            key = f"{symbol}_{timeframe}"
            self.current_data[key] = data
            
            return data
            
        except FileNotFoundError:
            logger.error(f"Data file not found: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading market data: {str(e)}")
            return pd.DataFrame()
    
    def generate_features(
        self,
        data: pd.DataFrame,
        feature_set: str = "default",
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Generate features from raw market data.
        
        Args:
            data: Input market data
            feature_set: Name of feature set to generate
            params: Parameters for feature generation
            
        Returns:
            DataFrame with generated features
        """
        params = params or {}
        features = data.copy()
        
        if feature_set == "default":
            # Basic price-based features
            if "close" in features.columns:
                # Price-based features
                features["returns"] = features["close"].pct_change()
                features["log_returns"] = np.log(features["close"] / features["close"].shift(1))
                
                # Moving averages
                for window in [5, 10, 20, 50, 200]:
                    features[f"ma_{window}"] = features["close"].rolling(window=window).mean()
                    features[f"ma_ratio_{window}"] = features["close"] / features[f"ma_{window}"]
                
                # Volatility estimates
                for window in [10, 20, 50]:
                    features[f"volatility_{window}"] = features["returns"].rolling(window=window).std()
                
                # RSI 
                delta = features["close"].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                
                rs = avg_gain / avg_loss
                features["rsi_14"] = 100 - (100 / (1 + rs))
                
                # MACD
                features["ema_12"] = features["close"].ewm(span=12, adjust=False).mean()
                features["ema_26"] = features["close"].ewm(span=26, adjust=False).mean()
                features["macd"] = features["ema_12"] - features["ema_26"]
                features["macd_signal"] = features["macd"].ewm(span=9, adjust=False).mean()
                features["macd_hist"] = features["macd"] - features["macd_signal"]
            
            # Volume-based features if available
            if "volume" in features.columns:
                features["volume_ma_10"] = features["volume"].rolling(window=10).mean()
                features["volume_ratio"] = features["volume"] / features["volume_ma_10"]
                
        elif feature_set == "advanced":
            # Include all default features first
            features = self.generate_features(data, feature_set="default")
            
            # Add advanced features
            if "high" in features.columns and "low" in features.columns:
                # Bollinger Bands
                window = params.get("bb_window", 20)
                std_dev = params.get("bb_std", 2)
                
                features[f"bb_ma_{window}"] = features["close"].rolling(window=window).mean()
                features[f"bb_std_{window}"] = features["close"].rolling(window=window).std()
                features[f"bb_upper_{window}"] = features[f"bb_ma_{window}"] + (features[f"bb_std_{window}"] * std_dev)
                features[f"bb_lower_{window}"] = features[f"bb_ma_{window}"] - (features[f"bb_std_{window}"] * std_dev)
                features[f"bb_width_{window}"] = (features[f"bb_upper_{window}"] - features[f"bb_lower_{window}"]) / features[f"bb_ma_{window}"]
                features[f"bb_pct_{window}"] = (features["close"] - features[f"bb_lower_{window}"]) / (features[f"bb_upper_{window}"] - features[f"bb_lower_{window}"])
                
                # ATR (Average True Range)
                tr1 = abs(features["high"] - features["low"])
                tr2 = abs(features["high"] - features["close"].shift(1))
                tr3 = abs(features["low"] - features["close"].shift(1))
                
                features["tr"] = pd.DataFrame([tr1, tr2, tr3]).max()
                features["atr_14"] = features["tr"].rolling(window=14).mean()
        
        # Drop rows with NaN values from calculations
        features = features.dropna()
        
        return features
    
    def split_data(
        self,
        features: pd.DataFrame,
        target_col: str = "target_next_return",
        test_size: float = 0.2,
        validation_size: float = 0.2,
        shuffle: bool = False,
        random_state: int = 42
    ) -> Dict[str, Union[pd.DataFrame, pd.Series]]:
        """
        Split data into training, validation, and test sets.
        
        Args:
            features: Feature DataFrame
            target_col: Target column name
            test_size: Fraction of data for testing
            validation_size: Fraction of training data for validation
            shuffle: Whether to shuffle data before splitting
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with split dataframes and series
        """
        if target_col not in features.columns:
            raise ValueError(f"Target column '{target_col}' not found in features")
        
        # Extract target variable
        y = features[target_col]
        X = features.drop(columns=[target_col])
        
        # Extract potential target direction column
        if "target_next_direction" in X.columns:
            direction = X["target_next_direction"]
            X = X.drop(columns=["target_next_direction"])
        else:
            direction = None
        
        # First split into train+val and test
        if shuffle:
            from sklearn.model_selection import train_test_split
            X_train_val, X_test, y_train_val, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            if direction is not None:
                train_val_idx = X_train_val.index
                test_idx = X_test.index
                direction_train_val = direction.loc[train_val_idx]
                direction_test = direction.loc[test_idx]
            
        else:
            # Time series split (no shuffle)
            test_idx = int(len(X) * (1 - test_size))
            X_train_val, X_test = X.iloc[:test_idx], X.iloc[test_idx:]
            y_train_val, y_test = y.iloc[:test_idx], y.iloc[test_idx:]
            
            if direction is not None:
                direction_train_val = direction.iloc[:test_idx]
                direction_test = direction.iloc[test_idx:]
        
        # Then split train+val into train and val
        if shuffle:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_val, y_train_val, 
                test_size=validation_size / (1 - test_size),
                random_state=random_state
            )
            
            if direction is not None:
                train_idx = X_train.index
                val_idx = X_val.index
                direction_train = direction_train_val.loc[train_idx]
                direction_val = direction_train_val.loc[val_idx]
            
        else:
            # Time series split (no shuffle)
            val_idx = int(len(X_train_val) * (1 - validation_size / (1 - test_size)))
            X_train, X_val = X_train_val.iloc[:val_idx], X_train_val.iloc[val_idx:]
            y_train, y_val = y_train_val.iloc[:val_idx], y_train_val.iloc[val_idx:]
            
            if direction is not None:
                direction_train = direction_train_val.iloc[:val_idx]
                direction_val = direction_train_val.iloc[val_idx:]
        
        result = {
            "X_train": X_train,
            "X_val": X_val, 
            "X_test": X_test,
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test
        }
        
        if direction is not None:
            result.update({
                "direction_train": direction_train,
                "direction_val": direction_val,
                "direction_test": direction_test
            })
        
        return result
    
    def preprocess_data(
        self,
        X_train: pd.DataFrame,
        X_val: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        scaler_type: str = "standard",
        feature_selection: bool = False,
        n_features: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Preprocess data by scaling and optionally performing feature selection.
        
        Args:
            X_train: Training features
            X_val: Validation features
            X_test: Test features
            scaler_type: Type of scaler ('standard' or 'minmax')
            feature_selection: Whether to perform feature selection
            n_features: Number of features to select
            
        Returns:
            Dictionary with processed data and scaler
        """
        # Initialize scaler
        if scaler_type == "standard":
            scaler = StandardScaler()
        elif scaler_type == "minmax":
            scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaler type: {scaler_type}")
        
        # Fit scaler on training data and transform
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        # Save the scaler
        self.scalers[scaler_type] = scaler
        
        # Transform validation data if provided
        X_val_scaled = None
        if X_val is not None:
            X_val_scaled = pd.DataFrame(
                scaler.transform(X_val),
                columns=X_val.columns,
                index=X_val.index
            )
        
        # Transform test data if provided
        X_test_scaled = None
        if X_test is not None:
            X_test_scaled = pd.DataFrame(
                scaler.transform(X_test),
                columns=X_test.columns,
                index=X_test.index
            )
        
        # Feature selection if enabled
        selected_features = None
        if feature_selection and n_features is not None:
            # Basic feature selection based on correlation with target
            feature_correlations = X_train.abs().mean().sort_values(ascending=False)
            selected_features = feature_correlations.head(n_features).index.tolist()
            
            X_train_scaled = X_train_scaled[selected_features]
            
            if X_val_scaled is not None:
                X_val_scaled = X_val_scaled[selected_features]
                
            if X_test_scaled is not None:
                X_test_scaled = X_test_scaled[selected_features]
                
            logger.info(f"Selected {n_features} features based on mean absolute value")
        
        return {
            "X_train_scaled": X_train_scaled,
            "X_val_scaled": X_val_scaled,
            "X_test_scaled": X_test_scaled,
            "scaler": scaler,
            "selected_features": selected_features
        }
    
    # -------------------------------------------------------------------------
    # Backtest Result Management
    # -------------------------------------------------------------------------
    
    def save_backtest_result(
        self,
        backtest_id: str,
        result_data: Dict[str, Any]
    ) -> bool:
        """
        Save a backtest result.
        
        Args:
            backtest_id: Unique identifier for the backtest
            result_data: Dictionary with backtest results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in result_data:
                result_data["timestamp"] = datetime.now().isoformat()
            
            # Create results directory if it doesn't exist
            backtest_dir = self.results_dir / "backtests"
            backtest_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            result_path = backtest_dir / f"{backtest_id}.json"
            
            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)
            
            # Cache in memory
            self.backtest_results[backtest_id] = result_data
            
            logger.info(f"Saved backtest result: {backtest_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving backtest result: {str(e)}")
            return False
    
    def get_backtest_result(
        self,
        backtest_id: str
    ) -> Dict[str, Any]:
        """
        Get a backtest result.
        
        Args:
            backtest_id: Unique identifier for the backtest
            
        Returns:
            Dictionary with backtest results
        """
        # Try to get from in-memory cache first
        if backtest_id in self.backtest_results:
            return self.backtest_results[backtest_id]
        
        # Load from file
        backtest_dir = self.results_dir / "backtests"
        result_path = backtest_dir / f"{backtest_id}.json"
        
        if not result_path.exists():
            logger.error(f"Backtest result not found: {backtest_id}")
            return {}
        
        try:
            with open(result_path, "r") as f:
                result_data = json.load(f)
            
            # Cache in memory
            self.backtest_results[backtest_id] = result_data
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error loading backtest result: {str(e)}")
            return {}
    
    def get_backtest_results(
        self,
        limit: int = 10,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get multiple backtest results.
        
        Args:
            limit: Maximum number of results to return
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of backtest result dictionaries
        """
        backtest_dir = self.results_dir / "backtests"
        
        if not backtest_dir.exists():
            logger.warning("Backtest directory does not exist")
            return []
        
        try:
            # Get all JSON files in backtest directory
            result_files = list(backtest_dir.glob("*.json"))
            
            # Load all results
            results = []
            for file_path in result_files:
                try:
                    with open(file_path, "r") as f:
                        result_data = json.load(f)
                    
                    # Add backtest ID from filename
                    if "backtest_id" not in result_data:
                        result_data["backtest_id"] = file_path.stem
                    
                    results.append(result_data)
                    
                    # Cache in memory
                    self.backtest_results[file_path.stem] = result_data
                    
                except Exception as e:
                    logger.error(f"Error loading backtest result file {file_path}: {str(e)}")
            
            # Sort results
            if sort_by in results[0] if results else False:
                reverse = sort_order.lower() == "desc"
                results.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
            
            # Limit results
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting backtest results: {str(e)}")
            return []
    
    def delete_backtest_result(
        self,
        backtest_id: str
    ) -> bool:
        """
        Delete a backtest result.
        
        Args:
            backtest_id: Unique identifier for the backtest
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from in-memory cache
            if backtest_id in self.backtest_results:
                del self.backtest_results[backtest_id]
            
            # Delete file
            backtest_dir = self.results_dir / "backtests"
            result_path = backtest_dir / f"{backtest_id}.json"
            
            if result_path.exists():
                result_path.unlink()
                logger.info(f"Deleted backtest result: {backtest_id}")
                return True
            else:
                logger.warning(f"Backtest result not found for deletion: {backtest_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting backtest result: {str(e)}")
            return False
    
    # -------------------------------------------------------------------------
    # Learning Result Management
    # -------------------------------------------------------------------------
    
    def save_learning_result(
        self,
        learning_id: str,
        result_data: Dict[str, Any]
    ) -> bool:
        """
        Save a learning result.
        
        Args:
            learning_id: Unique identifier for the learning process
            result_data: Dictionary with learning results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in result_data:
                result_data["timestamp"] = datetime.now().isoformat()
            
            # Create results directory if it doesn't exist
            learning_dir = self.results_dir / "learning"
            learning_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            result_path = learning_dir / f"{learning_id}.json"
            
            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)
            
            # Cache in memory
            self.learning_results[learning_id] = result_data
            
            logger.info(f"Saved learning result: {learning_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving learning result: {str(e)}")
            return False
    
    def get_learning_result(
        self,
        learning_id: str
    ) -> Dict[str, Any]:
        """
        Get a learning result.
        
        Args:
            learning_id: Unique identifier for the learning process
            
        Returns:
            Dictionary with learning results
        """
        # Try to get from in-memory cache first
        if learning_id in self.learning_results:
            return self.learning_results[learning_id]
        
        # Load from file
        learning_dir = self.results_dir / "learning"
        result_path = learning_dir / f"{learning_id}.json"
        
        if not result_path.exists():
            logger.error(f"Learning result not found: {learning_id}")
            return {}
        
        try:
            with open(result_path, "r") as f:
                result_data = json.load(f)
            
            # Cache in memory
            self.learning_results[learning_id] = result_data
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error loading learning result: {str(e)}")
            return {}
    
    def get_learning_results(
        self,
        limit: int = 10,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get multiple learning results.
        
        Args:
            limit: Maximum number of results to return
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of learning result dictionaries
        """
        learning_dir = self.results_dir / "learning"
        
        if not learning_dir.exists():
            logger.warning("Learning directory does not exist")
            return []
        
        try:
            # Get all JSON files in learning directory
            result_files = list(learning_dir.glob("*.json"))
            
            # Load all results
            results = []
            for file_path in result_files:
                try:
                    with open(file_path, "r") as f:
                        result_data = json.load(f)
                    
                    # Add learning ID from filename
                    if "learning_id" not in result_data:
                        result_data["learning_id"] = file_path.stem
                    
                    results.append(result_data)
                    
                    # Cache in memory
                    self.learning_results[file_path.stem] = result_data
                    
                except Exception as e:
                    logger.error(f"Error loading learning result file {file_path}: {str(e)}")
            
            # Sort results
            if sort_by in results[0] if results else False:
                reverse = sort_order.lower() == "desc"
                results.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
            
            # Limit results
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting learning results: {str(e)}")
            return []
    
    # -------------------------------------------------------------------------
    # Model Management
    # -------------------------------------------------------------------------
    
    def save_model(
        self,
        model_id: str,
        model: Any,
        model_info: Dict[str, Any]
    ) -> bool:
        """
        Save a trained model.
        
        Args:
            model_id: Unique identifier for the model
            model: Trained model object
            model_info: Dictionary with model metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in model_info:
                model_info["timestamp"] = datetime.now().isoformat()
            
            # Create models directory if it doesn't exist
            model_dir = self.models_dir / model_id
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model to pickle file
            model_path = model_dir / f"{model_id}.pkl"
            
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            
            # Save model info to JSON file
            info_path = model_dir / f"{model_id}_info.json"
            
            with open(info_path, "w") as f:
                json.dump(model_info, f, indent=2)
            
            logger.info(f"Saved model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def load_model(
        self,
        model_id: str
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Load a trained model.
        
        Args:
            model_id: Unique identifier for the model
            
        Returns:
            Tuple of (model, model_info)
        """
        model_dir = self.models_dir / model_id
        model_path = model_dir / f"{model_id}.pkl"
        info_path = model_dir / f"{model_id}_info.json"
        
        if not model_path.exists() or not info_path.exists():
            logger.error(f"Model files not found for: {model_id}")
            return None, {}
        
        try:
            # Load model from pickle file
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            
            # Load model info from JSON file
            with open(info_path, "r") as f:
                model_info = json.load(f)
            
            logger.info(f"Loaded model: {model_id}")
            return model, model_info
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return None, {}
    
    def get_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of model IDs
        """
        if not self.models_dir.exists():
            logger.warning("Models directory does not exist")
            return []
        
        try:
            # Get all subdirectories in models directory
            model_dirs = [d.name for d in self.models_dir.iterdir() if d.is_dir()]
            return model_dirs
            
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return []
    
    def delete_model(
        self,
        model_id: str
    ) -> bool:
        """
        Delete a model.
        
        Args:
            model_id: Unique identifier for the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete model directory and all contents
            model_dir = self.models_dir / model_id
            
            if model_dir.exists():
                for file_path in model_dir.iterdir():
                    file_path.unlink()
                
                model_dir.rmdir()
                logger.info(f"Deleted model: {model_id}")
                return True
            else:
                logger.warning(f"Model not found for deletion: {model_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting model: {str(e)}")
            return False 