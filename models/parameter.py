"""Parameter information model."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ParameterInfo:
    """Information about an API parameter."""

    name: str
    required: bool
    description: str
    param_type: str
    location: str
    enum: list[Any] | None = None
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    items_type: str | None = None  # For array types

    @classmethod
    def from_swagger_param(cls, param: dict[str, Any]) -> "ParameterInfo":
        """Create from Swagger parameter definition."""
        info = cls(
            name=param["name"],
            required=param.get("required", False),
            description=param.get("description", f"Parameter {param['name']}"),
            param_type=param.get("type", "string"),
            location=param.get("in", "query"),
        )

        # Add optional fields
        if "enum" in param:
            info.enum = param["enum"]
        if "default" in param:
            info.default = param["default"]
        if "minimum" in param:
            info.minimum = param["minimum"]
        if "maximum" in param:
            info.maximum = param["maximum"]
        if "pattern" in param:
            info.pattern = param["pattern"]

        # Handle array types
        if info.param_type == "array":
            items = param.get("items", {})
            info.items_type = items.get("type", "string")

        return info
