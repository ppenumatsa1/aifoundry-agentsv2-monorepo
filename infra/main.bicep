@description('Location for all resources')
param location string = 'eastus2'

@description('Environment name for resource tags')
param environmentName string = 'dev'

@description('Optional user principal object ID for local Search RBAC assignment')
param userPrincipalId string = ''

@description('Optional existing Foundry account name. When empty, defaults to computed name for this environment.')
param existingFoundryName string = ''

@description('Optional existing Foundry project name. When empty, defaults to computed name for this environment.')
param existingFoundryProjectName string = ''

@description('Container image tag for the Teams ACA app')
param m365ImageTag string = ''

@description('Resolved service image name from azd deploy output for Teams ACA app')
param m365ServiceImageName string = ''

@description('Optional existing ACR name for Teams app image pull')
param m365AcrName string = ''

@description('Bot app registration client ID')
param m365BotAppId string = ''

@description('Bot app registration tenant ID')
param m365BotTenantId string = ''

@description('Bot app type')
param m365BotAppType string = 'SingleTenant'

@description('Bot app registration client secret')
@secure()
param m365BotAppPassword string = ''

@description('Optional existing Azure Bot resource name. When set, updates the existing bot instead of creating a new one.')
param m365BotName string = ''

@description('Foundry agent id for Teams runtime')
param m365AgentId string = 'pb-teams-bing-agent'

@description('Model deployment name for Teams runtime')
param m365ModelDeploymentName string = 'gpt-4.1-mini'

@description('Optional Foundry project endpoint override for Teams runtime')
param m365FoundryProjectEndpoint string = ''

@description('Optional Log Analytics workspace resource ID override for Teams ACA environment')
param m365LogAnalyticsWorkspaceResourceId string = ''

@description('Azure AI Search SKU for this environment (free has a subscription-wide limit of 1)')
param searchSkuName string = 'basic'

@description('Capacity for text-embedding-3-small deployment (in TPM thousands)')
param textEmbedding3SmallCapacity int = 120

@description('Capacity for gpt-4o deployment (in TPM thousands)')
param gpt4oCapacity int = 200

@description('Capacity for gpt-4.1-mini deployment (in TPM thousands)')
param gpt41MiniCapacity int = 1000

@description('Capacity for text-embedding-3-large deployment (in TPM thousands)')
param textEmbedding3LargeCapacity int = 100

@description('Tags applied to all resources')
param tags object = {
  environment: environmentName
  project: 'aifoundry-agentsv2-demo'
  region: location
  managedBy: 'azd'
  SecurityControl: 'Ignore'
}

var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName))
var namePrefix = 'aif${resourceToken}'
var defaultFoundryName = '${namePrefix}-foundry'
var defaultFoundryProjectName = '${namePrefix}-proj'
var foundryName = empty(existingFoundryName) ? defaultFoundryName : existingFoundryName
var foundryProjectName = empty(existingFoundryProjectName) ? defaultFoundryProjectName : existingFoundryProjectName
var searchServiceName = '${namePrefix}-search-basic'

// When existingFoundryName is provided we reference pre-existing resources;
// when empty this is a greenfield environment and we create everything.
var useExistingFoundry = !empty(existingFoundryName)

var foundryProjectEndpoint = empty(m365FoundryProjectEndpoint)
  ? 'https://${foundryName}.services.ai.azure.com/api/projects/${foundryProjectName}'
  : m365FoundryProjectEndpoint

var logAnalyticsWorkspaceResourceId = empty(m365LogAnalyticsWorkspaceResourceId)
  ? monitoring.outputs.logAnalyticsWorkspaceId
  : m365LogAnalyticsWorkspaceResourceId
var logAnalyticsWorkspaceIdSegments = split(logAnalyticsWorkspaceResourceId, '/')
var logAnalyticsWorkspaceSubscriptionId = length(logAnalyticsWorkspaceIdSegments) > 2
  ? logAnalyticsWorkspaceIdSegments[2]
  : subscription().subscriptionId
var logAnalyticsWorkspaceResourceGroup = length(logAnalyticsWorkspaceIdSegments) > 4
  ? logAnalyticsWorkspaceIdSegments[4]
  : resourceGroup().name
var logAnalyticsWorkspaceName = length(logAnalyticsWorkspaceIdSegments) > 8
  ? logAnalyticsWorkspaceIdSegments[8]
  : monitoring.outputs.logAnalyticsWorkspaceName

var optionalGpt4oDeployment = gpt4oCapacity > 0
  ? [
      {
        name: 'gpt-4o'
        modelName: 'gpt-4o'
        modelVersion: '2024-08-06'
        modelPublisherFormat: 'OpenAI'
        skuName: 'GlobalStandard'
        capacity: gpt4oCapacity
      }
    ]
  : []

var optionalTextEmbedding3LargeDeployment = textEmbedding3LargeCapacity > 0
  ? [
      {
        name: 'text-embed-3-large'
        modelName: 'text-embedding-3-large'
        modelVersion: '1'
        modelPublisherFormat: 'OpenAI'
        skuName: 'GlobalStandard'
        capacity: textEmbedding3LargeCapacity
      }
    ]
  : []

