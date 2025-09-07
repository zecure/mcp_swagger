# MCP Swagger Server

Dynamic MCP server generator that creates FastMCP servers from Swagger/OpenAPI specifications with flexible filtering options.

## Features

- **Dynamic Tool Generation**: Automatically generates MCP tools from Swagger/OpenAPI endpoints
- **Flexible Filtering**: Control which endpoints to expose through various filter options
- **Rich Metadata**: Preserves Swagger descriptions, parameters, and schemas in MCP tools
- **Token Authentication**: Built-in support for Bearer token authentication
- **Type Safety**: Automatic parameter validation and type conversion
- **Comprehensive Documentation**: Tools include detailed descriptions and parameter documentation
- **Modular Architecture**: Clean separation of concerns for easy maintenance and extension

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

By default, only GET endpoints are exposed:

```bash
python main.py path/to/swagger.json
```

### With Authentication

```bash
# Via environment variable
export API_TOKEN="your-api-token"
python main.py swagger.json

# Via command line
python main.py swagger.json --api-token "your-api-token"
```

### Custom Base URL

```bash
python main.py swagger.json --base-url "https://api.example.com"
```

## Filtering Options

### HTTP Methods

Control which HTTP methods to expose:

```bash
# Expose GET and POST endpoints
python main.py swagger.json --methods get post

# Expose all methods except DELETE
python main.py swagger.json --methods get post put patch head options
```

### Path Patterns

Include or exclude specific paths (supports wildcards):

```bash
# Include only specific paths
python main.py swagger.json --paths "/documents/*" "/agents/*"

# Exclude admin endpoints
python main.py swagger.json --exclude-paths "/admin/*" "/internal/*"

# Combine include and exclude
python main.py swagger.json \
  --paths "/api/v1/*" \
  --exclude-paths "/api/v1/admin/*"
```

### Swagger Tags

Filter by Swagger tags:

```bash
# Include only specific tags
python main.py swagger.json --tags documents agents

# Exclude certain tags
python main.py swagger.json --exclude-tags internal deprecated
```

### Operation IDs

Filter by specific operation IDs:

```bash
# Include specific operations
python main.py swagger.json \
  --operation-ids get_document create_document list_documents

# Exclude specific operations
python main.py swagger.json \
  --exclude-operation-ids delete_all debug_endpoint
```

## Complex Filtering Examples

### Example 1: Public Read-Only API

Expose only GET endpoints for public-facing resources:

```bash
python main.py swagger.json \
  --methods get \
  --tags public \
  --exclude-paths "/internal/*" "/admin/*"
```

### Example 2: Document Management

Expose full CRUD operations for documents but read-only for everything else:

```bash
python main.py swagger.json \
  --methods get \
  --paths "/documents/*" \
  --methods get post put delete \
  --paths "/agents/*" \
  --methods get
```

### Example 3: Specific Operations Only

Expose only specific, whitelisted operations:

```bash
python main.py swagger.json \
  --operation-ids \
    list_documentation \
    get_documentation \
    search_documents \
    agent_assistance
```

## Server Options

### Transport Protocol

```bash
# Use SSE transport
python main.py swagger.json --transport sse

# Use streamable HTTP (default)
python main.py swagger.json --transport streamable-http
```

### Host and Port

```bash
python main.py swagger.json --host localhost --port 9000
```

### Dry Run

Preview what tools would be generated without starting the server:

```bash
python main.py swagger.json --dry-run --methods get post
```

## Environment Variables

- `API_BASE_URL`: Default base URL for the API
- `API_TOKEN`: API token for authentication

## Docker Support

Build and run with Docker:

```bash
# Build the image
docker build -t mcp-swagger .

# Run with environment variables
docker run -p 8080:8080 \
  -e API_BASE_URL=https://api.example.com \
  -e API_TOKEN=your-token \
  -v $(pwd)/swagger.json:/app/swagger.json \
  mcp-swagger \
  /app/swagger.json --methods get post
```

## Architecture

The server is organized into clean, modular components:

- **`config/`**: CLI argument parsing and application settings
- **`filters/`**: Endpoint filtering logic with flexible pattern matching
- **`models/`**: Data models for parameters and tools
- **`parsers/`**: Swagger specification parsing and schema generation
- **`api_client/`**: HTTP client and security handling
- **`generators/`**: Tool generation from Swagger operations
- **`utils/`**: Logging and output formatting
- **`main.py`**: Main entry point and server orchestration

## How It Works

1. **Specification Loading**: Loads Swagger/OpenAPI spec from file or URL
2. **Filtering**: Applies filters to select which endpoints to expose
3. **Tool Generation**: Creates FastMCP tools with:
   - Comprehensive descriptions from Swagger metadata
   - Parameter validation and type hints
   - Automatic authentication header injection
   - Error handling and response formatting
4. **Server Start**: Launches FastMCP server with generated tools

## Tool Naming

Tools are named using the Swagger `operationId` if available, otherwise a name is generated from the HTTP method and path:

- `get_document` (from operationId)
- `get_documents_doc_id` (generated from GET /documents/{doc_id})

## Parameter Handling

- **Path parameters**: Automatically substituted in URLs
- **Query parameters**: Added as query strings
- **Body parameters**: Sent as JSON request body
- **Headers**: Authentication headers automatically added

## Response Format

Successful responses return the JSON response from the API. Error responses include:

```json
{
  "error": "Error message",
  "status_code": 404,
  "response": "Raw response text"
}
```

## Limitations

- Currently supports Bearer token authentication only
- Request body schema validation is basic
- File uploads not yet supported
- WebSocket endpoints not supported

## Examples with the Provided Swagger

Using the included `documentation_swagger.json`:

```bash
# Expose only document reading operations
python main.py ../documentation_swagger.json \
  --methods get \
  --tags documents

# Expose document and agent operations
python main.py ../documentation_swagger.json \
  --methods get post \
  --tags documents agents \
  --exclude-operation-ids delete_documentation

# Full access except admin operations
python main.py ../documentation_swagger.json \
  --methods get post put delete \
  --exclude-paths "*/admin/*" "*/internal/*"
```
