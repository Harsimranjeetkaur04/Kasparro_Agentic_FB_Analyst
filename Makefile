# Makefile — common tasks for the Agentic FB Ads Analyst project

PYTHON := python
PIP := pip
VENV := .venv
ACTIVATE_WIN := .venv\Scripts\activate
ACTIVATE_SH := source .venv/bin/activate
REQ := requirements.txt

.PHONY: help setup install run test lint clean format

help:
	@echo "Available targets:"
	@echo "  make setup      -> create venv and install dependencies"
	@echo "  make install    -> install dependencies into active env"
	@echo "  make run QUERY  -> run pipeline (provide QUERY)"
	@echo "  make test       -> run pytest"
	@echo "  make lint       -> run flake8 (if installed)"
	@echo "  make clean      -> remove .pyc, __pycache__ and reports"

setup:
	@echo "Creating virtual env and installing dependencies..."
	python -m venv $(VENV)
	@echo "Activate the venv with: $(ACTIVATE_SH) or $(ACTIVATE_WIN)"
	$(PIP) install -r $(REQ)

install:
	$(PIP) install -r $(REQ)

run:
	@if [ -z "$(QUERY)" ]; then \
		echo "Usage: make run QUERY=\"Analyze ROAS drop in last 7 days\""; \
		exit 1; \
	fi
	$(PYTHON) src/run.py "$(QUERY)"

test:
	pytest -q

lint:
	flake8 || echo "flake8 not installed; run 'pip install flake8' to enable linting"

clean:
	@echo "Cleaning pycache, compiled files and reports..."
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	rm -rf reports/* || true
