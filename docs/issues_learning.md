# Issues and Learnings (AI Foundry Agents v2 Demo)

Permalink: Issues and Learnings (AI Foundry Agents v2 Demo)

This document captures the main deployment and runtime issues encountered while hardening
`agents/50-pb-teams-bing-agent` for repeatable `azd provision` + `azd deploy` flows.

For each issue: symptom, root cause, fix applied, and reusable learning.

---

## 1) ACA provisioning timed out with placeholder image path

Permalink: 1) ACA provisioning timed out with placeholder image path

- Symptom:
  - `azd provision` intermittently failed at Container App creation with `ContainerAppOperationError` and `Operation expired`.
  - Failures were more frequent in fresh environments.
- Root cause:
  - Container App creation was coupled to first-revision startup during infra provisioning.
  - Placeholder/bootstrap image and first-revision health behavior created a fragile provisioning path.
- Fix:
  - Split lifecycle into two phases:
    - Provision phase creates base infra (ACR, ACE, Bot, Foundry, Search, monitoring, UAMI).
    - Deploy phase handles ACA image rollout via hooks and dedicated ACA deployment template.
  - Removed dependency on placeholder image in steady-state deploy path.
- Learning:
  - Keep long-running app revision concerns out of baseline infra provisioning.
  - Provision should focus on durable infrastructure; app runtime rollout belongs in deploy orchestration.

---

## 2) ACR pull auth failure on first ACA revision

Permalink: 2) ACR pull auth failure on first ACA revision

- Symptom:
  - ACA create failed with image pull errors similar to:
    - `unable to pull image using Managed identity system for registry ...`
- Root cause:
  - First revision attempted to pull from ACR before identity + role assignment path was consistently ready.
  - System-assigned identity timing was not deterministic during first create.
- Fix:
  - Introduced User-Assigned Managed Identity (UAMI) created during provision.
  - Assigned `AcrPull` and Foundry role to UAMI in provision path.
  - ACA deploy uses UAMI explicitly for registry pull.
- Learning:
  - For first-revision reliability, pre-provision UAMI + RBAC and bind explicitly.
  - Avoid relying on just-created system identity for immediate critical pulls.

---

## 3) Runtime auth failure: `DefaultAzureCredential` could not resolve identity

Permalink: 3) Runtime auth failure: DefaultAzureCredential could not resolve identity

- Symptom:
  - Bot replies failed with `DefaultAzureCredential failed to retrieve a token...`.
  - `ManagedIdentityCredential` branch reported inability to load proper managed identity.
- Root cause:
  - App switched to UAMI runtime, but `MANAGED_IDENTITY_CLIENT_ID` was not injected into ACA env.
  - Runtime code expects managed identity client id path for deterministic token acquisition.
- Fix:
  - Added `AZURE_UAMI_CLIENT_ID` output wiring and passed it into ACA env as `MANAGED_IDENTITY_CLIENT_ID`.
  - Verified env var presence in live container app revision.
- Learning:
  - Identity model changes must include runtime env contract updates.
  - Always verify effective env vars in deployed container, not only template intent.

---

## 4) ACE/ACA race condition during predeploy

Permalink: 4) ACE/ACA race condition during predeploy

- Symptom:
  - First deploy after provision intermittently failed with errors such as:
    - `ManagedEnvironmentNotFound`
    - transient ACA deployment failures despite ACE showing as provisioned.
- Root cause:
  - Control-plane eventual consistency: ACE marked complete before ACA operations fully stabilized.
- Fix (minimal):
  - Added slim stabilization in `scripts/predeploy-teams-aca.sh`:
    - fixed short wait,
    - short ACE readiness poll,
    - single retry on first ACA deployment attempt.
- Learning:
  - Small controlled waits + one retry can eliminate most transient control-plane races without adding heavy complexity.

---

## 5) Deploy hook path resolution failure

Permalink: 5) Deploy hook path resolution failure

- Symptom:
  - `azd deploy` failed with predeploy script not found (`.../predeploy-teams-aca.sh: not found`).
