#!/usr/bin/env python3
"""Unit tests for ToolGenerator component.

This test suite validates the generation of MCP tools from Swagger operations,
including URL building, parameter handling, and integration with FastMCP.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add parent directory to path to import from generators
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_swagger.generators.tool_generator import ToolGenerator
from mcp_swagger.models import ParameterInfo, ToolInfo
from mcp_swagger.models.swagger import SwaggerOperation, SwaggerSpec


class TestToolGenerator:
    """Test suite for ToolGenerator functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_spec = SwaggerSpec.from_dict(
            {
                "swagger": "2.0",
                "host": "api.example.com",
                "basePath": "/v1",
                "schemes": ["https"],
                "paths": {
                    "/users": {
                        "get": {
                            "operationId": "listUsers",
                            "summary": "List all users",
                            "parameters": [
                                {
                                    "name": "limit",
                                    "in": "query",
                                    "type": "integer",
                                    "required": False,
                                }
                            ],
                        },
                        "post": {
                            "operationId": "createUser",
                            "summary": "Create a new user",
                            "parameters": [
                                {
                                    "name": "body",
                                    "in": "body",
                                    "required": True,
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                    },
                                }
                            ],
                        },
                    },
                    "/users/{userId}": {
                        "get": {
                            "operationId": "getUser",
                            "summary": "Get user by ID",
                            "parameters": [
                                {
                                    "name": "userId",
                                    "in": "path",
                                    "type": "string",
                                    "required": True,
                                }
                            ],
                        },
                    },
                },
            }
        )

        # Mock dependencies
        self.mock_security_handler = Mock()
        self.mock_security_handler.get_headers.return_value = {}

        self.mock_filter = Mock()
        self.mock_filter.should_include.return_value = True

        self.mock_mcp = Mock()
        self.mock_mcp.tool.return_value = lambda f: f

        self.mock_http_client = AsyncMock()

    def test_initialization(self) -> None:
        """Test ToolGenerator initialization."""
        # Act
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Assert
        assert generator.spec == self.sample_spec
        assert generator.base_url == "https://api.example.com"
        assert generator.base_path == "/v1"
        assert generator.security_handler == self.mock_security_handler
        assert generator.filter == self.mock_filter
        assert generator.mcp == self.mock_mcp
        assert len(generator.generated_tools) == 0

    def test_extract_base_path(self) -> None:
        """Test extraction of base path from specification."""
        # Test with basePath
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )
        assert generator.base_path == "/v1"

        # Test without basePath
        spec_no_base = SwaggerSpec.from_dict({"swagger": "2.0", "paths": {}})
        generator = ToolGenerator(
            swagger_spec=spec_no_base,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )
        assert not generator.base_path  # Empty string check

    def test_generate_all_tools(self) -> None:
        """Test generation of all tools from specification."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Act
        count = generator.generate_all_tools()

        # Assert
        expected_tool_count = 3  # Three operations in sample spec
        assert count == expected_tool_count
        assert len(generator.generated_tools) == expected_tool_count
        assert self.mock_mcp.tool.call_count == expected_tool_count

    def test_filter_excludes_operations(self) -> None:
        """Test that filtered operations are not generated."""
        # Arrange
        self.mock_filter.should_include.side_effect = [
            True,  # Include first operation
            False,  # Exclude second operation
            True,  # Include third operation
        ]

        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Act
        count = generator.generate_all_tools()

        # Assert
        expected_tool_count = 2  # Only two operations included
        assert count == expected_tool_count
        assert len(generator.generated_tools) == expected_tool_count

    def test_skip_invalid_http_methods(self) -> None:
        """Test that invalid HTTP methods are skipped."""
        # Arrange
        spec_with_invalid = SwaggerSpec.from_dict(
            {
                "paths": {
                    "/test": {
                        "get": {"operationId": "valid"},
                        "parameters": {},  # Not a valid HTTP method
                        "x-custom": {},  # Custom extension
                    }
                }
            }
        )

        generator = ToolGenerator(
            swagger_spec=spec_with_invalid,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Act
        count = generator.generate_all_tools()

        # Assert
        assert count == 1  # Only the GET method is valid

    def test_create_tool_info(self) -> None:
        """Test creation of ToolInfo from operation."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        operation = self.sample_spec.paths["/users"].get

        # Act
        tool_info = generator._create_tool_info("/users", "get", operation)

        # Assert
        assert isinstance(tool_info, ToolInfo)
        assert tool_info.name == "listUsers"
        assert tool_info.method == "get"
        assert tool_info.path == "/users"
        assert "List all users" in tool_info.description
        assert len(tool_info.query_params) == 1
        assert "limit" in tool_info.query_params

    def test_create_tool_info_without_operation_id(self) -> None:
        """Test tool name generation when operationId is missing."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        operation = SwaggerOperation.from_dict(
            {"summary": "Test operation"}
        )  # No operationId

        # Act
        tool_info = generator._create_tool_info("/users/profile", "put", operation)

        # Assert
        assert tool_info.name == "put_users_profile"

    def test_build_url_with_path_params(self) -> None:
        """Test URL building with path parameter substitution."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        path_params = {
            "userId": ParameterInfo(
                name="userId",
                required=True,
                description="User ID",
                param_type="string",
                location="path",
            ),
            "postId": ParameterInfo(
                name="postId",
                required=True,
                description="Post ID",
                param_type="string",
                location="path",
            ),
        }
        params_dict = {"userId": "123", "postId": "456"}

        # Act
        url = generator._build_url(
            "/users/{userId}/posts/{postId}", path_params, params_dict
        )

        # Assert
        assert url == "https://api.example.com/v1/users/123/posts/456"

    def test_build_url_missing_required_path_param(self) -> None:
        """Test that missing required path parameters raise an error."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        path_params = {
            "service_id": ParameterInfo(
                name="service_id",
                required=True,
                description="Service ID",
                param_type="integer",
                location="path",
            ),
        }
        params_dict = {}  # Missing required service_id

        # Act & Assert
        with pytest.raises(
            ValueError,
            match=r"Required path parameter 'service_id' is missing.*Path template: /specs/\{service_id\}/stats",
        ):
            generator._build_url("/specs/{service_id}/stats", path_params, params_dict)

    def test_build_query_params(self) -> None:
        """Test building query parameters dictionary."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        query_params = {
            "limit": ParameterInfo(
                name="limit",
                required=False,
                description="Limit",
                param_type="integer",
                location="query",
            ),
            "offset": ParameterInfo(
                name="offset",
                required=False,
                description="Offset",
                param_type="integer",
                location="query",
            ),
            "filter": ParameterInfo(
                name="filter",
                required=False,
                description="Filter",
                param_type="string",
                location="query",
            ),
        }
        params_dict = {"limit": 10, "offset": 20, "other": "ignored"}

        # Act
        query = generator._build_query_params(query_params, params_dict)

        # Assert
        assert query == {"limit": 10, "offset": 20}
        assert "filter" not in query  # Not in params_dict
        assert "other" not in query  # Not a query param

    def test_build_request_body_explicit(self) -> None:
        """Test building request body with explicit body parameter."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        params_dict = {"body": {"name": "John", "email": "john@example.com"}}

        # Act
        body = generator._build_request_body("post", params_dict, {}, {})

        # Assert
        assert body == {"name": "John", "email": "john@example.com"}

    def test_build_request_body_implicit(self) -> None:
        """Test building request body from non-path/query parameters."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        path_params = {
            "userId": ParameterInfo(
                name="userId",
                required=True,
                description="User ID",
                param_type="string",
                location="path",
            )
        }
        query_params = {
            "limit": ParameterInfo(
                name="limit",
                required=False,
                description="Limit",
                param_type="integer",
                location="query",
            )
        }
        params_dict = {
            "userId": "123",
            "limit": 10,
            "name": "John",
            "email": "john@example.com",
        }

        # Act
        body = generator._build_request_body(
            "post", params_dict, path_params, query_params
        )

        # Assert
        assert body == {"name": "John", "email": "john@example.com"}

    def test_build_request_body_for_get(self) -> None:
        """Test that GET requests don't include body even with extra params."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        params_dict = {"extra": "value"}

        # Act
        body = generator._build_request_body("get", params_dict, {}, {})

        # Assert
        assert body is None

    def test_prepare_headers(self) -> None:
        """Test preparation of request headers."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        security_headers = {"Authorization": "Bearer token123"}

        # Act
        headers = generator._prepare_headers(security_headers)

        # Assert
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer token123"

    def test_get_full_url(self) -> None:
        """Test construction of full URLs."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Act & Assert
        assert generator._get_full_url("/users") == "https://api.example.com/v1/users"
        assert generator._get_full_url("users") == "https://api.example.com/v1/users"
        assert (
            generator._get_full_url("/users/123")
            == "https://api.example.com/v1/users/123"
        )

    @pytest.mark.asyncio
    async def test_create_function_with_params(self) -> None:
        """Test creation of tool function with parameters."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )
        generator.http_client = self.mock_http_client
        self.mock_http_client.execute_request.return_value = {"result": "success"}

        tool_info = ToolInfo(
            name="getUser",
            description="Get user by ID",
            method="get",
            path="/users/{userId}",
            path_params={
                "userId": ParameterInfo(
                    name="userId",
                    required=True,
                    description="User ID",
                    param_type="string",
                    location="path",
                )
            },
        )

        # Mock the params model
        with patch(
            "mcp_swagger.generators.tool_generator.SchemaParser.build_params_model"
        ) as mock_build:
            mock_model = MagicMock()
            mock_model.__name__ = "TestParams"
            mock_build.return_value = mock_model

            # Act
            func = generator._create_tool_function(tool_info)

            # Assert
            assert callable(func)
            assert func.__name__ == "getUser"
            assert func.__doc__ == "Get user by ID"

    @pytest.mark.asyncio
    async def test_create_function_without_params(self) -> None:
        """Test creation of tool function without parameters."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )
        generator.http_client = self.mock_http_client
        self.mock_http_client.execute_request.return_value = {"result": "success"}

        tool_info = ToolInfo(
            name="healthCheck",
            description="Check API health",
            method="get",
            path="/health",
        )

        # Mock the params model to return None (no params)
        with patch(
            "mcp_swagger.generators.tool_generator.SchemaParser.build_params_model"
        ) as mock_build:
            mock_build.return_value = None

            # Act
            func = generator._create_tool_function(tool_info)

            # Assert
            assert callable(func)
            assert func.__name__ == "healthCheck"

            # Test execution
            result = await func()
            expected_result = {"status": "success", "data": {"result": "success"}}
            assert result["status"] == expected_result["status"]
            assert result["data"] == expected_result["data"]
            assert "error" in result  # error method should be present but not called
            self.mock_http_client.execute_request.assert_called_once()

    def test_get_generated_tools(self) -> None:
        """Test retrieval of generated tools list."""
        # Arrange
        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Add some tools
        tool1 = ToolInfo("tool1", "desc1", "get", "/path1")
        tool2 = ToolInfo("tool2", "desc2", "post", "/path2")
        generator.generated_tools = [tool1, tool2]

        # Act
        tools = generator.get_generated_tools()

        # Assert
        expected_tool_count = 2
        assert len(tools) == expected_tool_count
        assert tools[0].name == "tool1"
        assert tools[1].name == "tool2"

    def test_valid_http_methods(self) -> None:
        """Test the set of valid HTTP methods."""
        # Assert
        assert "get" in ToolGenerator.VALID_HTTP_METHODS
        assert "post" in ToolGenerator.VALID_HTTP_METHODS
        assert "put" in ToolGenerator.VALID_HTTP_METHODS
        assert "patch" in ToolGenerator.VALID_HTTP_METHODS
        assert "delete" in ToolGenerator.VALID_HTTP_METHODS
        assert "head" in ToolGenerator.VALID_HTTP_METHODS
        assert "options" in ToolGenerator.VALID_HTTP_METHODS
        expected_method_count = 7
        assert len(ToolGenerator.VALID_HTTP_METHODS) == expected_method_count

    def test_process_path_with_security(self) -> None:
        """Test that security headers are properly retrieved for operations."""
        # Arrange
        self.mock_security_handler.get_headers.return_value = {
            "Authorization": "Bearer secret"
        }

        generator = ToolGenerator(
            swagger_spec=self.sample_spec,
            base_url="https://api.example.com",
            security_handler=self.mock_security_handler,
            filter_config=self.mock_filter,
            mcp_server=self.mock_mcp,
        )

        # Act
        generator.generate_all_tools()

        # Assert
        # Security handler should be called for each operation
        expected_call_count = 3
        assert self.mock_security_handler.get_headers.call_count == expected_call_count

        # Check that generated tools have security headers
        for tool in generator.generated_tools:
            assert tool.security_headers == {"Authorization": "Bearer secret"}


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v", "-s"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestToolGenerator()
        test_methods = [
            m
            for m in dir(test_suite)
            if m.startswith("test_") and not m.startswith("test_create_function")
        ]

        for method_name in test_methods:
            test_suite.setup_method()
            method = getattr(test_suite, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")

        print("\nBasic tests completed (async tests skipped)!")
