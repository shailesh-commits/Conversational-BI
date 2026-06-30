#!/bin/bash
# Conversational BI Assistant - Startup Script for macOS/Linux

echo ""
echo "===================================================="
echo "  Conversational BI Assistant - Quick Start"
echo "===================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate sample data if not exists
if [ ! -f "data/sales_data.db" ]; then
    echo "Generating sample data..."
    python data/sample_data.py
fi

# Start backend
echo ""
echo "===================================================="
echo "Starting Flask backend on http://localhost:5000"
echo "===================================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python backend/app.py
