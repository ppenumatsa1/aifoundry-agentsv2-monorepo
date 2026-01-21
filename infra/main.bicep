@description('Location for all resources')
param location string = 'eastus2'

@description('Environment name for resource tags')
param environmentName string = 'dev'

@description('Deploy gpt-4.1-mini model')
param deployGpt41Mini bool = true

@description('Deploy gpt-5 model (requires region/quota support)')
param deployGpt5 bool = true

@description('Deploy text-embedding-3-large model')
param deployTextEmbedding bool = true

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
var foundryName = '${namePrefix}-foundry'
var foundryProjectName = '${namePrefix}-proj'

var gpt41MiniDeployment = {
  name: 'gpt-4.1-mini'
  modelName: 'gpt-4.1-mini'
  modelVersion: ''
  modelPublisherFormat: 'OpenAI'
  skuName: 'GlobalStandard'
  capacity: 1000
}

var gpt5Deployment = {
  name: 'gpt-5'
  modelName: 'gpt-5'
  modelVersion: '2025-08-07'
  modelPublisherFormat: 'OpenAI'
  skuName: 'GlobalStandard'
  capacity: 100
}

var textEmbeddingDeployment = {
  name: 'text-embed-3-large'
  modelName: 'text-embedding-3-large'
  modelVersion: ''
  modelPublisherFormat: 'OpenAI'
  skuName: 'GlobalStandard'
  capacity: 100
}

var modelDeployments = union(
  deployGpt41Mini ? [gpt41MiniDeployment] : [],
  deployGpt5 ? [gpt5Deployment] : [],
  deployTextEmbedding ? [textEmbeddingDeployment] : []
)

module monitoring 'modules/monitoring.bicep' = {
  params: {
    location: location
    tags: tags
    namePrefix: namePrefix
  }
}

module foundry 'modules/foundry-resource.bicep' = {
  params: {
    location: location
    tags: tags
    name: foundryName
  }
}

module foundryProject 'modules/foundry-project.bicep' = {
  params: {
    location: location
    tags: tags
    foundryName: foundry.outputs.foundryName
    projectName: foundryProjectName
    displayName: 'AI Agents'
    projectDescription: 'AI Foundry project for multi-agent workloads.'
  }
}

module foundryModels 'modules/foundry-models.bicep' = {
  params: {
    foundryName: foundry.outputs.foundryName
    deployments: modelDeployments
  }
}

output location string = location
output environmentName string = environmentName
output foundryName string = foundry.outputs.foundryName
output foundryProjectName string = foundryProject.outputs.projectName
output foundryModelDeploymentNames string[] = foundryModels.outputs.deploymentNames
@secure()
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
