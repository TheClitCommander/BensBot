#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Manager - Advanced risk management system with dynamic position sizing,
stop-loss mechanisms, and exposure controls.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from trading_bot.common.config_utils import setup_directories, load_config, save_state, load_state

# Setup logging
logger = logging.getLogger("RiskManager")

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    CRITICAL = 5

class StopLossType(Enum):
    """Stop-loss type enumeration"""
    FIXED = 1         # Fixed percentage
    VOLATILITY = 2    # Volatility-based (e.g., ATR multiple)
    TRAILING = 3      # Trailing stop
    TIME_BASED = 4    # Time-based stop

class RiskManager:
    """
    Advanced risk management system that controls position sizing,
    implements stop-loss mechanisms, and monitors portfolio risk.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the risk manager.
        
        Args:
            config: Configuration dictionary
        """
        # Setup paths
        self.paths = setup_directories(
            data_dir=config.get("data_dir") if config else None,
            component_name="risk_manager"
        )
        
        # Load configuration
        self.config = load_config(
            self.paths.get("config_path"), 
            default_config_factory=self._get_default_config
        ) if not config else config
        
        # Maximum drawdown settings
        self.max_drawdown_pct = self.config.get("max_drawdown_pct", 0.15)  # 15% max drawdown
        self.max_daily_drawdown_pct = self.config.get("max_daily_drawdown_pct", 0.05)  # 5% max daily drawdown
        
        # Position sizing settings
        self.default_risk_per_trade = self.config.get("default_risk_per_trade", 0.01)  # 1% risk per trade
        self.max_risk_per_trade = self.config.get("max_risk_per_trade", 0.05)  # 5% max risk per trade
        self.max_portfolio_risk = self.config.get("max_portfolio_risk", 0.30)  # 30% max portfolio risk
        
        # Stop-loss settings
        self.stop_loss_type = StopLossType[self.config.get("stop_loss_type", "VOLATILITY")]
        self.fixed_stop_loss_pct = self.config.get("fixed_stop_loss_pct", 0.02)  # 2% fixed stop-loss
        self.atr_multiplier = self.config.get("atr_multiplier", 3.0)  # 3 x ATR for volatility-based stops
        self.trailing_stop_activation_pct = self.config.get("trailing_stop_activation_pct", 0.01)  # 1% profit to activate trailing stop
        self.trailing_stop_distance_pct = self.config.get("trailing_stop_distance_pct", 0.02)  # 2% trailing stop distance
        
        # Portfolio state
        self.portfolio_value = self.config.get("initial_portfolio_value", 100000.0)
        self.peak_portfolio_value = self.portfolio_value
        self.positions = {}  # Symbol -> position info
        self.trades_history = []
        self.max_positions = self.config.get("max_positions", 10)
        
        # Risk metrics
        self.current_drawdown_pct = 0.0
        self.daily_drawdown_pct = 0.0
        self.total_portfolio_risk = 0.0
        self.risk_level = RiskLevel.LOW
        
        # VaR settings
        self.var_confidence_level = self.config.get("var_confidence_level", 0.95)
        self.var_time_horizon = self.config.get("var_time_horizon", 1)  # days
        self.position_var = {}  # Symbol -> VaR
        self.portfolio_var = 0.0
        
        # Daily tracking
        self.today = datetime.now().date()
        self.daily_high = self.portfolio_value
        
        # Load state if available
        self.load_state()
        
        logger.info("Risk Manager initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "max_drawdown_pct": 0.15,
            "max_daily_drawdown_pct": 0.05,
            "default_risk_per_trade": 0.01,
            "max_risk_per_trade": 0.05,
            "max_portfolio_risk": 0.30,
            "stop_loss_type": "VOLATILITY",
            "fixed_stop_loss_pct": 0.02,
            "atr_multiplier": 3.0,
            "trailing_stop_activation_pct": 0.01,
            "trailing_stop_distance_pct": 0.02,
            "initial_portfolio_value": 100000.0,
            "max_positions": 10,
            "var_confidence_level": 0.95,
            "var_time_horizon": 1
        }
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss_price: float, market_data: Dict[str, Any]) -> int:
        """
        Calculate the appropriate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            entry_price: Planned entry price
            stop_loss_price: Initial stop-loss price
            market_data: Market data dictionary containing price history
            
        Returns:
            int: Number of shares/contracts to trade
        """
        # Calculate risk per trade in dollars
        risk_dollars = self.portfolio_value * self.default_risk_per_trade
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0:
            logger.warning(f"Invalid risk per share for {symbol}: {risk_per_share}")
            return 0
        
        # Calculate position size
        position_size = int(risk_dollars / risk_per_share)
        
        # Limit position by max risk per trade
        max_position_size = int(self.portfolio_value * self.max_risk_per_trade / entry_price)
        position_size = min(position_size, max_position_size)
        
        # Check if we're within the max portfolio risk
        new_exposure = position_size * entry_price
        current_exposure = sum(pos.get("current_value", 0) for pos in self.positions.values())
        
        if (current_exposure + new_exposure) / self.portfolio_value > self.max_portfolio_risk:
            # Scale back position to respect max portfolio risk
            available_risk = (self.max_portfolio_risk * self.portfolio_value) - current_exposure
            if available_risk <= 0:
                logger.warning(f"Cannot open position for {symbol}: Max portfolio risk reached")
                return 0
            
            position_size = int(available_risk / entry_price)
        
        # Ensure we don't exceed max positions
        if len(self.positions) >= self.max_positions and symbol not in self.positions:
            logger.warning(f"Cannot open position for {symbol}: Max positions reached")
            return 0
        
        logger.info(f"Calculated position size for {symbol}: {position_size} shares at ${entry_price:.2f}")
        return position_size
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, 
                          direction: int, market_data: Dict[str, Any]) -> float:
        """
        Calculate stop-loss price based on the configured stop-loss type.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            direction: Trade direction (1 for long, -1 for short)
            market_data: Market data dictionary containing price history
            
        Returns:
            float: Stop-loss price
        """
        if self.stop_loss_type == StopLossType.FIXED:
            # Fixed percentage stop-loss
            stop_loss = entry_price * (1 - direction * self.fixed_stop_loss_pct)
        
        elif self.stop_loss_type == StopLossType.VOLATILITY:
            # Volatility-based stop-loss using ATR
            atr = self._calculate_atr(market_data, period=14)
            stop_loss = entry_price - (direction * self.atr_multiplier * atr)
        
        elif self.stop_loss_type == StopLossType.TRAILING:
            # Initial stop for trailing stop-loss
            # Will be updated as price moves in favorable direction
            atr = self._calculate_atr(market_data, period=14)
            stop_loss = entry_price - (direction * self.atr_multiplier * atr)
        
        else:  # TIME_BASED or any other type
            # Default to fixed stop-loss
            stop_loss = entry_price * (1 - direction * self.fixed_stop_loss_pct)
        
        logger.info(f"Calculated stop-loss for {symbol}: ${stop_loss:.2f} (entry: ${entry_price:.2f}, direction: {direction})")
        return stop_loss
    
    def _calculate_atr(self, market_data: Dict[str, Any], period: int = 14) -> float:
        """
        Calculate the Average True Range (ATR) from market data.
        
        Args:
            market_data: Market data dictionary
            period: ATR period
            
        Returns:
            float: ATR value
        """
        highs = market_data.get("high", [])
        lows = market_data.get("low", [])
        closes = market_data.get("close", [])
        
        if len(closes) < period + 1:
            # Not enough data, return a default ATR based on recent volatility
            if len(closes) > 1:
                return abs(closes[-1] - closes[0]) / len(closes)
            return closes[-1] * 0.02  # Default to 2% of current price
        
        # Calculate true ranges
        tr_values = []
        for i in range(1, len(closes)):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i-1]
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = max(tr1, tr2, tr3)
            tr_values.append(true_range)
        
        # Calculate ATR
        atr = sum(tr_values[-period:]) / period
        return atr
    
    def update_trailing_stops(self, market_data: Dict[str, Dict[str, Any]]):
        """
        Update trailing stop-losses for all positions.
        
        Args:
            market_data: Dictionary mapping symbols to market data
        """
        for symbol, position in self.positions.items():
            if position.get("stop_loss_type") != StopLossType.TRAILING:
                continue
            
            # Get current price for the symbol
            if symbol not in market_data:
                logger.warning(f"No market data for {symbol}, cannot update trailing stop")
                continue
                
            current_price = market_data[symbol].get("price", position.get("entry_price"))
            if not current_price:
                continue
            
            # Update position value
            position["current_value"] = position["size"] * current_price
            
            # Check if position is in profit enough to activate trailing stop
            entry_price = position["entry_price"]
            direction = position["direction"]
            activation_threshold = entry_price * (1 + direction * self.trailing_stop_activation_pct)
            
            # For long positions: current_price > activation_threshold
            # For short positions: current_price < activation_threshold
            if (direction == 1 and current_price > activation_threshold) or \
               (direction == -1 and current_price < activation_threshold):
                
                # Calculate new stop-loss level
                new_stop = current_price * (1 - direction * self.trailing_stop_distance_pct)
                
                # Only update stop if it's better than the current one
                # For long: new_stop > current_stop
                # For short: new_stop < current_stop
                current_stop = position["stop_loss_price"]
                if (direction == 1 and new_stop > current_stop) or \
                   (direction == -1 and new_stop < current_stop):
                    position["stop_loss_price"] = new_stop
                    logger.info(f"Updated trailing stop for {symbol} to ${new_stop:.2f}")
    
    def check_stop_losses(self, market_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Check if any positions have hit their stop-loss levels.
        
        Args:
            market_data: Dictionary mapping symbols to market data
            
        Returns:
            List of symbols that hit stop-loss
        """
        triggered_symbols = []
        
        for symbol, position in list(self.positions.items()):
            if symbol not in market_data:
                continue
                
            current_price = market_data[symbol].get("price")
            if not current_price:
                continue
            
            stop_price = position["stop_loss_price"]
            direction = position["direction"]
            
            # Check if stop-loss is triggered
            # For long positions: current_price <= stop_price
            # For short positions: current_price >= stop_price
            if (direction == 1 and current_price <= stop_price) or \
               (direction == -1 and current_price >= stop_price):
                
                logger.info(f"Stop-loss triggered for {symbol} at ${current_price:.2f} (stop: ${stop_price:.2f})")
                triggered_symbols.append(symbol)
                
                # Record the stopped out trade
                trade_record = position.copy()
                trade_record["exit_price"] = current_price
                trade_record["exit_time"] = datetime.now().isoformat()
                trade_record["pnl"] = position["size"] * (current_price - position["entry_price"]) * direction
                trade_record["pnl_pct"] = (current_price / position["entry_price"] - 1) * direction * 100
                trade_record["exit_reason"] = "stop_loss"
                
                self.trades_history.append(trade_record)
                
                # Remove the position
                del self.positions[symbol]
        
        return triggered_symbols
    
    def open_position(self, symbol: str, entry_price: float, direction: int, 
                    market_data: Dict[str, Any], reason: str = "signal") -> bool:
        """
        Open a new position with appropriate risk management.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            direction: Trade direction (1 for long, -1 for short)
            market_data: Market data dictionary
            reason: Reason for opening the position
            
        Returns:
            bool: True if position was opened successfully
        """
        # Check if we already have this position
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return False
        
        # Calculate stop-loss price
        stop_loss_price = self.calculate_stop_loss(symbol, entry_price, direction, market_data)
        
        # Calculate position size
        position_size = self.calculate_position_size(symbol, entry_price, stop_loss_price, market_data)
        
        if position_size <= 0:
            logger.warning(f"Invalid position size for {symbol}: {position_size}")
            return False
        
        # Create position record
        position = {
            "symbol": symbol,
            "entry_price": entry_price,
            "entry_time": datetime.now().isoformat(),
            "direction": direction,
            "size": position_size,
            "current_value": position_size * entry_price,
            "stop_loss_price": stop_loss_price,
            "stop_loss_type": self.stop_loss_type,
            "reason": reason
        }
        
        # Add position to portfolio
        self.positions[symbol] = position
        
        # Update portfolio risk
        self._update_portfolio_risk()
        
        logger.info(f"Opened {position_size} {'long' if direction == 1 else 'short'} position in {symbol} at ${entry_price:.2f}")
        return True
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "signal") -> bool:
        """
        Close an existing position.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for closing the position
            
        Returns:
            bool: True if position was closed successfully
        """
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return False
        
        position = self.positions[symbol]
        direction = position["direction"]
        entry_price = position["entry_price"]
        size = position["size"]
        
        # Calculate P&L
        pnl = size * (exit_price - entry_price) * direction
        pnl_pct = (exit_price / entry_price - 1) * direction * 100
        
        # Record the closed trade
        trade_record = position.copy()
        trade_record["exit_price"] = exit_price
        trade_record["exit_time"] = datetime.now().isoformat()
        trade_record["pnl"] = pnl
        trade_record["pnl_pct"] = pnl_pct
        trade_record["exit_reason"] = reason
        
        self.trades_history.append(trade_record)
        
        # Remove the position
        del self.positions[symbol]
        
        # Update portfolio value and risk
        self.portfolio_value += pnl
        self._update_portfolio_risk()
        
        logger.info(f"Closed {size} {'long' if direction == 1 else 'short'} position in {symbol} at ${exit_price:.2f} for ${pnl:.2f} ({pnl_pct:.2f}%)")
        return True
    
    def update_portfolio_value(self, market_data: Dict[str, Dict[str, Any]]):
        """
        Update portfolio value based on current market prices.
        
        Args:
            market_data: Dictionary mapping symbols to market data
        """
        # Check if date has changed
        current_date = datetime.now().date()
        if current_date != self.today:
            # Reset daily tracking
            self.today = current_date
            self.daily_high = self.portfolio_value
            self.daily_drawdown_pct = 0.0
        
        # Start with cash value
        updated_value = self.portfolio_value
        
        # Subtract current positions' values since we'll recalculate them
        for position in self.positions.values():
            updated_value -= position.get("current_value", 0)
        
        # Add updated positions' values
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol].get("price")
                if current_price:
                    current_value = position["size"] * current_price
                    position["current_value"] = current_value
                    updated_value += current_value
        
        # Update portfolio value
        self.portfolio_value = updated_value
        
        # Update peak value if we have a new high
        if self.portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = self.portfolio_value
        
        # Update daily high if we have a new daily high
        if self.portfolio_value > self.daily_high:
            self.daily_high = self.portfolio_value
        
        # Calculate drawdowns
        self._calculate_drawdowns()
        
        # Check risk levels
        self._update_risk_level()
        
        # Log portfolio update
        logger.debug(f"Updated portfolio value: ${self.portfolio_value:.2f}, Drawdown: {self.current_drawdown_pct:.2f}%, Risk level: {self.risk_level.name}")
    
    def _calculate_drawdowns(self):
        """Calculate current drawdown metrics."""
        # Overall drawdown from peak
        if self.peak_portfolio_value > 0:
            self.current_drawdown_pct = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
        else:
            self.current_drawdown_pct = 0.0
        
        # Daily drawdown from today's high
        if self.daily_high > 0:
            self.daily_drawdown_pct = (self.daily_high - self.portfolio_value) / self.daily_high
        else:
            self.daily_drawdown_pct = 0.0
    
    def _update_portfolio_risk(self):
        """Update portfolio risk metrics."""
        # Simple calculation of total portfolio risk
        total_exposure = sum(pos.get("current_value", 0) for pos in self.positions.values())
        self.total_portfolio_risk = total_exposure / self.portfolio_value if self.portfolio_value > 0 else 0
    
    def _update_risk_level(self):
        """Update the current risk level based on drawdowns and exposure."""
        # Determine risk level based on current metrics
        if self.current_drawdown_pct >= 0.9 * self.max_drawdown_pct or self.daily_drawdown_pct >= 0.9 * self.max_daily_drawdown_pct:
            self.risk_level = RiskLevel.CRITICAL
        elif self.current_drawdown_pct >= 0.7 * self.max_drawdown_pct or self.daily_drawdown_pct >= 0.7 * self.max_daily_drawdown_pct:
            self.risk_level = RiskLevel.EXTREME
        elif self.current_drawdown_pct >= 0.5 * self.max_drawdown_pct or self.daily_drawdown_pct >= 0.5 * self.max_daily_drawdown_pct:
            self.risk_level = RiskLevel.HIGH
        elif self.current_drawdown_pct >= 0.3 * self.max_drawdown_pct or self.daily_drawdown_pct >= 0.3 * self.max_daily_drawdown_pct:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
    
    def calculate_var(self, market_data: Dict[str, Dict[str, Any]], method: str = "historical"):
        """
        Calculate Value at Risk (VaR) for portfolio.
        
        Args:
            market_data: Dictionary mapping symbols to market data
            method: VaR calculation method ('historical', 'parametric', or 'monte_carlo')
        """
        if method == "historical":
            self._calculate_historical_var(market_data)
        elif method == "parametric":
            self._calculate_parametric_var(market_data)
        elif method == "monte_carlo":
            self._calculate_monte_carlo_var(market_data)
        else:
            logger.warning(f"Unknown VaR method: {method}, using historical")
            self._calculate_historical_var(market_data)
    
    def _calculate_historical_var(self, market_data: Dict[str, Dict[str, Any]]):
        """
        Calculate VaR using historical method.
        
        Args:
            market_data: Dictionary mapping symbols to market data
        """
        # For each position, calculate historical returns
        position_vars = {}
        
        for symbol, position in self.positions.items():
            if symbol not in market_data:
                continue
            
            # Get price history
            prices = market_data[symbol].get("close", [])
            if len(prices) < 30:  # Need sufficient history
                continue
            
            # Calculate daily returns
            returns = np.diff(prices) / prices[:-1]
            
            # Sort returns from worst to best
            sorted_returns = np.sort(returns)
            
            # Find the return at the specified confidence level
            var_index = int(len(sorted_returns) * (1 - self.var_confidence_level))
            var_return = sorted_returns[var_index]
            
            # Calculate VAR in dollar terms
            position_value = position.get("current_value", 0)
            position_var = position_value * abs(var_return) * np.sqrt(self.var_time_horizon)
            
            position_vars[symbol] = position_var
        
        # Store position VaRs
        self.position_var = position_vars
        
        # Simple sum of position VaRs (ignoring correlations)
        self.portfolio_var = sum(position_vars.values())
        
        logger.debug(f"Historical VaR ({self.var_confidence_level*100}%, {self.var_time_horizon}-day): ${self.portfolio_var:.2f}")
    
    def _calculate_parametric_var(self, market_data: Dict[str, Dict[str, Any]]):
        """Placeholder for parametric VaR calculation."""
        logger.info("Parametric VaR calculation not yet implemented, using historical")
        self._calculate_historical_var(market_data)
    
    def _calculate_monte_carlo_var(self, market_data: Dict[str, Dict[str, Any]]):
        """Placeholder for Monte Carlo VaR calculation."""
        logger.info("Monte Carlo VaR calculation not yet implemented, using historical")
        self._calculate_historical_var(market_data)
    
    def check_risk_limits(self) -> Tuple[bool, List[str]]:
        """
        Check if any risk limits are breached.
        
        Returns:
            Tuple of (should_reduce_risk, list of reasons)
        """
        reasons = []
        
        # Check drawdown limits
        if self.current_drawdown_pct >= self.max_drawdown_pct:
            reasons.append(f"Max drawdown limit breached: {self.current_drawdown_pct:.2%} >= {self.max_drawdown_pct:.2%}")
        
        if self.daily_drawdown_pct >= self.max_daily_drawdown_pct:
            reasons.append(f"Max daily drawdown limit breached: {self.daily_drawdown_pct:.2%} >= {self.max_daily_drawdown_pct:.2%}")
        
        # Check portfolio risk
        if self.total_portfolio_risk >= self.max_portfolio_risk:
            reasons.append(f"Max portfolio risk breached: {self.total_portfolio_risk:.2%} >= {self.max_portfolio_risk:.2%}")
        
        # Critical risk level check
        if self.risk_level == RiskLevel.CRITICAL:
            reasons.append(f"Risk level is CRITICAL")
        
        return len(reasons) > 0, reasons
    
    def get_reduction_actions(self) -> List[Dict[str, Any]]:
        """
        Get recommended actions to reduce risk when limits are breached.
        
        Returns:
            List of action dictionaries with 'symbol', 'action', and 'reason' keys
        """
        should_reduce, reasons = self.check_risk_limits()
        
        if not should_reduce:
            return []
        
        actions = []
        
        # If at critical risk level, close all positions
        if self.risk_level == RiskLevel.CRITICAL:
            for symbol in self.positions:
                actions.append({
                    "symbol": symbol,
                    "action": "close_position",
                    "reason": "Critical risk level reached"
                })
            return actions
        
        # If at extreme risk, reduce largest positions
        if self.risk_level == RiskLevel.EXTREME:
            # Sort positions by size
            sorted_positions = sorted(
                self.positions.items(),
                key=lambda x: x[1].get("current_value", 0),
                reverse=True
            )
            
            # Close top 30% of positions
            positions_to_close = sorted_positions[:max(1, int(len(sorted_positions) * 0.3))]
            
            for symbol, _ in positions_to_close:
                actions.append({
                    "symbol": symbol,
                    "action": "close_position",
                    "reason": "Extreme risk level - reducing largest positions"
                })
            
            return actions
        
        # For high risk, reduce underwater positions
        if self.risk_level == RiskLevel.HIGH:
            # Find underwater positions
            underwater_positions = [
                (symbol, pos) for symbol, pos in self.positions.items()
                if (pos["direction"] == 1 and pos.get("current_value", 0) < pos["size"] * pos["entry_price"]) or
                   (pos["direction"] == -1 and pos.get("current_value", 0) > pos["size"] * pos["entry_price"])
            ]
            
            # Close most underwater positions first
            sorted_underwater = sorted(
                underwater_positions,
                key=lambda x: (x[1].get("current_value", 0) / (x[1]["size"] * x[1]["entry_price"]) - 1) * x[1]["direction"],
                reverse=False
            )
            
            # Close up to 20% of positions
            positions_to_close = sorted_underwater[:max(1, int(len(self.positions) * 0.2))]
            
            for symbol, _ in positions_to_close:
                actions.append({
                    "symbol": symbol,
                    "action": "close_position",
                    "reason": "High risk level - reducing underwater positions"
                })
            
            return actions
        
        # For medium risk, tighten stops on underwater positions
        if self.risk_level == RiskLevel.MEDIUM:
            for symbol, position in self.positions.items():
                current_price = position.get("current_value", 0) / position["size"]
                
                # Check if position is underwater
                if (position["direction"] == 1 and current_price < position["entry_price"]) or \
                   (position["direction"] == -1 and current_price > position["entry_price"]):
                    
                    actions.append({
                        "symbol": symbol,
                        "action": "tighten_stop",
                        "reason": "Medium risk level - tightening stops"
                    })
            
            return actions
        
        return actions
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics.
        
        Returns:
            Dictionary with risk metrics
        """
        return {
            "portfolio_value": self.portfolio_value,
            "peak_portfolio_value": self.peak_portfolio_value,
            "current_drawdown_pct": self.current_drawdown_pct,
            "daily_drawdown_pct": self.daily_drawdown_pct,
            "total_portfolio_risk": self.total_portfolio_risk,
            "risk_level": self.risk_level.name,
            "portfolio_var": self.portfolio_var,
            "position_var": self.position_var,
            "positions_count": len(self.positions),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_state(self) -> None:
        """Save risk manager state to disk."""
        state = {
            "portfolio_value": self.portfolio_value,
            "peak_portfolio_value": self.peak_portfolio_value,
            "positions": self.positions,
            "trades_history": self.trades_history[-1000:] if len(self.trades_history) > 1000 else self.trades_history,
            "risk_level": self.risk_level.name,
            "current_drawdown_pct": self.current_drawdown_pct,
            "daily_drawdown_pct": self.daily_drawdown_pct,
            "total_portfolio_risk": self.total_portfolio_risk,
            "today": self.today.isoformat(),
            "daily_high": self.daily_high,
            "timestamp": datetime.now().isoformat()
        }
        
        save_state(self.paths["state_path"], state)
        logger.info("Risk manager state saved")
    
    def load_state(self) -> bool:
        """
        Load risk manager state from disk.
        
        Returns:
            bool: True if state loaded successfully
        """
        state = load_state(self.paths["state_path"])
        
        if not state:
            return False
        
        try:
            self.portfolio_value = state.get("portfolio_value", self.portfolio_value)
            self.peak_portfolio_value = state.get("peak_portfolio_value", self.peak_portfolio_value)
            self.positions = state.get("positions", {})
            self.trades_history = state.get("trades_history", [])
            
            # Convert string risk level back to enum
            risk_level_name = state.get("risk_level", self.risk_level.name)
            self.risk_level = RiskLevel[risk_level_name]
            
            self.current_drawdown_pct = state.get("current_drawdown_pct", self.current_drawdown_pct)
            self.daily_drawdown_pct = state.get("daily_drawdown_pct", self.daily_drawdown_pct)
            self.total_portfolio_risk = state.get("total_portfolio_risk", self.total_portfolio_risk)
            
            if "today" in state:
                self.today = datetime.fromisoformat(state["today"]).date()
            
            self.daily_high = state.get("daily_high", self.daily_high)
            
            logger.info("Risk manager state loaded")
            return True
        except Exception as e:
            logger.error(f"Error loading risk manager state: {e}")
            return False


# Simple example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create risk manager
    risk_manager = RiskManager()
    
    # Create sample market data
    market_data = {
        "AAPL": {
            "price": 150.0,
            "close": [148.5, 149.2, 150.1, 149.8, 150.0],
            "high": [149.5, 150.2, 151.1, 150.8, 151.0],
            "low": [147.5, 148.2, 149.1, 148.8, 149.0],
            "volume": [5000000, 5200000, 4800000, 5100000, 5000000]
        },
        "MSFT": {
            "price": 290.0,
            "close": [285.5, 287.2, 289.1, 288.8, 290.0],
            "high": [287.5, 289.2, 291.1, 290.8, 292.0],
            "low": [283.5, 285.2, 287.1, 286.8, 288.0],
            "volume": [3000000, 3200000, 2800000, 3100000, 3000000]
        }
    }
    
    # Open some positions
    risk_manager.open_position("AAPL", 150.0, 1, market_data["AAPL"], "test")
    risk_manager.open_position("MSFT", 290.0, -1, market_data["MSFT"], "test")
    
    # Update portfolio value
    risk_manager.update_portfolio_value(market_data)
    
    # Calculate VaR
    risk_manager.calculate_var(market_data)
    
    # Get risk metrics
    metrics = risk_manager.get_risk_metrics()
    print("Risk metrics:", json.dumps(metrics, indent=2))
    
    # Check stops
    triggered = risk_manager.check_stop_losses(market_data)
    print("Triggered stops:", triggered)
    
    # Check risk limits
    should_reduce, reasons = risk_manager.check_risk_limits()
    print(f"Should reduce risk: {should_reduce}")
    if should_reduce:
        print("Reasons:", reasons)
        actions = risk_manager.get_reduction_actions()
        print("Recommended actions:", json.dumps(actions, indent=2)) 