@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name for resource tags')
param environmentName string = 'dev'

@description('Tags applied to all resources')
param tags object = {
  environment: environmentName
  project: 'aifoundry-agentsv2-demo'
}

// TODO: Add Azure AI Foundry / AI Project resources and supporting services.
// This file is intentionally minimal to keep the agent domain self-contained.

output location string = location
output environmentName string = environmentName
