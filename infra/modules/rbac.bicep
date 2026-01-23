@description('Azure AI Search service name')
param searchServiceName string

@description('Azure AI Search system-assigned principal ID')
param searchPrincipalId string

@description('Azure AI Foundry account name')
param foundryName string

@description('Azure AI Foundry project name')
param foundryProjectName string

@description('Foundry project system-assigned principal ID')
param projectPrincipalId string

@description('User principal ID for admin role assignments')
param userPrincipalId string = ''

@description('Role definition ID for Search Service Contributor')
param searchServiceContributorRoleId string = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'

@description('Role definition ID for Search Index Data Contributor')
param searchIndexDataContributorRoleId string = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'

@description('Role definition ID for Search Index Data Reader')
param searchIndexDataReaderRoleId string = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

@description('Role definition ID for Cognitive Services User')
param cognitiveServicesUserRoleId string = 'a97b65f3-24c7-4388-baec-2e87135dc908'

@description('Role definition ID for Azure AI User')
param azureAiUserRoleId string = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

@description('Role definition ID for Azure AI Project Manager')
param azureAiProjectManagerRoleId string = 'eadc314b-1a2d-4efa-be10-5d325db5065e'

resource search 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
  scope: resourceGroup()
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryName
  scope: resourceGroup()
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  name: foundryProjectName
  parent: foundry
}

var assignUserRoles = userPrincipalId != ''

resource projectSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, projectPrincipalId, searchServiceContributorRoleId)
  scope: search
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource projectSearchDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, projectPrincipalId, searchIndexDataContributorRoleId)
  scope: search
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource projectSearchDataReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, projectPrincipalId, searchIndexDataReaderRoleId)
  scope: search
  properties: {
    principalId: projectPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataReaderRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource searchCognitiveServicesUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, searchPrincipalId, cognitiveServicesUserRoleId)
  scope: foundry
  properties: {
    principalId: searchPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource userSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(search.id, userPrincipalId, searchServiceContributorRoleId)
  scope: search
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
    principalType: 'User'
  }
}

resource userSearchDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(search.id, userPrincipalId, searchIndexDataContributorRoleId)
  scope: search
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
    principalType: 'User'
  }
}

resource userSearchDataReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(search.id, userPrincipalId, searchIndexDataReaderRoleId)
  scope: search
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataReaderRoleId)
    principalType: 'User'
  }
}

resource userAzureAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(foundryProject.id, userPrincipalId, azureAiUserRoleId)
  scope: foundryProject
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
    principalType: 'User'
  }
}

resource userAzureAiProjectManager 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(foundryProject.id, userPrincipalId, azureAiProjectManagerRoleId)
  scope: foundryProject
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiProjectManagerRoleId)
    principalType: 'User'
  }
}
