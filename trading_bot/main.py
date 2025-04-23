#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot Main Module

This module integrates the feature engineering, model training, trade analysis,
and visualization components for interpretable machine learning trading.
"""

import pandas as pd
import numpy as np
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import components
from trading_bot.utils.feature_engineering import FeatureEngineering
from trading_bot.models.model_trainer import ModelTrainer
from trading_bot.analysis.trade_analyzer import TradeAnalyzer
from trading_bot.visualization.model_dashboard import ModelDashboard

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    return config

def prepare_output_dirs(config: Dict[str, Any]) -> None:
    """
    Create necessary output directories.
    
    Args:
        config: Configuration dictionary
    """
    base_dir = config.get('output_dir', './output')
    
    # Create subdirectories
    dirs = [
        base_dir,
        os.path.join(base_dir, 'models'),
        os.path.join(base_dir, 'logs'),
        os.path.join(base_dir, 'logs/trades'),
        os.path.join(base_dir, 'visualizations')
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_data(config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Load market data from source.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with loaded dataframes
    """
    data_sources = config.get('data_sources', {})
    result = {}
    
    for source_name, source_config in data_sources.items():
        path = source_config.get('path')
        if path and os.path.exists(path):
            df = pd.read_csv(path, parse_dates=True, index_col=source_config.get('index_col', 0))
            result[source_name] = df
        else:
            print(f"Warning: Could not load data source {source_name} from {path}")
    
    return result

