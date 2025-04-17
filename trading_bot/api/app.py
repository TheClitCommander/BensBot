#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot API - FastAPI application for the trading bot
providing UI and API endpoints for monitoring and control.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
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

# Initialize logging
logger = logging.getLogger("TradingBotAPI")

# Initialize FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="API for monitoring and controlling the trading bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
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
    
    # Start the API server
    uvicorn.run(app, host="0.0.0.0", port=8000) 