from typing import Any

from contractguard.models import Change, ContractReport
from contractguard.parser import spec_title

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
SUCCESS_STATUS_PREFIXES = ("2",)


def compare_specs(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> ContractReport:
    changes: list[Change] = []
    old_paths = old_spec.get("paths", {}) or {}
    new_paths = new_spec.get("paths", {}) or {}

    for path in sorted(old_paths):
        if path not in new_paths:
            methods = ", ".join(sorted(_operation_methods(old_paths[path])))
            changes.append(Change(
                category="Removed endpoint",
                severity="High",
                location=path,
                message=f"Endpoint removed with methods: {methods or 'none'}.",
                recommendation="Restore the endpoint or introduce a versioned replacement before release.",
            ))
            continue

        changes.extend(_compare_path(path, old_paths[path], new_paths[path]))

    risk_level = _risk_level(changes)
    result = "FAIL" if any(change.breaking for change in changes) else "PASS"
    return ContractReport(
        old_title=spec_title(old_spec),
        new_title=spec_title(new_spec),
        result=result,
        risk_level=risk_level,
        changes=changes,
    )


def _compare_path(path: str, old_path_item: dict[str, Any], new_path_item: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    old_methods = _operation_methods(old_path_item)
    new_methods = _operation_methods(new_path_item)

    for method in sorted(old_methods - new_methods):
        changes.append(Change(
            category="Removed method",
            severity="High",
            location=f"{method.upper()} {path}",
            message=f"HTTP method {method.upper()} was removed.",
            recommendation="Restore the method or release the change under a new API version.",
        ))

    for method in sorted(old_methods & new_methods):
        old_operation = old_path_item.get(method, {}) or {}
        new_operation = new_path_item.get(method, {}) or {}
        location = f"{method.upper()} {path}"
        changes.extend(_compare_parameters(location, old_path_item, new_path_item, old_operation, new_operation))
        changes.extend(_compare_request_body(location, old_operation, new_operation))
        changes.extend(_compare_responses(location, old_operation, new_operation))

    return changes


def _operation_methods(path_item: dict[str, Any]) -> set[str]:
    return {key.lower() for key in path_item if key.lower() in HTTP_METHODS}


def _compare_parameters(
    location: str,
    old_path_item: dict[str, Any],
    new_path_item: dict[str, Any],
    old_operation: dict[str, Any],
    new_operation: dict[str, Any],
) -> list[Change]:
    changes: list[Change] = []
    old_params = _parameter_map((old_path_item.get("parameters") or []) + (old_operation.get("parameters") or []))
    new_params = _parameter_map((new_path_item.get("parameters") or []) + (new_operation.get("parameters") or []))

    for key, old_param in sorted(old_params.items()):
        if key not in new_params:
            param_in, name = key
            changes.append(Change(
                category="Removed parameter",
                severity="Medium",
                location=f"{location} parameter {param_in}.{name}",
                message=f"Parameter '{name}' in '{param_in}' was removed.",
                recommendation="Keep the parameter for backward compatibility or document a versioned migration.",
            ))
            continue

        old_type = _schema_type(old_param.get("schema", {}) or {})
        new_type = _schema_type(new_params[key].get("schema", {}) or {})
        if old_type and new_type and old_type != new_type:
            param_in, name = key
            changes.append(Change(
                category="Changed parameter type",
                severity="High",
                location=f"{location} parameter {param_in}.{name}",
                message=f"Parameter '{name}' changed type from {old_type} to {new_type}.",
                recommendation="Preserve the original parameter type or create a new versioned endpoint.",
            ))

    for key, new_param in sorted(new_params.items()):
        old_param = old_params.get(key)
        was_required = bool(old_param and old_param.get("required", False))
        is_required = bool(new_param.get("required", False))

        if old_param is None and is_required:
            param_in, name = key
            changes.append(Change(
                category="Added required parameter",
                severity="High",
                location=f"{location} parameter {param_in}.{name}",
                message=f"New required parameter '{name}' was added in '{param_in}'.",
                recommendation="Make the parameter optional or release the change under a new API version.",
            ))
        elif old_param is not None and not was_required and is_required:
            param_in, name = key
            changes.append(Change(
                category="Parameter made required",
                severity="High",
                location=f"{location} parameter {param_in}.{name}",
                message=f"Existing parameter '{name}' is now required.",
                recommendation="Keep the parameter optional for existing clients.",
            ))

    return changes


def _compare_request_body(location: str, old_operation: dict[str, Any], new_operation: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    old_schema = _json_body_schema(old_operation.get("requestBody", {}) or {})
    new_schema = _json_body_schema(new_operation.get("requestBody", {}) or {})
    old_required = set(old_schema.get("required", []) or [])
    new_required = set(new_schema.get("required", []) or [])

    for field_name in sorted(new_required - old_required):
        changes.append(Change(
            category="Added required request field",
            severity="High",
            location=f"{location} requestBody.{field_name}",
            message=f"Required request field '{field_name}' was added.",
            recommendation="Make the field optional or release the request contract under a new version.",
        ))

    old_properties = old_schema.get("properties", {}) or {}
    new_properties = new_schema.get("properties", {}) or {}

    for field_name in sorted(set(old_properties) & set(new_properties)):
        old_type = _schema_type(old_properties[field_name])
        new_type = _schema_type(new_properties[field_name])
        if old_type and new_type and old_type != new_type:
            changes.append(Change(
                category="Changed request field type",
                severity="High",
                location=f"{location} requestBody.{field_name}",
                message=f"Request field '{field_name}' changed type from {old_type} to {new_type}.",
                recommendation="Preserve the original field type or version the API.",
            ))

    return changes


def _compare_responses(location: str, old_operation: dict[str, Any], new_operation: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    old_responses = old_operation.get("responses", {}) or {}
    new_responses = new_operation.get("responses", {}) or {}

    for status_code in sorted(old_responses):
        if str(status_code).startswith(SUCCESS_STATUS_PREFIXES) and status_code not in new_responses:
            changes.append(Change(
                category="Removed success response",
                severity="High",
                location=f"{location} response {status_code}",
                message=f"Success response status '{status_code}' was removed.",
                recommendation="Preserve existing successful response codes for dependent clients.",
            ))

    for status_code in sorted(set(old_responses) & set(new_responses)):
        old_schema = _json_body_schema(old_responses[status_code])
        new_schema = _json_body_schema(new_responses[status_code])
        old_properties = old_schema.get("properties", {}) or {}
        new_properties = new_schema.get("properties", {}) or {}

        for field_name in sorted(set(old_properties) - set(new_properties)):
            changes.append(Change(
                category="Removed response field",
                severity="High",
                location=f"{location} response {status_code}.{field_name}",
                message=f"Response field '{field_name}' was removed from status {status_code}.",
                recommendation="Keep the response field or version the response contract.",
            ))

        for field_name in sorted(set(old_properties) & set(new_properties)):
            old_type = _schema_type(old_properties[field_name])
            new_type = _schema_type(new_properties[field_name])
            if old_type and new_type and old_type != new_type:
                changes.append(Change(
                    category="Changed response field type",
                    severity="High",
                    location=f"{location} response {status_code}.{field_name}",
                    message=f"Response field '{field_name}' changed type from {old_type} to {new_type}.",
                    recommendation="Preserve the original response field type or version the API.",
                ))

    return changes


def _parameter_map(parameters: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    mapped = {}
    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        name = parameter.get("name")
        param_in = parameter.get("in")
        if name and param_in:
            mapped[(str(param_in), str(name))] = parameter
    return mapped


def _json_body_schema(container: dict[str, Any]) -> dict[str, Any]:
    content = container.get("content", {}) or {}
    json_media = content.get("application/json", {}) or {}
    schema = json_media.get("schema", {}) or {}
    return schema if isinstance(schema, dict) else {}


def _schema_type(schema: dict[str, Any]) -> str | None:
    if not isinstance(schema, dict):
        return None

    value = schema.get("type")
    if isinstance(value, list):
        return "|".join(sorted(str(item) for item in value))
    if value:
        return str(value)

    return None


def _risk_level(changes: list[Change]) -> str:
    breaking = [change for change in changes if change.breaking]
    high_count = sum(1 for change in breaking if change.severity.lower() == "high")

    if high_count >= 3:
        return "Critical"
    if high_count >= 1:
        return "High"
    if breaking:
        return "Medium"
    return "Low"
