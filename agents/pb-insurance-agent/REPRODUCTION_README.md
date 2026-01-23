# Reproduction Materials

This directory contains scripts and documentation to reproduce the Knowledge Base MCP authentication issue.

## Files

1. **`reproduce_auth_issue.py`** - Automated reproduction script
   - Tests direct MCP endpoint access (works ✅)
   - Verifies connection configuration (works ✅)
   - Tests Foundry Responses API (fails ❌ with 401)

2. **`ISSUE_KB_MCP_AUTH.md`** - Detailed issue documentation
   - Complete environment details
   - Reproduction steps
   - All attempted solutions
   - Root cause analysis

3. **`scripts/test_mcp_with_apikey.py`** - Simple MCP endpoint test
   - Proves MCP endpoint is functional
   - Shows correct API key authentication

## Quick Start

### Prerequisites

```bash
# Ensure .env has required variables
SEARCH_ENDPOINT=https://your-search.search.windows.net
KNOWLEDGE_BASE_NAME=your-kb-name
SEARCH_API_KEY=your-search-admin-key
AZURE_AI_PROJECT_ENDPOINT=https://your-project-endpoint
AZURE_OPENAI_MODEL=gpt-4.1-mini
```

### Run Reproduction

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the reproduction script
python reproduce_auth_issue.py
```

### Expected Output

```
TEST 1: Direct MCP endpoint call with API key
✅ SUCCESS: Status 200
MCP endpoint is functional with direct API key auth

TEST 2: Verify project connection configuration
✅ Target URL matches MCP endpoint
✅ Connection is marked as default RemoteTool

TEST 3: Foundry Responses API with Knowledge Base MCP tool
❌ FAILED: Authentication failed... 401 (Unauthorized)

🔴 AUTHENTICATION FAILURE CONFIRMED
```

## What This Proves

1. **MCP Endpoint Works**: Direct API calls succeed (Test 1 ✅)
2. **Connection Is Correct**: Properly configured as default RemoteTool (Test 2 ✅)
3. **Platform Issue**: Foundry can't authenticate to the MCP endpoint (Test 3 ❌)

The issue is in how Foundry Responses API authenticates to external MCP servers using project connections, not in the MCP endpoint itself or the connection configuration.

## Next Steps

1. Review `ISSUE_KB_MCP_AUTH.md` for complete details
2. Include these files when filing a support ticket
3. Provide subscription/resource details from the documentation

## Alternative Testing

Simple MCP endpoint test (no Foundry involved):

```bash
python scripts/test_mcp_with_apikey.py
```

This proves the Knowledge Base MCP endpoint is fully functional when called directly.
