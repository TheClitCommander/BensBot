#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot API - FastAPI application for the trading bot
providing UI and API endpoints for monitoring and control.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import auth modules
from trading_bot.auth.api import router as auth_router
from trading_bot.auth.service import AuthService

# Import typed settings
from trading_bot.config.typed_settings import APISettings, TradingBotSettings, load_config

# Initialize logging
logger = logging.getLogger("TradingBotAPI")

# Load typed settings if available
api_settings = None
try:
    config = load_config()
    api_settings = config.api
    logger.info("Loaded API settings from typed config")
except Exception as e:
    logger.warning(f"Could not load typed API settings: {str(e)}. Using defaults.")
    api_settings = APISettings()

# Initialize FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="API for monitoring and controlling the trading bot",
    version="1.0.0"
)

# Add CORS middleware with settings from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Reference to strategy rotator and continuous learner
# These will be set when the app is started
_strategy_rotator = None
_continuous_learner = None

# API Models
class StrategyInfo(BaseModel):
    name: str
    enabled: bool
    average_performance: float
    current_weight: float
    last_signal: Optional[float] = None

class StrategyUpdate(BaseModel):
    enabled: Optional[bool] = None
    weight: Optional[float] = None

class PerformanceReport(BaseModel):
    timestamp: str
    overall_performance: float
    strategies: Dict[str, Any]

class MarketData(BaseModel):
    prices: List[float]
    volume: Optional[List[float]] = None
    additional_data: Optional[Dict[str, Any]] = None

