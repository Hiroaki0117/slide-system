from __future__ import annotations

from pathlib import Path
from typing import Any

from .storage import read_json


class DocumentValidationError(ValueError):
    def __init__(self, schema_name: str, issues: list[str]) -> None:
        super().__init__(f"{schema_name}の検証に失敗しました: " + "; ".join(issues))
        self.schema_name = schema_name
        self.issues = issues


def _jsonschema():
    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "jsonschemaが必要です。`python -m pip install -e .`を実行してください。"
        ) from exc
    return jsonschema


def load_schema(project_root: Path, schema_name: str) -> dict[str, Any]:
    path = project_root / "schemas" / f"{schema_name}.schema.json"
    if not path.is_file():
        raise FileNotFoundError(f"JSON Schemaが見つかりません: {path}")
    return read_json(path)


def validate_document(project_root: Path, schema_name: str, document: Any) -> None:
    jsonschema = _jsonschema()
    schema = load_schema(project_root, schema_name)
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if not errors:
        return
    issues = []
    for error in errors:
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        issues.append(f"{location}: {error.message}")
    raise DocumentValidationError(schema_name, issues)


def validate_file(project_root: Path, schema_name: str, path: Path) -> dict[str, Any]:
    document = read_json(path)
    validate_document(project_root, schema_name, document)
    return document
