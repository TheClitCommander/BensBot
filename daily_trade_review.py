#!/usr/bin/env python3
"""
Daily Trade Review and Strategy Adaptation

This script automatically evaluates all trades from the previous trading day using
the LLM trade evaluator and adjusts strategy weights based on performance and feedback.
"""

import os
import sys
import json
import yaml
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import internal components
from trading_bot.journal.trade_journal import TradeJournal, FeedbackLearningModule
from trading_bot.ai_analysis.llm_trade_evaluator import LLMTradeEvaluator
from trading_bot.data.market_data_provider import create_data_provider
from trading_bot.market.regime_classifier import MarketRegimeClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/daily_review.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class DailyTradeReviewer:
    """
    Automatically reviews trades and adapts strategy allocations based on performance.
    """
    
    def __init__(
        self,
        journal_dir: str = "trade_journal",
        config_path: str = "configs/config.json",
        output_config_path: str = "configs/strategy_allocation_weights.yaml",
        cache_dir: str = "cache"
    ):
        """
        Initialize the daily trade reviewer.
        
        Args:
            journal_dir: Directory where trade journal is stored
            config_path: Path to configuration file
            output_config_path: Path to output updated strategy weights
            cache_dir: Directory to cache LLM responses
        """
        self.config_path = config_path
        self.output_config_path = output_config_path
        
        # Load configuration
        self.config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
        
        # Initialize trade journal
        self.journal = TradeJournal(
            journal_dir=journal_dir,
            config_path=config_path
        )
        
        # Initialize learning module
        self.learning_module = FeedbackLearningModule(self.journal)
        
        # Initialize LLM evaluator
        self.evaluator = LLMTradeEvaluator(
            config_path=config_path,
            use_mock=self.config.get("use_mock_llm", False),
            cache_dir=cache_dir
        )
        
        # Initialize market data provider
        data_provider_type = self.config.get("data_provider_type", "alpaca")
        self.data_provider = create_data_provider(
            provider_type=data_provider_type,
            config_path=config_path
        )
        
        # Initialize market regime classifier
        self.regime_classifier = MarketRegimeClassifier(
            config_path=config_path,
            data_provider=self.data_provider
        )
        
        # Initialize statistics
        self.stats = {
            "total_trades": 0,
            "evaluated_trades": 0,
            "strategy_adjustments": 0,
            "strategy_scores": {},
            "regime_effectiveness": {}
        }
        
        logger.info("Daily Trade Reviewer initialized")
    
    def run_daily_review(self, review_date: Optional[str] = None):
        """
        Run the daily review process.
        
        Args:
            review_date: Date to review in YYYY-MM-DD format (default: yesterday)
        """
        # Determine date to review
        if review_date:
            date_to_review = review_date
        else:
            # Default to yesterday
            yesterday = datetime.now() - timedelta(days=1)
            date_to_review = yesterday.strftime("%Y-%m-%d")
        
        logger.info(f"Starting daily review for {date_to_review}")
        console.print(Panel(f"[bold green]Daily Trade Review[/bold green]", 
                           subtitle=f"Analyzing trades from {date_to_review}"))
        
        # Get trades from the specified date
        trades = self._get_trades_for_date(date_to_review)
        
        if not trades:
            logger.info(f"No trades found for {date_to_review}")
            console.print(f"[yellow]No trades found for {date_to_review}[/yellow]")
            return
        
        # Update statistics
        self.stats["total_trades"] = len(trades)
        
        # Evaluate trades using LLM
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False
        ) as progress:
            task = progress.add_task(f"[cyan]Evaluating {len(trades)} trades...", total=len(trades))
            
            for trade in trades:
                self._evaluate_trade(trade)
                progress.update(task, advance=1)
        
        # Update strategy scores based on evaluations
        self._update_strategy_scores()
        
        # Determine current market regime
        current_regime = self._determine_current_regime()
        
        # Generate new strategy allocations
        new_allocations = self._generate_strategy_allocations(current_regime)
        
        # Save updated strategy weights
        self._save_strategy_allocations(new_allocations, current_regime)
        
        # Display results
        self._display_results(current_regime)
        
        logger.info(f"Daily review completed for {date_to_review}")
    
    def _get_trades_for_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of trade dictionaries
        """
        # Convert date strings to datetime for comparison
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get all trades
        all_trades = self.journal.trades
        
        # Filter trades for the specific date
        date_trades = []
        
        for trade in all_trades:
            # Extract date from entry_time (handle both closed and open trades)
            entry_time = trade.get('entry_time')
            if entry_time:
                try:
                    entry_date = datetime.fromisoformat(entry_time).date()
                    if entry_date == target_date:
                        date_trades.append(trade)
                except (ValueError, TypeError):
                    continue
        
        logger.info(f"Found {len(date_trades)} trades for {date}")
        return date_trades
    
    def _evaluate_trade(self, trade: Dict[str, Any]):
        """
        Evaluate a trade using the LLM evaluator.
        
        Args:
            trade: Trade dictionary
        """
        # Skip if trade is still open or already has an evaluation
        if trade.get('status') != 'closed' or 'llm_evaluation' in trade:
            return
        
        symbol = trade.get('symbol')
        direction = trade.get('direction')
        strategy = trade.get('strategy')
        entry_price = trade.get('entry_price')
        exit_price = trade.get('exit_price')
        stop_loss = trade.get('stop_loss')
        take_profit = trade.get('take_profit')
        market_context = trade.get('market_context', {})
        
        try:
            # Fetch recent market data and news for context
            market_data = self._fetch_market_data(symbol)
            news_data = self._fetch_news_data(symbol)
            
            # Perform LLM evaluation
            evaluation = self.evaluator.evaluate_trade(
                symbol=symbol,
                direction=direction,
                strategy=strategy,
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                market_data=market_data,
                news_data=news_data,
                market_context=market_context
            )
            
            # Store evaluation in trade record
            trade['llm_evaluation'] = evaluation
            
            # Generate additional feedback based on exit
            if 'exit_reason' in trade:
                feedback_note = self._generate_feedback_note(trade, evaluation)
                if feedback_note:
                    self.journal.add_note(trade['id'], feedback_note)
            
            # Update statistics
            self.stats["evaluated_trades"] += 1
            
            # Update strategy scores
            if strategy not in self.stats["strategy_scores"]:
                self.stats["strategy_scores"][strategy] = {
                    "count": 0,
                    "confidence_sum": 0,
                    "pnl_sum": 0
                }
            
            self.stats["strategy_scores"][strategy]["count"] += 1
            self.stats["strategy_scores"][strategy]["confidence_sum"] += evaluation.get('confidence_score', 50)
            self.stats["strategy_scores"][strategy]["pnl_sum"] += trade.get('pnl', 0)
            
            # Update regime effectiveness
            regime = market_context.get('market_regime', 'unknown')
            if regime not in self.stats["regime_effectiveness"]:
                self.stats["regime_effectiveness"][regime] = {
                    "strategies": {},
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_pnl": 0
                }
            
            regime_stats = self.stats["regime_effectiveness"][regime]
            regime_stats["total_trades"] += 1
            
            if trade.get('pnl', 0) > 0:
                regime_stats["winning_trades"] += 1
            
            regime_stats["total_pnl"] += trade.get('pnl', 0)
            
            if strategy not in regime_stats["strategies"]:
                regime_stats["strategies"][strategy] = {
                    "trades": 0,
                    "wins": 0,
                    "pnl": 0
                }
            
            strategy_stats = regime_stats["strategies"][strategy]
            strategy_stats["trades"] += 1
            
            if trade.get('pnl', 0) > 0:
                strategy_stats["wins"] += 1
            
            strategy_stats["pnl"] += trade.get('pnl', 0)
            
            logger.debug(f"Evaluated trade {trade['id']} for {symbol} with confidence {evaluation.get('confidence_score')}")
            
        except Exception as e:
            logger.error(f"Error evaluating trade {trade.get('id')}: {str(e)}")
    
    def _fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch market data for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with market data
        """
        try:
            # Get current market data
            market_data = self.data_provider.get_current_market_data([symbol])
            return market_data
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {str(e)}")
            return {}
    
    def _fetch_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch news data for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of news articles
        """
        try:
            # Use the evaluator's news fetcher if available
            if hasattr(self.evaluator, 'fetch_news_data'):
                return self.evaluator.fetch_news_data(symbol)
            
            # Otherwise return empty list
            return []
        except Exception as e:
            logger.error(f"Error fetching news data for {symbol}: {str(e)}")
            return []
    
    def _generate_feedback_note(self, trade: Dict[str, Any], evaluation: Dict[str, Any]) -> str:
        """
        Generate additional feedback note based on trade outcome and LLM evaluation.
        
        Args:
            trade: Trade dictionary
            evaluation: LLM evaluation dictionary
            
        Returns:
            Feedback note string or empty string
        """
        exit_reason = trade.get('exit_reason', '')
        pnl = trade.get('pnl', 0)
        confidence_score = evaluation.get('confidence_score', 50)
        
        feedback = []
        
        # Add feedback based on trade outcome vs LLM confidence
        if pnl > 0 and confidence_score < 50:
            feedback.append("Trade was profitable despite low LLM confidence. Consider reviewing what indicators the model might be missing.")
        elif pnl < 0 and confidence_score > 70:
            feedback.append("Trade lost despite high LLM confidence. Review what key risks the model overlooked.")
        
        # Add feedback based on exit reason
        if exit_reason == 'stop_loss' and confidence_score > 60:
            feedback.append("Stop loss triggered despite high confidence. Consider adjusting stop placement or entry timing.")
        elif exit_reason == 'take_profit' and 'suggested_adjustments' in evaluation:
            if any('tighter stop' in adj.lower() for adj in evaluation['suggested_adjustments']):
                feedback.append("Consider trailing stops for this setup in the future as LLM suggested.")
        
        return "\n".join(feedback) if feedback else ""
    
    def _update_strategy_scores(self):
        """Update strategy scores based on evaluations and performance."""
        for strategy, scores in self.stats["strategy_scores"].items():
            count = scores["count"]
            if count > 0:
                scores["avg_confidence"] = scores["confidence_sum"] / count
                scores["avg_pnl"] = scores["pnl_sum"] / count
                
                # Calculate a score that combines confidence and performance
                confidence_weight = 0.4
                pnl_weight = 0.6
                
                # Normalize confidence (0-100)
                norm_confidence = scores["avg_confidence"] / 100
                
                # Normalize PnL (arbitrary scale)
                # We'll consider $100 per trade a "perfect" result for normalization
                norm_pnl = min(1.0, max(-1.0, scores["avg_pnl"] / 100))
                
                scores["combined_score"] = (
                    confidence_weight * norm_confidence + 
                    pnl_weight * (norm_pnl + 1) / 2  # Convert from [-1,1] to [0,1]
                )
    
    def _determine_current_regime(self) -> str:
        """
        Determine the current market regime.
        
        Returns:
            Market regime string
        """
        try:
            # Use regime classifier to get current regime
            current_regime = self.regime_classifier.classify_regime()
            logger.info(f"Current market regime: {current_regime}")
            return current_regime
        except Exception as e:
            logger.error(f"Error determining market regime: {str(e)}")
            return "neutral"  # Default to neutral if error
    
    def _generate_strategy_allocations(self, current_regime: str) -> Dict[str, float]:
        """
        Generate new strategy allocations based on performance and current regime.
        
        Args:
            current_regime: Current market regime
            
        Returns:
            Dictionary mapping strategies to allocation percentages
        """
        # Get recommended allocations from learning module
        base_allocations = self.learning_module.get_regime_allocations(current_regime)
        
        # Apply adjustments based on recent evaluations
        adjusted_allocations = {}
        
        for strategy, allocation in base_allocations.items():
            # Start with base allocation
            new_allocation = allocation
            
            # Adjust based on recent performance if we have data
            if strategy in self.stats["strategy_scores"]:
                scores = self.stats["strategy_scores"][strategy]
                
                if scores.get("count", 0) >= 3:  # Only adjust if we have enough data
                    # Get combined score
                    combined_score = scores.get("combined_score", 0.5)
                    
                    # Adjust allocation: multiply by factor between 0.5 and 1.5
                    adjustment_factor = 0.5 + combined_score
                    new_allocation = allocation * adjustment_factor
            
            adjusted_allocations[strategy] = new_allocation
        
        # Normalize allocations to sum to 100%
        total = sum(adjusted_allocations.values())
        if total > 0:
            for strategy in adjusted_allocations:
                adjusted_allocations[strategy] = (adjusted_allocations[strategy] / total) * 100
        
        # Record number of adjustments
        self.stats["strategy_adjustments"] = sum(
            1 for s in base_allocations if abs(base_allocations[s] - adjusted_allocations[s]) > 1.0
        )
        
        logger.info(f"Generated new allocations for {current_regime} regime")
        return adjusted_allocations
    
    def _save_strategy_allocations(self, allocations: Dict[str, float], regime: str):
        """
        Save updated strategy allocations to YAML file.
        
        Args:
            allocations: Dictionary mapping strategies to allocation percentages
            regime: Current market regime
        """
        try:
            # Create output structure
            output = {
                "last_updated": datetime.now().isoformat(),
                "market_regime": regime,
                "strategy_allocations": {k: round(v, 2) for k, v in allocations.items()},
                "regime_specific_allocations": {}
            }
            
            # Get regime-specific allocations for all regimes
            for r in ["bullish", "moderately_bullish", "neutral", 
                     "moderately_bearish", "bearish", "volatile", "sideways"]:
                regime_allocs = self.learning_module.get_regime_allocations(r)
                output["regime_specific_allocations"][r] = {
                    k: round(v, 2) for k, v in regime_allocs.items()
                }
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_config_path), exist_ok=True)
            
            # Save to YAML file
            with open(self.output_config_path, 'w') as f:
                yaml.dump(output, f, default_flow_style=False)
            
            logger.info(f"Saved updated strategy allocations to {self.output_config_path}")
            console.print(f"[green]✓[/green] Updated strategy allocations saved to {self.output_config_path}")
            
        except Exception as e:
            logger.error(f"Error saving strategy allocations: {str(e)}")
            console.print(f"[red]✗[/red] Failed to save strategy allocations: {str(e)}")
    
    def _display_results(self, current_regime: str):
        """
        Display the results of the daily review.
        
        Args:
            current_regime: Current market regime
        """
        console.print("\n[bold]Daily Review Results[/bold]")
        
        # Display statistics
        stats_table = Table(title="Review Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Trades Reviewed", str(self.stats["total_trades"]))
        stats_table.add_row("Trades Evaluated", str(self.stats["evaluated_trades"]))
        stats_table.add_row("Strategy Adjustments", str(self.stats["strategy_adjustments"]))
        stats_table.add_row("Current Market Regime", current_regime)
        
        console.print(stats_table)
        
        # Display strategy scores
        if self.stats["strategy_scores"]:
            scores_table = Table(title="Strategy Scores")
            scores_table.add_column("Strategy", style="blue")
            scores_table.add_column("Trades", style="green")
            scores_table.add_column("Avg Confidence", style="green")
            scores_table.add_column("Avg P&L", style="green")
            scores_table.add_column("Score", style="green")
            
            for strategy, scores in sorted(
                self.stats["strategy_scores"].items(), 
                key=lambda x: x[1].get("combined_score", 0), 
                reverse=True
            ):
                count = scores.get("count", 0)
                if count > 0:
                    scores_table.add_row(
                        strategy,
                        str(count),
                        f"{scores.get('avg_confidence', 0):.1f}",
                        f"${scores.get('avg_pnl', 0):.2f}",
                        f"{scores.get('combined_score', 0):.2f}"
                    )
            
            console.print(scores_table)
        
        # Display updated allocations
        allocations = self.learning_module.get_regime_allocations(current_regime)
        
        if allocations:
            alloc_table = Table(title=f"Updated Strategy Allocations for {current_regime}")
            alloc_table.add_column("Strategy", style="blue")
            alloc_table.add_column("Allocation %", style="green")
            
            for strategy, alloc in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
                alloc_table.add_row(strategy, f"{alloc:.2f}%")
            
            console.print(alloc_table)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Daily trade review and strategy adaptation")
    parser.add_argument("--date", help="Date to review in YYYY-MM-DD format (default: yesterday)")
    parser.add_argument("--config", default="configs/config.json", help="Path to configuration file")
    parser.add_argument("--journal-dir", default="trade_journal", help="Trade journal directory")
    parser.add_argument("--output", default="configs/strategy_allocation_weights.yaml", help="Output config path")
    
    args = parser.parse_args()
    
    # Initialize and run reviewer
    reviewer = DailyTradeReviewer(
        journal_dir=args.journal_dir,
        config_path=args.config,
        output_config_path=args.output
    )
    
    reviewer.run_daily_review(args.date) 