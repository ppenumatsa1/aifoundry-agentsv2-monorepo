# Knowledge Base MCP Authentication Issue

## Issue Summary

Azure AI Foundry Responses API fails to authenticate to Knowledge Base MCP endpoints, despite the MCP endpoints working correctly with direct API authentication. This appears to be a platform limitation in the preview API (2025-11-01-Preview).

**Status**: Blocking end-to-end agent execution  
**Severity**: High - Prevents using Foundry IQ Knowledge Base with Responses API  
**API Version**: 2025-11-01-Preview  
**Region**: eastus2

---

## Environment

- **Azure AI Search**: Basic SKU, system-assigned MI
- **Azure AI Foundry Project**: System-assigned MI (principal ID: `d255b92d-6caf-4f6d-b56b-586e6240bfdb`)
- **Knowledge Base**: `insurance-knowledge-base` (319 document chunks ingested successfully)
- **MCP Endpoint**: `https://aifcfh3y2fxzl3ji-search-basic.search.windows.net/knowledgebases/insurance-knowledge-base/mcp?api-version=2025-11-01-Preview`
- **Connection**: `foundry-iq-connection` (RemoteTool, CustomKeys auth, isDefault: true)

---

## What Works ✅

### 1. Direct MCP Endpoint Access

```bash
curl -X POST "$MCP_ENDPOINT" \
  -H "api-key: $SEARCH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

**Result**: 200 OK, returns `knowledge_base_retrieve` tool

### 2. Knowledge Base Retrieval

```bash
curl -X POST "$MCP_ENDPOINT" \
  -H "api-key: $SEARCH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "knowledge_base_retrieve",
      "arguments": {
        "request": {
          "knowledgeAgentIntents": ["What is the annual deductible?"]
        }
      }
    },
    "id": 2
  }'
```

**Result**: 200 OK, returns relevant document chunks

### 3. Connection Configuration

```bash
az rest --method get \
  --url "https://management.azure.com/.../connections/foundry-iq-connection?api-version=2025-10-01-preview"
```

**Result**: Connection properly configured with:

- `authType`: "CustomKeys"
- `category`: "RemoteTool"
- `isDefault`: true
- `target`: MCP endpoint URL
- `credentials.keys.api-key`: Search admin key

---

## What Fails ❌

### Foundry Responses API with MCP Tool

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition

# Create agent with MCP tool
tool = MCPTool(
    server_label="foundry-iq",
    server_url=MCP_ENDPOINT,
    require_approval="always",
    allowed_tools=["knowledge_base_retrieve"],
    project_connection_id=None  # Use default RemoteTool connection
)

agent = project_client.agents.create_version(
    agent_name="test-agent",
    definition=PromptAgentDefinition(
        model="gpt-4.1-mini",
        instructions="You are a helpful assistant.",
        tools=[tool]
    )
)

# Call Responses API
openai_client = project_client.get_openai_client()
conversation = openai_client.conversations.create()

response = openai_client.responses.create(
    agent_id=agent.name,
    agent_version=agent.version,
    conversation_id=conversation.id,
    input={"query": "What is the annual deductible?"},
    tool_choice="required"
)
```

**Result**:

```
openai.BadRequestError: Error code: 400 - {
  'error': {
    'message': 'Authentication failed when connecting to the MCP server:
                https://aifcfh3y2fxzl3ji-search-basic.search.windows.net:443/knowledgebases/insurance-knowledge-base/mcp:
                Response status code does not indicate success: 401 (Unauthorized).
                Verify your authentication headers.',
    'type': 'invalid_request_error',
    'code': 'tool_user_error'
  }
}
```

---

## Attempted Solutions

### 1. ProjectManagedIdentity Authentication ❌

- Configured connection with `authType: ProjectManagedIdentity`
- Audience: `https://search.azure.com/`
- Granted RBAC roles:
  - Owner on Search service
  - Search Service Contributor
  - Search Index Data Reader
  - Search Index Data Contributor
  - Cognitive Services OpenAI User
- Waited 5+ minutes for RBAC propagation
- **Result**: 401 Unauthorized

### 2. CustomKeys Authentication ❌

- Configured connection with `authType: CustomKeys`
- Credentials: Search admin key in `credentials.keys.api-key`
- Set `isDefault: true` (required for Responses API)
- Deleted and recreated connection to clear cache
- **Result**: Still 401 Unauthorized

### 3. Various Audience/Scope Values ❌