class TrainingRequest(BaseModel):
    strategy_names: List[str]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {"message": "Trading Bot API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if _strategy_rotator is None:
        return {"status": "degraded", "message": "Strategy rotator not initialized"}
    
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Protected endpoints
@app.get("/strategies", response_model=List[StrategyInfo])
async def get_strategies(current_user = Depends(AuthService.get_current_active_user)):
    """Get all available strategies and their current status."""
    if _strategy_rotator is None:
        raise HTTPException(status_code=503, detail="Strategy rotator not initialized")
    
    strategies = []
    weights = _strategy_rotator.get_strategy_weights()
    
    for strategy in _strategy_rotator.strategies:
        avg_perf = strategy.get_average_performance()
        
        strategies.append({
            "name": strategy.name,
            "enabled": strategy.enabled,
            "average_performance": avg_perf,
            "current_weight": weights.get(strategy.name, 0.0),
            "last_signal": strategy.last_signal
        })
    
    return strategies

@app.get("/strategies/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str, current_user = Depends(AuthService.get_current_active_user)):
    """Get information about a specific strategy."""
    if _strategy_rotator is None:
        raise HTTPException(status_code=503, detail="Strategy rotator not initialized")
    
    if strategy_name not in _strategy_rotator.strategies_by_name:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
    
    strategy = _strategy_rotator.strategies_by_name[strategy_name]
    weights = _strategy_rotator.get_strategy_weights()
    
    return {
        "name": strategy.name,
        "enabled": strategy.enabled,
        "average_performance": strategy.get_average_performance(),
        "current_weight": weights.get(strategy.name, 0.0),
        "last_signal": strategy.last_signal
    }

@app.put("/strategies/{strategy_name}", response_model=StrategyInfo)
async def update_strategy(strategy_name: str, update: StrategyUpdate, current_user = Depends(AuthService.get_current_active_user)):
    """Update a strategy's configuration."""
    if _strategy_rotator is None:
        raise HTTPException(status_code=503, detail="Strategy rotator not initialized")
    
    if strategy_name not in _strategy_rotator.strategies_by_name:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
    
    strategy = _strategy_rotator.strategies_by_name[strategy_name]
    weights = _strategy_rotator.get_strategy_weights()
    
    # Update enabled status if provided
    if update.enabled is not None:
        strategy.enabled = update.enabled
    
    # Update weight if provided
    if update.weight is not None:
        # Ensure weight is valid
        if update.weight < 0 or update.weight > 1:
            raise HTTPException(
                status_code=400, 
                detail="Weight must be between 0 and 1"
            )
        
        # Update weight
        _strategy_rotator.strategy_weights[strategy_name] = update.weight
        
        # Normalize weights
        _strategy_rotator._normalize_weights()
        
        # Get updated weights
        weights = _strategy_rotator.get_strategy_weights()
    
    # Save state
    _strategy_rotator.save_state()
    
    return {
        "name": strategy.name,
        "enabled": strategy.enabled,
        "average_performance": strategy.get_average_performance(),
        "current_weight": weights.get(strategy.name, 0.0),
        "last_signal": strategy.last_signal
    }

@app.get("/performance", response_model=PerformanceReport)
async def get_performance(current_user = Depends(AuthService.get_current_active_user)):
    """Get performance report for all strategies."""
    if _continuous_learner is None:
        raise HTTPException(status_code=503, detail="Continuous learner not initialized")
    
    return _continuous_learner.get_performance_report()

@app.post("/generate_signal")
async def generate_signal(market_data: MarketData, current_user = Depends(AuthService.get_current_active_user)):
    """Generate a trading signal from current market data."""
    if _strategy_rotator is None:
        raise HTTPException(status_code=503, detail="Strategy rotator not initialized")
    
    # Convert market data to expected format
    data_dict = {
        "prices": market_data.prices
    }
    
    if market_data.volume:
        data_dict["volume"] = market_data.volume
    
    if market_data.additional_data:
        data_dict.update(market_data.additional_data)
    
    try:
        # Generate signals
        signals = _strategy_rotator.generate_signals(data_dict)
        combined_signal = _strategy_rotator.get_combined_signal()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "signals": signals,
            "combined_signal": combined_signal
        }
    except Exception as e:
        logger.error(f"Error generating signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")

@app.post("/train", status_code=202)
async def train_strategies(request: TrainingRequest, background_tasks: BackgroundTasks, current_user = Depends(AuthService.get_current_active_user)):
    """Trigger training for specific strategies."""
    if _continuous_learner is None:
        raise HTTPException(status_code=503, detail="Continuous learner not initialized")
    
    if not request.strategy_names:
        raise HTTPException(status_code=400, detail="No strategy names provided")
    
    # Schedule training in background
    background_tasks.add_task(
        _continuous_learner.manually_trigger_retraining,
        request.strategy_names
    )
    
    return {
        "message": f"Training scheduled for {len(request.strategy_names)} strategies",
        "strategies": request.strategy_names
    }

@app.get("/market_regime")
async def get_market_regime(current_user = Depends(AuthService.get_current_active_user)):
    """Get current market regime."""
    if _strategy_rotator is None:
        raise HTTPException(status_code=503, detail="Strategy rotator not initialized")
    
    return {
        "current_regime": _strategy_rotator.current_regime.name,
        "timestamp": datetime.now().isoformat()
    }

# Dashboard API Endpoints

@app.get("/api/portfolio")
async def get_portfolio(account: str = "live"):
    """Get portfolio data for the dashboard."""
    try:
        # In a real implementation, this would pull data from your portfolio manager
        # For now, we'll create simulated data that matches the dashboard's expectations
        current_date = datetime.now()
        
        # Create simulated portfolio data
        portfolio_data = {
            "account_type": account,
            "total_value": 124573.82,
            "cash": 34125.61,
            "invested": 90448.21,
            "day_change_pct": 1.23,
            "day_change_value": 1512.34,
            "total_return_pct": 24.57,
            "total_return_value": 24573.82,
            "allocation": {
                "Technology": 35.2,
                "Healthcare": 18.7,
                "Financials": 15.3,
                "Consumer Discretionary": 12.5,
                "Industrials": 9.8,
                "Energy": 5.1,
                "Materials": 3.4
            },
            "metrics": {
                "sharpe": 1.87,
                "max_drawdown": -12.3,
                "volatility": 14.2,
                "beta": 0.92
            },
            "updated_at": current_date.isoformat()
        }
        
        return portfolio_data
    except Exception as e:
        logger.error(f"Error fetching portfolio data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio data: {str(e)}")

@app.get("/api/trades")
async def get_trades(account: str = "live", limit: int = 20):
    """Get recent trades for the dashboard."""
    try:
        # In a real implementation, this would pull data from your trade manager
        # For now, we'll create simulated data that matches the dashboard's expectations
        
        # Create sample trade data
        trade_types = ["BUY", "SELL"]
        statuses = ["FILLED", "PARTIAL_FILL", "PENDING"]
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
        strategies = ["Momentum Growth", "Adaptive Trend-Following", "Volatility Breakout Pro"]
        
        trades = []
        for i in range(min(limit, 20)):
            execution_time = datetime.now() - timedelta(days=i//3, hours=i%24, minutes=(i*7)%60)
            trade_type = trade_types[i % len(trade_types)]
            symbol = symbols[i % len(symbols)]
            price = round(100 + (i * 3.5) % 200, 2)
            quantity = round((i + 1) * 5.1)
            status = statuses[i % len(statuses)]
            strategy = strategies[i % len(strategies)]
            
            trades.append({
                "id": f"trade-{i+1000}",
                "symbol": symbol,
                "type": trade_type,
                "price": price,
                "quantity": quantity,
                "value": round(price * quantity, 2),
                "status": status,
                "execution_time": execution_time.isoformat(),
                "strategy": strategy,
                "account": account
            })
        
        return trades
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching trades: {str(e)}")

@app.get("/api/alerts")
async def get_alerts(limit: int = 20):
    """Get system alerts and notifications."""
    try:
        # In a real implementation, this would pull data from your notification manager
        # For now, we'll create simulated data that matches the dashboard's expectations
        
        # Create sample alert data
        alert_types = ["INFO", "WARNING", "ERROR", "SUCCESS"]
        sources = ["SYSTEM", "STRATEGY", "MARKET", "ORDER", "PORTFOLIO"]
        messages = [
            "Market volatility exceeding threshold",
            "Strategy signal generated for AAPL",
            "Order successfully executed",
            "Portfolio rebalance recommended",
            "API connection restored",
            "New trading opportunity detected",
            "Risk limits approaching threshold",
            "Backtest completed successfully",
            "System update available",
            "Performance metrics updated"
        ]
        
        alerts = []
        for i in range(min(limit, 20)):
            created_at = datetime.now() - timedelta(hours=i, minutes=(i*11)%60)
            alert_type = alert_types[i % len(alert_types)]
            source = sources[i % len(sources)]
            message = messages[i % len(messages)]
            
            alerts.append({
                "id": f"alert-{i+1000}",
                "type": alert_type,
                "source": source,
                "message": message,
                "created_at": created_at.isoformat(),
                "is_read": i < 3,  # First few are unread
                "related_entity": {} if i % 3 == 0 else {"type": "strategy", "id": f"strat-{i+100}"}
            })
        
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@app.get("/api/system_logs")
async def get_system_logs(limit: int = 50):
    """Get system log entries."""
    try:
        # In a real implementation, this would pull data from your logging system
        # For now, we'll create simulated data that matches the dashboard's expectations
        
        # Create sample log entries
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        components = ["SYSTEM", "API", "STRATEGIES", "DATA", "EXECUTOR", "EVENT_BUS"]
        messages = [
            "System startup complete",
            "Processing market data update",
            "Strategy manager initialized",
            "New data source connected",
            "Order execution completed",
            "Event bus processing message",
            "Configuration loaded",
            "Scheduler task completed",
            "Portfolio valuation updated",
            "Market hours check"
        ]
        
        logs = []
        for i in range(min(limit, 50)):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            log_level = log_levels[i % len(log_levels)]
            component = components[i % len(components)]
            message = f"{messages[i % len(messages)]} ({i+1})"
            
            logs.append({
                "timestamp": timestamp.isoformat(),
                "level": log_level,
                "component": component,
                "message": message
            })
        
        return logs
    except Exception as e:
        logger.error(f"Error fetching system logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching system logs: {str(e)}")

@app.get("/api/event_bus")
async def get_event_bus_status():
    """Get the status of the event bus system."""
    try:
        # In a real implementation, this would pull data from your event system
        # For now, we'll create simulated data that matches the dashboard's expectations
        
        # Create sample event bus status
        queues = {
            "market_data": {
                "size": 12,
                "processed_total": 1458,
                "consumers": 3
            },
            "signals": {
                "size": 8,
                "processed_total": 892,
                "consumers": 2
            },
            "orders": {
                "size": 5,
                "processed_total": 723,
                "consumers": 4
            },
            "notifications": {
                "size": 15,
                "processed_total": 2145,
                "consumers": 2
            }
        }
        
        channels = [
            {
                "name": "market_updates",
                "subscribers": 5,
                "messages_per_second": 3.2,
                "status": "active"
            },
            {
                "name": "strategy_signals",
                "subscribers": 3,
                "messages_per_second": 1.5,
                "status": "active"
            },
            {
                "name": "order_execution",
                "subscribers": 2,
                "messages_per_second": 0.8,
                "status": "active"
            }
        ]
        
        return {
            "status": "healthy",
            "active_connections": 12,
            "uptime_seconds": 7825,
            "queues": queues,
            "channels": channels,
            "metrics": {
                "messages_per_second": 5.5,
                "average_latency_ms": 12.3,
                "peak_queue_size": 24
            }
        }
    except Exception as e:
        logger.error(f"Error fetching event bus status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching event bus status: {str(e)}")

@app.get("/api/strategies")
async def get_strategies(status: str = None):
    """Get trading strategies filtered by status."""
    try:
        # Create realistic strategy data that matches what the dashboard expects
        # This would normally come from your strategy manager
        
        # Strategy types and their associated symbols
        strategy_data = {
            "active": [
                {
                    "id": "strat-101",
                    "name": "Momentum Growth (AAPL/MSFT/AMZN)",
                    "description": "Active momentum strategy targeting high-growth tech stocks with dynamic position sizing. Utilizing RSI and MACD crossovers with volume confirmation for entry/exit signals. Currently performing well in volatile market conditions.",
                    "type": "momentum",
                    "win_rate": 72.5,
                    "profit_factor": 2.1,
                    "sharpe": 1.8,
                    "trades": 142,
                    "symbols": ["AAPL", "MSFT", "AMZN"],
                    "status": "active",
                    "date_added": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "entry_rsi": 35.0,
                        "exit_rsi": 70.0,
                        "fast_ema": 12,
                        "slow_ema": 26,
                        "stop_loss_pct": 2.5,
                        "take_profit_pct": 5.0,
                        "trailing_stop_pct": 1.5
                    }
                },
                {
                    "id": "strat-102",
                    "name": "Adaptive Trend-Following (SPY/QQQ)",
                    "description": "Multi-timeframe trend following system with adaptive parameter optimization. Employs EMA crossovers on daily and 4-hour charts with trailing stops. Showing consistent returns across market regimes.",
                    "type": "trend",
                    "win_rate": 68.2,
                    "profit_factor": 2.3,
                    "sharpe": 1.65,
                    "trades": 82,
                    "symbols": ["SPY", "QQQ"],
                    "status": "active",
                    "date_added": (datetime.now() - timedelta(days=62)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "fast_period": 8,
                        "slow_period": 21,
                        "signal_period": 9,
                        "stop_loss_pct": 3.0,
                        "take_profit_pct": 6.0
                    }
                },
                {
                    "id": "strat-103",
                    "name": "Volatility Breakout Pro (NVDA/AMD)",
                    "description": "Volatility-based breakout strategy with ATR-based position sizing and stop placement. Uses volume profile analysis for accurate entry timing. Effective in capturing sudden price movements.",
                    "type": "breakout",
                    "win_rate": 67.8,
                    "profit_factor": 1.95,
                    "sharpe": 1.72,
                    "trades": 98,
                    "symbols": ["NVDA", "AMD"],
                    "status": "active",
                    "date_added": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "atr_period": 14,
                        "breakout_periods": 20,
                        "volume_threshold": 1.5,
                        "stop_loss_atr": 2.0,
                        "take_profit_atr": 3.5
                    }
                }
            ],
            "pending_win": [
                {
                    "id": "strat-201",
                    "name": "Quantum Mean Reversion (JPM/BAC/GS)",
                    "description": "Statistical mean reversion system utilizing Bollinger Bands, RSI, and Keltner Channels with machine learning-enhanced entry signals. Exceptional backtest results across multiple market conditions with minimal drawdowns. Pending final verification in live trading.",
                    "type": "mean_reversion",
                    "win_rate": 85.2,
                    "profit_factor": 2.85,
                    "sharpe": 2.25,
                    "trades": 74,
                    "symbols": ["JPM", "BAC", "GS"],
                    "status": "pending_win",
                    "date_added": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "bb_period": 20,
                        "bb_std": 2.0,
                        "rsi_period": 14,
                        "rsi_oversold": 30,
                        "rsi_overbought": 70,
                        "kc_period": 20,
                        "kc_mult": 1.5
                    }
                },
                {
                    "id": "strat-202",
                    "name": "Advanced Swing System (JNJ/PFE/ABBV)",
                    "description": "Multi-day swing trading strategy combining technical and sentiment analysis. Uses proprietary scoring system for timing entries at optimal risk/reward levels. Currently completing final validation phase with outstanding results.",
                    "type": "swing",
                    "win_rate": 81.7,
                    "profit_factor": 2.62,
                    "sharpe": 2.1,
                    "trades": 52,
                    "symbols": ["JNJ", "PFE", "ABBV"],
                    "status": "pending_win",
                    "date_added": (datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "lookback_days": 5,
                        "vwap_deviation": 2.5,
                        "min_risk_reward": 2.0,
                        "max_hold_days": 10,
                        "min_sentiment_score": 65
                    }
                }
            ],
            "experimental": [
                {
                    "id": "strat-301",
                    "name": "AI-Enhanced Sector Rotation (XLK/XLF/XLE/XLV)",
                    "description": "Experimental sector rotation strategy using machine learning to predict sector performance based on macroeconomic indicators. Incorporates Federal Reserve data, yield curve analysis, and sector relative strength. Currently in early testing phase with promising initial results.",
                    "type": "sector_rotation",
                    "win_rate": 68.4,
                    "profit_factor": 1.75,
                    "sharpe": 1.4,
                    "trades": 28,
                    "symbols": ["XLK", "XLF", "XLE", "XLV"],
                    "status": "experimental",
                    "date_added": (datetime.now() - timedelta(days=9)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "lookback_periods": 12,
                        "rotation_frequency": 10,
                        "min_rs_rank": 70,
                        "max_sectors": 2,
                        "min_sector_momentum": 0.5
                    }
                },
                {
                    "id": "strat-302",
                    "name": "NLP News Sentiment Analyzer (AMZN/GOOGL/META)",
                    "description": "Advanced news sentiment analysis system using transformers-based NLP models to extract market-moving signals from financial news. Processes over 1,000 sources in real-time with custom sentiment classification. Early validation shows correlation with short-term price movements.",
                    "type": "sentiment",
                    "win_rate": 64.2,
                    "profit_factor": 1.45,
                    "sharpe": 1.2,
                    "trades": 36,
                    "symbols": ["AMZN", "GOOGL", "META"],
                    "status": "experimental",
                    "date_added": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "sentiment_threshold": 0.65,
                        "confidence_min": 0.8,
                        "news_lookback_hours": 24,
                        "position_hold_time": 2,
                        "max_position_count": 3
                    }
                }
            ],
            "failed": [
                {
                    "id": "strat-401",
                    "name": "High Frequency Signal Capture (SPY/QQQ/TQQQ)",
                    "description": "High frequency trading strategy targeting microstructure inefficiencies. Failed due to unresolvable latency issues and insufficient infrastructure for consistent execution. Post-mortem analysis revealed declining alpha factor after transaction costs even with optimized execution.",
                    "type": "hft",
                    "win_rate": 48.2,
                    "profit_factor": 0.85,
                    "sharpe": 0.45,
                    "trades": 312,
                    "symbols": ["SPY", "QQQ", "TQQQ"],
                    "status": "failed",
                    "date_added": (datetime.now() - timedelta(days=32)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "signal_threshold": 0.5,
                        "exec_timeout_ms": 10,
                        "min_edge_bps": 5,
                        "max_slippage_bps": 2,
                        "max_spread_bps": 3
                    }
                },
                {
                    "id": "strat-402",
                    "name": "Deep Pattern Recognition (TSLA/RIVN/LCID)",
                    "description": "Neural network-based pattern recognition system for identifying chart patterns. Failed validation due to overfitting on historical data and inability to adapt to changing market conditions. Additional training data did not improve performance metrics.",
                    "type": "pattern",
                    "win_rate": 41.5,
                    "profit_factor": 0.76,
                    "sharpe": 0.3,
                    "trades": 88,
                    "symbols": ["TSLA", "RIVN", "LCID"],
                    "status": "failed",
                    "date_added": (datetime.now() - timedelta(days=24)).strftime("%Y-%m-%d"),
                    "backtest_complete": True,
                    "parameters": {
                        "detection_confidence": 0.75,
                        "pattern_lookback": 120,
                        "prediction_horizon": 5,
                        "min_pattern_quality": 0.65,
                        "max_correlation": 0.85
                    }
                }
            ]
        }
        
        # If status is provided, filter the strategies
        if status and status in strategy_data:
            return strategy_data[status]
        elif status == "template":
            # Return template strategies
            return [
                {
                    "id": "template-101",
                    "name": "Momentum Template",
                    "description": "Configurable momentum strategy template ready for customization",
                    "type": "momentum",
                    "status": "template",
                    "parameters": {
                        "entry_rsi": 30.0,
                        "exit_rsi": 70.0,
                        "fast_ema": 12,
                        "slow_ema": 26,
                        "stop_loss_pct": 2.0,
                        "take_profit_pct": 4.0
                    }
                },
                {
                    "id": "template-102",
                    "name": "Mean Reversion Template",
                    "description": "Configurable mean reversion strategy template",
                    "type": "mean_reversion",
                    "status": "template",
                    "parameters": {
                        "bb_period": 20,
                        "bb_std": 2.0,
                        "rsi_period": 14,
                        "rsi_oversold": 30,
                        "rsi_overbought": 70
                    }
                }
            ]
        
        # If no status or invalid status, return all strategies
        all_strategies = []
        for strategies in strategy_data.values():
            all_strategies.extend(strategies)
        return all_strategies
        
    except Exception as e:
        logger.error(f"Error fetching strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching strategies: {str(e)}")

