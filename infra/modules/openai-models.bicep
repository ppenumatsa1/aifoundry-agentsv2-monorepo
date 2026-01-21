type ModelDeployment = {
  @description('Deployment name')
  name: string

  @description('Model name')
  modelName: string

  @description('Optional model version')
  modelVersion: string

  @description('SKU name for the deployment')
  skuName: string

  @description('Capacity for the deployment')
  capacity: int
}

@description('Location for all resources')
param location string

@description('Tags applied to all resources')
param tags object

@description('Azure OpenAI account name')
param accountName string

@description('SKU for the OpenAI account')
param accountSkuName string = 'S0'

@description('Model deployments')
param deployments ModelDeployment[]

@description('Public network access setting')
param publicNetworkAccess string = 'Enabled'

resource openai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  kind: 'OpenAI'
  sku: {
    name: accountSkuName
  }
  tags: tags
  properties: {
    publicNetworkAccess: publicNetworkAccess
  }
}

@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for deployment in deployments: {
  name: deployment.name
  parent: openai
  sku: {
    name: deployment.skuName
    capacity: deployment.capacity
  }
  properties: {
    model: deployment.modelVersion != '' ? {
      format: 'OpenAI'
      name: deployment.modelName
      version: deployment.modelVersion
    } : {
      format: 'OpenAI'
      name: deployment.modelName
    }
  }
}]

output openaiAccountId string = openai.id
output openaiEndpoint string = openai.properties.endpoint
output deploymentNames string[] = [for deployment in deployments: deployment.name]
