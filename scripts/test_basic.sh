#!/bin/bash

# Basic connectivity test for Codex Umbra
echo "🔬 Testing Codex Umbra Basic Connectivity"
echo "=" * 50

echo "🛡️  Testing The Sentinel..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Sentinel health check passed"
    curl -s http://localhost:8001/health | jq . 2>/dev/null || echo "$(curl -s http://localhost:8001/health)"
else
    echo "❌ Sentinel not responding on port 8001"
fi

echo ""
echo "🎯 Testing The Conductor..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Conductor health check passed"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "$(curl -s http://localhost:8000/health)"
else
    echo "❌ Conductor not responding on port 8000"
fi

echo ""
echo "🔗 Testing Conductor -> Sentinel communication..."
if curl -s http://localhost:8000/api/v1/sentinel/health > /dev/null; then
    echo "✅ Conductor->Sentinel communication works"
    curl -s http://localhost:8000/api/v1/sentinel/health | jq . 2>/dev/null || echo "$(curl -s http://localhost:8000/api/v1/sentinel/health)"
else
    echo "❌ Conductor->Sentinel communication failed"
fi

echo ""
echo "💬 Testing chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "status"}')

if [[ $? -eq 0 && "$CHAT_RESPONSE" != "" ]]; then
    echo "✅ Chat endpoint works"
    echo "$CHAT_RESPONSE" | jq . 2>/dev/null || echo "$CHAT_RESPONSE"
else
    echo "❌ Chat endpoint failed"
fi

echo ""
echo "🎉 Basic connectivity test complete!"