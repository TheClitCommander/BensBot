#!/usr/bin/env python3
"""
Test script for Advanced Market Regime Detector

This standalone script tests the main functionality of the AdvancedRegimeDetector
without relying on other modules from the trading_bot package.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Import the advanced regime detector
sys.path.insert(0, str(Path(__file__).parent))
from trading_bot.backtesting.advanced_regime_detector import (
    AdvancedRegimeDetector,
    VolatilityRegime,
    CorrelationRegime,
    SectorRotationPhase
)

def generate_test_data():
    """Generate synthetic market data for testing"""
    # Create date ranges
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)  # 90 days of history
    
    daily_dates = pd.date_range(start=start_date, end=end_date, freq='B')
    weekly_dates = pd.date_range(start=start_date, end=end_date, freq='W-FRI')
    
    # List of symbols to include
    symbols = ['SPY', 'QQQ', 'XLK', 'XLF', 'XLV', 'XLE', 'GLD']
    
    # Initialize data containers
    daily_data = []
    weekly_data = []
    
    # Generate price data for SPY (benchmark)
    np.random.seed(42)  # For reproducibility
    spy_daily_returns = np.random.normal(0.0005, 0.01, size=len(daily_dates))
    spy_daily_prices = 100 * np.cumprod(1 + spy_daily_returns)
    
    # Correlation coefficients for the test
    correlations = {
        'QQQ': 0.9,
        'XLK': 0.85,
        'XLF': 0.7,
        'XLV': 0.5,
        'XLE': 0.3,
        'GLD': -0.2
    }
    
    # Generate data for each symbol
    for symbol in symbols:
        # For SPY, use the base series
        if symbol == 'SPY':
            price_series = spy_daily_prices
        else:
            # Generate correlated returns
            correlation = correlations.get(symbol, 0.5)
            independent_returns = np.random.normal(0.0003, 0.012, size=len(daily_dates))
            correlated_returns = (correlation * spy_daily_returns + 
                                 np.sqrt(1 - correlation**2) * independent_returns)
            
            # Convert returns to prices
            price_series = 100 * np.cumprod(1 + correlated_returns)
        
        # Create daily data entries
        for i, date in enumerate(daily_dates):
            daily_data.append({
                'date': date,
                'symbol': symbol,
                'close': price_series[i],
                'volume': np.random.randint(100000, 10000000)
            })
        
        # Create weekly data (use Friday's values)
        weekly_indices = [i for i, date in enumerate(daily_dates) if date.dayofweek == 4 and date in weekly_dates]
        for i in weekly_indices:
            if i < len(price_series):
                weekly_data.append({
                    'date': daily_dates[i],
                    'symbol': symbol,
                    'close': price_series[i],
                    'volume': np.random.randint(500000, 50000000)
                })
    
    # Convert to DataFrames
    daily_df = pd.DataFrame(daily_data)
    weekly_df = pd.DataFrame(weekly_data)
    
    # Create a dictionary mapping timeframes to price DataFrames
    data_by_timeframe = {
        'daily': daily_df,
        'weekly': weekly_df
    }
    
    print(f"Generated test data with {len(daily_df)} daily rows and {len(weekly_df)} weekly rows")
    return data_by_timeframe

def test_advanced_regime_detector():
    """Run basic tests for the AdvancedRegimeDetector"""
    # Generate test data
    print("Step 1: Generating test data...")
    market_data = generate_test_data()
    
    # Create detector instance
    print("\nStep 2: Creating detector instance...")
    detector = AdvancedRegimeDetector(
        lookback_days=60,  # Shorter window for testing
        timeframes=['daily', 'weekly'],
        volatility_windows={'daily': 10, 'weekly': 4},
        trend_windows={'daily': 20, 'weekly': 8},
        correlation_window=15,
        num_regimes=4,
        regime_persistence=3
    )
    
    # Load market data
    print("\nStep 3: Loading market data...")
    detector.load_market_data_multi_timeframe(
        price_data_by_timeframe=market_data,
        symbol_col='symbol',
        date_col='date',
        price_col='close',
        volume_col='volume',
        benchmark_symbol='SPY'
    )
    
    # Compute features
    print("\nStep 4: Computing features...")
    features = detector.compute_features_multi_timeframe()
    print(f"Computed features for {list(features.keys())} timeframes")
    
    # Detect regimes
    print("\nStep 5: Detecting regimes...")
    regimes = detector.detect_regimes_multi_timeframe()
    print(f"Detected regimes for {list(regimes.keys())} timeframes")
    
    # Detect trend conflicts
    print("\nStep 6: Detecting trend conflicts...")
    conflicts = detector.detect_trend_conflicts()
    print(f"Found {len(conflicts)} trend conflict entries")
    
    # Classify volatility regimes
    print("\nStep 7: Classifying volatility regimes...")
    vol_regimes = detector.classify_volatility_regimes()
    print(f"Classified {len(vol_regimes)} volatility regime entries")
    
    # Detect correlation regimes
    print("\nStep 8: Detecting correlation regimes...")
    corr_regimes = detector.detect_correlation_regimes()
    print(f"Detected correlation regimes for {len(corr_regimes.columns)//2} asset classes")
    
    # Analyze sector rotation
    print("\nStep 9: Analyzing sector rotation...")
    rotation = detector.analyze_sector_rotation()
    print(f"Generated {len(rotation)} sector rotation entries")
    
    # Run full analysis
    print("\nStep 10: Running full analysis...")
    analysis = detector.run_full_analysis()
    
    # Print results summary
    print("\n===== ANALYSIS RESULTS =====")
    
    if 'primary_regime' in analysis:
        regime_info = analysis['primary_regime']
        print(f"\nPrimary Regime: {regime_info.get('label', 'Unknown')} (#{regime_info.get('regime', 'Unknown')})")
    
    if 'trend_conflicts' in analysis:
        conflict_info = analysis['trend_conflicts']
        print(f"\nTrend Conflict Status: {conflict_info.get('status', 'unknown')}")
    
    if 'volatility_regime' in analysis:
        vol_info = analysis['volatility_regime']
        print(f"\nCurrent Volatility Regime: {vol_info.get('current', 'Unknown')}")
    
    if 'correlation_regimes' in analysis and 'current' in analysis['correlation_regimes']:
        print("\nCorrelation Regimes:")
        for asset, regime in analysis['correlation_regimes']['current'].items():
            print(f"  - {asset}: {regime}")
    
    if 'sector_rotation' in analysis:
        rotation_info = analysis['sector_rotation']
        print(f"\nSector Rotation Phase: {rotation_info.get('current_phase', 'Unknown')}")
        top_sectors = rotation_info.get('top_sectors', [])
        if top_sectors:
            print(f"Top Sectors: {', '.join(top_sectors)}")
    
    if 'actionable_insights' in analysis:
        insights = analysis['actionable_insights']
        print("\nActionable Insights:")
        for insight in insights:
            print(f"  - {insight.get('type', 'unknown')}: {insight.get('description', '')}")
            print(f"    Recommendation: {insight.get('recommendation', '')}")
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    test_advanced_regime_detector() 