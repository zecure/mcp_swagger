# SSE Transport Bug in FastMCP 2.12.2

## Issue Description

The SSE transport in FastMCP 2.12.2 has a critical bug that prevents proper message routing. The server creates session IDs with dashes but sends them to clients without dashes, causing session lookup failures.

## Root Cause

1. Server creates session ID: `3fef88bd-9948-4349-b767-e009418bb809`
2. Server sends in SSE endpoint event: `3fef88bd99484349b767e009418bb809` (dashes removed)
3. Client uses the ID without dashes in POST requests
4. Server tries to parse the ID and adds dashes back in wrong positions
5. Session lookup fails with "Could not find session for ID"

## Impact

- SSE transport is completely non-functional
- Tool calls are accepted (202 status) but never executed
- Responses are never sent back through the SSE stream

## Evidence

From server logs:

```
2025-09-07 12:15:16,257 - mcp.server.sse - DEBUG - Created new session with ID: 3fef88bd-9948-4349-b767-e009418bb809
2025-09-07 12:15:16,259 - mcp.server.sse - DEBUG - Sent endpoint event: /messages/?session_id=3fef88bd99484349b767e009418bb809
2025-09-07 12:15:16,265 - mcp.server.sse - DEBUG - Parsed session ID: 1b7fa651-dd6b-48c5-a670-39f082f31bd7
2025-09-07 12:15:16,265 - mcp.server.sse - WARNING - Could not find session for ID: 1b7fa651-dd6b-48c5-a670-39f082f31bd7
```

## Workaround

Unfortunately, this bug is in the FastMCP library itself and cannot be fixed in user code. The options are:

1. **Use streamable-http transport instead of SSE** (Recommended)
   - This transport works correctly
   - Simply set `MCP_TRANSPORT=streamable-http`

2. **Wait for FastMCP to fix the bug**
   - Report the issue to FastMCP maintainers
   - The bug is in the SSE transport session ID handling

3. **Downgrade/upgrade FastMCP**
   - Check if other versions have this bug fixed

## Verification

The streamable-http transport works correctly as shown in the logs:

```
2025-09-07 12:02:00 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest
2025-09-07 12:02:00 - httpx - INFO - HTTP Request: GET https://zecmf-docs-api.zecure.org/api/v1/documents - Status: 200
```

## Recommendation

Use `streamable-http` transport until the SSE bug is fixed in FastMCP.
