#!/bin/bash

# Test script for Codex Umbra web application
# This script tests the web application usability and functionality

set -e

echo "🚀 Starting Codex Umbra Web Application Test"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" &> /dev/null; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        ((FAILED++))
    fi
}

# Function to run a test with output
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -n "Testing: $test_name... "
    
    local output
    output=$(eval "$test_command" 2>&1)
    
    if [[ "$output" =~ $expected_pattern ]]; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        echo "Expected pattern: $expected_pattern"
        echo "Actual output: $output"
        ((FAILED++))
    fi
}

echo "📋 Phase 1: Service Health Checks"
echo "================================="

# Check if services are running
run_test "Conductor service health" "curl -f -s http://localhost:8000/health"
run_test "Sentinel service health" "curl -f -s http://localhost:8000/api/v1/sentinel/health"
run_test "Frontend accessibility" "curl -f -s http://localhost:5173"

echo ""
echo "🔧 Phase 2: API Functionality Tests"
echo "===================================="

# Test basic API functionality
run_test_with_output "Basic chat API" \
    "curl -s -X POST http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"message\":\"Hello\",\"user_id\":\"test\"}'" \
    "response.*timestamp"

run_test_with_output "LLM providers endpoint" \
    "curl -s http://localhost:8000/api/v1/llm/providers" \
    "\[.*\]"

echo ""
echo "💬 Phase 3: Natural Language Processing Tests"
echo "=============================================="

# Test various natural language queries
test_queries=(
    "Hello, how are you today?"
    "What is 2 + 2?"
    "Tell me about the weather"
    "What is the capital of France?"
)

for query in "${test_queries[@]}"; do
    run_test_with_output "Query: '$query'" \
        "curl -s -X POST http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"message\":\"$query\",\"user_id\":\"test\"}' | jq -r '.response'" \
        ".+"
done

echo ""
echo "🌐 Phase 4: Frontend Component Tests"
echo "===================================="

# Check if frontend is properly built and serving
run_test "Frontend serves static files" "curl -f -s http://localhost:5173/assets/"
run_test "Frontend serves main page" "curl -s http://localhost:5173 | grep -q 'Codex Umbra'"

echo ""
echo "⚡ Phase 5: Performance Tests"
echo "============================="

# Basic performance test
echo -n "Testing API response time... "
start_time=$(date +%s%N)
curl -s -X POST http://localhost:8000/api/v1/chat \
    -H 'Content-Type: application/json' \
    -d '{"message":"Quick test","user_id":"perf_test"}' > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

if [ $response_time -lt 10000 ]; then # Less than 10 seconds
    echo -e "${GREEN}PASSED${NC} (${response_time}ms)"
    ((PASSED++))
else
    echo -e "${RED}FAILED${NC} (${response_time}ms - too slow)"
    ((FAILED++))
fi

echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}All tests passed! The web application is working correctly.${NC}"
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}Some tests failed. Please check the issues above.${NC}"
    exit 1
fi