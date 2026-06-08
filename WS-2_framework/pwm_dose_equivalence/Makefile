# pwm_dose_equivalence — developer Makefile.
#
# Bundles the verification commands documented in CONTRIBUTING.md so a
# contributor can run a single `make ci` before opening a PR and know
# they have hit every gate the GitHub Actions workflow will hit.
#
# Run `make help` (or just `make`) for a target list.

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help install lint typecheck test coverage \
        regenerate-examples regenerate-schema regenerate-snapshots regenerate \
        ci clean

help:
	@echo "pwm_dose_equivalence — Makefile targets"
	@echo ""
	@echo "  make install               pip install -e \".[test,lint]\""
	@echo "  make lint                  ruff check src/ tests/ examples/ scripts/"
	@echo "  make typecheck             mypy (uses [tool.mypy] in pyproject.toml)"
	@echo "  make test                  pytest -q"
	@echo "  make coverage              pytest with line-coverage report"
	@echo "  make regenerate-examples   re-issue all examples/ JSON files"
	@echo "  make regenerate-schema     dump CREDENTIAL_JSON_SCHEMA to credential_schema.json"
	@echo "  make regenerate-snapshots  re-capture examples/expected_audit_output.txt"
	@echo "  make regenerate            run all three regenerate targets in sequence"
	@echo "  make ci                    lint + typecheck + coverage (one-command PR gate)"
	@echo "  make clean                 remove caches"

install:
	$(PIP) install -e ".[test,lint]"

lint:
	ruff check src/ tests/ examples/ scripts/

typecheck:
	mypy

test:
	pytest -q

coverage:
	pytest --cov=pwm_dose_equivalence --cov-report=term-missing -q

regenerate-examples:
	$(PYTHON) examples/regenerate.py

regenerate-schema:
	$(PYTHON) scripts/dump_schema.py

regenerate-snapshots:
	$(PYTHON) examples/regenerate_expected_outputs.py

regenerate: regenerate-examples regenerate-schema regenerate-snapshots

# `make ci` is the one-command PR gate. The GitHub Actions workflow at
# ../../.github/workflows/ci.yml runs the same three steps; passing locally
# is necessary but not sufficient (CI also runs on the 3.10 / 3.11 / 3.12
# matrix). Run `make regenerate` first if you have edited the schema
# Python dict, the example credentials, or the CLI output formatter.
ci: lint typecheck coverage

clean:
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
