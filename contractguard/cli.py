import argparse
import sys

from contractguard.diff import compare_specs
from contractguard.parser import load_openapi_spec
from contractguard.report import render_markdown_report, write_markdown_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contractguard",
        description="Detect breaking OpenAPI contract changes before release.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare two OpenAPI specs.")
    compare.add_argument("--old", required=True, help="Path to the current/old OpenAPI spec.")
    compare.add_argument("--new", required=True, help="Path to the proposed/new OpenAPI spec.")
    compare.add_argument("--fail-on-breaking", action="store_true", help="Exit with code 1 when breaking changes exist.")

    report = subparsers.add_parser("report", help="Generate a Markdown compatibility report.")
    report.add_argument("--old", required=True, help="Path to the current/old OpenAPI spec.")
    report.add_argument("--new", required=True, help="Path to the proposed/new OpenAPI spec.")
    report.add_argument("--out", default="reports/contract_report.md", help="Output Markdown report path.")
    report.add_argument("--fail-on-breaking", action="store_true", help="Exit with code 1 when breaking changes exist.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    old_spec = load_openapi_spec(args.old)
    new_spec = load_openapi_spec(args.new)
    contract_report = compare_specs(old_spec, new_spec)

    if args.command == "compare":
        print(render_markdown_report(contract_report))
    elif args.command == "report":
        output_path = write_markdown_report(contract_report, args.out)
        print(f"ContractGuard result: {contract_report.result}")
        print(f"Risk level: {contract_report.risk_level}")
        print(f"Breaking changes: {contract_report.breaking_count}")
        print(f"Report written to: {output_path}")

    if getattr(args, "fail_on_breaking", False) and contract_report.breaking_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
