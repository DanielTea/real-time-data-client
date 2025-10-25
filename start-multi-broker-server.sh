#!/bin/bash

# Multi-Broker Trading Server Startup Script
# Supports: Alpaca, Bybit, Binance

echo "🚀 Starting Multi-Broker Trading Server..."
echo ""
echo "📊 Supported Brokers:"
echo "  • Alpaca (Stocks + Crypto + Options)"
echo "  • Bybit (Crypto Futures, 100x Leverage)"
echo "  • Binance (Crypto Futures, 125x Leverage)"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv venv' first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if broker dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing broker dependencies..."
    uv pip install requests
fi

# Start the server
echo ""
echo "✅ Starting server on http://localhost:5002"
echo "📝 Configure your broker in the frontend Settings page"
echo ""
echo "Press Ctrl+C to stop the server"
echo "═══════════════════════════════════════════"
echo ""

python3 multi-broker-trading-server.py

