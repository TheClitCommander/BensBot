#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Monitoring Dashboard for BensBot

This dashboard monitors the enhanced reliability and efficiency components:
1. Persistence Layer (MongoDB)
2. Watchdog & Fault Tolerance
3. Dynamic Capital Scaling
4. Strategy Retirement & Promotion
5. Execution Quality Modeling

Run with: streamlit run enhanced_monitoring_dashboard.py
"""

import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from pymongo import MongoClient
import requests

# Add the project root to the Python path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Try to import the enhanced components
try:
    from trading_bot.data.persistence import PersistenceManager
    from trading_bot.core.watchdog import ServiceWatchdog, ServiceStatus
    from trading_bot.risk.capital_manager import CapitalManager
    from trading_bot.core.strategy_manager import StrategyPerformanceManager, StrategyStatus
    from trading_bot.execution.execution_model import ExecutionQualityModel
    
    COMPONENTS_IMPORTED = True
except ImportError as e:
    st.warning(f"Failed to import enhanced components: {e}")
    COMPONENTS_IMPORTED = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="BensBot Enhanced Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for connection details
if "mongodb_uri" not in st.session_state:
    st.session_state["mongodb_uri"] = "mongodb://localhost:27017/"
    
if "mongodb_database" not in st.session_state:
    st.session_state["mongodb_database"] = "bensbot"
    
if "api_base_url" not in st.session_state:
    st.session_state["api_base_url"] = "http://localhost:8000"
    
if "persistence" not in st.session_state:
    st.session_state["persistence"] = None
    
if "connected" not in st.session_state:
    st.session_state["connected"] = False
    
if "refresh_interval" not in st.session_state:
    st.session_state["refresh_interval"] = 10  # seconds

def connect_to_mongodb():
    """Connect to the MongoDB server using PersistenceManager"""
    try:
        uri = st.session_state["mongodb_uri"]
        database = st.session_state["mongodb_database"]
        
        # Use PersistenceManager if available, otherwise use direct connection
        if COMPONENTS_IMPORTED:
            persistence = PersistenceManager(
                connection_string=uri,
                database=database,
                auto_connect=True
            )
            st.session_state["persistence"] = persistence
            st.session_state["connected"] = persistence.is_connected()
            return persistence.is_connected()
        else:
            # Direct MongoDB connection
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')  # Check connection
            st.session_state["client"] = client
            st.session_state["db"] = client[database]
            st.session_state["connected"] = True
            return True
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {str(e)}")
        st.session_state["connected"] = False
        return False

def header():
    """Render the dashboard header"""
    st.title("BensBot Enhanced Monitoring Dashboard")
    
    # Current time and auto-refresh
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown(f"**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    with col2:
        st.session_state["refresh_interval"] = st.slider(
            "Auto-refresh interval (seconds)",
            min_value=5,
            max_value=60,
            value=st.session_state["refresh_interval"],
            step=5
        )
        
    with col3:
        if st.button("Refresh Now"):
            st.experimental_rerun()

def sidebar():
    """Render the dashboard sidebar"""
    st.sidebar.title("BensBot Monitor")
    
    st.sidebar.header("Connection Settings")
    
    # MongoDB connection settings
    st.sidebar.subheader("MongoDB")
    st.session_state["mongodb_uri"] = st.sidebar.text_input(
        "MongoDB URI",
        value=st.session_state["mongodb_uri"]
    )
    
    st.session_state["mongodb_database"] = st.sidebar.text_input(
        "Database Name",
        value=st.session_state["mongodb_database"]
    )
    
    # API connection settings
    st.sidebar.subheader("API")
    st.session_state["api_base_url"] = st.sidebar.text_input(
        "API Base URL",
        value=st.session_state["api_base_url"]
    )
    
    # Connect button
    if st.sidebar.button("Connect"):
        with st.spinner("Connecting to MongoDB..."):
            if connect_to_mongodb():
                st.sidebar.success("Connected to MongoDB!")
            else:
                st.sidebar.error("Failed to connect to MongoDB")
    
    # Navigation
    st.sidebar.header("Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        [
            "Overview",
            "Persistence Monitor",
            "Watchdog Monitor",
            "Capital Management",
            "Strategy Performance",
            "Execution Quality"
        ]
    )
    
    return page

def fetch_system_health():
    """Fetch system health data from API or MongoDB"""
    try:
        # Try API first
        api_url = f"{st.session_state['api_base_url']}/health"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        # API failed, try MongoDB directly
        pass
        
    # Fallback to MongoDB for health data
    if st.session_state["connected"]:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Get logs from persistence manager
            logs_df = st.session_state["persistence"].get_system_logs(
                level="ERROR",
                limit=10
            )
            
            # Check collections stats
            health_data = {
                "status": "healthy" if st.session_state["connected"] else "unhealthy",
                "components": {
                    "persistence": "online" if st.session_state["connected"] else "offline",
                    "watchdog": "unknown",
                    "trading_engine": "unknown"
                },
                "errors": len(logs_df) if not logs_df.empty else 0,
                "last_update": datetime.now().isoformat()
            }
            
            return health_data
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            
            # Check collections
            collections = {
                "trades": db.trades.count_documents({}),
                "strategy_states": db.strategy_states.count_documents({}),
                "performance": db.performance.count_documents({}),
                "logs": db.system_logs.count_documents({})
            }
            
            # Check for recent errors
            recent_errors = db.system_logs.count_documents({
                "level": "ERROR",
                "timestamp": {"$gte": datetime.now() - timedelta(hours=1)}
            })
            
            health_data = {
                "status": "healthy" if st.session_state["connected"] else "unhealthy",
                "components": {
                    "persistence": "online" if st.session_state["connected"] else "offline",
                    "collections": collections
                },
                "errors": recent_errors,
                "last_update": datetime.now().isoformat()
            }
            
            return health_data
    
    # No connection, return dummy data
    return {
        "status": "unknown",
        "components": {},
        "errors": 0,
        "last_update": datetime.now().isoformat()
    }

def overview_page():
    """Render the overview page"""
    st.header("System Overview")
    
    # Fetch health data
    health_data = fetch_system_health()
    
    # Display health status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("System Status")
        status = health_data.get("status", "unknown")
        
        if status == "healthy":
            st.success("Healthy")
        elif status == "degraded":
            st.warning("Degraded")
        elif status == "unhealthy":
            st.error("Unhealthy")
        else:
            st.info("Unknown")
            
        st.text(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        st.subheader("Component Status")
        components = health_data.get("components", {})
        
        for component, status in components.items():
            if status == "online":
                st.success(f"{component.title()}: Online")
            elif status == "offline":
                st.error(f"{component.title()}: Offline")
            elif status == "degraded":
                st.warning(f"{component.title()}: Degraded")
            else:
                st.info(f"{component.title()}: Unknown")
    
    with col3:
        st.subheader("Recent Issues")
        error_count = health_data.get("errors", 0)
        
        if error_count == 0:
            st.success("No recent errors")
        else:
            st.error(f"{error_count} errors in the last hour")
    
    # Display key metrics
    st.header("Key Metrics")
    
    if st.session_state["connected"]:
        # Fetch data from MongoDB
        try:
            if COMPONENTS_IMPORTED and st.session_state["persistence"]:
                # Use persistence manager
                persistence = st.session_state["persistence"]
                trades_df = persistence.get_trades_history(limit=1000)
                performance_df = persistence.get_performance_history(limit=100)
                
                if not trades_df.empty:
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    
                    with metric_col1:
                        st.metric(
                            "Total Trades",
                            len(trades_df)
                        )
                    
                    with metric_col2:
                        # Calculate win rate
                        if 'win' in trades_df.columns:
                            win_rate = trades_df['win'].mean() * 100
                            st.metric(
                                "Win Rate",
                                f"{win_rate:.1f}%"
                            )
                        else:
                            st.metric("Win Rate", "N/A")
                    
                    with metric_col3:
                        # Calculate profit
                        if 'profit_loss' in trades_df.columns:
                            total_profit = trades_df['profit_loss'].sum()
                            st.metric(
                                "Total P&L",
                                f"${total_profit:.2f}"
                            )
                        else:
                            st.metric("Total P&L", "N/A")
                    
                    with metric_col4:
                        # Calculate active strategies
                        if 'strategy_id' in trades_df.columns:
                            active_strategies = trades_df['strategy_id'].nunique()
                            st.metric(
                                "Active Strategies",
                                active_strategies
                            )
                        else:
                            st.metric("Active Strategies", "N/A")
            else:
                # Direct MongoDB access
                db = st.session_state["db"]
                trades_count = db.trades.count_documents({})
                
                # Calculate metrics
                win_count = db.trades.count_documents({"win": True})
                total_pl = sum(trade.get("profit_loss", 0) for trade in db.trades.find({}, {"profit_loss": 1}))
                active_strategies = len(db.strategy_states.distinct("strategy_id"))
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("Total Trades", trades_count)
                
                with metric_col2:
                    win_rate = (win_count / trades_count * 100) if trades_count > 0 else 0
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with metric_col3:
                    st.metric("Total P&L", f"${total_pl:.2f}")
                
                with metric_col4:
                    st.metric("Active Strategies", active_strategies)
        except Exception as e:
            st.error(f"Error fetching metrics: {str(e)}")
    else:
        st.warning("Connect to MongoDB to view metrics")
        
        # Example charts with dummy data
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("Total Trades", "N/A")
        
        with metric_col2:
            st.metric("Win Rate", "N/A")
        
        with metric_col3:
            st.metric("Total P&L", "N/A")
        
        with metric_col4:
            st.metric("Active Strategies", "N/A")

    # Auto-refresh functionality
    time.sleep(1)  # Small delay to prevent excessive refreshing
    st.experimental_rerun()

def persistence_page():
    """Render the persistence monitor page"""
    st.header("Persistence Layer Monitor")
    
    if not st.session_state["connected"]:
        st.warning("Not connected to MongoDB. Please connect using the sidebar.")
        return
    
    # Display connection info
    st.subheader("Connection Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"**URI:** {st.session_state['mongodb_uri']}")
        st.markdown(f"**Database:** {st.session_state['mongodb_database']}")
    
    with info_col2:
        status = "Connected" if st.session_state["connected"] else "Disconnected"
        status_color = "green" if st.session_state["connected"] else "red"
        st.markdown(f"**Status:** <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
    
    # Collection statistics
    st.subheader("Collection Statistics")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            
            # Display collection stats
            col_stats = [
                {"Collection": "trades", "Documents": len(persistence.get_trades_history(limit=1000000))},
                {"Collection": "strategy_states", "Documents": len(persistence.load_strategy_state("") or [])},
                {"Collection": "performance", "Documents": len(persistence.get_performance_history(limit=1000000))},
                {"Collection": "logs", "Documents": len(persistence.get_system_logs(limit=1000000))}
            ]
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            
            # Get collection stats
            col_stats = []
            for collection_name in ["trades", "strategy_states", "performance", "system_logs"]:
                count = db[collection_name].count_documents({})
                col_stats.append({"Collection": collection_name, "Documents": count})
        
        # Display as table
        col_stats_df = pd.DataFrame(col_stats)
        st.table(col_stats_df)
    except Exception as e:
        st.error(f"Error getting collection statistics: {str(e)}")
    
    # Recent trades
    st.subheader("Recent Trades")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            trades_df = persistence.get_trades_history(limit=10)
            
            if not trades_df.empty:
                st.dataframe(trades_df)
            else:
                st.info("No trades found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            trades = list(db.trades.find().sort("timestamp", -1).limit(10))
            
            if trades:
                trades_df = pd.DataFrame(trades)
                st.dataframe(trades_df)
            else:
                st.info("No trades found")
    except Exception as e:
        st.error(f"Error getting recent trades: {str(e)}")
    
    # System logs
    st.subheader("Recent System Logs")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            logs_df = persistence.get_system_logs(limit=10)
            
            if not logs_df.empty:
                st.dataframe(logs_df)
            else:
                st.info("No logs found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            logs = list(db.system_logs.find().sort("timestamp", -1).limit(10))
            
            if logs:
                logs_df = pd.DataFrame(logs)
                st.dataframe(logs_df)
            else:
                st.info("No logs found")
    except Exception as e:
        st.error(f"Error getting system logs: {str(e)}")

def watchdog_page():
    """Render the watchdog monitor page"""
    st.header("Watchdog & Fault Tolerance Monitor")
    
    # Fetch service status
    try:
        api_url = f"{st.session_state['api_base_url']}/watchdog/status"
        
        try:
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                watchdog_data = response.json()
            else:
                watchdog_data = None
        except Exception:
            watchdog_data = None
            
        # If API failed, try MongoDB
        if watchdog_data is None and st.session_state["connected"]:
            if COMPONENTS_IMPORTED and st.session_state["persistence"]:
                logs_df = st.session_state["persistence"].get_system_logs(
                    component="ServiceWatchdog",
                    limit=100
                )
                
                # Extract service status from logs
                watchdog_data = {
                    "running": True,
                    "services": {},
                    "system_health": {
                        "overall_status": "UNKNOWN",
                        "service_count": 0,
                        "uptime_seconds": 0
                    }
                }
            else:
                db = st.session_state["db"]
                logs = list(db.system_logs.find(
                    {"component": "ServiceWatchdog"}
                ).sort("timestamp", -1).limit(100))
                
                # Extract service status from logs
                watchdog_data = {
                    "running": len(logs) > 0,
                    "services": {},
                    "system_health": {
                        "overall_status": "UNKNOWN",
                        "service_count": 0,
                        "uptime_seconds": 0
                    }
                }
                
                # Extract service statuses from logs if possible
                for log in logs:
                    if "data" in log and "service" in log["data"]:
                        service_name = log["data"]["service"]
                        if service_name not in watchdog_data["services"]:
                            watchdog_data["services"][service_name] = {
                                "status": log["data"].get("status", "UNKNOWN"),
                                "last_check": log["timestamp"]
                            }
        
        # Display watchdog status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Watchdog Status")
            
            if watchdog_data:
                running = watchdog_data.get("running", False)
                status_color = "green" if running else "red"
                st.markdown(f"**Status:** <span style='color:{status_color}'>{'Running' if running else 'Stopped'}</span>", unsafe_allow_html=True)
                
                # System health
                system_health = watchdog_data.get("system_health", {})
                overall_status = system_health.get("overall_status", "UNKNOWN")
                
                if overall_status == "HEALTHY":
                    st.success(f"Overall Health: {overall_status}")
                elif overall_status == "DEGRADED":
                    st.warning(f"Overall Health: {overall_status}")
                elif overall_status == "UNHEALTHY":
                    st.error(f"Overall Health: {overall_status}")
                else:
                    st.info(f"Overall Health: {overall_status}")
                
                # Uptime
                uptime_seconds = system_health.get("uptime_seconds", 0)
                uptime_str = str(timedelta(seconds=uptime_seconds))
                st.markdown(f"**Uptime:** {uptime_str}")
                
                # Service count
                service_count = system_health.get("service_count", 0)
                st.markdown(f"**Monitored Services:** {service_count}")
            else:
                st.error("Watchdog status not available")
        
        with col2:
            st.subheader("Services Health")
            
            if watchdog_data and "services" in watchdog_data:
                services = watchdog_data["services"]
                
                for service_name, service_data in services.items():
                    status = service_data.get("status", "UNKNOWN")
                    
                    if status == "HEALTHY":
                        st.success(f"{service_name}: {status}")
                    elif status == "DEGRADED":
                        st.warning(f"{service_name}: {status}")
                    elif status == "UNHEALTHY" or status == "FAILED":
                        st.error(f"{service_name}: {status}")
                    else:
                        st.info(f"{service_name}: {status}")
            else:
                st.info("No service health data available")
        
        # Service details
        st.subheader("Service Details")
        
        if watchdog_data and "services" in watchdog_data:
            services = watchdog_data["services"]
            
            # Create table data
            table_data = []
            for service_name, service_data in services.items():
                failures = service_data.get("failures", 0)
                recovery_attempts = service_data.get("recovery_attempts", 0)
                last_failure = service_data.get("last_failure", "N/A")
                last_recovery = service_data.get("last_recovery", "N/A")
                
                table_data.append({
                    "Service": service_name,
                    "Status": service_data.get("status", "UNKNOWN"),
                    "Failures": failures,
                    "Recovery Attempts": recovery_attempts,
                    "Last Failure": last_failure,
                    "Last Recovery": last_recovery
                })
            
            if table_data:
                st.table(pd.DataFrame(table_data))
            else:
                st.info("No service details available")
        else:
            st.info("No service details available")
        
        # Recovery history
        st.subheader("Recovery History")
        
        if st.session_state["connected"]:
            try:
                if COMPONENTS_IMPORTED and st.session_state["persistence"]:
                    # Use persistence manager
                    persistence = st.session_state["persistence"]
                    recovery_logs = persistence.get_system_logs(
                        component="ServiceWatchdog",
                        limit=20
                    )
                    
                    if not recovery_logs.empty:
                        st.dataframe(recovery_logs)
                    else:
                        st.info("No recovery history found")
                else:
                    # Direct MongoDB access
                    db = st.session_state["db"]
                    recovery_logs = list(db.system_logs.find(
                        {"component": "ServiceWatchdog", "message": {"$regex": "Recovery"}}
                    ).sort("timestamp", -1).limit(20))
                    
                    if recovery_logs:
                        st.dataframe(pd.DataFrame(recovery_logs))
                    else:
                        st.info("No recovery history found")
            except Exception as e:
                st.error(f"Error getting recovery history: {str(e)}")
    except Exception as e:
        st.error(f"Error loading watchdog data: {str(e)}")

def capital_management_page():
    """Render the capital management page"""
    st.header("Dynamic Capital Management")
    
    if not st.session_state["connected"]:
        st.warning("Not connected to MongoDB. Please connect using the sidebar.")
        return
    
    # Capital overview section
    st.subheader("Capital Overview")
    
    try:
        # Fetch capital data
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            capital_state = persistence.load_strategy_state("capital_manager")
            
            if capital_state:
                # Display capital metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    initial_capital = capital_state.get("initial_capital", 0)
                    st.metric(
                        "Initial Capital",
                        f"${initial_capital:,.2f}"
                    )
                
                with col2:
                    current_capital = capital_state.get("current_capital", 0)
                    change = current_capital - initial_capital
                    st.metric(
                        "Current Capital",
                        f"${current_capital:,.2f}",
                        delta=f"${change:+,.2f}"
                    )
                
                with col3:
                    max_capital = capital_state.get("max_capital", 0)
                    st.metric(
                        "Peak Capital",
                        f"${max_capital:,.2f}"
                    )
                
                with col4:
                    drawdown = capital_state.get("current_drawdown_pct", 0) * 100
                    max_drawdown = capital_state.get("max_drawdown_pct", 0) * 100
                    st.metric(
                        "Current Drawdown",
                        f"{drawdown:.2f}%",
                        delta=f"{max_drawdown-drawdown:.2f}% from max",
                        delta_color="inverse"
                    )
                
                # Capital history chart
                st.subheader("Capital History")
                
                # Fetch capital history
                capital_history = persistence.get_performance_history(
                    metric_type="capital",
                    limit=100
                )
                
                if not capital_history.empty:
                    # Create capital chart
                    fig = px.line(
                        capital_history,
                        x="timestamp",
                        y="value",
                        title="Capital Over Time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No capital history data available")
            else:
                st.info("No capital manager state found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            capital_state = db.strategy_states.find_one({"strategy_id": "capital_manager"})
            
            if capital_state:
                # Display capital metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    initial_capital = capital_state.get("data", {}).get("initial_capital", 0)
                    st.metric(
                        "Initial Capital",
                        f"${initial_capital:,.2f}"
                    )
                
                with col2:
                    current_capital = capital_state.get("data", {}).get("current_capital", 0)
                    change = current_capital - initial_capital
                    st.metric(
                        "Current Capital",
                        f"${current_capital:,.2f}",
                        delta=f"${change:+,.2f}"
                    )
                
                with col3:
                    max_capital = capital_state.get("data", {}).get("max_capital", 0)
                    st.metric(
                        "Peak Capital",
                        f"${max_capital:,.2f}"
                    )
                
                with col4:
                    drawdown = capital_state.get("data", {}).get("current_drawdown_pct", 0) * 100
                    max_drawdown = capital_state.get("data", {}).get("max_drawdown_pct", 0) * 100
                    st.metric(
                        "Current Drawdown",
                        f"{drawdown:.2f}%",
                        delta=f"{max_drawdown-drawdown:.2f}% from max",
                        delta_color="inverse"
                    )
                
                # Capital history chart
                st.subheader("Capital History")
                
                # Fetch capital history
                capital_history = list(db.performance.find(
                    {"metric_type": "capital"}
                ).sort("timestamp", -1).limit(100))
                
                if capital_history:
                    # Convert to DataFrame
                    capital_df = pd.DataFrame(capital_history)
                    
                    # Create capital chart
                    fig = px.line(
                        capital_df,
                        x="timestamp",
                        y="value",
                        title="Capital Over Time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No capital history data available")
            else:
                st.info("No capital manager state found")
    except Exception as e:
        st.error(f"Error loading capital management data: {str(e)}")
    
    # Risk Parameters
    st.subheader("Risk Management Parameters")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            capital_state = persistence.load_strategy_state("capital_manager")
            
            if capital_state and "risk_params" in capital_state:
                risk_params = capital_state["risk_params"]
                
                # Display risk parameters
                params_df = pd.DataFrame({
                    "Parameter": list(risk_params.keys()),
                    "Value": list(risk_params.values())
                })
                st.table(params_df)
            else:
                st.info("No risk parameters found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            capital_state = db.strategy_states.find_one({"strategy_id": "capital_manager"})
            
            if capital_state and "data" in capital_state and "risk_params" in capital_state["data"]:
                risk_params = capital_state["data"]["risk_params"]
                
                # Display risk parameters
                params_df = pd.DataFrame({
                    "Parameter": list(risk_params.keys()),
                    "Value": list(risk_params.values())
                })
                st.table(params_df)
            else:
                st.info("No risk parameters found")
    except Exception as e:
        st.error(f"Error loading risk parameters: {str(e)}")
    
    # Strategy Allocation
    st.subheader("Strategy Capital Allocation")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            strategy_allocations = persistence.get_performance_history(
                metric_type="strategy_allocation",
                limit=100
            )
            
            if not strategy_allocations.empty:
                # Get latest allocations
                latest_date = strategy_allocations["timestamp"].max()
                latest_allocations = strategy_allocations[strategy_allocations["timestamp"] == latest_date]
                
                # Create allocation chart
                fig = px.pie(
                    latest_allocations,
                    values="value",
                    names="strategy_id",
                    title="Current Strategy Allocation"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display allocation table
                st.dataframe(latest_allocations[["strategy_id", "value"]])
            else:
                st.info("No strategy allocation data available")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            allocations = list(db.performance.find(
                {"metric_type": "strategy_allocation"}
            ).sort("timestamp", -1))
            
            if allocations:
                # Group by latest timestamp
                allocation_df = pd.DataFrame(allocations)
                latest_date = allocation_df["timestamp"].max()
                latest_allocations = allocation_df[allocation_df["timestamp"] == latest_date]
                
                # Create allocation chart
                fig = px.pie(
                    latest_allocations,
                    values="value",
                    names="strategy_id",
                    title="Current Strategy Allocation"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display allocation table
                st.dataframe(latest_allocations[["strategy_id", "value"]])
            else:
                st.info("No strategy allocation data available")
    except Exception as e:
        st.error(f"Error loading strategy allocations: {str(e)}")
    
    # Capital scaling factors
    st.subheader("Dynamic Scaling Factors")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            scaling_factors = persistence.get_performance_history(
                metric_type="scaling_factor",
                limit=100
            )
            
            if not scaling_factors.empty:
                # Create scaling factors chart
                fig = px.line(
                    scaling_factors,
                    x="timestamp",
                    y="value",
                    color="factor_type",
                    title="Dynamic Scaling Factors Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No scaling factor data available")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            factors = list(db.performance.find(
                {"metric_type": "scaling_factor"}
            ).sort("timestamp", -1).limit(100))
            
            if factors:
                # Convert to DataFrame
                factors_df = pd.DataFrame(factors)
                
                # Create scaling factors chart
                fig = px.line(
                    factors_df,
                    x="timestamp",
                    y="value",
                    color="factor_type",
                    title="Dynamic Scaling Factors Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No scaling factor data available")
    except Exception as e:
        st.error(f"Error loading scaling factors: {str(e)}")

def strategy_performance_page():
    """Render the strategy performance page"""
    st.header("Strategy Performance & Lifecycle")
    
    if not st.session_state["connected"]:
        st.warning("Not connected to MongoDB. Please connect using the sidebar.")
        return
    
    # Strategy overview section
    st.subheader("Strategy Overview")
    
    try:
        # Fetch active strategies
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            strategy_state = persistence.load_strategy_state("strategy_manager")
            
            if strategy_state and "strategies" in strategy_state:
                strategies = strategy_state["strategies"]
                
                # Count strategies by status
                status_counts = {}
                for strategy_id, strategy_data in strategies.items():
                    status = strategy_data.get("status", "UNKNOWN")
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                
                # Display strategy status counts
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    active_count = status_counts.get("ACTIVE", 0)
                    st.metric(
                        "Active Strategies",
                        active_count
                    )
                
                with col2:
                    testing_count = status_counts.get("TESTING", 0)
                    st.metric(
                        "Testing Strategies",
                        testing_count
                    )
                
                with col3:
                    retired_count = status_counts.get("RETIRED", 0)
                    st.metric(
                        "Retired Strategies",
                        retired_count
                    )
                
                with col4:
                    promoted_count = status_counts.get("PROMOTED", 0)
                    st.metric(
                        "Promoted Strategies",
                        promoted_count
                    )
                
                # Display strategy status pie chart
                status_df = pd.DataFrame({
                    "Status": list(status_counts.keys()),
                    "Count": list(status_counts.values())
                })
                
                fig = px.pie(
                    status_df,
                    values="Count",
                    names="Status",
                    title="Strategy Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No strategy manager state found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            strategy_state = db.strategy_states.find_one({"strategy_id": "strategy_manager"})
            
            if strategy_state and "data" in strategy_state and "strategies" in strategy_state["data"]:
                strategies = strategy_state["data"]["strategies"]
                
                # Count strategies by status
                status_counts = {}
                for strategy_id, strategy_data in strategies.items():
                    status = strategy_data.get("status", "UNKNOWN")
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                
                # Display strategy status counts
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    active_count = status_counts.get("ACTIVE", 0)
                    st.metric(
                        "Active Strategies",
                        active_count
                    )
                
                with col2:
                    testing_count = status_counts.get("TESTING", 0)
                    st.metric(
                        "Testing Strategies",
                        testing_count
                    )
                
                with col3:
                    retired_count = status_counts.get("RETIRED", 0)
                    st.metric(
                        "Retired Strategies",
                        retired_count
                    )
                
                with col4:
                    promoted_count = status_counts.get("PROMOTED", 0)
                    st.metric(
                        "Promoted Strategies",
                        promoted_count
                    )
                
                # Display strategy status pie chart
                status_df = pd.DataFrame({
                    "Status": list(status_counts.keys()),
                    "Count": list(status_counts.values())
                })
                
                fig = px.pie(
                    status_df,
                    values="Count",
                    names="Status",
                    title="Strategy Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No strategy manager state found")
    except Exception as e:
        st.error(f"Error loading strategy overview: {str(e)}")
    
    # Strategy performance metrics
    st.subheader("Strategy Performance Metrics")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            strategy_metrics = persistence.get_performance_history(
                metric_type="strategy_metrics",
                limit=1000
            )
            
            if not strategy_metrics.empty:
                # Group by strategy
                strategies = strategy_metrics["strategy_id"].unique()
                
                # Create tabs for each strategy
                tabs = st.tabs([f"Strategy: {strategy}" for strategy in strategies])
                
                for i, strategy in enumerate(strategies):
                    with tabs[i]:
                        # Filter metrics for this strategy
                        strategy_data = strategy_metrics[strategy_metrics["strategy_id"] == strategy]
                        
                        # Create metrics sections
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        # Get latest metrics
                        latest_date = strategy_data["timestamp"].max()
                        latest_metrics = strategy_data[strategy_data["timestamp"] == latest_date]
                        
                        with metric_col1:
                            win_rate = latest_metrics[latest_metrics["metric_name"] == "win_rate"]["value"].values
                            if len(win_rate) > 0:
                                st.metric(
                                    "Win Rate",
                                    f"{win_rate[0]:.2f}%"
                                )
                            else:
                                st.metric("Win Rate", "N/A")
                        
                        with metric_col2:
                            sharpe = latest_metrics[latest_metrics["metric_name"] == "sharpe_ratio"]["value"].values
                            if len(sharpe) > 0:
                                st.metric(
                                    "Sharpe Ratio",
                                    f"{sharpe[0]:.2f}"
                                )
                            else:
                                st.metric("Sharpe Ratio", "N/A")
                        
                        with metric_col3:
                            profit_factor = latest_metrics[latest_metrics["metric_name"] == "profit_factor"]["value"].values
                            if len(profit_factor) > 0:
                                st.metric(
                                    "Profit Factor",
                                    f"{profit_factor[0]:.2f}"
                                )
                            else:
                                st.metric("Profit Factor", "N/A")
                        
                        with metric_col4:
                            drawdown = latest_metrics[latest_metrics["metric_name"] == "max_drawdown"]["value"].values
                            if len(drawdown) > 0:
                                st.metric(
                                    "Max Drawdown",
                                    f"{drawdown[0]:.2f}%"
                                )
                            else:
                                st.metric("Max Drawdown", "N/A")
                        
                        # Plot metrics over time
                        st.subheader(f"Metrics Over Time - {strategy}")
                        
                        # Pivot the data to get metrics by timestamp
                        pivoted = strategy_data.pivot(index="timestamp", columns="metric_name", values="value")
                        pivoted.reset_index(inplace=True)
                        
                        # Create line chart
                        fig = px.line(
                            pivoted,
                            x="timestamp",
                            y=pivoted.columns[1:],  # Skip the timestamp column
                            title=f"{strategy} - Performance Metrics Over Time"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No strategy metrics data available")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            metrics = list(db.performance.find(
                {"metric_type": "strategy_metrics"}
            ).sort("timestamp", -1).limit(1000))
            
            if metrics:
                # Convert to DataFrame
                metrics_df = pd.DataFrame(metrics)
                
                # Group by strategy
                strategies = metrics_df["strategy_id"].unique()
                
                # Create tabs for each strategy
                tabs = st.tabs([f"Strategy: {strategy}" for strategy in strategies])
                
                for i, strategy in enumerate(strategies):
                    with tabs[i]:
                        # Filter metrics for this strategy
                        strategy_data = metrics_df[metrics_df["strategy_id"] == strategy]
                        
                        # Create metrics sections
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        # Get latest metrics
                        latest_date = strategy_data["timestamp"].max()
                        latest_metrics = strategy_data[strategy_data["timestamp"] == latest_date]
                        
                        with metric_col1:
                            win_rate = latest_metrics[latest_metrics["metric_name"] == "win_rate"]["value"].values
                            if len(win_rate) > 0:
                                st.metric(
                                    "Win Rate",
                                    f"{win_rate[0]:.2f}%"
                                )
                            else:
                                st.metric("Win Rate", "N/A")
                        
                        with metric_col2:
                            sharpe = latest_metrics[latest_metrics["metric_name"] == "sharpe_ratio"]["value"].values
                            if len(sharpe) > 0:
                                st.metric(
                                    "Sharpe Ratio",
                                    f"{sharpe[0]:.2f}"
                                )
                            else:
                                st.metric("Sharpe Ratio", "N/A")
                        
                        with metric_col3:
                            profit_factor = latest_metrics[latest_metrics["metric_name"] == "profit_factor"]["value"].values
                            if len(profit_factor) > 0:
                                st.metric(
                                    "Profit Factor",
                                    f"{profit_factor[0]:.2f}"
                                )
                            else:
                                st.metric("Profit Factor", "N/A")
                        
                        with metric_col4:
                            drawdown = latest_metrics[latest_metrics["metric_name"] == "max_drawdown"]["value"].values
                            if len(drawdown) > 0:
                                st.metric(
                                    "Max Drawdown",
                                    f"{drawdown[0]:.2f}%"
                                )
                            else:
                                st.metric("Max Drawdown", "N/A")
                        
                        # Plot metrics over time
                        st.subheader(f"Metrics Over Time - {strategy}")
                        
                        # Pivot the data to get metrics by timestamp
                        pivoted = strategy_data.pivot(index="timestamp", columns="metric_name", values="value")
                        pivoted.reset_index(inplace=True)
                        
                        # Create line chart
                        fig = px.line(
                            pivoted,
                            x="timestamp",
                            y=pivoted.columns[1:],  # Skip the timestamp column
                            title=f"{strategy} - Performance Metrics Over Time"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No strategy metrics data available")
    except Exception as e:
        st.error(f"Error loading strategy metrics: {str(e)}")
    
    # Strategy Lifecycle Events
    st.subheader("Strategy Lifecycle Events")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            lifecycle_events = persistence.get_system_logs(
                component="StrategyPerformanceManager",
                level="INFO",
                limit=100
            )
            
            if not lifecycle_events.empty:
                # Filter for lifecycle events
                lifecycle_events = lifecycle_events[
                    lifecycle_events["message"].str.contains("RETIRED|PROMOTED|TESTING|ACTIVE")
                ]
                
                # Display events
                st.dataframe(lifecycle_events[["timestamp", "message", "strategy_id", "data"]])
            else:
                st.info("No strategy lifecycle events found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            lifecycle_events = list(db.system_logs.find(
                {
                    "component": "StrategyPerformanceManager",
                    "message": {"$regex": "RETIRED|PROMOTED|TESTING|ACTIVE"}
                }
            ).sort("timestamp", -1).limit(100))
            
            if lifecycle_events:
                # Convert to DataFrame
                events_df = pd.DataFrame(lifecycle_events)
                
                # Display events
                st.dataframe(events_df[["timestamp", "message", "strategy_id", "data"]])
            else:
                st.info("No strategy lifecycle events found")
    except Exception as e:
        st.error(f"Error loading lifecycle events: {str(e)}")
    
    # Strategy Performance Rankings
    st.subheader("Strategy Performance Rankings")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            strategy_state = persistence.load_strategy_state("strategy_manager")
            
            if strategy_state and "performance_rankings" in strategy_state:
                rankings = strategy_state["performance_rankings"]
                
                # Create a DataFrame from rankings
                rankings_data = []
                for metric, ranked_strategies in rankings.items():
                    for rank, (strategy_id, value) in enumerate(ranked_strategies):
                        rankings_data.append({
                            "Metric": metric,
                            "Rank": rank + 1,
                            "Strategy": strategy_id,
                            "Value": value
                        })
                
                rankings_df = pd.DataFrame(rankings_data)
                
                # Create a tab for each metric
                metrics = rankings_df["Metric"].unique()
                tabs = st.tabs([f"Ranking: {metric}" for metric in metrics])
                
                for i, metric in enumerate(metrics):
                    with tabs[i]:
                        # Filter for this metric
                        metric_data = rankings_df[rankings_df["Metric"] == metric]
                        
                        # Sort by rank
                        metric_data = metric_data.sort_values("Rank")
                        
                        # Display as bar chart
                        fig = px.bar(
                            metric_data,
                            x="Strategy",
                            y="Value",
                            title=f"Strategy Ranking by {metric}",
                            color="Rank",
                            color_continuous_scale="Viridis"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display as table
                        st.dataframe(metric_data[["Rank", "Strategy", "Value"]].set_index("Rank"))
            else:
                st.info("No strategy performance rankings found")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            strategy_state = db.strategy_states.find_one({"strategy_id": "strategy_manager"})
            
            if strategy_state and "data" in strategy_state and "performance_rankings" in strategy_state["data"]:
                rankings = strategy_state["data"]["performance_rankings"]
                
                # Create a DataFrame from rankings
                rankings_data = []
                for metric, ranked_strategies in rankings.items():
                    for rank, (strategy_id, value) in enumerate(ranked_strategies):
                        rankings_data.append({
                            "Metric": metric,
                            "Rank": rank + 1,
                            "Strategy": strategy_id,
                            "Value": value
                        })
                
                rankings_df = pd.DataFrame(rankings_data)
                
                # Create a tab for each metric
                metrics = rankings_df["Metric"].unique()
                tabs = st.tabs([f"Ranking: {metric}" for metric in metrics])
                
                for i, metric in enumerate(metrics):
                    with tabs[i]:
                        # Filter for this metric
                        metric_data = rankings_df[rankings_df["Metric"] == metric]
                        
                        # Sort by rank
                        metric_data = metric_data.sort_values("Rank")
                        
                        # Display as bar chart
                        fig = px.bar(
                            metric_data,
                            x="Strategy",
                            y="Value",
                            title=f"Strategy Ranking by {metric}",
                            color="Rank",
                            color_continuous_scale="Viridis"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display as table
                        st.dataframe(metric_data[["Rank", "Strategy", "Value"]].set_index("Rank"))
            else:
                st.info("No strategy performance rankings found")
    except Exception as e:
        st.error(f"Error loading strategy rankings: {str(e)}")

def execution_quality_page():
    """Render the execution quality page"""
    st.header("Execution Quality Metrics")
    
    if not st.session_state["connected"]:
        st.warning("Not connected to MongoDB. Please connect using the sidebar.")
        return
    
    # Execution overview section
    st.subheader("Execution Overview")
    
    try:
        # Fetch execution data
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            execution_metrics = persistence.get_performance_history(
                metric_type="execution_quality",
                limit=1000
            )
            
            if not execution_metrics.empty:
                # Display execution metrics summary
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate mean metrics
                mean_slippage = execution_metrics[execution_metrics["metric_name"] == "slippage"]["value"].mean()
                mean_latency = execution_metrics[execution_metrics["metric_name"] == "latency"]["value"].mean()
                mean_spread = execution_metrics[execution_metrics["metric_name"] == "effective_spread"]["value"].mean()
                mean_impact = execution_metrics[execution_metrics["metric_name"] == "market_impact"]["value"].mean()
                
                with col1:
                    st.metric(
                        "Avg. Slippage (pips)",
                        f"{mean_slippage:.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Avg. Latency (ms)",
                        f"{mean_latency:.2f}"
                    )
                
                with col3:
                    st.metric(
                        "Avg. Spread (pips)",
                        f"{mean_spread:.2f}"
                    )
                
                with col4:
                    st.metric(
                        "Avg. Market Impact (pips)",
                        f"{mean_impact:.2f}"
                    )
                
                # Execution metrics by symbol
                st.subheader("Execution Metrics by Symbol")
                
                # Group by symbol
                symbols = execution_metrics["symbol"].unique()
                
                # Create tabs for different metric types
                metric_tabs = st.tabs(["Slippage", "Latency", "Spread", "Market Impact"])
                
                with metric_tabs[0]:  # Slippage
                    slippage_data = execution_metrics[execution_metrics["metric_name"] == "slippage"]
                    
                    if not slippage_data.empty:
                        # Group by symbol
                        symbol_slippage = slippage_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_slippage,
                            x="symbol",
                            y="value",
                            title="Average Slippage by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high slippage, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No slippage data available")
                
                with metric_tabs[1]:  # Latency
                    latency_data = execution_metrics[execution_metrics["metric_name"] == "latency"]
                    
                    if not latency_data.empty:
                        # Group by symbol
                        symbol_latency = latency_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_latency,
                            x="symbol",
                            y="value",
                            title="Average Latency by Symbol (ms)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high latency, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No latency data available")
                
                with metric_tabs[2]:  # Spread
                    spread_data = execution_metrics[execution_metrics["metric_name"] == "effective_spread"]
                    
                    if not spread_data.empty:
                        # Group by symbol
                        symbol_spread = spread_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_spread,
                            x="symbol",
                            y="value",
                            title="Average Spread by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high spread, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No spread data available")
                
                with metric_tabs[3]:  # Market Impact
                    impact_data = execution_metrics[execution_metrics["metric_name"] == "market_impact"]
                    
                    if not impact_data.empty:
                        # Group by symbol
                        symbol_impact = impact_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_impact,
                            x="symbol",
                            y="value",
                            title="Average Market Impact by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high impact, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No market impact data available")
                
                # Execution trends over time
                st.subheader("Execution Trends")
                
                # Create line chart for trends over time
                fig = px.line(
                    execution_metrics,
                    x="timestamp",
                    y="value",
                    color="metric_name",
                    facet_col="metric_name",
                    facet_col_wrap=2,  # 2 charts per row
                    title="Execution Metrics Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No execution quality metrics available")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            execution_metrics = list(db.performance.find(
                {"metric_type": "execution_quality"}
            ).sort("timestamp", -1).limit(1000))
            
            if execution_metrics:
                # Convert to DataFrame
                metrics_df = pd.DataFrame(execution_metrics)
                
                # Display execution metrics summary
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate mean metrics
                mean_slippage = metrics_df[metrics_df["metric_name"] == "slippage"]["value"].mean()
                mean_latency = metrics_df[metrics_df["metric_name"] == "latency"]["value"].mean()
                mean_spread = metrics_df[metrics_df["metric_name"] == "effective_spread"]["value"].mean()
                mean_impact = metrics_df[metrics_df["metric_name"] == "market_impact"]["value"].mean()
                
                with col1:
                    st.metric(
                        "Avg. Slippage (pips)",
                        f"{mean_slippage:.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Avg. Latency (ms)",
                        f"{mean_latency:.2f}"
                    )
                
                with col3:
                    st.metric(
                        "Avg. Spread (pips)",
                        f"{mean_spread:.2f}"
                    )
                
                with col4:
                    st.metric(
                        "Avg. Market Impact (pips)",
                        f"{mean_impact:.2f}"
                    )
                
                # Execution metrics by symbol
                st.subheader("Execution Metrics by Symbol")
                
                # Group by symbol
                symbols = metrics_df["symbol"].unique()
                
                # Create tabs for different metric types
                metric_tabs = st.tabs(["Slippage", "Latency", "Spread", "Market Impact"])
                
                with metric_tabs[0]:  # Slippage
                    slippage_data = metrics_df[metrics_df["metric_name"] == "slippage"]
                    
                    if not slippage_data.empty:
                        # Group by symbol
                        symbol_slippage = slippage_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_slippage,
                            x="symbol",
                            y="value",
                            title="Average Slippage by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high slippage, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No slippage data available")
                
                with metric_tabs[1]:  # Latency
                    latency_data = metrics_df[metrics_df["metric_name"] == "latency"]
                    
                    if not latency_data.empty:
                        # Group by symbol
                        symbol_latency = latency_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_latency,
                            x="symbol",
                            y="value",
                            title="Average Latency by Symbol (ms)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high latency, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No latency data available")
                
                with metric_tabs[2]:  # Spread
                    spread_data = metrics_df[metrics_df["metric_name"] == "effective_spread"]
                    
                    if not spread_data.empty:
                        # Group by symbol
                        symbol_spread = spread_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_spread,
                            x="symbol",
                            y="value",
                            title="Average Spread by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high spread, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No spread data available")
                
                with metric_tabs[3]:  # Market Impact
                    impact_data = metrics_df[metrics_df["metric_name"] == "market_impact"]
                    
                    if not impact_data.empty:
                        # Group by symbol
                        symbol_impact = impact_data.groupby("symbol")["value"].mean().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            symbol_impact,
                            x="symbol",
                            y="value",
                            title="Average Market Impact by Symbol (pips)",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high impact, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No market impact data available")
                
                # Execution trends over time
                st.subheader("Execution Trends")
                
                # Create line chart for trends over time
                fig = px.line(
                    metrics_df,
                    x="timestamp",
                    y="value",
                    color="metric_name",
                    facet_col="metric_name",
                    facet_col_wrap=2,  # 2 charts per row
                    title="Execution Metrics Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No execution quality metrics available")
    except Exception as e:
        st.error(f"Error loading execution quality metrics: {str(e)}")
    
    # Order fill quality
    st.subheader("Order Fill Quality")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            trades = persistence.get_trades_history(limit=1000)
            
            if not trades.empty and "fill_quality" in trades.columns:
                # Calculate fill quality metrics
                avg_fill_quality = trades["fill_quality"].mean()
                
                st.metric(
                    "Average Fill Quality",
                    f"{avg_fill_quality:.2f}%"
                )
                
                # Group by symbol
                fill_by_symbol = trades.groupby("symbol")["fill_quality"].mean().reset_index()
                
                # Create bar chart
                fig = px.bar(
                    fill_by_symbol,
                    x="symbol",
                    y="fill_quality",
                    title="Fill Quality by Symbol (%)",
                    color="fill_quality",
                    color_continuous_scale="Viridis"  # Purple for higher quality
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Fill quality vs. volume scatter plot
                if "volume" in trades.columns:
                    fig = px.scatter(
                        trades,
                        x="volume",
                        y="fill_quality",
                        color="symbol",
                        size="volume",
                        hover_data=["timestamp", "price"],
                        title="Fill Quality vs. Order Volume"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fill quality data available in trades")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            trades = list(db.trades.find().sort("timestamp", -1).limit(1000))
            
            if trades:
                trades_df = pd.DataFrame(trades)
                
                if "fill_quality" in trades_df.columns:
                    # Calculate fill quality metrics
                    avg_fill_quality = trades_df["fill_quality"].mean()
                    
                    st.metric(
                        "Average Fill Quality",
                        f"{avg_fill_quality:.2f}%"
                    )
                    
                    # Group by symbol
                    fill_by_symbol = trades_df.groupby("symbol")["fill_quality"].mean().reset_index()
                    
                    # Create bar chart
                    fig = px.bar(
                        fill_by_symbol,
                        x="symbol",
                        y="fill_quality",
                        title="Fill Quality by Symbol (%)",
                        color="fill_quality",
                        color_continuous_scale="Viridis"  # Purple for higher quality
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Fill quality vs. volume scatter plot
                    if "volume" in trades_df.columns:
                        fig = px.scatter(
                            trades_df,
                            x="volume",
                            y="fill_quality",
                            color="symbol",
                            size="volume",
                            hover_data=["timestamp", "price"],
                            title="Fill Quality vs. Order Volume"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No fill quality data available in trades")
            else:
                st.info("No trades data available")
    except Exception as e:
        st.error(f"Error loading order fill quality data: {str(e)}")
    
    # Session Analysis
    st.subheader("Execution Quality by Session")
    
    try:
        if COMPONENTS_IMPORTED and st.session_state["persistence"]:
            # Use persistence manager
            persistence = st.session_state["persistence"]
            execution_metrics = persistence.get_performance_history(
                metric_type="execution_quality",
                limit=1000
            )
            
            if not execution_metrics.empty and "session" in execution_metrics.columns:
                # Group by session and metric name
                session_metrics = execution_metrics.groupby(["session", "metric_name"])["value"].mean().reset_index()
                
                # Create bar chart for each metric by session
                for metric in session_metrics["metric_name"].unique():
                    metric_data = session_metrics[session_metrics["metric_name"] == metric]
                    
                    fig = px.bar(
                        metric_data,
                        x="session",
                        y="value",
                        title=f"Average {metric.capitalize()} by Trading Session",
                        color="value",
                        color_continuous_scale="RdYlGn_r"  # Red for high metrics, green for low
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No session-based execution data available")
        else:
            # Direct MongoDB access
            db = st.session_state["db"]
            execution_metrics = list(db.performance.find(
                {"metric_type": "execution_quality"}
            ).limit(1000))
            
            if execution_metrics:
                metrics_df = pd.DataFrame(execution_metrics)
                
                if "session" in metrics_df.columns:
                    # Group by session and metric name
                    session_metrics = metrics_df.groupby(["session", "metric_name"])["value"].mean().reset_index()
                    
                    # Create bar chart for each metric by session
                    for metric in session_metrics["metric_name"].unique():
                        metric_data = session_metrics[session_metrics["metric_name"] == metric]
                        
                        fig = px.bar(
                            metric_data,
                            x="session",
                            y="value",
                            title=f"Average {metric.capitalize()} by Trading Session",
                            color="value",
                            color_continuous_scale="RdYlGn_r"  # Red for high metrics, green for low
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No session data available in execution metrics")
            else:
                st.info("No execution metrics data available")
    except Exception as e:
        st.error(f"Error loading session-based execution data: {str(e)}")

def main():
    """Main dashboard function"""
    # Render header
    header()
    
    # Render sidebar and get selected page
    page = sidebar()
    
    # Render selected page
    if page == "Overview":
        overview_page()
    elif page == "Persistence Monitor":
        persistence_page()
    elif page == "Watchdog Monitor":
        watchdog_page()
    elif page == "Capital Management":
        capital_management_page()
    elif page == "Strategy Performance":
        strategy_performance_page()
    elif page == "Execution Quality":
        execution_quality_page()

if __name__ == "__main__":
    main()
