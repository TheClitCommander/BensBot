#!/usr/bin/env python3
"""
Minimal Dashboard Server

This is a standalone dashboard with no dependencies on other modules
"""

from flask import Flask, jsonify, render_template_string
import datetime
import json
import logging
import random
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #2c3e50;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .card {
            background-color: white;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .success {
            color: green;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .positive { color: green; }
        .negative { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Trading Dashboard</h1>
        <p>Server time: {{ server_time }}</p>
    </div>
    
    <div class="card">
        <h2>Connection Status</h2>
        <p class="success">✅ Dashboard server is running correctly!</p>
        <p>If you're seeing this page, the Flask server is working properly.</p>
    </div>
    
    <div class="card">
        <h2>Portfolio Summary</h2>
        <table>
            <tr>
                <th>Total Value</th>
                <td>$100,000.00</td>
            </tr>
            <tr>
                <th>Cash</th>
                <td>$25,000.00</td>
            </tr>
            <tr>
                <th>Equity</th>
                <td>$75,000.00</td>
            </tr>
            <tr>
                <th>P&L</th>
                <td class="positive">+$5,000.00 (+5.26%)</td>
            </tr>
        </table>
    </div>
    
    <div class="card">
        <h2>Positions</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>AAPL</td>
                    <td>100</td>
                    <td>$150.00</td>
                    <td>$175.00</td>
                    <td class="positive">+$2,500.00 (+16.67%)</td>
                </tr>
                <tr>
                    <td>MSFT</td>
                    <td>50</td>
                    <td>$250.00</td>
                    <td>$300.00</td>
                    <td class="positive">+$2,500.00 (+20.00%)</td>
                </tr>
                <tr>
                    <td>TSLA</td>
                    <td>10</td>
                    <td>$200.00</td>
                    <td>$180.00</td>
                    <td class="negative">-$200.00 (-10.00%)</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Render the dashboard page"""
    server_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(DASHBOARD_HTML, server_time=server_time)

@app.route('/api/status')
def status():
    """Return the server status"""
    return jsonify({
        "status": "ok",
        "time": datetime.datetime.now().isoformat(),
        "server": "mini_dashboard",
        "version": "1.0.0"
    })

@app.route('/api/portfolio')
def portfolio():
    """Return portfolio data"""
    return jsonify({
        "total_value": 100000.00,
        "cash": 25000.00,
        "equity": 75000.00,
        "pnl": 5000.00,
        "pnl_percent": 5.26,
        "positions": [
            {"symbol": "AAPL", "quantity": 100, "entry": 150.00, "current": 175.00, "pnl": 2500.00, "pnl_percent": 16.67},
            {"symbol": "MSFT", "quantity": 50, "entry": 250.00, "current": 300.00, "pnl": 2500.00, "pnl_percent": 20.00},
            {"symbol": "TSLA", "quantity": 10, "entry": 200.00, "current": 180.00, "pnl": -200.00, "pnl_percent": -10.00}
        ]
    })

if __name__ == "__main__":
    # Use a port that's definitely free (not 5000, 8080, or 8090)
    PORT = 9876
    HOST = "0.0.0.0"
    
    print(f"\n{'='*60}")
    print(f"Mini Dashboard Server Starting")
    print(f"{'='*60}")
    print(f"Access URL: http://localhost:{PORT}")
    print(f"API Status: http://localhost:{PORT}/api/status")
    print(f"API Portfolio: http://localhost:{PORT}/api/portfolio")
    print(f"Press Ctrl+C to exit")
    print(f"{'='*60}\n")
    
    # Start the server
    app.run(host=HOST, port=PORT, debug=True) 