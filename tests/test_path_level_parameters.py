#!/usr/bin/env python3
"""Test path-level parameter inheritance in Swagger specifications."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path to import from parsers
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP

from mcp_swagger.api_client import SecurityHandler
from mcp_swagger.filters import SwaggerFilter
from mcp_swagger.generators import ToolGenerator


class TestPathLevelParameters:
    """Test suite for path-level parameter handling."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.mcp = FastMCP("test")
        # Include all methods for testing
        self.filter = SwaggerFilter(methods=["get", "post", "put", "patch", "delete"])

    def test_path_level_parameters_inherited(self) -> None:
        """Test that path-level parameters are inherited by operations."""
        # Arrange - spec with path-level parameters
        swagger_spec = {
            "swagger": "2.0",
            "basePath": "/api/v1",
            "paths": {
                "/users/{userId}": {
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "type": "string",
                            "required": True,
                            "description": "User ID",
                        }
                    ],
                    "get": {
                        "operationId": "getUser",
                        "summary": "Get user by ID",
                        "responses": {"200": {"description": "Success"}},
                    },
                    "delete": {
                        "operationId": "deleteUser",
                        "summary": "Delete user by ID",
                        "responses": {"204": {"description": "Deleted"}},
                    },
                }
            },
        }

        security_handler = SecurityHandler(None, swagger_spec)
        generator = ToolGenerator(
            swagger_spec=swagger_spec,
            base_url="https://api.example.com",
            security_handler=security_handler,
            filter_config=self.filter,
            mcp_server=self.mcp,
        )

        # Act
        tool_count = generator.generate_all_tools()
        tools = generator.get_generated_tools()

        # Assert
        expected_tool_count = 2  # GET and DELETE operations
        assert tool_count == expected_tool_count, (
            f"Should generate {expected_tool_count} tools (GET and DELETE)"
        )

        # Both tools should have the path parameter
        for tool in tools:
            assert "userId" in tool.path_params, (
                f"Tool {tool.name} should have userId path param"
            )
            assert tool.path_params["userId"].required is True
            assert tool.path_params["userId"].location == "path"

    def test_operation_parameters_override_path_level(self) -> None:
        """Test that operation-level parameters override path-level ones."""
        # Arrange - spec where operation overrides path-level parameter
        swagger_spec = {
            "swagger": "2.0",
            "basePath": "/api/v1",
            "paths": {
                "/items/{itemId}": {
                    "parameters": [
                        {
                            "name": "itemId",
                            "in": "path",
                            "type": "string",
                            "required": True,
                            "description": "Item ID as string",
                        },
                        {
                            "name": "version",
                            "in": "query",
                            "type": "string",
                            "description": "API version",
                            "default": "v1",
                        },
                    ],
                    "get": {
                        "operationId": "getItem",
                        "summary": "Get item",
                        "parameters": [
                            {
                                "name": "itemId",
                                "in": "path",
                                "type": "integer",  # Override type
                                "required": True,
                                "description": "Item ID as integer",
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    },
                }
            },
        }

        security_handler = SecurityHandler(None, swagger_spec)
        generator = ToolGenerator(
            swagger_spec=swagger_spec,
            base_url="https://api.example.com",
            security_handler=security_handler,
            filter_config=self.filter,
            mcp_server=self.mcp,
        )

        # Act
        generator.generate_all_tools()
        tools = generator.get_generated_tools()

        # Assert
        assert len(tools) == 1
        tool = tools[0]

        # Should have itemId with integer type (overridden)
        assert "itemId" in tool.path_params
        assert tool.path_params["itemId"].param_type == "integer"
        assert tool.path_params["itemId"].description == "Item ID as integer"

        # Should also have version from path level
        assert "version" in tool.query_params
        assert tool.query_params["version"].default == "v1"

    def test_mixed_path_and_operation_parameters(self) -> None:
        """Test mixing path-level and operation-level parameters."""
        # Arrange
        swagger_spec = {
            "swagger": "2.0",
            "basePath": "/api/v1",
            "paths": {
                "/projects/{projectId}/tasks/{taskId}": {
                    "parameters": [
                        {
                            "name": "projectId",
                            "in": "path",
                            "type": "string",
                            "required": True,
                            "description": "Project ID",
                        }
                    ],
                    "get": {
                        "operationId": "getTask",
                        "summary": "Get task",
                        "parameters": [
                            {
                                "name": "taskId",
                                "in": "path",
                                "type": "string",
                                "required": True,
                                "description": "Task ID",
                            },
                            {
                                "name": "include",
                                "in": "query",
                                "type": "string",
                                "description": "Include related data",
                            },
                        ],
                        "responses": {"200": {"description": "Success"}},
                    },
                }
            },
        }

        security_handler = SecurityHandler(None, swagger_spec)
        generator = ToolGenerator(
            swagger_spec=swagger_spec,
            base_url="https://api.example.com",
            security_handler=security_handler,
            filter_config=self.filter,
            mcp_server=self.mcp,
        )

        # Act
        generator.generate_all_tools()
        tools = generator.get_generated_tools()

        # Assert
        assert len(tools) == 1
        tool = tools[0]

        # Should have both path parameters
        expected_param_count = 2  # projectId and taskId
        assert len(tool.path_params) == expected_param_count
        assert "projectId" in tool.path_params
        assert "taskId" in tool.path_params

        # Should have query parameter from operation level
        assert "include" in tool.query_params

    def test_url_substitution_with_path_level_params(self) -> None:
        """Test that URL substitution works correctly with path-level parameters."""
        # Arrange
        swagger_spec = {
            "swagger": "2.0",
            "basePath": "/api/v1",
            "paths": {
                "/orgs/{orgId}/users/{userId}": {
                    "parameters": [
                        {
                            "name": "orgId",
                            "in": "path",
                            "type": "string",
                            "required": True,
                        },
                        {
                            "name": "userId",
                            "in": "path",
                            "type": "string",
                            "required": True,
                        },
                    ],
                    "get": {
                        "operationId": "getOrgUser",
                        "summary": "Get organization user",
                        "responses": {"200": {"description": "Success"}},
                    },
                }
            },
        }

        security_handler = SecurityHandler(None, swagger_spec)
        generator = ToolGenerator(
            swagger_spec=swagger_spec,
            base_url="https://api.example.com",
            security_handler=security_handler,
            filter_config=self.filter,
            mcp_server=self.mcp,
        )

        # Act
        generator.generate_all_tools()
        tools = generator.get_generated_tools()
        tool = tools[0]

        # Test URL building
        test_params = {"orgId": "acme", "userId": "john123"}
        url = generator._build_url(tool.path, tool.path_params, test_params)

        # Assert
        assert "/orgs/acme/users/john123" in url
        assert "{orgId}" not in url
        assert "{userId}" not in url
        assert "%7B" not in url  # No URL-encoded braces


if __name__ == "__main__":
    # Run tests with pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestPathLevelParameters()
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
