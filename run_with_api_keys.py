#!/usr/bin/env python3
"""
BenBot Dashboard Launcher with API Keys
---------------------------------------
Loads API keys from .env file and runs the dashboard
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DashboardAPIKeyLoader")

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    
    if not env_path.exists():
        logger.error(".env file not found")
        return False
    
    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
                    logger.info(f"Loaded environment variable: {key}")
        
        # Print API configuration status
        keys_found = False
        if os.environ.get("OPENAI_API_KEY"):
            logger.info("✅ OpenAI API key loaded")
            keys_found = True
        if os.environ.get("ANTHROPIC_API_KEY"):
            logger.info("✅ Anthropic/Claude API key loaded")
            keys_found = True
        if os.environ.get("MISTRAL_API_KEY"):
            logger.info("✅ Mistral API key loaded")
            keys_found = True
        if os.environ.get("COHERE_API_KEY"):
            logger.info("✅ Cohere API key loaded")
            keys_found = True
        if os.environ.get("GEMINI_API_KEY"):
            logger.info("✅ Gemini API key loaded")
            keys_found = True
            
        if not keys_found:
            logger.warning("❌ No API keys found in .env file")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error loading .env file: {str(e)}")
        return False

def main():
    """Main function to load API keys and start the dashboard"""
    logger.info("Loading API keys for BenBot Trading Dashboard")
    
    # Load API keys from .env file
    if not load_env_file():
        logger.warning("Failed to load API keys, the dashboard will use rule-based responses")
    
    # Run the dashboard
    logger.info("Starting dashboard with API keys...")
    
    try:
        # Import and run the dashboard directly in this process
        # This ensures the environment variables are available to the dashboard
        from run_dashboard import main as run_dashboard_main
        run_dashboard_main()
    except Exception as e:
        logger.error(f"Error running dashboard: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 