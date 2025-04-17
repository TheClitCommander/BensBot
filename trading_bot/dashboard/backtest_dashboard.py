#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Dashboard Interface - Provides unified access to backtest and ML results for the dashboard.
"""

import logging
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO

from trading_bot.data.data_manager import DataManager
from trading_bot.learning.backtest_learner import BacktestLearner

logger = logging.getLogger(__name__)

class BacktestDashboard:
    """
    Provides a unified interface for the dashboard to access backtesting and ML results.
    
    This class:
    - Aggregates data from various sources (backtests, ML models)
    - Creates visualizations for dashboard display
    - Provides a consistent API for the dashboard to consume
    """
    
    def __init__(
        self,
        data_manager: Optional[DataManager] = None,
        learner: Optional[BacktestLearner] = None,
        data_dir: str = "data",
        results_dir: str = "results",
        models_dir: str = "models"
    ):
        """
        Initialize the backtest dashboard interface.
        
        Args:
            data_manager: DataManager instance for data operations
            learner: BacktestLearner instance for ML operations
            data_dir: Directory for data storage
            results_dir: Directory for results storage
            models_dir: Directory for model storage
        """
        self.data_manager = data_manager if data_manager else DataManager(
            data_dir=data_dir, 
            results_dir=results_dir, 
            models_dir=models_dir
        )
        self.learner = learner if learner else BacktestLearner(
            data_manager=self.data_manager,
            models_dir=models_dir
        )
        
        logger.info("Initialized BacktestDashboard interface")
    
    # -------------------------------------------------------------------------
    # Backtest Results
    # -------------------------------------------------------------------------
    
    def get_backtest_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a summary of recent backtests.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of backtest summary dictionaries
        """
        backtest_results = self.data_manager.get_backtest_results(limit=limit)
        
        # Extract summary information
        summaries = []
        for result in backtest_results:
            summary = {
                "backtest_id": result.get("backtest_id"),
                "strategy_name": result.get("strategy_name", "Unknown"),
                "symbol": result.get("symbol", "Unknown"),
                "timeframe": result.get("timeframe", "Unknown"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "initial_capital": result.get("initial_capital", 0),
                "final_capital": result.get("final_capital", 0),
                "total_return_pct": result.get("total_return_pct", 0),
                "annualized_return_pct": result.get("annualized_return_pct", 0),
                "sharpe_ratio": result.get("sharpe_ratio", 0),
                "max_drawdown_pct": result.get("max_drawdown_pct", 0),
                "total_trades": result.get("total_trades", 0),
                "win_rate": result.get("win_rate", 0),
                "timestamp": result.get("timestamp")
            }
            summaries.append(summary)
        
        return summaries
    
    def get_backtest_detail(self, backtest_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific backtest.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Dictionary with backtest details
        """
        return self.data_manager.get_backtest_result(backtest_id)
    
    def generate_equity_curve(self, backtest_id: str) -> Dict[str, Any]:
        """
        Generate an equity curve plot for a backtest.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Dictionary with plot data
        """
        # Get backtest result
        result = self.data_manager.get_backtest_result(backtest_id)
        
        if not result:
            return {"error": f"Backtest {backtest_id} not found"}
        
        # Check if equity curve data exists
        if "equity_curve" not in result:
            return {"error": "Equity curve data not available for this backtest"}
        
        equity_curve = result["equity_curve"]
        
        # Convert to pandas Series if it's a list
        if isinstance(equity_curve, list):
            equity_curve = pd.Series(equity_curve)
        
        # Create plotly figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=equity_curve,
                mode="lines",
                name="Equity",
                line=dict(color="royalblue")
            )
        )
        
        # Update layout
        strategy_name = result.get("strategy_name", "Unknown")
        symbol = result.get("symbol", "Unknown")
        fig.update_layout(
            title=f"Equity Curve - {strategy_name} - {symbol}",
            xaxis_title="Trade Number",
            yaxis_title="Equity",
            height=600,
            width=1000
        )
        
        # Convert to JSON for dashboard
        return {
            "plotly_json": fig.to_json(),
            "backtest_id": backtest_id
        }
    
    def generate_drawdown_chart(self, backtest_id: str) -> Dict[str, Any]:
        """
        Generate a drawdown chart for a backtest.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Dictionary with plot data
        """
        # Get backtest result
        result = self.data_manager.get_backtest_result(backtest_id)
        
        if not result:
            return {"error": f"Backtest {backtest_id} not found"}
        
        # Check if drawdown data exists
        if "drawdowns" not in result:
            # Try to calculate drawdowns from equity curve
            if "equity_curve" in result:
                equity_curve = pd.Series(result["equity_curve"] if isinstance(result["equity_curve"], list) else result["equity_curve"])
                drawdowns = self._calculate_drawdown(equity_curve)
            else:
                return {"error": "Drawdown data not available for this backtest"}
        else:
            drawdowns = result["drawdowns"]
            if isinstance(drawdowns, list):
                drawdowns = pd.Series(drawdowns)
        
        # Create plotly figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=drawdowns * 100,  # Convert to percentage
                mode="lines",
                name="Drawdown",
                line=dict(color="crimson")
            )
        )
        
        # Update layout
        strategy_name = result.get("strategy_name", "Unknown")
        symbol = result.get("symbol", "Unknown")
        fig.update_layout(
            title=f"Drawdown - {strategy_name} - {symbol}",
            xaxis_title="Trade Number",
            yaxis_title="Drawdown (%)",
            height=400,
            width=1000
        )
        
        # Convert to JSON for dashboard
        return {
            "plotly_json": fig.to_json(),
            "backtest_id": backtest_id
        }
    
    def _calculate_drawdown(self, equity_curve: pd.Series) -> pd.Series:
        """
        Calculate drawdown from equity curve.
        
        Args:
            equity_curve: Equity curve series
            
        Returns:
            Drawdown series
        """
        # Calculate running maximum
        running_max = equity_curve.cummax()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        return drawdown
    
    def generate_trade_analysis(self, backtest_id: str) -> Dict[str, Any]:
        """
        Generate trade analysis visualizations.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Dictionary with plot data
        """
        # Get backtest result
        result = self.data_manager.get_backtest_result(backtest_id)
        
        if not result:
            return {"error": f"Backtest {backtest_id} not found"}
        
        # Check if trades data exists
        if "trades" not in result:
            return {"error": "Trades data not available for this backtest"}
        
        trades = result["trades"]
        
        # Convert to DataFrame if it's a list
        if isinstance(trades, list):
            trades = pd.DataFrame(trades)
        
        # Create scatter plot of trades
        fig = go.Figure()
        
        # Add winning trades
        winning_trades = trades[trades["pnl"] > 0]
        if not winning_trades.empty:
            fig.add_trace(
                go.Scatter(
                    x=winning_trades.index,
                    y=winning_trades["pnl"],
                    mode="markers",
                    name="Winning Trades",
                    marker=dict(
                        color="green",
                        size=10,
                        symbol="circle"
                    )
                )
            )
        
        # Add losing trades
        losing_trades = trades[trades["pnl"] < 0]
        if not losing_trades.empty:
            fig.add_trace(
                go.Scatter(
                    x=losing_trades.index,
                    y=losing_trades["pnl"],
                    mode="markers",
                    name="Losing Trades",
                    marker=dict(
                        color="red",
                        size=10,
                        symbol="circle"
                    )
                )
            )
        
        # Update layout
        strategy_name = result.get("strategy_name", "Unknown")
        symbol = result.get("symbol", "Unknown")
        fig.update_layout(
            title=f"Trades - {strategy_name} - {symbol}",
            xaxis_title="Trade Number",
            yaxis_title="Profit/Loss",
            height=500,
            width=1000
        )
        
        # Create trade metrics visualization
        metrics_fig = go.Figure()
        
        # Calculate trade metrics
        win_rate = result.get("win_rate", 0) * 100
        avg_win = trades[trades["pnl"] > 0]["pnl"].mean() if not winning_trades.empty else 0
        avg_loss = abs(trades[trades["pnl"] < 0]["pnl"].mean()) if not losing_trades.empty else 0
        profit_factor = avg_win / avg_loss if avg_loss != 0 else 0
        
        # Create bar chart for metrics
        metrics_fig.add_trace(
            go.Bar(
                x=["Win Rate (%)", "Avg Win", "Avg Loss", "Profit Factor"],
                y=[win_rate, avg_win, avg_loss, profit_factor],
                marker_color=["blue", "green", "red", "purple"]
            )
        )
        
        # Update layout
        metrics_fig.update_layout(
            title=f"Trade Metrics - {strategy_name} - {symbol}",
            xaxis_title="Metric",
            yaxis_title="Value",
            height=400,
            width=800
        )
        
        # Convert to JSON for dashboard
        return {
            "trades_plot": fig.to_json(),
            "metrics_plot": metrics_fig.to_json(),
            "backtest_id": backtest_id
        }
    
    def generate_performance_metrics(self, backtest_id: str) -> Dict[str, Any]:
        """
        Generate performance metrics visualization.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Dictionary with plot data
        """
        # Get backtest result
        result = self.data_manager.get_backtest_result(backtest_id)
        
        if not result:
            return {"error": f"Backtest {backtest_id} not found"}
        
        # Extract key metrics
        metrics = {
            "Total Return (%)": result.get("total_return_pct", 0),
            "Annualized Return (%)": result.get("annualized_return_pct", 0),
            "Sharpe Ratio": result.get("sharpe_ratio", 0),
            "Max Drawdown (%)": result.get("max_drawdown_pct", 0),
            "Win Rate (%)": result.get("win_rate", 0) * 100,
            "Profit Factor": result.get("profit_factor", 0)
        }
        
        # Create plotly figure
        fig = go.Figure()
        
        # Create radar chart for metrics
        fig.add_trace(
            go.Scatterpolar(
                r=list(metrics.values()),
                theta=list(metrics.keys()),
                fill="toself",
                name="Performance Metrics"
            )
        )
        
        # Update layout
        strategy_name = result.get("strategy_name", "Unknown")
        symbol = result.get("symbol", "Unknown")
        fig.update_layout(
            title=f"Performance Metrics - {strategy_name} - {symbol}",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(metrics.values()) * 1.2]
                )
            ),
            height=600,
            width=600
        )
        
        # Create table of metrics
        metrics_table = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["Metric", "Value"],
                        fill_color="paleturquoise",
                        align="left"
                    ),
                    cells=dict(
                        values=[
                            list(metrics.keys()),
                            [f"{v:.2f}" for v in metrics.values()]
                        ],
                        fill_color="lavender",
                        align="left"
                    )
                )
            ]
        )
        
        metrics_table.update_layout(
            title=f"Performance Metrics - {strategy_name} - {symbol}",
            height=400,
            width=500
        )
        
        # Convert to JSON for dashboard
        return {
            "metrics_plot": fig.to_json(),
            "metrics_table": metrics_table.to_json(),
            "backtest_id": backtest_id,
            "raw_metrics": metrics
        }
    
    def compare_backtests(self, backtest_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple backtests.
        
        Args:
            backtest_ids: List of backtest IDs to compare
            
        Returns:
            Dictionary with comparison data and visualizations
        """
        if not backtest_ids:
            return {"error": "No backtest IDs provided"}
        
        # Load backtest results
        results = {}
        for backtest_id in backtest_ids:
            result = self.data_manager.get_backtest_result(backtest_id)
            if result:
                results[backtest_id] = result
        
        if not results:
            return {"error": "No valid backtest results found"}
        
        # Compare equity curves
        equity_curves = {}
        for backtest_id, result in results.items():
            if "equity_curve" in result:
                equity_curve = result["equity_curve"]
                if isinstance(equity_curve, list):
                    equity_curve = pd.Series(equity_curve)
                
                # Normalize to percentage return for fair comparison
                normalized_equity = (equity_curve / equity_curve.iloc[0] - 1) * 100
                equity_curves[backtest_id] = normalized_equity
        
        # Create equity curve comparison plot
        equity_fig = go.Figure()
        
        for backtest_id, equity_curve in equity_curves.items():
            result = results[backtest_id]
            strategy_name = result.get("strategy_name", "Unknown")
            symbol = result.get("symbol", "Unknown")
            label = f"{strategy_name} - {symbol}"
            
            equity_fig.add_trace(
                go.Scatter(
                    y=equity_curve,
                    mode="lines",
                    name=label
                )
            )
        
        equity_fig.update_layout(
            title="Equity Curve Comparison",
            xaxis_title="Trade Number",
            yaxis_title="Return (%)",
            height=600,
            width=1000
        )
        
        # Compare performance metrics
        metrics = {
            "Total Return (%)": [],
            "Annualized Return (%)": [],
            "Sharpe Ratio": [],
            "Max Drawdown (%)": [],
            "Win Rate (%)": [],
            "Profit Factor": []
        }
        
        labels = []
        for backtest_id, result in results.items():
            strategy_name = result.get("strategy_name", "Unknown")
            symbol = result.get("symbol", "Unknown")
            labels.append(f"{strategy_name} - {symbol}")
            
            metrics["Total Return (%)"].append(result.get("total_return_pct", 0))
            metrics["Annualized Return (%)"].append(result.get("annualized_return_pct", 0))
            metrics["Sharpe Ratio"].append(result.get("sharpe_ratio", 0))
            metrics["Max Drawdown (%)"].append(result.get("max_drawdown_pct", 0))
            metrics["Win Rate (%)"].append(result.get("win_rate", 0) * 100)
            metrics["Profit Factor"].append(result.get("profit_factor", 0))
        
        # Create metrics comparison bar chart
        metrics_fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=list(metrics.keys()),
            vertical_spacing=0.05
        )
        
        row = 1
        for metric_name, metric_values in metrics.items():
            metrics_fig.add_trace(
                go.Bar(
                    x=labels,
                    y=metric_values,
                    name=metric_name
                ),
                row=row,
                col=1
            )
            row += 1
        
        metrics_fig.update_layout(
            title="Performance Metrics Comparison",
            height=200 * len(metrics),
            width=1000,
            showlegend=False
        )
        
        # Convert to JSON for dashboard
        return {
            "equity_plot": equity_fig.to_json(),
            "metrics_plot": metrics_fig.to_json(),
            "backtest_ids": backtest_ids,
            "raw_metrics": metrics
        }
    
    # -------------------------------------------------------------------------
    # ML Model Results
    # -------------------------------------------------------------------------
    
    def get_model_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a summary of available ML models.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of model summary dictionaries
        """
        model_list = self.learner.list_models()
        
        # Limit number of models
        model_list = model_list[:limit]
        
        # Get details for each model
        summaries = []
        for model_name in model_list:
            model, model_info = self.learner.load_model(model_name)
            
            if model is None or not model_info:
                continue
            
            # Extract key information
            summary = {
                "model_name": model_name,
                "model_type": model_info.get("model_type", "Unknown"),
                "is_classification": model_info.get("is_classification", True),
                "n_samples": model_info.get("n_samples", 0),
                "n_features": model_info.get("n_features", 0),
                "timestamp": model_info.get("timestamp"),
                "train_metrics": self._extract_key_metrics(model_info.get("train_metrics", {}), model_info.get("is_classification", True)),
                "val_metrics": self._extract_key_metrics(model_info.get("val_metrics", {}), model_info.get("is_classification", True))
            }
            
            summaries.append(summary)
        
        return summaries
    
    def _extract_key_metrics(self, metrics: Dict[str, Any], is_classification: bool) -> Dict[str, float]:
        """
        Extract key metrics from full metrics dictionary.
        
        Args:
            metrics: Full metrics dictionary
            is_classification: Whether classification or regression
            
        Returns:
            Dictionary with key metrics
        """
        if not metrics:
            return {}
        
        if is_classification:
            return {
                "accuracy": metrics.get("accuracy", 0),
                "precision": metrics.get("precision", 0),
                "recall": metrics.get("recall", 0),
                "f1": metrics.get("f1", 0),
                "auc": metrics.get("auc", 0)
            }
        else:
            return {
                "mse": metrics.get("mse", 0),
                "rmse": metrics.get("rmse", 0),
                "mae": metrics.get("mae", 0),
                "r2": metrics.get("r2", 0)
            }
    
    def get_model_detail(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific ML model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model details
        """
        model, model_info = self.learner.load_model(model_name)
        
        if model is None or not model_info:
            return {"error": f"Model {model_name} not found"}
        
        # Generate feature importance if possible
        feature_importance = {}
        try:
            if hasattr(model, 'feature_importances_') or hasattr(model, 'coef_'):
                feature_names = model_info.get("feature_names", [])
                if feature_names:
                    feature_importance = self.learner.feature_importance(model, feature_names)
        except Exception as e:
            logger.warning(f"Could not generate feature importance: {str(e)}")
        
        # Add feature importance to model info
        model_info["feature_importance"] = feature_importance
        
        return model_info
    
    def generate_feature_importance_chart(self, model_name: str, top_n: int = 10) -> Dict[str, Any]:
        """
        Generate a feature importance chart for a model.
        
        Args:
            model_name: Name of the model
            top_n: Number of top features to include
            
        Returns:
            Dictionary with plot data
        """
        model, model_info = self.learner.load_model(model_name)
        
        if model is None or not model_info:
            return {"error": f"Model {model_name} not found"}
        
        # Generate feature importance
        try:
            feature_names = model_info.get("feature_names", [])
            if not feature_names:
                return {"error": "Feature names not available for this model"}
            
            importance_dict = self.learner.feature_importance(model, feature_names, top_n)
            
            if not importance_dict:
                return {"error": "Feature importance not available for this model"}
            
            # Create plotly figure
            fig = go.Figure()
            
            # Sort by importance
            importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1]))
            
            # Create horizontal bar chart
            fig.add_trace(
                go.Bar(
                    y=list(importance_dict.keys()),
                    x=list(importance_dict.values()),
                    orientation="h",
                    marker_color="royalblue"
                )
            )
            
            # Update layout
            fig.update_layout(
                title=f"Feature Importance - {model_name} (Top {top_n})",
                xaxis_title="Importance",
                yaxis_title="Feature",
                height=max(400, 20 * len(importance_dict)),
                width=800
            )
            
            # Convert to JSON for dashboard
            return {
                "plotly_json": fig.to_json(),
                "model_name": model_name,
                "raw_importance": importance_dict
            }
            
        except Exception as e:
            logger.error(f"Error generating feature importance chart: {str(e)}")
            return {"error": f"Error generating feature importance chart: {str(e)}"}
    
    def generate_confusion_matrix(self, model_name: str) -> Dict[str, Any]:
        """
        Generate a confusion matrix visualization for a classification model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with plot data
        """
        model, model_info = self.learner.load_model(model_name)
        
        if model is None or not model_info:
            return {"error": f"Model {model_name} not found"}
        
        # Check if this is a classification model
        if not model_info.get("is_classification", True):
            return {"error": "Confusion matrix only available for classification models"}
        
        # Get confusion matrix from validation metrics
        val_metrics = model_info.get("val_metrics", {})
        if not val_metrics or "confusion_matrix" not in val_metrics:
            return {"error": "Confusion matrix data not available for this model"}
        
        confusion_matrix = val_metrics["confusion_matrix"]
        
        # Create plotly figure
        fig = go.Figure(data=go.Heatmap(
            z=confusion_matrix,
            x=["Predicted Negative", "Predicted Positive"],
            y=["Actual Negative", "Actual Positive"],
            colorscale="Blues",
            showscale=False
        ))
        
        # Add annotations
        for i in range(len(confusion_matrix)):
            for j in range(len(confusion_matrix[i])):
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=str(confusion_matrix[i][j]),
                    showarrow=False,
                    font=dict(color="white" if confusion_matrix[i][j] > 100 else "black")
                )
        
        # Update layout
        fig.update_layout(
            title=f"Confusion Matrix - {model_name}",
            xaxis_title="Predicted",
            yaxis_title="Actual",
            height=500,
            width=500
        )
        
        # Convert to JSON for dashboard
        return {
            "plotly_json": fig.to_json(),
            "model_name": model_name,
            "raw_matrix": confusion_matrix
        }
    
    def generate_model_metrics_chart(self, model_name: str) -> Dict[str, Any]:
        """
        Generate a visualization of model performance metrics.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with plot data
        """
        model, model_info = self.learner.load_model(model_name)
        
        if model is None or not model_info:
            return {"error": f"Model {model_name} not found"}
        
        # Get train and validation metrics
        train_metrics = model_info.get("train_metrics", {})
        val_metrics = model_info.get("val_metrics", {})
        
        if not train_metrics and not val_metrics:
            return {"error": "Performance metrics not available for this model"}
        
        # Extract metrics based on model type
        is_classification = model_info.get("is_classification", True)
        
        if is_classification:
            metric_names = ["accuracy", "precision", "recall", "f1"]
            if "auc" in train_metrics or "auc" in val_metrics:
                metric_names.append("auc")
        else:
            metric_names = ["mse", "rmse", "mae", "r2"]
        
        # Create values for training and validation
        train_values = [train_metrics.get(metric, 0) for metric in metric_names]
        val_values = [val_metrics.get(metric, 0) for metric in metric_names]
        
        # Create plotly figure
        fig = go.Figure()
        
        # Add traces for training and validation
        fig.add_trace(
            go.Bar(
                x=metric_names,
                y=train_values,
                name="Training"
            )
        )
        
        if val_metrics:
            fig.add_trace(
                go.Bar(
                    x=metric_names,
                    y=val_values,
                    name="Validation"
                )
            )
        
        # Update layout
        model_type = model_info.get("model_type", "Unknown")
        fig.update_layout(
            title=f"Performance Metrics - {model_name} ({model_type})",
            xaxis_title="Metric",
            yaxis_title="Value",
            height=500,
            width=800,
            barmode="group"
        )
        
        # Convert to JSON for dashboard
        return {
            "plotly_json": fig.to_json(),
            "model_name": model_name,
            "raw_metrics": {
                "train": train_metrics,
                "val": val_metrics
            }
        }
    
    def compare_models(self, model_names: List[str]) -> Dict[str, Any]:
        """
        Compare multiple ML models.
        
        Args:
            model_names: List of model names to compare
            
        Returns:
            Dictionary with comparison data and visualizations
        """
        if not model_names:
            return {"error": "No model names provided"}
        
        # Load model information
        models_info = {}
        for model_name in model_names:
            _, model_info = self.learner.load_model(model_name)
            if model_info:
                models_info[model_name] = model_info
        
        if not models_info:
            return {"error": "No valid model information found"}
        
        # Check if models are comparable (same task type)
        model_types = [info.get("is_classification", True) for info in models_info.values()]
        if len(set(model_types)) > 1:
            return {"error": "Cannot compare classification and regression models together"}
        
        is_classification = next(iter(models_info.values())).get("is_classification", True)
        
        # Determine metrics to compare
        if is_classification:
            metric_names = ["accuracy", "precision", "recall", "f1"]
            if any("auc" in info.get("val_metrics", {}) for info in models_info.values()):
                metric_names.append("auc")
        else:
            metric_names = ["mse", "rmse", "mae", "r2"]
        
        # Create data for comparison
        model_labels = []
        metrics_data = {metric: [] for metric in metric_names}
        
        for model_name, model_info in models_info.items():
            model_type = model_info.get("model_type", "Unknown")
            model_labels.append(f"{model_name} ({model_type})")
            
            # Use validation metrics if available, otherwise training metrics
            metrics = model_info.get("val_metrics", model_info.get("train_metrics", {}))
            
            for metric in metric_names:
                metrics_data[metric].append(metrics.get(metric, 0))
        
        # Create metrics comparison bar chart
        metrics_fig = make_subplots(
            rows=len(metric_names),
            cols=1,
            subplot_titles=metric_names,
            vertical_spacing=0.05
        )
        
        row = 1
        for metric_name, metric_values in metrics_data.items():
            metrics_fig.add_trace(
                go.Bar(
                    x=model_labels,
                    y=metric_values,
                    name=metric_name
                ),
                row=row,
                col=1
            )
            row += 1
        
        metrics_fig.update_layout(
            title="Model Performance Comparison",
            height=200 * len(metric_names),
            width=1000,
            showlegend=False
        )
        
        # Create radar chart for metrics if we have at least 3 metrics
        if len(metric_names) >= 3:
            radar_fig = go.Figure()
            
            for i, model_name in enumerate(model_names):
                model_info = models_info[model_name]
                model_type = model_info.get("model_type", "Unknown")
                metrics = model_info.get("val_metrics", model_info.get("train_metrics", {}))
                
                radar_fig.add_trace(
                    go.Scatterpolar(
                        r=[metrics.get(metric, 0) for metric in metric_names],
                        theta=metric_names,
                        fill="toself",
                        name=f"{model_name} ({model_type})"
                    )
                )
            
            radar_fig.update_layout(
                title="Model Performance Comparison",
                polar=dict(
                    radialaxis=dict(
                        visible=True
                    )
                ),
                height=600,
                width=600
            )
        else:
            radar_fig = None
        
        # Convert to JSON for dashboard
        result = {
            "metrics_plot": metrics_fig.to_json(),
            "model_names": model_names,
            "raw_metrics": metrics_data
        }
        
        if radar_fig:
            result["radar_plot"] = radar_fig.to_json()
        
        return result
    
    # -------------------------------------------------------------------------
    # Integrated Analytics
    # -------------------------------------------------------------------------
    
    def generate_backtest_model_analysis(self, backtest_id: str, model_name: str) -> Dict[str, Any]:
        """
        Generate analysis combining backtest and ML model results.
        
        Args:
            backtest_id: ID of the backtest
            model_name: Name of the model
            
        Returns:
            Dictionary with combined analysis data
        """
        # Get backtest result
        backtest_result = self.data_manager.get_backtest_result(backtest_id)
        
        if not backtest_result:
            return {"error": f"Backtest {backtest_id} not found"}
        
        # Get model information
        model, model_info = self.learner.load_model(model_name)
        
        if model is None or not model_info:
            return {"error": f"Model {model_name} not found"}
        
        # Check if model predictions exist in backtest result
        if "model_predictions" not in backtest_result:
            return {"error": "Model predictions not available in backtest result"}
        
        predictions = backtest_result["model_predictions"]
        
        # If predictions reference the model, check if they match
        if "model_name" in backtest_result and backtest_result["model_name"] != model_name:
            return {"error": f"Backtest used model {backtest_result['model_name']} but requested analysis for {model_name}"}
        
        # Create analysis visualizations
        
        # 1. Prediction vs. actual values
        if "actual_values" in backtest_result:
            actuals = backtest_result["actual_values"]
            
            pred_vs_actual_fig = go.Figure()
            
            pred_vs_actual_fig.add_trace(
                go.Scatter(
                    y=actuals,
                    mode="lines",
                    name="Actual",
                    line=dict(color="blue")
                )
            )
            
            pred_vs_actual_fig.add_trace(
                go.Scatter(
                    y=predictions,
                    mode="lines",
                    name="Predicted",
                    line=dict(color="red")
                )
            )
            
            pred_vs_actual_fig.update_layout(
                title=f"Prediction vs. Actual - {model_name}",
                xaxis_title="Time",
                yaxis_title="Value",
                height=500,
                width=1000
            )
        else:
            pred_vs_actual_fig = None
        
        # 2. Prediction distribution
        pred_dist_fig = go.Figure()
        
        pred_dist_fig.add_trace(
            go.Histogram(
                x=predictions,
                nbinsx=30,
                marker_color="purple"
            )
        )
        
        pred_dist_fig.update_layout(
            title=f"Prediction Distribution - {model_name}",
            xaxis_title="Prediction Value",
            yaxis_title="Frequency",
            height=400,
            width=800
        )
        
        # 3. Trade outcomes by prediction value
        if "trades" in backtest_result:
            trades = backtest_result["trades"]
            
            if isinstance(trades, list):
                trades = pd.DataFrame(trades)
            
            # Check if predictions are aligned with trades
            if len(predictions) == len(trades):
                trades["prediction"] = predictions
                
                # Create scatter plot of trade PnL vs. prediction
                trade_outcome_fig = go.Figure()
                
                trade_outcome_fig.add_trace(
                    go.Scatter(
                        x=trades["prediction"],
                        y=trades["pnl"],
                        mode="markers",
                        marker=dict(
                            color=trades["pnl"],
                            colorscale="RdBu",
                            cmin=-max(abs(trades["pnl"])),
                            cmax=max(abs(trades["pnl"])),
                            colorbar=dict(title="PnL")
                        )
                    )
                )
                
                trade_outcome_fig.update_layout(
                    title=f"Trade Outcomes by Prediction Value - {model_name}",
                    xaxis_title="Prediction Value",
                    yaxis_title="Trade PnL",
                    height=500,
                    width=800
                )
            else:
                trade_outcome_fig = None
        else:
            trade_outcome_fig = None
        
        # Combine results
        result = {
            "backtest_id": backtest_id,
            "model_name": model_name,
            "prediction_distribution": pred_dist_fig.to_json() if pred_dist_fig else None
        }
        
        if pred_vs_actual_fig:
            result["prediction_vs_actual"] = pred_vs_actual_fig.to_json()
        
        if trade_outcome_fig:
            result["trade_outcomes"] = trade_outcome_fig.to_json()
        
        return result 