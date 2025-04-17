import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class BacktestVisualizer:
    """
    A class to create rich visualizations of backtesting results.
    """
    
    def __init__(self, results_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the visualizer with path to results directory.
        
        Args:
            results_dir: Directory containing backtest results
            logger: Logger instance
        """
        self.results_dir = results_dir
        self.output_dir = os.path.join(results_dir, 'visualizations')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        
        # Set default style for matplotlib
        sns.set(style="whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        
        self.logger.info(f"Initialized BacktestVisualizer for results in {results_dir}")
    
    def load_backtest_results(self) -> Dict[str, Any]:
        """
        Load backtest results from CSV and JSON files.
        
        Returns:
            Dictionary containing loaded backtest data
        """
        try:
            # Load summary JSON
            summary_path = os.path.join(self.results_dir, 'summary.json')
            if not os.path.exists(summary_path):
                self.logger.error(f"Summary file not found at {summary_path}")
                return {}
                
            with open(summary_path, 'r') as f:
                summary = json.load(f)
            
            # Load CSV files
            equity_curve = pd.read_csv(
                os.path.join(self.results_dir, 'equity_curve.csv'),
                index_col='date',
                parse_dates=True
            )
            
            daily_returns = pd.read_csv(
                os.path.join(self.results_dir, 'daily_returns.csv'),
                index_col='date',
                parse_dates=True
            )
            
            trades_path = os.path.join(self.results_dir, 'trades.csv')
            if os.path.exists(trades_path):
                trades = pd.read_csv(trades_path, parse_dates=['date'])
            else:
                trades = pd.DataFrame()
            
            # Combine into a results dictionary
            results = {
                'summary': summary,
                'equity_curve': equity_curve,
                'daily_returns': daily_returns,
                'trades': trades
            }
            
            self.logger.info(f"Loaded backtest results for {summary.get('strategy_name', 'unknown strategy')}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error loading backtest results: {str(e)}")
            return {}
    
    def create_all_visualizations(self, save_path: Optional[str] = None, interactive: bool = True) -> None:
        """
        Create and save all visualizations.
        
        Args:
            save_path: Path to save visualizations (defaults to output_dir)
            interactive: Whether to create interactive Plotly charts if available
        """
        results = self.load_backtest_results()
        if not results:
            self.logger.error("No backtest results to visualize")
            return
            
        save_dir = save_path or self.output_dir
        
        # Create visualizations
        self.create_equity_curve_plot(results, save_dir, interactive)
        self.create_returns_distribution_plot(results, save_dir, interactive)
        self.create_performance_metrics_plot(results, save_dir, interactive)
        
        if not results['trades'].empty:
            self.create_trade_analysis_plot(results, save_dir, interactive)
        
        self.logger.info(f"All visualizations created and saved to {save_dir}")
    
    def create_equity_curve_plot(self, results: Dict[str, Any], save_dir: str, interactive: bool = True) -> None:
        """
        Create and save equity curve visualization.
        
        Args:
            results: Dictionary containing backtest results
            save_dir: Directory to save the plot
            interactive: Whether to create interactive Plotly chart
        """
        if not results:
            return
            
        equity_curve = results['equity_curve']
        summary = results['summary']
        
        if equity_curve.empty:
            self.logger.warning("Empty equity curve data, skipping plot")
            return
        
        # Calculate drawdown
        equity_peak = equity_curve['portfolio_value'].cummax()
        drawdown = (equity_curve['portfolio_value'] - equity_peak) / equity_peak
        
        if interactive and PLOTLY_AVAILABLE:
            # Create interactive plotly figure
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=('Equity Curve', 'Drawdown'),
                row_heights=[0.7, 0.3]
            )
            
            # Add equity curve trace
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=equity_curve['portfolio_value'],
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # Add drawdown trace
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=drawdown * 100,  # Convert to percentage
                    mode='lines',
                    name='Drawdown',
                    line=dict(color='red', width=1.5)
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=f"{summary['strategy_name']} - Equity Curve and Drawdown",
                yaxis_title="Portfolio Value ($)",
                yaxis2_title="Drawdown (%)",
                height=800,
                width=1200,
                showlegend=True
            )
            
            # Add annotations for key metrics
            metrics_text = (
                f"Total Return: {summary['total_return']*100:.2f}%<br>"
                f"Annual Return: {summary['performance_metrics']['annual_return']*100:.2f}%<br>"
                f"Sharpe Ratio: {summary['performance_metrics']['sharpe_ratio']:.2f}<br>"
                f"Max Drawdown: {summary['performance_metrics']['max_drawdown']*100:.2f}%"
            )
            
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref="paper",
                yref="paper",
                text=metrics_text,
                showarrow=False,
                font=dict(size=14),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="gray",
                borderwidth=1,
                borderpad=4,
                align="left"
            )
            
            # Save interactive plot
            fig.write_html(os.path.join(save_dir, 'equity_curve_interactive.html'))
            self.logger.info("Created interactive equity curve plot")
            
        else:
            # Create static matplotlib figure
            fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot equity curve
            equity_curve['portfolio_value'].plot(
                ax=axes[0],
                color='blue',
                linewidth=2,
                label='Portfolio Value'
            )
            
            axes[0].set_title(f"{summary['strategy_name']} - Equity Curve")
            axes[0].set_ylabel('Portfolio Value ($)')
            axes[0].legend()
            axes[0].grid(True)
            
            # Plot drawdown
            drawdown.mul(100).plot(  # Convert to percentage
                ax=axes[1],
                color='red',
                linewidth=1.5,
                label='Drawdown'
            )
            
            axes[1].set_title('Drawdown')
            axes[1].set_ylabel('Drawdown (%)')
            axes[1].set_xlabel('Date')
            axes[1].grid(True)
            
            # Add key metrics as text box
            metrics_text = (
                f"Total Return: {summary['total_return']*100:.2f}%\n"
                f"Annual Return: {summary['performance_metrics']['annual_return']*100:.2f}%\n"
                f"Sharpe Ratio: {summary['performance_metrics']['sharpe_ratio']:.2f}\n"
                f"Max Drawdown: {summary['performance_metrics']['max_drawdown']*100:.2f}%"
            )
            
            axes[0].text(
                0.02, 0.98, metrics_text,
                transform=axes[0].transAxes,
                verticalalignment='top',
                horizontalalignment='left',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray')
            )
            
            plt.tight_layout()
            
            # Save static plot
            plt.savefig(os.path.join(save_dir, 'equity_curve.png'), dpi=300)
            plt.close()
            self.logger.info("Created static equity curve plot")
    
    def create_returns_distribution_plot(self, results: Dict[str, Any], save_dir: str, interactive: bool = True) -> None:
        """
        Create and save returns distribution visualization.
        
        Args:
            results: Dictionary containing backtest results
            save_dir: Directory to save the plot
            interactive: Whether to create interactive Plotly chart
        """
        if not results:
            return
            
        daily_returns = results['daily_returns']
        summary = results['summary']
        
        if daily_returns.empty:
            self.logger.warning("Empty returns data, skipping plot")
            return
        
        if interactive and PLOTLY_AVAILABLE:
            # Create interactive plotly figure
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Daily Returns Distribution', 'Daily Returns Over Time')
            )
            
            # Daily returns histogram
            fig.add_trace(
                go.Histogram(
                    x=daily_returns['return'] * 100,  # Convert to percentage
                    name='Daily Returns',
                    marker_color='blue',
                    opacity=0.7,
                    nbinsx=30
                ),
                row=1, col=1
            )
            
            # Daily returns over time
            fig.add_trace(
                go.Bar(
                    x=daily_returns.index,
                    y=daily_returns['return'] * 100,  # Convert to percentage
                    name='Daily Returns',
                    marker_color=daily_returns['return'].apply(
                        lambda x: 'green' if x > 0 else 'red'
                    )
                ),
                row=1, col=2
            )
            
            # Update layout
            fig.update_layout(
                title=f"{summary['strategy_name']} - Returns Analysis",
                height=600,
                width=1200,
                showlegend=False
            )
            
            fig.update_xaxes(title_text="Return (%)", row=1, col=1)
            fig.update_yaxes(title_text="Frequency", row=1, col=1)
            
            fig.update_xaxes(title_text="Date", row=1, col=2)
            fig.update_yaxes(title_text="Return (%)", row=1, col=2)
            
            # Save interactive plot
            fig.write_html(os.path.join(save_dir, 'returns_distribution_interactive.html'))
            self.logger.info("Created interactive returns distribution plot")
            
        else:
            # Create static matplotlib figure
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Daily returns histogram
            sns.histplot(
                daily_returns['return'] * 100,  # Convert to percentage
                kde=True,
                color='blue',
                ax=axes[0],
                bins=30
            )
            axes[0].set_title('Daily Returns Distribution')
            axes[0].set_xlabel('Return (%)')
            axes[0].set_ylabel('Frequency')
            
            # Daily returns over time
            daily_returns['return'].mul(100).plot(  # Convert to percentage
                kind='bar',
                ax=axes[1],
                color=daily_returns['return'].apply(
                    lambda x: 'green' if x > 0 else 'red'
                )
            )
            axes[1].set_title('Daily Returns Over Time')
            axes[1].set_xlabel('Date')
            axes[1].set_ylabel('Return (%)')
            plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=90)
            
            plt.suptitle(f"{summary['strategy_name']} - Returns Analysis", fontsize=16)
            plt.tight_layout()
            plt.subplots_adjust(top=0.92)
            
            # Save static plot
            plt.savefig(os.path.join(save_dir, 'returns_distribution.png'), dpi=300)
            plt.close()
            self.logger.info("Created static returns distribution plot")
    
    def create_performance_metrics_plot(self, results: Dict[str, Any], save_dir: str, interactive: bool = True) -> None:
        """
        Create and save performance metrics visualization.
        
        Args:
            results: Dictionary containing backtest results
            save_dir: Directory to save the plot
            interactive: Whether to create interactive Plotly chart
        """
        if not results:
            return
            
        summary = results['summary']
        metrics = summary['performance_metrics']
        
        # Select key metrics to display
        key_metrics = [
            'annual_return', 
            'sharpe_ratio', 
            'sortino_ratio', 
            'calmar_ratio',
            'max_drawdown', 
            'win_rate', 
            'profit_factor'
        ]
        
        # Format metric values for display
        metric_values = []
        for metric in key_metrics:
            value = metrics[metric]
            if metric in ['annual_return', 'max_drawdown', 'win_rate']:
                # Convert to percentage
                value = value * 100
            metric_values.append(value)
        
        # Format metric names for display
        display_names = [
            'Annual Return (%)', 
            'Sharpe Ratio', 
            'Sortino Ratio', 
            'Calmar Ratio',
            'Max Drawdown (%)', 
            'Win Rate (%)', 
            'Profit Factor'
        ]
        
        # Determine colors based on values
        colors = []
        for i, metric in enumerate(key_metrics):
            if metric == 'max_drawdown':
                colors.append('red')  # Drawdown is always bad
            else:
                colors.append('green' if metric_values[i] > 0 else 'red')
        
        if interactive and PLOTLY_AVAILABLE:
            # Create interactive plotly figure
            fig = go.Figure()
            
            fig.add_trace(
                go.Bar(
                    x=display_names,
                    y=metric_values,
                    marker_color=colors,
                    text=[f"{val:.2f}" for val in metric_values],
                    textposition='auto',
                )
            )
            
            # Update layout
            fig.update_layout(
                title=f"{summary['strategy_name']} - Performance Metrics",
                xaxis_title="Metric",
                yaxis_title="Value",
                height=600,
                width=1000,
                showlegend=False
            )
            
            # Save interactive plot
            fig.write_html(os.path.join(save_dir, 'performance_metrics_interactive.html'))
            self.logger.info("Created interactive performance metrics plot")
            
        else:
            # Create static matplotlib figure
            plt.figure(figsize=(12, 6))
            
            bars = plt.bar(display_names, metric_values, color=colors)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:.2f}",
                    ha='center',
                    va='bottom' if height > 0 else 'top',
                    fontsize=10
                )
            
            plt.title(f"{summary['strategy_name']} - Performance Metrics")
            plt.ylabel('Value')
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save static plot
            plt.savefig(os.path.join(save_dir, 'performance_metrics.png'), dpi=300)
            plt.close()
            self.logger.info("Created static performance metrics plot")
    
    def create_trade_analysis_plot(self, results: Dict[str, Any], save_dir: str, interactive: bool = True) -> None:
        """
        Create and save trade analysis visualization.
        
        Args:
            results: Dictionary containing backtest results
            save_dir: Directory to save the plot
            interactive: Whether to create interactive Plotly chart
        """
        if not results or results['trades'].empty:
            self.logger.warning("No trade data to visualize")
            return
            
        trades = results['trades']
        summary = results['summary']
        
        # Calculate trade statistics by symbol
        trades_by_symbol = trades.groupby('symbol').agg({
            'symbol': 'count',
        }).rename(columns={'symbol': 'trade_count'})
        
        # Calculate profit/loss by symbol if possible
        has_pnl = False
        
        if 'side' in trades.columns and 'cost' in trades.columns:
            buy_trades = trades[trades['side'] == 'buy'].copy()
            sell_trades = trades[trades['side'] == 'sell'].copy()
            
            if not buy_trades.empty and not sell_trades.empty:
                symbol_pnl = {}
                for symbol in trades['symbol'].unique():
                    symbol_buys = buy_trades[buy_trades['symbol'] == symbol]['cost'].sum()
                    symbol_sells = sell_trades[sell_trades['symbol'] == symbol]['cost'].sum()
                    commissions = trades[trades['symbol'] == symbol]['commission'].sum() if 'commission' in trades.columns else 0
                    slippage = trades[trades['symbol'] == symbol]['slippage'].sum() if 'slippage' in trades.columns else 0
                    
                    symbol_pnl[symbol] = symbol_sells - symbol_buys - commissions - slippage
                
                trades_by_symbol['pnl'] = pd.Series(symbol_pnl)
                has_pnl = True
        
        if interactive and PLOTLY_AVAILABLE:
            # Create interactive plotly figure
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Trade Count by Symbol', 'P&L by Symbol' if has_pnl else 'Trade Count by Symbol'),
                specs=[[{"type": "pie"}, {"type": "bar"}]]
            )
            
            # Trade count by symbol (pie chart)
            fig.add_trace(
                go.Pie(
                    labels=trades_by_symbol.index,
                    values=trades_by_symbol['trade_count'],
                    hole=0.4,
                    textinfo='label+percent',
                    marker_colors=px.colors.qualitative.Plotly
                ),
                row=1, col=1
            )
            
            # P&L by symbol if available
            if has_pnl:
                fig.add_trace(
                    go.Bar(
                        x=trades_by_symbol.index,
                        y=trades_by_symbol['pnl'],
                        marker_color=trades_by_symbol['pnl'].apply(
                            lambda x: 'green' if x > 0 else 'red'
                        ),
                        text=trades_by_symbol['pnl'].apply(
                            lambda x: f"${x:.2f}"
                        ),
                        textposition='auto'
                    ),
                    row=1, col=2
                )
            
            # Update layout
            fig.update_layout(
                title=f"{summary['strategy_name']} - Trade Analysis",
                height=600,
                width=1200,
                showlegend=False
            )
            
            # Save interactive plot
            fig.write_html(os.path.join(save_dir, 'trade_analysis_interactive.html'))
            self.logger.info("Created interactive trade analysis plot")
            
        else:
            # Create static matplotlib figure
            fig, axes = plt.subplots(1, 2, figsize=(14, 7))
            
            # Trade count by symbol (pie chart)
            axes[0].pie(
                trades_by_symbol['trade_count'],
                labels=trades_by_symbol.index,
                autopct='%1.1f%%',
                startangle=90,
                wedgeprops={'edgecolor': 'white'}
            )
            axes[0].set_title('Trade Count by Symbol')
            
            # P&L by symbol if available
            if has_pnl:
                bars = axes[1].bar(
                    trades_by_symbol.index,
                    trades_by_symbol['pnl'],
                    color=trades_by_symbol['pnl'].apply(
                        lambda x: 'green' if x > 0 else 'red'
                    )
                )
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    axes[1].text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f"${height:.2f}",
                        ha='center',
                        va='bottom' if height > 0 else 'top',
                        fontsize=10
                    )
                
                axes[1].set_title('P&L by Symbol')
                axes[1].set_ylabel('Profit/Loss ($)')
                axes[1].grid(True, axis='y')
            
            plt.suptitle(f"{summary['strategy_name']} - Trade Analysis", fontsize=16)
            plt.tight_layout()
            plt.subplots_adjust(top=0.88)
            
            # Save static plot
            plt.savefig(os.path.join(save_dir, 'trade_analysis.png'), dpi=300)
            plt.close()
            self.logger.info("Created static trade analysis plot") 