VENV=.venv
PYTHON=$(VENV)/bin/python3
PIP=$(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

format:
	$(PYTHON) -m ruff format .

lint:
	$(PYTHON) -m ruff check .

lint-fix:
	$(PYTHON) -m ruff check . --fix --show-fixes

run:
	PYTHONPATH=src $(PYTHON) src/main.py tests/documents/sample.txt context.md

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf build dist *.egg-info
	rm -rf $(VENV)

check: format lint
