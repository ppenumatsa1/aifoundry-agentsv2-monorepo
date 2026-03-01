# pb-teams-bing-agent Architecture

## Target system

```text
Teams User
  -> Azure Bot Service
    -> ACA-hosted FastAPI app (/api/messages)
      -> Azure AI Foundry Published Agent (via AZURE_AI_PROJECT_ENDPOINT)
        -> response back through Bot Service to Teams
```

## Design goals

- Keep runtime minimal and repo-aligned
- Remove unnecessary Bot/MSAL complexity
- Use `DefaultAzureCredential` for both local and ACA
- Use RBAC for Foundry access (no Foundry secrets)

## Identity model

### Inbound (Teams to app)

- Teams activity arrives through Azure Bot Service to app endpoint.
- App processes messages using Microsoft Agents hosting components.

### Outbound (app to Foundry)

- App authenticates with `DefaultAzureCredential`.
- Local development: Azure CLI login (`az login`).
- Azure runtime: Managed Identity.
- Foundry authorization controlled by RBAC role assignment (`Azure AI User`).

## Runtime components

- `app.py`: API host and message handler
- `config.py`: env-backed configuration
- `runtime/openai_client.py`: credentialed Foundry project client
- `runtime/run.py`: single-turn request to published agent
- `runtime/agent.py`: published agent name resolver

## Operational notes

- `AZURE_AI_PROJECT_ENDPOINT` is used as the canonical project endpoint.
- `AZURE_PROJECT_RESOURCE_ID` and `AZURE_AI_MODEL_DEPLOYMENT_NAME` remain in config for alignment with other projects.
- Multi-stage Docker build is preserved.
- `.gitignore` and `.dockerignore` are preserved.
