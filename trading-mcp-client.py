#!/usr/bin/env python3
"""
Proper MCP Client for Alpaca Trading
Uses the official mcp SDK to connect to the Alpaca MCP server
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import asyncio
import threading
import time
from datetime import datetime
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state
mcp_session = None
mcp_read = None
mcp_write = None
anthropic_client = None
alpaca_api_key = None
alpaca_secret_key = None
paper_mode = True

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
    if len(autotrading_logs) > 100:
        autotrading_logs = autotrading_logs[-100:]
    logger.info(f"Auto-trading: {message}")

# Background event loop for MCP
mcp_loop = None
mcp_thread = None
mcp_connection_ready = threading.Event()

def start_mcp_loop():
    """Start the event loop in a background thread"""
    global mcp_loop
    mcp_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(mcp_loop)
    mcp_loop.run_forever()

async def connect_to_mcp_server_async():
    """Connect to the official Alpaca MCP server using stdio transport"""
    global mcp_session, mcp_read, mcp_write
    
    try:
        # Configure server parameters
        server_params = StdioServerParameters(
            command="alpaca-mcp-server",
            args=["serve"],
            env={
                "ALPACA_API_KEY": alpaca_api_key,
                "ALPACA_SECRET_KEY": alpaca_secret_key,
                "ALPACA_PAPER_TRADE": "True" if paper_mode else "False"
            }
        )
        
        logger.info(f"Starting Alpaca MCP server with paper_mode={paper_mode}")
        
        # Connect using stdio transport with async context manager
        async with stdio_client(server_params) as (read, write):
            mcp_read = read
            mcp_write = write
            
            logger.info("Stdio connection established, creating session...")
            
            # Create session
            mcp_session = ClientSession(read, write)
            
            logger.info("Session created, initializing...")
            
            # Initialize the session
            await mcp_session.initialize()
            
            logger.info("Successfully connected to Alpaca MCP server")
            mcp_connection_ready.set()
            
            # Keep the connection alive indefinitely
            await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Error in connect_to_mcp_server_async: {e}")
        logger.exception("Full traceback:")
        mcp_connection_ready.set()  # Set anyway to unblock, but connection failed
        raise

def connect_to_mcp_server():
    """Initialize MCP connection in background thread"""
    global mcp_thread, mcp_loop
    
    # Start event loop in background thread if not already running
    if mcp_thread is None or not mcp_thread.is_alive():
        mcp_thread = threading.Thread(target=start_mcp_loop, daemon=True)
        mcp_thread.start()
        time.sleep(0.5)  # Give thread time to start
    
    # Schedule the connection in the background loop
    future = asyncio.run_coroutine_threadsafe(connect_to_mcp_server_async(), mcp_loop)
    
    # Wait for connection to be ready (with timeout)
    if not mcp_connection_ready.wait(timeout=30):
        raise Exception("MCP connection timeout")
    
    logger.info("MCP connection established and ready")
    return True

async def call_mcp_tool_async(tool_name: str, arguments: dict):
    """Call a tool on the MCP server (async)"""
    if not mcp_session:
        raise Exception("MCP session not initialized")
    
    result = await mcp_session.call_tool(tool_name, arguments)
    return result

def call_mcp_tool(tool_name: str, arguments: dict):
    """Call a tool on the MCP server (sync wrapper)"""
    if not mcp_loop:
        raise Exception("MCP loop not started")
    future = asyncio.run_coroutine_threadsafe(call_mcp_tool_async(tool_name, arguments), mcp_loop)
    return future.result(timeout=30)

async def list_mcp_tools_async():
    """List available tools from the MCP server (async)"""
    if not mcp_session:
        raise Exception("MCP session not initialized")
    
    tools = await mcp_session.list_tools()
    return tools

def list_mcp_tools():
    """List available tools from the MCP server (sync wrapper)"""
    if not mcp_loop:
        raise Exception("MCP loop not started")
    future = asyncio.run_coroutine_threadsafe(list_mcp_tools_async(), mcp_loop)
    return future.result(timeout=30)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "implementation": "Official Alpaca MCP Server via mcp SDK",
        "initialized": mcp_session is not None
    })

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize with API keys and connect to MCP server"""
    global alpaca_api_key, alpaca_secret_key, anthropic_client, paper_mode, conversation_history, mcp_connection_ready
    
    data = request.json
    alpaca_api_key = data.get('alpaca_key')
    alpaca_secret_key = data.get('alpaca_secret')
    claude_key = data.get('claude_key')
    paper_mode = data.get('paper_mode', True)
    
    try:
        # Initialize Claude
        anthropic_client = Anthropic(api_key=claude_key)
        
        # Reset connection ready flag
        mcp_connection_ready.clear()
        
        # Connect to MCP server (runs in background thread)
        connect_to_mcp_server()
        
        # Clear conversation history
        conversation_history = []
        
        logger.info(f"Initialized in {'PAPER' if paper_mode else 'LIVE'} mode with official MCP server")
        
        return jsonify({
            "status": "initialized",
            "paper_mode": paper_mode
        })
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        logger.exception("Full traceback:")
        return jsonify({"error": str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    """Get account information via MCP"""
    if not mcp_session:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        result = call_mcp_tool("get_account", {})
        return jsonify(result.content[0].text if result.content else {})
    except Exception as e:
        logger.error(f"Error getting account: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions via MCP"""
    if not mcp_session:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        result = call_mcp_tool("get_all_positions", {})
        
        # Parse the result
        if result.content:
            content = result.content[0].text
            return jsonify(json.loads(content))
        return jsonify([])
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """List available MCP tools"""
    if not mcp_session:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        tools = list_mcp_tools()
        
        # Convert tools to Claude-compatible format
        tool_list = []
        for tool in tools.tools:
            tool_list.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        return jsonify({"tools": tool_list})
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for trading commands using MCP tools"""
    global conversation_history
    
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    if not anthropic_client or not mcp_session:
        return jsonify({"error": "Not initialized"}), 400
    
    try:
        # Get available MCP tools
        mcp_tools = list_mcp_tools()
        
        # Convert to Claude format
        claude_tools = []
        for tool in mcp_tools.tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude with MCP tools
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=claude_tools,
            messages=conversation_history
        )
        
        # Process tool calls
        while response.stop_reason == "tool_use":
            assistant_content = []
            tool_results = []
            
            for block in response.content:
                if hasattr(block, 'text'):
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    
                    # Execute tool via MCP (now synchronous)
                    result = call_mcp_tool(block.name, block.input)
                    
                    # Extract result content
                    result_content = ""
                    if result.content:
                        if isinstance(result.content[0].text, str):
                            result_content = result.content[0].text
                        else:
                            result_content = json.dumps(result.content[0].text)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_content
                    })
            
            conversation_history.append({"role": "assistant", "content": assistant_content})
            conversation_history.append({"role": "user", "content": tool_results})
            
            # Get next response
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                tools=claude_tools,
                messages=conversation_history
            )
        
        # Final text response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text = block.text
        
        conversation_history.append({
            "role": "assistant",
            "content": [{"type": "text", "text": response_text}]
        })
        
        return jsonify({"response": response_text})
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

# Auto-trading endpoints
@app.route('/api/autotrading/start', methods=['POST'])
def start_autotrading():
    """Start auto-trading"""
    global autotrading_active, autotrading_thread, autotrading_config, autotrading_logs
    
    if not anthropic_client or not mcp_session:
        return jsonify({"error": "Clients not initialized"}), 400
    
    if autotrading_active:
        return jsonify({"error": "Auto-trading is already active"}), 400
    
    data = request.json
    autotrading_config = data
    
    autotrading_logs = []
    add_autotrading_log(f"📊 Starting auto-trading with {len(data.get('categories', []))} categories and {len(data.get('keywords', []))} keywords", "success")
    
    autotrading_active = True
    autotrading_thread = threading.Thread(target=autotrading_loop, daemon=True)
    autotrading_thread.start()
    
    return jsonify({"status": "started", "config": autotrading_config})

@app.route('/api/autotrading/stop', methods=['POST'])
def stop_autotrading():
    """Stop auto-trading"""
    global autotrading_active
    
    if not autotrading_active:
        return jsonify({"error": "Auto-trading is not active"}), 400
    
    autotrading_active = False
    add_autotrading_log("🛑 Stop requested by user", "info")
    
    return jsonify({"status": "stopped"})

@app.route('/api/autotrading/status', methods=['GET'])
def autotrading_status():
    """Get auto-trading status"""
    return jsonify({
        "active": autotrading_active,
        "config": autotrading_config if autotrading_active else None
    })

@app.route('/api/autotrading/logs', methods=['GET'])
def autotrading_logs_endpoint():
    """Get recent auto-trading logs"""
    return jsonify({
        "logs": autotrading_logs[-50:]
    })

def autotrading_loop():
    """Background loop for auto-trading using MCP tools"""
    global autotrading_active, autotrading_config
    
    add_autotrading_log("🚀 Auto-trading loop started", "success")
    
    while autotrading_active:
        try:
            if not autotrading_config:
                time.sleep(5)
                continue
            
            add_autotrading_log("🔍 Analyzing market conditions...", "info")
            
            # Get account and positions via MCP (now synchronous)
            account_result = call_mcp_tool("get_account", {})
            positions_result = call_mcp_tool("get_all_positions", {})
            
            # Parse results
            account_info = json.loads(account_result.content[0].text) if account_result.content else {}
            positions_list = json.loads(positions_result.content[0].text) if positions_result.content else []
            
            add_autotrading_log(f"💰 Portfolio: ${account_info.get('portfolio_value', 0):.2f} | Cash: ${account_info.get('cash', 0):.2f} | Positions: {len(positions_list)}", "info")
            
            # Build context
            context = f"""
MARKET FILTER:
{json.dumps({
    "categories": autotrading_config.get("categories", []),
    "keywords": autotrading_config.get("keywords", []),
    "maxTradeAmount": autotrading_config.get("maxTradeAmount", 100)
}, indent=2)}

CURRENT ACCOUNT:
{json.dumps(account_info, indent=2)}

CURRENT POSITIONS:
{json.dumps(positions_list, indent=2)}

Based on the configured strategy, analyze the current portfolio and market conditions, then decide if any trades should be executed.
"""
            
            add_autotrading_log("🤖 Consulting AI for trading decision...", "info")
            
            # Get available MCP tools (now synchronous)
            mcp_tools = list_mcp_tools()
            claude_tools = []
            for tool in mcp_tools.tools:
                claude_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            system_prompt = autotrading_config.get("systemPrompt", "You are an AI trading assistant.")
            strategy_prompt = autotrading_config.get("strategyPrompt", "Execute profitable trades.")
            full_prompt = f"{system_prompt}\n\nSTRATEGY: {strategy_prompt}\n\n{context}"
            
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                tools=claude_tools,
                messages=[{"role": "user", "content": full_prompt}],
                timeout=60.0
            )
            
            add_autotrading_log(f"✅ AI response received (stop_reason: {response.stop_reason})", "info")
            
            # Process tool calls
            if response.stop_reason == "tool_use":
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        
                        add_autotrading_log(f"⚡ AI executing: {tool_name} with {json.dumps(tool_input)}", "trade")
                        
                        try:
                            result = call_mcp_tool(tool_name, tool_input)
                            result_text = result.content[0].text if result.content else "No result"
                            add_autotrading_log(f"✅ Tool result: {result_text[:200]}", "success")
                        except Exception as tool_error:
                            add_autotrading_log(f"❌ Tool error: {str(tool_error)}", "error")
            
            # Extract AI reasoning
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    add_autotrading_log(f"💭 AI says: {content_block.text[:200]}...", "info")
            
            # Wait for next check
            interval = autotrading_config.get("checkInterval", 60)
            add_autotrading_log(f"⏰ Waiting {interval} seconds until next check...", "info")
            time.sleep(interval)
            
        except Exception as e:
            add_autotrading_log(f"❌ Error: {str(e)}", "error")
            logger.exception("Auto-trading error:")
            time.sleep(30)
    
    add_autotrading_log("🛑 Auto-trading loop stopped", "info")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting MCP Client Server (connects to official Alpaca MCP) on port {port}")
    logger.info("This server uses the official Alpaca MCP server via the mcp SDK")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

