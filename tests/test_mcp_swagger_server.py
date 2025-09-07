#!/usr/bin/env python3
"""Integration tests for MCPSwaggerServer.

This test suite validates the end-to-end functionality of the MCP Swagger
server, including initialization, tool generation, and server configuration.
These tests follow ZecMF patterns for integration testing.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add parent directory to path to import main module
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_swagger.config import Settings
from mcp_swagger.main import MCPSwaggerServer


class TestMCPSwaggerServer:
    """Integration test suite for MCPSwaggerServer."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "host": "api.example.com",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "List all users",
                        "tags": ["users"],
                        "parameters": [
                            {"name": "limit", "in": "query", "type": "integer"}
                        ],
                        "responses": {"200": {"description": "Success"}},
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create a user",
                        "tags": ["users"],
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                },
                            }
                        ],
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/users/{userId}": {
                    "get": {
                        "operationId": "getUser",
                        "summary": "Get user by ID",
                        "tags": ["users"],
                        "parameters": [
                            {
                                "name": "userId",
                                "in": "path",
                                "type": "string",
                                "required": True,
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    },
                    "delete": {
                        "operationId": "deleteUser",
                        "summary": "Delete user",
                        "tags": ["admin"],
                        "parameters": [
                            {
                                "name": "userId",
                                "in": "path",
                                "type": "string",
                                "required": True,
                            }
                        ],
                        "responses": {"204": {"description": "Deleted"}},
                    },
                },
            },
            "securityDefinitions": {
                "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
            },
        }

        self.test_settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token="test_token",
            server_name="test-mcp-server",
            instructions=None,
            methods=["get", "post"],
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )

    def test_server_initialization(self) -> None:
        """Test MCPSwaggerServer initialization."""
        # Act
        server = MCPSwaggerServer(self.test_settings, self.sample_spec)

        # Assert
        assert server.settings == self.test_settings
        assert server.swagger_spec == self.sample_spec
        assert server.filter is not None
        assert server.security_handler is not None
        assert server.tool_generator is not None
        assert server.mcp is not None

    def test_generate_tools_basic(self) -> None:
        """Test basic tool generation."""
        # Arrange
        server = MCPSwaggerServer(self.test_settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        expected_tool_count = 3  # GET /users, POST /users, GET /users/{userId}
        assert tool_count == expected_tool_count
        tools = server.get_generated_tools()
        assert len(tools) == expected_tool_count

        # Verify tool names
        tool_names = [tool.name for tool in tools]
        assert "listUsers" in tool_names
        assert "createUser" in tool_names
        assert "getUser" in tool_names
        assert "deleteUser" not in tool_names  # DELETE method not included

    def test_generate_tools_with_method_filter(self) -> None:
        """Test tool generation with method filtering."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get"],  # Only GET methods
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        expected_tool_count = 2  # Only GET operations
        assert tool_count == expected_tool_count
        tools = server.get_generated_tools()
        tool_names = [tool.name for tool in tools]
        assert "listUsers" in tool_names
        assert "getUser" in tool_names
        assert "createUser" not in tool_names  # POST excluded

    def test_generate_tools_with_tag_filter(self) -> None:
        """Test tool generation with tag filtering."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get", "post", "delete"],
            paths=None,
            exclude_paths=None,
            tags=["admin"],  # Only admin tag
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        assert tool_count == 1  # Only deleteUser has admin tag
        tools = server.get_generated_tools()
        assert tools[0].name == "deleteUser"

    def test_generate_tools_with_path_filter(self) -> None:
        """Test tool generation with path filtering."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get", "post", "delete"],
            paths=["/users/{userId}"],  # Only user detail endpoints
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        expected_tool_count = 2  # GET and DELETE for /users/{userId}
        assert tool_count == expected_tool_count
        tools = server.get_generated_tools()
        tool_names = [tool.name for tool in tools]
        assert "getUser" in tool_names
        assert "deleteUser" in tool_names
        assert "listUsers" not in tool_names

    def test_generate_tools_with_exclude_operation_ids(self) -> None:
        """Test tool generation with excluded operation IDs."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get", "post"],
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=["createUser"],  # Exclude createUser
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        expected_tool_count = 2  # All except createUser
        assert tool_count == expected_tool_count
        tools = server.get_generated_tools()
        tool_names = [tool.name for tool in tools]
        assert "listUsers" in tool_names
        assert "getUser" in tool_names
        assert "createUser" not in tool_names

    def test_generate_no_tools(self) -> None:
        """Test when no tools match the filter criteria."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["patch"],  # No PATCH methods in spec
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        assert tool_count == 0
        tools = server.get_generated_tools()
        assert len(tools) == 0

    def test_server_with_security(self) -> None:
        """Test server initialization with security configuration."""
        # Arrange
        settings_with_token = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token="secret_token_123",
            server_name="secure-server",
            instructions=None,
            methods=["get"],
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )

        # Act
        server = MCPSwaggerServer(settings_with_token, self.sample_spec)

        # Assert
        assert server.security_handler.api_token == "secret_token_123"
        assert "Bearer" in server.security_handler.security_definitions

    def test_server_run_method(self) -> None:
        """Test server run method calls FastMCP correctly."""
        # Arrange
        server = MCPSwaggerServer(self.test_settings, self.sample_spec)
        mock_mcp = Mock()
        server.mcp = mock_mcp

        # Act
        server.run()

        # Assert
        mock_mcp.run.assert_called_once_with(
            transport="stdio", host="localhost", port=8080
        )

    def test_create_filter_from_settings(self) -> None:
        """Test filter creation from settings."""
        # Arrange
        complex_settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get", "post"],
            paths=["/api/*"],
            exclude_paths=["/internal/*"],
            tags=["public"],
            exclude_tags=["deprecated"],
            operation_ids=["op1", "op2"],
            exclude_operation_ids=["op3"],
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )

        # Act
        server = MCPSwaggerServer(complex_settings, self.sample_spec)
        filter_config = server.filter

        # Assert
        assert "get" in filter_config.methods
        assert "post" in filter_config.methods
        assert len(filter_config.path_patterns) == 1
        assert len(filter_config.exclude_patterns) == 1
        assert "public" in filter_config.tags
        assert "deprecated" in filter_config.exclude_tags
        assert "op1" in filter_config.operation_ids
        assert "op3" in filter_config.exclude_operation_ids

    def test_base_path_extraction(self) -> None:
        """Test that base path is correctly extracted from spec."""
        # Arrange
        spec_with_base = {**self.sample_spec, "basePath": "/api/v2"}
        server = MCPSwaggerServer(self.test_settings, spec_with_base)

        # Act
        server.generate_tools()

        # Assert
        assert server.tool_generator.base_path == "/api/v2"

    def test_server_with_empty_spec(self) -> None:
        """Test server with empty specification."""
        # Arrange
        empty_spec = {"swagger": "2.0", "paths": {}}

        # Act
        server = MCPSwaggerServer(self.test_settings, empty_spec)
        tool_count = server.generate_tools()

        # Assert
        assert tool_count == 0
        assert len(server.get_generated_tools()) == 0

    def test_complex_filtering_combination(self) -> None:
        """Test complex combination of multiple filters."""
        # Arrange
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.example.com",
            api_token=None,
            server_name="test-server",
            instructions=None,
            methods=["get", "post", "delete"],  # Allow multiple methods
            paths=["/users", "/users/*"],  # Specific paths
            exclude_paths=None,
            tags=["users"],  # Must have users tag
            exclude_tags=["admin"],  # But not admin tag
            operation_ids=None,
            exclude_operation_ids=None,
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )
        server = MCPSwaggerServer(settings, self.sample_spec)

        # Act
        tool_count = server.generate_tools()

        # Assert
        # Should include: listUsers, createUser, getUser
        # Should exclude: deleteUser (has admin tag)
        expected_tool_count = 3
        assert tool_count == expected_tool_count
        tools = server.get_generated_tools()
        tool_names = [tool.name for tool in tools]
        assert "listUsers" in tool_names
        assert "createUser" in tool_names
        assert "getUser" in tool_names
        assert "deleteUser" not in tool_names

    def test_tool_metadata_preservation(self) -> None:
        """Test that tool metadata is correctly preserved."""
        # Arrange
        server = MCPSwaggerServer(self.test_settings, self.sample_spec)

        # Act
        server.generate_tools()
        tools = server.get_generated_tools()

        # Assert
        # Find the listUsers tool
        list_users = next(t for t in tools if t.name == "listUsers")
        assert list_users.method == "get"
        assert list_users.path == "/users"
        assert "List all users" in list_users.description
        assert "limit" in list_users.query_params

        # Find the getUser tool
        get_user = next(t for t in tools if t.name == "getUser")
        assert get_user.method == "get"
        assert get_user.path == "/users/{userId}"
        assert "userId" in get_user.path_params


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestMCPSwaggerServer()
        test_methods = [m for m in dir(test_suite) if m.startswith("test_")]

        for method_name in test_methods:
            test_suite.setup_method()
            method = getattr(test_suite, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except (AssertionError, StopIteration) as e:
                print(f"✗ {method_name}: {e}")

        print("\nBasic tests completed!")
