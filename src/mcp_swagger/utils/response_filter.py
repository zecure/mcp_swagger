"""Response filtering utilities for excluding attributes using dot-notation."""

from typing import Any


def filter_response_attributes(
    data: dict[str, Any], exclude_attributes: list[str] | None
) -> dict[str, Any]:
    """Filter response data by excluding specified attributes using dot-notation.

    Args:
        data: Response data dictionary
        exclude_attributes: List of attribute paths to exclude using dot-notation

    Returns:
        Filtered response data with specified attributes removed

    """
    if not exclude_attributes or not isinstance(data, dict):
        return data

    # Create a deep copy to avoid modifying the original data
    filtered_data = _deep_copy_dict(data)

    for attribute_path in exclude_attributes:
        _remove_attribute_path(filtered_data, attribute_path)

    return filtered_data


def _deep_copy_dict(
    obj: dict[str, Any] | list[Any] | str | int | float | bool | None,
) -> dict[str, Any] | list[Any] | str | int | float | bool | None:
    """Create a deep copy of a dictionary or list structure.

    Args:
        obj: Object to copy

    Returns:
        Deep copy of the object

    """
    if isinstance(obj, dict):
        return {key: _deep_copy_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_deep_copy_dict(item) for item in obj]
    else:
        return obj


def _remove_attribute_path(data: dict[str, Any], path: str) -> None:
    """Remove an attribute path from nested dictionary structure.

    Args:
        data: Dictionary to modify
        path: Dot-notation path to remove (e.g., "user.email", "data.password")

    """
    if not path or not isinstance(data, dict):
        return

    parts = path.split(".")

    # Handle single-level path
    if len(parts) == 1:
        data.pop(parts[0], None)
        return

    # Handle nested path
    current = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return

        # If we encounter a list, apply filtering to each item
        if isinstance(current[part], list):
            remaining_path = ".".join(parts[parts.index(part) + 1 :])
            for item in current[part]:
                if isinstance(item, dict):
                    _remove_attribute_path(item, remaining_path)
            return

        current = current[part]

    # Remove the final attribute
    if isinstance(current, dict):
        current.pop(parts[-1], None)
