from contractguard.diff import compare_specs
from contractguard.parser import load_openapi_spec


def test_safe_spec_passes_without_breaking_changes():
    old_spec = load_openapi_spec("specs/openapi_old.yaml")
    new_spec = load_openapi_spec("specs/openapi_new_safe.yaml")

    report = compare_specs(old_spec, new_spec)

    assert report.result == "PASS"
    assert report.breaking_count == 0


def test_breaking_spec_detects_required_field_and_removed_response_field():
    old_spec = load_openapi_spec("specs/openapi_old.yaml")
    new_spec = load_openapi_spec("specs/openapi_new_breaking.yaml")

    report = compare_specs(old_spec, new_spec)
    categories = {change.category for change in report.changes}

    assert report.result == "FAIL"
    assert "Added required request field" in categories
    assert "Removed response field" in categories
    assert "Changed parameter type" in categories
    assert "Added required parameter" in categories


def test_breaking_spec_has_high_risk():
    old_spec = load_openapi_spec("specs/openapi_old.yaml")
    new_spec = load_openapi_spec("specs/openapi_new_breaking.yaml")

    report = compare_specs(old_spec, new_spec)

    assert report.risk_level in {"High", "Critical"}
