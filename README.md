# AI Foundry Agents v2 (Domain-Driven)

This repository contains multiple Azure AI Foundry Agents v2, organized as self-contained packages with azd provisioning and per-agent local execution.

## Summary

- Multiple agents, each isolated with its own runtime, tests, and evals.
- Automated provisioning via azd.
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
- scripts/: reserved for shared infra helpers.
- agents/agent-name/: fully isolated agent packages.

## Agents

| Agent                           | Type         | Description                                                                                                                                                                            | README                                                                                               |
| ------------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 10-pb-vectorstore-invoice-agent | prompt-based | Ingests invoice documents into Azure AI Projects vector stores. Uses vector store search RAG and returns strict JSON output via Azure OpenAI Responses API validated against a schema. | [agents/10-pb-vectorstore-invoice-agent/README.md](agents/10-pb-vectorstore-invoice-agent/README.md) |
| 20-pb-mcp-gh-agent              | prompt-based | Connects to a remote MCP server (GitHub) and answers GitHub questions using MCP tools.                                                                                                 | [agents/20-pb-mcp-gh-agent/README.md](agents/20-pb-mcp-gh-agent/README.md)                           |
| 30-pb-foundryiq-insurance-agent | prompt-based | Uses Foundry IQ with Knowledge Base and Knowledge Source resources through the MCP method, with MCP-first runtime and automatic direct Search fallback on MCP auth failure.            | [agents/30-pb-foundryiq-insurance-agent/README.md](agents/30-pb-foundryiq-insurance-agent/README.md) |
| 40-pb-sharepoint-agent          | prompt-based | Grounds responses against SharePoint content using Azure AI Search and Foundry.                                                                                                        | [agents/40-pb-sharepoint-agent/README.md](agents/40-pb-sharepoint-agent/README.md)                   |
| 50-pb-teams-bing-agent          | prompt-based | Teams-connected agent deployed as an Azure Container App with a Bot Service channel. Uses Bing grounding and Azure AI Foundry agent runtime.                                           | [agents/50-pb-teams-bing-agent/README.md](agents/50-pb-teams-bing-agent/README.md)                   |

## Prerequisites

- Python 3.10+
- Azure Developer CLI (azd)
- Azure CLI authenticated session (`az login`)

## Provision and deploy with azd

This repo assumes you do NOT check in `.env` or `.venv`.

### 1) Create/select an azd environment

```sh
azd env new <env-name>
```

### 2) Provision infrastructure

```sh
azd provision --preview
azd provision
```

### 3) Deploy application services

```sh
azd deploy
```

### 4) Run a specific agent locally

Follow the agent README for setup, env, and make targets:

- [agents/20-pb-mcp-gh-agent/README.md](agents/20-pb-mcp-gh-agent/README.md)
- [agents/10-pb-vectorstore-invoice-agent/README.md](agents/10-pb-vectorstore-invoice-agent/README.md)
- [agents/30-pb-foundryiq-insurance-agent/README.md](agents/30-pb-foundryiq-insurance-agent/README.md)
- [agents/40-pb-sharepoint-agent/README.md](agents/40-pb-sharepoint-agent/README.md)
- [agents/50-pb-teams-bing-agent/README.md](agents/50-pb-teams-bing-agent/README.md)

Agent-specific setup (env vars, secrets, scripts, evals, and troubleshooting) lives in each agent README.

## Disclaimer

This repository is provided for educational and demonstration purposes only. It is not intended for production use as-is. You are responsible for reviewing, testing, and securing any code, configurations, credentials, or deployment artifacts before using them in real systems. Do not deploy this repository without your own security review, compliance checks, and operational hardening (logging, alerting, backups, access controls, and cost safeguards). By using this repository, you acknowledge that you assume all risks associated with its use.
