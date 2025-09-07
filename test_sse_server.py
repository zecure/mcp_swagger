#!/usr/bin/env python3
"""Minimal test server to reproduce SSE issue."""

import asyncio
import sys

from fastmcp import FastMCP

# Create server
mcp = FastMCP("test_sse_server")


@mcp.tool()
def simple_test() -> dict:
    """Test tool that returns immediately."""
    print("Tool called: simple_test", file=sys.stderr, flush=True)
    result = {"message": "Test successful", "timestamp": "2025-09-07"}
    print(f"Returning: {result}", file=sys.stderr, flush=True)
    return result


@mcp.tool()
async def delayed_test() -> dict:
    """Test tool with a small delay."""
    print("Tool called: delayed_test", file=sys.stderr, flush=True)
    await asyncio.sleep(0.5)
    result = {"message": "Delayed test complete"}
    print(f"Returning: {result}", file=sys.stderr, flush=True)
    return result


if __name__ == "__main__":
    # Run with SSE transport
    print("Starting test server with SSE transport", file=sys.stderr, flush=True)
    mcp.run(transport="sse", host="127.0.0.1", port=8001)
