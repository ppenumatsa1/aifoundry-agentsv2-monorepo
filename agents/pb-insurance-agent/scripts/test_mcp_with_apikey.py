#!/usr/bin/env python3
"""Test script to verify MCP endpoint works with API key authentication."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get Search service details
search_endpoint = os.environ.get("SEARCH_ENDPOINT")
kb_name = os.environ.get("KNOWLEDGE_BASE_NAME")
search_api_key = os.environ.get("SEARCH_API_KEY")

if not all([search_endpoint, kb_name, search_api_key]):
    print("❌ Missing required env vars: SEARCH_ENDPOINT, KNOWLEDGE_BASE_NAME, SEARCH_API_KEY")
    exit(1)

# Build MCP endpoint
mcp_url = f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2025-11-01-Preview"

print(f"Testing MCP endpoint with API key authentication...")
print(f"URL: {mcp_url}")
print(f"Key: {search_api_key[:8]}...{search_api_key[-4:]}")
print()

# Test 1: MCP tools/list
print("Test 1: Calling tools/list...")
try:
    response = requests.post(
        mcp_url,
        headers={
            "api-key": search_api_key,
            "Content-Type": "application/json"
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ tools/list successful!")
        
        # Parse SSE response
        lines = response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                print(f"Response: {data[:200]}...")
                break
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: MCP tools/call with knowledge_base_retrieve
print("Test 2: Calling knowledge_base_retrieve...")
try:
    response = requests.post(
        mcp_url,
        headers={
            "api-key": search_api_key,
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
                            "What is the annual deductible for Northwind Standard plan?"
                        ]
                    }
                }
            },
            "id": 2
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ knowledge_base_retrieve successful!")
        
        # Parse SSE response
        lines = response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                data = line[6:]
                if len(data) > 100:
                    print(f"Response preview: {data[:300]}...")
                else:
                    print(f"Response: {data}")
                break
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("If both tests passed, API key authentication works!")
print("Next: Update connection to use API key instead of MI")
