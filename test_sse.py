#!/usr/bin/env python3
"""Test SSE transport issue."""

from fastmcp import FastMCP

# Create a simple test server
mcp = FastMCP("test_server")


@mcp.tool()
def test_tool() -> dict:
    """Test tool that returns a simple response."""
    return {"message": "Hello from test tool", "status": "success"}


# Check if tools are registered
tools = mcp._tool_manager._tools
print(f"Registered tools: {list(tools.keys())}")


# Check what happens when we call a tool
def test_call() -> None:
    """Test calling the tool function."""
    result = test_tool()
    print(f"Tool result type: {type(result)}")
    print(f"Tool result: {result}")


if __name__ == "__main__":
    test_call()
