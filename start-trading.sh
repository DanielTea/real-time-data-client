#!/usr/bin/env bash
#
# Stop all services and restart trading server
#

echo "🛑 Stopping all running services..."
echo ""

# Stop trading server
pkill -f alpaca-trading-server.py && echo "   ✓ Stopped trading server" || echo "   - No trading server running"

# Stop WebSocket server
pkill -f websocket-server.js && echo "   ✓ Stopped WebSocket server" || echo "   - No WebSocket server running"

# Stop frontend
pkill -f "vite.*5173" && echo "   ✓ Stopped frontend" || echo "   - No frontend running"

# Wait for processes to fully terminate
sleep 2

echo ""
echo "🚀 Starting services..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: uv venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Create logs directory
mkdir -p logs

echo "🔧 Starting Alpaca Trading Server on port 5001..."
echo "   (Uses alpaca-py library directly - same as official Alpaca MCP server)"
python alpaca-trading-server.py > logs/trading-$(date +%Y%m%d_%H%M%S).log 2>&1 &
SERVER_PID=$!
echo "   ✅ Trading Server started (PID: $SERVER_PID)"

sleep 2

# Verify it started
if ps -p $SERVER_PID > /dev/null; then
    echo ""
    echo "✅ Alpaca Trading Server started successfully!"
    echo ""
    echo "🌐 REST API: http://localhost:5001"
    echo "📝 Implementation: alpaca-py (same library as official MCP server)"
    echo ""
    echo "Configure your API keys via the Settings page at http://localhost:5173/settings"
    echo ""
    echo "To stop, run: ./stop-all.sh"
    echo ""
else
    echo ""
    echo "❌ Trading Server failed to start!"
    echo "Check logs: logs/trading-*.log"
    exit 1
fi
