"""Parser for Swagger parameter definitions."""

from typing import Any

from mcp_swagger.models import ParameterInfo, SwaggerOperation


class ParameterParser:
    """Parser for Swagger parameter definitions."""

    @staticmethod
    def parse_operation_parameters(
        operation: SwaggerOperation,
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

        for swagger_param in operation.parameters:
            # Convert SwaggerParameter to ParameterInfo
            param_info = ParameterInfo(
                name=swagger_param.name,
                required=swagger_param.required,
                description=swagger_param.description
                or f"Parameter {swagger_param.name}",
                param_type=swagger_param.type_ or "string",
                location=swagger_param.in_,
                enum=swagger_param.enum,
                default=swagger_param.default,
                minimum=swagger_param.minimum,
                maximum=swagger_param.maximum,
                pattern=swagger_param.pattern,
                items_type=swagger_param.items.get("type")
                if swagger_param.items
                else None,
            )
            parameters.append(param_info)

            if param_info.location == "path":
                path_params[param_info.name] = param_info
            elif param_info.location == "query":
                query_params[param_info.name] = param_info
            elif param_info.location == "body":
                body_schema = swagger_param.schema or {}

        return parameters, path_params, query_params, body_schema

    @staticmethod
    def build_tool_description(
        operation: SwaggerOperation, method: str, path: str
    ) -> str:
        """Build a comprehensive tool description from operation metadata."""
        summary = operation.summary or ""
        description = operation.description or ""

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

        return full_desc

    @staticmethod
    def _add_parameter_docs(description: str, operation: SwaggerOperation) -> str:
        """Add parameter documentation to description."""
        params = operation.parameters
        if not params:
            return description

        param_docs = []
        for param in params:
            param_desc = param.description or ""
            param_type = param.type_ or "string"
            param_in = param.in_
            required = " (required)" if param.required else " (optional)"

            param_doc = (
                f"- {param.name}: {param_desc} [{param_type} in {param_in}]{required}"
            )
            param_docs.append(param_doc)

        if param_docs:
            description += "\n\nParameters:\n" + "\n".join(param_docs)

        return description

    @staticmethod
    def _add_response_docs(description: str, operation: SwaggerOperation) -> str:
        """Add response documentation to description."""
        http_ok = "200"
        http_created = "201"

        responses = operation.responses
        success_response = responses.get(http_ok) or responses.get(http_created)

        if success_response:
            response_desc = success_response.description
            if response_desc:
                description += f"\n\nReturns: {response_desc}"

        return description
