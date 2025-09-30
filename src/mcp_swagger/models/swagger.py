"""Swagger/OpenAPI specification models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SwaggerInfo:
    """Swagger info object."""

    title: str
    version: str
    description: str | None = None
    terms_of_service: str | None = None
    contact: dict[str, str] | None = None
    license: dict[str, str] | None = None


@dataclass
class SwaggerParameter:
    """Swagger parameter definition."""

    name: str
    in_: str  # location (query, path, header, body, form)
    type_: str | None = None
    required: bool = False
    description: str | None = None
    enum: list[Any] | None = None
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    items: dict[str, Any] | None = None
    schema: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwaggerParameter":
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            in_=data.get("in", "query"),
            type_=data.get("type"),
            required=data.get("required", False),
            description=data.get("description"),
            enum=data.get("enum"),
            default=data.get("default"),
            minimum=data.get("minimum"),
            maximum=data.get("maximum"),
            pattern=data.get("pattern"),
            items=data.get("items"),
            schema=data.get("schema"),
        )


@dataclass
class SwaggerResponse:
    """Swagger response definition."""

    description: str
    schema: dict[str, Any] | None = None
    headers: dict[str, Any] | None = None
    examples: dict[str, Any] | None = None


@dataclass
class SwaggerOperation:
    """Swagger operation definition."""

    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    consumes: list[str] | None = None
    produces: list[str] | None = None
    parameters: list[SwaggerParameter] = field(default_factory=list)
    responses: dict[str, SwaggerResponse] = field(default_factory=dict)
    tags: list[str] | None = None
    security: list[dict[str, list[str]]] | None = None
    deprecated: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwaggerOperation":
        """Create from dictionary representation."""
        parameters = [
            SwaggerParameter.from_dict(param) for param in data.get("parameters", [])
        ]

        responses = {}
        for code, resp_data in data.get("responses", {}).items():
            if isinstance(resp_data, dict):
                responses[code] = SwaggerResponse(
                    description=resp_data.get("description", ""),
                    schema=resp_data.get("schema"),
                    headers=resp_data.get("headers"),
                    examples=resp_data.get("examples"),
                )

        return cls(
            operation_id=data.get("operationId"),
            summary=data.get("summary"),
            description=data.get("description"),
            consumes=data.get("consumes"),
            produces=data.get("produces"),
            parameters=parameters,
            responses=responses,
            tags=data.get("tags"),
            security=data.get("security"),
            deprecated=data.get("deprecated", False),
        )


@dataclass
class SwaggerPathItem:
    """Swagger path item definition."""

    get: SwaggerOperation | None = None
    post: SwaggerOperation | None = None
    put: SwaggerOperation | None = None
    patch: SwaggerOperation | None = None
    delete: SwaggerOperation | None = None
    head: SwaggerOperation | None = None
    options: SwaggerOperation | None = None
    parameters: list[SwaggerParameter] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwaggerPathItem":
        """Create from dictionary representation."""
        # Extract path-level parameters
        parameters = [
            SwaggerParameter.from_dict(param) for param in data.get("parameters", [])
        ]

        # Create path item with operations
        path_item = cls(parameters=parameters)

        # Add operations for each HTTP method
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            if method in data:
                operation = SwaggerOperation.from_dict(data[method])
                setattr(path_item, method, operation)

        return path_item

    def get_operations(self) -> dict[str, SwaggerOperation]:
        """Get all operations for this path."""
        operations = {}
        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            operation = getattr(self, method)
            if operation is not None:
                operations[method] = operation
        return operations


@dataclass
class SwaggerSecurityDefinition:
    """Swagger security definition."""

    type_: str
    name: str | None = None
    in_: str | None = None
    flow: str | None = None
    authorization_url: str | None = None
    token_url: str | None = None
    scopes: dict[str, str] | None = None


@dataclass
class SwaggerSpec:
    """Swagger/OpenAPI specification."""

    swagger: str
    info: SwaggerInfo
    host: str | None = None
    base_path: str | None = None
    schemes: list[str] = field(default_factory=list)
    consumes: list[str] | None = None
    produces: list[str] | None = None
    paths: dict[str, SwaggerPathItem] = field(default_factory=dict)
    definitions: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, SwaggerParameter] = field(default_factory=dict)
    responses: dict[str, SwaggerResponse] = field(default_factory=dict)
    security_definitions: dict[str, SwaggerSecurityDefinition] = field(
        default_factory=dict
    )
    security: list[dict[str, list[str]]] | None = None
    tags: list[dict[str, str]] | None = None
    external_docs: dict[str, str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwaggerSpec":
        """Create from dictionary representation."""
        # Parse info section
        info_data = data.get("info", {})
        info = SwaggerInfo(
            title=info_data.get("title", "API"),
            version=info_data.get("version", "1.0.0"),
            description=info_data.get("description"),
            terms_of_service=info_data.get("termsOfService"),
            contact=info_data.get("contact"),
            license=info_data.get("license"),
        )

        # Parse paths
        paths = {}
        for path, path_data in data.get("paths", {}).items():
            paths[path] = SwaggerPathItem.from_dict(path_data)

        # Parse security definitions
        security_definitions = {}
        for name, sec_def in data.get("securityDefinitions", {}).items():
            security_definitions[name] = SwaggerSecurityDefinition(
                type_=sec_def.get("type", ""),
                name=sec_def.get("name"),
                in_=sec_def.get("in"),
                flow=sec_def.get("flow"),
                authorization_url=sec_def.get("authorizationUrl"),
                token_url=sec_def.get("tokenUrl"),
                scopes=sec_def.get("scopes"),
            )

        return cls(
            swagger=data.get("swagger", "2.0"),
            info=info,
            host=data.get("host"),
            base_path=data.get("basePath"),
            schemes=data.get("schemes", []),
            consumes=data.get("consumes"),
            produces=data.get("produces"),
            paths=paths,
            definitions=data.get("definitions", {}),
            security_definitions=security_definitions,
            security=data.get("security"),
            tags=data.get("tags"),
            external_docs=data.get("externalDocs"),
        )
