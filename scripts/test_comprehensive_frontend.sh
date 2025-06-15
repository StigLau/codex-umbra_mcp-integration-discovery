#!/bin/bash

# Comprehensive Frontend Test Script for Codex Umbra
# Tests the full stack through the API endpoints

API_BASE="http://localhost:8000/api/v1/chat"
USER_ID="test-user"

echo "🧪 Codex Umbra Comprehensive Frontend Test Suite"
echo "=================================================="
echo ""

# Function to test a command
test_command() {
    local input="$1"
    local expected_pattern="$2"
    local description="$3"
    
    echo "🔍 Testing: $description"
    echo "   Input: '$input'"
    
    response=$(curl -s -X POST "$API_BASE" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$input\",\"user_id\":\"$USER_ID\"}" | jq -r '.response')
    
    echo "   Response: $response"
    
    if echo "$response" | grep -q "$expected_pattern"; then
        echo "   ✅ PASS"
    else
        echo "   ❌ FAIL (Expected pattern: $expected_pattern)"
    fi
    echo ""
    sleep 1
}

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

echo "=== PHASE 1: Basic Command Tests ==="
test_command "status" "Sentinel Status" "Basic status command"
test_command "get_status" "Sentinel Status" "Direct status command"
test_command "health" "Sentinel Health" "Basic health command"
test_command "health check" "Sentinel Health" "Health check command"

echo "=== PHASE 2: Natural Language Tests ==="
test_command "How are you doing?" "Sentinel Health\|Oracle" "Natural language health query"
test_command "What is the system status?" "Sentinel Status\|Oracle" "Natural language status query"
test_command "Tell me about the system" "Oracle\|Sentinel" "System information request"
test_command "Is everything working?" "Sentinel\|Oracle" "General wellness check"

echo "=== PHASE 3: Help and Capability Tests ==="
test_command "What can you do?" "Oracle Guidance\|Oracle Response" "Capability inquiry"
test_command "help" "Oracle Guidance\|Oracle Response" "Help request"
test_command "I need assistance" "Oracle Guidance\|Oracle Response" "Assistance request"

echo "=== PHASE 4: Conversational Tests ==="
test_command "Hello" "Oracle\|Sentinel" "Greeting"
test_command "Thank you" "Oracle Response" "Gratitude expression"
test_command "Good morning" "Oracle\|Sentinel" "Time-based greeting"

echo "=== PHASE 5: Edge Case Tests ==="
test_command "xyz123invalid" "Oracle Response" "Invalid command"
test_command "!@#$%^&*()" "Oracle Response" "Special characters"
test_command "How is the Sentinel doing today?" "Sentinel Health\|Oracle" "Complex health query"

echo "=== PHASE 6: System Diagnostic Tests ==="
test_command "System diagnostic" "Oracle\|Sentinel" "Diagnostic request"
test_command "Check all systems" "Oracle\|Sentinel" "Comprehensive check"
test_command "Is the MCP operational?" "Sentinel Status\|Oracle" "MCP-specific query"

echo "=============================================="
echo "🎯 Test Suite Complete!"
echo ""
echo "Expected Results:"
echo "✅ Status commands should return 'Sentinel Status: MCP Operational'"
echo "✅ Health commands should return 'Sentinel Health: healthy'"  
echo "✅ Help queries should return 'Oracle Guidance: ...' with helpful info"
echo "✅ Complex queries should return 'Oracle Response: ...' with interpretations"
echo "✅ Invalid input should be handled gracefully by Oracle"
echo ""
echo "Frontend Testing: Visit http://localhost:5173 and try these commands!"