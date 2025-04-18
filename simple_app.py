import streamlit as st
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard")

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the module causing the error
try:
    from trading_bot.portfolio_state import PortfolioStateManager
    logger.info("Successfully imported PortfolioStateManager")
except Exception as e:
    logger.error(f"Error importing PortfolioStateManager: {str(e)}")

# Try to create an instance
try:
    portfolio_state = PortfolioStateManager()
    logger.info("Successfully created PortfolioStateManager instance")
except Exception as e:
    logger.error(f"Error creating PortfolioStateManager: {str(e)}")

# Set page configuration
st.set_page_config(
    page_title="Simple Testing App",
    page_icon="📈"
)

# Display results
st.title("Module Import Test")
st.write("This app tests if the necessary modules can be imported.")

if 'portfolio_state' in locals():
    st.success("✅ PortfolioStateManager was successfully imported and initialized!")
    st.write("Portfolio Value:", portfolio_state.get_portfolio_value())
else:
    st.error("❌ Failed to import or initialize PortfolioStateManager.") 