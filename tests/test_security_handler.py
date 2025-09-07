#!/usr/bin/env python3
"""Unit tests for SecurityHandler component.

This test suite validates the handling of API authentication and security
headers based on Swagger security definitions, including Bearer tokens,
API keys, and various authentication schemes.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path to import from api_client
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client.security import SecurityHandler


class TestSecurityHandler:
    """Test suite for SecurityHandler functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_spec_with_bearer = {
            "swagger": "2.0",
            "security": [{"Bearer": []}],
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                }
            },
        }

        self.sample_spec_with_api_key = {
            "swagger": "2.0",
            "securityDefinitions": {
                "ApiKey": {
                    "type": "apiKey",
                    "name": "X-API-Key",
                    "in": "header",
                }
            },
        }

        self.sample_spec_no_security = {
            "swagger": "2.0",
            "paths": {},
        }

    def test_initialization(self) -> None:
        """Test SecurityHandler initialization."""
        # Act
        handler = SecurityHandler("test_token", self.sample_spec_with_bearer)

        # Assert
        assert handler.api_token == "test_token"
        assert handler.spec == self.sample_spec_with_bearer
        assert "Bearer" in handler.security_definitions

    def test_get_headers_no_token(self) -> None:
        """Test that no headers are returned when no token is provided."""
        # Arrange
        handler = SecurityHandler(None, self.sample_spec_with_bearer)
        operation = {}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}

    def test_get_headers_bearer_global_security(self) -> None:
        """Test Bearer token headers with global security definition."""
        # Arrange
        handler = SecurityHandler("my_token_123", self.sample_spec_with_bearer)
        operation = {}  # No operation-level security, uses global

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {"Authorization": "Bearer my_token_123"}

    def test_get_headers_bearer_operation_security(self) -> None:
        """Test Bearer token headers with operation-level security."""
        # Arrange
        handler = SecurityHandler("op_token", self.sample_spec_with_bearer)
        operation = {"security": [{"Bearer": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {"Authorization": "Bearer op_token"}

    def test_get_headers_api_key_custom_header(self) -> None:
        """Test API key with custom header name."""
        # Arrange
        handler = SecurityHandler("api_key_value", self.sample_spec_with_api_key)
        operation = {"security": [{"ApiKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {"X-API-Key": "api_key_value"}

    def test_get_headers_api_key_authorization_header(self) -> None:
        """Test API key that uses Authorization header."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "AuthKey": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                }
            }
        }
        handler = SecurityHandler("auth_key_123", spec)
        operation = {"security": [{"AuthKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {"Authorization": "Bearer auth_key_123"}

    def test_get_headers_no_security_required(self) -> None:
        """Test operation with no security requirements."""
        # Arrange
        handler = SecurityHandler("token", self.sample_spec_no_security)
        operation = {}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}

    def test_get_headers_multiple_security_requirements(self) -> None:
        """Test handling multiple security requirements."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                },
                "ApiKey": {
                    "type": "apiKey",
                    "name": "X-API-Key",
                    "in": "header",
                },
            }
        }
        handler = SecurityHandler("multi_token", spec)
        # Multiple security requirements (usually OR logic, but we process all)
        operation = {"security": [{"Bearer": []}, {"ApiKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        # Both headers should be present (last one wins for Authorization)
        assert "Authorization" in headers or "X-API-Key" in headers

    def test_get_headers_unsupported_security_type(self) -> None:
        """Test handling of unsupported security types."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "OAuth2": {
                    "type": "oauth2",
                    "flow": "implicit",
                    "authorizationUrl": "https://auth.example.com",
                }
            }
        }
        handler = SecurityHandler("token", spec)
        operation = {"security": [{"OAuth2": ["read", "write"]}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}  # OAuth2 not supported, no headers added

    def test_get_headers_query_param_security(self) -> None:
        """Test that query parameter security is not added to headers."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "QueryKey": {
                    "type": "apiKey",
                    "name": "api_key",
                    "in": "query",  # Query parameter, not header
                }
            }
        }
        handler = SecurityHandler("query_token", spec)
        operation = {"security": [{"QueryKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}  # Query params not added to headers

    def test_operation_security_overrides_global(self) -> None:
        """Test that operation-level security overrides global security."""
        # Arrange
        spec = {
            "security": [{"GlobalKey": []}],
            "securityDefinitions": {
                "GlobalKey": {
                    "type": "apiKey",
                    "name": "X-Global-Key",
                    "in": "header",
                },
                "OperationKey": {
                    "type": "apiKey",
                    "name": "X-Op-Key",
                    "in": "header",
                },
            },
        }
        handler = SecurityHandler("test_token", spec)
        operation = {"security": [{"OperationKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {"X-Op-Key": "test_token"}
        assert "X-Global-Key" not in headers

    def test_empty_security_array(self) -> None:
        """Test handling of empty security array (public endpoint)."""
        # Arrange
        handler = SecurityHandler("token", self.sample_spec_with_bearer)
        operation = {"security": []}  # Empty array means no security

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}

    def test_undefined_security_scheme(self) -> None:
        """Test handling of undefined security schemes."""
        # Arrange
        spec = {"securityDefinitions": {}}
        handler = SecurityHandler("token", spec)
        operation = {"security": [{"UndefinedScheme": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers == {}  # Undefined scheme ignored

    def test_mixed_security_types_in_requirement(self) -> None:
        """Test a single security requirement with multiple schemes."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "Key1": {
                    "type": "apiKey",
                    "name": "X-Key-1",
                    "in": "header",
                },
                "Key2": {
                    "type": "apiKey",
                    "name": "X-Key-2",
                    "in": "header",
                },
            }
        }
        handler = SecurityHandler("shared_token", spec)
        # Single requirement with multiple schemes (AND logic)
        operation = {"security": [{"Key1": [], "Key2": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        assert headers["X-Key-1"] == "shared_token"
        assert headers["X-Key-2"] == "shared_token"

    def test_security_definitions_missing(self) -> None:
        """Test handling when securityDefinitions is missing."""
        # Arrange
        spec = {"swagger": "2.0"}  # No securityDefinitions
        handler = SecurityHandler("token", spec)
        operation = {"security": [{"Bearer": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        # Special case: "Bearer" is handled even without definition
        assert headers == {"Authorization": "Bearer token"}

    def test_process_security_requirement_bearer_shortcut(self) -> None:
        """Test the Bearer shortcut in _process_security_requirement."""
        # Arrange
        handler = SecurityHandler("bearer_token", {})
        sec_req = {"Bearer": []}

        # Act
        headers = handler._process_security_requirement(sec_req)

        # Assert
        assert headers == {"Authorization": "Bearer bearer_token"}

    def test_api_key_with_missing_name(self) -> None:
        """Test API key definition with missing name field."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "BadKey": {
                    "type": "apiKey",
                    # Missing "name" field
                    "in": "header",
                }
            }
        }
        handler = SecurityHandler("token", spec)
        operation = {"security": [{"BadKey": []}]}

        # Act
        headers = handler.get_headers(operation)

        # Assert
        # Should default to "Authorization" when name is missing
        assert headers == {"Authorization": "Bearer token"}

    def test_case_sensitivity(self) -> None:
        """Test that security scheme names are case-sensitive."""
        # Arrange
        spec = {
            "securityDefinitions": {
                "bearer": {  # lowercase
                    "type": "apiKey",
                    "name": "X-Token",
                    "in": "header",
                }
            }
        }
        handler = SecurityHandler("token", spec)
        operation = {"security": [{"Bearer": []}]}  # uppercase

        # Act
        headers = handler.get_headers(operation)

        # Assert
        # "Bearer" with capital B triggers shortcut, not the "bearer" definition
        assert headers == {"Authorization": "Bearer token"}


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestSecurityHandler()
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
