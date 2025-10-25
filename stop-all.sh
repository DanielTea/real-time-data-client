#!/bin/bash

# Stop All Services Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🛑 Stopping All Services                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to kill process on port
kill_port() {
    local port=$1
    local name=$2
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Stopping $name (port $port)...${NC}"
        kill -15 $pids 2>/dev/null || kill -9 $pids 2>/dev/null
        sleep 1
        echo -e "${GREEN}✓${NC} $name stopped"
    fi
}

# Read PIDs from file if exists
if [ -f ".running-services.pid" ]; then
    source .running-services.pid
    
    if [ ! -z "$WS_PID" ] && ps -p $WS_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping WebSocket Server (PID: $WS_PID)...${NC}"
        kill -15 $WS_PID 2>/dev/null || kill -9 $WS_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} WebSocket Server stopped"
    fi
    
    if [ ! -z "$TRADING_PID" ] && ps -p $TRADING_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Trading Server (PID: $TRADING_PID)...${NC}"
        kill -15 $TRADING_PID 2>/dev/null || kill -9 $TRADING_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Trading Server stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
        kill -15 $FRONTEND_PID 2>/dev/null || kill -9 $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Frontend stopped"
    fi
    
    rm -f .running-services.pid
fi

# Fallback: kill by port
kill_port 8080 "WebSocket Server"
kill_port 8000 "Alpaca MCP Server"
kill_port 5001 "Trading Server / MCP Wrapper"
kill_port 5173 "Frontend"

# Clean up any remaining node/python processes related to our servers
pkill -f "websocket-server.js" 2>/dev/null
pkill -f "alpaca-trading-server.py" 2>/dev/null
pkill -f "mcp-alpaca-trading-server.py" 2>/dev/null
pkill -f "trading-mcp-client.py" 2>/dev/null
pkill -f "alpaca-alpaca-trading-server.py" 2>/dev/null
pkill -f "alpaca-mcp-server" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"
echo ""
echo -e "${BLUE}To start again, run:${NC}"
echo -e "   ./start-all.sh"
echo ""

