"""Command-line interface configuration."""

import argparse


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate an MCP server from a Swagger/OpenAPI specification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_epilog(),
    )

    _add_required_arguments(parser)
    _add_optional_arguments(parser)
    _add_filtering_options(parser)
    _add_server_options(parser)

    return parser


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = create_argument_parser()
    return parser.parse_args(args)


def _add_required_arguments(parser: argparse.ArgumentParser) -> None:
    """Add required arguments to the parser."""
    parser.add_argument(
        "swagger_spec", help="Path to Swagger/OpenAPI specification file or URL"
    )


def _add_optional_arguments(parser: argparse.ArgumentParser) -> None:
    """Add optional arguments to the parser."""
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for the API (overrides spec, default: from env or http://localhost:8000)",
    )
    parser.add_argument(
        "--api-token",
        default=None,
        help="API token for authentication (default: from env)",
    )
    parser.add_argument(
        "--server-name",
        default="swagger_mcp",
        help="Name for the MCP server (default: swagger_mcp)",
    )
    parser.add_argument(
        "--instructions",
        default=None,
        help="Description of how to interact with this server",
    )


def _add_filtering_options(parser: argparse.ArgumentParser) -> None:
    """Add filtering options to the parser."""
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["get", "post", "put", "patch", "delete", "head", "options"],
        help="HTTP methods to expose (default: get)",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        help="Path patterns to include (supports wildcards with *)",
    )
    parser.add_argument(
        "--exclude-paths",
        nargs="+",
        help="Path patterns to exclude (supports wildcards with *)",
    )
    parser.add_argument("--tags", nargs="+", help="Swagger tags to include")
    parser.add_argument("--exclude-tags", nargs="+", help="Swagger tags to exclude")
    parser.add_argument(
        "--operation-ids", nargs="+", help="Specific operation IDs to include"
    )
    parser.add_argument(
        "--exclude-operation-ids", nargs="+", help="Specific operation IDs to exclude"
    )


def _add_server_options(parser: argparse.ArgumentParser) -> None:
    """Add server options to the parser."""
    parser.add_argument(
        "--host",
        default="0.0.0.0",  # noqa: S104
        help="Host to bind the MCP server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind the MCP server to (default: 8080)",
    )
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse"],
        default="streamable-http",
        help="Transport protocol to use (default: streamable-http)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Timeout for HTTP requests in seconds (default: 600)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what tools would be generated without starting the server",
    )


def _get_epilog() -> str:
    """Get the epilog text for the argument parser."""
    return """
Examples:
  # Expose only GET endpoints (default)
  python main.py swagger.json

  # Expose GET and POST endpoints
  python main.py swagger.json --methods get post

  # Expose only specific paths
  python main.py swagger.json --paths "/documents/*" "/agents/*"

  # Exclude certain paths
  python main.py swagger.json --exclude-paths "/internal/*" "/admin/*"

  # Filter by Swagger tags
  python main.py swagger.json --tags documents agents

  # Filter by operation IDs
  python main.py swagger.json --operation-ids get_document create_document

  # Complex filtering
  python main.py swagger.json \\
    --methods get post \\
    --paths "/api/v1/*" \\
    --exclude-paths "/api/v1/admin/*" \\
    --tags public
    """
