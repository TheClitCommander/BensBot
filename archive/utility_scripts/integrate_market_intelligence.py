"""
Market Intelligence Integration Script
This script integrates the Market Intelligence Center into the main application
and demonstrates how to use the unified MarketContext across all components.
"""

import os
import sys
import json
import time
import logging
import streamlit as st
from datetime import datetime

# Import our components
from trading_bot.market_context.market_context import get_market_context
from trading_bot.symbolranker.symbol_ranker import get_symbol_ranker
from trading_bot.ml_pipeline.adaptive_trainer import get_adaptive_trainer
from trading_bot.market_intelligence_controller import get_market_intelligence_controller

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/market_intelligence.log")
    ]
)

logger = logging.getLogger("MarketIntelligenceIntegration")

def initialize_market_intelligence(symbols=None):
    """
    Initialize the Market Intelligence Center and all its components.
    
    Args:
        symbols: List of symbols to initialize with or None for defaults
        
    Returns:
        MarketIntelligenceController instance
    """
    logger.info("Initializing Market Intelligence Center")
    
    # Create directory for context data
    os.makedirs("data/market_context", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Get controller and initialize
    controller = get_market_intelligence_controller()
    
    # Initialize with provided symbols or defaults
    success = controller.initialize(symbols)
    
    if success:
        logger.info("Market Intelligence Center initialized successfully")
    else:
        logger.error("Failed to initialize Market Intelligence Center")
    
    return controller

def get_global_price_data(symbol, force_refresh=False):
    """
    Enhanced version of get_global_price_data that leverages the unified MarketContext.
    This function can replace or augment the existing implementation in app.py.
    
    Args:
        symbol: Stock symbol to get price data for
        force_refresh: Whether to force refresh cached data
        
    Returns:
        Dictionary containing price data
    """
    # Check if we already have data in session state
    if not force_refresh and "global_price_data" in st.session_state and symbol in st.session_state.global_price_data:
        return st.session_state.global_price_data[symbol]
    
    # Get market context
    market_context = get_market_context()
    
    # Update symbol data if needed
    if force_refresh:
        market_context.update_symbol_data([symbol])
    
    # Get context data
    context = market_context.get_market_context()
    
    # Extract price data from context
    if symbol in context.get("symbols", {}):
        price_data = context["symbols"][symbol].get("price", {})
        
        # Ensure we store this in session state for other components
        if "global_price_data" not in st.session_state:
            st.session_state.global_price_data = {}
        
        st.session_state.global_price_data[symbol] = price_data
        
        return price_data
    
    # Fallback - use standard method if symbol not in context
    # Import only here to avoid circular imports
    from news_api import news_service
    price_data = news_service.get_stock_price(symbol, force_refresh=force_refresh)
    
    # Store in session state
    if "global_price_data" not in st.session_state:
        st.session_state.global_price_data = {}
    
    st.session_state.global_price_data[symbol] = price_data
    
    return price_data

def get_market_intelligence():
    """
    Get market intelligence data for use in the dashboard.
    
    Returns:
        Dictionary with market intelligence data
    """
    # Get market intelligence controller
    controller = get_market_intelligence_controller()
    
    # If not initialized, initialize it
    if controller.metadata["status"] == "initializing":
        controller.initialize()
    
    # Get latest data
    market_summary = controller.get_market_summary()
    top_pairs = controller.get_top_symbol_strategy_pairs(limit=5)
    
    return {
        "market_summary": market_summary,
        "top_pairs": top_pairs,
        "timestamp": datetime.now().isoformat()
    }

def add_market_intelligence_to_dashboard():
    """
    Add market intelligence UI components to the Market Intelligence Dashboard.
    This function demonstrates how to integrate the unified system into the existing UI.
    """
    st.header("🌟 Enhanced Market Intelligence")
    
    # Get market intelligence data
    intelligence = get_market_intelligence()
    market_summary = intelligence["market_summary"]
    top_pairs = intelligence["top_pairs"]
    
    # Market regime and summary
    st.subheader("Market Regime Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        regime = market_summary.get("regime", "unknown")
        st.markdown(f"""
        <div style='border:1px solid #34495e; border-radius:5px; padding:10px; background-color:#1e2130;'>
            <h3 style='color:#3498db;'>Current Market Regime</h3>
            <h2 style='color:#ffffff;'>{regime.replace('_', ' ').title()}</h2>
            <p>Last updated: {market_summary.get("timestamp", "")[:19].replace('T', ' ')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        vix = market_summary.get("indicators", {}).get("vix", 0)
        vix_color = "#e74c3c" if vix > 25 else "#2ecc71" if vix < 15 else "#f39c12"
        
        st.markdown(f"""
        <div style='border:1px solid #34495e; border-radius:5px; padding:10px; background-color:#1e2130;'>
            <h3 style='color:#3498db;'>Key Market Indicators</h3>
            <p><strong>VIX:</strong> <span style='color:{vix_color};'>{vix:.2f}</span></p>
            <p><strong>Treasury 10Y:</strong> {market_summary.get("indicators", {}).get("treasury_10y", 0):.2f}%</p>
            <p><strong>Market Direction:</strong> {market_summary.get("indicators", {}).get("market_direction", "neutral").title()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display top strategy-symbol pairs
    st.subheader("Optimal Strategy-Symbol Pairs")
    
    if not top_pairs:
        st.info("No optimal pairs found. Try updating market data.")
    else:
        cols = st.columns(len(top_pairs[:3]))
        
        for i, pair in enumerate(top_pairs[:3]):
            symbol = pair.get("symbol", "")
            strategy = pair.get("strategy", "").replace('_', ' ').title()
            score = pair.get("score", 0) * 100
            
            # Get price data for this symbol
            price_data = get_global_price_data(symbol)
            current_price = price_data.get("current", 0)
            change_pct = price_data.get("change", 0)
            change_color = "#2ecc71" if change_pct >= 0 else "#e74c3c"
            
            with cols[i]:
                st.markdown(f"""
                <div style='border:1px solid #34495e; border-radius:5px; padding:10px; background-color:#1e2130;'>
                    <h3 style='color:#3498db;'>{symbol}</h3>
                    <p><strong>Strategy:</strong> {strategy}</p>
                    <p><strong>Match Score:</strong> {score:.1f}%</p>
                    <p><strong>Price:</strong> ${current_price:.2f} <span style='color:{change_color};'>({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)</span></p>
                </div>
                """, unsafe_allow_html=True)
    
    # List additional pairs
    if len(top_pairs) > 3:
        st.markdown("### Additional Recommended Pairs")
        
        for pair in top_pairs[3:]:
            symbol = pair.get("symbol", "")
            strategy = pair.get("strategy", "").replace('_', ' ').title()
            score = pair.get("score", 0) * 100
            
            st.markdown(f"- **{symbol}** with *{strategy}* strategy (Score: {score:.1f}%)")
    
    # Action button to update data
    if st.button("Update Market Intelligence"):
        controller = get_market_intelligence_controller()
        result = controller.update(force=True)
        
        if result["status"] == "success":
            st.success("Market intelligence updated successfully!")
        else:
            st.error(f"Error updating market intelligence: {result.get('message', 'Unknown error')}")
        
        # Force UI refresh
        st.experimental_rerun()

if __name__ == "__main__":
    # This code will run if this script is executed directly
    print("Initializing Market Intelligence Center...")
    controller = initialize_market_intelligence()
    
    print("Market Summary:")
    market_summary = controller.get_market_summary()
    print(json.dumps(market_summary, indent=2))
    
    print("\nTop Symbol-Strategy Pairs:")
    top_pairs = controller.get_top_symbol_strategy_pairs()
    print(json.dumps(top_pairs, indent=2))
    
    print("\nDone. Use the controller in your Streamlit app for full integration.")
