# BensBot Trading System

A robust, production-ready trading bot system with crash resilience, event-driven architecture, and adaptive position management.

## Overview

BensBot is a professional-grade, modular trading system designed for reliability, observability, and adaptability. Key features include:

1. **Event-Driven Architecture** - Core components communicate through a centralized event bus for decoupling and extensibility
2. **Multi-Broker Support** - Trade through multiple brokers with unified interface, automatic failover, and asset routing
3. **Adaptive Position Management** - Dynamic position sizing based on market regime, volatility, and portfolio state
4. **Durable Persistence Layer** - Crash-resilient storage with MongoDB and Redis for orders, fills, positions, and P&L
5. **Risk Management** - Automatic circuit breakers for drawdown, volatility, and margin monitoring
6. **Containerized Deployment** - Docker Compose orchestration for the trading engine, dashboard, MongoDB, and Redis

## Installation

BensBot can be installed and run in three ways:

### 1. Local Installation (Development)

```bash
# Clone the repository
git clone https://github.com/YourUsername/BensBot.git
cd BensBot

# Install with pip in development mode
pip install -e .

# Or use Poetry for dependency management
pip install poetry
poetry install
```

### 2. Docker Compose (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/YourUsername/BensBot.git
cd BensBot

# Start the entire system with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Python Package Installation

```bash
# Install directly from GitHub
pip install git+https://github.com/YourUsername/BensBot.git

# Or install from local directory after cloning
pip install .
```

## Dependencies

All dependencies are managed through `pyproject.toml` and include:

- **Core Dependencies**:
  - pandas, numpy, scipy
  - pymongo, redis
  - pydantic (for configuration validation)
  - fastapi, uvicorn (for the API dashboard)
  
- **Broker Integration**:
  - requests, websockets
  - alpaca-trade-api
  - tradier (custom client)

- **Analytics & Visualization**:
  - matplotlib, plotly, streamlit
  - ta-lib (technical indicators)
  
## Directory Structure

```
trading_bot/               # Main package
├── brokers/                # Broker integrations
│   ├── adapter.py          # Generic broker adapter interface
│   ├── tradier/            # Tradier broker implementation
│   ├── alpaca/             # Alpaca broker implementation
│   └── multi_broker_manager.py  # Multi-broker orchestration
│
├── core/                   # Core trading system
│   ├── events.py           # Event types and handlers
│   ├── main_orchestrator.py # Primary system orchestration
│   ├── risk_manager.py     # Risk management and circuit breakers
│   └── adaptive_position_manager.py # Position sizing
│
├── persistence/            # Persistence layer
│   ├── connection_manager.py # MongoDB and Redis connection pooling
│   ├── base_repository.py  # Generic repository pattern
│   ├── order_repository.py # Order storage and retrieval
│   ├── position_repository.py # Position tracking
│   └── idempotency.py      # Crash-safe operation manager
│
├── dashboard/              # Monitoring and control dashboard
│   ├── app.py              # Streamlit dashboard
│   ├── api.py              # FastAPI backend
│   └── components/         # UI components
│
├── config/                 # Configuration management
│   ├── loader.py           # Config loading with validation
│   ├── models.py           # Pydantic config schemas
│   └── migrate_configs.py  # Legacy config migration
│
├── run_bot.py              # Main entry point
└── main.py                 # Legacy entry point

config/                     # Configuration files
├── config.yaml             # Main unified config
└── persistence_config.json # Persistence layer config

docker-compose.yml          # Docker Compose definition
Dockerfile                  # Trading bot container
Dockerfile.dashboard        # Dashboard container
pyproject.toml              # Python package definition
```

## Quick Start

### 1. Local Development

```bash
# Install with development dependencies
pip install -e .[dev]

# Initialize MongoDB and Redis (if not using Docker)
# On macOS with Homebrew
brew services start mongodb-community
brew services start redis

# Start the trading bot
python -m trading_bot.run_bot --config config/config.yaml

# In a separate terminal, start the dashboard
python -m trading_bot.dashboard.app
```

### 2. Docker Compose Deployment

```bash
# Start all services
docker-compose up -d

# Check services status
docker-compose ps

# View logs
docker-compose logs -f trading-bot

# Access the dashboard
open http://localhost:8000
```

### 3. Migrating from Legacy Configuration

```bash
# Run the migration utility
python -m trading_bot.config.migrate_configs --base-dir ./config --output ./config/config.yaml

# Generate a report without migrating
python -m trading_bot.config.migrate_configs --report
```

## Configuration System

BensBot uses a unified configuration system with Pydantic validation:

### Configuration File Structure

