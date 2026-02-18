.PHONY: help venv install env run batch evals orchestrate e2e-once smoke-anon smoke-auth test clean

VENV := .venv
PY := $(VENV)/bin/python

help:
	@echo "Targets:"
	@echo "  make venv         Create local virtual environment"
	@echo "  make install      Install package in editable mode"
	@echo "  make env          Copy .env.example to .env if missing"
	@echo "  make run          Start FastAPI Teams bot endpoint"
	@echo "  make batch        Run batch questions"
	@echo "  make evals        Run Foundry evaluations"
	@echo "  make orchestrate  Run full orchestration flow"
	@echo "  make e2e-once     Alias for orchestration flow"
	@echo "  make smoke-anon   Run anonymous smoke test against /api/messages"
	@echo "  make smoke-auth   Run authenticated smoke test against /api/messages"
	@echo "  make test         Run unit tests"
	@echo "  make clean        Remove venv and cache artifacts"

venv:
	python3 -m venv $(VENV)

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .

env:
	@if [ ! -f .env ]; then cp .env.example .env; fi

run:
	$(PY) scripts/run_agent.py

batch:
	$(PY) scripts/run_batch_questions.py --questions src/teams_bing_agent/evals/datasets/questions.jsonl

evals:
	$(PY) scripts/run_foundry_evaluations.py --data src/teams_bing_agent/evals/datasets/golden_capture.jsonl

orchestrate:
	$(PY) scripts/run_orchestrator.py

e2e-once: orchestrate

smoke-anon:
	$(PY) scripts/run_anon_smoke_test.py

smoke-auth:
	$(PY) scripts/run_auth_smoke_test.py

test:
	$(PY) -m pytest -m unit

clean:
	rm -rf $(VENV) .pytest_cache
