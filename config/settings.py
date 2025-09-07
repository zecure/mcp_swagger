"""Application settings and configuration."""

import argparse
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class Settings:
    """Application settings container."""

    swagger_spec_path: str
    base_url: str
    api_token: str | None
    server_name: str

    # Filtering options
    methods: list[str] | None
    paths: list[str] | None
    exclude_paths: list[str] | None
    tags: list[str] | None
    exclude_tags: list[str] | None
    operation_ids: list[str] | None
    exclude_operation_ids: list[str] | None

    # Server options
    host: str
    port: int
    transport: str
    timeout: float
    dry_run: bool

    @classmethod
    def from_args(
        cls, args: argparse.Namespace, swagger_spec: dict[str, Any]
    ) -> "Settings":
        """Create settings from command-line arguments and Swagger spec."""
        return cls(
            swagger_spec_path=args.swagger_spec,
            base_url=_determine_base_url(args, swagger_spec),
            api_token=_get_api_token(args),
            server_name=args.server_name,
            methods=args.methods,
            paths=args.paths,
            exclude_paths=args.exclude_paths,
            tags=args.tags,
            exclude_tags=args.exclude_tags,
            operation_ids=args.operation_ids,
            exclude_operation_ids=args.exclude_operation_ids,
            host=args.host,
            port=args.port,
            transport=args.transport,
            timeout=args.timeout,
            dry_run=args.dry_run,
        )


def _determine_base_url(args: argparse.Namespace, swagger_spec: dict[str, Any]) -> str:
    """Determine the base URL for the API."""
    if args.base_url:
        return args.base_url

    # Try environment variable
    base_url = os.getenv("API_BASE_URL")
    if base_url:
        return base_url

    # Try to extract from spec
    if "schemes" in swagger_spec and "host" in swagger_spec:
        scheme = swagger_spec["schemes"][0] if swagger_spec["schemes"] else "http"
        return f"{scheme}://{swagger_spec['host']}"

    return "http://localhost:8000"


def _get_api_token(args: argparse.Namespace) -> str | None:
    """Get API token from arguments or environment."""
    return args.api_token or os.getenv("API_TOKEN")
