#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iron Condor Strategy

A professional-grade iron condor implementation that leverages the modular,
event-driven architecture. This strategy is designed to collect premium in 
range-bound markets with defined risk and reward.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from trading_bot.data.data_pipeline import DataPipeline
from trading_bot.core.events import Event, EventType, EventBus
from trading_bot.strategies_new.options.base.options_base_strategy import OptionsSession
from trading_bot.strategies_new.options.base.spread_types import OptionType
from trading_bot.strategies_new.options.base.complex_spread_engine import ComplexSpreadEngine
from trading_bot.strategies_new.factory.registry import register_strategy

# Configure logging
logger = logging.getLogger(__name__)

@register_strategy(
    name="IronCondorStrategy",
    market_type="options",
    description="A market-neutral strategy that combines a bull put spread and a bear call spread to profit from time decay when the underlying security remains within a defined range",
    timeframes=["1d", "1w"],
    parameters={
        "call_spread_delta_short": {"description": "Target delta for short call (OTM)", "type": "float"},
        "put_spread_delta_short": {"description": "Target delta for short put (OTM)", "type": "float"},
        "wing_width_pct": {"description": "Width of each spread as % of underlying price", "type": "float"},
        "min_range_score": {"description": "Minimum range-bound market score (0-100)", "type": "float"}
    }
)
class IronCondorStrategy(ComplexSpreadEngine):
    """
    Iron Condor Strategy
    
    This strategy combines a bull put spread and a bear call spread to create a 
    market-neutral position that profits from time decay when the underlying 
    security remains within a defined range.
    
    Features:
    - Adapts the legacy Iron Condor implementation to the new architecture
    - Uses event-driven signal generation and position management
    - Leverages the ComplexSpreadEngine for core multi-leg spread mechanics
    - Implements custom filtering and range-bound market condition analysis
    """
    
    def __init__(self, session: OptionsSession, data_pipeline: DataPipeline, 
                 parameters: Dict[str, Any] = None):
        """
        Initialize the Iron Condor strategy.
        
        Args:
            session: Options trading session
            data_pipeline: Data processing pipeline
            parameters: Strategy parameters (will override defaults)
        """
        # Initialize base engine
        super().__init__(session, data_pipeline, parameters)
        
        # Strategy-specific default parameters
        default_params = {
            # Strategy identification
            'strategy_name': 'Iron Condor',
            'strategy_id': 'iron_condor',
            
            # Market condition preferences
            'prefer_high_iv': True,        # Iron condors benefit from high IV
            'min_iv_percentile': 60,       # Minimum IV percentile to enter
            'max_iv_percentile': 90,       # Maximum IV percentile to enter
            'min_range_score': 65,         # Minimum range-bound score (0-100)
            
            # Spread construction parameters
            'call_spread_delta_short': 0.16,  # Target delta for short call (OTM)
            'call_spread_delta_long': 0.08,   # Target delta for long call (further OTM)
            'put_spread_delta_short': 0.16,   # Target delta for short put (OTM) - absolute value
            'put_spread_delta_long': 0.08,    # Target delta for long put (further OTM) - absolute value
            'wing_width_pct': 5,              # Width of each spread as % of underlying price
            
            # Risk parameters
            'max_risk_per_trade_pct': 3.0,    # Max risk as % of account
            'target_profit_pct': 50,          # Target profit as % of max credit
            'stop_loss_pct': 200,             # Stop loss as % of credit (e.g., 200% = 2x initial credit)
            'max_positions': 2,               # Maximum concurrent positions
            'min_credit_to_max_loss': 0.20,   # Minimum credit as % of max loss
            
            # Trade management
            'days_to_expiry_exit': 7,         # Exit N days before expiration
            'manage_winners_pct': 50,         # Take profit when P&L reaches this % of max profit
        }
        
        # Update with default parameters for Iron Condors
        for key, value in default_params.items():
            if key not in self.parameters:
                self.parameters[key] = value
        
        # Register for market events
        self.register_events()
        
        logger.info(f"Initialized Iron Condor Strategy for {session.symbol}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators for the Iron Condor strategy.
        
        Args:
            data: Market data DataFrame with OHLCV columns
            
        Returns:
            Dictionary of calculated indicators
        """
        # Get base indicators from parent class
        indicators = super().calculate_indicators(data)
        
        if data.empty or len(data) < 50:
            return indicators
        
        # Calculate specific indicators for range-bound market assessment
        
        # Bollinger Band Width as volatility indicator
        if 'ma_20' not in indicators:
            indicators['ma_20'] = data['close'].rolling(window=20).mean()
        
        std_20 = data['close'].rolling(window=20).std()
        upper_band = indicators['ma_20'] + (std_20 * 2)
        lower_band = indicators['ma_20'] - (std_20 * 2)
        indicators['bb_width_pct'] = (upper_band - lower_band) / indicators['ma_20'] * 100
        
        # Calculate historical price range
        if len(data) >= 20:
            # 20-day high-low range as % of current price
            high_20d = data['high'].rolling(window=20).max()
            low_20d = data['low'].rolling(window=20).min()
            current_price = data['close'].iloc[-1]
            
            range_pct = (high_20d - low_20d) / current_price * 100
            indicators['price_range_20d_pct'] = range_pct
        
        # Calculate ADX for trend strength (lower is better for range-bound strategies)
        if 'adx' not in indicators:
            # Calculate DI+, DI-, and ADX
            high = data['high']
            low = data['low']
            close = data['close']
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr14 = tr.rolling(window=14).mean()
            
            # Plus Directional Movement
            plus_dm = high.diff()
            plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > -low.diff()), 0)
            
            # Minus Directional Movement
            minus_dm = low.shift(1) - low
            minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > high - high.shift(1)), 0)
            
            # Directional Indicators
            plus_di14 = 100 * (plus_dm.rolling(window=14).sum() / atr14.rolling(window=14).sum())
            minus_di14 = 100 * (minus_dm.rolling(window=14).sum() / atr14.rolling(window=14).sum())
            
            # Directional Index
            dx = 100 * abs(plus_di14 - minus_di14) / (plus_di14 + minus_di14)
            
            # Average Directional Index
            indicators['adx'] = dx.rolling(window=14).mean()
        
        # Calculate range-bound score (0-100)
        if len(data) >= 50:
            range_score = 50  # Start neutral
            
            # ADX - lower is better for range-bound markets
            if 'adx' in indicators:
                adx = indicators['adx'].iloc[-1]
                
                if adx < 20:  # Weak trend - good for range-bound strategies
                    range_score += 20
                elif adx < 30:
                    range_score += 10
                elif adx > 40:  # Strong trend - bad for range-bound strategies
                    range_score -= 20
            
            # Bollinger Band Width - narrower bands suggest range-bound market
            if 'bb_width_pct' in indicators:
                bb_width = indicators['bb_width_pct'].iloc[-1]
                
                if bb_width < 4:  # Narrow bands - good for range bound
                    range_score += 15
                elif bb_width > 8:  # Wide bands - more volatile
                    range_score -= 10
            
            # Price location within its recent range
            if 'price_range_20d_pct' in indicators:
                current_price = data['close'].iloc[-1]
                high_20d = data['high'].rolling(window=20).max().iloc[-1]
                low_20d = data['low'].rolling(window=20).min().iloc[-1]
                
                # Percentage of where price is in the range (0% = at low, 100% = at high)
                price_in_range_pct = (current_price - low_20d) / (high_20d - low_20d) * 100
                
                # Best for Iron Condor when price is in middle of range (40-60%)
                if 40 <= price_in_range_pct <= 60:
                    range_score += 15
                elif (30 <= price_in_range_pct < 40) or (60 < price_in_range_pct <= 70):
                    range_score += 5
                elif price_in_range_pct < 20 or price_in_range_pct > 80:
                    range_score -= 10  # Price near extremes of range
            
            # Historical price action (standard deviation of returns)
            if len(data) >= 50:
                returns = data['close'].pct_change()
                returns_std = returns.std() * 100  # As percentage
                
                if returns_std < 1.5:  # Low daily volatility - good for range bound
                    range_score += 10
                elif returns_std > 3.0:  # High daily volatility - may break range
                    range_score -= 10
            
            # Ensure score is within 0-100 range
            range_score = max(0, min(100, range_score))
            indicators['range_bound_score'] = range_score
        
        return indicators
    
    def generate_signals(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signals for Iron Condors based on market conditions.
        
        Args:
            data: Market data DataFrame
            indicators: Pre-calculated indicators
            
        Returns:
            Dictionary of trading signals
        """
        signals = {
            "entry": False,
            "exit_positions": [],
            "signal_strength": 0.0
        }
        
        if data.empty or not indicators:
            return signals
        
        # Check if we already have too many positions
        if len(self.positions) >= self.parameters['max_positions']:
            logger.info("Maximum number of positions reached, no new entries.")
            # Still check for exits
        else:
            # Check IV environment
            iv_check_passed = True
            if self.session.current_iv is not None and self.session.symbol in self.iv_history:
                iv_metrics = self.calculate_implied_volatility_metrics(self.iv_history[self.session.symbol])
                iv_percentile = iv_metrics.get('iv_percentile', 50)
                
                min_iv = self.parameters['min_iv_percentile']
                max_iv = self.parameters['max_iv_percentile']
                
                if iv_percentile < min_iv:
                    iv_check_passed = False
                    logger.info(f"IV filter failed: current IV percentile {iv_percentile:.2f} below min {min_iv}")
                elif iv_percentile > max_iv:
                    iv_check_passed = False
                    logger.info(f"IV filter failed: current IV percentile {iv_percentile:.2f} above max {max_iv}")
            
            # Check range-bound score
            if 'range_bound_score' in indicators and iv_check_passed:
                range_score = indicators['range_bound_score']
                min_score = self.parameters['min_range_score']
                
                if range_score >= min_score:
                    # Generate entry signal
                    signals["entry"] = True
                    signals["signal_strength"] = range_score / 100.0
                    logger.info(f"Iron Condor entry signal: range score {range_score}, strength {signals['signal_strength']:.2f}")
                else:
                    logger.info(f"Range-bound score {range_score} below threshold {min_score}")
        
        # Check for exits on existing positions
        for position in self.positions:
            if position.status == "open":
                exit_signal = self._check_exit_conditions(position, data, indicators)
                if exit_signal:
                    signals["exit_positions"].append(position.position_id)
        
        return signals
    
    def _check_exit_conditions(self, position, data: pd.DataFrame, indicators: Dict[str, Any]) -> bool:
        """
        Check exit conditions for an open position.
        
        Args:
            position: The position to check
            data: Market data DataFrame
            indicators: Pre-calculated indicators
            
        Returns:
            Boolean indicating whether to exit
        """
        # Get current market data
        if data.empty:
            return False
        
        current_price = data['close'].iloc[-1]
        
        # Check if range-bound conditions have deteriorated
        if 'range_bound_score' in indicators:
            range_score = indicators['range_bound_score']
            if range_score < 40:  # Market no longer range-bound
                logger.info(f"Exit signal: range score dropped to {range_score}")
                return True
        
        # Check if ADX is increasing (market developing a trend)
        if 'adx' in indicators:
            adx = indicators['adx'].iloc[-1]
            adx_5_ago = indicators['adx'].iloc[-6] if len(indicators['adx']) > 5 else indicators['adx'].iloc[0]
            
            if adx > 30 and adx > adx_5_ago * 1.2:  # ADX increasing by more than 20%
                logger.info(f"Exit signal: ADX increasing ({adx_5_ago:.1f} to {adx:.1f}), trend developing")
                return True
        
        # Check if price is approaching short strikes
        # In a real implementation, would check actual option prices and Greeks
        
        # Days to expiration check
        if hasattr(position, 'call_spread') and 'expiration' in position.call_spread:
            expiry_date = position.call_spread.get('expiration')
            if isinstance(expiry_date, str):
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            
            days_to_expiry = (expiry_date - datetime.now().date()).days
            if days_to_expiry <= self.parameters['days_to_expiry_exit']:
                logger.info(f"Exit signal: approaching expiration ({days_to_expiry} days left)")
                return True
        
        # Profit target and stop loss are handled by the base ComplexSpreadEngine
        
        return False
    
    def filter_option_chains(self, option_chain: pd.DataFrame) -> pd.DataFrame:
        """
        Apply custom filters for Iron Condor option selection.
        
        Args:
            option_chain: Option chain data
            
        Returns:
            Filtered option chain
        """
        # Apply base filters first
        filtered_chain = super().filter_option_chains(option_chain)
        
        if filtered_chain is None or filtered_chain.empty:
            return filtered_chain
        
        # Additional filters specific to Iron Condors
        
        # We need good liquidity for all four legs
        if 'open_interest' in filtered_chain.columns and 'volume' in filtered_chain.columns:
            min_oi = 100
            min_volume = 10
            filtered_chain = filtered_chain[
                (filtered_chain['open_interest'] >= min_oi) |
                (filtered_chain['volume'] >= min_volume)
            ]
        
        # Filter for delta values appropriate for Iron Condor legs
        if 'delta' in filtered_chain.columns:
            call_short_delta = self.parameters['call_spread_delta_short']
            call_long_delta = self.parameters['call_spread_delta_long']
            put_short_delta = self.parameters['put_spread_delta_short']
            put_long_delta = self.parameters['put_spread_delta_long']
            
            # Delta tolerance - allow slight variation around target values
            delta_tolerance = 0.05
            
            # For calls, filter options that match our delta targets
            call_short_filter = (
                (filtered_chain['option_type'] == 'call') & 
                (filtered_chain['delta'] >= call_short_delta - delta_tolerance) & 
                (filtered_chain['delta'] <= call_short_delta + delta_tolerance)
            )
            
            call_long_filter = (
                (filtered_chain['option_type'] == 'call') & 
                (filtered_chain['delta'] >= call_long_delta - delta_tolerance) & 
                (filtered_chain['delta'] <= call_long_delta + delta_tolerance)
            )
            
            # For puts, filter options that match our delta targets (puts have negative delta)
            put_short_filter = (
                (filtered_chain['option_type'] == 'put') & 
                (filtered_chain['delta'].abs() >= put_short_delta - delta_tolerance) & 
                (filtered_chain['delta'].abs() <= put_short_delta + delta_tolerance)
            )
            
            put_long_filter = (
                (filtered_chain['option_type'] == 'put') & 
                (filtered_chain['delta'].abs() >= put_long_delta - delta_tolerance) & 
                (filtered_chain['delta'].abs() <= put_long_delta + delta_tolerance)
            )
            
            # Combine all filters
            filtered_chain = filtered_chain[
                call_short_filter | call_long_filter | put_short_filter | put_long_filter
            ]
        
        return filtered_chain
    
    def construct_iron_condor(self, option_chain: pd.DataFrame, underlying_price: float) -> Optional[Dict]:
        """
        Construct an Iron Condor position from the option chain.
        
        Args:
            option_chain: Filtered option chain data
            underlying_price: Current price of the underlying asset
            
        Returns:
            Iron Condor position details or None if not possible
        """
        # Use the base complex spread engine method
        iron_condor = super().construct_iron_condor(option_chain, underlying_price)
        
        if iron_condor is None:
            logger.warning("Could not construct Iron Condor with given parameters")
            return None
        
        # Additional checks specific to this strategy
        
        # Calculate net credit as percentage of max loss
        max_loss = iron_condor['max_loss']
        net_credit = iron_condor['net_credit']
        
        if max_loss > 0 and net_credit > 0:
            credit_to_loss_ratio = net_credit / max_loss
            min_ratio = self.parameters['min_credit_to_max_loss']
            
            if credit_to_loss_ratio < min_ratio:
                logger.info(f"Iron Condor rejected: credit/loss ratio {credit_to_loss_ratio:.2f} below minimum {min_ratio:.2f}")
                return None
        
        return iron_condor
    
    def _execute_signals(self):
        """
        Execute Iron Condor specific trading signals.
        """
        # Use parent class for basic signal execution
        super()._execute_signals()
        
        # Add any Iron Condor specific execution logic here
    
    def register_events(self):
        """Register for events relevant to Iron Condors."""
        # Register for common event types from the parent class
        super().register_events()
        
        # Add any Iron Condor specific event subscriptions
        EventBus.subscribe(EventType.VOLATILITY_SPIKE, self.on_event)
        EventBus.subscribe(EventType.MARKET_REGIME_CHANGE, self.on_event)
    
    def on_event(self, event: Event):
        """
        Process incoming events for the Iron Condor strategy.
        
        Args:
            event: The event to process
        """
        # Let parent class handle common events first
        super().on_event(event)
        
        # Add additional Iron Condor specific event handling
        if event.type == EventType.VOLATILITY_SPIKE:
            spike_pct = event.data.get('percentage', 0)
            
            if spike_pct > 15:
                logger.info(f"Volatility spike of {spike_pct}% detected, adjusting Iron Condor parameters")
                # Widen our wings during volatility spikes
                self.parameters['call_spread_delta_short'] = max(0.10, self.parameters['call_spread_delta_short'] - 0.05)
                self.parameters['put_spread_delta_short'] = max(0.10, self.parameters['put_spread_delta_short'] - 0.05)
                
                # Consider closing existing positions during extreme volatility
                if spike_pct > 30:
                    logger.warning(f"Extreme volatility spike ({spike_pct}%), closing all Iron Condor positions")
                    for position in self.positions:
                        if position.status == "open":
                            self.spread_manager.close_position(position.position_id, "volatility_spike")
        
        elif event.type == EventType.MARKET_REGIME_CHANGE:
            new_regime = event.data.get('new_regime')
            
            if new_regime == 'trending':
                logger.info("Market regime changed to trending, reducing Iron Condor allocations")
                # Reduce position sizes during trending markets
                self.parameters['max_positions'] = max(1, self.parameters['max_positions'] - 1)
                
                # Increase our minimum range score requirement
                self.parameters['min_range_score'] = min(80, self.parameters['min_range_score'] + 10)
