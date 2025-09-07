#!/usr/bin/env python3
"""Test if wrapping responses helps with SSE."""

import json
import sys
from typing import Any

from fastmcp import FastMCP

# Create server
mcp = FastMCP("test_wrapper")


@mcp.tool()
def test_wrapped() -> dict[str, Any]:
    """Test tool with explicit dict return."""
    result = {
        "status": "success",
        "data": {"message": "Hello from wrapped test"},
        "metadata": {"timestamp": "2025-09-07"},
    }
    print(
        f"Returning wrapped result: {json.dumps(result)}", file=sys.stderr, flush=True
    )
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport", default="sse", choices=["sse", "streamable-http"]
    )
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()

    print(
        f"Starting server with {args.transport} transport on port {args.port}",
        file=sys.stderr,
        flush=True,
    )
    mcp.run(transport=args.transport, host="127.0.0.1", port=args.port)
