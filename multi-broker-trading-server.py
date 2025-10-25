#!/usr/bin/env python3
"""
Multi-Broker Trading Server
Supports: Alpaca, Bybit, Binance with leverage trading
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from anthropic import Anthropic
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np

# Add brokers directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import broker abstraction
from broker_adapter import (
    initialize_broker,
    get_current_broker,
    get_broker_info,
    get_supported_brokers
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state
broker = None
anthropic_client = None
openai_client = None
ai_model = "claude"

# Auto-trading state
autotrading_active = False
autotrading_thread = None
autotrading_config = None
autotrading_logs = []
conversation_history = []

def add_autotrading_log(message, log_type="info"):
    """Add a log entry for auto-trading"""
    global autotrading_logs
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "type": log_type
    }
    autotrading_logs.append(log_entry)
    if len(autotrading_logs) > 500:
        autotrading_logs = autotrading_logs[-500:]
    logger.info(f"Auto-trading: {message}")

# Technical analysis functions
def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    if len(prices) < slow:
        return None, None, None
    
    ema_fast = pd.Series(prices).ewm(span=fast).mean().iloc[-1]
    ema_slow = pd.Series(prices).ewm(span=slow).mean().iloc[-1]
    macd_line = ema_fast - ema_slow
    
    macd_values = pd.Series(prices).ewm(span=fast).mean() - pd.Series(prices).ewm(span=slow).mean()
    signal_line = macd_values.ewm(span=signal).mean().iloc[-1]
    histogram = macd_line - signal_line
    
    return round(macd_line, 4), round(signal_line, 4), round(histogram, 4)

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return None, None, None
    
    recent_prices = prices[-period:]
    sma = sum(recent_prices) / period
    variance = sum((x - sma) ** 2 for x in recent_prices) / period
    std = variance ** 0.5
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return round(upper, 2), round(sma, 2), round(lower, 2)

# Tool definitions with leverage support
TOOLS = [
    {
        "name": "get_account",
        "description": "Get account information (balance, equity, buying power, etc.)",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_all_positions",
        "description": "Get all current positions",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "close_position",
        "description": "Close a position (full or partial)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol to close"},
                "qty": {"type": "number", "description": "Quantity to close (optional)"},
                "percentage": {"type": "number", "description": "Percentage to close (optional, e.g., 50 for 50%)"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_crypto_latest_bar",
        "description": "Get latest crypto price data",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Crypto symbol (e.g., BTC/USD, BTCUSDT)"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "place_crypto_order",
        "description": "Place crypto order. Supports LEVERAGE on Bybit/Binance (up to 100x/125x)!",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Crypto symbol"},
                "side": {"type": "string", "enum": ["buy", "sell"], "description": "Order side"},
                "qty": {"type": "number", "description": "Quantity (optional if notional provided)"},
                "notional": {"type": "number", "description": "Dollar amount (optional if qty provided)"},
                "leverage": {
                    "type": "integer",
                    "description": "Leverage multiplier (1-100 for Bybit, 1-125 for Binance, 1 for Alpaca). Example: 10 for 10x leverage"
                }
            },
            "required": ["symbol", "side"]
        }
    },
    {
        "name": "place_stock_order",
        "description": "Place stock order (Alpaca only, not supported on Bybit/Binance)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "qty": {"type": "number", "description": "Quantity"},
                "notional": {"type": "number", "description": "Dollar amount (optional)"},
                "order_type": {"type": "string", "enum": ["market", "limit", "stop", "stop_limit"], "description": "Order type"},
                "limit_price": {"type": "number", "description": "Limit price (for limit orders)"},
                "stop_price": {"type": "number", "description": "Stop price (for stop orders)"},
                "time_in_force": {"type": "string", "enum": ["day", "gtc", "ioc", "fok"], "description": "Time in force"}
            },
            "required": ["symbol", "side"]
        }
    },
    {
        "name": "get_stock_quote",
        "description": "Get stock quote (Alpaca only)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_stock_bars",
        "description": "Get historical stock/crypto bars",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["1Min", "5Min", "15Min", "1Hour", "1Day"]},
                "limit": {"type": "integer", "description": "Number of bars (default 100)"}
            },
            "required": ["symbol", "timeframe"]
        }
    },
    {
        "name": "get_technical_indicators",
        "description": "Get comprehensive technical analysis (RSI, MACD, Bollinger Bands, Moving Averages)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol to analyze"},
                "timeframe": {"type": "string", "enum": ["1d", "1h", "15m"], "description": "Timeframe for analysis"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_orders",
        "description": "Get orders (open, closed, or all)",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["open", "closed", "all"], "description": "Order status filter"}
            },
            "required": []
        }
    },
    {
        "name": "cancel_order",
        "description": "Cancel a specific order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to cancel"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "cancel_all_orders",
        "description": "Cancel all pending orders",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_market_clock",
        "description": "Check if market is open (for stocks) or get market status",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    # Trading memory tools
    {
        "name": "read_trading_memory",
        "description": "Read trading memory with line numbers",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "write_trading_memory",
        "description": "Write/update trading memory",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "append_trading_memory",
        "description": "Append to trading memory",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to append"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "clear_trading_memory",
        "description": "Clear all trading memory",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]

def execute_tool(tool_name, arguments):
    """Execute a trading tool using broker abstraction"""
    global broker
    
    if not broker:
        return {"error": "Broker not initialized. Please configure broker credentials in Settings."}
    
    try:
        # Account & Portfolio tools
        if tool_name == "get_account":
            return broker.get_account()
        
        elif tool_name == "get_all_positions":
            return broker.get_positions()
        
        elif tool_name == "close_position":
            return broker.close_position(
                symbol=arguments["symbol"],
                qty=arguments.get("qty"),
                percentage=arguments.get("percentage")
            )
        
        # Crypto trading tools
        elif tool_name == "get_crypto_latest_bar":
            return broker.get_crypto_price(arguments["symbol"])
        
        elif tool_name == "place_crypto_order":
            leverage = arguments.get("leverage", 1)
            
            # Check if broker supports leverage
            if leverage > 1 and not broker.supports_crypto_leverage():
                return {
                    "error": f"{broker.get_broker_name()} doesn't support leverage trading. "
                            f"Switch to Bybit or Binance for leverage trading."
                }
            
            # Check max leverage
            max_lev = broker.get_max_leverage('crypto')
            if leverage > max_lev:
                return {
                    "error": f"{broker.get_broker_name()} max leverage is {max_lev}x, "
                            f"you requested {leverage}x"
                }
            
            return broker.place_crypto_order(
                symbol=arguments["symbol"],
                side=arguments["side"],
                qty=arguments.get("qty"),
                notional=arguments.get("notional"),
                leverage=leverage
            )
        
        # Stock trading tools (Alpaca only)
        elif tool_name == "place_stock_order":
            # Check if broker supports stocks
            if not hasattr(broker, 'supports_stocks'):
                # Try to place order, will raise NotImplementedError if not supported
                pass
            
            return broker.place_stock_order(
                symbol=arguments["symbol"],
                side=arguments["side"],
                qty=arguments.get("qty"),
                notional=arguments.get("notional"),
                order_type=arguments.get("order_type", "market"),
                limit_price=arguments.get("limit_price"),
                stop_price=arguments.get("stop_price"),
                time_in_force=arguments.get("time_in_force", "day")
            )
        
        elif tool_name == "get_stock_quote":
            return broker.get_stock_quote(arguments["symbol"])
        
        elif tool_name == "get_stock_bars":
            from datetime import datetime, timedelta
            start = datetime.now() - timedelta(days=30)
            return broker.get_stock_bars(
                symbol=arguments["symbol"],
                timeframe=arguments["timeframe"],
                start=start,
                limit=arguments.get("limit", 100)
            )
        
        # Technical indicators
        elif tool_name == "get_technical_indicators":
            symbol = arguments["symbol"]
            timeframe = arguments.get("timeframe", "1d")
            
            # Determine if it's crypto or stock
            is_crypto = '/' in symbol or symbol.endswith('USDT') or symbol.endswith('USD')
            
            try:
                if is_crypto:
                    # Use broker's historical data
                    from datetime import datetime, timedelta
                    start = datetime.now() - timedelta(days=30)
                    bars = broker.get_stock_bars(symbol, "1Day", start, limit=100)
                    prices = [b['close'] for b in bars]
                else:
                    # Use Yahoo Finance for stocks
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1mo", interval=timeframe)
                    prices = hist['Close'].tolist()
                
                if len(prices) < 20:
                    return {"error": f"Insufficient data for {symbol}"}
                
                # Calculate indicators
                rsi = calculate_rsi(prices)
                macd, signal, histogram = calculate_macd(prices)
                upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(prices)
                
                current_price = prices[-1]
                
                return {
                    "symbol": symbol,
                    "current_price": round(current_price, 2),
                    "rsi": rsi,
                    "rsi_signal": "Oversold" if rsi and rsi < 30 else "Overbought" if rsi and rsi > 70 else "Neutral",
                    "macd": {"line": macd, "signal": signal, "histogram": histogram},
                    "macd_signal": "Bullish" if histogram and histogram > 0 else "Bearish",
                    "bollinger_bands": {"upper": upper_bb, "middle": middle_bb, "lower": lower_bb},
                    "bb_signal": "Near Upper Band" if current_price > middle_bb else "Near Lower Band"
                }
            except Exception as e:
                return {"error": f"Technical analysis failed: {str(e)}"}
        
        # Order management
        elif tool_name == "get_orders":
            status = arguments.get("status", "all")
            return broker.get_orders(status)
        
        elif tool_name == "cancel_order":
            return broker.cancel_order(arguments["order_id"])
        
        elif tool_name == "cancel_all_orders":
            return broker.cancel_all_orders()
        
        # Market status
        elif tool_name == "get_market_clock":
            return broker.get_market_status()
        
        # Trading memory tools
        elif tool_name == "read_trading_memory":
            memory_file = "trading_memory.md"
            if os.path.exists(memory_file):
                with open(memory_file, "r") as f:
                    content = f.read()
                lines = content.split("\n")
                numbered = "\n".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
                return {"content": numbered, "line_count": len(lines)}
            return {"content": "", "line_count": 0}
        
        elif tool_name == "write_trading_memory":
            with open("trading_memory.md", "w") as f:
                f.write(arguments["content"])
            return {"success": True, "message": "Memory updated"}
        
        elif tool_name == "append_trading_memory":
            with open("trading_memory.md", "a") as f:
                f.write("\n" + arguments["content"])
            return {"success": True, "message": "Content appended"}
        
        elif tool_name == "clear_trading_memory":
            with open("trading_memory.md", "w") as f:
                f.write("")
            return {"success": True, "message": "Memory cleared"}
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except NotImplementedError as e:
        return {
            "error": f"{broker.get_broker_name()} doesn't support this feature: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return {"error": str(e)}

# AI conversation functions
def convert_tools_to_openai_format():
    """Convert tools to OpenAI format for DeepSeek"""
    openai_tools = []
    for tool in TOOLS:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        })
    return openai_tools

def call_ai_with_tools(messages_for_ai, max_turns=10):
    """Call AI (Claude or DeepSeek) with tool support"""
    global ai_model, anthropic_client, openai_client
    
    if ai_model == "claude" and anthropic_client:
        return _call_claude_with_tools(messages_for_ai, max_turns)
    elif ai_model == "deepseek" and openai_client:
        return _call_deepseek_with_tools(messages_for_ai, max_turns)
    else:
        return "AI client not initialized. Please configure API keys in Settings."

def _call_claude_with_tools(messages, max_turns):
    """Claude-specific tool calling"""
    for turn in range(max_turns):
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            final_text = next((block.text for block in response.content if hasattr(block, "text")), "")
            return final_text
        
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    result = execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            
            messages.append({"role": "user", "content": tool_results})
            continue
    
    return "Max turns reached."

def _call_deepseek_with_tools(messages, max_turns):
    """DeepSeek-specific tool calling"""
    openai_tools = convert_tools_to_openai_format()
    
    for turn in range(max_turns):
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if not message.tool_calls:
            return message.content
        
        messages.append(message)
        
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_name, tool_args)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })
    
    return "Max turns reached."

# API Endpoints

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    broker_name = broker.get_broker_name() if broker else "None"
    return jsonify({
        "status": "healthy",
        "broker": broker_name,
        "initialized": broker is not None
    })

@app.route('/api/brokers', methods=['GET'])
def get_brokers():
    """Get supported brokers and their info"""
    return jsonify({
        'brokers': get_broker_info(),
        'supported': get_supported_brokers()
    })

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize with broker and API keys"""
    global broker, anthropic_client, openai_client, ai_model, conversation_history
    
    data = request.json
    
    # Get broker configuration
    broker_type = data.get('broker', 'alpaca')
    
    # Get broker API keys based on broker type
    if broker_type == 'alpaca':
        broker_key = data.get('alpaca_key')
        broker_secret = data.get('alpaca_secret')
    elif broker_type == 'bybit':
        broker_key = data.get('bybit_key')
        broker_secret = data.get('bybit_secret')
    elif broker_type == 'binance':
        broker_key = data.get('binance_key')
        broker_secret = data.get('binance_secret')
    else:
        return jsonify({"error": f"Unsupported broker: {broker_type}"}), 400
    
    if not broker_key or not broker_secret:
        return jsonify({"error": f"Missing API keys for {broker_type}"}), 400
    
    # Get AI keys and settings
    claude_key = data.get('claude_key')
    deepseek_key = data.get('deepseek_key')
    selected_model = data.get('ai_model', 'claude')
    paper_mode = data.get('paper_mode', True)
    
    try:
        # Initialize broker
        broker = initialize_broker(
            broker_type=broker_type,
            api_key=broker_key,
            api_secret=broker_secret,
            paper_mode=paper_mode
        )
        
        # Initialize AI clients
        ai_model = selected_model
        if ai_model == 'claude' and claude_key:
            anthropic_client = Anthropic(api_key=claude_key)
        elif ai_model == 'deepseek' and deepseek_key:
            openai_client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1"
            )
        
        conversation_history = []
        
        broker_name = broker.get_broker_name()
        max_leverage = broker.get_max_leverage('crypto')
        supports_leverage = broker.supports_crypto_leverage()
        
        return jsonify({
            "success": True,
            "message": f"Initialized with {broker_name}",
            "broker": broker_name,
            "paper_mode": paper_mode,
            "ai_model": ai_model,
            "supports_leverage": supports_leverage,
            "max_crypto_leverage": max_leverage
        })
        
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account info"""
    if not broker:
        return jsonify({"error": "Broker not initialized"}), 400
    
    try:
        account = broker.get_account()
        return jsonify(account)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get positions"""
    if not broker:
        return jsonify({"error": "Broker not initialized"}), 400
    
    try:
        positions = broker.get_positions()
        return jsonify(positions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI trader"""
    global conversation_history
    
    if not broker:
        return jsonify({"error": "Broker not initialized"}), 400
    
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Add broker context to system message
    broker_name = broker.get_broker_name()
    max_leverage = broker.get_max_leverage('crypto')
    supports_leverage = broker.supports_crypto_leverage()
    
    system_message = f"""You are an AI trading assistant using {broker_name} broker.

Broker Capabilities:
- Max Crypto Leverage: {max_leverage}x
- Supports Leverage: {supports_leverage}
- Supports Stocks: {not supports_leverage or broker_name == 'Alpaca'}

When user requests leverage trading:
1. Check if broker supports it
2. Don't exceed max leverage
3. For Alpaca: No leverage on crypto (spot only)
4. For Bybit/Binance: Use leverage parameter in place_crypto_order

Always provide helpful trading advice and execute requested trades."""
    
    try:
        # Build conversation
        if not conversation_history:
            conversation_history.append({"role": "user", "content": system_message})
        
        conversation_history.append({"role": "user", "content": user_message})
        
        # Call AI
        response_text = call_ai_with_tools(conversation_history, max_turns=10)
        
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep conversation history manageable
        if len(conversation_history) > 20:
            conversation_history = [conversation_history[0]] + conversation_history[-19:]
        
        return jsonify({"response": response_text})
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/autotrading/start', methods=['POST'])
def start_autotrading():
    """Start auto-trading"""
    global autotrading_active, autotrading_thread, autotrading_config
    
    if autotrading_active:
        return jsonify({"error": "Auto-trading already active"}), 400
    
    if not broker:
        return jsonify({"error": "Broker not initialized"}), 400
    
    data = request.json
    autotrading_config = data
    
    autotrading_active = True
    autotrading_thread = threading.Thread(target=autotrading_loop, daemon=True)
    autotrading_thread.start()
    
    add_autotrading_log(f"Auto-trading started with {broker.get_broker_name()}", "success")
    
    return jsonify({"success": True, "message": "Auto-trading started"})

@app.route('/api/autotrading/stop', methods=['POST'])
def stop_autotrading():
    """Stop auto-trading"""
    global autotrading_active
    
    if not autotrading_active:
        return jsonify({"error": "Auto-trading not active"}), 400
    
    autotrading_active = False
    add_autotrading_log("Auto-trading stopped", "info")
    
    return jsonify({"success": True, "message": "Auto-trading stopped"})

@app.route('/api/autotrading/status', methods=['GET'])
def autotrading_status():
    """Get auto-trading status"""
    return jsonify({
        "active": autotrading_active,
        "config": autotrading_config
    })

@app.route('/api/autotrading/logs', methods=['GET'])
def autotrading_logs_endpoint():
    """Get auto-trading logs"""
    return jsonify(autotrading_logs)

@app.route('/api/autotrading/logs/clear', methods=['POST'])
def clear_autotrading_logs():
    """Clear auto-trading logs"""
    global autotrading_logs
    autotrading_logs = []
    return jsonify({"success": True})

def autotrading_loop():
    """Auto-trading main loop"""
    global autotrading_active, autotrading_config, conversation_history
    
    add_autotrading_log(f"Auto-trading loop started with {broker.get_broker_name()}")
    
    while autotrading_active:
        try:
            # Get account info
            account = broker.get_account()
            positions = broker.get_positions()
            
            # Build trading context
            context = f"""Current Account:
- Broker: {broker.get_broker_name()}
- Cash: ${account.get('cash', 0):.2f}
- Equity: ${account.get('equity', 0):.2f}
- Positions: {len(positions)}

Analyze market conditions and suggest trading opportunities."""
            
            add_autotrading_log("Analyzing markets...")
            
            # Call AI for trading decisions
            messages = [
                {"role": "user", "content": "You are an automated trading system."},
                {"role": "user", "content": context}
            ]
            
            response = call_ai_with_tools(messages, max_turns=5)
            
            add_autotrading_log(f"AI Response: {response[:200]}...")
            
            # Sleep before next iteration
            interval = autotrading_config.get('interval', 60)
            time.sleep(interval)
            
        except Exception as e:
            add_autotrading_log(f"Auto-trading error: {str(e)}", "error")
            time.sleep(60)
    
    add_autotrading_log("Auto-trading loop ended")

if __name__ == '__main__':
    print("🚀 Multi-Broker Trading Server Starting...")
    print(f"📊 Supported Brokers: {', '.join(get_supported_brokers())}")
    print("🌐 Server running on http://localhost:5002")
    print("📝 Configure broker in frontend Settings page")
    app.run(host='0.0.0.0', port=5002, debug=False)
