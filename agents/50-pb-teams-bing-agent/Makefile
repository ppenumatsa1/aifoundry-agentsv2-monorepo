.PHONY: help venv install env run batch evals orchestrate e2e-once create-agent provision-bot provision-aca teams-package test clean

VENV := .venv
PY := $(VENV)/bin/python
QUESTION ?= What is the capital of France?
help:
	@echo "Targets:"
	@echo "  make venv         Create local virtual environment"
	@echo "  make install      Install package in editable mode"
	@echo "  make env          Copy .env.example to .env if missing"
	@echo "  make run          Start M365 bot server on /api/messages"
	@echo "  make batch        Placeholder: batch flow scaffold"
	@echo "  make evals        Placeholder: Foundry eval scaffold"
	@echo "  make orchestrate  Placeholder: orchestration scaffold"
	@echo "  make e2e-once     Alias for orchestrate"
	@echo "  make create-agent Create/print Foundry agent with web_search + gpt-4o-mini"
	@echo "  make provision-bot Provision Azure Bot + write MICROSOFT_APP_* to .env"
	@echo "  make provision-aca Provision ACR + ACA env + ACA app (bot-first flow)"
	@echo "  make teams-package Build Teams app zip under teams/build/"
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

create-agent:
	$(PY) -m teams_bing_agent.runtime.agent

provision-aca:
	bash infra/provision_aca.sh

provision-bot:
	bash infra/provision_bot.sh

teams-package:
	python3 teams/build_teams_package.py

test:
	$(PY) -m pytest -m unit

clean:
	rm -rf $(VENV) .pytest_cache
