#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position Sizer Module

This module provides the PositionSizer class for determining
appropriate position sizes based on risk parameters.
"""

import logging
import math
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Position Sizer for calculating position sizes based on risk parameters.
    
    The PositionSizer helps determine the appropriate number of shares or
    contracts to trade based on account size, risk tolerance, and other
    risk management criteria.
    """
    
    def __init__(self, portfolio_value: float, default_risk_percent: float = 0.01):
        """
        Initialize the PositionSizer.
        
        Args:
            portfolio_value: Current portfolio value
            default_risk_percent: Default percentage of portfolio to risk per trade (0.01 = 1%)
        """
        self.portfolio_value = portfolio_value
        self.default_risk_percent = default_risk_percent
        
        logger.info(f"Initialized PositionSizer with portfolio value: ${portfolio_value:,.2f}")
    
    def get_portfolio_value(self) -> float:
        """
        Get the current portfolio value.
        
        Returns:
            Current portfolio value
        """
        return self.portfolio_value
    
    def update_portfolio_value(self, new_value: float) -> None:
        """
        Update the portfolio value.
        
        Args:
            new_value: New portfolio value
        """
        old_value = self.portfolio_value
        self.portfolio_value = new_value
        logger.info(f"Updated portfolio value: ${old_value:,.2f} -> ${new_value:,.2f}")
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss: Optional[float] = None,
                              risk_percent: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            symbol: Symbol to trade
            entry_price: Entry price
            stop_loss: Stop loss price (optional)
            risk_percent: Percentage of portfolio to risk (optional, uses default if not provided)
            
        Returns:
            Dictionary with position size information
        """
        if risk_percent is None:
            risk_percent = self.default_risk_percent
        
        # Calculate dollar risk
        dollar_risk = self.portfolio_value * risk_percent
        
        # If stop loss is provided, calculate position size based on stop loss
        if stop_loss is not None and stop_loss != entry_price:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            # Calculate position size in shares
            shares = dollar_risk / risk_per_share
            
            # Round down to nearest whole share
            shares = math.floor(shares)
            
            # Calculate total position value
            position_value = shares * entry_price
            
            # Percentage of portfolio
            portfolio_percent = position_value / self.portfolio_value
            
            # Actual dollar risk
            actual_dollar_risk = shares * risk_per_share
            
            return {
                "symbol": symbol,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "shares": shares,
                "position_value": position_value,
                "portfolio_percent": portfolio_percent,
                "dollar_risk": actual_dollar_risk,
                "risk_percent": actual_dollar_risk / self.portfolio_value
            }
        else:
            # Without a stop loss, use a fixed percentage of portfolio for position sizing
            # This is less ideal but allows for position sizing without a stop loss
            
            # Calculate position value as a percentage of portfolio
            position_value = self.portfolio_value * (risk_percent * 10)  # 10x risk percentage
            
            # Calculate shares
            shares = math.floor(position_value / entry_price)
            
            # Recalculate position value
            position_value = shares * entry_price
            
            # Percentage of portfolio
            portfolio_percent = position_value / self.portfolio_value
            
            return {
                "symbol": symbol,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "shares": shares,
                "position_value": position_value,
                "portfolio_percent": portfolio_percent,
                "dollar_risk": None,  # Unknown without stop loss
                "risk_percent": None  # Unknown without stop loss
            }
    
    def calculate_option_position_size(self, symbol: str, premium: float, 
                                     max_loss_per_contract: float,
                                     risk_percent: Optional[float] = None,
                                     min_contracts: int = 1,
                                     max_contracts: int = 100) -> Dict[str, Any]:
        """
        Calculate position size for options trades.
        
        Args:
            symbol: Symbol to trade
            premium: Option premium per contract
            max_loss_per_contract: Maximum loss per contract
            risk_percent: Percentage of portfolio to risk (optional, uses default if not provided)
            min_contracts: Minimum number of contracts
            max_contracts: Maximum number of contracts
            
        Returns:
            Dictionary with position size information
        """
        if risk_percent is None:
            risk_percent = self.default_risk_percent
        
        # Calculate dollar risk
        dollar_risk = self.portfolio_value * risk_percent
        
        # Calculate contracts based on risk
        if max_loss_per_contract > 0:
            contracts = math.floor(dollar_risk / max_loss_per_contract)
        else:
            contracts = min_contracts
        
        # Apply limits
        contracts = max(min_contracts, min(contracts, max_contracts))
        
        # Calculate total premium and max loss
        total_premium = contracts * premium * 100  # 100 multiplier for options
        total_max_loss = contracts * max_loss_per_contract
        
        # Percentage of portfolio
        portfolio_percent = total_premium / self.portfolio_value
        
        return {
            "symbol": symbol,
            "premium": premium,
            "contracts": contracts,
            "total_premium": total_premium,
            "max_loss_per_contract": max_loss_per_contract,
            "total_max_loss": total_max_loss,
            "portfolio_percent": portfolio_percent,
            "risk_percent": total_max_loss / self.portfolio_value
        }
    
    def adjust_for_correlation(self, position_sizes: Dict[str, Dict[str, Any]], 
                            correlation_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, Any]]:
        """
        Adjust position sizes based on correlation between symbols.
        
        Args:
            position_sizes: Dictionary mapping symbols to position size information
            correlation_matrix: Matrix of correlations between symbols
            
        Returns:
            Adjusted position sizes
        """
        # This is a simplified correlation adjustment
        # In a real implementation, you would adjust position sizes based on
        # portfolio risk and correlation between positions
        
        adjusted_position_sizes = position_sizes.copy()
        
        for symbol, position in adjusted_position_sizes.items():
            # Skip if symbol not in correlation matrix
            if symbol not in correlation_matrix:
                continue
                
            # Calculate average correlation with other positions
            correlations = []
            for other_symbol in position_sizes:
                if other_symbol != symbol and other_symbol in correlation_matrix[symbol]:
                    correlations.append(abs(correlation_matrix[symbol][other_symbol]))
            
            if not correlations:
                continue
                
            avg_correlation = sum(correlations) / len(correlations)
            
            # Adjust position size based on correlation
            # Higher correlation = smaller position size
            if avg_correlation > 0.7:
                # Reduce position size by up to 50% for high correlations
                reduction_factor = 0.5 + 0.5 * (1 - avg_correlation) / 0.3
                
                # Apply reduction to shares and position value
                position["shares"] = math.floor(position["shares"] * reduction_factor)
                position["position_value"] = position["shares"] * position["entry_price"]
                
                # Update other values
                position["portfolio_percent"] = position["position_value"] / self.portfolio_value
                
                if position["stop_loss"] is not None:
                    position["dollar_risk"] = position["shares"] * abs(position["entry_price"] - position["stop_loss"])
                    position["risk_percent"] = position["dollar_risk"] / self.portfolio_value
        
        return adjusted_position_sizes 