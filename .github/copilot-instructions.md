# Copilot instructions

## Context

- This repo hosts multiple Azure AI Foundry Agents v2 under `agents/`.
- Infrastructure is managed via `azd provision` and Bicep in `infra/`.
- Agent execution is local per agent (no azd deploy hooks).

## Do

- Prefer `python3` for venv creation and scripts.
- Use each agent's Makefile targets for setup and runs.
- Keep `.env` local and never commit secrets; edit `.env.example` for placeholders only.
- Use canonical env vars:
  - `AZURE_AI_PROJECT_ENDPOINT`
  - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- Follow each agent README for ingest/run/eval flow.

## Do not

- Do not reintroduce azd postdeploy hooks or agent execution in azd deploy.
- Do not add duplicate env variable names for project endpoints or model names.
- Do not write real credentials or keys into tracked files.

## Common paths

- `agents/<agent>/scripts/run_orchestrator.py` orchestrates ingest -> smoke test -> batch -> eval.
- `agents/<agent>/scripts/run_orchestrator.sh` bootstraps env + venv and calls the Python orchestrator.
- `infra/` contains Bicep only; local runs belong in `agents/`.
