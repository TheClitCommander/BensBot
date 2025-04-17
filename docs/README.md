# Trading Bot Documentation

Welcome to the documentation for the Trading Bot system. This guide covers all aspects of the trading system, including backtesting, risk management, performance metrics, and live trading dashboard.

## Documentation Sections

### Backtesting

* [Performance Metrics](backtesting/performance_metrics.md) - Comprehensive guide to all performance metrics calculated by the backtester, including risk-adjusted returns, drawdown analysis, and trade statistics.

### Risk Management

* [Risk Controls](risk_management/risk_controls.md) - Documentation of risk management features including circuit breakers, volatility-based position sizing, emergency risk controls, and stress testing.

### Dashboard and Visualization

* [Live Trading Dashboard](dashboard/live_trading_dashboard.md) - Guide to the real-time monitoring dashboard for tracking performance, market data, and risk metrics.

### System Components

* [Adaptive Market Scheduler](adaptive_scheduler.md) - Documentation of the dynamic scheduling system that adjusts update frequency based on market hours.

## Quick Start Guides

### Backtesting

To run a backtest with the unified backtester:

```python
from trading_bot.backtesting.unified_backtester import UnifiedBacktester

# Initialize backtester
backtester = UnifiedBacktester(
    initial_capital=100000.0,
    strategies=["trend_following", "momentum", "mean_reversion"],
    start_date="2022-01-01",
    end_date="2022-12-31",
    rebalance_frequency="weekly"
)

# Run backtest
results = backtester.run_backtest()

# Generate and display performance report
performance_report = backtester.generate_performance_report()
print(f"Total Return: {performance_report['summary']['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {performance_report['risk_adjusted_metrics']['sharpe_ratio']:.2f}")
```

### Risk Management Integration

To enable risk management in your backtest:

```python
# Configure risk management
risk_config = {
    "circuit_breakers": {
        "drawdown": {
            "daily": {"threshold": -0.03, "level": 1}
        }
    },
    "position_sizing": {
        "volatility_scaling": True
    }
}

# Initialize backtester with risk management
backtester = UnifiedBacktester(
    initial_capital=100000.0,
    strategies=["trend_following", "momentum"],
    start_date="2022-01-01",
    end_date="2022-12-31",
    enable_risk_management=True,
    risk_config=risk_config
)
```

### Running the Dashboard

To launch the live trading dashboard:

```bash
# With mock data for testing
python trading_bot/run_dashboard.py --mock-data

# With real data connection
python trading_bot/run_dashboard.py --alpaca-key YOUR_KEY --alpaca-secret YOUR_SECRET
```

## System Architecture

The trading system consists of several interconnected components:

1. **Backtesting Engine** - For historical simulation and strategy validation
2. **Risk Management System** - For controlling risk and protecting portfolio
3. **Strategy Implementation** - Various trading strategies and their logic
4. **Data Pipeline** - For acquiring and processing market data
5. **Live Trading Dashboard** - For monitoring and visualization
6. **Execution Engine** - For executing trades in live accounts

## Configuration

Most components support configuration via JSON files or Python dictionaries. Default configurations are stored in `trading_bot/defaults/`.

Example configuration files:
- `backtester_config.json` - Backtesting parameters
- `risk_config.json` - Risk management settings
- `dashboard_config.json` - Dashboard appearance and behavior

## Extending the System

The trading system is designed to be modular and extensible. Key extension points include:

- **Custom Strategies** - Implement your own strategy classes
- **Risk Models** - Add custom risk metrics and controls
- **Data Sources** - Integrate additional market data providers
- **Performance Metrics** - Add new performance calculations
- **Visualization Components** - Extend the dashboard with new charts

For more information on extending the system, see the [Extension Guide](extending.md).

## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs/` directory
2. Ensure all configuration files are properly formatted
3. Verify data sources are accessible
4. Consult the [Common Issues](troubleshooting.md) document 