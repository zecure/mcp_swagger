"""Generator for creating MCP tools from Swagger operations."""

from collections.abc import Callable
from typing import Any, ClassVar

from fastmcp import FastMCP

from mcp_swagger.api_client import HTTPClient, SecurityHandler
from mcp_swagger.filters import SwaggerFilter
from mcp_swagger.models import ParameterInfo, ToolInfo
from mcp_swagger.parsers import ParameterParser, SchemaParser


class ToolGenerator:
    """Generator for creating MCP tools from Swagger specifications."""

    VALID_HTTP_METHODS: ClassVar[set[str]] = {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
    }

    def __init__(
        self,
        swagger_spec: dict[str, Any],
        base_url: str,
        security_handler: SecurityHandler,
        filter_config: SwaggerFilter,
        mcp_server: FastMCP,
        timeout: float = 600.0,
    ) -> None:
        """Initialize the tool generator.

        Args:
            swagger_spec: Swagger/OpenAPI specification
            base_url: Base URL for API requests
            security_handler: Handler for API security
            filter_config: Filter configuration
            mcp_server: FastMCP server instance
            timeout: Timeout for HTTP requests in seconds

        """
        self.spec = swagger_spec
        self.base_url = base_url.rstrip("/")
        self.base_path = self._extract_base_path()
        self.security_handler = security_handler
        self.filter = filter_config
        self.mcp = mcp_server
        self.http_client = HTTPClient(timeout=timeout)
        self.generated_tools: list[ToolInfo] = []

    def generate_all_tools(self) -> int:
        """Generate all MCP tools from the Swagger specification.

        Returns:
            Number of tools generated

        """
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            self._process_path(path, path_item)

        return len(self.generated_tools)

    def get_generated_tools(self) -> list[ToolInfo]:
        """Get list of generated tools."""
        return self.generated_tools

    def _extract_base_path(self) -> str:
        """Extract base path from specification."""
        if "basePath" in self.spec:
            return self.spec["basePath"].rstrip("/")
        return ""

    def _process_path(self, path: str, path_item: dict[str, Any]) -> None:
        """Process a single path and its operations."""
        # Extract path-level parameters if they exist
        path_level_params = path_item.get("parameters", [])

        for method, operation in path_item.items():
            if method not in self.VALID_HTTP_METHODS:
                continue

            if not self.filter.should_include(path, method, operation):
                continue

            # Merge path-level parameters with operation-level parameters
            # Operation-level parameters override path-level ones with the same name
            merged_operation = operation.copy()
            operation_params = operation.get("parameters", [])

            # Create a set of operation parameter names for deduplication
            operation_param_names = {
                (param.get("name"), param.get("in")) for param in operation_params
            }

            # Add path-level parameters that aren't overridden by operation-level ones
            merged_params = operation_params.copy()
            for path_param in path_level_params:
                param_key = (path_param.get("name"), path_param.get("in"))
                if param_key not in operation_param_names:
                    merged_params.append(path_param)

            # Update the operation with merged parameters
            if merged_params:
                merged_operation["parameters"] = merged_params

            self._generate_tool(path, method, merged_operation)

    def _generate_tool(self, path: str, method: str, operation: dict[str, Any]) -> None:
        """Generate a single tool from an operation."""
        # Parse operation details
        tool_info = self._create_tool_info(path, method, operation)

        # Create tool function
        tool_function = self._create_tool_function(tool_info)

        # Register with FastMCP
        self.mcp.tool()(tool_function)

        # Track generated tool
        self.generated_tools.append(tool_info)

    def _create_tool_info(
        self, path: str, method: str, operation: dict[str, Any]
    ) -> ToolInfo:
        """Create tool information from operation."""
        # Parse parameters
        parameters, path_params, query_params, body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Get security headers
        security_headers = self.security_handler.get_headers(operation)

        # Build description
        description = ParameterParser.build_tool_description(operation, method, path)

        # Create tool name
        tool_name = operation.get(
            "operationId", f"{method}_{path.replace('/', '_').strip('_')}"
        )

        return ToolInfo(
            name=tool_name,
            description=description,
            method=method,
            path=path,
            parameters=parameters,
            path_params=path_params,
            query_params=query_params,
            body_schema=body_schema,
            security_headers=security_headers,
        )

    def _create_tool_function(self, tool_info: ToolInfo) -> Callable:
        """Create the actual tool function."""
        # Build Pydantic model for parameters
        params_model = SchemaParser.build_params_model(
            tool_info.parameters, tool_info.body_schema, tool_info.name
        )

        if params_model:
            return self._create_function_with_params(tool_info, params_model)
        else:
            return self._create_function_without_params(tool_info)

    def _create_function_with_params(
        self, tool_info: ToolInfo, params_model: type
    ) -> Callable:
        """Create tool function with parameters."""

        async def api_tool(params: params_model) -> dict[str, Any]:
            """Execute API request with parameters."""
            params_dict = params.model_dump(exclude_none=True)

            # Build URL with path parameters
            url = self._build_url(tool_info.path, tool_info.path_params, params_dict)

            # Build query parameters
            query = self._build_query_params(tool_info.query_params, params_dict)

            # Build request body
            json_body = self._build_request_body(
                tool_info.method,
                params_dict,
                tool_info.path_params,
                tool_info.query_params,
            )

            # Prepare headers
            headers = self._prepare_headers(tool_info.security_headers)

            # Execute request and ensure response is awaited
            result = await self.http_client.execute_request(
                tool_info.method, url, query, json_body, headers
            )

            # Ensure result is properly formatted for SSE transport
            if result is None:
                result = {"status": "success"}
            elif not isinstance(result, dict):
                result = {"data": result}

            return result

        api_tool.__name__ = tool_info.name
        api_tool.__doc__ = tool_info.description
        return api_tool

    def _create_function_without_params(self, tool_info: ToolInfo) -> Callable:
        """Create tool function without parameters."""

        async def api_tool() -> dict[str, Any]:
            """Execute API request without parameters."""
            url = self._get_full_url(tool_info.path)
            headers = self._prepare_headers(tool_info.security_headers)

            # Execute request and ensure response is awaited
            result = await self.http_client.execute_request(
                tool_info.method, url, None, None, headers
            )

            # Ensure result is properly formatted for SSE transport
            if result is None:
                result = {"status": "success"}
            elif not isinstance(result, dict):
                result = {"data": result}

            return result

        api_tool.__name__ = tool_info.name
        api_tool.__doc__ = tool_info.description
        return api_tool

    def _build_url(
        self,
        path: str,
        path_params: dict[str, ParameterInfo],
        params_dict: dict[str, Any],
    ) -> str:
        """Build URL with path parameters substituted."""
        url_path = path

        for param_name, param_info in path_params.items():
            if param_name in params_dict:
                # Replace the path parameter placeholder with the actual value
                placeholder = f"{{{param_name}}}"
                value = str(params_dict[param_name])
                url_path = url_path.replace(placeholder, value)
            elif param_info.required:
                # Path parameters are always required in OpenAPI spec
                # If a required path param is missing, raise an error
                raise ValueError(
                    f"Required path parameter '{param_name}' is missing. "
                    f"Path template: {path}"
                )

        return self._get_full_url(url_path)

    def _build_query_params(
        self, query_params: dict[str, ParameterInfo], params_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Build query parameters dictionary."""
        return {
            param_name: params_dict[param_name]
            for param_name in query_params
            if param_name in params_dict
        }

    def _build_request_body(
        self,
        method: str,
        params_dict: dict[str, Any],
        path_params: dict[str, ParameterInfo],
        query_params: dict[str, ParameterInfo],
    ) -> dict[str, Any] | None:
        """Build request body for POST/PUT/PATCH requests."""
        # Check for explicit body parameter
        if "body" in params_dict:
            return params_dict["body"]

        # For methods that expect a body, collect remaining params
        if method in {"post", "put", "patch"}:
            body_params = {
                k: v
                for k, v in params_dict.items()
                if k not in path_params and k not in query_params and k != "body"
            }
            if body_params:
                return body_params

        return None

    def _prepare_headers(self, security_headers: dict[str, str]) -> dict[str, str]:
        """Prepare request headers."""
        headers = {"Content-Type": "application/json"}
        headers.update(security_headers)
        return headers

    def _get_full_url(self, path: str) -> str:
        """Get the full URL for an endpoint path."""
        clean_path = path.lstrip("/")
        return f"{self.base_url}{self.base_path}/{clean_path}"
