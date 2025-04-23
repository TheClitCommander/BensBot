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

# Trading Bot

A comprehensive trading bot system with machine learning capabilities, backtesting, and dashboard visualization.

## 🚀 Quick Start

To get started with the Trading Bot:

1. Clone the repository
2. Run the setup script:

```bash
# Make the script executable if needed
chmod +x run_streamlit.sh

# Run the dashboard
./run_streamlit.sh
```

The script will:
- Create a virtual environment if needed
- Install all required dependencies
- Check for commonly missing packages
- Launch the Streamlit dashboard

## 📦 Manual Installation

If you prefer to set up manually:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

## 🧩 System Components

The Trading Bot consists of several modules:

- **Data Providers**: Fetch market data from various sources
- **Strategy Library**: Collection of trading strategies 
- **Backtesting Engine**: Test strategies on historical data
- **ML Models**: Machine learning models for prediction and optimization
- **Dashboard**: Web interface for monitoring and control
- **Risk Management**: Tools for position sizing and risk control

## ⚠️ Common Issues and Solutions

### Missing Dependencies

If you encounter dependency errors, ensure you're running in the virtual environment and install the specific package:

```bash
pip install flask pandas yfinance streamlit
```

### Module Not Found Errors

The system has interdependencies between modules. If you see a "module not found" error, it's likely because:

1. A required module isn't installed (use `pip install`)
2. You're not running the script from the project root directory
3. Your Python path doesn't include the project directory

### Import Issues

If you see import errors like:
```
ImportError: cannot import name 'DataSourceInterface' from 'trading_bot.core.interfaces'
```

This is usually because the interface classes were renamed or moved. The current interface names are:
- `DataProvider` (was previously `DataSourceInterface`)
- `IndicatorInterface`
- `StrategyInterface`
- `SignalInterface`

## 📚 Documentation

Additional documentation is available in the `/docs` folder.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

# TradingView UI

A modern, responsive trading dashboard interface built with React, TypeScript, Tailwind CSS, and shadcn/UI.

## Features

- **Three-panel Layout**: Left sidebar with real-time data, main content area with portfolio visualization, and right sidebar with key statistics.
- **Dark Mode Support**: Clean, professional dark theme for optimal trading experience.
- **Interactive Charts**: Portfolio performance visualization using Recharts.
- **Responsive Design**: Adapts seamlessly to different screen sizes.
- **Type Safety**: Built with TypeScript for robust code quality.
- **Modern UI Components**: Built with shadcn/UI for consistent, accessible components.

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- shadcn/UI (based on Radix UI)
- Vite (for fast builds)
- Recharts (for data visualization)

## Getting Started

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Building for Production

```bash
npm run build
```

## Project Structure

- `/src/components` - Reusable UI components
- `/src/layouts` - Layout components for the application
- `/src/pages` - Page components
- `/src/lib` - Utility functions and hooks

## Connecting to Backend

This UI connects to the existing trading backend APIs. See the API documentation for details on the available endpoints for fetching portfolio data, trade history, and executing trades.

## Customization

The UI uses Tailwind CSS for styling, making it easy to customize colors, spacing, and other design elements. The main theme variables are defined in `tailwind.config.js` and `src/index.css`.

# Trading Backtester

A comprehensive backtesting system for evaluating trading strategies using market data from Alpha Vantage.

## Features

- Backtest multiple trading strategies on historical data
- Supports several popular technical indicators and strategies
- Calculates key performance metrics (return, drawdown, Sharpe ratio, etc.)
- Visualizes backtest results with interactive charts
- Handles stop losses and take profits
- Uses Alpha Vantage API for market data with intelligent caching

## Included Strategies

- **SMA Crossover**: Buy when short SMA crosses above long SMA, sell when it crosses below
- **RSI**: Buy when RSI crosses above oversold threshold, sell when it crosses below overbought threshold
- **MACD**: Buy when MACD line crosses above signal line, sell when it crosses below
- **Bollinger Bands**: Buy when price crosses below lower band, sell when it crosses above upper band

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/trading-backtester.git
cd trading-backtester
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Alpha Vantage API key (get one for free at https://www.alphavantage.co/):
```bash
export ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Usage

### Quick Start

Run a backtest using the default configuration:

```bash
python run_backtest.py
```

### Custom Configuration

Create a JSON configuration file (e.g., `my_config.json`):

```json
{
    "initial_capital": 100000.0,
    "position_size": 0.2,
    "commission": 0.001,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.1,
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "start_date": "2022-01-01",
    "end_date": "2023-01-01",
    "strategy": "sma_crossover",
    "strategy_params": {
        "sma_crossover": {
            "short_window": 20,
            "long_window": 50
        }
    }
}
```

Run the backtest with your configuration:

```bash
python run_backtest.py --config my_config.json
```

### Compare All Strategies

Run backtests for all available strategies and compare their performance:

```bash
python run_backtest.py --all
```

## Directory Structure

- `trading/`: Core trading modules
  - `backtester.py`: Backtester implementation
  - `data/`: Data fetching modules
    - `alpha_vantage_fetcher.py`: Alpha Vantage API client
- `results/`: Backtest results (JSON files and plots)
- `run_backtest.py`: Command-line interface script

## Customization

You can easily add new strategies by extending the backtester module. The system is designed to be modular and extensible.

### Adding a New Strategy

Create a new method in `Backtester` class that generates signals according to your strategy, then update the corresponding sections in `run_backtest.py`.

## Performance Considerations

- Alpha Vantage has API rate limits (typically 5 calls per minute for free tier)
- Data is cached locally to reduce API calls
- Running backtests on multiple symbols can be time-consuming
- Consider using a smaller symbol set for initial testing

## License

MIT License

## Acknowledgements

- [Alpha Vantage](https://www.alphavantage.co/) for the market data API
- [pandas](https://pandas.pydata.org/) for data manipulation
- [matplotlib](https://matplotlib.org/) for visualization