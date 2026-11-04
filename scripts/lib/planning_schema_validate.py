"""Stdlib structural JSON Schema validator for docs/templates/tasks-schema.json keywords only."""

from __future__ import annotations

import re
from typing import Any


class SchemaValidationError(Exception):
    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def validate_instance(
    data: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> None:
    """Validate *data* against *schema*; raise SchemaValidationError on failure."""
    if root_schema is None:
        root_schema = schema

    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise SchemaValidationError(path, f"unsupported $ref target: {ref}")
        target = _resolve_ref(root_schema, ref)
        validate_instance(data, target, root_schema=root_schema, path=path)
        return

    schema_type = schema.get("type")
    if schema_type is not None:
        _validate_type(data, schema_type, path)

    if "const" in schema and data != schema["const"]:
        raise SchemaValidationError(path, f"expected const {schema['const']!r}, got {data!r}")

    if "enum" in schema and data not in schema["enum"]:
        raise SchemaValidationError(
            path,
            f"expected one of {schema['enum']!r}, got {data!r}",
        )

    if schema_type == "string":
        if not isinstance(data, str):
            return
        if "minLength" in schema and len(data) < schema["minLength"]:
            raise SchemaValidationError(
                path,
                f"string shorter than minLength {schema['minLength']}",
            )
        if "pattern" in schema and not re.fullmatch(schema["pattern"], data):
            raise SchemaValidationError(
                path,
                f"string does not match pattern {schema['pattern']!r}",
            )

    if schema_type == "array":
        if not isinstance(data, list):
            return
        if "minItems" in schema and len(data) < schema["minItems"]:
            raise SchemaValidationError(
                path,
                f"array shorter than minItems {schema['minItems']}",
            )
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            for index, item in enumerate(data):
                key = _unique_key(item)
                if key in seen:
                    raise SchemaValidationError(
                        f"{path}[{index}]",
                        "duplicate array item (uniqueItems)",
                    )
                seen.add(key)
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(data):
                validate_instance(
                    item,
                    item_schema,
                    root_schema=root_schema,
                    path=f"{path}[{index}]",
                )

    if schema_type == "object":
        if not isinstance(data, dict):
            return
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                raise SchemaValidationError(path, f"missing required property {key!r}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in data.items():
            child_path = f"{path}.{key}"
            if key in properties:
                validate_instance(
                    value,
                    properties[key],
                    root_schema=root_schema,
                    path=child_path,
                )
            elif additional is False:
                raise SchemaValidationError(
                    child_path,
                    f"additional property {key!r} is not allowed",
                )
            elif isinstance(additional, dict):
                validate_instance(
                    value,
                    additional,
                    root_schema=root_schema,
                    path=child_path,
                )


def _validate_type(data: Any, schema_type: str, path: str) -> None:
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    expected = type_map.get(schema_type)
    if expected is None:
        raise SchemaValidationError(path, f"unsupported schema type {schema_type!r}")
    if not isinstance(data, expected):
        raise SchemaValidationError(
            path,
            f"expected type {schema_type}, got {type(data).__name__}",
        )


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    parts = ref.lstrip("#/").split("/")
    node: Any = root_schema
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise SchemaValidationError(ref, f"unresolved $ref {ref!r}")
        node = node[part]
    if not isinstance(node, dict):
        raise SchemaValidationError(ref, f"$ref {ref!r} did not resolve to an object schema")
    return node


def _unique_key(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return repr(value)
    return repr(value)