```yaml
# config/config.yaml
---
version: "1.1"
environment: "development"  # or "production"

# Broker configuration
broker_manager:
  brokers:
    - id: "tradier_main"
      name: "Tradier Main"
      type: "tradier"
      enabled: true
      sandbox_mode: false  # Set to true for paper trading
      timeout_seconds: 30
      retry_attempts: 3
      credentials:
        api_key: "env:TRADIER_API_KEY"  # Reference to environment variable
        account_id: "env:TRADIER_ACCOUNT_ID"
  
  asset_routing:
    - symbol_pattern: "*"  # Default route for all symbols
      primary_broker_id: "tradier_main"
      failover_broker_ids: []
  
  failover_enabled: true
  metrics_enabled: true

# Risk management settings
risk_manager:
  max_drawdown_pct: 5.0
  volatility_threshold: 2.5
  cooldown_minutes: 60
  margin_call_threshold: 0.25
  margin_warning_threshold: 0.35
  max_leverage: 2.0
  position_size_limit_pct: 5.0

# MongoDB and Redis for persistence
persistence:
  mongodb:
    uri: "mongodb://localhost:27017"
    database: "bensbot_trading"
    max_pool_size: 20
    timeout_ms: 5000
  
  redis:
    host: "localhost"
    port: 6379
    db: 0
    timeout: 5.0
    decode_responses: true
    key_prefix: "bensbot:"
  
  recovery:
    recover_on_startup: true
    recover_open_orders: true
    recover_positions: true
    recover_pnl: true
  
  sync:
    periodic_sync_enabled: true
    sync_interval_seconds: 3600  # Sync to MongoDB every hour

# Strategy configuration
strategy_manager:
  strategies:
    - id: "sma_crossover"
      name: "SMA Crossover"
      enabled: true
      class_path: "trading_bot.strategies.equity.sma_crossover.SMACrossoverStrategy"
      parameters:
        short_period: 20
        long_period: 50
      symbols: ["SPY", "QQQ", "AAPL"]
      time_frames: ["1d"]
```

### Environment Variable Overrides

Any configuration value can be overridden with environment variables:

```bash
# For broker credentials
export TRADIER_API_KEY="your-api-key"
export TRADIER_ACCOUNT_ID="your-account-id"

# For persistence settings
export MONGODB_URI="mongodb://custom-host:27017"
export REDIS_HOST="custom-redis-host"

# For risk parameters
export RISK_MAX_DRAWDOWN_PCT="3.5"
export RISK_MAX_LEVERAGE="1.5"
```

### Configuration Validation

Configuration is validated using Pydantic models defined in `trading_bot.config.models`:

```python
from trading_bot.config.loader import load_config

# Load and validate configuration
config = load_config("config/config.yaml")

# Access typed configuration sections
broker_config = config.broker_manager
print(f"Using {len(broker_config.brokers)} brokers")

# Risk parameters are validated against constraints
risk_config = config.risk_manager
print(f"Max drawdown: {risk_config.max_drawdown_pct}%")
```
```

## Persistence Layer

BensBot's persistence layer provides crash resilience and state recovery for all trading operations:

### Architecture

<pre>
┌─────────────────┐     ┌───────────────┐     ┌──────────────┐
│  Event System   │────▶│Redis Hot Store│────▶│MongoDB Durable│
└─────────────────┘     └───────────────┘     └──────────────┘
         │                      ▲                    ▲
         │                      │                    │
         ▼                      │                    │
┌─────────────────┐             │                    │
│Trading Operations│────────────┘                    │
└─────────────────┘                                  │
         │                                           │
         ▼                                           │
┌─────────────────┐                                  │
│  Idempotency    │──────────────────────────────────┘
└─────────────────┘
</pre>

### Key Components

1. **Repository Pattern**: All persistent entities (orders, fills, positions, PnL) are managed through type-specific repositories that implement a common interface.

2. **Two-Tier Storage**:
   - **Redis** for hot, in-memory state with fast access
   - **MongoDB** for durable, persistent storage

3. **Idempotency Management**: Prevents duplicate operations when recovering from crashes by tracking operation IDs and their outcomes.

4. **Event-Driven Updates**: All state changes are triggered by events, allowing for loose coupling between components.

5. **Automatic Recovery**: On system restart, all state is recovered from the persistence layer.

### Benefits

* **Crash Resilience**: Trading can resume safely after unexpected shutdowns
* **Concurrency Support**: Multiple instances can operate on the same data safely
* **Audit Trail**: Complete history of all trading operations
* **Hot/Cold Architecture**: Fast operations with durable guarantees
* **Unified Interface**: Consistent access patterns for all persistent entities

## Risk Management

BensBot incorporates a comprehensive risk management system with automatic circuit breakers:

### Key Features

1. **Margin Monitoring**: Continuously tracks account margin status across all brokers, with configurable warning and call thresholds.

2. **Circuit Breakers**: Automatically pause trading when predefined risk thresholds are exceeded:
   - Maximum drawdown percentage
   - Volatility threshold
   - Max correlation exposure

3. **Forced De-Leveraging**: Automatically reduces positions when margin thresholds are breached.

4. **Position Size Limits**: Enforces maximum position size as a percentage of portfolio.

5. **Dashboard Controls**: Provides a risk control panel for monitoring and manual intervention.

### Risk Control Flow

```
1. Monitor margin status, drawdown, volatility metrics
2. If thresholds breached:
   a. Emit warning or circuit breaker event
   b. Pause trading via EventBus
   c. Initiate de-leveraging if required
