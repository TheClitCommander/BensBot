#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Evaluation Framework Configuration

This module defines the default configuration for the strategy evaluation framework.
"""

import os
from pathlib import Path

# Default configuration for the strategy evaluator
DEFAULT_CONFIG = {
    # Section 1: Evaluation Philosophy
    "evaluation_objectives": {
        "signal_quality_weight": 0.3,     # 30% weight for signal quality
        "execution_quality_weight": 0.2,  # 20% weight for execution quality
        "risk_control_weight": 0.3,       # 30% weight for risk control
        "operational_reliability_weight": 0.2  # 20% weight for operational reliability
    },
    
    # Section 2: Test Universes & Timeframes
    "test_universes": {
        "backtest": {
            "min_history_years": 3,          # Minimum 3 years of backtest data
            "market_regimes_required": ["bull", "bear", "sideways"],
            "min_data_quality": 0.95         # Minimum 95% data quality
        },
        "paper_trading": {
            "min_duration_months": 3,        # Minimum 3 months of paper trading
            "min_trades": 30                 # Minimum 30 trades in paper trading
        },
        "live_trading": {
            "initial_allocation_pct": 0.05,   # Start with 5% of capital
            "scale_up_threshold_sharpe": 1.5, # Scale up when Sharpe > 1.5
            "max_allocation_pct": 0.5,        # Maximum 50% allocation to a single strategy
            "min_live_period_days": 30        # Minimum 30 days in live trading
        }
    },
    
    # Section 3: Aggregate Performance Metrics
    "performance_thresholds": {
        "min_sharpe_ratio": 1.0,       # Minimum acceptable Sharpe ratio
        "min_sortino_ratio": 1.2,      # Minimum acceptable Sortino ratio
        "min_profit_factor": 1.5,      # Minimum acceptable profit factor
        "max_drawdown_pct": 0.15,      # Maximum acceptable drawdown (15%)
        "min_calmar_ratio": 0.8,       # Minimum acceptable Calmar ratio (return/max drawdown)
        "max_daily_var_95": 0.02,      # Maximum acceptable 95% daily VaR (2%)
        "min_win_rate": 0.45,          # Minimum acceptable win rate (45%)
        "min_profit_to_loss": 1.5,     # Minimum profit to loss ratio
        "max_turnover_annual": 20,     # Maximum annual turnover (20x)
        "min_sharpe_vs_benchmark": 0.3 # Minimum outperformance vs benchmark
    },
    
    # Section 4: Module-Level Signal Quality
    "signal_quality": {
        "min_win_rate": {
            "swing_trading": 0.50,      # Min win rate for swing trading
            "day_trading": 0.45,        # Min win rate for day trading
            "scalping": 0.40,           # Min win rate for scalping
            "trend_following": 0.40,    # Min win rate for trend following
            "mean_reversion": 0.55,     # Min win rate for mean reversion
            "breakout": 0.45            # Min win rate for breakout
        },
        "min_avg_rr": {                 # Min risk-reward ratio
            "swing_trading": 1.5,
            "day_trading": 1.3,
            "scalping": 1.0,
            "trend_following": 2.0,
            "mean_reversion": 1.2,
            "breakout": 1.5
        },
        "max_false_alarm_rate": 0.2,    # Maximum false alarm rate 
        "max_signal_latency_ms": 500,   # Maximum signal latency in ms
        "max_overlap_correlation": 0.7  # Maximum correlation between strategy signals
    },
    
    # Section 5: Execution & Slippage Analysis
    "execution_quality": {
        "min_fill_rate": 0.85,           # Minimum 85% of orders filled
        "max_avg_slippage_bps": {        # Maximum average slippage in basis points
            "stocks": 5,
            "futures": 3, 
            "forex": 1,
            "options": 10
        },
        "max_signal_to_order_ms": 150,   # Maximum signal to order latency in ms
        "max_order_to_fill_ms": 250,     # Maximum order to fill latency in ms
        "min_limit_order_fill_rate": 0.7 # Minimum fill rate for limit orders
    },
    
    # Section 6: Risk Control Verification
    "risk_control": {
        "max_per_trade_risk_pct": 0.01,     # Maximum 1% risk per trade
        "max_portfolio_risk_pct": 0.05,     # Maximum 5% portfolio risk
        "daily_drawdown_limit_pct": 0.03,   # 3% daily drawdown limit
        "weekly_drawdown_limit_pct": 0.07,  # 7% weekly drawdown limit
        "monthly_drawdown_limit_pct": 0.15, # 15% monthly drawdown limit
        "max_correlated_exposure": 0.2,     # Maximum 20% exposure to correlated assets
        "stress_test_scenarios": [
            "double_spreads",              # Test with doubled spreads
            "latency_2x",                  # Test with doubled latency
            "gap_open_5pct",               # Test with 5% gap open
            "liquidity_half"               # Test with halved liquidity
        ]
    },
    
    # Section 7: Parameter Stability & Walk-Forward
    "parameter_stability": {
        "optimization_frequency": "quarterly",  # Re-optimize quarterly
        "in_sample_window": "1y",             # 1 year in-sample window
        "out_sample_window": "6m",            # 6 month out-of-sample window
        "max_parameter_drift_pct": 0.3,        # Maximum 30% parameter drift
        "max_performance_degradation": 0.25,   # Maximum 25% performance degradation
        "min_robustness_ratio": 0.7,           # Min ratio of out-of-sample to in-sample performance
        "walk_forward_efficiency_min": 0.6     # Minimum walk-forward efficiency
    },
    
    # Section 8: Robustness & Sensitivity
    "robustness": {
        "parameter_sensitivity_range": 0.15,   # Test parameters ±15%
        "min_sensitivity_score": 0.7,          # Minimum sensitivity score
        "scenario_tests": [
            "vol_spike_2x",                   # 2x volatility spike
            "vol_collapse_half",              # 50% volatility reduction
            "correlation_breakdown",          # Correlation breakdown
            "liquidity_crisis",               # Liquidity crisis
            "flash_crash"                      # Flash crash scenario
        ],
        "module_knockout_threshold": 0.4,      # Max 40% degradation on module removal
        "min_monte_carlo_confidence": 0.8     # Minimum Monte Carlo simulation confidence
    },
    
    # Section 9: Operational Resilience
    "operational_resilience": {
        "min_uptime_pct": 0.995,              # 99.5% minimum system uptime
        "max_error_rate": 0.001,              # Maximum 0.1% error rate
        "max_mttr_minutes": 15,               # Mean time to recover: 15 minutes
        "max_api_failure_rate": 0.01,         # Maximum API failure rate: 1%
        "failsafe_test_frequency": "weekly",   # Test failsafe mechanisms weekly
        "max_data_latency_ms": 250,           # Maximum data latency: 250ms
        "max_processing_time_ms": 500,        # Maximum processing time: 500ms
        "min_backup_success_rate": 0.99       # Minimum backup success rate: 99%
    },
    
    # Section 10: Continuous Monitoring & Governance
    "monitoring": {
        "dashboard_refresh_seconds": 60,       # Dashboard refresh rate: 60 seconds
        "alert_thresholds": {
            "slippage_spike_bps": 10,          # Alert on 10bps slippage spike
            "strategy_underperformance_days": 5, # Alert after 5 days underperformance
            "error_rate_threshold": 0.005,     # Alert on 0.5% error rate
            "drawdown_alert_pct": 0.08,        # Alert on 8% drawdown
            "execution_latency_ms": 500        # Alert on 500ms execution latency
        },
        "review_cadence": {
            "performance_snapshot": "daily",   # Daily performance snapshot
            "detailed_performance": "weekly",  # Weekly detailed performance review
            "risk_review": "weekly",           # Weekly risk review
            "full_strategy_review": "monthly", # Monthly full strategy review
            "governance_review": "quarterly"   # Quarterly governance review
        },
        "model_retraining_triggers": {
            "signal_accuracy_threshold": 0.85,  # Retrain if accuracy < 85%
            "slippage_threshold_bps": 8,        # Retrain if slippage > 8bps
            "win_rate_decay_pct": 0.15,         # Retrain if win rate decays 15%
            "profit_factor_threshold": 1.2,     # Retrain if profit factor < 1.2
            "max_days_without_retraining": 90   # Maximum 90 days without retraining
        }
    }
}

# Path to save default configuration
DEFAULT_CONFIG_PATH = os.path.join(
    Path(__file__).parent.absolute(),
    "default_evaluation_config.json"
)

def get_default_config():
    """
    Get the default evaluation configuration.
    
    Returns:
        Dict containing the default configuration
    """
    return DEFAULT_CONFIG.copy()

def save_default_config():
    """
    Save the default configuration to a file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    
    try:
        with open(DEFAULT_CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving default configuration: {e}")
        return False

if __name__ == "__main__":
    # Save the default configuration when this module is run directly
    save_default_config()
    print(f"Default configuration saved to: {DEFAULT_CONFIG_PATH}") 