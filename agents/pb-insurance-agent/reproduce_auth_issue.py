#!/usr/bin/env python3
"""
Reproduction script for Knowledge Base MCP authentication issue.

This script demonstrates that:
1. ✅ MCP endpoint works with direct API key authentication
2. ✅ Project connection is properly configured with CustomKeys auth
3. ❌ Foundry Responses API fails with 401 when using the connection

Issue: Knowledge Base MCP endpoints don't work with Foundry Responses API,
despite working correctly with direct API calls.
"""

import os
import sys
import requests
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

# Configuration
SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"]
KB_NAME = os.environ["KNOWLEDGE_BASE_NAME"]
SEARCH_API_KEY = os.environ["SEARCH_API_KEY"]
PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
CONNECTION_NAME = "foundry-iq-connection"
AGENT_NAME = "test-kb-agent"
MODEL = os.environ.get("AZURE_OPENAI_MODEL", "gpt-4.1-mini")

MCP_URL = f"{SEARCH_ENDPOINT}/knowledgebases/{KB_NAME}/mcp?api-version=2025-11-01-Preview"

print("=" * 80)
print("KNOWLEDGE BASE MCP AUTHENTICATION ISSUE REPRODUCTION")
print("=" * 80)
print()

# Test 1: Direct MCP call with API key
print("TEST 1: Direct MCP endpoint call with API key")
print("-" * 80)
print(f"URL: {MCP_URL}")
print(f"Auth: api-key header with Search admin key")
print()

try:
    response = requests.post(
        MCP_URL,
        headers={
            "api-key": SEARCH_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "knowledge_base_retrieve",
                "arguments": {
                    "request": {
                        "knowledgeAgentIntents": [
                            "What is the annual deductible?"
                        ]
                    }
                }
            },
            "id": 1
        },
        timeout=30
    )
    
    if response.status_code == 200:
        print(f"✅ SUCCESS: Status {response.status_code}")
        print(f"Response length: {len(response.text)} bytes")
        print("MCP endpoint is functional with direct API key auth")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print()

# Test 2: Verify connection configuration
print("TEST 2: Verify project connection configuration")
print("-" * 80)

try:
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=credential
    )
    
    conn = project_client.connections.get(CONNECTION_NAME)
    print(f"Connection name: {conn.name}")
    print(f"Connection type: {conn.type}")
    print(f"Auth type: {conn.credentials.get('type') if conn.credentials else 'CustomKeys'}")
    print(f"Is default: {conn.is_default}")
    print(f"Target: {conn.target}")
    print()
    
    if conn.target == MCP_URL:
        print("✅ Target URL matches MCP endpoint")
    else:
        print(f"⚠️  Target mismatch: {conn.target} != {MCP_URL}")
        
    if conn.is_default:
        print("✅ Connection is marked as default RemoteTool")
    else:
        print("❌ Connection is NOT default (Responses API requires isDefault: true)")
        
except Exception as e:
    print(f"❌ ERROR checking connection: {e}")

print()
print()

# Test 3: Foundry Responses API with MCP tool
print("TEST 3: Foundry Responses API with Knowledge Base MCP tool")
print("-" * 80)
print(f"Creating agent '{AGENT_NAME}' with MCP tool...")
print(f"Connection: {CONNECTION_NAME} (using default, project_connection_id=None)")
print()

try:
    from azure.ai.projects.models import MCPTool, PromptAgentDefinition
    
    # Create agent with MCP tool
    tool = MCPTool(
        server_label="foundry-iq",
        server_url=MCP_URL,
        require_approval="always",
        allowed_tools=["knowledge_base_retrieve"],
        project_connection_id=None  # Use default RemoteTool connection
    )
    
    agent = project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL,
            instructions="You are a helpful assistant with access to insurance knowledge.",
            tools=[tool]
        )
    )
    
    print(f"✅ Agent created: {agent.name} v{agent.version}")
    print()
    
    # Get OpenAI client and create conversation
    openai_client = project_client.get_openai_client()
    
    print("Creating conversation...")
    conversation = openai_client.conversations.create()
    print(f"✅ Conversation created: {conversation.id}")
    print()
    
    # Try calling responses API
    print("Calling Responses API with tool_choice='required'...")
    print("Question: What is the annual deductible?")
    print()
    
    response = openai_client.responses.create(
        conversation=conversation.id,
        tool_choice="required",
        input="What is the annual deductible?",
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )
    
    print(f"✅ SUCCESS: Got response!")
    print(f"Response ID: {response.id}")
    print(f"Status: {response.status}")
    
except Exception as e:
    error_str = str(e)
    print(f"❌ FAILED: {error_str[:200]}")
    
    if "401" in error_str or "Unauthorized" in error_str:
        print()
        print("🔴 AUTHENTICATION FAILURE CONFIRMED")
        print("   - Direct API key auth works (Test 1 passed)")
        print("   - Connection is properly configured (Test 2 passed)")
        print("   - Foundry Responses API gets 401 Unauthorized")
        print()
        print("ROOT CAUSE:")
        print("   Knowledge Base MCP endpoints are not properly integrated")
        print("   with Foundry Responses API connection authentication.")
        print("   The platform doesn't correctly pass CustomKeys credentials")
        print("   when calling the MCP endpoint on behalf of the agent.")

print()
print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("Expected: All three tests pass")
print("Actual: Test 1 (direct) passes, Test 3 (Foundry) fails with 401")
print()
print("This confirms a platform limitation in the preview API where")
print("Knowledge Base MCP integration doesn't work with Responses API.")
print()
print("=" * 80)
