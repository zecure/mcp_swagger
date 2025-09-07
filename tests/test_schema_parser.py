#!/usr/bin/env python3
"""Unit tests for SchemaParser component.

This test suite validates the creation of Pydantic models from Swagger
parameter definitions, ensuring proper type mapping, validation constraints,
and field configurations.
"""

import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

# Add parent directory to path to import from parsers
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_swagger.models.parameter import ParameterInfo
from mcp_swagger.parsers.schema_parser import SchemaParser


class TestSchemaParser:
    """Test suite for SchemaParser functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        self.basic_string_param = ParameterInfo(
            name="username",
            location="query",
            param_type="string",
            required=True,
            description="User's username",
        )

        self.optional_int_param = ParameterInfo(
            name="limit",
            location="query",
            param_type="integer",
            required=False,
            default=10,
            description="Result limit",
        )

        self.constrained_param = ParameterInfo(
            name="age",
            location="query",
            param_type="integer",
            required=True,
            minimum=0,
            maximum=150,
            description="User's age",
        )

    def test_build_model_with_single_required_param(self) -> None:
        """Test building a model with a single required parameter."""
        # Arrange
        parameters = [self.basic_string_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        assert model is not None, "Model should be created"
        assert issubclass(model, BaseModel), "Should be a Pydantic model"
        assert "username" in model.model_fields, "Should have username field"

        # Test instantiation
        instance = model(username="john_doe")
        assert instance.username == "john_doe"

        # Test validation
        with pytest.raises(ValidationError):
            model()  # Missing required field

    def test_build_model_with_optional_param(self) -> None:
        """Test building a model with optional parameters."""
        # Arrange
        parameters = [self.optional_int_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        assert model is not None
        model.model_fields["limit"]

        # Test default value
        instance = model()
        default_limit = 10
        assert instance.limit == default_limit, "Should use default value"

        # Test custom value
        custom_limit = 20
        instance = model(limit=custom_limit)
        assert instance.limit == custom_limit

    def test_build_model_with_mixed_params(self) -> None:
        """Test building a model with both required and optional parameters."""
        # Arrange
        parameters = [self.basic_string_param, self.optional_int_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        assert "username" in model.model_fields
        assert "limit" in model.model_fields

        # Test valid instantiation
        instance = model(username="alice")
        assert instance.username == "alice"
        default_limit = 10
        assert instance.limit == default_limit

        custom_limit = 5
        instance = model(username="bob", limit=custom_limit)
        assert instance.username == "bob"
        assert instance.limit == custom_limit

    def test_build_model_with_constraints(self) -> None:
        """Test building a model with validation constraints."""
        # Arrange
        parameters = [self.constrained_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        # Test valid values
        test_age = 25
        instance = model(age=test_age)
        assert instance.age == test_age

        # Test boundary values
        instance = model(age=0)
        assert instance.age == 0
        max_age = 150
        instance = model(age=max_age)
        assert instance.age == max_age

        # Test constraint violations
        with pytest.raises(ValidationError) as exc_info:
            model(age=-1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            model(age=151)
        assert "less than or equal to 150" in str(exc_info.value).lower()

    def test_build_model_with_enum_param(self) -> None:
        """Test building a model with enum constraints."""
        # Arrange
        enum_param = ParameterInfo(
            name="status",
            location="query",
            param_type="string",
            required=True,
            enum=["active", "inactive", "pending"],
            description="User status",
        )
        parameters = [enum_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        # Test valid enum values
        instance = model(status="active")
        assert instance.status == "active"

        # Note: Pydantic's enum validation through json_schema_extra
        # doesn't enforce at runtime by default, but the schema is set
        field_info = model.model_fields["status"]
        assert field_info.json_schema_extra == {
            "enum": ["active", "inactive", "pending"]
        }

    def test_build_model_with_body_schema(self) -> None:
        """Test building a model with a body schema."""
        # Arrange
        body_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            },
        }

        # Act
        model = SchemaParser.build_params_model([], body_schema, "testOperation")

        # Assert
        assert model is not None
        assert "body" in model.model_fields

        # Test body field accepts dict
        instance = model(body={"name": "John", "email": "john@example.com"})
        assert instance.body == {"name": "John", "email": "john@example.com"}

        # Test body is optional
        instance = model()
        assert instance.body is None

    def test_build_model_with_params_and_body(self) -> None:
        """Test building a model with both parameters and body schema."""
        # Arrange
        parameters = [self.basic_string_param]
        body_schema = {"type": "object", "properties": {"data": {"type": "string"}}}

        # Act
        model = SchemaParser.build_params_model(
            parameters, body_schema, "testOperation"
        )

        # Assert
        assert "username" in model.model_fields
        assert "body" in model.model_fields

        instance = model(username="alice", body={"data": "test"})
        assert instance.username == "alice"
        assert instance.body == {"data": "test"}

    def test_build_model_no_parameters(self) -> None:
        """Test that no model is created when there are no parameters."""
        # Arrange
        parameters = []

        # Act
        model = SchemaParser.build_params_model(parameters, None, "testOperation")

        # Assert
        assert model is None, "Should return None when no parameters"

    def test_type_mapping_string(self) -> None:
        """Test type mapping for string parameters."""
        # Arrange
        param = ParameterInfo(
            name="text",
            required=True,
            description="Text parameter",
            param_type="string",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["text"].annotation
        assert field_type is str

    def test_type_mapping_integer(self) -> None:
        """Test type mapping for integer parameters."""
        # Arrange
        param = ParameterInfo(
            name="count",
            required=True,
            description="Count parameter",
            param_type="integer",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["count"].annotation
        assert field_type is int

    def test_type_mapping_number(self) -> None:
        """Test type mapping for number (float) parameters."""
        # Arrange
        param = ParameterInfo(
            name="price",
            required=True,
            description="Price parameter",
            param_type="number",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["price"].annotation
        assert field_type is float

    def test_type_mapping_boolean(self) -> None:
        """Test type mapping for boolean parameters."""
        # Arrange
        param = ParameterInfo(
            name="active",
            required=True,
            description="Active parameter",
            param_type="boolean",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["active"].annotation
        assert field_type is bool

    def test_type_mapping_array(self) -> None:
        """Test type mapping for array parameters."""
        # Arrange
        param = ParameterInfo(
            name="tags",
            required=True,
            description="Tags parameter",
            param_type="array",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["tags"].annotation
        assert field_type is list

    def test_type_mapping_object(self) -> None:
        """Test type mapping for object parameters."""
        # Arrange
        param = ParameterInfo(
            name="metadata",
            required=True,
            description="Metadata parameter",
            param_type="object",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["metadata"].annotation
        assert field_type is dict

    def test_type_mapping_unknown(self) -> None:
        """Test type mapping for unknown parameter types."""
        # Arrange
        param = ParameterInfo(
            name="custom",
            required=True,
            description="Custom parameter",
            param_type="custom_type",
            location="query",
        )

        # Act
        model = SchemaParser.build_params_model([param], None, "test")

        # Assert
        field_type = model.model_fields["custom"].annotation
        assert field_type == Any

    def test_skip_body_location_params(self) -> None:
        """Test that body location parameters are skipped (handled separately)."""
        # Arrange
        body_param = ParameterInfo(
            name="body",
            required=True,
            description="Body parameter",
            param_type="object",
            location="body",
        )
        query_param = ParameterInfo(
            name="filter",
            required=False,
            description="Filter parameter",
            param_type="string",
            location="query",
        )
        parameters = [body_param, query_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        assert "filter" in model.model_fields
        assert "body" not in model.model_fields  # Body params handled separately

    def test_model_naming(self) -> None:
        """Test that generated models have appropriate names."""
        # Arrange
        parameters = [self.basic_string_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "getUserById")

        # Assert
        assert model.__name__ == "getUserByIdParams"

    def test_field_descriptions(self) -> None:
        """Test that field descriptions are preserved."""
        # Arrange
        param_with_desc = ParameterInfo(
            name="userId",
            location="path",
            param_type="string",
            required=True,
            description="The unique identifier of the user",
        )
        parameters = [param_with_desc]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        field = model.model_fields["userId"]
        assert field.description == "The unique identifier of the user"

    def test_complex_constraints_combination(self) -> None:
        """Test multiple constraints on a single parameter."""
        # Arrange
        complex_param = ParameterInfo(
            name="score",
            location="query",
            param_type="number",
            required=True,
            minimum=0.0,
            maximum=100.0,
            enum=[0.0, 25.0, 50.0, 75.0, 100.0],
            description="Score value",
        )
        parameters = [complex_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        field = model.model_fields["score"]
        assert field.json_schema_extra == {"enum": [0.0, 25.0, 50.0, 75.0, 100.0]}

        # Test valid values
        test_score = 50.0
        instance = model(score=test_score)
        assert instance.score == test_score

        # Test constraint violations
        with pytest.raises(ValidationError):
            model(score=-1.0)  # Below minimum
        with pytest.raises(ValidationError):
            model(score=101.0)  # Above maximum

    def test_optional_with_none_default(self) -> None:
        """Test optional parameters with None as default."""
        # Arrange
        optional_param = ParameterInfo(
            name="filter",
            location="query",
            param_type="string",
            required=False,
            default=None,
            description="Optional filter",
        )
        parameters = [optional_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        instance = model()
        assert instance.filter is None

        instance = model(filter="active")
        assert instance.filter == "active"

    def test_path_params_included(self) -> None:
        """Test that path parameters are properly included in the model."""
        # Arrange
        path_param = ParameterInfo(
            name="resourceId",
            location="path",
            param_type="string",
            required=True,
            description="Resource identifier",
        )
        parameters = [path_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        assert "resourceId" in model.model_fields
        field = model.model_fields["resourceId"]
        assert field.is_required()

    def test_header_params_included(self) -> None:
        """Test that header parameters are properly included in the model."""
        # Arrange
        header_param = ParameterInfo(
            name="X-Request-ID",
            location="header",
            param_type="string",
            required=False,
            description="Request tracking ID",
        )
        parameters = [header_param]

        # Act
        model = SchemaParser.build_params_model(parameters, None, "test")

        # Assert
        assert "X-Request-ID" in model.model_fields


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        test_suite = TestSchemaParser()
        test_methods = [m for m in dir(test_suite) if m.startswith("test_")]

        for method_name in test_methods:
            test_suite.setup_method()
            method = getattr(test_suite, method_name)
            try:
                method()
                print(f"✓ {method_name}")
            except (AssertionError, ValidationError) as e:
                print(f"✗ {method_name}: {e}")

        print("\nBasic tests completed!")
