// ── Deploy-time module: Container App + Bot endpoint reconciliation ─────────────
// Called from:
//   predeploy-teams-aca.sh  — first deploy only, with an init ACR image
//   postdeploy-teams-aca.sh — every deploy, with the real image pushed by azd
//
// Prerequisites from azd provision (m365-teams-agent.bicep):
//   • ACR with the UAMI already granted AcrPull
//   • ACA Managed Environment
//   • UAMI with AcrPull on ACR + Foundry AI User on Foundry — fully propagated
//   • Bot Service with predictable endpoint
//
// No RBAC assignments here — they live in m365-teams-agent.bicep so they are
// fully propagated before this module ever runs, eliminating the auth race.

@description('Azure region for the Container App')
param location string

@description('Resource tags')
param tags object = {}

@description('Existing ACR name (from AZURE_CONTAINER_REGISTRY_NAME provision output)')
param acrName string

@description('Existing ACA managed environment name (from AZURE_ACA_ENV_NAME provision output)')
param acaEnvironmentName string

@description('Container App name — must match the name produced by m365-teams-agent.bicep')
param acaAppName string

@description('Existing Azure Bot resource name (from AZURE_BOT_NAME provision output)')
param botName string

@description('Resource ID of the UAMI created at provision time (from AZURE_UAMI_ID)')
param uamiId string

@description('Client ID of the UAMI created at provision time (from AZURE_UAMI_CLIENT_ID)')
param uamiClientId string

@description('Full container image reference — e.g., myacr.azurecr.io/pb-teams-bing-agent:20250303.1')
param imageFullName string

@description('Azure Bot App registration client ID')
param botAppId string

@description('Azure Bot App registration tenant ID')
param botTenantId string = ''

@description('Azure Bot app type')
@allowed([
  'SingleTenant'
  'MultiTenant'
  'UserAssignedMSI'
])
param botAppType string = 'SingleTenant'

@description('Azure Bot app registration client secret — stored as ACA secret, not in ARM state')
@secure()
param botAppPassword string = ''

@description('Foundry project endpoint URL')
param foundryProjectEndpoint string

@description('Model deployment name the agent runtime will use')
param foundryModelDeploymentName string = 'gpt-4.1-mini'

@description('Foundry agent identifier')
param foundryAgentId string = 'pb-teams-bing-agent'

@description('App Insights resource name — connection string is looked up at deploy time (no secret in params)')
param appInsightsName string = ''

// ── Existing resource references ───────────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: acaEnvironmentName
}

// ── Runtime secret / env var construction ─────────────────────────────────────

var hasBotPassword = !empty(botAppPassword)
var botPasswordSecret = hasBotPassword
  ? [
      {
        name: 'ms-app-password'
        value: botAppPassword
      }
    ]
  : []
var botPasswordEnv = hasBotPassword
  ? [
      {
        name: 'MICROSOFT_APP_PASSWORD'
        secretRef: 'ms-app-password'
      }
    ]
  : []

// Fetch App Insights connection string directly from Azure — avoids passing secrets
// through the script params file on disk.
var appInsightsConnectionString = !empty(appInsightsName)
  ? reference(resourceId('Microsoft.Insights/components', appInsightsName), '2020-02-02').ConnectionString
  : ''
var hasAppInsights = !empty(appInsightsConnectionString)
var appInsightsSecret = hasAppInsights
  ? [
      {
        name: 'app-insights-connection-string'
        value: appInsightsConnectionString
      }
    ]
  : []
var appInsightsEnv = hasAppInsights
  ? [
      {
        name: 'APP_INSIGHTS_CONNECTION_STRING'
        secretRef: 'app-insights-connection-string'
      }
    ]
  : []

var containerEnv = concat([
  {
    name: 'MICROSOFT_APP_ID'
    value: botAppId
  }
  {
    name: 'MICROSOFT_APP_TENANT_ID'
    value: botTenantId
  }
  {
    name: 'MICROSOFT_APP_TYPE'
    value: botAppType
  }
  {
    name: 'AZURE_AI_PROJECT_ENDPOINT'
    value: foundryProjectEndpoint
  }
  {
    name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME'
    value: foundryModelDeploymentName
  }
  {
    name: 'FOUNDRY_AGENT_ID'
    value: foundryAgentId
  }
  {
    name: 'MANAGED_IDENTITY_CLIENT_ID'
    value: uamiClientId
  }
], botPasswordEnv, appInsightsEnv)

// ── Container App ──────────────────────────────────────────────────────────────
// Uses a User-Assigned Managed Identity for ACR pull — no race condition since
// the UAMI already holds AcrPull from the provision phase.

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: acaAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'teamsbingagent' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uamiId}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'Auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: uamiId
        }
      ]
      secrets: concat(botPasswordSecret, appInsightsSecret)
    }
    template: {
      containers: [
        {
          name: acaAppName
          image: imageFullName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: containerEnv
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// ── Bot Service — reconciling PUT ──────────────────────────────────────────────
// Updates the endpoint from the predictable-but-provisional FQDN set at provision
// time to the actual live FQDN once the Container App is running.

resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  kind: 'azurebot'
  sku: { name: 'F0' }
  tags: tags
  properties: {
    displayName: botName
    endpoint: 'https://${containerApp.properties.configuration.ingress.fqdn}/api/messages'
    msaAppId: botAppId
    msaAppTenantId: botTenantId
    msaAppType: botAppType
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    isStreamingSupported: false
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────

output acaName string = containerApp.name
output acaFqdn string = containerApp.properties.configuration.ingress.fqdn
output acaResourceId string = containerApp.id
output botEndpoint string = botService.properties.endpoint
