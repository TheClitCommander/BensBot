# Interpretable ML Trading Bot

A machine learning trading system with a focus on model interpretability and market regime awareness.

## Overview

This trading bot implements a complete machine learning pipeline for trading strategy development with a focus on:

1. **Interpretable Models** - Uses transparent models like logistic regression and tree-based models to ensure trading decisions can be understood
2. **Feature Importance Analysis** - Tracks which features drive predictions over time and across different market regimes
3. **Market Regime Detection** - Automatically detects market regimes (trending, mean-reverting, volatile) and adapts models accordingly
4. **Performance Visualization** - Provides detailed visualizations of model performance and feature contributions

## Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```

## Dependencies

- pandas
- numpy
- scikit-learn
- matplotlib
- talib (for technical indicators)
- xgboost
- lightgbm
- shap (for model interpretability)
- plotly (for interactive visualizations)

## Directory Structure

```
trading_bot/
├── utils/
│   └── feature_engineering.py  # Feature generation and transformation
├── models/
│   └── model_trainer.py        # Interpretable ML model training
├── analysis/
│   └── trade_analyzer.py       # Trade outcome analysis and feedback
├── visualization/
│   └── model_dashboard.py      # Performance and interpretation dashboards
├── main.py                     # Main entry point
└── config.json                 # Configuration file
```

## Quick Start

### 1. Prepare your data

Place your price data CSV files in the `data/` directory. The files should have OHLCV columns.

### 2. Configure parameters

Adjust the `config.json` file to set your model parameters, feature settings, and backtest configuration.

### 3. Train models

```bash
python -m trading_bot.main --mode train --config config.json
```

This will:
- Load the market data
- Generate technical features 
- Train interpretable ML models
- Generate feature importance visualizations
- Create a performance dashboard

### 4. Run backtest

```bash
python -m trading_bot.main --mode backtest --config config.json
```

This will:
- Use the trained models to generate trading signals
- Calculate performance metrics
- Generate trade explanations
- Create a performance dashboard

### 5. View dashboard only

```bash
python -m trading_bot.main --mode dashboard --config config.json
```

## Configuration

The `config.json` file contains all parameters for the system:

```json
{
    "output_dir": "./output",
    "data_sources": {
        "spy": {
            "path": "./data/spy_daily.csv",
            "index_col": "date"
        }
    },
    "feature_engineering": {
        "include_technicals": true,
        "ta_feature_sets": ["momentum", "trend", "volatility", "volume"],
        "detect_market_regime": true
    },
    "model_trainer": {
        "model_algorithm": "random_forest",
        "n_estimators": 100,
        "calculate_shap": true
    },
    "models": [
        {
            "name": "spy_direction",
            "type": "classification",
            "data_source": "spy",
            "target_horizon": 5,
            "threshold": 0.01,
            "use_regime_models": true
        }
    ],
    "backtest": {
        "model_name": "spy_direction",
        "data_source": "spy",
        "test_size": 0.2
    }
}
```

## Feature Interpretation

For each trade, the system provides feature-level explanations that help you understand what drove the model's decision:

```
Trade on 2023-05-01 decision: BUY with 78.5% confidence. Market regime was trending.
This prediction was driven by: 
  - rsi_14 (68.5) with positive influence of 0.324
  - macd_hist (0.85) with positive influence of 0.219  
  - bb_width_20 (1.32) with negative influence of 0.112
```

## Market Regimes

The system automatically detects four market regimes:

1. **Trending** - Strong directional movement with momentum
2. **Mean-reverting** - Oscillating price action around a central value
3. **High volatility** - Large price swings with elevated uncertainty
4. **Random walk** - No clear pattern identifiable

Specialized models are trained for each regime when enough data is available.

## Visualization Dashboard

The system creates an interactive dashboard with:

- Performance metrics by timeframe and market regime
- Feature importance visualizations
- Feature stability analysis
- Trade explanations with feature contributions
- Cumulative P&L tracking

Access the dashboard by opening `output/visualizations/index.html` in your browser after running training or backtesting.

## Extending the System

To add new models or features:

1. **New Features**: Extend the `FeatureEngineering` class with additional methods
2. **New Models**: Add model configurations to `config.json`
3. **Custom Analysis**: Extend the `TradeAnalyzer` class for custom performance metrics

## License

MIT