#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universe Module

This module provides the Universe class for defining tradable assets and filtering them.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Callable, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class Universe:
    """
    Class representing a collection of tradable assets (universe).
    
    A universe defines the set of assets that a strategy can trade, along with
    filtering criteria to select specific assets based on various properties.
    """
    
    def __init__(self, 
                name: str, 
                symbols: Optional[List[str]] = None,
                description: str = "",
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a Universe.
        
        Args:
            name: Name of the universe
            symbols: List of ticker symbols in the universe
            description: Description of the universe
            metadata: Additional metadata about the universe
        """
        self.name = name
        self.symbols = set(symbols or [])
        self.description = description
        self.metadata = metadata or {}
        self.filters = []
        
        logger.info(f"Created universe '{name}' with {len(self.symbols)} symbols")
    
    def add_symbol(self, symbol: str) -> None:
        """
        Add a symbol to the universe.
        
        Args:
            symbol: Symbol to add
        """
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            logger.debug(f"Added symbol {symbol} to universe '{self.name}'")
    
    def add_symbols(self, symbols: List[str]) -> None:
        """
        Add multiple symbols to the universe.
        
        Args:
            symbols: List of symbols to add
        """
        new_symbols = [s for s in symbols if s not in self.symbols]
        if new_symbols:
            self.symbols.update(new_symbols)
            logger.debug(f"Added {len(new_symbols)} symbols to universe '{self.name}'")
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a symbol from the universe.
        
        Args:
            symbol: Symbol to remove
            
        Returns:
            True if symbol was in universe and removed, False otherwise
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.debug(f"Removed symbol {symbol} from universe '{self.name}'")
            return True
        return False
    
    def clear(self) -> None:
        """Remove all symbols from the universe."""
        count = len(self.symbols)
        self.symbols.clear()
        logger.debug(f"Cleared {count} symbols from universe '{self.name}'")
    
    def add_filter(self, filter_func: Callable[[str, Dict[str, Any]], bool], 
                  name: Optional[str] = None) -> None:
        """
        Add a filter function to the universe.
        
        Args:
            filter_func: Function that takes a symbol and data dictionary and returns True/False
            name: Optional name for the filter
        """
        filter_name = name or f"filter_{len(self.filters) + 1}"
        self.filters.append((filter_name, filter_func))
        logger.debug(f"Added filter '{filter_name}' to universe '{self.name}'")
    
    def apply_filters(self, data: Dict[str, Dict[str, Any]]) -> Set[str]:
        """
        Apply all filters to the universe symbols.
        
        Args:
            data: Dictionary mapping symbols to data dictionaries
            
        Returns:
            Set of symbols that pass all filters
        """
        # Start with all symbols
        filtered_symbols = self.symbols.copy()
        
        # Apply each filter
        for filter_name, filter_func in self.filters:
            # Filter symbols
            before_count = len(filtered_symbols)
            filtered_symbols = {
                symbol for symbol in filtered_symbols
                if symbol in data and filter_func(symbol, data[symbol])
            }
            after_count = len(filtered_symbols)
            
            logger.debug(f"Filter '{filter_name}' removed {before_count - after_count} symbols")
        
        logger.info(f"Applied {len(self.filters)} filters: {len(filtered_symbols)} symbols remain")
        return filtered_symbols
    
    def __len__(self) -> int:
        """Return the number of symbols in the universe."""
        return len(self.symbols)
    
    def __contains__(self, symbol: str) -> bool:
        """Check if a symbol is in the universe."""
        return symbol in self.symbols
    
    def __iter__(self):
        """Iterate over symbols in the universe."""
        return iter(self.symbols)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert universe to a dictionary.
        
        Returns:
            Dictionary representation of the universe
        """
        return {
            "name": self.name,
            "description": self.description,
            "symbols": list(self.symbols),
            "num_filters": len(self.filters),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_list(cls, name: str, symbols: List[str], description: str = "") -> 'Universe':
        """
        Create a universe from a list of symbols.
        
        Args:
            name: Name for the universe
            symbols: List of symbols to include
            description: Description of the universe
            
        Returns:
            New Universe instance
        """
        return cls(name=name, symbols=symbols, description=description)
    
    @classmethod
    def from_file(cls, filepath: str, name: Optional[str] = None, 
                 description: str = "") -> 'Universe':
        """
        Create a universe from a file containing symbols.
        
        Args:
            filepath: Path to file with symbols (one per line)
            name: Name for the universe (defaults to filename)
            description: Description of the universe
            
        Returns:
            New Universe instance
        """
        # Get name from filename if not provided
        if name is None:
            import os
            name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Read symbols from file
        with open(filepath, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        return cls(name=name, symbols=symbols, description=description) 