"""Parser for creating Pydantic schemas from Swagger definitions."""

from typing import Any, ClassVar

from pydantic import Field, create_model

from mcp_swagger.models.parameter import ParameterInfo


class SchemaParser:
    """Parser for creating Pydantic schemas from Swagger definitions."""

    TYPE_MAPPING: ClassVar[dict[str, type]] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    @classmethod
    def build_params_model(
        cls,
        parameters: list[ParameterInfo],
        body_schema: dict[str, Any] | None,
        operation_id: str,
    ) -> type | None:
        """Build a Pydantic model for API parameters.

        Args:
            parameters: List of parameter information
            body_schema: Body schema if present
            operation_id: Operation ID for model naming

        Returns:
            Pydantic model class or None if no parameters

        """
        field_definitions = {}

        # Add field definitions for each parameter
        for param_info in parameters:
            field_def = cls._create_field_definition(param_info)
            if field_def:
                field_definitions[param_info.name] = field_def

        # Add body parameter if present
        if body_schema:
            field_definitions["body"] = cls._create_body_field()

        # Create model if there are fields
        if field_definitions:
            model_name = f"{operation_id}Params"
            return create_model(model_name, **field_definitions)

        return None

    @classmethod
    def _create_field_definition(
        cls, param_info: ParameterInfo
    ) -> tuple[type, Any] | None:
        """Create a Pydantic field definition from parameter info."""
        # Skip body parameters (handled separately)
        if param_info.location == "body":
            return None

        # Get Python type
        py_type = cls.TYPE_MAPPING.get(param_info.param_type, Any)

        # Create field kwargs
        field_kwargs = {"description": param_info.description}

        # Add validation constraints
        if param_info.enum:
            field_kwargs["json_schema_extra"] = {"enum": param_info.enum}
        if param_info.minimum is not None:
            field_kwargs["ge"] = param_info.minimum
        if param_info.maximum is not None:
            field_kwargs["le"] = param_info.maximum

        # Handle required vs optional
        if param_info.required:
            return py_type, Field(**field_kwargs)
        else:
            return py_type | None, Field(default=param_info.default, **field_kwargs)

    @classmethod
    def _create_body_field(cls) -> tuple[type, Any]:
        """Create a field definition for request body."""
        return dict | None, Field(default=None, description="Request body")
