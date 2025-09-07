#!/usr/bin/env python3
"""Main entry point for MCP Swagger server."""

import sys
from typing import Any

from api_client import SecurityHandler
from config import Settings, parse_arguments
from fastmcp import FastMCP
from filters import SwaggerFilter
from generators import ToolGenerator
from parsers import SpecLoader
from utils import print_banner, print_server_info, print_summary, setup_logging


class MCPSwaggerServer:
    """Main server class for MCP Swagger integration."""

    def __init__(self, settings: Settings, swagger_spec: dict[str, Any]) -> None:
        """Initialize the MCP Swagger server.

        Args:
            settings: Application settings
            swagger_spec: Loaded Swagger specification

        """
        self.settings = settings
        self.swagger_spec = swagger_spec
        self.mcp = FastMCP(settings.server_name)

        # Initialize components
        self.filter = self._create_filter()
        self.security_handler = SecurityHandler(settings.api_token, swagger_spec)
        self.tool_generator = ToolGenerator(
            swagger_spec=swagger_spec,
            base_url=settings.base_url,
            security_handler=self.security_handler,
            filter_config=self.filter,
            mcp_server=self.mcp,
            timeout=settings.timeout,
        )

    def generate_tools(self) -> int:
        """Generate MCP tools from the Swagger specification.

        Returns:
            Number of tools generated

        """
        return self.tool_generator.generate_all_tools()

    def get_generated_tools(self) -> list:
        """Get list of generated tools."""
        return self.tool_generator.get_generated_tools()

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run(
            transport=self.settings.transport,
            host=self.settings.host,
            port=self.settings.port,
        )

    def _create_filter(self) -> SwaggerFilter:
        """Create filter from settings."""
        return SwaggerFilter(
            methods=self.settings.methods,
            paths=self.settings.paths,
            exclude_paths=self.settings.exclude_paths,
            tags=self.settings.tags,
            exclude_tags=self.settings.exclude_tags,
            operation_ids=self.settings.operation_ids,
            exclude_operation_ids=self.settings.exclude_operation_ids,
        )


def main() -> None:
    """Run the MCP Swagger server."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    setup_logging()

    # Create settings first (with timeout)
    # Note: We'll update settings after loading spec
    Settings.from_args(args, {})

    # Load Swagger specification with timeout
    try:
        swagger_spec = SpecLoader.load(args.swagger_spec, timeout=args.timeout)
    except Exception as e:
        print(f"Error loading Swagger specification: {e}", file=sys.stderr)
        sys.exit(1)

    # Create final settings with loaded spec
    settings = Settings.from_args(args, swagger_spec)

    # Print startup information
    print_banner(settings)

    # Create and configure server
    server = MCPSwaggerServer(settings, swagger_spec)

    # Generate tools
    tool_count = server.generate_tools()

    if tool_count == 0:
        print("No tools were generated based on the filter criteria!", file=sys.stderr)
        sys.exit(1)

    # Print summary
    tools = server.get_generated_tools()
    print_summary(tools)

    # Exit if dry run
    if settings.dry_run:
        print("\nDry run complete. Server not started.", flush=True)
        sys.exit(0)

    # Start server
    print_server_info(settings)
    server.run()


if __name__ == "__main__":
    main()
