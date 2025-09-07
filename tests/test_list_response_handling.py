#!/usr/bin/env python3
"""Regression tests for list response handling in MCP Swagger.

This test ensures that list responses from APIs are properly wrapped
in a dict to comply with FastMCP's requirements.

Issue: FastMCP's ToolResult expects structured_content to be a dict or None,
but APIs can return lists directly. This caused a ValueError when tools
returned list responses.

Fix: HTTPClient._parse_success_response() now wraps list responses in
a dict with an "items" key.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

# Add parent directory to path to import from api_client
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client.client import HTTPClient


class TestListResponseHandling:
    """Test suite for list response handling."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.client = HTTPClient()
        self.mock_response = Mock(spec=httpx.Response)
        self.mock_response.status_code = 200
        # Constants for test values
        self.TEST_NUMBER_VALUE = 42.5
        self.HTTP_OK = 200

    def test_list_response_wrapped_in_dict(self) -> None:
        """Test that list responses are wrapped in a dict with 'items' key."""
        # Arrange
        list_data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"},
        ]
        self.mock_response.json.return_value = list_data

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "items" in result, "Result should have 'items' key"
        assert result["items"] == list_data, "Original list should be preserved"

    def test_dict_response_not_wrapped(self) -> None:
        """Test that dict responses are returned unchanged."""
        # Arrange
        dict_data = {
            "status": "success",
            "data": [{"id": 1}, {"id": 2}],
            "count": 2,
        }
        self.mock_response.json.return_value = dict_data

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert result == dict_data, "Dict response should be unchanged"
        assert "items" not in result or result == dict_data

    def test_empty_list_wrapped(self) -> None:
        """Test that empty lists are still wrapped."""
        # Arrange
        self.mock_response.json.return_value = []

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "items" in result, "Result should have 'items' key"
        assert result["items"] == [], "Empty list should be preserved"

    def test_complex_list_items_preserved(self) -> None:
        """Test that complex list items are preserved correctly."""
        # Arrange
        complex_list = [
            {
                "id": 3,
                "title": "JWT-Based Authentication and Role Management",
                "slug": "jwt-authentication-role-management",
                "summary": "Explains ZecMF's JWT authentication",
                "tags": ["authentication", "jwt", "security"],
                "nested": {"key": "value", "list": [1, 2, 3]},
            },
            {
                "id": 4,
                "title": "Another Document",
                "data": None,
                "boolean": True,
                "number": self.TEST_NUMBER_VALUE,
            },
        ]
        self.mock_response.json.return_value = complex_list

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "items" in result, "Result should have 'items' key"
        assert result["items"] == complex_list, (
            "Complex list structure should be preserved"
        )
        assert result["items"][0]["nested"]["list"] == [1, 2, 3]
        assert result["items"][1]["number"] == self.TEST_NUMBER_VALUE

    def test_non_json_response_handling(self) -> None:
        """Test that non-JSON responses are handled correctly."""
        # Arrange
        self.mock_response.json.side_effect = json.JSONDecodeError("test", "doc", 0)
        self.mock_response.text = "Plain text response"

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "result" in result, "Non-JSON should have 'result' key"
        assert result["result"] == "Plain text response"
        assert result["status_code"] == self.HTTP_OK

    def test_nested_lists_in_dict_not_affected(self) -> None:
        """Test that lists nested within dicts are not affected."""
        # Arrange
        dict_with_lists = {
            "results": [1, 2, 3],
            "data": {
                "items": ["a", "b", "c"],
                "nested": {"deep": [{"id": 1}]},
            },
        }
        self.mock_response.json.return_value = dict_with_lists

        # Act
        result = self.client._parse_success_response(self.mock_response)

        # Assert
        assert result == dict_with_lists, "Dict with nested lists should be unchanged"
        assert result["data"]["items"] == ["a", "b", "c"]
        assert result["data"]["nested"]["deep"] == [{"id": 1}]

    def test_primitive_list_types(self) -> None:
        """Test that lists of primitives are properly wrapped."""
        # Test string list
        self.mock_response.json.return_value = ["string1", "string2", "string3"]
        result = self.client._parse_success_response(self.mock_response)
        assert result == {"items": ["string1", "string2", "string3"]}

        # Test number list
        self.mock_response.json.return_value = [1, 2, 3, 4, 5]
        result = self.client._parse_success_response(self.mock_response)
        assert result == {"items": [1, 2, 3, 4, 5]}

        # Test boolean list
        self.mock_response.json.return_value = [True, False, True]
        result = self.client._parse_success_response(self.mock_response)
        assert result == {"items": [True, False, True]}

        # Test mixed primitive list
        self.mock_response.json.return_value = [1, "two", True, None]
        result = self.client._parse_success_response(self.mock_response)
        assert result == {"items": [1, "two", True, None]}


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test = TestListResponseHandling()

        # Run each test method
        test_methods = [m for m in dir(test) if m.startswith("test_")]

        for method_name in test_methods:
            test.setup_method()
            method = getattr(test, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")

        print("\nBasic tests completed!")
