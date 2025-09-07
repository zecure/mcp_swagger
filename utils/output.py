"""Output formatting utilities."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config.settings import Settings


def print_banner(settings: "Settings") -> None:
    """Print startup banner with configuration info.

    Args:
        settings: Application settings

    """
    print(
        f"Loading Swagger specification from {settings.swagger_spec_path}...",
        flush=True,
    )
    print(f"Using base URL: {settings.base_url}", flush=True)

    if settings.api_token:
        print("API token configured for authentication", flush=True)
    else:
        print("No API token configured (requests will be unauthenticated)", flush=True)

    print("\nGenerating MCP tools from Swagger specification...", flush=True)


def print_summary(tools: list[Any]) -> None:
    """Print summary of generated tools.

    Args:
        tools: List of generated tools

    """
    print(f"\nGenerated {len(tools)} MCP tools from Swagger specification:", flush=True)
    print("-" * 60, flush=True)

    for tool in tools:
        print(f"  {tool.display_name}", flush=True)

    print("-" * 60, flush=True)


def print_server_info(settings: "Settings") -> None:
    """Print server startup information.

    Args:
        settings: Application settings

    """
    print(
        f"\nStarting FastMCP {settings.transport} server on {settings.host}:{settings.port}",
        flush=True,
    )
    print(f"Server name: {settings.server_name}", flush=True)
    print("Press Ctrl+C to stop the server", flush=True)