Tried:

- `https://search.azure.com/`
- `https://cognitiveservices.azure.com/`
- `null` (auto-derive)
- **Result**: All failed with 401

---

## Root Cause Analysis

Based on extensive testing, the issue is:

**The Foundry Responses API backend does not properly authenticate to Knowledge Base MCP endpoints when using project connections.**

Evidence:

1. ✅ Direct MCP calls work (proves endpoint is functional)
2. ✅ Connection is properly configured (verified via ARM API)
3. ✅ Both ProjectManagedIdentity and CustomKeys attempted
4. ❌ Foundry backend consistently receives 401 from MCP endpoint

The platform is not correctly:

- Passing CustomKeys credentials when calling the MCP server, OR
- Obtaining/passing valid tokens when using ProjectManagedIdentity

---

## Expected Behavior

When a Foundry agent uses an MCP tool with a project connection:

1. Agent calls Responses API with tool_choice="required"
2. Responses API identifies the MCPTool needs the default RemoteTool connection
3. Responses API retrieves credentials from the connection (API key or MI token)
4. Responses API calls MCP endpoint with proper authentication headers
5. MCP endpoint responds with knowledge retrieval results
6. Agent receives results and formulates response

## Actual Behavior

Steps 1-3 work, but step 4 fails:

- Responses API calls MCP endpoint
- MCP endpoint returns 401 Unauthorized
- Error is surfaced to caller
- Agent execution fails

---

## Reproduction Steps

1. Clone repo or use attached script: `reproduce_auth_issue.py`

2. Set environment variables:

```bash
export SEARCH_ENDPOINT="https://your-search.search.windows.net"
export KNOWLEDGE_BASE_NAME="your-kb-name"
export SEARCH_API_KEY="your-search-admin-key"
export AZURE_AI_PROJECT_ENDPOINT="https://your-project-endpoint"
export AZURE_OPENAI_MODEL="gpt-4.1-mini"
```

3. Ensure Knowledge Base exists:

```bash
# Create index, upload documents, create knowledge source/base
python scripts/ingest_documents.py
```

4. Create project connection:

```bash
az rest --method put \
  --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{foundry}/projects/{project}/connections/foundry-iq-connection?api-version=2025-10-01-preview" \
  --body '{
    "properties": {
      "authType": "CustomKeys",
      "category": "RemoteTool",
      "credentials": {"keys": {"api-key": "your-search-key"}},
      "isDefault": true,
      "target": "https://your-search.search.windows.net/knowledgebases/your-kb/mcp?api-version=2025-11-01-Preview"
    }
  }'
```

5. Run reproduction script:

```bash
python reproduce_auth_issue.py
```

**Expected Output**: All tests pass  
**Actual Output**: Test 1 (direct) passes, Test 3 (Foundry) fails with 401

---

## Workaround

None available. Knowledge Base MCP integration with Foundry Responses API is not functional in the current preview.

Alternative approaches (not tested):

- Implement custom RAG without using Knowledge Base MCP protocol
- Use AI Search vector search directly with azure-search-documents SDK
- Wait for platform fix

---

## Impact

**Blocks**: End-to-end agent scenarios using Foundry IQ Knowledge Base  
**Affected Features**:

- Responses API with MCP tools pointing to Knowledge Base endpoints
- Agent orchestration with knowledge retrieval from KB
- Foundry IQ integration in production workflows

**Timeline**: Preview API (2025-11-01-Preview) - likely will be fixed before GA

---

## Request

Please investigate why Knowledge Base MCP endpoints receive 401 Unauthorized when called by Foundry Responses API, despite:

- MCP endpoints working with direct authentication
- Project connections properly configured with credentials
- Multiple authentication methods attempted (MI and API keys)

This appears to be a gap in the MCP connection integration where the Foundry backend isn't correctly passing authentication headers to external MCP servers.

---

## Contact Information

- **Date**: January 23, 2026
- **Subscription**: 4f18d577-3506-4a11-85e5-a83b14727a84
- **Resource Group**: rg-dev
- **Region**: eastus2
- **Search Service**: aifcfh3y2fxzl3ji-search-basic
- **Foundry Project**: aifcfh3y2fxzl3ji-proj

---

## Additional Files

- `reproduce_auth_issue.py` - Automated reproduction script
- `scripts/test_mcp_with_apikey.py` - Proves MCP endpoint works directly
- `.env` - Environment configuration (search endpoint, KB name, etc.)
