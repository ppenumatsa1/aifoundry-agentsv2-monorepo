# AI Foundry Agents v2 (Domain-Driven)

This repository contains multiple Azure AI Foundry Agents v2, organized as self-contained packages with automated azd provisioning and deployment hooks.

## Summary

- Multiple agents, each isolated with its own runtime, tests, and evals.
- Automated provisioning/deploy via azd hooks.
- Clear naming conventions for agent styles.

## Goals

- Each agent owns its prompts, schemas, ingestion logic, tests, and evaluations.
- No shared runtime dependencies across agents.
- Azure infrastructure managed with azd + Bicep at the repository root.

## Naming conventions

- `pb-` means prompt-based.
- `wf-` will mean workflow-based (future agents).

## Structure (high level)

- infra/: Azure infrastructure (Bicep).
- infra/hooks/<agent>/: azd lifecycle hooks per agent (preprovision/postdeploy).
- scripts/: reserved for shared infra helpers.
- agents/<domain>/: fully isolated agent packages.

## Agents

| Agent            | Type         | Description                                                                                                                                                                            | README                                                                 |
| ---------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| pb-invoice-agent | prompt-based | Ingests invoice documents into Azure AI Projects vector stores. Uses vector store search RAG and returns strict JSON output via Azure OpenAI Responses API validated against a schema. | [agents/pb-invoice-agent/README.md](agents/pb-invoice-agent/README.md) |
| pb-gh-mcp-agent  | prompt-based | Connects to a remote MCP server (GitHub) and answers GitHub questions using MCP tools.                                                                                                 | [agents/pb-gh-mcp-agent/README.md](agents/pb-gh-mcp-agent/README.md)   |

## Prerequisites

- Python 3.10+
- Azure Developer CLI (azd)
- Azure CLI authenticated session (`az login`)

## Provision and deploy (automated)

This repo assumes you do NOT check in `.env` or `.venv`. The azd hooks will:

- create a `.venv` if missing and install dependencies,
- copy `.env` from `.azure/<env>/.env` if missing,
- derive Foundry endpoints from azd outputs,
- prompt for missing secrets (for example, GitHub PAT) if not set in the azd env.

### 1) Create/select an azd environment

- azd env new <env-name>

### 2) Provision infrastructure

- azd provision

### 3) Set required per-agent secrets

pb-gh-mcp-agent needs a GitHub PAT:

- azd env set MCP_PAT=<your_github_pat>

### 4) Deploy a specific agent (runs postdeploy hook)

Set the agent you want to run:

- AGENT_NAME=pb-gh-mcp-agent azd deploy
- AGENT_NAME=pb-invoice-agent azd deploy

If no agent is provided, the default hook targets `pb-invoice-agent`.

Agent-specific details (setup, env, scripts, and evals) live in each agent README.
