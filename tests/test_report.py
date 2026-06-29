from contractguard.diff import compare_specs
from contractguard.parser import load_openapi_spec
from contractguard.report import render_markdown_report


def test_markdown_report_contains_fail_result():
    old_spec = load_openapi_spec("specs/openapi_old.yaml")
    new_spec = load_openapi_spec("specs/openapi_new_breaking.yaml")

    report = compare_specs(old_spec, new_spec)
    markdown = render_markdown_report(report)

    assert "ContractGuard API Compatibility Report" in markdown
    assert "**Result:** FAIL" in markdown
    assert "Detected Changes" in markdown
