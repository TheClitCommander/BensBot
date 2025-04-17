#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test dashboard to verify connectivity
"""

from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Dashboard Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .success { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Dashboard Test Page</h1>
        <p class="success">✅ Connection successful!</p>
        <p>If you can see this page, your web server is working correctly.</p>
        <p>The issue might be with:</p>
        <ul>
            <li>Dependencies: Install required packages with <code>pip install -r requirements.txt</code></li>
            <li>Port conflict: Try using a different port (current: 8085)</li>
            <li>Python path: Ensure your working directory structure is correct</li>
        </ul>
    </body>
    </html>
    """

@app.route('/api/test')
def test_api():
    return jsonify({
        "status": "success",
        "message": "API endpoint is working"
    })

if __name__ == '__main__':
    PORT = 8085  # Using a different port to avoid conflicts
    print(f"\n🚀 Test server running at: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server\n")
    app.run(host='0.0.0.0', port=PORT, debug=True) 