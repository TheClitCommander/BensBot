#!/usr/bin/env python
"""
Fix script for core/__init__.py
"""

import os

# Define the correct content for the file
content = '''"""
Trading Bot Core Module

Contains base classes, interfaces, and common abstractions.
"""

from trading_bot.core.interfaces import (
    DataProvider,
    IndicatorInterface,
    StrategyInterface,
    SignalInterface
)

__all__ = [
    "DataProvider",
    "IndicatorInterface",
    "StrategyInterface",
    "SignalInterface"
]
'''

# Path to the file
file_path = os.path.join('trading_bot', 'core', '__init__.py')

# Write the content to the file
with open(file_path, 'w') as f:
    f.write(content)

print(f"Fixed {file_path}") 