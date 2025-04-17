#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Restart Dashboard Script

This script:
1. Terminates any process using port 8080
2. Installs required dependencies
3. Launches a simplified dashboard on port 8080
"""

import os
import sys
import subprocess
import time
import logging
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_and_kill_port_process(port):
    """Find and kill any process using the specified port."""
    print(f"Looking for processes using port {port}...")
    
    is_windows = platform.system() == "Windows"
    is_mac = platform.system() == "Darwin"
    
    try:
        if is_windows:
            # Windows command to find process using port
            cmd = f"netstat -ano | findstr :{port}"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            if result:
                # Extract PID
                for line in result.split('\n'):
                    if f":{port}" in line and "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        print(f"Found process with PID {pid} using port {port}")
                        # Kill the process
                        print(f"Terminating process {pid}...")
                        subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                        time.sleep(1)  # Give it time to terminate
                        return True
        elif is_mac:
            # macOS command to find process using port
            cmd = f"lsof -i :{port}"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            if result:
                # Extract PID
                lines = result.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    for line in lines[1:]:
                        pid = line.split()[1]
                        print(f"Found process with PID {pid} using port {port}")
                        # Kill the process
                        print(f"Terminating process {pid}...")
                        subprocess.call(f"kill -9 {pid}", shell=True)
                        time.sleep(1)  # Give it time to terminate
                        return True
        else:
            # Linux command to find process using port
            cmd = f"lsof -i :{port} -t"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            if result:
                pid = result.strip()
                print(f"Found process with PID {pid} using port {port}")
                # Kill the process
                print(f"Terminating process {pid}...")
                subprocess.call(f"kill -9 {pid}", shell=True)
                time.sleep(1)  # Give it time to terminate
                return True
                
        print(f"No process found using port {port}")
        return False
    except subprocess.CalledProcessError:
        print(f"No process found using port {port}")
        return False
    except Exception as e:
        print(f"Error finding/killing process: {e}")
        return False

def install_dependencies():
    """Install required packages for the dashboard."""
    try:
        print("Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio", "flask-cors"])
        return True
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_simple_dashboard():
    """Create a simple dashboard file that will work."""
    dashboard_code = """
