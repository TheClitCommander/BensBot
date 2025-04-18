#!/usr/bin/env python3
"""
Run the trading dashboard on port 9999
"""

import os
import sys
from simple_dashboard import app

if __name__ == "__main__":
    print("\n🚀 Dashboard is running at: http://localhost:9999")
    print("📱 Try these URLs in your browser:")
    print("   - http://localhost:9999")
    print("   - http://127.0.0.1:9999")
    print("Press Ctrl+C to stop the server\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=9999, debug=True) 