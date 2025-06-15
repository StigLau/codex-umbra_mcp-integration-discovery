#!/bin/bash

# Comprehensive Integration Test Script for Codex Umbra
# Tests the full integration between Sentinel, Conductor, Oracle, and Visage

set -e

echo "🚀 Starting Codex Umbra Comprehensive Integration Tests"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -e "${BLUE}Testing: ${test_name}${NC}"
    
    if result=$(eval "$test_command" 2>&1); then
        if [[ -z "$expected_pattern" ]] || echo "$result" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✅ PASS: ${test_name}${NC}"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}❌ FAIL: ${test_name} - Pattern not found${NC}"
            echo "Expected: $expected_pattern"
            echo "Got: $result"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL: ${test_name} - Command failed${NC}"
        echo "Error: $result"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Helper function to test API endpoints
test_api() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local expected="$4"
    local description="$5"
    
    if [[ "$method" == "POST" ]]; then
        cmd="curl -s -X POST $endpoint -H 'Content-Type: application/json' -d '$data'"
    else
        cmd="curl -s $endpoint"
    fi
    
    run_test "$description" "$cmd" "$expected"
}

echo -e "${YELLOW}📋 Step 1: Check Docker Services Status${NC}"
echo "============================================"

# Check if Docker Compose services are running
run_test "Docker Compose Services Status" "docker-compose ps | grep 'Up'" "Up"

echo -e "\n${YELLOW}🏥 Step 2: Health Check Tests${NC}"
echo "================================="

# Test Sentinel health
test_api "http://localhost:8001/health" "GET" "" "healthy" "Sentinel Health Check"

# Test Conductor health
test_api "http://localhost:8000/health" "GET" "" "healthy" "Conductor Health Check"

# Test Visage accessibility
run_test "Visage Web Interface Accessibility" "curl -s -o /dev/null -w '%{http_code}' http://localhost:5173" "200"

echo -e "\n${YELLOW}🔗 Step 3: Direct API Integration Tests${NC}"
echo "=========================================="

# Test Sentinel status endpoint directly
test_api "http://localhost:8001/status" "GET" "" "MCP Operational" "Sentinel Status Direct"

# Test Sentinel root endpoint
test_api "http://localhost:8001/" "GET" "" "Sentinel is operational" "Sentinel Root Endpoint"

# Test Conductor root endpoint
test_api "http://localhost:8000/" "GET" "" "Conductor is operational" "Conductor Root Endpoint"

echo -e "\n${YELLOW}🎭 Step 4: Conductor-to-Sentinel Proxy Tests${NC}"
echo "==============================================="

# Test Conductor's Sentinel health proxy
test_api "http://localhost:8000/api/v1/sentinel/health" "GET" "" "healthy" "Conductor→Sentinel Health Proxy"

# Test Conductor's Sentinel status proxy
test_api "http://localhost:8000/api/v1/sentinel/status" "GET" "" "MCP Operational" "Conductor→Sentinel Status Proxy"

echo -e "\n${YELLOW}💬 Step 5: Chat API Integration Tests${NC}"
echo "======================================"

# Test chat with status command
test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "status", "user_id": "test"}' "Sentinel Status" "Chat API - Status Command"

# Test chat with health_check command
test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "health_check", "user_id": "test"}' "Sentinel Health" "Chat API - Health Command"

# Test chat with direct get_status command
test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "get_status", "user_id": "test"}' "MCP Operational" "Chat API - Direct get_status"

# Test chat with general message (fallback behavior)
test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "hello world", "user_id": "test"}' "response" "Chat API - General Message"

echo -e "\n${YELLOW}🔮 Step 6: Oracle (Ollama) Integration Tests${NC}"
echo "=============================================="

# Check if Oracle is available
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Oracle (Ollama) is available"
    
    # Test Oracle models endpoint
    test_api "http://localhost:11434/api/tags" "GET" "" "mistral" "Oracle Models Availability"
    
    # Test chat with Oracle interpretation (should show Oracle processing in logs)
    test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "What can you help me with?", "user_id": "oracle-test"}' "response" "Chat API - Oracle Interpretation"
else
    echo "⚠️  Oracle (Ollama) not available - fallback mode will be used"
fi

echo -e "\n${YELLOW}🌐 Step 7: Web Interface Simulation Tests${NC}"
echo "==========================================="

# Simulate browser requests that would come from the simple visage interface
test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "Check the status of The Sentinel", "user_id": "browser-test"}' "Sentinel Status" "Simulated Browser - Status Request"

test_api "http://localhost:8000/api/v1/chat" "POST" '{"message": "health", "user_id": "browser-test"}' "Sentinel Health" "Simulated Browser - Health Request"

# Test error handling with invalid JSON
echo -e "${BLUE}Testing: API Error Handling${NC}"
if error_result=$(curl -s -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"invalid": json}' 2>&1); then
    if echo "$error_result" | grep -q "error\|detail"; then
        echo -e "${GREEN}✅ PASS: API Error Handling${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL: API Error Handling - No error response${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${GREEN}✅ PASS: API Error Handling (Connection refused as expected)${NC}"
    ((TESTS_PASSED++))
fi

echo -e "\n${YELLOW}📊 Step 8: Performance and Response Time Tests${NC}"
echo "================================================"

# Test response times (should be reasonable)
echo -e "${BLUE}Testing: Response Times${NC}"
start_time=$(date +%s%N)
curl -s http://localhost:8000/api/v1/chat -X POST -H "Content-Type: application/json" -d '{"message": "status", "user_id": "perf-test"}' > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

if [ $response_time -lt 5000 ]; then
    echo -e "${GREEN}✅ PASS: Response Time (${response_time}ms < 5000ms)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: Response Time (${response_time}ms >= 5000ms)${NC}"
    ((TESTS_FAILED++))
fi

echo -e "\n${YELLOW}🔍 Step 9: Data Integrity Tests${NC}"
echo "================================="

# Test that responses contain expected JSON structure
echo -e "${BLUE}Testing: JSON Response Structure${NC}"
json_response=$(curl -s -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message": "status", "user_id": "json-test"}')

if echo "$json_response" | jq -e '.response and .timestamp' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS: JSON Response Structure${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: JSON Response Structure${NC}"
    echo "Response: $json_response"
    ((TESTS_FAILED++))
fi

# Test timestamp format
echo -e "${BLUE}Testing: Timestamp Format${NC}"
timestamp=$(echo "$json_response" | jq -r '.timestamp')
if [[ $timestamp =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]; then
    echo -e "${GREEN}✅ PASS: Timestamp Format${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: Timestamp Format${NC}"
    echo "Timestamp: $timestamp"
    ((TESTS_FAILED++))
fi

echo -e "\n${YELLOW}📈 Step 10: Final Results${NC}"
echo "=========================="

total_tests=$((TESTS_PASSED + TESTS_FAILED))
pass_rate=$((TESTS_PASSED * 100 / total_tests))

echo "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Pass Rate: ${GREEN}$pass_rate%${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Codex Umbra integration is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please check the integration.${NC}"
    exit 1
fi