from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import datetime
import threading
import time
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'trading_dashboard_secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Dashboard HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Trading Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        .metrics {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .metric {
            flex: 1;
            min-width: 150px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            margin: 5px 0;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .chart-container {
            height: 300px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background-color: #f8f9fa;
        }
        #notifications {
            max-height: 200px;
            overflow-y: auto;
        }
        .notification {
            padding: 10px;
            margin-bottom: 5px;
            background-color: #f8f9fa;
            border-left: 4px solid #f39c12;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>Simple Trading Dashboard</h1>
        <p>Last updated: <span id="last-updated">-</span></p>
    </div>
    
    <div class="card">
        <h2>Portfolio Overview</h2>
        <div class="metrics">
            <div class="metric">
                <div>Portfolio Value</div>
                <div class="metric-value">$<span id="portfolio-value">100,000.00</span></div>
                <div id="portfolio-change" class="positive">+0.00%</div>
            </div>
            <div class="metric">
                <div>Cash Balance</div>
                <div class="metric-value">$<span id="cash-balance">50,000.00</span></div>
                <div>50.00% of portfolio</div>
            </div>
            <div class="metric">
                <div>Profit/Loss</div>
                <div class="metric-value">$<span id="pnl-value">5,000.00</span></div>
                <div id="pnl-percent" class="positive">+5.00%</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>Portfolio Performance</h2>
        <div class="chart-container">
            <canvas id="performance-chart"></canvas>
        </div>
    </div>
    
    <div class="card">
        <h2>Positions</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Entry Price</th>
                    <th>Current Price</th>
                    <th>P&L</th>
                </tr>
            </thead>
            <tbody id="positions-table">
                <!-- Will be populated via JavaScript -->
            </tbody>
        </table>
    </div>
    
    <div class="card">
        <h2>Notifications</h2>
        <div id="notifications">
            <!-- Will be populated via JavaScript -->
        </div>
    </div>
    
    <script>
        // Initialize data
        let portfolioData = {
            value: 100000,
            cash: 50000,
            pnl: 5000,
            pnlPercent: 5.0,
            change: 0.5
        };
        
        let positions = [
            { symbol: 'AAPL', quantity: 100, entryPrice: 150.50, currentPrice: 165.75, pnl: 1525, pnlPercent: 10.13 },
            { symbol: 'MSFT', quantity: 50, entryPrice: 250.25, currentPrice: 275.80, pnl: 1277.5, pnlPercent: 10.21 },
            { symbol: 'TSLA', quantity: 20, entryPrice: 180.45, currentPrice: 175.20, pnl: -105, pnlPercent: -2.91 }
        ];
        
        // Format currency and percentage
        function formatCurrency(value) {
            return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        
        function formatPercent(value) {
            return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%';
        }
        
        // Update the UI with the latest data
        function updateUI() {
            // Update portfolio metrics
            document.getElementById('portfolio-value').textContent = formatCurrency(portfolioData.value);
            document.getElementById('cash-balance').textContent = formatCurrency(portfolioData.cash);
            document.getElementById('pnl-value').textContent = formatCurrency(portfolioData.pnl);
            
            const pnlPercentEl = document.getElementById('pnl-percent');
            pnlPercentEl.textContent = (portfolioData.pnlPercent >= 0 ? '+' : '') + formatPercent(portfolioData.pnlPercent);
            pnlPercentEl.className = portfolioData.pnlPercent >= 0 ? 'positive' : 'negative';
            
            const portfolioChangeEl = document.getElementById('portfolio-change');
            portfolioChangeEl.textContent = (portfolioData.change >= 0 ? '+' : '') + formatPercent(portfolioData.change);
            portfolioChangeEl.className = portfolioData.change >= 0 ? 'positive' : 'negative';
            
            // Update positions table
            const positionsTable = document.getElementById('positions-table');
            positionsTable.innerHTML = '';
            
            positions.forEach(position => {
                const row = document.createElement('tr');
                const pnlClass = position.pnl >= 0 ? 'positive' : 'negative';
                
                row.innerHTML = `
                    <td>${position.symbol}</td>
                    <td>${position.quantity}</td>
                    <td>$${formatCurrency(position.entryPrice)}</td>
                    <td>$${formatCurrency(position.currentPrice)}</td>
                    <td class="${pnlClass}">$${formatCurrency(position.pnl)} (${(position.pnl >= 0 ? '+' : '')}${formatPercent(position.pnlPercent)})</td>
                `;
                
                positionsTable.appendChild(row);
            });
            
            // Update last updated time
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
        }
        
        // Initialize the performance chart
        let performanceChart;
        
        function initializeChart() {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            // Generate some sample data
            const labels = [];
            const portfolioValues = [];
            const benchmarkValues = [];
            
            const today = new Date();
            for (let i = 30; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(today.getDate() - i);
                labels.push(date.toLocaleDateString());
                
                // Start at 95000 and trend upward with some randomness
                const baseValue = 95000 + (5000 * (30 - i) / 30);
                const randomFactor = Math.random() * 1000 - 500;
                portfolioValues.push(baseValue + randomFactor);
                
                // Benchmark grows slower
                const benchmarkBaseValue = 97500 + (2500 * (30 - i) / 30);
                const benchmarkRandomFactor = Math.random() * 800 - 400;
                benchmarkValues.push(benchmarkBaseValue + benchmarkRandomFactor);
            }
            
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Portfolio',
                            data: portfolioValues,
                            borderColor: 'rgb(52, 152, 219)',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.1,
                            fill: true
                        },
                        {
                            label: 'Benchmark',
                            data: benchmarkValues,
                            borderColor: 'rgb(243, 156, 18)',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            borderDash: [5, 5],
                            tension: 0.1,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: value => '$' + value.toLocaleString()
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Add a notification to the list
        function addNotification(message) {
            const notificationsDiv = document.getElementById('notifications');
            const notificationEl = document.createElement('div');
            notificationEl.className = 'notification';
            notificationEl.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
            
            notificationsDiv.prepend(notificationEl);
            
            // Limit to 10 notifications
            if (notificationsDiv.children.length > 10) {
                notificationsDiv.removeChild(notificationsDiv.lastChild);
            }
        }
        
        // Connect to WebSocket server
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Connected to server');
            addNotification('Dashboard connected to server');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            addNotification('Dashboard disconnected from server');
        });
        
        socket.on('data_update', (data) => {
            console.log('Received data update:', data);
            
            // Update our data objects
            if (data.portfolio) {
                portfolioData = data.portfolio;
            }
            
            if (data.positions) {
                positions = data.positions;
            }
            
            // Update the UI
            updateUI();
            
            // Add notification
            addNotification('Received data update from server');
        });
        
        socket.on('notification', (data) => {
            addNotification(data.message);
        });
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            initializeChart();
            updateUI();
            addNotification('Dashboard initialized');
        });
    </script>
