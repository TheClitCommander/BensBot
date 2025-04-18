#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Options Utilities Module

This module provides utility functions for options trading and analysis.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union

logger = logging.getLogger(__name__)

def get_atm_strike(current_price: float, available_strikes: List[float]) -> float:
    """
    Find the at-the-money (ATM) strike price closest to the current price.
    
    Args:
        current_price: Current price of the underlying
        available_strikes: List of available strike prices
        
    Returns:
        Strike price closest to the current price
    """
    if not available_strikes:
        return current_price
        
    # Calculate absolute difference between each strike and current price
    diffs = [abs(strike - current_price) for strike in available_strikes]
    
    # Find the index of the minimum difference
    min_diff_index = diffs.index(min(diffs))
    
    # Return the strike with minimum difference
    return available_strikes[min_diff_index]

def calculate_max_loss(strategy_type: str, strikes: List[float], 
                     premium: float, contracts: int = 1) -> float:
    """
    Calculate the maximum possible loss for an options strategy.
    
    Args:
        strategy_type: Type of strategy (e.g., 'long_call', 'iron_condor', etc.)
        strikes: List of strike prices involved in the strategy
        premium: Net premium paid or received
        contracts: Number of contracts
        
    Returns:
        Maximum possible loss in dollars
    """
    multiplier = 100  # Standard options contract multiplier
    
    if strategy_type.lower() == 'long_call' or strategy_type.lower() == 'long_put':
        # For long options, max loss is the premium paid
        return premium * multiplier * contracts
        
    elif strategy_type.lower() == 'short_call' or strategy_type.lower() == 'short_put':
        # For short options, max loss is theoretically unlimited for calls
        # and strike - premium for puts
        if strategy_type.lower() == 'short_put' and len(strikes) > 0:
            return (strikes[0] - premium) * multiplier * contracts
        return float('inf')  # Infinite risk for short calls
        
    elif strategy_type.lower() == 'call_spread' or strategy_type.lower() == 'put_spread':
        # For spreads, max loss is width of strikes minus premium received (or plus premium paid)
        if len(strikes) >= 2:
            width = abs(strikes[1] - strikes[0])
            
            if (strategy_type.lower() == 'call_spread' and strikes[0] < strikes[1]) or \
               (strategy_type.lower() == 'put_spread' and strikes[0] > strikes[1]):
                # Credit spread
                return (width - premium) * multiplier * contracts
            else:
                # Debit spread
                return premium * multiplier * contracts
                
        return premium * multiplier * contracts
        
    elif strategy_type.lower() == 'iron_condor' or strategy_type.lower() == 'iron_butterfly':
        # For iron condors and butterflies, max loss is the width of the widest wing minus premium received
        if len(strikes) >= 4:
            call_width = abs(strikes[2] - strikes[3])
            put_width = abs(strikes[0] - strikes[1])
            max_width = max(call_width, put_width)
            return (max_width - premium) * multiplier * contracts
            
        return premium * multiplier * contracts
        
    else:
        logger.warning(f"Unknown strategy type: {strategy_type}, returning premium as max loss")
        return premium * multiplier * contracts

def annualize_returns(returns: float, days_held: int) -> float:
    """
    Annualize a return based on the number of days held.
    
    Args:
        returns: Returns as a decimal (e.g., 0.10 for 10%)
        days_held: Number of days the position was held
        
    Returns:
        Annualized return as a decimal
    """
    if days_held <= 0:
        return 0.0
        
    # Annualization formula
    annual_trading_days = 252
    return (1 + returns) ** (annual_trading_days / days_held) - 1

def calculate_iv_percentile(current_iv: float, historical_ivs: List[float]) -> float:
    """
    Calculate the percentile of current IV relative to historical IVs.
    
    Args:
        current_iv: Current implied volatility
        historical_ivs: List of historical implied volatility values
        
    Returns:
        IV percentile (0-100)
    """
    if not historical_ivs:
        return 50.0  # Default to middle if no history
        
    # Count values less than current IV
    count_less = sum(1 for iv in historical_ivs if iv < current_iv)
    
    # Calculate percentile
    percentile = 100 * count_less / len(historical_ivs)
    
    return percentile

def calculate_option_greeks(price: float, strike: float, time_to_expiry: float, 
                          risk_free_rate: float, volatility: float, 
                          option_type: str = 'call') -> Dict[str, float]:
    """
    Calculate option Greeks using the Black-Scholes model.
    
    Args:
        price: Current price of the underlying
        strike: Option strike price
        time_to_expiry: Time to expiry in years
        risk_free_rate: Risk-free interest rate as decimal
        volatility: Implied volatility as decimal
        option_type: 'call' or 'put'
        
    Returns:
        Dictionary containing the Greeks (delta, gamma, theta, vega)
    """
    # Prevent errors from bad inputs
    if time_to_expiry <= 0 or volatility <= 0 or price <= 0:
        return {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
    
    # Black-Scholes formula parameters
    sqrt_t = np.sqrt(time_to_expiry)
    d1 = (np.log(price / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    
    # Calculate Phi(d1) and Phi(d2)
    phi_d1 = np.exp(-d1 ** 2 / 2) / np.sqrt(2 * np.pi)
    nd1 = 0.5 * (1 + np.math.erf(d1 / np.sqrt(2)))
    nd2 = 0.5 * (1 + np.math.erf(d2 / np.sqrt(2)))
    
    # Calculate option price and Greeks based on option type
    if option_type.lower() == 'call':
        delta = nd1
        theta = -(price * phi_d1 * volatility) / (2 * sqrt_t) - risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * nd2
        rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * nd2
    else:  # Put
        delta = nd1 - 1
        theta = -(price * phi_d1 * volatility) / (2 * sqrt_t) + risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * (1 - nd2)
        rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * (1 - nd2)
    
    # Greeks that are the same for both calls and puts
    gamma = phi_d1 / (price * volatility * sqrt_t)
    vega = price * sqrt_t * phi_d1 / 100  # Divided by 100 to express as change per 1% change in vol
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta / 365,  # Express theta as daily decay
        'vega': vega,
        'rho': rho / 100  # Express rho as change per 1% change in interest rates
    } 