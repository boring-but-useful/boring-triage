.PHONY: test verify demo

PYTHON ?= .venv/bin/python

test:
	$(PYTHON) -m pytest

verify: test
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 overview >/dev/null
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 timeline >/dev/null

demo:
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 overview
	$(PYTHON) -m boring_triage --case fixtures/case-egress-001 timeline
