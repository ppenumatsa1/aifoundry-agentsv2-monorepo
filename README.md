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

## Provision (azd) + run locally

This repo assumes you do NOT check in `.env` or `.venv`. Use azd for infra, then run agents locally from their folders.

### 1) Create/select an azd environment

```sh
azd env new <env-name>
```

### 2) Provision infrastructure

```sh
azd provision
```

> **First run on a new environment:** Bicep creates the full stack — Azure AI Foundry account, Foundry project, all model deployments, AI Search, monitoring, and the Teams agent ACA + Bot Service. After provisioning completes, azd writes the resource names back into `.azure/<env-name>/.env` (e.g. `existingFoundryName`, `existingFoundryProjectName`).

> **Subsequent runs (day-2):** Because `existingFoundryName` is already set in `.env`, Bicep detects the Foundry and project as pre-existing and skips recreating them. Only resources that differ from desired state are updated (e.g. Container App image, Bot endpoint). Model deployments are also skipped — they are only deployed on initial greenfield provisioning.

#### How the greenfield / day-2 switch works

The decision is driven entirely by a single Bicep parameter:

| `existingFoundryName` value     | Behaviour                                                                     |
| ------------------------------- | ----------------------------------------------------------------------------- |
| `""` (empty — new environment)  | **Greenfield**: creates Foundry account, project, and all 5 model deployments |
| `"<name>"` (set — existing env) | **Day-2**: references existing Foundry and project; model deployments skipped |

The parameter is controlled by the azd environment variable of the same name. You never need to set it manually — `azd provision` writes it to `.env` on first deploy. To start completely fresh, create a new azd environment (`azd env new`), which starts with an empty `.env`.

#### Teams agent (50-pb-teams-bing-agent) — required env vars

The Teams agent requires a pre-registered Azure Bot app. Set these before provisioning:

```sh
azd env set MICROSOFT_APP_ID       <bot-app-client-id>
azd env set MICROSOFT_APP_PASSWORD <bot-app-client-secret>
azd env set MICROSOFT_APP_TENANT_ID <tenant-id>
azd env set M365_ACR_NAME          <existing-acr-name>   # if reusing an existing ACR
azd env set m365BotName            <existing-bot-name>   # if reusing an existing Azure Bot resource
```

If `MICROSOFT_APP_PASSWORD` is not set, the Bot password secret is omitted from the Container App (useful for Managed Identity bots).

### 3) Set required per-agent secrets

`20-pb-mcp-gh-agent` needs a GitHub PAT:

```sh
azd env set MCP_PAT <your_github_pat>
```

### 4) Run a specific agent locally

Follow the agent README for setup, env, and make targets:

- [agents/20-pb-mcp-gh-agent/README.md](agents/20-pb-mcp-gh-agent/README.md)
- [agents/10-pb-vectorstore-invoice-agent/README.md](agents/10-pb-vectorstore-invoice-agent/README.md)
- [agents/30-pb-foundryiq-insurance-agent/README.md](agents/30-pb-foundryiq-insurance-agent/README.md)

Agent-specific details (setup, env, scripts, and evals) live in each agent README.

## Disclaimer

This repository is provided for educational and demonstration purposes only. It is not intended for production use as-is. You are responsible for reviewing, testing, and securing any code, configurations, credentials, or deployment artifacts before using them in real systems. Do not deploy this repository without your own security review, compliance checks, and operational hardening (logging, alerting, backups, access controls, and cost safeguards). By using this repository, you acknowledge that you assume all risks associated with its use.
