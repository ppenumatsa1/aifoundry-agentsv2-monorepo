# Product Requirements

## Problem

Teams users need fast, reliable question answering through a Bot endpoint backed by an Azure AI Foundry published agent, with production-safe auth and observable runtime behavior.

## Goals

- Support end-to-end Teams chat flow: Teams -> Bot Service -> FastAPI `/api/messages` -> Foundry agent -> Teams response.
- Keep runtime minimal and operationally stable in Azure Container Apps.
- Use `DefaultAzureCredential` + RBAC (`Azure AI User`) for Foundry access (no Foundry API key flow).
- Emit structured telemetry and traces to Application Insights when `APP_INSIGHTS_CONNECTION_STRING` is set.
- Provide scriptable evaluation flow (`run_batch_questions.py`, `run_foundry_evaluations.py`, `run_orchestrator.py`).
- Keep deployment reproducible via root IaC + `azd`.

## Non-goals

- No custom web UI in this agent.
- No shared runtime package coupling with other agents.
- No advanced telemetry sampling strategy by default (only optional tuning).

## Functional Requirements

- Accept authenticated Bot activities at `POST /api/messages`.
- Reject unauthenticated Bot requests.
- Validate message input and return assistant response text.
- Resolve or create Foundry agent version and invoke it via `responses.create`.
- Support Bing/web search tool usage through Foundry agent tool configuration.

## Operational Requirements

- Health endpoint: `GET /healthz` returns service status.
- Container startup must use Dockerfile command (no runtime bootstrap override).
- Bot credentials and App Insights connection string must be injected via ACA secrets/env from IaC.
- Logs should prioritize business outcome events (`*_completed`, `*_failed`).

## Success Criteria

- Teams E2E message round-trip succeeds.
- `/healthz` returns `200` in deployed environment.
- App Insights contains business flow telemetry and Foundry dependency traces.
- Batch/eval scripts execute successfully against configured Foundry project.
