"""
Autonomous Trading UI

This module provides the Streamlit UI for the autonomous trading system,
connecting to the autonomous engine and displaying strategy candidates
for approval and deployment.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import threading
import logging

# Import autonomous engine
from trading_bot.autonomous.autonomous_engine import AutonomousEngine

# Configure logging
logger = logging.getLogger("autonomous_ui")
logger.setLevel(logging.INFO)

class AutonomousUI:
    """
    Streamlit UI for the autonomous trading system.
    Connects to the autonomous engine for strategy generation,
    backtesting, evaluation, and deployment.
    """
    
    def __init__(self):
        """Initialize the autonomous trading UI"""
        # Initialize engine
        self.engine = AutonomousEngine()
        
        # Create data directories
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "autonomous"
        )
        os.makedirs(data_dir, exist_ok=True)
        
        # UI state
        if "autonomous_refresh_counter" not in st.session_state:
            st.session_state.autonomous_refresh_counter = 0
    
    def render(self):
        """Render the autonomous trading UI"""
        st.markdown('<div class="sub-header">🤖 Autonomous Trading System</div>', unsafe_allow_html=True)
        
        # Create columns for control panel and results display
        control_col, results_col = st.columns([1, 3])
        
        with control_col:
            self._render_control_panel()
        
        with results_col:
            self._render_results_panel()
        
        # Auto-refresh when engine is running
        if self.engine.is_running:
            # Use a key based on the counter to force a refresh
            st.empty().markdown(f"<div id='refresh-{st.session_state.autonomous_refresh_counter}'></div>", unsafe_allow_html=True)
            
            # Schedule the next refresh
            if st.session_state.autonomous_refresh_counter < 100:  # Prevent infinite refreshes
                st.session_state.autonomous_refresh_counter += 1
                
                # Auto-refresh every 2 seconds during active processing
                st.rerun()
    
    def _render_control_panel(self):
        """Render the control panel for configuring the autonomous system"""
        st.markdown("### Control Panel")
        
        # Status information
        status = self.engine.get_status()
        
        # Data source indicator - check if real data is being used
        data_source = "🟢 REAL MARKET DATA" if getattr(self.engine, "using_real_data", False) else "🟠 SIMULATED DATA"
        st.info(f"**Data Source:** {data_source}")
        
        # Market status - in a real implementation this would check actual market hours
        market_hours = self._check_market_hours()
        market_status = "🟢 OPEN" if market_hours["is_open"] else "🔴 CLOSED"
        next_event = f"Closes {market_hours['next_event_time']}" if market_hours["is_open"] else f"Opens {market_hours['next_event_time']}"
        
        st.markdown(f"**Market Status:** {market_status} - {next_event}")
        
        # Process status
        if status["is_running"]:
            st.success(f"**Process Status:** 🟢 Running - {status['current_phase'].title()}")
            st.progress(status["progress"] / 100, status["status_message"])
        else:
            st.warning(f"**Process Status:** ⚪ Idle")
            
            # Configuration options (only show when not running)
            st.markdown("### Configuration")
            
            # Market universe selection
            universe = st.selectbox(
                "Securities Universe",
                [
                    "Nasdaq 100", 
                    "S&P 500", 
                    "Dow Jones 30", 
                    "Russell 2000", 
                    "Crypto Top 20", 
                    "Forex Majors"
                ],
                index=0
            )
            
            # Strategy types
            strategy_types = st.multiselect(
                "Strategy Types to Consider",
                [
                    "Momentum", 
                    "Mean Reversion", 
                    "Trend Following", 
                    "Volatility Breakout", 
                    "Machine Learning"
                ],
                default=["Momentum", "Mean Reversion", "Trend Following"]
            )
            
            # Performance thresholds
            st.markdown("### Performance Thresholds")
            
            thresholds = {}
            
            thresholds["min_sharpe_ratio"] = st.slider(
                "Minimum Sharpe Ratio", 
                min_value=0.0, 
                max_value=3.0, 
                value=1.0, 
                step=0.1
            )
            
            thresholds["min_profit_factor"] = st.slider(
                "Minimum Profit Factor", 
                min_value=1.0, 
                max_value=5.0, 
                value=1.5, 
                step=0.1
            )
            
            thresholds["max_drawdown"] = st.slider(
                "Maximum Drawdown (%)", 
                min_value=5.0, 
                max_value=50.0, 
                value=20.0, 
                step=1.0
            )
            
            thresholds["min_win_rate"] = st.slider(
                "Minimum Win Rate (%)", 
                min_value=30.0, 
                max_value=80.0, 
                value=50.0, 
                step=1.0
            )
            
            # Action buttons
            if st.button("🚀 Launch Autonomous Process", use_container_width=True, type="primary"):
                # Start the autonomous process
                self.engine.start_process(
                    universe=universe,
                    strategy_types=strategy_types,
                    thresholds=thresholds
                )
                st.session_state.autonomous_refresh_counter = 0
                st.rerun()
        
        # Stop button (only show when running)
        if status["is_running"]:
            if st.button("⏹️ Stop Process", use_container_width=True):
                self.engine.stop_process()
                st.rerun()
        
        # Additional information
        st.markdown("### System Information")
        
        if status["candidates_count"] > 0:
            st.metric("Total Strategies", str(status["candidates_count"]))
            st.metric("Meeting Criteria", str(status["top_candidates_count"]))
            
            # Calculate approval rate
            if status["candidates_count"] > 0:
                approval_rate = (status["top_candidates_count"] / status["candidates_count"]) * 100
                st.metric("Approval Rate", f"{approval_rate:.1f}%")
    
    def _render_results_panel(self):
        """Render the results panel for displaying strategy candidates"""
        # Get status
        status = self.engine.get_status()
        
        # Different content based on whether process has been run
        if status["candidates_count"] > 0:
            # Display results
            st.markdown("### Generated Strategies Ready for Approval")
            
            # Create tabs for different views
            strategy_tabs = st.tabs(["Top Performers", "All Strategies", "Historical Performance"])
            
            with strategy_tabs[0]:
                self._render_top_performers()
            
            with strategy_tabs[1]:
                self._render_all_strategies()
            
            with strategy_tabs[2]:
                self._render_historical_performance()
        
        elif status["is_running"]:
            # Show progress information
            st.info(f"🔄 {status['status_message']} Progress: {status['progress']}%")
            
            # Placeholder visualization
            st.markdown("### Process Visualization")
            
            # Create placeholders for various stages
            stages = [
                "Market Scanning",
                "Strategy Generation",
                "Backtesting",
                "Performance Evaluation", 
                "Preparing Results"
            ]
            
            # Determine active stage based on progress
            active_stage = min(int(status["progress"] / 20), len(stages) - 1)
            
            # Display stages with highlighting for active stage
            for i, stage in enumerate(stages):
                if i < active_stage:
                    st.markdown(f"✅ **{stage}** - Completed")
                elif i == active_stage:
                    st.markdown(f"🔄 **{stage}** - In Progress...")
                else:
                    st.markdown(f"⚪ **{stage}** - Pending")
        
        else:
            # Initial instructions
            st.info("👈 Click 'Launch Autonomous Process' to start scanning the market, generating and backtesting strategies automatically.")
            
            st.markdown("""
            ### How the Autonomous Trading System Works:
            
            1. **Market Scanning**: The system automatically scans your selected universe of securities using built-in indicators
            
            2. **Strategy Generation**: Based on market conditions, it creates optimized trading strategies
            
            3. **Automated Backtesting**: All generated strategies are backtested without manual configuration
            
            4. **Performance Filtering**: Only strategies meeting your performance thresholds are presented
            
            5. **One-Click Approval**: Review and approve strategies with a single click
            
            6. **Paper Trading Deployment**: Approved strategies are automatically deployed to paper trading
            """)
            
            # Show sample visualization
            st.markdown("### Sample System Output")
            
            # Sample data for visualization
            sample_data = {
                "Strategy": ["Momentum", "Mean Reversion", "Trend Following", "Volatility Breakout", "ML Strategy"],
                "Return (%)": [27.5, 18.2, 22.1, 15.5, 16.8],
                "Sharpe Ratio": [1.85, 1.62, 1.73, 1.35, 1.48],
                "Drawdown (%)": [12.5, 9.8, 15.3, 18.2, 16.5],
                "Win Rate (%)": [62.5, 71.2, 55.8, 48.5, 53.2],
            }
            
            # Create sample performance chart
            fig = go.Figure()
            
            for i, strategy in enumerate(sample_data["Strategy"]):
                fig.add_trace(go.Scatterpolar(
                    r=[
                        sample_data["Return (%)"][i] / 30 * 100,  # Scale to 0-100
                        sample_data["Sharpe Ratio"][i] / 2 * 100,  # Scale to 0-100
                        (30 - sample_data["Drawdown (%)"][i]) / 30 * 100,  # Inverse and scale
                        sample_data["Win Rate (%)"][i],
                        (i % 3) * 20 + 60  # Random trade efficiency
                    ],
                    theta=["Return", "Sharpe", "Low Drawdown", "Win Rate", "Trade Efficiency"],
                    fill="toself",
                    name=strategy
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title="Strategy Performance Comparison",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_top_performers(self):
        """Render the top performers tab"""
        # Get top candidates
        top_candidates = self.engine.get_top_candidates()
        
        if not top_candidates:
            st.info("No strategies meeting criteria yet. Adjust thresholds or run the process.")
            return
        
        st.markdown("#### Top-Performing Strategies")
        st.markdown("These strategies have been automatically generated, backtested, and meet your performance criteria.")
        
        # Convert to dataframe for display
        df_data = []
        
        for candidate in top_candidates:
            df_data.append({
                "Strategy ID": candidate["strategy_id"],
                "Type": candidate["strategy_type"],
                "Universe": candidate["universe"],
                "Return (%)": round(candidate["performance"]["returns"], 1),
                "Sharpe": round(candidate["performance"]["sharpe_ratio"], 2),
                "Drawdown (%)": round(candidate["performance"]["drawdown"], 1),
                "Win Rate (%)": round(candidate["performance"]["win_rate"], 1),
                "Trades": candidate["performance"]["trades_count"],
                "Status": candidate["status"].title()
            })
        
        if df_data:
            strategies_df = pd.DataFrame(df_data)
            
            # Display the dataframe
            st.dataframe(strategies_df, use_container_width=True)
            
            # Show action buttons for each strategy
            st.markdown("#### Strategy Actions")
            
            # Create dynamic columns based on number of strategies (max 3)
            num_cols = min(len(df_data), 3)
            cols = st.columns(num_cols)
            
            # Add buttons for each strategy
            for i, candidate in enumerate(top_candidates[:num_cols]):
                with cols[i % num_cols]:
                    strategy_id = candidate["strategy_id"]
                    strategy_type = candidate["strategy_type"]
                    
                    if candidate["status"] == "backtested" or candidate["status"] == "pending":
                        # Approve button
                        if st.button(f"👍 Approve {strategy_type}", key=f"approve_{strategy_id}", use_container_width=True):
                            self.engine.approve_strategy(strategy_id)
                            st.rerun()
                    
                    elif candidate["status"] == "approved":
                        # Deploy button
                        if st.button(f"🚀 Deploy {strategy_type}", key=f"deploy_{strategy_id}", use_container_width=True):
                            self.engine.deploy_strategy(strategy_id)
                            st.rerun()
                    
                    elif candidate["status"] == "deployed":
                        # Already deployed
                        st.markdown(f"✅ **{strategy_type}** Deployed")
            
            # Option to approve all if any are pending
            pending_candidates = [c for c in top_candidates if c["status"] == "backtested" or c["status"] == "pending"]
            
            if pending_candidates and len(pending_candidates) > 1:
                if st.button("✅ Approve All Strategies", use_container_width=True):
                    for candidate in pending_candidates:
                        self.engine.approve_strategy(candidate["strategy_id"])
                    st.rerun()
    
    def _render_all_strategies(self):
        """Render all strategies tab"""
        # Get all candidates
        all_candidates = self.engine.get_all_candidates()
        
        if not all_candidates:
            st.info("No strategies generated yet. Run the autonomous process to generate strategies.")
            return
        
        st.markdown("#### All Generated Strategies")
        
        # Filter options
        st.markdown("#### Filter Options")
        
        filter_cols = st.columns(4)
        
        with filter_cols[0]:
            strategy_types = ["All"] + list(set(c["strategy_type"] for c in all_candidates))
            filter_type = st.selectbox("Strategy Type", strategy_types)
        
        with filter_cols[1]:
            statuses = ["All", "Pending", "Backtested", "Approved", "Deployed", "Rejected"]
            filter_status = st.selectbox("Status", statuses)
        
        with filter_cols[2]:
            metrics = ["Return (%)", "Sharpe", "Drawdown (%)", "Win Rate (%)", "Trades"]
            sort_by = st.selectbox("Sort By", metrics)
        
        with filter_cols[3]:
            order = st.selectbox("Order", ["Descending", "Ascending"])
        
        # Apply filters
        filtered_candidates = all_candidates
        
        if filter_type != "All":
            filtered_candidates = [c for c in filtered_candidates if c["strategy_type"] == filter_type]
        
        if filter_status != "All":
            filtered_candidates = [c for c in filtered_candidates if c["status"].lower() == filter_status.lower()]
        
        # Convert to dataframe
        df_data = []
        
        for candidate in filtered_candidates:
            df_data.append({
                "Strategy ID": candidate["strategy_id"],
                "Type": candidate["strategy_type"],
                "Universe": candidate["universe"],
                "Return (%)": round(candidate["performance"]["returns"], 1),
                "Sharpe": round(candidate["performance"]["sharpe_ratio"], 2),
                "Drawdown (%)": round(candidate["performance"]["drawdown"], 1),
                "Win Rate (%)": round(candidate["performance"]["win_rate"], 1),
                "Trades": candidate["performance"]["trades_count"],
                "Status": candidate["status"].title(),
                "Meets Criteria": "✅" if candidate["meets_criteria"] else "❌"
            })
        
        if df_data:
            # Sort data
            strategies_df = pd.DataFrame(df_data)
            
            # Apply sorting
            sort_ascending = order == "Ascending"
            strategies_df = strategies_df.sort_values(by=sort_by, ascending=sort_ascending)
            
            # Display the dataframe
            st.dataframe(strategies_df, use_container_width=True)
            
            # Show summary
            st.markdown(f"**Showing {len(strategies_df)} of {len(all_candidates)} strategies**")
        else:
            st.info("No strategies match the current filters.")
    
    def _render_historical_performance(self):
        """Render historical performance tab"""
        # In a real implementation, this would show actual historical data
        # For demo purposes, generate simulated data
        
        st.markdown("#### Autonomous System Performance History")
        
        # Create historical data (simulated for demo)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=12, freq='M')
        
        hist_data = {
            "Date": dates,
            "Strategies Generated": [8, 7, 11, 9, 12, 8, 7, 10, 11, 9, 10, 12],
            "Strategies Approved": [3, 2, 4, 3, 5, 2, 2, 4, 5, 3, 4, 5],
            "Avg Return (%)": [18.2, 15.7, 21.3, 17.8, 20.5, 16.9, 15.5, 19.2, 22.1, 18.5, 19.7, 22.8],
            "Avg Sharpe": [1.42, 1.35, 1.67, 1.51, 1.70, 1.44, 1.40, 1.55, 1.78, 1.52, 1.60, 1.75]
        }
        
        hist_df = pd.DataFrame(hist_data)
        
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hist_df["Date"],
            y=hist_df["Strategies Generated"],
            mode='lines+markers',
            name='Strategies Generated'
        ))
        
        fig.add_trace(go.Scatter(
            x=hist_df["Date"],
            y=hist_df["Strategies Approved"],
            mode='lines+markers',
            name='Strategies Approved'
        ))
        
        fig.add_trace(go.Scatter(
            x=hist_df["Date"],
            y=hist_df["Avg Return (%)"],
            mode='lines+markers',
            name='Avg Return (%)',
            yaxis="y2"
        ))
        
        fig.update_layout(
            title="Strategy Generation and Performance History",
            xaxis_title="Date",
            yaxis_title="Count",
            yaxis2=dict(
                title="Return (%)",
                overlaying="y",
                side="right"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.markdown("#### System Performance Summary")
        
        summary_cols = st.columns(4)
        
        with summary_cols[0]:
            st.metric("Total Strategies Generated", sum(hist_data["Strategies Generated"]))
        
        with summary_cols[1]:
            st.metric("Total Strategies Approved", sum(hist_data["Strategies Approved"]))
        
        with summary_cols[2]:
            approval_rate = sum(hist_data["Strategies Approved"]) / sum(hist_data["Strategies Generated"]) * 100
            st.metric("Approval Rate", f"{approval_rate:.1f}%")
        
        with summary_cols[3]:
            avg_return = sum(hist_data["Avg Return (%)"]) / len(hist_data["Avg Return (%)"])
            st.metric("Average Return", f"{avg_return:.1f}%")
