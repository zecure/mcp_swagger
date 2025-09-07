#!/usr/bin/env python3
"""Unit tests for ParameterParser component.

This test suite validates the parsing of Swagger parameter definitions,
including path, query, and body parameters, as well as the generation
of comprehensive tool descriptions.
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import from parsers
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_swagger.parsers.parameter_parser import ParameterParser


class TestParameterParser:
    """Test suite for ParameterParser functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_path_param = {
            "name": "userId",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The user ID",
        }

        self.sample_query_param = {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Maximum number of results",
        }

        self.sample_body_param = {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            },
        }

    def test_parse_path_parameters(self) -> None:
        """Test parsing of path parameters."""
        # Arrange
        operation = {"parameters": [self.sample_path_param]}

        # Act
        parameters, path_params, query_params, body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        assert len(parameters) == 1, "Should parse one parameter"
        assert len(path_params) == 1, "Should have one path parameter"
        assert "userId" in path_params, "Path parameter should be keyed by name"
        assert len(query_params) == 0, "Should have no query parameters"
        assert body_schema is None, "Should have no body schema"

        param_info = path_params["userId"]
        assert param_info.name == "userId"
        assert param_info.location == "path"
        assert param_info.required is True

    def test_parse_query_parameters(self) -> None:
        """Test parsing of query parameters."""
        # Arrange
        operation = {"parameters": [self.sample_query_param]}

        # Act
        parameters, path_params, query_params, _body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        assert len(parameters) == 1, "Should parse one parameter"
        assert len(query_params) == 1, "Should have one query parameter"
        assert "limit" in query_params, "Query parameter should be keyed by name"
        assert len(path_params) == 0, "Should have no path parameters"

        param_info = query_params["limit"]
        assert param_info.name == "limit"
        assert param_info.location == "query"
        assert param_info.required is False
        default_limit = 10
        assert param_info.default == default_limit

    def test_parse_body_parameter(self) -> None:
        """Test parsing of body parameters."""
        # Arrange
        operation = {"parameters": [self.sample_body_param]}

        # Act
        parameters, path_params, query_params, body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        assert len(parameters) == 1, "Should parse one parameter"
        assert body_schema is not None, "Should have body schema"
        assert body_schema["type"] == "object"
        assert "properties" in body_schema
        assert len(path_params) == 0, "Should have no path parameters"
        assert len(query_params) == 0, "Should have no query parameters"

    def test_parse_mixed_parameters(self) -> None:
        """Test parsing of mixed parameter types."""
        # Arrange
        operation = {
            "parameters": [
                self.sample_path_param,
                self.sample_query_param,
                self.sample_body_param,
            ]
        }

        # Act
        parameters, path_params, query_params, body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        expected_param_count = 3
        assert len(parameters) == expected_param_count, "Should parse all parameters"
        assert len(path_params) == 1, "Should have one path parameter"
        assert len(query_params) == 1, "Should have one query parameter"
        assert body_schema is not None, "Should have body schema"
        assert "userId" in path_params
        assert "limit" in query_params

    def test_parse_empty_parameters(self) -> None:
        """Test parsing when no parameters are present."""
        # Arrange
        operation = {}  # No parameters key

        # Act
        parameters, path_params, query_params, body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        assert len(parameters) == 0, "Should have no parameters"
        assert len(path_params) == 0, "Should have no path parameters"
        assert len(query_params) == 0, "Should have no query parameters"
        assert body_schema is None, "Should have no body schema"

    def test_build_basic_tool_description(self) -> None:
        """Test building a basic tool description."""
        # Arrange
        operation = {
            "summary": "Get user details",
            "description": "Retrieves detailed information about a specific user",
        }

        # Act
        description = ParameterParser.build_tool_description(
            operation, "get", "/users/{userId}"
        )

        # Assert
        assert "Get user details" in description
        assert "Retrieves detailed information" in description

    def test_build_description_with_parameters(self) -> None:
        """Test building description with parameter documentation."""
        # Arrange
        operation = {
            "summary": "List users",
            "parameters": [
                {
                    "name": "limit",
                    "in": "query",
                    "type": "integer",
                    "description": "Maximum results",
                    "required": False,
                },
                {
                    "name": "offset",
                    "in": "query",
                    "type": "integer",
                    "description": "Skip results",
                    "required": True,
                },
            ],
        }

        # Act
        description = ParameterParser.build_tool_description(operation, "get", "/users")

        # Assert
        assert "Parameters:" in description
        assert "limit: Maximum results [integer in query] (optional)" in description
        assert "offset: Skip results [integer in query] (required)" in description

    def test_build_description_with_responses(self) -> None:
        """Test building description with response documentation."""
        # Arrange
        operation = {
            "summary": "Create user",
            "responses": {
                "201": {"description": "User successfully created"},
                "400": {"description": "Invalid input"},
            },
        }

        # Act
        description = ParameterParser.build_tool_description(
            operation, "post", "/users"
        )

        # Assert
        assert "Returns: User successfully created" in description
        assert "Invalid input" not in description  # Only success response included

    def test_build_description_with_example(self) -> None:
        """Test building description with example documentation."""
        # Arrange
        example_data = {"name": "John Doe", "age": 30}
        operation = {"summary": "Create user", "x-example": example_data}

        # Act
        description = ParameterParser.build_tool_description(
            operation, "post", "/users"
        )

        # Assert
        assert "Example:" in description
        assert json.dumps(example_data, indent=2) in description

    def test_build_description_fallback(self) -> None:
        """Test description fallback when no metadata is available."""
        # Arrange
        operation = {}  # No summary or description

        # Act
        description = ParameterParser.build_tool_description(
            operation, "delete", "/users/123"
        )

        # Assert
        assert "Execute DELETE request to /users/123" in description

    def test_parameter_with_enum_values(self) -> None:
        """Test parsing parameters with enum constraints."""
        # Arrange
        enum_param = {
            "name": "status",
            "in": "query",
            "type": "string",
            "enum": ["active", "inactive", "pending"],
            "description": "User status filter",
        }
        operation = {"parameters": [enum_param]}

        # Act
        _parameters, _, query_params, _ = ParameterParser.parse_operation_parameters(
            operation
        )

        # Assert
        param_info = query_params["status"]
        assert param_info.enum == ["active", "inactive", "pending"]

    def test_parameter_with_constraints(self) -> None:
        """Test parsing parameters with min/max constraints."""
        # Arrange
        constrained_param = {
            "name": "age",
            "in": "query",
            "type": "integer",
            "minimum": 0,
            "maximum": 150,
            "description": "User age",
        }
        operation = {"parameters": [constrained_param]}

        # Act
        _parameters, _, query_params, _ = ParameterParser.parse_operation_parameters(
            operation
        )

        # Assert
        param_info = query_params["age"]
        assert param_info.minimum == 0
        max_age = 150
        assert param_info.maximum == max_age

    def test_header_parameters_handling(self) -> None:
        """Test that header parameters are parsed correctly."""
        # Arrange
        header_param = {
            "name": "X-API-Key",
            "in": "header",
            "type": "string",
            "required": True,
            "description": "API authentication key",
        }
        operation = {"parameters": [header_param]}

        # Act
        parameters, path_params, query_params, _body_schema = (
            ParameterParser.parse_operation_parameters(operation)
        )

        # Assert
        assert len(parameters) == 1, "Should parse header parameter"
        assert parameters[0].location == "header"
        assert parameters[0].name == "X-API-Key"
        # Header params shouldn't be in path or query dicts
        assert len(path_params) == 0
        assert len(query_params) == 0

    def test_form_data_parameters(self) -> None:
        """Test parsing of form data parameters."""
        # Arrange
        form_param = {
            "name": "file",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "File to upload",
        }
        operation = {"parameters": [form_param]}

        # Act
        parameters, _, _, _ = ParameterParser.parse_operation_parameters(operation)

        # Assert
        assert len(parameters) == 1
        assert parameters[0].location == "formData"
        assert parameters[0].param_type == "file"

    def test_array_type_parameters(self) -> None:
        """Test parsing of array type parameters."""
        # Arrange
        array_param = {
            "name": "tags",
            "in": "query",
            "type": "array",
            "items": {"type": "string"},
            "collectionFormat": "csv",
            "description": "Filter by tags",
        }
        operation = {"parameters": [array_param]}

        # Act
        _parameters, _, query_params, _ = ParameterParser.parse_operation_parameters(
            operation
        )

        # Assert
        param_info = query_params["tags"]
        assert param_info.param_type == "array"
        assert param_info.items_type == "string"  # Changed from items to items_type
        # Note: collection_format is not tracked in current model

    def test_complex_body_schema(self) -> None:
        """Test parsing of complex nested body schemas."""
        # Arrange
        complex_schema = {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "email": {"type": "string", "format": "email"},
                "profile": {
                    "type": "object",
                    "properties": {
                        "bio": {"type": "string"},
                        "avatar": {"type": "string", "format": "uri"},
                    },
                },
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        }
        body_param = {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": complex_schema,
        }
        operation = {"parameters": [body_param]}

        # Act
        _parameters, _, _, body_schema = ParameterParser.parse_operation_parameters(
            operation
        )

        # Assert
        assert body_schema == complex_schema
        assert body_schema["properties"]["profile"]["type"] == "object"
        assert body_schema["required"] == ["name", "email"]

    def test_description_with_all_components(self) -> None:
        """Test building description with all possible components."""
        # Arrange
        operation = {
            "summary": "Update user profile",
            "description": "Updates a user's profile information with validation",
            "parameters": [
                {
                    "name": "userId",
                    "in": "path",
                    "type": "string",
                    "description": "User identifier",
                    "required": True,
                },
                {
                    "name": "validate",
                    "in": "query",
                    "type": "boolean",
                    "description": "Enable validation",
                    "required": False,
                },
            ],
            "responses": {"200": {"description": "Profile updated successfully"}},
            "x-example": {"userId": "user123", "validate": True},
        }

        # Act
        description = ParameterParser.build_tool_description(
            operation, "put", "/users/{userId}/profile"
        )

        # Assert
        assert "Update user profile" in description
        assert "Updates a user's profile information" in description
        assert "Parameters:" in description
        assert "userId: User identifier" in description
        assert "validate: Enable validation" in description
        assert "Returns: Profile updated successfully" in description
        assert "Example:" in description

    def test_missing_parameter_fields(self) -> None:
        """Test handling of parameters with missing optional fields."""
        # Arrange
        minimal_param = {"name": "id", "in": "path"}  # Missing type, description, etc.
        operation = {"parameters": [minimal_param]}

        # Act
        _parameters, path_params, _, _ = ParameterParser.parse_operation_parameters(
            operation
        )

        # Assert
        param_info = path_params["id"]
        assert param_info.name == "id"
        assert param_info.location == "path"
        assert param_info.param_type == "string"  # Default type
        assert param_info.description == "Parameter id"  # Default description format


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestParameterParser()
        test_methods = [m for m in dir(test_suite) if m.startswith("test_")]

        for method_name in test_methods:
            test_suite.setup_method()
            method = getattr(test_suite, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")

        print("\nBasic tests completed!")