var optionalTextEmbedding3SmallDeployment = textEmbedding3SmallCapacity > 0
  ? [
      {
        name: 'text-embedding-3-small'
        modelName: 'text-embedding-3-small'
        modelVersion: '1'
        modelPublisherFormat: 'OpenAI'
        skuName: 'Standard'
        capacity: textEmbedding3SmallCapacity
      }
    ]
  : []

// ── Path A: reference pre-existing Foundry (day-2 re-run) ───────────────────
resource foundryExisting 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = if (useExistingFoundry) {
  name: foundryName
}

resource foundryProjectExisting 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = if (useExistingFoundry) {
  name: foundryProjectName
  parent: foundryExisting
}

// ── Path B: create Foundry + project + model deployments (greenfield) ────────
module foundryNew 'modules/foundry-resource.bicep' = if (!useExistingFoundry) {
  name: 'foundry'
  params: {
    name: foundryName
    location: location
    tags: tags
  }
}

module foundryProjectNew 'modules/foundry-project.bicep' = if (!useExistingFoundry) {
  name: 'foundryProject'
  dependsOn: [foundryNew]
  params: {
    foundryName: foundryName
    projectName: foundryProjectName
    displayName: foundryProjectName
    projectDescription: 'AI Foundry project for environment ${environmentName}'
    location: location
    tags: tags
  }
}

module foundryModels 'modules/foundry-models.bicep' = if (!useExistingFoundry) {
  name: 'foundryModels'
  dependsOn: [foundryProjectNew]
  params: {
    foundryName: foundryName
    deployments: concat(
      [
        {
          name: 'gpt-4.1-mini'
          modelName: 'gpt-4.1-mini'
          modelVersion: '2025-04-14'
          modelPublisherFormat: 'OpenAI'
          skuName: 'GlobalStandard'
          capacity: gpt41MiniCapacity
        }
        {
          name: 'gpt-5'
          modelName: 'gpt-5'
          modelVersion: '2025-08-07'
          modelPublisherFormat: 'OpenAI'
          skuName: 'GlobalStandard'
          capacity: 100
        }
      ],
      optionalTextEmbedding3LargeDeployment,
      optionalGpt4oDeployment,
      optionalTextEmbedding3SmallDeployment
    )
  }
}

// ── Unified resolved values (whichever path was taken) ───────────────────────
var resolvedFoundryId = useExistingFoundry ? foundryExisting!.id : foundryNew!.outputs.foundryId
var resolvedProjectPrincipalId = useExistingFoundry
  ? foundryProjectExisting!.identity.principalId
  : foundryProjectNew!.outputs.projectPrincipalId

module monitoring 'modules/monitoring.bicep' = {
  params: {
    location: location
    tags: tags
    namePrefix: namePrefix
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  params: {
    location: location
    tags: tags
    namePrefix: namePrefix
    searchServiceName: searchServiceName
    skuName: searchSkuName
  }
}

module rbac 'modules/rbac.bicep' = {
  params: {
    searchServiceName: aiSearch.outputs.searchName
    projectPrincipalId: resolvedProjectPrincipalId
    userPrincipalId: userPrincipalId
  }
}

module m365Teams 'modules/m365-teams-agent.bicep' = {
  name: 'm365TeamsInfra'
  params: {
    location: location
    tags: tags
    namePrefix: namePrefix
    foundryName: foundryName
    foundryProjectEndpoint: foundryProjectEndpoint
    foundryModelDeploymentName: m365ModelDeploymentName
    foundryAgentId: m365AgentId
    acrName: m365AcrName
    imageTag: m365ImageTag
    serviceImageName: m365ServiceImageName
    botAppId: m365BotAppId
    botTenantId: m365BotTenantId
    botAppType: m365BotAppType
    botAppPassword: m365BotAppPassword
    botName: m365BotName
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    logAnalyticsWorkspaceSubscriptionId: logAnalyticsWorkspaceSubscriptionId
    logAnalyticsWorkspaceResourceGroup: logAnalyticsWorkspaceResourceGroup
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
  }
}

output location string = location
output environmentName string = environmentName
output foundryId string = resolvedFoundryId
output foundryName string = foundryName
output foundryProjectName string = foundryProjectName
output foundryProjectPrincipalId string = resolvedProjectPrincipalId
@secure()
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
output logAnalyticsWorkspaceResourceId string = monitoring.outputs.logAnalyticsWorkspaceId
output logAnalyticsWorkspaceName string = monitoring.outputs.logAnalyticsWorkspaceName
output searchServiceName string = aiSearch.outputs.searchName
output searchServiceId string = aiSearch.outputs.searchId
output searchEndpoint string = aiSearch.outputs.searchEndpoint
output searchServicePrincipalId string = aiSearch.outputs.searchPrincipalId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = m365Teams.outputs.acrLoginServer
output AZURE_CONTAINER_REGISTRY_NAME string = m365Teams.outputs.acrName
output SERVICE_TEAMSBINGAGENT_RESOURCE_ID string = resourceId('Microsoft.App/containerApps', m365Teams.outputs.acaAppName)
