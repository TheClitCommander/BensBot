"""
Mean Reversion Strategy.

This module implements a mean reversion trading strategy using Bollinger Bands and RSI.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger("mean_reversion")

class MeanReversionStrategy:
    def __init__(self, params=None):
        self.params = params or {
            "bollinger_period": 20,
            "bollinger_std": 2.0,
            "min_mean_distance": 1.5,  # Minimum distance from mean in std devs
            "rsi_period": 5,
            "risk_per_trade": 0.01  # Risk 1% of portfolio per trade
        }
    
    def generate_signals(self, market_data, context):
        """Generate mean reversion signals based on Bollinger Bands and RSI"""
        signals = []
        
        for symbol, data in market_data.items():
            # Calculate indicators
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                data['close'], 
                self.params['bollinger_period'], 
                self.params['bollinger_std']
            )
            rsi = self._calculate_rsi(data['close'], self.params['rsi_period'])
            
            # Current price
            current_price = data['close'][-1]
            
            # Volatility for stop loss calculation
            atr = self._calculate_atr(data, 14)
            
            # Calculate distance from mean in standard deviations
            std_dev = (bb_upper[-1] - bb_middle[-1]) / self.params['bollinger_std']
            upper_distance = (current_price - bb_middle[-1]) / std_dev
            lower_distance = (bb_middle[-1] - current_price) / std_dev
            
            # Long signal when price is below lower band by min_mean_distance
            if lower_distance >= self.params['min_mean_distance'] and rsi[-1] < 30:
                # Generate long signal
                stop_loss = current_price - (atr[-1] * 1.5)  # Tighter stop for mean reversion
                target = bb_middle[-1]  # Target the mean
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'long',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'risk_amount': current_price - stop_loss,
                    'signal_type': 'mean_reversion',
                    'confidence': self._calculate_confidence(upper_distance, lower_distance, rsi[-1], context, 'long')
                })
            
            # Short signal when price is above upper band by min_mean_distance
            elif upper_distance >= self.params['min_mean_distance'] and rsi[-1] > 70:
                # Generate short signal
                stop_loss = current_price + (atr[-1] * 1.5)  # Tighter stop for mean reversion
                target = bb_middle[-1]  # Target the mean
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'short',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'risk_amount': stop_loss - current_price,
                    'signal_type': 'mean_reversion',
                    'confidence': self._calculate_confidence(upper_distance, lower_distance, rsi[-1], context, 'short')
                })
        
        return signals
    
    def calculate_position_size(self, signal, portfolio_value):
        """Calculate position size based on risk per trade"""
        risk_amount = signal['risk_amount']
        dollar_risk = portfolio_value * self.params['risk_per_trade']
        
        # For mean reversion, use slightly less risk (shorter-term trades)
        dollar_risk *= 0.8
        
        # Position size = Dollar risk / Risk amount per share
        return dollar_risk / risk_amount if risk_amount > 0 else 0
    
    def _calculate_bollinger_bands(self, prices, period, num_std):
        # Calculate moving average
        ma = [sum(prices[max(0, i-period+1):i+1]) / min(i+1, period) for i in range(len(prices))]
        
        # Calculate standard deviation
        std = []
        for i in range(len(prices)):
            if i < period - 1:
                std.append(0)
            else:
                period_prices = prices[i-(period-1):i+1]
                std.append(self._calculate_std_dev(period_prices, ma[i]))
        
        # Calculate upper and lower bands
        upper_band = [ma[i] + num_std * std[i] for i in range(len(prices))]
        lower_band = [ma[i] - num_std * std[i] for i in range(len(prices))]
        
        return upper_band, ma, lower_band
    
    def _calculate_std_dev(self, values, mean):
        # Standard deviation calculation
        return (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
    
    def _calculate_rsi(self, prices, period):
        # Implementation of Relative Strength Index
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # First average
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Subsequent averages
        rsi_values = []
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
        
        # Pad beginning to match input length
        return [rsi_values[0]] * (len(prices) - len(rsi_values)) + rsi_values
    
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
    
    def _calculate_confidence(self, upper_distance, lower_distance, rsi, context, direction):
        # Base confidence
        confidence = 0.5
        
        # Adjust based on distance from mean
        if direction == 'long':
            # Stronger signal when more oversold
            confidence += min(lower_distance / 4, 0.2)
            confidence += (30 - min(rsi, 30)) / 30 * 0.2
        else:
            # Stronger signal when more overbought
            confidence += min(upper_distance / 4, 0.2)
            confidence += (max(rsi, 70) - 70) / 30 * 0.2
        
        # Adjust based on market regime - mean reversion works best in sideways markets
        market_regime = context.get('market_regime', 'neutral')
        if market_regime == 'neutral' or market_regime == 'sideways':
            confidence += 0.1
        elif (direction == 'long' and market_regime == 'bearish') or \
             (direction == 'short' and market_regime == 'bullish'):
            confidence -= 0.15
        
        # Ensure confidence is between 0.1 and 0.9
        return max(0.1, min(0.9, confidence)) 