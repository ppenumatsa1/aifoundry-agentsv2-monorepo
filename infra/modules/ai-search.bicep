@description('Location for all resources')
param location string

@description('Tags applied to all resources')
param tags object

@description('Name prefix used for resource naming')
param namePrefix string

@description('Azure AI Search service name')
param searchServiceName string = '${namePrefix}-search'

@description('Azure AI Search SKU')
param skuName string = 'free'

@description('Search replica count')
param replicaCount int = 1

@description('Search partition count')
param partitionCount int = 1

@description('Public network access setting')
param publicNetworkAccess string = 'Enabled'

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: skuName
  }
  tags: tags
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

output searchId string = search.id
output searchName string = search.name
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output searchPrincipalId string = search.identity.principalId
