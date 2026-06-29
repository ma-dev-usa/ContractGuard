from pathlib import Path
from typing import Any

import yaml


def load_openapi_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    with spec_path.open("r", encoding="utf-8") as file:
        spec = yaml.safe_load(file) or {}

    if not isinstance(spec, dict):
        raise ValueError(f"Invalid OpenAPI document: {spec_path}")

    if "paths" not in spec:
        raise ValueError(f"OpenAPI document is missing 'paths': {spec_path}")

    return spec


def spec_title(spec: dict[str, Any]) -> str:
    info = spec.get("info", {}) or {}
    title = info.get("title", "Unknown API")
    version = info.get("version", "unknown-version")
    return f"{title} {version}"