</body>
</html>
'''

# Mock data for the dashboard
portfolio_data = {
    "value": 100000,
    "cash": 50000,
    "pnl": 5000,
    "pnlPercent": 5.0,
    "change": 0.5
}

positions_data = [
    {"symbol": "AAPL", "quantity": 100, "entryPrice": 150.50, "currentPrice": 165.75, "pnl": 1525, "pnlPercent": 10.13},
    {"symbol": "MSFT", "quantity": 50, "entryPrice": 250.25, "currentPrice": 275.80, "pnl": 1277.5, "pnlPercent": 10.21},
    {"symbol": "TSLA", "quantity": 20, "entryPrice": 180.45, "currentPrice": 175.20, "pnl": -105, "pnlPercent": -2.91}
]

# Define routes
@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def get_data():
    """API endpoint to get current data."""
    return jsonify({
        "portfolio": portfolio_data,
        "positions": positions_data,
        "timestamp": datetime.datetime.now().isoformat()
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    socketio.emit('notification', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

# Background thread for sending updates
def background_thread():
    """Background thread to send periodic updates to clients."""
    count = 0
    while True:
        socketio.sleep(5)  # Send updates every 5 seconds
        count += 1
        
        # Simulate price changes
        for position in positions_data:
            # Random price change between -1% and +1%
            price_change = random.uniform(-0.01, 0.01)
            position["currentPrice"] *= (1 + price_change)
            position["pnl"] = position["quantity"] * (position["currentPrice"] - position["entryPrice"])
            position["pnlPercent"] = ((position["currentPrice"] / position["entryPrice"]) - 1) * 100
        
        # Update portfolio value based on positions
        total_position_value = sum(p["quantity"] * p["currentPrice"] for p in positions_data)
        portfolio_data["value"] = portfolio_data["cash"] + total_position_value
        portfolio_data["pnl"] = portfolio_data["value"] - 95000  # Assuming initial investment was 95000
        portfolio_data["pnlPercent"] = (portfolio_data["pnl"] / 95000) * 100
        
        # Add small change for current update
        portfolio_data["change"] = random.uniform(-0.5, 0.7)
        
        # Emit update to clients
        socketio.emit('data_update', {
            "portfolio": portfolio_data,
            "positions": positions_data
        })
        
        if count % 12 == 0:  # Every ~1 minute
            # Send a notification
            notification_messages = [
                "Market volatility increasing",
                "New trading signal detected",
                "Portfolio rebalancing recommended",
                "Market close approaching",
                "Data feed updated",
                "Strategy performance report available"
            ]
            socketio.emit('notification', {
                'message': random.choice(notification_messages)
            })

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=background_thread)
    thread.daemon = True
    thread.start()
    
    # Run the app
    port = 8080
    print(f"🚀 Dashboard running at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server\n")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

    with open("working_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("Created working_dashboard.py")
    return True

def run_dashboard():
    """Run the dashboard."""
    try:
        print("Starting dashboard on port 8080...")
        subprocess.Popen([sys.executable, "working_dashboard.py"])
        print("Dashboard started successfully!")
        print("Access your dashboard at: http://localhost:8080")
        return True
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        return False

def main():
    """Main function to restart dashboard."""
    print("=" * 60)
    print("Dashboard Restart Tool")
    print("=" * 60)
    
    # 1. Kill any process using port 8080
    find_and_kill_port_process(8080)
    
    # 2. Install dependencies
    install_dependencies()
    
    # 3. Create simple dashboard
    create_simple_dashboard()
    
    # 4. Run the dashboard
    if run_dashboard():
        print("\nDashboard is now running in the background.")
        print("Open your browser and go to: http://localhost:8080")
    else:
        print("\nFailed to start dashboard. Please check the error messages above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 