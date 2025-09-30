"""Filter for selecting which endpoints to expose from a Swagger spec."""

import re

from mcp_swagger.models import SwaggerOperation


class SwaggerFilter:
    """Filter for selecting which endpoints to expose."""

    def __init__(
        self,
        methods: list[str] | None = None,
        paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        operation_ids: list[str] | None = None,
        exclude_operation_ids: list[str] | None = None,
    ) -> None:
        """Initialize the filter with various selection criteria.

        Args:
            methods: HTTP methods to include (default: ["get"])
            paths: Path patterns to include (supports wildcards)
            exclude_paths: Path patterns to exclude
            tags: Swagger tags to include
            exclude_tags: Swagger tags to exclude
            operation_ids: Specific operation IDs to include
            exclude_operation_ids: Specific operation IDs to exclude

        """
        self.methods = {m.lower() for m in (methods or ["get"])}
        self.path_patterns = [self._compile_pattern(p) for p in (paths or [])]
        self.exclude_patterns = [
            self._compile_pattern(p) for p in (exclude_paths or [])
        ]
        self.tags = set(tags or [])
        self.exclude_tags = set(exclude_tags or [])
        self.operation_ids = set(operation_ids or [])
        self.exclude_operation_ids = set(exclude_operation_ids or [])

    def should_include(
        self, path: str, method: str, operation: SwaggerOperation
    ) -> bool:
        """Determine if an endpoint should be included based on filters.

        Logic:
        1. If operation ID is explicitly included via operation_ids, include it (bypass method filter)
        2. Otherwise, check if method matches and other filters pass
        """
        method = method.lower()
        op_id = operation.operation_id

        # Check if explicitly included by ID
        is_explicitly_included = self.operation_ids and op_id in self.operation_ids

        if is_explicitly_included:
            # Only check excludes when explicitly included
            return self._check_excludes_only(path, operation)

        # Standard filtering logic
        return self._apply_standard_filters(path, method, operation)

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """Convert a path pattern with wildcards to regex."""
        pattern = re.escape(pattern).replace(r"\*", ".*")
        return re.compile(f"^{pattern}$")

    def _check_excludes_only(self, path: str, operation: SwaggerOperation) -> bool:
        """Check only exclusion filters (for explicitly included operations)."""
        op_id = operation.operation_id

        # Check excluded operation IDs
        if op_id in self.exclude_operation_ids:
            return False

        # Check excluded paths
        if any(p.match(path) for p in self.exclude_patterns):
            return False

        # Check excluded tags
        op_tags = set(operation.tags or [])
        return not (self.exclude_tags and op_tags.intersection(self.exclude_tags))

    def _apply_standard_filters(
        self, path: str, method: str, operation: SwaggerOperation
    ) -> bool:
        """Apply standard filtering logic."""
        # Check method
        if method not in self.methods:
            return False

        # Check operation filters
        if not self._check_operation_filters(operation):
            return False

        # Check path patterns
        return self._check_path_patterns(path)

    def _check_operation_filters(self, operation: SwaggerOperation) -> bool:
        """Check operation-level filters (IDs and tags)."""
        op_id = operation.operation_id

        # Check excluded operation IDs
        if op_id in self.exclude_operation_ids:
            return False

        # Check included operation IDs (if specified)
        if self.operation_ids and op_id not in self.operation_ids:
            return False

        # Check tags
        op_tags = set(operation.tags or [])

        # Check included tags
        if self.tags and not op_tags.intersection(self.tags):
            return False

        # Check excluded tags
        return not (self.exclude_tags and op_tags.intersection(self.exclude_tags))

    def _check_path_patterns(self, path: str) -> bool:
        """Check if path matches inclusion/exclusion patterns."""
        # Check included paths
        if self.path_patterns and not any(p.match(path) for p in self.path_patterns):
            return False

        # Check excluded paths
        return not any(p.match(path) for p in self.exclude_patterns)
