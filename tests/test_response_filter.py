#!/usr/bin/env python3
"""Unit tests for response filtering functionality."""

from mcp_swagger.utils.response_filter import filter_response_attributes


class TestResponseFilter:
    """Test suite for response filtering functionality."""

    def test_filter_simple_attribute(self) -> None:
        """Test filtering a simple attribute."""
        # Arrange
        data = {"name": "John", "email": "john@example.com", "password": "secret"}
        exclude_attributes = ["password"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {"name": "John", "email": "john@example.com"}
        assert result == expected

    def test_filter_nested_attribute(self) -> None:
        """Test filtering a nested attribute using dot-notation."""
        # Arrange
        data = {
            "user": {"name": "John", "email": "john@example.com", "secret": "hidden"},
            "metadata": {"version": "1.0"},
        }
        exclude_attributes = ["user.secret"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {
            "user": {"name": "John", "email": "john@example.com"},
            "metadata": {"version": "1.0"},
        }
        assert result == expected

    def test_filter_multiple_attributes(self) -> None:
        """Test filtering multiple attributes."""
        # Arrange
        data = {
            "user": {"name": "John", "email": "john@example.com", "password": "secret"},
            "api_key": "secret_key",
            "data": {"value": 42},
        }
        exclude_attributes = ["user.password", "api_key"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {
            "user": {"name": "John", "email": "john@example.com"},
            "data": {"value": 42},
        }
        assert result == expected

    def test_filter_array_items(self) -> None:
        """Test filtering attributes in array items."""
        # Arrange
        data = {
            "users": [
                {"name": "John", "email": "john@example.com", "password": "secret1"},
                {"name": "Jane", "email": "jane@example.com", "password": "secret2"},
            ]
        }
        exclude_attributes = ["users.password"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {
            "users": [
                {"name": "John", "email": "john@example.com"},
                {"name": "Jane", "email": "jane@example.com"},
            ]
        }
        assert result == expected

    def test_filter_nonexistent_attribute(self) -> None:
        """Test filtering a nonexistent attribute doesn't cause errors."""
        # Arrange
        data = {"name": "John", "email": "john@example.com"}
        exclude_attributes = ["password", "user.secret"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {"name": "John", "email": "john@example.com"}
        assert result == expected

    def test_filter_empty_exclude_list(self) -> None:
        """Test with empty exclude list."""
        # Arrange
        data = {"name": "John", "email": "john@example.com", "password": "secret"}
        exclude_attributes = []

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        assert result == data

    def test_filter_none_exclude_list(self) -> None:
        """Test with None exclude list."""
        # Arrange
        data = {"name": "John", "email": "john@example.com", "password": "secret"}
        exclude_attributes = None

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        assert result == data

    def test_filter_preserves_original_data(self) -> None:
        """Test that filtering doesn't modify the original data."""
        # Arrange
        original_data = {"name": "John", "password": "secret"}
        exclude_attributes = ["password"]

        # Act
        result = filter_response_attributes(original_data, exclude_attributes)

        # Assert
        assert original_data == {"name": "John", "password": "secret"}  # Unchanged
        assert result == {"name": "John"}

    def test_filter_deeply_nested_attribute(self) -> None:
        """Test filtering deeply nested attributes."""
        # Arrange
        data = {
            "level1": {
                "level2": {
                    "level3": {"public": "visible", "private": "hidden"},
                    "other": "data",
                }
            }
        }
        exclude_attributes = ["level1.level2.level3.private"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {
            "level1": {"level2": {"level3": {"public": "visible"}, "other": "data"}}
        }
        assert result == expected

    def test_filter_with_mixed_data_types(self) -> None:
        """Test filtering with mixed data types."""
        # Arrange
        data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value", "secret": "hidden"},
        }
        exclude_attributes = ["object.secret"]

        # Act
        result = filter_response_attributes(data, exclude_attributes)

        # Assert
        expected = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }
        assert result == expected
