#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Dashboard Runner

This script launches a simplified trading dashboard on port 8085.
It avoids the import errors from the trading_bot package.
"""

import os
import sys
import logging
from pathlib import Path
import flask
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='trading_bot/dashboard/templates')
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'trading_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Define routes
@app.route('/')
def serve_dashboard():
    """Try to serve the main dashboard page or fallback to a simple page."""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard template: {e}")
        return """
        <html>
        <head>
            <title>Simple Trading Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .success { color: green; font-weight: bold; }
                .warning { color: orange; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Simple Trading Dashboard</h1>
            <p class="warning">⚠️ Template file not found. Using fallback page.</p>
            <p>Dashboard is running, but the full template wasn't loaded.</p>
            <ul>
                <li>API endpoint is available at: <a href="/api/status">/api/status</a></li>
                <li>WebSocket connection should be available</li>
            </ul>
        </body>
        </html>
        """

@app.route('/api/status')
def status():
    """Return status information."""
    return jsonify({
        "status": "online",
        "message": "Dashboard API is working",
        "version": "1.0.0"
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected via WebSocket")
    emit('message', {'status': 'connected', 'message': 'Connection established'})

def main():
    """Main function to run the dashboard"""
    try:
        # Print header
        print("-" * 56)
        logger.info("Starting Simple Trading Dashboard...")
        print("-" * 56)
        
        # Get port from environment or use default 8085 to avoid conflicts
        port = int(os.environ.get('PORT', 8085))
        
        # Print access instructions
        print(f"When ready, access the dashboard at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        print("-" * 56)
        
        # Run the dashboard
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        
        # Print user-friendly error message
        print("-" * 56)
        print(f"Dashboard server has stopped. Error: {e}")
        print("-" * 56)
        sys.exit(1)
    
    # Goodbye message when server stops
    print("-" * 56)
    print("Dashboard server has stopped. Press any key to close this window.")
    print("-" * 56)

if __name__ == '__main__':
    main() 