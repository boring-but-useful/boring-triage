.PHONY: audit demo format lint test typecheck verify

PYTHON ?= .venv/bin/python

format:
	$(PYTHON) -m ruff check --fix src tests
	$(PYTHON) -m ruff format src tests

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

typecheck:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest

verify: lint typecheck test
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 overview >/dev/null
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 timeline >/dev/null

audit:
	$(PYTHON) -m pip_audit -r requirements-dev.lock --no-deps --disable-pip --strict --cache-dir .cache/pip-audit

demo:
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 overview
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 timeline