def setup_components(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize all system components.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with initialized components
    """
    # Setup parameters for each component
    fe_params = config.get('feature_engineering', {})
    mt_params = config.get('model_trainer', {})
    ta_params = config.get('trade_analyzer', {})
    vd_params = config.get('visualization', {})
    
    # Set output directories
    base_dir = config.get('output_dir', './output')
    fe_params['output_dir'] = os.path.join(base_dir, 'features')
    mt_params['output_dir'] = os.path.join(base_dir, 'models')
    mt_params['model_dir'] = os.path.join(base_dir, 'models')
    ta_params['log_dir'] = os.path.join(base_dir, 'logs/trades')
    vd_params['output_dir'] = os.path.join(base_dir, 'visualizations')
    
        # Initialize components
    feature_engineering = FeatureEngineering(fe_params)
    model_trainer = ModelTrainer(mt_params)
    trade_analyzer = TradeAnalyzer(ta_params)
    model_dashboard = ModelDashboard(vd_params)
    
    # Connect visualization dashboard to other components
    model_dashboard.connect_components(
        trade_analyzer=trade_analyzer,
        model_trainer=model_trainer,
        feature_engineering=feature_engineering
    )
    
    return {
        'feature_engineering': feature_engineering,
        'model_trainer': model_trainer,
        'trade_analyzer': trade_analyzer,
        'model_dashboard': model_dashboard
    }

def generate_features(components: Dict[str, Any], data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Generate features for all data sources.
    
    Args:
        components: Component dictionary
        data: Data dictionary
        
    Returns:
        Dictionary with features
    """
    feature_engineering = components['feature_engineering']
    features = {}
    
    for source_name, df in data.items():
        print(f"Generating features for {source_name}...")
        features[source_name] = feature_engineering.generate_features(df)
        
    return features

def train_models(components: Dict[str, Any], features: Dict[str, pd.DataFrame], 
                config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train models based on configuration.
    
    Args:
        components: Component dictionary
        features: Features dictionary
        config: Configuration dictionary
        
    Returns:
        Dictionary with training results
    """
    model_trainer = components['model_trainer']
    feature_engineering = components['feature_engineering']
    model_configs = config.get('models', [])
    results = {}
    
    for model_config in model_configs:
        model_name = model_config.get('name', 'default')
        model_type = model_config.get('type', 'classification')
        source_name = model_config.get('data_source')
        target_horizon = model_config.get('target_horizon', 5)
        
        if source_name not in features:
            print(f"Warning: Data source {source_name} not found for model {model_name}")
            continue
            
        # Prepare data
        feature_df = features[source_name]
        
        # Generate target labels
        if not model_config.get('target_column'):
            # Generate labels if not specified
            print(f"Generating target labels for model {model_name}...")
            data_df = data.get(source_name)
            if data_df is not None:
                feature_df = feature_engineering.add_return_labels(
                    df=feature_df,
                    future_windows=[target_horizon],
                    thresholds=[0.0, 0.01, 0.02]
                )
                
                # Set target column based on type
                if model_type == 'classification':
                    target_column = f'label_{target_horizon}d_{int(model_config.get("threshold", 1) * 100)}pct'
                else:
                    target_column = f'future_return_{target_horizon}'
            else:
                print(f"Warning: Original data not found for {source_name}, cannot generate labels")
                continue
        else:
            target_column = model_config.get('target_column')
            
        if target_column not in feature_df.columns:
            print(f"Warning: Target column {target_column} not found in features")
            continue
            
        # Prepare train/test dataset
        X, y, metadata = feature_engineering.to_ml_dataset(feature_df, target_column)
        
        # Skip if not enough data
        if len(X) < 100:
            print(f"Warning: Not enough data for model {model_name} ({len(X)} samples)")
            continue
            
        # Train-test split
        train_size = int(len(X) * 0.8)
        X_train, y_train = X.iloc[:train_size], y.iloc[:train_size]
        X_test, y_test = X.iloc[train_size:], y.iloc[train_size:]
        
        # Check for regime column
        regime_column = None
        if 'market_regime' in feature_df.columns:
            regime_column = 'market_regime'
            
        # Train model
        print(f"Training model {model_name}...")
        model = model_trainer.train_model(
            X=X_train,
            y=y_train,
            model_type=model_type,
            model_name=model_name
        )
        
        # Cross-validation
        print(f"Performing cross-validation for model {model_name}...")
        cv_results = model_trainer.time_series_cv(
            X=X_train,
            y=y_train,
            model_type=model_type,
            model_name=model_name
        )
        
        # Train regime-specific models if applicable
        if regime_column and model_config.get('use_regime_models', True):
            print(f"Training regime-specific models for {model_name}...")
            regime_models = model_trainer.train_regime_specific_models(
                X=X_train.copy(),
                y=y_train.copy(),
                regime_column=regime_column,
                model_type=model_type,
                base_model_name=model_name
            )
        
        # Evaluate on test set
        print(f"Evaluating model {model_name}...")
        evaluation = model_trainer.evaluate_model(
            X=X_test,
            y=y_test,
            model_name=model_name
        )
        
        # Save model
        print(f"Saving model {model_name}...")
        model_path = model_trainer.save_model(model_name=model_name)
        
        # Store results
        results[model_name] = {
            'model_path': model_path,
            'evaluation': evaluation,
            'cv_results': cv_results,
            'feature_importance': model_trainer.get_top_features(model_name, top_n=20)
        }
        
    return results

def analyze_features_and_models(components: Dict[str, Any], 
                              training_results: Dict[str, Any],
                              features: Dict[str, pd.DataFrame]) -> None:
    """
    Analyze feature importance and model performance.
    
    Args:
        components: Component dictionary
        training_results: Training results
        features: Features dictionary
    """
    model_dashboard = components['model_dashboard']
    
    # Create visualizations
    print("Creating model dashboard...")
    dashboard_paths = model_dashboard.create_dashboard(interactive=True)
    
    # Print dashboard location
    if 'index' in dashboard_paths:
        print(f"Dashboard created at: {dashboard_paths['index']}")
    
    # Print model performance summaries
    for model_name, results in training_results.items():
        print(f"\nModel: {model_name}")
        print("Evaluation metrics:")
        for metric, value in results['evaluation'].items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.4f}")
                
        print("Top 5 features:")
        top_features = list(results['feature_importance'].items())[:5]
        for feature, importance in top_features:
            print(f"  {feature}: {importance:.4f}")
            
def run_backtest(components: Dict[str, Any], features: Dict[str, pd.DataFrame],
               data: Dict[str, pd.DataFrame], config: Dict[str, Any]) -> None:
    """
    Run backtest to generate trade signals and analyze performance.
    
    Args:
        components: Component dictionary
        features: Features dictionary
        data: Original data dictionary
        config: Configuration dictionary
    """
    model_trainer = components['model_trainer']
    trade_analyzer = components['trade_analyzer']
    
    # Get backtest configuration
    backtest_config = config.get('backtest', {})
    model_name = backtest_config.get('model_name', 'default')
    data_source = backtest_config.get('data_source')
    
    if data_source not in features:
        print(f"Warning: Data source {data_source} not found for backtest")
        return
        
    # Get feature and price data
    feature_df = features[data_source]
    price_df = data[data_source]
    
    # Check for regime column
    regime_column = None
    if 'market_regime' in feature_df.columns:
        regime_column = 'market_regime'
    
    # Backtest period
    test_size = int(len(feature_df) * backtest_config.get('test_size', 0.2))
    feature_test = feature_df.iloc[-test_size:]
    price_test = price_df.iloc[-test_size:]
    
    print(f"Running backtest with {test_size} periods...")
    
    # Generate predictions for each period
    for i in range(len(feature_test)):
        # Get features for current period
        current_features = feature_test.iloc[i:i+1]
        current_timestamp = feature_test.index[i]
        
        # Get regime if available
        regime = current_features[regime_column].iloc[0] if regime_column else None
        
        # Generate prediction
        try:
            # Get prediction and confidence
            if hasattr(model_trainer.models[model_name], 'predict_proba'):
                # Classification model
                pred_proba = model_trainer.predict_proba(current_features, model_name, 
                                                      regime=regime, regime_column=regime_column)
                prediction = model_trainer.predict(current_features, model_name, 
                                                 regime=regime, regime_column=regime_column)[0]
                confidence = np.max(pred_proba[0])
            else:
                # Regression model
                prediction = model_trainer.predict(current_features, model_name, 
                                                 regime=regime, regime_column=regime_column)[0]
                confidence = None
                
            # Get feature explanation
            explanations = model_trainer.get_feature_explanation(current_features, model_name, regime)
            top_features = explanations[0]['top_features'] if explanations else {}
            
            # Log prediction
            prediction_entry = trade_analyzer.log_prediction(
                timestamp=current_timestamp,
                features=current_features,
                prediction=prediction,
                confidence=confidence,
                top_features=top_features,
                regime=regime if regime else 'unknown',
                model_name=model_name,
                metadata={'price': price_test.iloc[i]['close'] if 'close' in price_test.columns else None}
            )
            
            # Determine actual outcome (if we have future data)
            if i < len(feature_test) - 5:  # Assuming 5-period forward returns
                # For classification models
                if isinstance(prediction, (int, np.integer)):
                    # Get actual direction (1, 0, -1)
                    future_return = price_test.iloc[i+5]['close'] / price_test.iloc[i]['close'] - 1
                    actual_outcome = 1 if future_return > 0.01 else (-1 if future_return < -0.01 else 0)
                    pnl = future_return if prediction == np.sign(future_return) else -future_return
                else:
                    # For regression models
                    future_return = price_test.iloc[i+5]['close'] / price_test.iloc[i]['close'] - 1
                    actual_outcome = future_return
                    pnl = future_return if np.sign(prediction) == np.sign(future_return) else -future_return
                
                # Log outcome
                trade_analyzer.log_trade_outcome(
                    prediction_id=current_timestamp,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    trade_metadata={'future_price': price_test.iloc[i+5]['close']}
                )
        except Exception as e:
            print(f"Error in prediction at {current_timestamp}: {str(e)}")
    
    # Analyze backtest results
    print("Analyzing backtest results...")
    
    # Overall performance
    performance = trade_analyzer.analyze_model_performance()
    
    print("\nBacktest Performance:")
    print(f"Total trades: {performance['total_trades']}")
    print(f"Accuracy: {performance['accuracy']:.4f}")
    print(f"Win rate: {performance['win_rate']:.4f}")
    print(f"Profit factor: {performance['profit_factor']:.4f}")
    print(f"Total P&L: {performance['total_pnl']:.4f}")
    
    # Performance by regime
    regime_performance = trade_analyzer.compare_regimes()
    
    print("\nPerformance by Regime:")
    for regime, metrics in regime_performance.items():
        if regime != 'overall':
            print(f"\n{regime.capitalize()} Regime:")
            print(f"  Trades: {metrics['total_trades']}")
            print(f"  Accuracy: {metrics['accuracy']:.4f}")
            print(f"  Win rate: {metrics['win_rate']:.4f}")
            print(f"  Profit factor: {metrics['profit_factor']:.4f}")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Trading Bot with Interpretable ML')
    parser.add_argument('--config', type=str, default='config.json', help='Path to configuration file')
    parser.add_argument('--mode', type=str, default='train', choices=['train', 'backtest', 'dashboard'],
                      help='Operating mode: train models, run backtest, or create dashboard')
    args = parser.parse_args()
    
    # Load configuration
    print(f"Loading configuration from {args.config}...")
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return
    
    # Prepare directories
    prepare_output_dirs(config)
    
    # Load data
    print("Loading market data...")
    data = load_data(config)
    
    if not data:
        print("No data loaded. Exiting.")
        return
    
    # Initialize components
    print("Setting up components...")
    components = setup_components(config)
    
    # Generate features
    print("Generating features...")
    features = generate_features(components, data)
    
    # Execute based on mode
    if args.mode == 'train':
        # Train models
        print("Training models...")
        training_results = train_models(components, features, config)
        
        # Analyze results
        print("Analyzing model results...")
        analyze_features_and_models(components, training_results, features)
        
    elif args.mode == 'backtest':
        # Run backtest
        print("Running backtest simulation...")
        run_backtest(components, features, data, config)
        
        # Create visualizations
        print("Creating performance visualizations...")
        components['model_dashboard'].create_dashboard(interactive=True)
        
    elif args.mode == 'dashboard':
        # Just create dashboard
        print("Creating visualization dashboard...")
        dashboard_paths = components['model_dashboard'].create_dashboard(interactive=True)
        
        # Print dashboard location
        if 'index' in dashboard_paths:
            print(f"Dashboard created at: {dashboard_paths['index']}")
    
    print("Done!")

if __name__ == "__main__":
    main() 