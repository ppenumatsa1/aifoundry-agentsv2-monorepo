// ── Provision-time module: stable infra that does NOT include the Container App ──
// ACA is created at deploy-time (via aca.bicep called from the predeploy hook) once
// the real runtime image is available in ACR.  This avoids placeholder-image races
// and ARM revision-provisioning timeouts entirely.
//
// What lives here:
//   • ACR  (image registry)
//   • ACA Managed Environment  (compute substrate)
//   • User-Assigned Managed Identity (UAMI) pre-wired with AcrPull + Foundry AI User
//   • Bot Service + Teams Channel  (endpoint is predictable from managedEnvironment.defaultDomain)
//
// What lives in aca.bicep (deploy-time):
//   • Container App  (created/updated with the real runtime image)
//   • Bot Service endpoint update  (synced to actual ACA FQDN)

@description('Location for all resources')
param location string

@description('Tags applied to all resources')
param tags object = {}

@description('Name prefix used for resource naming')
param namePrefix string

@description('Existing Foundry account name — used to pre-assign Foundry AI User role to UAMI')
param foundryName string

@description('Azure Bot App registration client ID')
param botAppId string

@description('Azure Bot App registration tenant ID')
param botTenantId string

@description('Azure Bot app type')
@allowed([
  'SingleTenant'
  'MultiTenant'
  'UserAssignedMSI'
])
param botAppType string = 'SingleTenant'

@description('Optional override for ACR name')
param acrName string = ''

@description('Optional override for ACA managed environment name')
param acaEnvironmentName string = ''

@description('Optional override for ACA app name — used to compute the predictable bot endpoint FQDN')
param acaAppName string = ''

@description('Optional override for Azure Bot resource name')
param botName string = ''

@description('Log Analytics workspace subscription ID')
param logAnalyticsWorkspaceSubscriptionId string = subscription().subscriptionId

@description('Log Analytics workspace resource group')
param logAnalyticsWorkspaceResourceGroup string = resourceGroup().name

@description('Log Analytics workspace name')
param logAnalyticsWorkspaceName string

@description('Role definition ID for AcrPull')
param acrPullRoleDefinitionId string = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

@description('Role definition ID for Azure AI User')
param azureAiUserRoleDefinitionId string = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

// ── Name resolution ────────────────────────────────────────────────────────────
var useExistingAcr = !empty(acrName)
var resolvedAcrName = toLower(empty(acrName) ? take(replace('${namePrefix}tacr', '-', ''), 50) : acrName)
var resolvedAcaEnvironmentName = empty(acaEnvironmentName) ? '${namePrefix}-ace' : acaEnvironmentName
var resolvedAcaAppName = empty(acaAppName) ? '${namePrefix}-teamsapp' : acaAppName
var resolvedBotName = empty(botName) ? '${namePrefix}-bot' : botName
var resolvedUamiName = '${namePrefix}-uami'
var acrResourceId = resourceId('Microsoft.ContainerRegistry/registries', resolvedAcrName)

// ── Existing references ────────────────────────────────────────────────────────

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryName
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: logAnalyticsWorkspaceName
  scope: resourceGroup(logAnalyticsWorkspaceSubscriptionId, logAnalyticsWorkspaceResourceGroup)
}

resource existingAcr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (useExistingAcr) {
  name: resolvedAcrName
}

// ── Resources ──────────────────────────────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = if (!useExistingAcr) {
  name: resolvedAcrName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: resolvedAcaEnvironmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// User-Assigned Managed Identity pre-provisioned with all required roles so
// there is zero race condition when aca.bicep creates the Container App at deploy time.
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: resolvedUamiName
  location: location
  tags: tags
}

// AcrPull: allows Container App to pull images from ACR via the pre-wired UAMI.
resource acrPullAssignmentNew 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!useExistingAcr) {
  name: guid(acrResourceId, uami.id, acrPullRoleDefinitionId)
  scope: acr
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
  }
}

resource acrPullAssignmentExisting 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useExistingAcr) {
  name: guid(acrResourceId, uami.id, acrPullRoleDefinitionId)
  scope: existingAcr
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
  }
}

// Foundry AI User: allows Container App to call Foundry models via the pre-wired UAMI.
resource foundryAiUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, uami.id, azureAiUserRoleDefinitionId)
  scope: foundry
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleDefinitionId)
  }
}

// Bot endpoint is deterministic: ACA FQDNs follow <appName>.<managedEnvironment.defaultDomain>.
// This URL is set now so the Bot Service is fully wired at provision time.
// aca.bicep (deploy-time) performs a reconciling PUT to update it to the live FQDN.
var botEndpoint = 'https://${resolvedAcaAppName}.${managedEnvironment.properties.defaultDomain}/api/messages'

resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: resolvedBotName
  location: 'global'
  kind: 'azurebot'
  sku: {
    name: 'F0'
  }
  tags: tags
  properties: {
    displayName: resolvedBotName
    endpoint: botEndpoint
    msaAppId: botAppId
    msaAppTenantId: botTenantId
    msaAppType: botAppType
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    isStreamingSupported: false
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: botService
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────

var acrLoginServer = reference(acrResourceId, '2023-07-01').loginServer

output acrId string = acrResourceId
output acrName string = resolvedAcrName
output acrLoginServer string = acrLoginServer
output acaEnvironmentId string = managedEnvironment.id
output acaEnvironmentName string = managedEnvironment.name
output acaAppName string = resolvedAcaAppName
output botName string = botService.name
output botEndpoint string = botEndpoint
output uamiId string = uami.id
output uamiClientId string = uami.properties.clientId
