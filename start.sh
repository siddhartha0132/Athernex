#!/bin/bash

echo "============================================================"
echo "  AI Voice Call System - Startup Script"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "Then run: pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials"
    exit 1
fi

echo "[1/3] Activating virtual environment..."
source venv/bin/activate

echo "[2/3] Checking dependencies..."
python -c "import flask, twilio, requests, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

echo "[3/3] Starting Flask server..."
echo ""
echo "============================================================"
echo "  Server will start on http://localhost:5000"
echo "  Press Ctrl+C to stop"
echo "============================================================"
echo ""
echo "IMPORTANT: In another terminal, run: ngrok http 5000"
echo ""

python app.py
