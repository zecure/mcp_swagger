#!/usr/bin/env python3
"""Test SSE fix by creating a simple mock API server and MCP wrapper."""

import asyncio
import sys

from fastmcp import FastMCP

# Create test server
mcp = FastMCP("test_sse_fix")


# Simulate what our generated tools do
@mcp.tool()
async def test_api_call() -> dict:
    """Simulate an API call like our generated tools."""
    # Simulate HTTP request
    await asyncio.sleep(0.1)  # Simulate network delay

    # Return a properly formatted dict response
    result = {
        "status": "success",
        "data": {"message": "API call successful", "timestamp": "2025-09-07T12:00:00Z"},
    }

    print(f"Tool returning: {result}", file=sys.stderr, flush=True)
    return result


@mcp.tool()
async def test_list_response() -> dict:
    """Test list response wrapping."""
    # Simulate a list response from API
    await asyncio.sleep(0.1)

    # Wrap list in dict as our fix does
    list_data = ["item1", "item2", "item3"]
    result = {"items": list_data}

    print(f"Tool returning wrapped list: {result}", file=sys.stderr, flush=True)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport", default="sse", choices=["sse", "streamable-http"]
    )
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()

    print(
        f"\nTesting SSE fix with {args.transport} transport on port {args.port}",
        file=sys.stderr,
        flush=True,
    )
    print("Tools registered:", file=sys.stderr, flush=True)
    print("  - test_api_call", file=sys.stderr, flush=True)
    print("  - test_list_response", file=sys.stderr, flush=True)
    print("\nStarting server...\n", file=sys.stderr, flush=True)

    mcp.run(transport=args.transport, host="127.0.0.1", port=args.port)
