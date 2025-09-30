"""Security handler for API authentication."""

from mcp_swagger.models import SwaggerOperation, SwaggerSpec


class SecurityHandler:
    """Handler for API security and authentication."""

    def __init__(self, api_token: str | None, swagger_spec: SwaggerSpec) -> None:
        """Initialize security handler.

        Args:
            api_token: API token for authentication
            swagger_spec: Swagger specification with security definitions

        """
        self.api_token = api_token
        self.spec = swagger_spec

    def get_headers(self, operation: SwaggerOperation) -> dict[str, str]:
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
        # Note: An empty list explicitly means no security is required
        if operation.security is not None:
            security = operation.security
        else:
            security = self.spec.security or []

        for sec_req in security:
            headers.update(self._process_security_requirement(sec_req))

        return headers

    def _process_security_requirement(
        self, sec_req: dict[str, list[str]]
    ) -> dict[str, str]:
        """Process a single security requirement."""
        headers = {}

        # Check for Bearer token auth
        if "Bearer" in sec_req:
            headers["Authorization"] = f"Bearer {self.api_token}"
            return headers

        # Check other security schemes
        for key in sec_req:
            sec_def = self.spec.security_definitions.get(key)
            if not sec_def:
                continue

            if sec_def.type_ == "apiKey" and sec_def.in_ == "header":
                header_name = sec_def.name or "Authorization"

                if header_name == "Authorization":
                    headers[header_name] = f"Bearer {self.api_token}"
                else:
                    headers[header_name] = self.api_token

        return headers
