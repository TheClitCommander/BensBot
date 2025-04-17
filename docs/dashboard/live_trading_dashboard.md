# Live Trading Dashboard

A real-time monitoring dashboard for tracking trading strategy performance, market data, risk metrics, and allocation changes.

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [Starting the Dashboard](#starting-the-dashboard)
4. [Dashboard Features](#dashboard-features)
5. [Data Sources and Integration](#data-sources-and-integration)
6. [Risk Monitoring Widgets](#risk-monitoring-widgets)
7. [Performance Metrics](#performance-metrics)
8. [Debugging and Alerts](#debugging-and-alerts)
9. [Customization](#customization)
10. [Configuration Options](#configuration-options)

## Overview

The Live Trading Dashboard provides real-time visualization and monitoring of trading system performance. Built with Streamlit, it offers a responsive user interface for tracking portfolio value, trade history, strategy allocations, market data, and risk metrics.

![Dashboard Overview](../assets/dashboard_overview.png)

## Installation and Setup

### Prerequisites

The dashboard requires:
- Python 3.7 or higher
- Streamlit 1.0 or higher
- Plotly for visualizations
- Access to real-time market data (or mock data for testing)

### Installation

```bash
# Install required packages
pip install streamlit plotly pandas numpy matplotlib seaborn

# For data connections (optional depending on your setup)
pip install alpaca-trade-api interactive-brokers-api
```

## Starting the Dashboard

### Command Line Interface

The dashboard can be launched using the provided `run_dashboard.py` script:

```bash
python trading_bot/run_dashboard.py
```

#### Command Line Options

```
--port        Port to run the dashboard on (default: 8501)
--alpaca-key  Alpaca API key (can also be set via ALPACA_API_KEY env var)
--alpaca-secret  Alpaca API secret (can also be set via ALPACA_API_SECRET env var) 
--mock-data   Use mock data instead of connecting to real data sources
```

### Environment Variables

The dashboard uses the following environment variables:

```
ALPACA_API_KEY     - API key for Alpaca data
ALPACA_API_SECRET  - API secret for Alpaca data
IB_HOST            - Host for Interactive Brokers connection (default: 127.0.0.1)
IB_PORT            - Port for Interactive Brokers connection (default: 7497)
IB_CLIENT_ID       - Client ID for Interactive Brokers connection (default: 1)
```

## Dashboard Features

### Portfolio Performance

![Portfolio Performance](../assets/portfolio_performance.png)

- **Portfolio Value Chart**: Real-time chart of portfolio value
- **Allocation Breakdown**: Current allocation across strategies
- **Performance Metrics**: Key performance indicators including:
  - Daily, weekly, monthly, and YTD returns
  - Sharpe ratio, Sortino ratio, and Calmar ratio
  - Maximum drawdown and recovery information

### Market Data

![Market Data](../assets/market_data.png)

- **Price Charts**: Real-time price charts for tracked symbols
- **Volume Analysis**: Volume indicators and unusual volume detection
- **Technical Indicators**: Moving averages, RSI, MACD, and other indicators
- **Correlation Matrix**: Dynamic correlation between tracked assets

### Trading Activity

![Trading Activity](../assets/trading_activity.png)

- **Trade History**: Real-time log of executed trades
- **Open Positions**: Current positions and unrealized P&L
- **Trade Metrics**: Win rate, profit factor, average win/loss

### Market Regime Detection

![Market Regime](../assets/market_regime.png)

- **Current Regime**: Visual indicator of detected market regime
- **Regime History**: Timeline of regime changes
- **Regime Probabilities**: Confidence levels for different regime classifications

## Data Sources and Integration

The dashboard can connect to multiple data sources:

### Supported Data Sources

1. **Alpaca**: Real-time and historical market data
   - Set up in the sidebar with API keys
   - Supports stocks, ETFs, and crypto assets

2. **Interactive Brokers**: Market data and trade execution
   - Requires running TWS or IB Gateway
   - Connects via the IB API

3. **Mock Data**: Simulated data for testing
   - Generates realistic price movements
   - Simulates different market regimes

### Data Integration

The dashboard integrates with the `RealTimeDataManager` class that handles:
- Data subscription and streaming
- Event-based updates
- Strategy calculations
- Market regime detection

## Risk Monitoring Widgets

### Risk Metrics Panel

![Risk Metrics](../assets/risk_metrics.png)

- **Current Volatility**: Realized volatility with trend indicator
- **Value at Risk (VaR)**: 95% and 99% daily VaR estimates
- **Conditional VaR**: Expected shortfall metrics
- **Drawdown Monitor**: Current drawdown with historical context

### Circuit Breaker Status

![Circuit Breakers](../assets/circuit_breakers.png)

- **Active Circuit Breakers**: Visual indicators for active breakers
- **Trigger History**: Timeline of circuit breaker activations
- **Current Restrictions**: Details on trading limitations in effect

### Risk Alerts

- **Anomaly Detection**: Alerts for unusual market or portfolio behavior
- **Correlation Warnings**: Alerts for sudden correlation changes
- **Volatility Spikes**: Notifications of significant volatility increases

### Stress Test Results

![Stress Tests](../assets/stress_tests.png)

- **Scenario Analysis**: Results from different stress test scenarios
- **Projected Metrics**: How the portfolio would perform under stress
- **Risk Level Assessment**: Overall risk level indicator

## Performance Metrics

### Real-time Metrics

- Portfolio value and daily change
- Strategy-specific returns
- Attribution analysis
- Cash allocation and leverage metrics

### Historical Comparisons

- Performance vs. benchmark
- Strategy contribution over time
- Rolling metrics (Sharpe, volatility, etc.)
- Drawdown comparison

### Customizable Time Ranges

- Intraday (1H, 4H)
- Daily
- Weekly
- Monthly
- YTD
- Custom date range

## Debugging and Alerts

### Log Panel

![Logs and Alerts](../assets/logs.png)

- **Real-time Logging**: Stream of system events and actions
- **Error Tracking**: Highlighted error messages and stack traces
- **Warning System**: Color-coded warnings for potential issues

### Alert Configuration

- **Email Alerts**: Configure email notifications for critical events
- **SMS Alerts**: Mobile alerts for emergency situations
- **Custom Thresholds**: Define custom alert triggers

### System Status

- **Connection Status**: Indicators for data source connectivity
- **Latency Monitoring**: Data and execution latency tracking
- **Resource Usage**: System resource monitoring

## Customization

### Layout Customization

- **Component Visibility**: Show/hide specific dashboard components
- **Chart Options**: Customize chart types, indicators, and time periods
- **Color Themes**: Choose between light, dark, and custom themes

### Data Display Options

- **Update Frequency**: Control real-time data update intervals
- **Symbol Selection**: Choose which symbols to display
- **Metric Selection**: Select performance metrics to highlight

## Configuration Options

### Dashboard Configuration

The dashboard can be configured through the `dashboard_config.json` file:

```json
{
  "theme": "dark",
  "default_symbols": ["SPY", "QQQ", "TLT", "GLD"],
  "update_frequency": 5,
  "default_time_range": "1 Day",
  "performance_metrics": [
    "total_return", "sharpe_ratio", "sortino_ratio", 
    "max_drawdown", "win_rate", "profit_factor"
  ],
  "chart_options": {
    "show_volume": true,
    "default_indicators": ["sma", "ema", "rsi"],
    "candlestick_time_frame": "15min"
  },
  "risk_options": {
    "var_confidence": 0.95,
    "stress_test_scenarios": ["market_crash", "volatility_spike"],
    "circuit_breaker_display": true
  },
  "alerts": {
    "email_enabled": false,
    "email_address": "",
    "sms_enabled": false,
    "phone_number": ""
  }
}
```

### User Preferences

User-specific preferences are stored locally and can be modified through the dashboard interface:

- Preferred data source
- Default symbols
- Chart types and indicators
- Alert settings
- Layout configuration

---

## Usage Examples

### Starting with Mock Data for Testing

```bash
python trading_bot/run_dashboard.py --mock-data
```

### Starting with Alpaca Data Source

```bash
python trading_bot/run_dashboard.py --alpaca-key YOUR_KEY --alpaca-secret YOUR_SECRET
```

### Connecting to Running System

To connect the dashboard to an existing trading system:

1. Ensure the trading system exposes a WebSocket or REST API
2. Configure the dashboard to connect to this API
3. Launch the dashboard with the `--connect` flag:

```bash
python trading_bot/run_dashboard.py --connect ws://localhost:8765
```

### Dashboard URL

Once started, the dashboard is available at:

```
http://localhost:8501
```

You can access it from any web browser on the local machine. 