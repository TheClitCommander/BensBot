# trading_bot/core/autonomous_orchestrator.py
"""
AutonomousOrchestrator: The robust, smart, and future-proof brain that ties together data, strategies, ML/AI, and pipeline execution.
- Uses CentralDataHub for all data needs
- Uses StrategyRegistry for all strategy logic
- Supports symbol discovery, strategy selection, parameter optimization, backtesting, evaluation, and improvement loop
- Returns results in a structured format for UI or paper trading
"""

import logging
from typing import List, Dict, Any, Optional
from trading_bot.core.data_hub import CentralDataHub
from trading_bot.core.strategy_registry import StrategyRegistry
import datetime

logger = logging.getLogger("AutonomousOrchestrator")

class AutonomousOrchestrator:
    def __init__(self, data_hub: CentralDataHub, benchmark: Optional[Dict[str, float]] = None):
        self.data_hub = data_hub
        self.benchmark = benchmark or {"sharpe_ratio": 1.0, "total_return": 10.0}
        self.results = []

    def discover_symbols(self, top_n=5) -> List[str]:
        """Autonomously discover top candidate symbols using news, sentiment, and indicators."""
        # Example: rank by sentiment score × volatility
        candidates = []
        # For demo, use a fixed universe - in production, pull from data_hub
        universe = ["AAPL", "MSFT", "TSLA", "SPY", "GOOGL", "AMZN"]
        for symbol in universe:
            sentiment = self.data_hub.get_sentiment(symbol)
            indicators = self.data_hub.get_indicators(symbol)
            score = sentiment.get("overall", 0) * indicators.get("volatility", 1)
            candidates.append((symbol, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Discovered top symbols: {[c[0] for c in candidates[:top_n]]}")
        return [c[0] for c in candidates[:top_n]]

    def select_strategy(self, symbol: str, context: Dict[str, Any]) -> str:
        """Select the best-fit strategy for a symbol based on indicators and sentiment."""
        # Example: use indicator/sentiment heuristics (extendable)
        if context["sentiment"].get("overall", 0) > 0.5 and context["indicators"].get("momentum", 0) > 0.5:
            return "momentum"
        elif context["indicators"].get("volatility", 0) > 2:
            return "mean_reversion"
        else:
            return "trend_following"

    def optimize_parameters(self, strategy_name: str, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize parameters for a given strategy and symbol using ParameterOptimizer."""
        try:
            import os
            from trading_bot.simulation.parameter_optimizer import ParameterOptimizer, ParameterSpace, OptimizationConfig
            from trading_bot.simulation.trading_simulator import SimulationConfig, SimulationMode, MarketScenario
            from trading_bot.data.data_providers import MockDataProvider

            # 1. Build parameter spaces for each supported strategy
            default_spaces = {
                "momentum": [
                    ParameterSpace(name="fast_period", values=[3, 5, 10], description="Fast MA period"),
                    ParameterSpace(name="slow_period", values=[15, 20, 30], description="Slow MA period"),
                ],
                "trend_following": [
                    ParameterSpace(name="short_ma_period", values=[5, 10, 20], description="Short MA period"),
                    ParameterSpace(name="long_ma_period", values=[20, 30, 50], description="Long MA period"),
                ],
                "mean_reversion": [
                    ParameterSpace(name="period", values=[10, 20, 30], description="Lookback period"),
                    ParameterSpace(name="std_dev_factor", values=[1.5, 2.0, 2.5], description="Std Dev Factor"),
                ],
            }
            parameter_spaces = default_spaces.get(strategy_name, [])
            if not parameter_spaces:
                logger.warning(f"No parameter space defined for strategy '{strategy_name}', using default.")
                parameter_spaces = [ParameterSpace(name="window", values=[10, 20, 30], description="Generic window")]

            # 2. Build OptimizationConfig
            optimization_config = OptimizationConfig(
                parameter_spaces=parameter_spaces,
                target_metric="sharpe_ratio",
                higher_is_better=True,
                max_parallel_jobs=2,
                output_dir=os.path.join("optimization_results", strategy_name, symbol),
                random_seed=42
            )

            # 3. Build SimulationConfig (use context and defaults)
            from datetime import datetime, timedelta
            price_data = context.get("price_data")
            if price_data is not None and hasattr(price_data, 'index'):
                start_date = price_data.index[0] if len(price_data.index) > 0 else datetime.now() - timedelta(days=365)
                end_date = price_data.index[-1] if len(price_data.index) > 0 else datetime.now()
            else:
                start_date = datetime.now() - timedelta(days=365)
                end_date = datetime.now()

            sim_config = SimulationConfig(
                mode=SimulationMode.BACKTEST,
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000.0,
                symbols=[symbol],
                market_scenario=MarketScenario.NORMAL,
                data_frequency="1d",
                slippage_model="fixed",
                slippage_value=0.0,
                commission_model="fixed",
                commission_value=0.0,
                enable_fractional_shares=True,
                random_seed=42
            )

            # 4. Data provider (use a mock or real one as appropriate)
            data_provider = MockDataProvider()

            # 5. Strategy factory
            strategy_cls = StrategyRegistry.get(strategy_name)
            def strategy_factory(symbol, data_provider, risk_manager=None, **params):
                # Accepts params as flat dict
                config = {k: v for k, v in params.items()}
                return strategy_cls(symbol, config=config)

            # 6. Instantiate and run optimizer
            optimizer = ParameterOptimizer(
                base_simulation_config=sim_config,
                optimization_config=optimization_config,
                data_provider=data_provider,
                strategy_factory=strategy_factory,
            )
            logger.info(f"Starting parameter optimization for {strategy_name} on {symbol}")
            result = optimizer.run_grid_search()
            logger.info(f"Optimization complete. Best params: {result.best_parameters}, Score: {result.best_score}")
            return result.best_parameters or {}
        except Exception as e:
            logger.error(f"Parameter optimization failed for {strategy_name} on {symbol}: {e}")
            return {}

    def run_pipeline(self, top_n=5, optimize_params=False) -> List[Dict[str, Any]]:
        """Run the full autonomous pipeline and return structured results."""
        results = []
        symbols = self.discover_symbols(top_n=top_n)
        for symbol in symbols:
            context = {
                "sentiment": self.data_hub.get_sentiment(symbol),
                "indicators": self.data_hub.get_indicators(symbol),
                "price_data": self.data_hub.get_price_data(symbol)
            }
            strategy_name = self.select_strategy(symbol, context)
            if optimize_params:
                params = self.optimize_parameters(strategy_name, symbol, context)
            else:
                params = {}
            strategy_cls = StrategyRegistry.get(strategy_name)
            strategy = strategy_cls(name=symbol, config=params)
            # Run backtest (assume strategy has a backtest method)
            try:
                backtest_result = strategy.backtest(context["price_data"])
            except Exception as e:
                logger.error(f"Backtest failed for {symbol} with {strategy_name}: {e}")
                backtest_result = {"error": str(e)}
            # Evaluate against benchmark
            meets_benchmark = (backtest_result.get("sharpe_ratio", 0) >= self.benchmark["sharpe_ratio"] and
                               backtest_result.get("total_return", 0) >= self.benchmark["total_return"])
            results.append({
                "symbol": symbol,
                "strategy": strategy_name,
                "params": params,
                "metrics": backtest_result,
                "meets_benchmark": meets_benchmark,
                "run_time": datetime.datetime.now().isoformat()
            })
        self.results = results
        return results
