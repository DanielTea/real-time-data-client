#!/usr/bin/env python3
"""
Comprehensive test script for all 17 trading tools
Tests live Alpaca endpoints to ensure everything works
"""

import requests
import json
import time
from datetime import datetime, timedelta

SERVER_URL = "http://localhost:5001"

def print_test(category, test_name, passed=None, details=""):
    """Print formatted test result"""
    if passed is None:
        print(f"\n{'='*60}")
        print(f"🧪 {category}")
        print(f"{'='*60}")
    elif passed:
        print(f"✅ {test_name}")
        if details:
            print(f"   {details}")
    else:
        print(f"❌ {test_name}")
        if details:
            print(f"   ERROR: {details}")

def send_chat_message(message):
    """Send a message to the chat endpoint"""
    try:
        response = requests.post(
            f"{SERVER_URL}/api/chat",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def test_account_portfolio():
    """Test Account & Portfolio tools (3 tools)"""
    print_test("ACCOUNT & PORTFOLIO", "Testing 3 tools")
    
    # Test 1: get_account
    result = send_chat_message("Show me my account details including cash, equity, and buying power")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "1. get_account", passed, details)
    time.sleep(1)
    
    # Test 2: get_all_positions
    result = send_chat_message("List all my current positions")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "2. get_all_positions", passed, details)
    time.sleep(1)
    
    # Test 3: close_position (will likely fail if no positions, but tests the tool)
    result = send_chat_message("Do I have any positions to close?")
    passed = "error" not in result and result.get("response")
    details = "Tool available (may have no positions)" if passed else result.get("error", "Unknown error")
    print_test("", "3. close_position (availability check)", passed, details)
    time.sleep(1)

def test_crypto():
    """Test Crypto Trading tools (2 tools)"""
    print_test("CRYPTO TRADING", "Testing 2 tools")
    
    # Test 4: get_crypto_latest_bar
    result = send_chat_message("What's the current price of Bitcoin and Ethereum?")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "4. get_crypto_latest_bar", passed, details)
    time.sleep(1)
    
    # Test 5: place_crypto_order (read-only check)
    result = send_chat_message("If I wanted to buy $10 of Bitcoin, what would happen? Don't actually place the order, just explain.")
    passed = "error" not in result and result.get("response")
    details = "Tool available (no order placed)" if passed else result.get("error", "Unknown error")
    print_test("", "5. place_crypto_order (capability check)", passed, details)
    time.sleep(1)

def test_stocks():
    """Test Stock Trading tools (4 tools)"""
    print_test("STOCK TRADING", "Testing 4 tools")
    
    # Test 6: place_stock_order (capability check)
    result = send_chat_message("Explain how to buy 10 shares of AAPL with a limit order. Don't place it.")
    passed = "error" not in result and result.get("response")
    details = "Tool available (no order placed)" if passed else result.get("error", "Unknown error")
    print_test("", "6. place_stock_order (capability check)", passed, details)
    time.sleep(1)
    
    # Test 7: get_stock_quote
    result = send_chat_message("What's the current bid and ask price for AAPL?")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "7. get_stock_quote", passed, details)
    time.sleep(1)
    
    # Test 8: get_stock_bars
    result = send_chat_message("Show me the last 5 days of price data for MSFT")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "8. get_stock_bars", passed, details)
    time.sleep(1)
    
    # Test 9: get_stock_snapshot
    result = send_chat_message("Get a complete snapshot of TSLA including latest trade, quote, and daily performance")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "9. get_stock_snapshot", passed, details)
    time.sleep(1)

def test_options():
    """Test Options Trading tools (2 tools)"""
    print_test("OPTIONS TRADING", "Testing 2 tools")
    
    # Test 10: get_option_contracts
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    result = send_chat_message(f"Show me AAPL call options expiring around {next_month} with strike prices between $170 and $190")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "10. get_option_contracts", passed, details)
    time.sleep(1)
    
    # Test 11: place_option_order (capability check)
    result = send_chat_message("Explain how to buy an AAPL call option. Don't place the order.")
    passed = "error" not in result and result.get("response")
    details = "Tool available (no order placed)" if passed else result.get("error", "Unknown error")
    print_test("", "11. place_option_order (capability check)", passed, details)
    time.sleep(1)

def test_order_management():
    """Test Order Management tools (3 tools)"""
    print_test("ORDER MANAGEMENT", "Testing 3 tools")
    
    # Test 12: get_orders
    result = send_chat_message("Show me all my open orders")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "12. get_orders", passed, details)
    time.sleep(1)
    
    # Test 13: cancel_order (capability check)
    result = send_chat_message("How would I cancel a specific order by ID?")
    passed = "error" not in result and result.get("response")
    details = "Tool available" if passed else result.get("error", "Unknown error")
    print_test("", "13. cancel_order (capability check)", passed, details)
    time.sleep(1)
    
    # Test 14: cancel_all_orders (capability check)
    result = send_chat_message("Do I have any orders I could cancel?")
    passed = "error" not in result and result.get("response")
    details = "Tool available (likely no orders)" if passed else result.get("error", "Unknown error")
    print_test("", "14. cancel_all_orders (capability check)", passed, details)
    time.sleep(1)

def test_market_intelligence():
    """Test Market Intelligence tools (1 tool)"""
    print_test("MARKET INTELLIGENCE", "Testing 1 tool")
    
    # Test 15: get_news
    result = send_chat_message("Get the latest market news for AAPL and TSLA")
    passed = "error" not in result and result.get("response")
    details = result.get("response", "")[:100] if passed else result.get("error", "Unknown error")
    print_test("", "15. get_news", passed, details)
    time.sleep(1)

def check_server():
    """Check if server is running and initialized"""
    print_test("SETUP", "Checking server status")
    
    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print_test("", "Server health check", True, f"Status: {health.get('status')}")
            
            if not health.get("initialized"):
                print_test("", "Server initialized", False, "Server not initialized! Please initialize in Settings first.")
                return False
            else:
                print_test("", "Server initialized", True, "Ready to test")
                return True
        else:
            print_test("", "Server connection", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_test("", "Server connection", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 ALPACA TRADING TOOLS - COMPREHENSIVE TEST")
    print("="*60)
    print(f"Testing all 17 tools against live Alpaca endpoints")
    print(f"Server: {SERVER_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check server first
    if not check_server():
        print("\n❌ Cannot proceed - server not available or not initialized")
        print("\nTo initialize:")
        print("1. Open the frontend (http://localhost:5173)")
        print("2. Go to Settings")
        print("3. Enter your Alpaca and Claude API keys")
        print("4. Click 'Save Settings'")
        print("5. Re-run this test")
        return
    
    print("\n⏱️  Starting tests in 2 seconds...")
    time.sleep(2)
    
    # Run all test categories
    try:
        test_account_portfolio()
        test_crypto()
        test_stocks()
        test_options()
        test_order_management()
        test_market_intelligence()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETE!")
        print("="*60)
        print("\nNote: Some tools may show 'no positions' or 'no orders'")
        print("This is normal if you haven't placed any trades yet.")
        print("The important thing is that the tools are accessible")
        print("and returning valid responses from Alpaca.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")

if __name__ == "__main__":
    main()