3. Dashboard updates with current status
4. Manual override available for resuming trading
```

## Deployment Architecture

BensBot is designed for containerized deployment using Docker Compose:

### Components

<pre>
┌─────────────────┐     ┌───────────────┐     ┌──────────────┐
│  Trading Bot    │────▶│    MongoDB    │◀────│   Dashboard   │
└─────────────────┘     └───────────────┘     └──────────────┘
         │                      ▲                    ▲
         │                      │                    │
         ▼                      │                    │
┌─────────────────┐             │                    │
│      Redis      │─────────────┘                    │
└─────────────────┘                                  │
         ▲                                           │
         │                                           │
         └───────────────────────────────────────────┘
</pre>

### Services

1. **Trading Bot** (Python)
   - Core trading engine
   - Strategy execution
   - Broker integration
   - Risk management

2. **MongoDB** (MongoDB Community)
   - Durable storage for all trading state
   - Historical data retention
   - Query support for dashboard

3. **Redis** (Redis Alpine)
   - Hot-state caching
   - Idempotency tracking
   - Fast access for real-time operations

4. **Dashboard** (FastAPI/Streamlit)
   - Monitoring UI
   - Control endpoints
   - Strategy management
   - Risk control panel

### Deployment Options

1. **Local Development**: Run services directly on the host machine
2. **Docker Compose**: Run all services as containers (recommended for production)
3. **Kubernetes**: Advanced deployment for high-availability (configuration provided separately)

### Scaling Considerations

* Each component can be scaled independently
* MongoDB supports replication for high availability
* Redis can be configured with persistence and replication
* Trading Bot can be deployed in active-passive configuration for redundancy

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

## Configuration System

BensBot features an enterprise-grade configuration system that provides schema validation, environment variable overrides, and hot-reloading capabilities.

### Configuration Structure

The main configuration file is located at `config/system_config.json` and is validated against the schema in `config/system_config.schema.json`. Additional configuration files include:

- `config/market_regime_config.json` - Market regime detection settings
- `config/market_data_config.json` - Market data sources and preferences
- `config/broker_config.json` - Broker connection settings

### Command-Line Interface

The BensBot runner provides several configuration-related options:

```bash
# Print the current configuration with environment overrides
python trading_bot/run_bot.py --print-config

# Validate configuration against schema
python trading_bot/run_bot.py --validate-schema

# Use a custom configuration file
python trading_bot/run_bot.py --config /path/to/custom_config.json

# Run with hot-reload disabled
python trading_bot/run_bot.py --no-hot-reload
```

### Environment Variable Overrides

Any configuration value can be overridden using environment variables with the `BENBOT_` prefix:

```bash
# Simple values
export BENBOT_INITIAL_CAPITAL=20000
export BENBOT_RISK_PER_TRADE=0.05
export BENBOT_LOG_LEVEL=DEBUG

# Nested values
export BENBOT_TRADING_HOURS_START=10:00
export BENBOT_TRADING_HOURS_END=16:30
export BENBOT_SYSTEM_SAFEGUARDS_CIRCUIT_BREAKERS_MAX_DRAWDOWN_PERCENT=15

# Lists (comma-separated)
export BENBOT_WATCHED_SYMBOLS=SPY,QQQ,AAPL,MSFT
```

### Configuration Validation

You can validate your configuration without starting BensBot using the validation tool:

```bash
python config/validate_config.py
```

This will check:
1. If your configuration file is valid JSON
2. If it passes schema validation
3. If all referenced files exist
4. If any environment variable overrides are active

### Hot Reload

BensBot supports hot reloading of configuration files. Changes are detected and applied without restarting:

```json
{
  "enable_config_hot_reload": true,
  "config_reload_interval_seconds": 60
}
```

For more detailed information, see the [Configuration Documentation](docs/CONFIG.md).

## License

MIT License

## Acknowledgements

- [Alpha Vantage](https://www.alphavantage.co/) for the market data API
- [pandas](https://pandas.pydata.org/) for data manipulation
- [matplotlib](https://matplotlib.org/) for visualization