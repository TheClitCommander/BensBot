#!/bin/bash

# Script to set up and run the React dashboard

echo "============================================"
echo "         Setting up React Dashboard         "
echo "============================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install Node.js:"
    echo "  brew install node"
    exit 1
fi

# Navigate to UI directory
cd ui || exit

# Install dependencies
echo "Installing dependencies..."
npm install

# Start the React app
echo "Starting the React dashboard..."
echo "The dashboard will be available at: http://localhost:3000"
npm start 