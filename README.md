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

## Provision and deploy (automated)

1. Provision infrastructure:

- azd provision

2. Deploy (runs the selected agent hook):

- azd deploy

Agent-specific details (setup, env, scripts, and evals) live in each agent README.
