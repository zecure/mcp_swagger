"""Parser for Swagger parameter definitions."""

import json
from typing import Any

from mcp_swagger.models.parameter import ParameterInfo


class ParameterParser:
    """Parser for Swagger parameter definitions."""

    @staticmethod
    def parse_operation_parameters(
        operation: dict[str, Any],
    ) -> tuple[
        list[ParameterInfo],
        dict[str, ParameterInfo],
        dict[str, ParameterInfo],
        dict[str, Any] | None,
    ]:
        """Parse and categorize parameters from an operation.

        Returns:
            Tuple of (all_parameters, path_params, query_params, body_schema)

        """
        parameters = []
        path_params = {}
        query_params = {}
        body_schema = None

        for param in operation.get("parameters", []):
            param_info = ParameterInfo.from_swagger_param(param)
            parameters.append(param_info)

            if param_info.location == "path":
                path_params[param_info.name] = param_info
            elif param_info.location == "query":
                query_params[param_info.name] = param_info
            elif param_info.location == "body":
                body_schema = param.get("schema", {})

        return parameters, path_params, query_params, body_schema

    @staticmethod
    def build_tool_description(
        operation: dict[str, Any], method: str, path: str
    ) -> str:
        """Build a comprehensive tool description from operation metadata."""
        summary = operation.get("summary", "")
        description = operation.get("description", "")

        # Combine summary and description
        if summary and description:
            full_desc = f"{summary}\n\n{description}"
        elif summary:
            full_desc = summary
        elif description:
            full_desc = description
        else:
            full_desc = f"Execute {method.upper()} request to {path}"

        # Add parameter documentation
        full_desc = ParameterParser._add_parameter_docs(full_desc, operation)

        # Add response documentation
        full_desc = ParameterParser._add_response_docs(full_desc, operation)

        # Add example if available
        full_desc = ParameterParser._add_example_docs(full_desc, operation)

        return full_desc

    @staticmethod
    def _add_parameter_docs(description: str, operation: dict[str, Any]) -> str:
        """Add parameter documentation to description."""
        params = operation.get("parameters", [])
        if not params:
            return description

        param_docs = []
        for param in params:
            param_desc = param.get("description", "")
            param_type = param.get("type", "string")
            param_in = param.get("in", "query")
            required = " (required)" if param.get("required") else " (optional)"

            param_doc = f"- {param['name']}: {param_desc} [{param_type} in {param_in}]{required}"
            param_docs.append(param_doc)

        if param_docs:
            description += "\n\nParameters:\n" + "\n".join(param_docs)

        return description

    @staticmethod
    def _add_response_docs(description: str, operation: dict[str, Any]) -> str:
        """Add response documentation to description."""
        http_ok = "200"
        http_created = "201"

        responses = operation.get("responses", {})
        success_response = responses.get(http_ok) or responses.get(http_created)

        if success_response:
            response_desc = success_response.get("description", "")
            if response_desc:
                description += f"\n\nReturns: {response_desc}"

        return description

    @staticmethod
    def _add_example_docs(description: str, operation: dict[str, Any]) -> str:
        """Add example documentation to description."""
        if "x-example" in operation:
            description += (
                f"\n\nExample: {json.dumps(operation['x-example'], indent=2)}"
            )

        return description