- Root cause:
  - Service-level hook paths were interpreted relative to service project path, not repo root.
- Fix:
  - Updated `azure.yaml` hook paths to use correct relative paths from service directory.
- Learning:
  - Validate hook execution context and path resolution when using service-scoped hooks.

---

## 6) Port mismatch risk (Uvicorn vs ACA ingress)

Permalink: 6) Port mismatch risk (Uvicorn vs ACA ingress)

- Symptom:
  - Potential startup/health instability when app listen port and ACA `targetPort` differ.
- Root cause:
  - Runtime and infra were temporarily inconsistent (`80` vs expected app port).
- Fix:
  - Standardized both app and ACA to `8000`.
- Learning:
  - Keep runtime container port and ingress target port explicitly aligned.

---

## 7) Quota failures across model deployments

Permalink: 7) Quota failures across model deployments

- Symptom:
  - Provision failed with `InsufficientQuota` for model capacities.
- Root cause:
  - Requested model capacities exceeded available per-subscription/per-region quota windows.
- Fix:
  - Parameterized capacities and used env-specific values.
  - Made high-cost models optional by setting capacity to `0` where needed.
  - Added configurable `gpt5Capacity` (instead of hardcoded value).
- Learning:
  - Treat model capacities as environment variables, not constants.
  - For new region/env bring-up, start with conservative defaults and scale up.

---

## 8) Accidental duplicate resource sets in one RG

Permalink: 8) Accidental duplicate resource sets in one RG

- Symptom:
  - New resource prefix appeared in same resource group, effectively creating a second set of resources.
- Root cause:
  - Top-level template had defaults for `location` and `environmentName`; fallback values could diverge from intended env settings.
  - Name prefix uses `resourceGroup().id + environmentName`, so input drift changes full resource names.
- Fix:
  - Removed defaults for top-level `location` and `environmentName` in `infra/main.bicep` (fail-fast behavior).
- Learning:
  - Critical naming inputs should be required parameters to prevent silent fallback drift.

---

## 9) Teams package endpoint drift (stale local `.env`)

Permalink: 9) Teams package endpoint drift (stale local .env)

- Symptom:
  - Teams package was built with older endpoint from local `.env`, not latest deployed ACA endpoint.
- Root cause:
  - Packaging script read `BOT_ENDPOINT` from local file instead of active deployment state.
- Fix:
  - Updated `teams/build_teams_package.py` to resolve latest endpoint from selected `azd` env + live ACA FQDN.
- Learning:
  - Packaging for deployment should source runtime endpoints from deployed state, not developer-local files.

---

## 10) First-principles workflow clarification: IaC + deploy only

Permalink: 10) First-principles workflow clarification: IaC + deploy only

- Symptom:
  - Confusion when manual app-registration commands were used during troubleshooting.
- Root cause:
  - Ad-hoc remediation mixed with intended automated workflow.
- Fix:
  - Standardized on hook-driven automation:
    - preprovision script creates/ensures bot app registration + secret if missing,
    - provision + deploy flows consume env values and propagate to templates/hooks.
- Learning:
  - Keep manual CLI actions out of baseline runbooks once automation path is validated.

---

## Current snapshot (validated)

Permalink: Current snapshot (validated)

- End-to-end `azd provision` + `azd deploy` validated on fresh environments (`test11`), including:
  - Bot app registration auto-prepared through preprovision hook,
  - ACA running with latest ACR image,
  - `MANAGED_IDENTITY_CLIENT_ID` present in runtime env,
  - Bot endpoint wired to latest ACA `/api/messages`.

---

## Recommended operating defaults

Permalink: Recommended operating defaults

1. Keep first-time environment setup minimal:
   - set env name, RG, location, quota-safe capacities,
   - leave bot values empty to allow automation to populate.
2. Keep model capacity knobs environment-specific.
3. Keep required naming inputs explicit (no default fallbacks for `location` / `environmentName`).
4. Preserve minimal predeploy stabilization (short wait + readiness poll + single retry).
5. Build Teams package from deployed endpoint source, not local `.env` endpoint values.
