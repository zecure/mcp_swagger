#!/usr/bin/env python3
"""Verify that streamable-http transport works correctly."""

import asyncio
import json
import httpx
import sys

async def test_streamable_http():
    """Test streamable-http transport."""
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Initialize connection
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test_client", "version": "1.0.0"}
            },
            "id": 1
        }
        
        print("Sending initialize request...")
        response = await client.post(f"{base_url}/mcp", json=init_msg)
        print(f"Initialize response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        return False

if __name__ == "__main__":
    success = asyncio.run(test_streamable_http())
    sys.exit(0 if success else 1)