#!/usr/bin/env python3
"""Unit tests for SwaggerFilter component.

This test suite validates the filtering logic for Swagger operations based on
various criteria including methods, paths, tags, and operation IDs.

The SwaggerFilter is crucial for controlling which API endpoints are exposed
through the MCP interface, allowing fine-grained control over tool generation.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path to import from filters
sys.path.insert(0, str(Path(__file__).parent.parent))
from filters.swagger_filter import SwaggerFilter


class TestSwaggerFilter:
    """Test suite for SwaggerFilter functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.sample_operation = {
            "operationId": "getUser",
            "tags": ["users", "public"],
            "summary": "Get user details",
        }

    def test_default_filter_allows_get_only(self) -> None:
        """Test that default filter only allows GET methods."""
        # Arrange
        filter_config = SwaggerFilter()

        # Act & Assert
        assert filter_config.should_include("/users", "get", self.sample_operation), (
            "Default filter should allow GET"
        )
        assert not filter_config.should_include(
            "/users", "post", self.sample_operation
        ), "Default filter should not allow POST"
        assert not filter_config.should_include(
            "/users", "put", self.sample_operation
        ), "Default filter should not allow PUT"
        assert not filter_config.should_include(
            "/users", "delete", self.sample_operation
        ), "Default filter should not allow DELETE"

    def test_method_filtering(self) -> None:
        """Test filtering by HTTP methods."""
        # Arrange
        filter_config = SwaggerFilter(methods=["get", "post"])

        # Act & Assert
        assert filter_config.should_include("/users", "get", self.sample_operation)
        assert filter_config.should_include("/users", "post", self.sample_operation)
        assert not filter_config.should_include("/users", "put", self.sample_operation)
        assert not filter_config.should_include(
            "/users", "delete", self.sample_operation
        )

    def test_path_pattern_filtering(self) -> None:
        """Test filtering by path patterns with wildcards."""
        # Arrange
        filter_config = SwaggerFilter(paths=["/users/*", "/admin/*"])

        # Act & Assert
        assert filter_config.should_include(
            "/users/123", "get", self.sample_operation
        ), "Should match /users/* pattern"
        assert filter_config.should_include(
            "/admin/settings", "get", self.sample_operation
        ), "Should match /admin/* pattern"
        assert not filter_config.should_include(
            "/posts/123", "get", self.sample_operation
        ), "Should not match unspecified pattern"
        assert not filter_config.should_include(
            "/users", "get", self.sample_operation
        ), "Should not match exact path without wildcard"

    def test_exclude_path_patterns(self) -> None:
        """Test exclusion by path patterns."""
        # Arrange
        filter_config = SwaggerFilter(exclude_paths=["/internal/*", "/admin/*"])

        # Act & Assert
        assert filter_config.should_include(
            "/users/123", "get", self.sample_operation
        ), "Should allow non-excluded paths"
        assert not filter_config.should_include(
            "/internal/metrics", "get", self.sample_operation
        ), "Should exclude /internal/* paths"
        assert not filter_config.should_include(
            "/admin/users", "get", self.sample_operation
        ), "Should exclude /admin/* paths"

    def test_tag_filtering(self) -> None:
        """Test filtering by Swagger tags."""
        # Arrange
        filter_config = SwaggerFilter(tags=["users"])
        operation_with_tags = {"tags": ["users", "public"]}
        operation_without_tags = {"tags": ["posts"]}
        operation_no_tags = {}

        # Act & Assert
        assert filter_config.should_include("/path", "get", operation_with_tags), (
            "Should include operation with matching tag"
        )
        assert not filter_config.should_include(
            "/path", "get", operation_without_tags
        ), "Should exclude operation without matching tag"
        assert not filter_config.should_include("/path", "get", operation_no_tags), (
            "Should exclude operation with no tags"
        )

    def test_exclude_tags(self) -> None:
        """Test exclusion by Swagger tags."""
        # Arrange
        filter_config = SwaggerFilter(exclude_tags=["internal", "deprecated"])
        public_operation = {"tags": ["public", "users"]}
        internal_operation = {"tags": ["internal", "metrics"]}
        deprecated_operation = {"tags": ["deprecated"]}

        # Act & Assert
        assert filter_config.should_include("/path", "get", public_operation), (
            "Should include non-excluded tags"
        )
        assert not filter_config.should_include("/path", "get", internal_operation), (
            "Should exclude internal tag"
        )
        assert not filter_config.should_include("/path", "get", deprecated_operation), (
            "Should exclude deprecated tag"
        )

    def test_operation_id_filtering(self) -> None:
        """Test filtering by specific operation IDs."""
        # Arrange
        filter_config = SwaggerFilter(operation_ids=["getUser", "createUser"])
        get_user_op = {"operationId": "getUser"}
        create_user_op = {"operationId": "createUser"}
        delete_user_op = {"operationId": "deleteUser"}

        # Act & Assert - operation IDs bypass method filter
        assert filter_config.should_include("/users", "get", get_user_op), (
            "Should include specified operation ID"
        )
        assert filter_config.should_include("/users", "post", create_user_op), (
            "Should include POST when operation ID matches"
        )
        assert not filter_config.should_include("/users", "delete", delete_user_op), (
            "Should exclude non-specified operation ID"
        )

    def test_exclude_operation_ids(self) -> None:
        """Test exclusion by operation IDs."""
        # Arrange
        filter_config = SwaggerFilter(
            exclude_operation_ids=["deleteUser", "archiveUser"]
        )
        get_user_op = {"operationId": "getUser"}
        delete_user_op = {"operationId": "deleteUser"}

        # Act & Assert
        assert filter_config.should_include("/users", "get", get_user_op), (
            "Should include non-excluded operation"
        )
        assert not filter_config.should_include("/users", "get", delete_user_op), (
            "Should exclude specified operation ID even with GET"
        )

    def test_complex_filter_combination(self) -> None:
        """Test complex combinations of filter criteria."""
        # Arrange
        filter_config = SwaggerFilter(
            methods=["get", "post"],
            paths=["/api/v1/*"],
            tags=["public"],
            exclude_tags=["deprecated"],
            exclude_paths=["/api/v1/internal/*"],
        )

        # Test various combinations
        public_api_op = {"tags": ["public"]}
        deprecated_api_op = {"tags": ["public", "deprecated"]}
        internal_api_op = {"tags": ["public"]}

        # Act & Assert
        assert filter_config.should_include("/api/v1/users", "get", public_api_op), (
            "Should match all positive criteria"
        )
        assert not filter_config.should_include(
            "/api/v1/users", "delete", public_api_op
        ), "Should fail on method mismatch"
        assert not filter_config.should_include(
            "/api/v2/users", "get", public_api_op
        ), "Should fail on path mismatch"
        assert not filter_config.should_include(
            "/api/v1/users", "get", deprecated_api_op
        ), "Should fail on excluded tag"
        assert not filter_config.should_include(
            "/api/v1/internal/metrics", "get", internal_api_op
        ), "Should fail on excluded path"

    def test_operation_id_bypass_method_filter(self) -> None:
        """Test that explicit operation IDs bypass method filtering."""
        # Arrange
        filter_config = SwaggerFilter(
            methods=["get"],  # Only GET allowed
            operation_ids=[
                "createUser",
                "updateUser",
            ],  # But these operations are included
        )
        create_op = {"operationId": "createUser"}
        update_op = {"operationId": "updateUser"}
        delete_op = {"operationId": "deleteUser"}

        # Act & Assert
        assert filter_config.should_include("/users", "post", create_op), (
            "POST should be allowed when operation ID matches"
        )
        assert filter_config.should_include("/users", "put", update_op), (
            "PUT should be allowed when operation ID matches"
        )
        assert not filter_config.should_include("/users", "delete", delete_op), (
            "DELETE should not be allowed without matching operation ID"
        )

    def test_empty_filter_lists(self) -> None:
        """Test behavior with empty filter lists."""
        # Arrange
        filter_config = SwaggerFilter(
            methods=[],  # Empty methods list
            paths=[],  # Empty paths list
            tags=[],  # Empty tags list
        )

        # Act & Assert
        # Empty methods list should actually default to ["get"] per implementation
        assert filter_config.should_include("/users", "get", self.sample_operation), (
            "Empty methods list defaults to GET"
        )
        assert not filter_config.should_include(
            "/users", "post", self.sample_operation
        ), "Empty methods list should not allow POST"

    def test_case_insensitive_methods(self) -> None:
        """Test that HTTP methods are case-insensitive."""
        # Arrange
        filter_config = SwaggerFilter(methods=["GET", "Post"])

        # Act & Assert
        assert filter_config.should_include("/users", "get", self.sample_operation), (
            "Should match lowercase get"
        )
        assert filter_config.should_include("/users", "GET", self.sample_operation), (
            "Should match uppercase GET"
        )
        assert filter_config.should_include("/users", "post", self.sample_operation), (
            "Should match lowercase post"
        )
        assert filter_config.should_include("/users", "POST", self.sample_operation), (
            "Should match uppercase POST"
        )

    def test_wildcard_patterns_edge_cases(self) -> None:
        """Test edge cases in wildcard pattern matching."""
        # Arrange
        filter_config = SwaggerFilter(paths=["*/users", "/api/*/users/*", "*"])

        # Act & Assert
        assert filter_config.should_include(
            "/v1/users", "get", self.sample_operation
        ), "Should match */users pattern"
        assert filter_config.should_include(
            "/api/v1/users/123", "get", self.sample_operation
        ), "Should match /api/*/users/* pattern"
        assert filter_config.should_include(
            "/anything", "get", self.sample_operation
        ), "Should match * pattern"

    def test_operation_without_tags(self) -> None:
        """Test handling of operations without tags."""
        # Arrange
        filter_with_tags = SwaggerFilter(tags=["users"])
        filter_exclude_tags = SwaggerFilter(exclude_tags=["internal"])
        operation_no_tags = {"operationId": "someOp"}

        # Act & Assert
        assert not filter_with_tags.should_include("/path", "get", operation_no_tags), (
            "Operation without tags should not match tag filter"
        )
        assert filter_exclude_tags.should_include("/path", "get", operation_no_tags), (
            "Operation without tags should pass exclude filter"
        )

    def test_operation_without_id(self) -> None:
        """Test handling of operations without operation IDs."""
        # Arrange
        filter_with_ids = SwaggerFilter(operation_ids=["getUser"])
        filter_exclude_ids = SwaggerFilter(exclude_operation_ids=["deleteUser"])
        operation_no_id = {"tags": ["users"]}

        # Act & Assert
        assert not filter_with_ids.should_include("/path", "get", operation_no_id), (
            "Operation without ID should not match ID filter"
        )
        assert filter_exclude_ids.should_include("/path", "get", operation_no_id), (
            "Operation without ID should pass exclude ID filter"
        )

    def test_priority_of_exclusions(self) -> None:
        """Test that exclusions take priority over inclusions."""
        # Arrange
        filter_config = SwaggerFilter(
            operation_ids=["getUser"],
            exclude_operation_ids=["getUser"],  # Same ID in both
        )
        operation = {"operationId": "getUser"}

        # Act & Assert
        assert not filter_config.should_include("/users", "get", operation), (
            "Exclusion should take priority over inclusion"
        )


