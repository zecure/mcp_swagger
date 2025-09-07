"""Security handler for API authentication."""

from typing import Any


class SecurityHandler:
    """Handler for API security and authentication."""

    def __init__(self, api_token: str | None, swagger_spec: dict[str, Any]) -> None:
        """Initialize security handler.

        Args:
            api_token: API token for authentication
            swagger_spec: Swagger specification with security definitions

        """
        self.api_token = api_token
        self.spec = swagger_spec
        self.security_definitions = swagger_spec.get("securityDefinitions", {})

    def get_headers(self, operation: dict[str, Any]) -> dict[str, str]:
        """Get security headers for an operation.

        Args:
            operation: Operation definition from Swagger spec

        Returns:
            Dictionary of security headers

        """
        if not self.api_token:
            return {}

        headers = {}

        # Get security requirements (operation-level or global)
        security = operation.get("security", self.spec.get("security", []))

        for sec_req in security:
            headers.update(self._process_security_requirement(sec_req))

        return headers

    def _process_security_requirement(self, sec_req: dict[str, Any]) -> dict[str, str]:
        """Process a single security requirement."""
        headers = {}

        # Check for Bearer token auth
        if "Bearer" in sec_req:
            headers["Authorization"] = f"Bearer {self.api_token}"
            return headers

        # Check other security schemes
        for key in sec_req:
            sec_def = self.security_definitions.get(key, {})

            if sec_def.get("type") == "apiKey" and sec_def.get("in") == "header":
                header_name = sec_def.get("name", "Authorization")

                if header_name == "Authorization":
                    headers[header_name] = f"Bearer {self.api_token}"
                else:
                    headers[header_name] = self.api_token

        return headers
