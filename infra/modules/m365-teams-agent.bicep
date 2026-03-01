@description('Location for all resources')
param location string

@description('Tags applied to all resources')
param tags object = {}

@description('Name prefix used for resource naming')
param namePrefix string

@description('Existing Foundry account name used as RBAC scope')
param foundryName string

@description('Foundry project endpoint used by app runtime')
param foundryProjectEndpoint string

@description('Model deployment name used by app runtime')
param foundryModelDeploymentName string

@description('Foundry agent identifier used by app runtime')
param foundryAgentId string = 'pb-teams-bing-agent'

@description('Container image repo name in ACR')
param imageRepository string = 'pb-teams-bing-agent'

@description('Container image tag')
param imageTag string = 'latest'

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

@description('Azure Bot app password / client secret')
@secure()
param botAppPassword string

@description('Optional override for ACR name')
param acrName string = ''

@description('Optional override for ACA managed environment name')
param acaEnvironmentName string = ''

@description('Optional override for ACA app name')
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

var useExistingAcr = !empty(acrName)
var resolvedAcrName = toLower(empty(acrName) ? take(replace('${namePrefix}tacr', '-', ''), 50) : acrName)
var resolvedAcaEnvironmentName = empty(acaEnvironmentName) ? '${namePrefix}-ace' : acaEnvironmentName
var resolvedAcaAppName = empty(acaAppName) ? '${namePrefix}-teamsapp' : acaAppName
var resolvedBotName = empty(botName) ? '${namePrefix}-bot' : botName
var botEndpoint = 'https://${containerApp.properties.configuration.ingress.fqdn}/api/messages'
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
var acrResourceId = resourceId('Microsoft.ContainerRegistry/registries', resolvedAcrName)
var acrLoginServer = reference(acrResourceId, '2023-07-01').loginServer
var acrCredentials = listCredentials(acrResourceId, '2023-07-01')
var acrRegistrySecret = [
  {
    name: 'acr-password'
    value: acrCredentials.passwords[0].value
  }
]

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

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: resolvedAcaAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
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
          server: acrLoginServer
          username: acrCredentials.username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: concat(botPasswordSecret, acrRegistrySecret)
    }
    template: {
      containers: [
        {
          name: resolvedAcaAppName
          image: '${acrLoginServer}/${imageRepository}:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
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
          ], botPasswordEnv)
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

resource acrPullAssignmentExisting 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useExistingAcr) {
  name: guid(acrResourceId, containerApp.id, acrPullRoleDefinitionId)
  scope: existingAcr
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
  }
}

resource acrPullAssignmentNew 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!useExistingAcr) {
  name: guid(acrResourceId, containerApp.id, acrPullRoleDefinitionId)
  scope: acr
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
  }
}

resource foundryAiUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, containerApp.id, azureAiUserRoleDefinitionId)
  scope: foundry
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleDefinitionId)
  }
}

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

output acrId string = acrResourceId
output acrName string = resolvedAcrName
output acrLoginServer string = acrLoginServer
output acaEnvironmentId string = managedEnvironment.id
output acaEnvironmentName string = managedEnvironment.name
output acaAppName string = containerApp.name
output acaFqdn string = containerApp.properties.configuration.ingress.fqdn
output botName string = botService.name
output botEndpoint string = botEndpoint
