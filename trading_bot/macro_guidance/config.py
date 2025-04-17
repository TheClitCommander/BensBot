"""
Macro Guidance Configuration

This module contains default configurations for the macro guidance engine.
"""

# Default configuration for macro guidance
DEFAULT_MACRO_CONFIG = {
    "enabled": True,
    "log_level": "INFO",
    "position_sizing": {
        "base_adjustment": 1.0,  # Multiplier for standard position size
        "event_adjustments": {
            "cpi": 0.7,  # Reduce position size to 70% before CPI
            "fomc": 0.6,  # Reduce position size to 60% before FOMC
            "jobs_report": 0.8,  # Reduce position size to 80% before jobs report
            "default": 0.8  # Default reduction for other major events
        },
        "vix_adjustments": {
            "above_20": 0.9,
            "above_25": 0.8,
            "above_30": 0.7,
            "above_40": 0.5
        },
        "regime_adjustments": {
            "expansion": 1.0,
            "late_cycle": 0.9,
            "contraction": 0.7,
            "early_recovery": 1.1,
            "unknown": 0.8
        }
    },
    "timeframe_adjustments": {
        "event_adjustments": {
            "cpi": "shorten by 20%",
            "fomc": "shorten by 30%",
            "jobs_report": "shorten by 15%"
        },
        "vix_adjustments": {
            "above_25": "shorten by 20%",
            "above_30": "shorten by 40%",
            "above_40": "shorten by 60%"
        }
    },
    "economic_calendar": {
        "source": "local",  # 'local' or 'api'
        "api_key": "",
        "update_frequency": "daily",
        "look_ahead_days": 14
    },
    "alert_settings": {
        "advance_notice": {
            "cpi": [48, 24, 2],  # Hours before event to alert
            "fomc": [72, 48, 24, 1],
            "jobs_report": [48, 24, 1],
            "default": [24]
        },
        "intraday_alerts": True,
        "vix_thresholds": [20, 25, 30, 40],  # VIX levels to trigger alerts
        "yield_curve_thresholds": [0.25, 0, -0.25, -0.5]  # 10Y-2Y spread thresholds
    },
    "priority_framework": {
        "highest_priority_events": ["fomc", "cpi", "jobs_report"],
        "moderate_priority_events": ["gdp", "vix_spike", "earnings_season"],
        "background_monitoring": ["yield_curve", "economic_regimes"]
    },
    "sector_sensitivities": {
        "technology": {
            "highly_sensitive_to": ["cpi", "fomc", "yield_curve"],
            "moderately_sensitive_to": ["jobs_report", "gdp"],
            "low_sensitivity_to": ["ppi", "retail_sales"]
        },
        "financials": {
            "highly_sensitive_to": ["fomc", "yield_curve", "jobs_report"],
            "moderately_sensitive_to": ["cpi", "gdp"],
            "low_sensitivity_to": ["retail_sales", "housing_data"]
        },
        "consumer_discretionary": {
            "highly_sensitive_to": ["jobs_report", "retail_sales", "consumer_confidence"],
            "moderately_sensitive_to": ["cpi", "gdp"],
            "low_sensitivity_to": ["manufacturing_data"]
        },
        "healthcare": {
            "highly_sensitive_to": ["healthcare_policy_changes"],
            "moderately_sensitive_to": ["gdp", "cpi"],
            "low_sensitivity_to": ["jobs_report", "manufacturing_data"]
        }
    },
    "regime_detection": {
        "indicators": {
            "leading_economic_index": {
                "weight": 0.25,
                "source": "conference_board",
                "expansion_threshold": 0.3,
                "contraction_threshold": -0.3
            },
            "yield_curve": {
                "weight": 0.2,
                "source": "treasury",
                "expansion_threshold": 0.5,
                "contraction_threshold": 0
            },
            "unemployment_trend": {
                "weight": 0.2,
                "source": "bls",
                "expansion_threshold": -0.2,
                "contraction_threshold": 0.2
            },
            "credit_spreads": {
                "weight": 0.15,
                "source": "fed",
                "expansion_threshold": -0.1,
                "contraction_threshold": 0.2
            },
            "inflation_trends": {
                "weight": 0.1,
                "source": "bls",
                "expansion_threshold": 0.2,
                "contraction_threshold": -0.2
            },
            "market_breadth": {
                "weight": 0.1,
                "source": "market_data",
                "expansion_threshold": 0.6,
                "contraction_threshold": 0.4
            }
        },
        "regime_thresholds": {
            "expansion": 0.6,  # Probability threshold to declare expansion
            "late_cycle": 0.6,
            "contraction": 0.7,  # Higher threshold for contraction
            "early_recovery": 0.6
        },
        "transition_signals": {
            "yield_curve_inversion": "signal for expansion to late cycle",
            "fed_cutting_rates": "signal for late cycle to contraction or contraction to early recovery",
            "credit_spread_widening": "signal for expansion to late cycle or late cycle to contraction",
            "improving_leading_indicators": "signal for contraction to early recovery",
            "accelerating_growth": "signal for early recovery to expansion"
        }
    }
} 