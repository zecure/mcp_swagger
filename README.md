# MCP Swagger Server

Generate MCP (Model Context Protocol) servers from Swagger/OpenAPI specifications with flexible filtering.

## Features

- **Dynamic Tool Generation**: Automatically creates MCP tools from OpenAPI endpoints
- **Flexible Filtering**: Control exposed endpoints via HTTP methods, paths, tags, and operation IDs
- **Authentication**: Built-in Bearer token support
- **Type Safety**: Automatic parameter validation and conversion
- **FastMCP Integration**: Built on the FastMCP framework for reliable MCP server implementation

## Installation

```bash
# Install from source
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Quick Start

```bash
# Basic usage (exposes GET endpoints by default)
mcp-swagger path/to/swagger.json

# With authentication
mcp-swagger swagger.json --api-token "your-token"

# Custom base URL
mcp-swagger swagger.json --base-url "https://api.example.com"
```

## Filtering Options

Control which endpoints are exposed:

- **HTTP Methods**: `--methods get post put delete`
- **Path Patterns**: `--paths "/api/*" --exclude-paths "/admin/*"`
- **Tags**: `--tags public documents --exclude-tags internal`
- **Operation IDs**: `--operation-ids list_docs get_doc --exclude-operation-ids delete_all`

## Examples

```bash
# Public read-only API
mcp-swagger api.json --methods get --tags public --exclude-paths "/admin/*"

# Specific operations only
mcp-swagger api.json --operation-ids list_docs get_doc search_docs

# Preview generated tools without starting server
mcp-swagger api.json --dry-run --methods get post
```

## Configuration

### Command Line Options

- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 8080)
- `--transport`: Transport protocol: `sse` or `streamable-http` (default)
- `--timeout`: Request timeout in seconds (default: 30)
- `--dry-run`: Preview tools without starting server

### Environment Variables

- `API_BASE_URL`: Default base URL for the API
- `API_TOKEN`: API token for authentication

## Docker

```bash
# Build image
docker build -t mcp-swagger .

# Run with configuration
docker run -p 8080:8080 \
  -e API_BASE_URL=https://api.example.com \
  -e API_TOKEN=your-token \
  -v $(pwd)/swagger.json:/app/swagger.json \
  mcp-swagger /app/swagger.json --methods get post
```

## Architecture

- **`config/`**: CLI parsing and settings
- **`filters/`**: Endpoint filtering logic
- **`generators/`**: MCP tool generation
- **`parsers/`**: OpenAPI spec parsing
- **`api_client/`**: HTTP client and auth
- **`models/`**: Data models
- **`utils/`**: Utilities and logging

## How It Works

1. Load OpenAPI/Swagger specification (file or URL)
2. Apply filters to select endpoints
3. Generate FastMCP tools with parameter validation and auth
4. Start MCP server with generated tools
