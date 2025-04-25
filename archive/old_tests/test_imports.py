#!/usr/bin/env python
"""Test script to check if modules can be imported correctly"""

import sys
import os

# Print Python path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Current directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

# Try importing the problematic modules
print("\nTesting imports:")

try:
    import socketio
    print(f"✅ socketio module can be imported")
except ImportError as e:
    print(f"❌ Error importing socketio: {e}")

try:
    import plotly
    print(f"✅ plotly module can be imported")
except ImportError as e:
    print(f"❌ Error importing plotly: {e}")

try:
    import trading_bot
    print(f"✅ trading_bot module can be imported")
except ImportError as e:
    print(f"❌ Error importing trading_bot: {e}")

try:
    from trading_bot import psychological_risk
    print(f"✅ trading_bot.psychological_risk module can be imported")
except ImportError as e:
    print(f"❌ Error importing trading_bot.psychological_risk: {e}")

print("\nAll tests completed.") 