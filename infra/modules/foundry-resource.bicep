@description('Location for all resources')
param location string

@description('Tags applied to all resources')
param tags object

@description('Azure AI Foundry account name')
param name string

@description('SKU for the Foundry account')
param skuName string = 'S0'

@description('Public network access setting')
param publicNetworkAccess string = 'Enabled'

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: name
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'AIServices'
  sku: {
    name: skuName
  }
  tags: tags
  properties: {
    allowProjectManagement: true
    customSubDomainName: name
    publicNetworkAccess: publicNetworkAccess
  }
}

output foundryId string = foundry.id
output foundryName string = foundry.name
output foundryEndpoint string = foundry.properties.endpoint
