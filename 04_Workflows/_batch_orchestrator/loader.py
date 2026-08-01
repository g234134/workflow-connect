"""Load and validate batch subtask / manifest JSON documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
    from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
    from referencing import Registry, Resource
except ImportError:  # pragma: no cover - jsonschema is a repo dependency
    Draft202012Validator = None  # type: ignore[assignment,misc]
    SchemaError = Exception  # type: ignore[assignment,misc]
    JsonSchemaValidationError = Exception  # type: ignore[assignment,misc]
    Registry = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]


DEFAULT_SCHEMA_REL = Path("_templates") / "batch_subtask.schema.json"


def default_schema_path(*, workflows_root: Path | None = None) -> Path:
    """Return the repo-relative batch subtask schema path."""
    root = workflows_root or Path(__file__).resolve().parents[1]
    return root / DEFAULT_SCHEMA_REL


def _load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    path = schema_path or default_schema_path()
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _validator(schema: Mapping[str, Any]) -> Draft202012Validator:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required for batch loader validation")
    return Draft202012Validator(schema)


def _format_schema_error(error: JsonSchemaValidationError) -> str:
    path = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"{path}: {error.message}"


def _exc_message(exc: BaseException) -> str:
    message = getattr(exc, "message", None)
    return str(message) if message is not None else str(exc)


def _schema_registry(schema_doc: Mapping[str, Any]) -> Registry:
    if Registry is None or Resource is None:
        raise RuntimeError("jsonschema is required for batch loader validation")
    schema_id = str(schema_doc.get("$id") or "")
    return Registry().with_resource(schema_id, Resource.from_contents(dict(schema_doc)))


def _manifest_validator(schema_doc: Mapping[str, Any]) -> Draft202012Validator:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required for batch loader validation")
    schema_id = str(schema_doc.get("$id") or "")
    return Draft202012Validator(
        {"$ref": f"{schema_id}#/$defs/batch_manifest"},
        registry=_schema_registry(schema_doc),
    )


def _dependency_errors(
    subtask: Mapping[str, Any],
    *,
    known_subtask_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    subtask_id = str(subtask.get("subtask_id", "")).strip()
    deps = subtask.get("dependencies") or []

    for dep in deps:
        dep_id = str(dep).strip()
        if not dep_id:
            errors.append(f"{subtask_id or '<unknown>'}: dependency must be a non-empty string")
            continue
        if subtask_id and dep_id == subtask_id:
            errors.append(f"{subtask_id}: dependency must not reference itself")
            continue
        if known_subtask_ids is not None and dep_id not in known_subtask_ids:
            errors.append(
                f"{subtask_id or '<unknown>'}: dependency '{dep_id}' is not defined in batch manifest"
            )
    return errors


def validate_subtask(
    payload: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    schema_path: Path | None = None,
    known_subtask_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Validate a single subtask document."""
    errors: list[str] = []
    schema_doc = schema or _load_schema(schema_path)

    try:
        validator = _validator(schema_doc)
    except (SchemaError, RuntimeError) as exc:
        return {"ok": False, "data": None, "errors": [f"invalid schema: {_exc_message(exc)}"]}

    collected = sorted(validator.iter_errors(dict(payload)), key=lambda err: list(err.path))
    for error in collected:
        errors.append(_format_schema_error(error))

    errors.extend(_dependency_errors(payload, known_subtask_ids=known_subtask_ids))

    if errors:
        return {"ok": False, "data": None, "errors": errors}

    return {"ok": True, "data": {"kind": "subtask", "subtask": dict(payload)}, "errors": []}


def validate_batch_manifest(
    payload: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Validate a batch manifest and each nested subtask."""
    errors: list[str] = []
    schema_doc = schema or _load_schema(schema_path)

    try:
        manifest_validator = _manifest_validator(schema_doc)
    except (SchemaError, RuntimeError) as exc:
        return {"ok": False, "data": None, "errors": [f"invalid manifest schema: {_exc_message(exc)}"]}

    for error in sorted(manifest_validator.iter_errors(dict(payload)), key=lambda err: list(err.path)):
        errors.append(_format_schema_error(error))

    subtasks = payload.get("subtasks")
    if not isinstance(subtasks, list):
        return {"ok": False, "data": None, "errors": errors or ["subtasks must be an array"]}

    known_ids = {
        str(item.get("subtask_id")).strip()
        for item in subtasks
        if isinstance(item, Mapping) and str(item.get("subtask_id", "")).strip()
    }

    validated_subtasks: list[dict[str, Any]] = []
    for index, item in enumerate(subtasks):
        if not isinstance(item, Mapping):
            errors.append(f"subtasks[{index}]: must be an object")
            continue
        result = validate_subtask(
            item,
            schema=schema_doc,
            schema_path=schema_path,
            known_subtask_ids=known_ids,
        )
        if not result["ok"]:
            errors.extend(result["errors"])
            continue
        validated_subtasks.append(result["data"]["subtask"])

    parent_ticket_id = str(payload.get("parent_ticket_id", "")).strip()
    for subtask in validated_subtasks:
        if parent_ticket_id and subtask.get("parent_ticket_id") != parent_ticket_id:
            errors.append(
                f"{subtask.get('subtask_id')}: parent_ticket_id must match manifest parent_ticket_id"
            )

    if errors:
        return {"ok": False, "data": None, "errors": errors}

    return {
        "ok": True,
        "data": {
            "kind": "manifest",
            "batch_id": payload.get("batch_id"),
            "parent_ticket_id": payload.get("parent_ticket_id"),
            "subtasks": validated_subtasks,
        },
        "errors": [],
    }


def _parse_json_source(source: str | Path | Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    if isinstance(source, Mapping):
        return dict(source), []

    text: str
    if isinstance(source, Path):
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            return None, [f"failed to read file: {exc}"]
    else:
        path = Path(source)
        if path.exists() and path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                return None, [f"failed to read file: {exc}"]
        else:
            text = source

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"]

    if not isinstance(parsed, dict):
        return None, ["document root must be a JSON object"]

    return parsed, []


def load_subtask(
    source: str | Path | Mapping[str, Any],
    *,
    schema_path: Path | None = None,
    known_subtask_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Load a single subtask JSON document from a path, JSON string, or mapping."""
    payload, errors = _parse_json_source(source)
    if errors:
        return {"ok": False, "data": None, "errors": errors}
    assert payload is not None
    return validate_subtask(
        payload,
        schema_path=schema_path,
        known_subtask_ids=known_subtask_ids,
    )


def load_batch_manifest(
    source: str | Path | Mapping[str, Any],
    *,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Load a batch manifest JSON document from a path, JSON string, or mapping."""
    payload, errors = _parse_json_source(source)
    if errors:
        return {"ok": False, "data": None, "errors": errors}
    assert payload is not None
    return validate_batch_manifest(payload, schema_path=schema_path)


def load_batch_document(
    source: str | Path | Mapping[str, Any],
    *,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Load either a subtask or a batch manifest based on document shape."""
    payload, errors = _parse_json_source(source)
    if errors:
        return {"ok": False, "data": None, "errors": errors}
    assert payload is not None

    if "subtasks" in payload:
        return validate_batch_manifest(payload, schema_path=schema_path)
    return validate_subtask(payload, schema_path=schema_path)


# FRAME public API aliases (BATCH-MVP-01)
load_subtasks_from_path = load_subtask
load_batch_manifest_from_path = load_batch_manifest
