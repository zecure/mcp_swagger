"""Swagger specification loader."""

import json
from typing import Any

import httpx

from mcp_swagger.models import SwaggerSpec


class SpecLoader:
    """Loader for Swagger/OpenAPI specifications."""

    @staticmethod
    def load(path_or_url: str, timeout: float = 600.0) -> SwaggerSpec:
        """Load a Swagger specification from a file or URL.

        Args:
            path_or_url: Path to local file or HTTP(S) URL
            timeout: Timeout for HTTP requests in seconds

        Returns:
            Parsed Swagger specification

        Raises:
            Exception: If loading fails

        """
        if path_or_url.startswith(("http://", "https://")):
            raw_spec = SpecLoader._load_from_url(path_or_url, timeout)
        else:
            raw_spec = SpecLoader._load_from_file(path_or_url)

        return SwaggerSpec.from_dict(raw_spec)

    @staticmethod
    def _load_from_url(url: str, timeout: float) -> dict[str, Any]:
        """Load specification from URL."""
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _load_from_file(path: str) -> dict[str, Any]:
        """Load specification from file."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)
