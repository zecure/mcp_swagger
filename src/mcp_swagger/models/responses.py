"""API response models."""

from dataclasses import dataclass
from typing import Any


@dataclass
class APIResponse:
    """Base API response model."""

    status: str
    data: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    error: str | None = None

    @classmethod
    def success(
        cls, data: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    ) -> "APIResponse":
        """Create a success response."""
        return cls(status="success", data=data)

    @classmethod
    def create_error(
        cls,
        error: str,
        data: dict[str, Any] | list[Any] | str | int | float | bool | None = None,
    ) -> "APIResponse":
        """Create an error response."""
        return cls(status="error", error=error, data=data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"status": self.status}
        if self.data is not None:
            result["data"] = self.data
        result["error"] = self.error
        return result


@dataclass
class HTTPErrorResponse:
    """HTTP error response model."""

    status_code: int
    error: str
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "status_code": self.status_code,
            "error": self.error,
        }
        if self.details is not None:
            result["details"] = self.details
        return result


@dataclass
class ToolExecutionResponse:
    """Response from tool execution."""

    tool_name: str
    success: bool
    data: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    error: str | None = None
    execution_time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "tool_name": self.tool_name,
            "success": self.success,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.execution_time is not None:
            result["execution_time"] = self.execution_time
        return result
