#!/usr/bin/env bash
# Quick tool verification script
# Run this anytime to verify all tools are working

echo "🔍 Quick Tool Verification"
echo "=========================="
echo ""

# Check server
echo "1. Checking server..."
SERVER_STATUS=$(curl -s http://localhost:5001/api/health | python -m json.tool 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ Server running"
    
    # Check if initialized
    if echo "$SERVER_STATUS" | grep -q '"initialized": true'; then
        echo "   ✅ Server initialized"
        
        # Run comprehensive test
        echo ""
        echo "2. Running comprehensive test..."
        echo "   (This will test all 15 tools via AI)"
        echo ""
        source .venv/bin/activate && python test-all-tools.py
        
    else
        echo "   ❌ Server not initialized"
        echo ""
        echo "To initialize:"
        echo "  1. Open http://localhost:5173"
        echo "  2. Go to Settings"
        echo "  3. Enter API keys"
        echo "  4. Save"
    fi
else
    echo "   ❌ Server not running"
    echo ""
    echo "To start server:"
    echo "  bash start-all.sh"
fi

echo ""
echo "📊 See TEST-RESULTS.md for detailed test report"

