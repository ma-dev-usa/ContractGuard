# ContractGuard

![Tests](https://github.com/ma-dev-usa/ContractGuard/actions/workflows/tests.yml/badge.svg)

ContractGuard is a Python-based API compatibility gate that detects breaking OpenAPI changes before release. It compares old and new API specifications, classifies contract risk, and generates Markdown reports for CI/CD pipelines.

This project demonstrates API contract testing, breaking-change detection, release-readiness reporting, pytest validation, and CI workflow setup.

## Why This Exists

API changes can silently break client applications when endpoints, required fields, parameters, response codes, or response fields change without coordination. ContractGuard automates first-pass API compatibility review before release.

## Features

- Detects removed endpoints and methods
- Detects added required parameters and request fields
- Detects changed parameter and schema field types
- Detects removed success responses and response fields
- Generates release-readiness Markdown reports
- Includes pytest coverage and a GitHub Actions workflow

## Tech Stack

- Python
- OpenAPI 3.1
- YAML
- Pytest
- GitHub Actions
- Markdown reports

## Quick Start

Run these commands:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pytest

Compare a safe API change:

    python -m contractguard compare --old specs/openapi_old.yaml --new specs/openapi_new_safe.yaml

Compare a breaking API change:

    python -m contractguard compare --old specs/openapi_old.yaml --new specs/openapi_new_breaking.yaml

Generate a Markdown report:

    python -m contractguard report --old specs/openapi_old.yaml --new specs/openapi_new_breaking.yaml --out reports/sample_contract_report.md

## Example Output

    ContractGuard result: FAIL
    Risk level: Critical
    Breaking changes: 6
    Report written to: reports/sample_contract_report.md

## Resume Summary

Built a Python CLI that compares OpenAPI specifications, detects breaking API contract changes, and generates release-readiness reports for CI/CD workflows.
