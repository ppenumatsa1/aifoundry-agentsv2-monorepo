.PHONY: help venv install env run batch evals orchestrate clean

VENV := .venv
PY := $(VENV)/bin/python
QUESTION ?= Summarize key security requirements from our SharePoint docs.

help:
	@echo "Targets:"
	@echo "  make venv         Create local virtual environment"
	@echo "  make install      Install package in editable mode"
	@echo "  make env          Copy .env.example to .env if missing"
	@echo "  make run          Run a single question (use QUESTION=...)"
	@echo "  make batch        Run batch questions"
	@echo "  make evals        Run Foundry evaluations"
	@echo "  make orchestrate  Run full orchestration flow"
	@echo "  make clean        Remove venv and cache artifacts"

venv:
	python3 -m venv $(VENV)

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .

env:
	@if [ ! -f .env ]; then cp .env.example .env; fi

run:
	$(PY) scripts/run_agent.py "$(QUESTION)"

batch:
	$(PY) scripts/run_batch_questions.py --questions src/sharepoint_agent/evals/datasets/questions.jsonl

evals:
	$(PY) scripts/run_foundry_evaluations.py --data src/sharepoint_agent/evals/datasets/golden_capture.jsonl

orchestrate:
	$(PY) scripts/run_orchestrator.py

clean:
	rm -rf $(VENV) .pytest_cache