@app.get("/api/news")
async def get_news(symbol: str = None, category: str = None, limit: int = 20):
    """Get financial news, optionally filtered by symbol or category."""
    try:
        # Create realistic financial news data that matches what the dashboard expects
        # In a real implementation, this would come from NewsData.io, Alpha Vantage, etc.
        
        # Base news data with professional formatting for high-impact market news
        general_market_news = [
            {
                "id": "news-001",
                "title": "Federal Reserve Signals Shift in Policy Stance",
                "description": "The Federal Reserve indicated a potential pivot in monetary policy during its latest meeting, suggesting rate cuts may come sooner than markets anticipated if inflation continues to moderate.",
                "content": "In a significant shift from previous communications, Federal Reserve Chair Jerome Powell outlined conditions under which the central bank could begin easing monetary policy. The Fed's latest minutes revealed growing consensus among board members that economic conditions may soon warrant a more accommodative stance, particularly if labor market conditions deteriorate while inflation continues its downward trend. Several FOMC members emphasized the risks of maintaining restrictive policy for too long, marking a notable change in tone from earlier meetings.",
                "source": "Alpha Vantage",
                "source_url": "https://www.alphaadvantage.co",
                "image_url": "https://static.seekingalpha.com/cdn/s3/uploads/getty_images/1399341513/image_1399341513.jpg",
                "published_at": (datetime.now() - timedelta(hours=3, minutes=15)).isoformat(),
                "category": "economic",
                "sentiment": "positive",
                "impact": "high",
                "symbols": ["SPY", "QQQ", "TLT", "GLD"],
                "portfolio_impact": "Positive for growth stocks and bonds, suggesting potential appreciation for tech-heavy portfolios. Consider increasing duration in fixed income holdings.",
                "action_plan": "Monitor yield curve for steepening. Consider allocation shift from value to growth sectors. Review bond duration strategy."
            },
            {
                "id": "news-002",
                "title": "U.S. GDP Growth Exceeds Expectations in Latest Quarter",
                "description": "The U.S. economy expanded at a 3.3% annualized rate last quarter, significantly outpacing consensus estimates of 2.5% growth, driven by robust consumer spending and business investment.",
                "content": "The Commerce Department reported that U.S. economic growth accelerated to a 3.3% annual rate in the latest quarter, substantially beating economists' projections of 2.5%. The stronger-than-expected performance was primarily fueled by resilient consumer spending, which increased 3.1%, and business investment, which rose 4.7%. Notably, the report showed broad-based growth across sectors, with particularly strong contributions from services and technology. The robust GDP print suggests the economy continues to show remarkable resilience despite elevated interest rates and earlier recession concerns.",
                "source": "NewsData.io",
                "source_url": "https://newsdata.io",
                "image_url": "https://www.investing.com/news/stock-market-news/wall-st-ends-lower-after-strong-gdp-data-dents-early-rate-cut-hopes-93CH-3282090-image",
                "published_at": (datetime.now() - timedelta(hours=6, minutes=42)).isoformat(),
                "category": "economic",
                "sentiment": "positive",
                "impact": "high",
                "symbols": ["SPY", "DIA", "XLY", "XLF"],
                "portfolio_impact": "Positive for cyclical sectors and consumer discretionary. May delay rate cuts, creating headwinds for high-duration assets.",
                "action_plan": "Consider increasing allocation to consumer discretionary and financials. Maintain quality focus in equity selections."
            },
            {
                "id": "news-003",
                "title": "Inflation Data Shows Unexpected Acceleration",
                "description": "Latest CPI readings came in above consensus, with core inflation rising 0.4% month-over-month, potentially complicating the Federal Reserve's policy path.",
                "content": "The Bureau of Labor Statistics reported that the Consumer Price Index increased 0.4% in the latest month, exceeding economists' forecasts of a 0.2% rise. On an annual basis, inflation stands at o3.8%, higher than the 3.5% rate predicted. Core inflation, which excludes volatile food and energy components, also accelerated more than anticipated, rising 0.4% for the month. The unexpected uptick was driven primarily by shelter costs and service inflation, which continued to show stickiness despite the Fed's restrictive policy stance. The report has prompted a reassessment of interest rate expectations, with markets now pricing in fewer rate cuts this year.",
                "source": "Marketaux",
                "source_url": "https://www.marketaux.com",
                "image_url": "https://www.reuters.com/resizer/fVVKJJxNuN9Q9ehPJeqp8x7QoNE=/1920x1005/smart/filters:quality(80)/cloudfront-us-east-2.images.arcpublishing.com/reuters/RO6RSM4J6NLMRN3BDLMGR2IZZA.jpg",
                "published_at": (datetime.now() - timedelta(hours=8, minutes=17)).isoformat(),
                "category": "economic",
                "sentiment": "negative",
                "impact": "high",
                "symbols": ["TLT", "IEF", "TIPS", "GLD"],
                "portfolio_impact": "Negative for fixed income and rate-sensitive equities. May support value over growth in the near term.",
                "action_plan": "Review duration exposure in fixed income. Consider inflation-protected securities. Evaluate growth stock allocations."
            },
            {
                "id": "news-004",
                "title": "Apple Announces Major AI Integration Across Product Line",
                "description": "Apple unveiled its comprehensive AI strategy, integrating advanced AI capabilities across its ecosystem, potentially challenging competitors in the rapidly evolving AI landscape.",
                "content": "During a special event, Apple CEO Tim Cook revealed the company's ambitious AI roadmap, announcing the integration of advanced machine learning capabilities across the entire product lineup. The initiative, dubbed 'Apple Intelligence,' will enhance Siri's capabilities, enable sophisticated on-device processing, and introduce generative AI features to productivity apps. The company emphasized its privacy-first approach, with most processing occurring on-device rather than in the cloud. Wall Street analysts reacted positively, with several firms upgrading their price targets, citing Apple's potential to monetize AI features across its vast installed base of devices.",
                "source": "GNews",
                "source_url": "https://news.google.com",
                "image_url": "https://images.barrons.com/im-219938/social",
                "published_at": (datetime.now() - timedelta(hours=12, minutes=36)).isoformat(),
                "category": "company",
                "sentiment": "positive",
                "impact": "medium",
                "symbols": ["AAPL", "MSFT", "GOOGL", "NVDA"],
                "portfolio_impact": "Positive for Apple and could accelerate the AI arms race among major tech companies. Potential positive spillover for AI chip providers.",
                "action_plan": "Evaluate Apple position relative to portfolio allocation limits. Consider semiconductor exposure for indirect benefits."
            },
            {
                "id": "news-005",
                "title": "Tesla Exceeds Delivery Expectations Despite EV Market Challenges",
                "description": "Tesla reported quarterly deliveries of 466,000 vehicles, surpassing analysts' estimates of 445,000, defying broader weakness in electric vehicle demand.",
                "content": "Tesla announced it delivered 466,000 vehicles in the last quarter, convincingly beating Wall Street's consensus estimate of 445,000 vehicles. The stronger-than-expected results come despite growing concerns about slowing electric vehicle demand globally and increasing competition from legacy automakers and Chinese manufacturers. The company attributed the outperformance to successful price adjustments and strong demand for the refreshed Model 3. CEO Elon Musk noted during the earnings call that the company remains on track to begin production of its lower-priced vehicle platform by early next year, which analysts view as crucial for maintaining growth as the premium EV market becomes increasingly saturated.",
                "source": "Alpha Vantage",
                "source_url": "https://www.alphaadvantage.co",
                "image_url": "https://assets.bwbx.io/images/users/iqjWHBFdfxIU/iOgf3lExe7_8/v1/1200x800.jpg",
                "published_at": (datetime.now() - timedelta(hours=15, minutes=8)).isoformat(),
                "category": "company",
                "sentiment": "positive",
                "impact": "medium",
                "symbols": ["TSLA", "RIVN", "NIO", "LCID"],
                "portfolio_impact": "Positive for Tesla but raises questions about broader EV sector health. Consider implications for battery supply chain.",
                "action_plan": "Reevaluate EV exposure beyond Tesla. Monitor battery material suppliers for potential impact."
            }
        ]
        
        # Tech stock specific news
        tech_news = [
            {
                "id": "news-101",
                "title": "Microsoft Cloud Revenue Surges as AI Investments Begin to Pay Off",
                "description": "Microsoft reported cloud revenue growth of 31%, exceeding analyst expectations, driven by accelerating enterprise adoption of AI services on Azure.",
                "content": "Microsoft reported exceptional performance in its cloud business, with Azure revenue growing 31% year-over-year, significantly above the 27% consensus estimate. The company attributed the acceleration to increasing enterprise adoption of its AI services, with more than 60% of the Fortune 500 now using Azure OpenAI Service. During the earnings call, CEO Satya Nadella highlighted that AI-related services contributed approximately 8 percentage points to Azure's growth, up from 6 points in the previous quarter. CFO Amy Hood provided strong forward guidance, projecting continued momentum in the cloud segment as customers move from experimentation to production deployment of AI applications.",
                "source": "MediaStack",
                "source_url": "https://mediastack.com",
                "image_url": "https://media.wired.com/photos/5f74bdd7dc2ce1a58a3e54c9/master/pass/business_microsoft_1162211568.jpg",
                "published_at": (datetime.now() - timedelta(hours=4, minutes=23)).isoformat(),
                "category": "company",
                "sentiment": "positive",
                "impact": "medium",
                "symbols": ["MSFT", "AMZN", "GOOGL", "CRM"],
                "portfolio_impact": "Positive for cloud providers with strong AI capabilities. Validates investment thesis for enterprise AI adoption.",
                "action_plan": "Review cloud exposure across portfolio. Consider increasing allocation to leading cloud providers with proven AI monetization."
            },
            {
                "id": "news-102",
                "title": "Nvidia Faces Supply Constraints as AI Chip Demand Continues to Outpace Production",
                "description": "Nvidia is struggling to meet demand for its advanced AI accelerators, with lead times extending to 6+ months for some high-end data center products.",
                "content": "Nvidia is facing significant challenges in meeting the unprecedented demand for its AI accelerators, with customers reporting extended lead times of six months or more for certain high-end data center products. The supply constraints center particularly on the company's H100 and upcoming H200 chips, which have become the gold standard for training and running large language models. During an industry conference, CEO Jensen Huang acknowledged the supply challenges but emphasized that production capacity is being ramped up aggressively with manufacturing partners. Several cloud service providers have warned that the chip shortage could impact their ability to expand AI services in the near term, potentially slowing the broader adoption of generative AI technologies.",
                "source": "NYTimes",
                "source_url": "https://www.nytimes.com",
                "image_url": "https://static01.nyt.com/images/2023/06/16/business/16nvidia-print/16nvidia-superJumbo.jpg",
                "published_at": (datetime.now() - timedelta(hours=9, minutes=41)).isoformat(),
                "category": "company",
                "sentiment": "mixed",
                "impact": "medium",
                "symbols": ["NVDA", "AMD", "INTC", "TSM"],
                "portfolio_impact": "Mixed - positive demand signal but potential for revenue timing impact. Broader implications for AI infrastructure deployment timelines.",
                "action_plan": "Monitor order backlog metrics in upcoming earnings. Evaluate semiconductor equipment manufacturers as alternative exposure."
            },
            {
                "id": "news-103",
                "title": "Google's Gemini AI Shows Impressive Results Against OpenAI's GPT-4",
                "description": "Google's latest AI model, Gemini, demonstrated superior performance in complex reasoning and coding tasks compared to OpenAI's GPT-4 in independent benchmarks.",
                "content": "Google's newest large language model, Gemini Ultra, has outperformed OpenAI's GPT-4 across several key benchmarks, according to independent testing by Stanford's AI Index. The model showed particularly strong results in multi-step reasoning, code generation, and scientific problem-solving tasks, scoring 10-15% higher than GPT-4 on these metrics. Google DeepMind CEO Demis Hassabis attributed the improvements to the model's multimodal training approach and enhanced context window. Industry analysts suggest that Google's advances could potentially shift the competitive landscape in generative AI, which has been dominated by OpenAI and Microsoft over the past year. The company announced that Gemini is being integrated into Google Search, Workspace, and Cloud products with immediate effect.",
                "source": "Currents",
                "source_url": "https://currents.google.com",
                "image_url": "https://storage.googleapis.com/gweb-uniblog-publish-prod/images/gemini_1.width-1300.format-webp.webp",
                "published_at": (datetime.now() - timedelta(hours=18, minutes=12)).isoformat(),
                "category": "company",
                "sentiment": "positive",
                "impact": "medium",
                "symbols": ["GOOGL", "MSFT", "META", "AMZN"],
                "portfolio_impact": "Positive for Google as it suggests potential to reclaim leadership in AI. May indicate more competitive AI landscape than previously assumed.",
                "action_plan": "Reassess competitive positioning in AI among major tech holdings. Monitor Google Cloud growth metrics for evidence of AI-driven acceleration."
            }
        ]
        
        # Financial sector news
        financial_news = [
            {
                "id": "news-201",
                "title": "JPMorgan Reports Record Quarterly Profit Amid Trading Boom",
                "description": "JPMorgan Chase announced record quarterly earnings, with profits rising 18% year-over-year, driven by strong trading revenue and expanded net interest margins.",
                "content": "JPMorgan Chase reported a record quarterly profit of $13.4 billion, representing an 18% increase from the same period last year and comfortably exceeding analyst estimates. The outperformance was largely driven by a 23% surge in trading revenue, particularly in fixed income and commodities, as well as resilient net interest income despite the flattening yield curve. CEO Jamie Dimon struck an optimistic tone on the economic outlook, noting that consumer spending remains robust across income segments, with credit card volumes up 9% year-over-year. However, he cautioned about geopolitical risks and the potential for unexpected inflation persistence, while indicating the bank continues to maintain elevated loan loss reserves as a precautionary measure.",
                "source": "Alpha Vantage",
                "source_url": "https://www.alphaadvantage.co",
                "image_url": "https://image.cnbcfm.com/api/v1/image/107054951-1651256946696-gettyimages-1240069631-AFP_329H8WP.jpeg",
                "published_at": (datetime.now() - timedelta(hours=7, minutes=19)).isoformat(),
                "category": "company",
                "sentiment": "positive",
                "impact": "medium",
                "symbols": ["JPM", "GS", "MS", "BAC"],
                "portfolio_impact": "Positive for banking sector, especially institutions with strong trading operations. Signals continued economic resilience.",
                "action_plan": "Consider increasing allocation to financial sector. Focus on banks with diverse revenue streams and strong trading desks."
            }
        ]
        
        # Combine all news categories
        all_news = general_market_news + tech_news + financial_news
        
        # Filter by symbol if provided
        if symbol:
            filtered_news = []
            for news_item in all_news:
                if symbol.upper() in news_item.get("symbols", []):
                    filtered_news.append(news_item)
            return filtered_news
        
        # Filter by category if provided
        if category:
            filtered_news = []
            for news_item in all_news:
                if news_item.get("category") == category:
                    filtered_news.append(news_item)
            return filtered_news
        
        # Apply limit to results
        return all_news[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.get("/api/trading_modes")
async def get_trading_modes():
    """Get available trading modes and their status."""
    try:
        # In a real implementation, this would pull data from your trading mode manager
        # For now, we'll create simulated data that matches the dashboard's expectations
        
        # Create sample trading modes
        modes = [
            {
                "id": "standard",
                "name": "Standard Trading",
                "description": "Balance between performance and risk with standard position sizing",
                "active": True,
                "risk_level": "medium",
                "max_positions": 10,
                "parameters": {
                    "position_size_pct": 5.0,
                    "stop_loss_pct": 2.5,
                    "take_profit_pct": 7.5
                }
            },
            {
                "id": "conservative",
                "name": "Conservative Mode",
                "description": "Reduced position sizing with tighter stops for capital preservation",
                "active": False,
                "risk_level": "low",
                "max_positions": 8,
                "parameters": {
                    "position_size_pct": 3.0,
                    "stop_loss_pct": 1.5,
                    "take_profit_pct": 4.5
                }
            },
            {
                "id": "aggressive",
                "name": "Aggressive Growth",
                "description": "Larger position sizing with wider stops for maximum returns",
                "active": False,
                "risk_level": "high",
                "max_positions": 15,
                "parameters": {
                    "position_size_pct": 10.0,
                    "stop_loss_pct": 5.0,
                    "take_profit_pct": 15.0
                }
            }
        ]
        
        return modes
    except Exception as e:
        logger.error(f"Error fetching trading modes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching trading modes: {str(e)}")

# Initialize API with references to the components
def initialize_api(strategy_rotator, continuous_learner):
    """Initialize the API with references to the components."""
    global _strategy_rotator, _continuous_learner
    
    _strategy_rotator = strategy_rotator
    _continuous_learner = continuous_learner
    
    logger.info("API initialized with strategy rotator and continuous learner")


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the API server with settings from config
    uvicorn.run(
        app, 
        host=api_settings.host, 
        port=api_settings.port,
        debug=api_settings.debug
    )