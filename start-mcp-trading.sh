#!/usr/bin/env bash
#
# Start the official Alpaca MCP Server and wrapper
#

set -e

echo "🚀 Starting Alpaca MCP Trading Server..."
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

# Set environment variables from keys.env if it exists
if [ -f "keys.env" ]; then
    echo "📝 Loading environment variables from keys.env..."
    export $(grep -v '^#' keys.env | xargs)
fi

# Check if API keys are set (optional, will be set via frontend)
if [ -z "$ALPACA_API_KEY" ]; then
    echo "⚠️  ALPACA_API_KEY not set in keys.env - you'll need to configure it via Settings"
fi

# Start the official Alpaca MCP server
echo "🔧 Starting official Alpaca MCP Server on port 8000..."
alpaca-mcp-server serve --transport http --port 8000 --host 127.0.0.1 > logs/alpaca-mcp-$(date +%Y%m%d_%H%M%S).log 2>&1 &
MCP_PID=$!
echo "   Official MCP Server started (PID: $MCP_PID)"

# Wait for MCP server to be ready
sleep 3

# Start the wrapper server
echo "🔧 Starting MCP wrapper server on port 5001..."
python mcp-trading-server.py > logs/mcp-wrapper-$(date +%Y%m%d_%H%M%S).log 2>&1 &
WRAPPER_PID=$!
echo "   Wrapper server started (PID: $WRAPPER_PID)"

echo ""
echo "✅ All servers started!"
echo ""
echo "📊 Official Alpaca MCP Server: http://localhost:8000 (PID: $MCP_PID)"
echo "🌐 Wrapper REST API: http://localhost:5001 (PID: $WRAPPER_PID)"
echo ""
echo "To stop all servers, run: ./stop-all.sh"
echo ""

