#!/usr/bin/env python3
"""
Integration test script for Codex Umbra Phase 4
Tests the connection between Visage -> Conductor -> Sentinel
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
CONDUCTOR_URL = "http://localhost:8000"
SENTINEL_URL = "http://localhost:8001"

async def test_sentinel_health():
    """Test The Sentinel health endpoint"""
    print("🔍 Testing The Sentinel health...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SENTINEL_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sentinel Health: {data.get('status')}")
                return True
            else:
                print(f"❌ Sentinel Health failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Sentinel connection failed: {e}")
        return False

async def test_conductor_health():
    """Test The Conductor health endpoint"""
    print("🔍 Testing The Conductor health...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CONDUCTOR_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conductor Health: {data.get('status')}")
                return True
            else:
                print(f"❌ Conductor Health failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Conductor connection failed: {e}")
        return False

async def test_conductor_to_sentinel():
    """Test Conductor -> Sentinel communication"""
    print("🔍 Testing Conductor -> Sentinel communication...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CONDUCTOR_URL}/api/v1/sentinel/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conductor->Sentinel: {data.get('status')}")
                return True
            else:
                print(f"❌ Conductor->Sentinel failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Conductor->Sentinel communication failed: {e}")
        return False

async def test_chat_endpoint():
    """Test the main chat endpoint (Visage -> Conductor flow)"""
    print("🔍 Testing chat endpoint...")
    test_messages = [
        "status",
        "health", 
        "Hello Sentinel"
    ]
    
    for message in test_messages:
        try:
            async with httpx.AsyncClient() as client:
                payload = {"text": message, "user_id": "test"}
                response = await client.post(
                    f"{CONDUCTOR_URL}/api/v1/chat",
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Chat '{message}': {data.get('response')[:50]}...")
                else:
                    print(f"❌ Chat '{message}' failed: HTTP {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Chat endpoint failed: {e}")
            return False
    
    return True

async def main():
    """Run all integration tests"""
    print("🚀 Starting Codex Umbra Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Sentinel Health", test_sentinel_health),
        ("Conductor Health", test_conductor_health),
        ("Conductor->Sentinel", test_conductor_to_sentinel),
        ("Chat Endpoint", test_chat_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! Codex Umbra is operational.")
    else:
        print("\n⚠️  Some tests failed. Check service status.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())