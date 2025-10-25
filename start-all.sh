#!/usr/bin/env bash

# All-in-One Startup Script
# Installs dependencies and starts all services

# Ensure script is run with bash
if [ -z "$BASH_VERSION" ]; then
    echo "Error: This script requires bash. Please run with: bash start-all.sh"
    exit 1
fi

# Note: We don't use 'set -e' to allow graceful error handling

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Polymarket + Trading Chat All-in-One Startup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  Port $port is in use. Killing existing process...${NC}"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"
echo ""

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed!${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js $(node --version)"

if ! command_exists pnpm; then
    echo -e "${YELLOW}⚠️  pnpm not found. Installing...${NC}"
    npm install -g pnpm
fi
echo -e "${GREEN}✓${NC} pnpm $(pnpm --version)"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $(python3 --version)"

if ! command_exists uv; then
    echo -e "${YELLOW}⚠️  uv not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo -e "${GREEN}✓${NC} uv installed"

echo ""

# Check environment files
if [ ! -f "keys.env" ]; then
    echo -e "${YELLOW}⚠️  keys.env not found!${NC}"
    echo "Please create keys.env with your Polymarket credentials"
    echo "Run: python generate_api_key.py"
    exit 1
fi
echo -e "${GREEN}✓${NC} keys.env found"

echo ""

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
echo ""

# Install Node.js dependencies (root)
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing root Node.js dependencies...${NC}"
    pnpm install
else
    echo -e "${GREEN}✓${NC} Root dependencies already installed"
fi

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    pnpm install
    cd ..
else
    echo -e "${GREEN}✓${NC} Frontend dependencies already installed"
fi

# Setup Python virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    uv venv .venv
fi
echo -e "${GREEN}✓${NC} Python virtual environment ready"

# Install Python dependencies
source .venv/bin/activate
echo -e "${YELLOW}Installing Python trading dependencies...${NC}"
uv pip install -r requirements-trading.txt > /tmp/uv-install.log 2>&1 || {
    echo -e "${YELLOW}⚠️  Warning: Python dependencies installation had issues${NC}"
    echo "Check /tmp/uv-install.log for details"
}
echo -e "${GREEN}✓${NC} Python dependencies ready"

echo ""

# Clean up any existing processes
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
kill_port 8080  # WebSocket server
kill_port 5001  # Trading server
kill_port 5173  # Frontend dev server

echo ""

# Check API keys
TRADING_ENABLED=false
if [ -f "$HOME/.config/trading-keys.env" ] || grep -q "alpaca_key" "$HOME/.local/share/polymarket-trading" 2>/dev/null; then
    TRADING_ENABLED=true
fi

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
echo ""

# Start WebSocket Server (Polymarket)
echo -e "${YELLOW}Starting Polymarket WebSocket Server (port 8080)...${NC}"
node websocket-server.js > "$LOG_DIR/websocket-$TIMESTAMP.log" 2>&1 &
WS_PID=$!
sleep 2

if ps -p $WS_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} WebSocket Server running (PID: $WS_PID)"
else
    echo -e "${RED}❌ Failed to start WebSocket Server${NC}"
    echo "Check logs: $LOG_DIR/websocket-$TIMESTAMP.log"
    exit 1
fi

# Start Trading Server (Optional)
echo -e "${YELLOW}Starting Trading Server (port 5001)...${NC}"
source .venv/bin/activate
python alpaca-trading-server.py > "$LOG_DIR/trading-$TIMESTAMP.log" 2>&1 &
TRADING_PID=$!
sleep 2

if ps -p $TRADING_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} Trading Server running (PID: $TRADING_PID)"
    echo -e "${BLUE}ℹ️  Configure API keys in Settings to use trading features${NC}"
else
    echo -e "${YELLOW}⚠️  Trading Server failed to start (optional)${NC}"
    TRADING_PID=""
fi

# Start Frontend
echo -e "${YELLOW}Starting Frontend Dev Server (port 5173)...${NC}"
cd frontend
pnpm dev > "$LOG_DIR/frontend-$TIMESTAMP.log" 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend running (PID: $FRONTEND_PID)"
else
    echo -e "${RED}❌ Failed to start Frontend${NC}"
    echo "Check logs: $LOG_DIR/frontend-$TIMESTAMP.log"
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ All services started successfully!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Display service info
echo -e "${BLUE}🌐 Services:${NC}"
echo ""
echo -e "  📊 ${GREEN}Dashboard:${NC}           http://localhost:5173"
echo -e "  🔌 ${GREEN}WebSocket Server:${NC}    ws://localhost:8080"
if [ ! -z "$TRADING_PID" ]; then
    echo -e "  💬 ${GREEN}Trading Server:${NC}      http://localhost:5001"
fi
echo ""

echo -e "${BLUE}📝 Logs:${NC}"
echo ""
echo -e "  WebSocket: $LOG_DIR/websocket-$TIMESTAMP.log"
if [ ! -z "$TRADING_PID" ]; then
    echo -e "  Trading:   $LOG_DIR/trading-$TIMESTAMP.log"
fi
echo -e "  Frontend:  $LOG_DIR/frontend-$TIMESTAMP.log"
echo ""

echo -e "${BLUE}🔑 Process IDs:${NC}"
echo ""
echo -e "  WebSocket Server: $WS_PID"
if [ ! -z "$TRADING_PID" ]; then
    echo -e "  Trading Server:   $TRADING_PID"
fi
echo -e "  Frontend:         $FRONTEND_PID"
echo ""

# Save PIDs to file for easy cleanup
cat > "$SCRIPT_DIR/.running-services.pid" <<EOF
WS_PID=$WS_PID
TRADING_PID=$TRADING_PID
FRONTEND_PID=$FRONTEND_PID
EOF

echo -e "${YELLOW}💡 To stop all services, run:${NC}"
echo -e "   ./stop-all.sh"
echo ""
echo -e "${YELLOW}💡 To view logs in real-time:${NC}"
echo -e "   tail -f $LOG_DIR/websocket-$TIMESTAMP.log"
echo -e "   tail -f $LOG_DIR/trading-$TIMESTAMP.log"
echo -e "   tail -f $LOG_DIR/frontend-$TIMESTAMP.log"
echo ""

# Setup trading
if [ -z "$TRADING_PID" ] || ! ps -p $TRADING_PID > /dev/null; then
    echo -e "${YELLOW}⚠️  Trading features require API keys:${NC}"
    echo "   1. Get Alpaca API keys: https://alpaca.markets/"
    echo "   2. Get Claude API key: https://console.anthropic.com/"
    echo "   3. Configure in Settings → Trading API Configuration"
    echo ""
fi

echo -e "${GREEN}✨ Opening browser...${NC}"
sleep 2

# Open browser
if command_exists open; then
    open http://localhost:5173
elif command_exists xdg-open; then
    xdg-open http://localhost:5173
elif command_exists start; then
    start http://localhost:5173
fi

echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for user interrupt
trap 'echo ""; echo -e "${YELLOW}Stopping all services...${NC}"; kill $WS_PID $TRADING_PID $FRONTEND_PID 2>/dev/null; rm -f .running-services.pid; echo -e "${GREEN}All services stopped!${NC}"; exit 0' INT TERM

# Keep script running
wait

