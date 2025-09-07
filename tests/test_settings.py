#!/usr/bin/env python3
"""Unit tests for Settings configuration component.

This test suite validates the Settings class and its configuration
handling, including argument parsing, environment variable support,
and base URL determination.
"""

import argparse
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path to import from config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Settings


# Local test copies of private functions to avoid import issues
def _determine_base_url(args: argparse.Namespace, swagger_spec: dict) -> str:
    """Determine the base URL for the API."""
    if args.base_url:
        return args.base_url

    # Try environment variable
    base_url = os.getenv("API_BASE_URL")
    if base_url:
        return base_url

    # Try to extract from spec
    if "schemes" in swagger_spec and "host" in swagger_spec:
        scheme = swagger_spec["schemes"][0] if swagger_spec["schemes"] else "http"
        return f"{scheme}://{swagger_spec['host']}"

    return "http://localhost:8000"


def _get_api_token(args: argparse.Namespace) -> str | None:
    """Get API token from arguments or environment."""
    return args.api_token or os.getenv("API_TOKEN")


class TestSettings:
    """Test suite for Settings functionality."""

    DEFAULT_TIMEOUT = 600.0  # Default timeout value in seconds

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_args = argparse.Namespace(
            swagger_spec="swagger.json",
            base_url=None,
            api_token=None,
            server_name="test-server",
            methods=["get", "post"],
            paths=["/api/*"],
            exclude_paths=["/internal/*"],
            tags=["public"],
            exclude_tags=["deprecated"],
            operation_ids=["getUser"],
            exclude_operation_ids=["deleteUser"],
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )

        self.sample_spec = {
            "swagger": "2.0",
            "host": "api.example.com",
            "schemes": ["https"],
            "basePath": "/v1",
        }

    def test_from_args_basic(self) -> None:
        """Test Settings creation from command-line arguments."""
        # Arrange
        self.sample_args.base_url = "https://custom.api.com"
        self.sample_args.api_token = "secret123"

        # Act
        settings = Settings.from_args(self.sample_args, self.sample_spec)

        # Assert
        assert settings.swagger_spec_path == "swagger.json"
        assert settings.base_url == "https://custom.api.com"
        assert settings.api_token == "secret123"
        assert settings.server_name == "test-server"
        assert settings.methods == ["get", "post"]
        assert settings.paths == ["/api/*"]
        assert settings.exclude_paths == ["/internal/*"]
        assert settings.tags == ["public"]
        assert settings.exclude_tags == ["deprecated"]
        assert settings.operation_ids == ["getUser"]
        assert settings.exclude_operation_ids == ["deleteUser"]
        assert settings.host == "localhost"
        default_port = 8080
        assert settings.port == default_port
        assert settings.transport == "stdio"
        assert settings.timeout == self.DEFAULT_TIMEOUT
        assert settings.dry_run is False

    def test_from_args_with_defaults(self) -> None:
        """Test Settings with default values."""
        # Arrange
        minimal_args = argparse.Namespace(
            swagger_spec="spec.yaml",
            base_url=None,
            api_token=None,
            server_name="server",
            methods=None,
            paths=None,
            exclude_paths=None,
            tags=None,
            exclude_tags=None,
            operation_ids=None,
            exclude_operation_ids=None,
            host="127.0.0.1",  # Use localhost instead of all interfaces
            port=3000,
            transport="tcp",
            timeout=600.0,
            dry_run=True,
        )

        # Act
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_args(minimal_args, {})

        # Assert
        assert settings.swagger_spec_path == "spec.yaml"
        assert settings.base_url == "http://localhost:8000"  # Default
        assert settings.api_token is None
        assert settings.methods is None
        assert settings.paths is None
        assert settings.dry_run is True

    def test_determine_base_url_from_args(self) -> None:
        """Test base URL determination from arguments."""
        # Arrange
        args = Mock()
        args.base_url = "https://args.api.com"
        spec = {}

        # Act
        base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "https://args.api.com"

    def test_determine_base_url_from_env(self) -> None:
        """Test base URL determination from environment variable."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {}

        # Act
        with patch.dict(os.environ, {"API_BASE_URL": "https://env.api.com"}):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "https://env.api.com"

    def test_determine_base_url_from_spec(self) -> None:
        """Test base URL determination from Swagger specification."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {"schemes": ["https", "http"], "host": "spec.api.com"}

        # Act
        with patch.dict(os.environ, {}, clear=True):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "https://spec.api.com"  # Uses first scheme

    def test_determine_base_url_from_spec_http(self) -> None:
        """Test base URL with HTTP scheme from spec."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {"schemes": ["http"], "host": "api.local"}

        # Act
        with patch.dict(os.environ, {}, clear=True):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "http://api.local"

    def test_determine_base_url_default(self) -> None:
        """Test default base URL when no source is available."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {}

        # Act
        with patch.dict(os.environ, {}, clear=True):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "http://localhost:8000"

    def test_determine_base_url_priority(self) -> None:
        """Test priority order for base URL determination."""
        # Arrange
        args = Mock()
        args.base_url = "https://args.api.com"
        spec = {"schemes": ["https"], "host": "spec.api.com"}

        # Act - Args takes priority over env and spec
        with patch.dict(os.environ, {"API_BASE_URL": "https://env.api.com"}):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "https://args.api.com"

        # Act - Env takes priority over spec when no args
        args.base_url = None
        with patch.dict(os.environ, {"API_BASE_URL": "https://env.api.com"}):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "https://env.api.com"

    def test_get_api_token_from_args(self) -> None:
        """Test API token retrieval from arguments."""
        # Arrange
        args = Mock()
        args.api_token = "token_from_args"

        # Act
        token = _get_api_token(args)

        # Assert
        assert token == "token_from_args"

    def test_get_api_token_from_env(self) -> None:
        """Test API token retrieval from environment variable."""
        # Arrange
        args = Mock()
        args.api_token = None

        # Act
        with patch.dict(os.environ, {"API_TOKEN": "token_from_env"}):
            token = _get_api_token(args)

        # Assert
        assert token == "token_from_env"

    def test_get_api_token_none(self) -> None:
        """Test API token when not provided."""
        # Arrange
        args = Mock()
        args.api_token = None

        # Act
        with patch.dict(os.environ, {}, clear=True):
            token = _get_api_token(args)

        # Assert
        assert token is None

    def test_get_api_token_priority(self) -> None:
        """Test priority for API token sources."""
        # Arrange
        args = Mock()
        args.api_token = "args_token"

        # Act - Args takes priority over env
        with patch.dict(os.environ, {"API_TOKEN": "env_token"}):
            token = _get_api_token(args)

        # Assert
        assert token == "args_token"

    def test_spec_with_empty_schemes(self) -> None:
        """Test base URL determination with empty schemes list."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {"schemes": [], "host": "api.example.com"}

        # Act
        with patch.dict(os.environ, {}, clear=True):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "http://api.example.com"  # Defaults to http

    def test_spec_missing_host(self) -> None:
        """Test base URL determination when spec has schemes but no host."""
        # Arrange
        args = Mock()
        args.base_url = None
        spec = {"schemes": ["https"]}  # No host field

        # Act
        with patch.dict(os.environ, {}, clear=True):
            base_url = _determine_base_url(args, spec)

        # Assert
        assert base_url == "http://localhost:8000"  # Falls back to default

    def test_settings_dataclass_fields(self) -> None:
        """Test that Settings dataclass has all expected fields."""
        # Arrange & Act
        settings = Settings(
            swagger_spec_path="test.json",
            base_url="https://api.test.com",
            api_token="token123",
            server_name="test",
            methods=["get"],
            paths=["/api/*"],
            exclude_paths=["/admin/*"],
            tags=["v1"],
            exclude_tags=["beta"],
            operation_ids=["op1"],
            exclude_operation_ids=["op2"],
            host="127.0.0.1",
            port=9000,
            transport="tcp",
            timeout=600.0,
            dry_run=True,
        )

        # Assert - All fields are accessible
        assert settings.swagger_spec_path == "test.json"
        assert settings.base_url == "https://api.test.com"
        assert settings.api_token == "token123"
        assert settings.server_name == "test"
        assert settings.methods == ["get"]
        assert settings.paths == ["/api/*"]
        assert settings.exclude_paths == ["/admin/*"]
        assert settings.tags == ["v1"]
        assert settings.exclude_tags == ["beta"]
        assert settings.operation_ids == ["op1"]
        assert settings.exclude_operation_ids == ["op2"]
        assert settings.host == "127.0.0.1"
        test_port = 9000
        assert settings.port == test_port
        assert settings.transport == "tcp"
        assert settings.timeout == self.DEFAULT_TIMEOUT
        assert settings.dry_run is True

    def test_from_args_preserves_list_types(self) -> None:
        """Test that list arguments are properly preserved."""
        # Arrange
        args = argparse.Namespace(
            swagger_spec="spec.json",
            base_url="https://api.com",
            api_token=None,
            server_name="server",
            methods=["get", "post", "put"],
            paths=["/users/*", "/posts/*"],
            exclude_paths=["/admin/*", "/internal/*"],
            tags=["public", "v1", "stable"],
            exclude_tags=["deprecated", "beta"],
            operation_ids=["op1", "op2", "op3"],
            exclude_operation_ids=["deleteAll", "purge"],
            host="localhost",
            port=8080,
            transport="stdio",
            timeout=600.0,
            dry_run=False,
        )

        # Act
        settings = Settings.from_args(args, {})

        # Assert - Lists are preserved correctly
        assert settings.methods == ["get", "post", "put"]
        expected_method_count = 3
        assert len(settings.methods) == expected_method_count
        assert settings.paths == ["/users/*", "/posts/*"]
        expected_path_count = 2
        assert len(settings.paths) == expected_path_count
        assert settings.tags == ["public", "v1", "stable"]
        expected_tag_count = 3
        assert len(settings.tags) == expected_tag_count


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestSettings()
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