def test_compile_pattern_regex_escaping() -> None:
    """Test that special regex characters are properly escaped in patterns."""
    # Arrange
    filter_config = SwaggerFilter(paths=["/api/v1.0/users", "/api/[test]/users"])

    # Act & Assert
    # The dots and brackets should be treated as literals, not regex special chars
    assert filter_config.should_include("/api/v1.0/users", "get", {}), (
        "Should match literal dot"
    )
    assert not filter_config.should_include("/api/v1X0/users", "get", {}), (
        "Should not match any character for dot"
    )
    assert filter_config.should_include("/api/[test]/users", "get", {}), (
        "Should match literal brackets"
    )
    assert not filter_config.should_include("/api/t/users", "get", {}), (
        "Should not match character class"
    )


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestSwaggerFilter()
        test_methods = [m for m in dir(test_suite) if m.startswith("test_")]

        for method_name in test_methods:
            test_suite.setup_method()
            method = getattr(test_suite, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except AssertionError as e:
                print(f"✗ {method_name}: {e}")

        # Run standalone test
        try:
            test_compile_pattern_regex_escaping()
            print("✓ test_compile_pattern_regex_escaping")
        except AssertionError as e:
            print(f"✗ test_compile_pattern_regex_escaping: {e}")

        print("\nBasic tests completed!")
