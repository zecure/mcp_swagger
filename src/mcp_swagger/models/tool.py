"""Tool information model."""

from dataclasses import dataclass, field
from typing import Any

from .parameter import ParameterInfo


@dataclass
class ToolInfo:
    """Information about a generated tool."""

    name: str
    description: str
    method: str
    path: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    path_params: dict[str, ParameterInfo] = field(default_factory=dict)
    query_params: dict[str, ParameterInfo] = field(default_factory=dict)
    body_schema: dict[str, Any] | None = None
    security_headers: dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Get display name for the tool."""
        return f"{self.method.upper()} {self.path} -> {self.name}"
