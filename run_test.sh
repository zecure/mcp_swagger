#!/bin/bash
# Test script to verify SSE fix

echo "Testing SSE transport fix..."
echo "=========================================="
echo ""

# Start test server in background
echo "Starting test server with SSE transport..."
python test_sse_fix.py --transport sse --port 8004 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo ""
echo "Server started with PID: $SERVER_PID"
echo ""

# Kill server on exit
trap "kill $SERVER_PID 2>/dev/null" EXIT

echo "To test the server, connect an MCP client to:"
echo "  Transport: SSE"
echo "  URL: http://localhost:8004/sse"
echo ""
echo "Press Ctrl+C to stop the server"

# Wait for interrupt
wait $SERVER_PID