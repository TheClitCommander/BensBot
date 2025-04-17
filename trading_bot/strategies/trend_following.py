"""
Trend Following Strategy.

This module implements a trend following strategy based on moving average crossovers.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger("trend_following")

class TrendFollowingStrategy:
    def __init__(self, params=None):
        self.params = params or {
            "fast_period": 20,
            "slow_period": 50,
            "atr_period": 14,
            "risk_per_trade": 0.01  # Risk 1% of portfolio per trade
        }
    
    def generate_signals(self, market_data, context):
        """Generate trend following signals based on moving average crossovers"""
        signals = []
        
        for symbol, data in market_data.items():
            # Calculate fast and slow moving averages
            fast_ma = self._calculate_ema(data['close'], self.params['fast_period'])
            slow_ma = self._calculate_ema(data['close'], self.params['slow_period'])
            atr = self._calculate_atr(data, self.params['atr_period'])
            
            # Current price and moving averages
            current_price = data['close'][-1]
            current_fast = fast_ma[-1]
            current_slow = slow_ma[-1]
            
            # Previous values
            prev_fast = fast_ma[-2]
            prev_slow = slow_ma[-2]
            
            # Entry conditions - MA crossovers
            if prev_fast <= prev_slow and current_fast > current_slow:
                # Bullish crossover - generate long signal
                stop_loss = current_price - (atr[-1] * 2)
                target = current_price + (atr[-1] * 3)  # 1.5:1 reward-risk
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'long',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'risk_amount': current_price - stop_loss,
                    'signal_type': 'trend_following',
                    'confidence': self._calculate_confidence(data, context, 'long')
                })
            
            elif prev_fast >= prev_slow and current_fast < current_slow:
                # Bearish crossunder - generate short signal
                stop_loss = current_price + (atr[-1] * 2)
                target = current_price - (atr[-1] * 3)  # 1.5:1 reward-risk
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'short',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'risk_amount': stop_loss - current_price,
                    'signal_type': 'trend_following',
                    'confidence': self._calculate_confidence(data, context, 'short')
                })
        
        return signals
    
    def calculate_position_size(self, signal, portfolio_value):
        """Calculate position size based on risk per trade"""
        risk_amount = signal['risk_amount']
        dollar_risk = portfolio_value * self.params['risk_per_trade']
        
        # Position size = Dollar risk / Risk amount per share
        return dollar_risk / risk_amount if risk_amount > 0 else 0
    
    def _calculate_ema(self, prices, period):
        # Implementation of Exponential Moving Average
        if len(prices) < period:
            return [prices[-1]] * len(prices)
        
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        
        for i in range(period, len(prices)):
            ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
            
        # Pad with initial EMA values to match input length
        return [ema[0]] * (len(prices) - len(ema)) + ema
    
    def _calculate_atr(self, data, period):
        # Implementation of Average True Range
        highs = data['high']
        lows = data['low']
        closes = data['close']
        
        tr_values = []
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr_values.append(max(tr1, tr2, tr3))
        
        # Calculate ATR
        atr_values = [sum(tr_values[:period]) / period]
        for i in range(period, len(tr_values)):
            atr_values.append((atr_values[-1] * (period-1) + tr_values[i]) / period)
        
        # Pad beginning to match input length
        return [atr_values[0]] * (len(closes) - len(atr_values)) + atr_values
    
    def _calculate_confidence(self, data, context, direction):
        # Base confidence
        confidence = 0.5
        
        # Adjust based on trend strength from context
        trend_strength = context.get('trend_strength', 0.5)
        if direction == 'long':
            confidence += (trend_strength - 0.5) * 0.2
        else:
            confidence += (0.5 - trend_strength) * 0.2
        
        # Adjust based on market regime
        market_regime = context.get('market_regime', 'neutral')
        if direction == 'long' and market_regime == 'bullish':
            confidence += 0.1
        elif direction == 'short' and market_regime == 'bearish':
            confidence += 0.1
        elif (direction == 'long' and market_regime == 'bearish') or \
             (direction == 'short' and market_regime == 'bullish'):
            confidence -= 0.1
        
        # Adjust based on volume confirmation
        volume = data['volume']
        avg_volume = sum(volume[-5:]) / 5
        if volume[-1] > avg_volume * 1.2:
            confidence += 0.1
        
        # Ensure confidence is between 0.1 and 0.9
        return max(0.1, min(0.9, confidence)) 