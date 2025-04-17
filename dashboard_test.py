#!/usr/bin/env python3
"""
Dashboard diagnostic script

This is a simple script to help diagnose issues with the dashboard.
"""

import os
import sys
import platform
import socket

# Print diagnostic information
print("="*50)
print("DASHBOARD DIAGNOSTIC REPORT")
print("="*50)
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Environment variables: {dict(os.environ)}")

# Check if port 8080 is available
def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

if check_port(8080):
    print("\n✅ Port 8080 is available")
else:
    print("\n❌ Port 8080 is already in use!")

# Try to import app.py
print("\nAttempting to import app.py:")
try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'trading_bot/dashboard'))
    import app
    print("✅ Successfully imported app.py")
    # Check what type of app it is
    if hasattr(app, 'socketio'):
        print("📊 App type: Flask with SocketIO")
    elif hasattr(app, 'st'):
        print("📊 App type: Streamlit")
    else:
        print("❓ Unknown app type")
except Exception as e:
    print(f"❌ Error importing app.py: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nDiagnostic complete. Use this information to troubleshoot your dashboard issues.")
print("="*50)

# Keep window open
input("Press Enter to close this window...") 