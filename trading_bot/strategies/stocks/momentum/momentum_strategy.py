#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Strategy - Captures continued price movement by buying assets that have
shown strong recent performance and selling those that have underperformed.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

from trading_bot.strategies.base.stock_base import StockBaseStrategy
from trading_bot.strategies.strategy_template import Signal, SignalType, TimeFrame, MarketRegime

logger = logging.getLogger(__name__)

class MomentumStrategy(StockBaseStrategy):
    """
    Momentum trading strategy implementation that identifies and trades based on
    price momentum and trend strength.
    """
    
    # Default parameters specific to momentum trading
    DEFAULT_MOMENTUM_PARAMS = {
        "lookback_period": 14,
        "overbought": 70,
        "oversold": 30,
        "adx_threshold": 25,
        "trend_strength_threshold": 0.05,
        "use_volatility_adjustment": True,
        "cross_sectional": False,
        "signal_threshold": 0.0,
        "volatility_lookback": 20,
        "stop_loss_atr_multiple": 2.0,
        "take_profit_atr_multiple": 3.0,
    }
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize the momentum strategy with configurable parameters.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters (will be merged with default parameters)
            metadata: Strategy metadata
        """
        # Start with default stock parameters
        momentum_params = self.DEFAULT_STOCK_PARAMS.copy()
        
        # Add momentum-specific parameters
        momentum_params.update(self.DEFAULT_MOMENTUM_PARAMS)
        
        # Override with provided parameters
        if parameters:
            momentum_params.update(parameters)
        
        # Initialize the parent class
        super().__init__(name=name, parameters=momentum_params, metadata=metadata)
        
        logger.info(f"Initialized momentum strategy: {name}")
    
    def get_parameter_space(self) -> Dict[str, List[Any]]:
        """
        Get parameter space for optimization.
        
        Returns:
            Dictionary mapping parameter names to lists of possible values
        """
        return {
            "lookback_period": [5, 10, 14, 20, 30],
            "overbought": [65, 70, 75, 80],
            "oversold": [20, 25, 30, 35],
            "adx_threshold": [20, 25, 30],
            "trend_strength_threshold": [0.03, 0.05, 0.07],
            "use_volatility_adjustment": [True, False],
            "cross_sectional": [True, False],
            "signal_threshold": [0.0, 0.1, 0.2],
            "stop_loss_atr_multiple": [1.5, 2.0, 2.5, 3.0],
            "take_profit_atr_multiple": [2.0, 3.0, 4.0, 5.0],
        }
    
    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Calculate momentum indicators for all symbols.
        
        Args:
            data: Dictionary mapping symbols to DataFrames with OHLCV data
            
        Returns:
            Dictionary of calculated indicators for each symbol
        """
        indicators = {}
        
        for symbol, df in data.items():
            # Skip if insufficient data
            if len(df) < self.parameters["lookback_period"]:
                continue
                
            try:
                # Calculate price momentum (close price change over lookback period)
                lookback = self.parameters["lookback_period"]
                momentum = df['close'].pct_change(lookback)
                
                # Calculate Rate of Change (ROC)
                roc = (df['close'] / df['close'].shift(lookback) - 1) * 100
                
                # Calculate RSI
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=lookback).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=lookback).mean()
                
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                # Calculate Average Directional Index (ADX) for trend strength
                high_diff = df['high'].diff()
                low_diff = df['low'].diff().abs()
                
                plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
                minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
                
                tr = pd.DataFrame({
                    'hl': df['high'] - df['low'],
                    'hc': (df['high'] - df['close'].shift()).abs(),
                    'lc': (df['low'] - df['close'].shift()).abs()
                }).max(axis=1)
                
                atr = tr.rolling(window=lookback).mean()
                
                plus_di = 100 * (plus_dm.rolling(window=lookback).mean() / atr)
                minus_di = 100 * (minus_dm.rolling(window=lookback).mean() / atr)
                
                dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
                adx = dx.rolling(window=lookback).mean()
                
                # Prepare volatility-adjusted momentum if enabled
                if self.parameters["use_volatility_adjustment"]:
                    volatility = df['close'].pct_change().rolling(
                        window=self.parameters["volatility_lookback"]).std() * np.sqrt(252)
                    # Add small constant to avoid division by zero
                    vol_adj_momentum = momentum / (volatility + 1e-8)
                else:
                    vol_adj_momentum = momentum
                
                # Store indicators
                indicators[symbol] = {
                    "momentum": pd.DataFrame({"momentum": momentum}),
                    "roc": pd.DataFrame({"roc": roc}),
                    "rsi": pd.DataFrame({"rsi": rsi}),
                    "adx": pd.DataFrame({"adx": adx}),
                    "atr": pd.DataFrame({"atr": atr}),
                    "vol_adj_momentum": pd.DataFrame({"vol_adj_momentum": vol_adj_momentum}),
                    "plus_di": pd.DataFrame({"plus_di": plus_di}),
                    "minus_di": pd.DataFrame({"minus_di": minus_di})
                }
                
            except Exception as e:
                logger.error(f"Error calculating momentum indicators for {symbol}: {e}")
        
        return indicators
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Signal]:
        """
        Generate trading signals based on momentum indicators.
        
        Args:
            data: Dictionary mapping symbols to DataFrames with OHLCV data
            
        Returns:
            Dictionary mapping symbols to Signal objects
        """
        # Apply stock-specific filters from the base class
        filtered_data = self.filter_universe(data)
        
        # Calculate indicators
        indicators = self.calculate_indicators(filtered_data)
        
        # Generate signals
        signals = {}
        
        for symbol, symbol_indicators in indicators.items():
            try:
                # Get latest data
                latest_data = filtered_data[symbol].iloc[-1]
                prev_data = filtered_data[symbol].iloc[-2] if len(filtered_data[symbol]) > 1 else None
                latest_price = latest_data['close']
                latest_timestamp = latest_data.name if isinstance(latest_data.name, datetime) else datetime.now()
                
                # Get indicator values
                latest_momentum = symbol_indicators["momentum"].iloc[-1]["momentum"]
                latest_roc = symbol_indicators["roc"].iloc[-1]["roc"]
                latest_rsi = symbol_indicators["rsi"].iloc[-1]["rsi"]
                latest_adx = symbol_indicators["adx"].iloc[-1]["adx"]
                latest_atr = symbol_indicators["atr"].iloc[-1]["atr"]
                
                # Previous values for trend analysis
                prev_rsi = symbol_indicators["rsi"].iloc[-2]["rsi"] if len(symbol_indicators["rsi"]) > 1 else 50
                prev_momentum = symbol_indicators["momentum"].iloc[-2]["momentum"] if len(symbol_indicators["momentum"]) > 1 else 0
                
                # Get parameters
                lookback = self.parameters["lookback_period"]
                overbought = self.parameters["overbought"]
                oversold = self.parameters["oversold"]
                adx_threshold = self.parameters["adx_threshold"]
                stop_loss_atr_multiple = self.parameters["stop_loss_atr_multiple"]
                take_profit_atr_multiple = self.parameters["take_profit_atr_multiple"]
                
                # Generate signal based on momentum conditions
                signal_type = None
                confidence = 0.0
                
                # BUY conditions:
                # 1. Strong upward momentum (positive ROC)
                # 2. RSI was oversold but is now increasing
                # 3. ADX indicates strong trend
                if (latest_roc > 0 and
                    latest_rsi > oversold and
                    prev_rsi <= oversold and
                    latest_adx > adx_threshold):
                    
                    signal_type = SignalType.BUY
                    
                    # Calculate confidence based on multiple factors
                    # 1. Momentum strength
                    momentum_confidence = min(0.3, abs(latest_momentum) * 5)
                    
                    # 2. Trend strength via ADX
                    trend_confidence = min(0.3, latest_adx / 100)
                    
                    # 3. RSI confirmation
                    rsi_confirmation = min(0.2, (latest_rsi - oversold) / 20)
                    
                    # 4. Volume confirmation (if available)
                    volume_confidence = 0.0
                    if 'volume' in filtered_data[symbol].columns:
                        avg_volume = filtered_data[symbol]['volume'].rolling(window=20).mean().iloc[-1]
                        if filtered_data[symbol]['volume'].iloc[-1] > avg_volume:
                            volume_confidence = 0.2
                    
                    confidence = min(0.9, momentum_confidence + trend_confidence + rsi_confirmation + volume_confidence)
                    
                    # Calculate stop loss and take profit based on ATR
                    stop_loss = latest_price - (latest_atr * stop_loss_atr_multiple)
                    take_profit = latest_price + (latest_atr * take_profit_atr_multiple)
                
                # SELL conditions:
                # 1. Momentum turns negative
                # 2. RSI reaches overbought territory
                # 3. Momentum weakening after being strong
                elif (latest_roc < 0 or
                      latest_rsi >= overbought or
                      (prev_momentum > latest_momentum and latest_momentum > 0 and latest_rsi > 60)):
                    
                    signal_type = SignalType.SELL
                    
                    # Calculate confidence for sell signal
                    # 1. Negative momentum strength
                    momentum_confidence = min(0.3, abs(latest_momentum) * 5) if latest_momentum < 0 else 0.1
                    
                    # 2. Overbought confirmation
                    overbought_confirmation = min(0.3, (latest_rsi - 50) / 30) if latest_rsi > 50 else 0.1
                    
                    # 3. Trend weakening
                    trend_weakening = min(0.2, (prev_momentum - latest_momentum) * 10) if prev_momentum > latest_momentum else 0.1
                    
                    # 4. Volume confirmation (if available)
                    volume_confidence = 0.0
                    if 'volume' in filtered_data[symbol].columns:
                        avg_volume = filtered_data[symbol]['volume'].rolling(window=20).mean().iloc[-1]
                        if filtered_data[symbol]['volume'].iloc[-1] > avg_volume:
                            volume_confidence = 0.2
                    
                    confidence = min(0.9, momentum_confidence + overbought_confirmation + trend_weakening + volume_confidence)
                    
                    # Calculate stop loss and take profit for short position
                    stop_loss = latest_price + (latest_atr * stop_loss_atr_multiple)
                    take_profit = latest_price - (latest_atr * take_profit_atr_multiple)
                
                # Create signal if we have a valid signal type
                if signal_type:
                    signals[symbol] = Signal(
                        symbol=symbol,
                        signal_type=signal_type,
                        price=latest_price,
                        timestamp=latest_timestamp,
                        confidence=confidence,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        timeframe=TimeFrame.DAY_1,
                        metadata={
                            "strategy_type": "momentum",
                            "lookback_period": lookback,
                            "rsi": latest_rsi,
                            "adx": latest_adx,
                            "momentum": latest_momentum,
                            "roc": latest_roc,
                            "atr": latest_atr
                        }
                    )
            
            except Exception as e:
                logger.error(f"Error generating momentum signal for {symbol}: {e}")
        
        return signals
    
    def _calculate_performance_score(self, signals: Dict[str, Signal], 
                                   data: Dict[str, Any]) -> float:
        """
        Calculate a performance score for the generated signals.
        
        Args:
            signals: Generated signals
            data: Input data
            
        Returns:
            Performance score (higher is better)
        """
        if not signals:
            return 0.0
            
        # This is a simplified performance calculation
        # In a real implementation, you would simulate trades and calculate metrics
            
        # Assume we have forward returns in the data (for backtest evaluation)
        forward_returns = {}
        for symbol, signal in signals.items():
            if symbol not in data:
                continue
                
            signal_date_idx = None
            for i, date in enumerate(data[symbol].index):
                if date >= signal.timestamp:
                    signal_date_idx = i
                    break
                    
            if signal_date_idx is None or signal_date_idx >= len(data[symbol]) - 5:
                continue
                
            # Get 5-day forward return
            entry_price = signal.price
            exit_price = data[symbol]['close'].iloc[signal_date_idx + 5]
            
            # Calculate return based on signal type
            if signal.signal_type == SignalType.BUY:
                ret = (exit_price / entry_price) - 1
            else:  # SELL signal
                ret = 1 - (exit_price / entry_price)
                
            forward_returns[symbol] = ret * signal.confidence
        
        if not forward_returns:
            return 0.0
            
        # Average return across all signals
        avg_return = sum(forward_returns.values()) / len(forward_returns)
        
        # Simple Sharpe ratio (no risk-free rate)
        if len(forward_returns) > 1:
            std_dev = np.std(list(forward_returns.values()))
            if std_dev > 0:
                sharpe = avg_return / std_dev
            else:
                sharpe = avg_return if avg_return > 0 else 0
        else:
            sharpe = avg_return if avg_return > 0 else 0
        
        return sharpe
    
    def regime_compatibility(self, regime: MarketRegime) -> float:
        """
        Get compatibility score for this strategy in the given market regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Compatibility score (0-1, higher is better)
        """
        # Regime compatibility scores
        compatibility = {
            MarketRegime.BULL_TREND: 0.9,      # Excellent in bull trends
            MarketRegime.BEAR_TREND: 0.3,      # Poor in bear trends
            MarketRegime.CONSOLIDATION: 0.2,   # Poor in sideways markets
            MarketRegime.HIGH_VOLATILITY: 0.3, # Below average in high volatility
            MarketRegime.LOW_VOLATILITY: 0.6,  # Good in low volatility
            MarketRegime.UNKNOWN: 0.5          # Neutral in unknown regime
        }
        
        return compatibility.get(regime, 0.5) 