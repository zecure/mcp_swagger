"""HTTP client for making API requests."""

import json
import logging
from typing import Any

import httpx


class HTTPClient:
    """HTTP client for executing API requests."""

    SUCCESS_STATUS_MIN = 200
    SUCCESS_STATUS_MAX = 300

    def __init__(self, timeout: float = 600.0) -> None:
        """Initialize HTTP client.

        Args:
            timeout: Timeout for HTTP requests in seconds

        """
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout

    async def execute_request(
        self,
        method: str,
        url: str,
        query: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request and handle the response.

        Args:
            method: HTTP method
            url: Request URL
            query: Query parameters
            json_body: JSON request body
            headers: Request headers

        Returns:
            Response data as dictionary

        """
        headers = headers or {}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=query if query else None,
                    json=json_body,
                    headers=headers,
                )

                self._log_request(method, url, response.status_code)

                # Ensure we always return a proper dict for SSE transport
                result = self._process_response(response)

                # Ensure the result is serializable and properly formatted
                if not isinstance(result, dict):
                    result = {"data": result}

                return result

        except Exception as e:
            self.logger.exception(f"Failed to execute API request to {url}")
            return {"error": f"Failed to execute API request: {e!s}"}

    def _log_request(self, method: str, url: str, status_code: int) -> None:
        """Log request information."""
        self.logger.info(f"API request: {method.upper()} {url} - Status: {status_code}")

    def _process_response(self, response: httpx.Response) -> dict[str, Any]:
        """Process HTTP response."""
        if self._is_success_status(response.status_code):
            return self._parse_success_response(response)
        else:
            return self._create_error_response(response)

    def _is_success_status(self, status_code: int) -> bool:
        """Check if status code indicates success."""
        return self.SUCCESS_STATUS_MIN <= status_code < self.SUCCESS_STATUS_MAX

    def _parse_success_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse successful response."""
        try:
            json_data = response.json()
            # FastMCP requires structured_content to be a dict or None
            # Wrap list responses in a dict
            if isinstance(json_data, list):
                return {"items": json_data}
            else:
                return json_data
        except json.JSONDecodeError:
            return {
                "result": response.text,
                "status_code": response.status_code,
            }

    def _create_error_response(self, response: httpx.Response) -> dict[str, Any]:
        """Create error response dictionary."""
        return {
            "error": f"API request failed with status {response.status_code}",
            "status_code": response.status_code,
            "response": response.text,
        }
