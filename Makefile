PYTHON ?= python

.PHONY: lint typecheck test validate gate

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy cosheaf tests

test:
	$(PYTHON) -m pytest

validate:
	$(PYTHON) -m cosheaf.cli validate

gate:
	$(PYTHON) -m cosheaf.cli gate
