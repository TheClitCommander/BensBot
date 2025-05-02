#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BenBot Assistant

This module implements a natural language interface for interacting with
the trading bot. It processes user queries, generates appropriate responses,
and interfaces with the main orchestrator to execute trading commands.
"""

import logging
import re
from typing import Dict, List, Optional, Union, Any
import json
import os
from datetime import datetime

# Import NLP libraries if available
try:
    import numpy as np
    NLP_LIBRARIES_AVAILABLE = True
except ImportError:
    NLP_LIBRARIES_AVAILABLE = False

logger = logging.getLogger(__name__)

class BenBotAssistant:
    """
    Natural language assistant for the trading bot system.
    
    This class provides a conversational interface to control the trading bot,
    retrieve information, and perform trading operations using natural language.
    """
    
    def __init__(self, orchestrator=None, config=None):
        """
        Initialize the BenBot Assistant.
        
        Args:
            orchestrator: Optional reference to the MainOrchestrator instance
            config: Configuration dictionary for the assistant
        """
        self.orchestrator = orchestrator
        self.config = config or {}
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Intent patterns - basic regex patterns for detecting user intents
        self.intent_patterns = {
            "run_strategy": r"(?i)run\s+(?:the\s+)?(?:trading\s+)?(?:strategy|strategies)(?:\s+for\s+(.+))?",
            "market_analysis": r"(?i)(?:what\s+is\s+)?(?:the\s+)?(?:current\s+)?market\s+(?:regime|status|analysis)",
            "trading_opportunities": r"(?i)(?:show|get|find)(?:\s+me)?\s+(?:the\s+)?(?:trading\s+)?opportunities",
            "portfolio_status": r"(?i)(?:what\s+is\s+)?(?:the\s+)?(?:current\s+)?portfolio\s+(?:status|value|holdings)",
            "help": r"(?i)(?:help|assist|what\s+can\s+you\s+do|commands)",
            "greeting": r"(?i)(?:hello|hi|hey|good\s+(?:morning|afternoon|evening))",
        }
        
        logger.info("BenBot Assistant initialized")
    
    def set_orchestrator(self, orchestrator):
        """Set the main orchestrator reference."""
        self.orchestrator = orchestrator
        logger.info("Orchestrator reference set in BenBot Assistant")
    
    def process_query(self, query: str) -> str:
        """
        Process a natural language query and return a response.
        
        Args:
            query: The user's natural language query
            
        Returns:
            Response string with results or action confirmation
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query, "timestamp": datetime.now().isoformat()})
        
        # Log the incoming query
        logger.info(f"Processing query: {query}")
        
        try:
            # Check if orchestrator is available
            if not self.orchestrator:
                response = "I'm not connected to the trading system yet. Please initialize the orchestrator first."
                logger.warning("Query received but orchestrator is not available")
            else:
                # Match intents using regex patterns
                response = self._match_intent(query)
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            response = f"I encountered an error while processing your request: {str(e)}"
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
        
        return response
    
    def _match_intent(self, query: str) -> str:
        """Match the query against known intent patterns and handle accordingly."""
        
        # Try to match against known patterns
        for intent, pattern in self.intent_patterns.items():
            match = re.search(pattern, query)
            if match:
                logger.info(f"Matched intent: {intent}")
                
                # Call the appropriate handler based on intent
                if intent == "run_strategy":
                    # Extract strategy name if present
                    strategy_name = match.group(1) if match.groups() else None
                    return self._handle_run_strategy(strategy_name)
                
                elif intent == "market_analysis":
                    return self._handle_market_analysis()
                
                elif intent == "trading_opportunities":
                    return self._handle_trading_opportunities()
                
                elif intent == "portfolio_status":
                    return self._handle_portfolio_status()
                
                elif intent == "help":
                    return self._handle_help()
                
                elif intent == "greeting":
                    return self._handle_greeting()
        
        # No intent matched, try generic response
        return self._handle_unknown_intent(query)
    
    # Intent handlers
    
    def _handle_run_strategy(self, strategy_name=None):
        """Handle request to run a trading strategy."""
        try:
            # Call the orchestrator's run_pipeline method
            result = self.orchestrator.run_pipeline(strategy_name)
            
            if strategy_name:
                return f"I've executed the {strategy_name} strategy. {result}"
            else:
                return f"I've executed all active trading strategies. {result}"
                
        except Exception as e:
            logger.error(f"Error running strategy: {e}")
            return f"I couldn't run the strategy. Error: {str(e)}"
    
    def _handle_market_analysis(self):
        """Handle request for current market analysis."""
        try:
            # Get market regime from orchestrator
            market_regime = self.orchestrator.get_market_regime()
            
            if market_regime:
                regime = market_regime.get("regime", "Unknown")
                confidence = market_regime.get("confidence", 0)
                trend_strength = market_regime.get("trend_strength", "Unknown")
                
                return (f"Current market regime: {regime} (confidence: {confidence:.0%}). "
                        f"Trend strength is {trend_strength}.")
            else:
                return "I couldn't retrieve the current market analysis."
                
        except Exception as e:
            logger.error(f"Error getting market analysis: {e}")
            return f"I encountered an error while retrieving market analysis: {str(e)}"
    
    def _handle_trading_opportunities(self):
        """Handle request for current trading opportunities."""
        try:
            # Get opportunities from orchestrator
            opportunities = self.orchestrator.get_approved_opportunities()
            
            if opportunities and len(opportunities) > 0:
                response = "Here are the current trading opportunities:\n"
                for idx, opp in enumerate(opportunities, 1):
                    symbol = opp.get("symbol", "Unknown")
                    strategy = opp.get("strategy", "Unknown")
                    confidence = opp.get("confidence", 0)
                    response += f"{idx}. {symbol} ({strategy}, confidence: {confidence:.0%})\n"
                return response
            else:
                return "There are no trading opportunities identified at the moment."
                
        except Exception as e:
            logger.error(f"Error getting trading opportunities: {e}")
            return f"I encountered an error while retrieving trading opportunities: {str(e)}"
    
    def _handle_portfolio_status(self):
        """Handle request for portfolio status."""
        # This would typically call a portfolio manager service
        # For now, return a placeholder response
        return "Portfolio status functionality is not yet implemented."
    
    def _handle_help(self):
        """Handle help request."""
        help_text = (
            "Here's what you can ask me to do:\n"
            "1. Run trading strategies (e.g., 'Run the MomentumStrategy')\n"
            "2. Get market analysis (e.g., 'What's the current market regime?')\n"
            "3. Show trading opportunities (e.g., 'Show me the current opportunities')\n"
            "4. Check portfolio status (e.g., 'What's my portfolio value?')\n"
        )
        return help_text
    
    def _handle_greeting(self):
        """Handle greeting."""
        return "Hello! I'm BenBot, your trading assistant. How can I help you today?"
    
    def _handle_unknown_intent(self, query):
        """Handle queries that don't match any known intent."""
        # This would typically use more advanced NLP for fallback handling
        # For now, return a simple response
        return "I'm not sure how to help with that. Try asking about running strategies, market analysis, or trading opportunities."
    
    def get_conversation_history(self):
        """Return the conversation history."""
        return self.conversation_history 