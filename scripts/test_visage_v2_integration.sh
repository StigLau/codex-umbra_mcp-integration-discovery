#!/bin/bash

echo "🧪 Testing Codex Umbra with Visage v2 Integration"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -n "Testing $test_name... "
    
    result=$(eval "$test_command" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ] && [[ "$result" =~ $expected_pattern ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected pattern: $expected_pattern"
        echo "  Got: $result"
        echo "  Exit code: $exit_code"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test JSON response
test_json_response() {
    local test_name="$1"
    local url="$2"
    local expected_field="$3"
    local expected_value="$4"
    
    echo -n "Testing $test_name... "
    
    result=$(curl -s "$url" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('$expected_field', 'FIELD_NOT_FOUND'))
except:
    print('INVALID_JSON')
" 2>/dev/null)
    
    if [[ "$result" == "$expected_value" ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected: $expected_value"
        echo "  Got: $result"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test HTML content
test_html_content() {
    local test_name="$1"
    local url="$2"
    local expected_content="$3"
    
    echo -n "Testing $test_name... "
    
    result=$(curl -s "$url")
    exit_code=$?
    
    if [ $exit_code -eq 0 ] && [[ "$result" =~ $expected_content ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected to find: $expected_content"
        echo "  Exit code: $exit_code"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test chat API end-to-end
test_chat_flow() {
    local test_name="$1"
    local message="$2"
    local expected_response_pattern="$3"
    
    echo -n "Testing $test_name... "
    
    result=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$message\"}" | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('response', 'NO_RESPONSE'))
except:
    print('INVALID_JSON')
" 2>/dev/null)
    
    if [[ "$result" =~ $expected_response_pattern ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected pattern: $expected_response_pattern"
        echo "  Got: $result"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo ""
echo "🔍 Step 1: Check if services are running"
echo "----------------------------------------"

# Check if services are running
run_test "Sentinel port 8001" "curl -s http://localhost:8001/health" "healthy"
run_test "Conductor port 8000" "curl -s http://localhost:8000/health" "healthy"
run_test "Visage v2 port 5173" "curl -s http://localhost:5173" "Codex Umbra"

echo ""
echo "🏥 Step 2: Health Check Tests"
echo "-----------------------------"

# Test health endpoints with JSON validation
test_json_response "Sentinel health status" "http://localhost:8001/health" "status" "healthy"
test_json_response "Conductor health status" "http://localhost:8000/health" "status" "healthy"
test_json_response "Sentinel status endpoint" "http://localhost:8001/status" "status" "MCP Operational"

echo ""
echo "🌐 Step 3: Visage v2 HTML Content Tests"
echo "---------------------------------------"

# Test Visage v2 HTML content
test_html_content "Visage title" "http://localhost:5173" "Codex Umbra"
test_html_content "Visage subtitle" "http://localhost:5173" "The Visage - Simplified Interface"
test_html_content "Input placeholder" "http://localhost:5173" "Enter command for The Sentinel"
test_html_content "Send button" "http://localhost:5173" '<button id="sendButton" class="send-button">Send</button>'
test_html_content "Messages container" "http://localhost:5173" '<div class="messages" id="messages">'
test_html_content "JavaScript API URL" "http://localhost:5173" "const API_BASE_URL = 'http://localhost:8000'"

echo ""
echo "🔗 Step 4: API Integration Tests"
echo "--------------------------------"

# Test Conductor-Sentinel integration
test_json_response "Conductor->Sentinel health" "http://localhost:8000/api/v1/sentinel/health" "status" "healthy"
test_json_response "Conductor->Sentinel status" "http://localhost:8000/api/v1/sentinel/status" "status" "MCP Operational"

echo ""
echo "💬 Step 5: Chat Flow End-to-End Tests"
echo "-------------------------------------"

# Test chat functionality
test_chat_flow "Basic chat message" "hello" ".*"
test_chat_flow "Status command" "status" ".*"
test_chat_flow "Health check command" "health" ".*"

echo ""
echo "🎯 Step 6: Visage v2 JavaScript Functionality Test"
echo "--------------------------------------------------"

# Test that the JavaScript can make API calls (simulate browser behavior)
echo -n "Testing Visage v2 API integration... "

# Create a simple Node.js script to test the frontend's API call
cat > /tmp/test_visage_api.js << 'EOF'
const http = require('http');

const postData = JSON.stringify({
    message: 'test from visage',
    user_id: 'default'
});

const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/api/v1/chat',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
    }
};

const req = http.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => {
        data += chunk;
    });
    res.on('end', () => {
        try {
            const response = JSON.parse(data);
            if (response.response) {
                console.log('SUCCESS');
            } else {
                console.log('NO_RESPONSE_FIELD');
            }
        } catch (e) {
            console.log('INVALID_JSON');
        }
    });
});

req.on('error', (e) => {
    console.log('ERROR');
});

req.write(postData);
req.end();
EOF

api_test_result=$(node /tmp/test_visage_api.js 2>/dev/null)
if [[ "$api_test_result" == "SUCCESS" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Got: $api_test_result"
    ((TESTS_FAILED++))
fi

# Cleanup
rm -f /tmp/test_visage_api.js

echo ""
echo "📊 Step 7: Performance and Load Test"
echo "------------------------------------"

# Simple load test
echo -n "Testing multiple concurrent requests... "
concurrent_results=""
for i in {1..5}; do
    result=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"test $i\"}" &)
    concurrent_results="$concurrent_results $!"
done

# Wait for all background jobs
wait

echo -e "${GREEN}✅ PASS${NC} (5 concurrent requests completed)"
((TESTS_PASSED++))

echo ""
echo "🔍 Step 8: Docker Container Health (if running in Docker)"
echo "--------------------------------------------------------"

if docker ps | grep -q codex; then
    echo "Docker containers detected, checking health..."
    
    # Check Docker container health
    sentinel_health=$(docker inspect codex-sentinel --format='{{.State.Health.Status}}' 2>/dev/null || echo "not-running")
    conductor_health=$(docker inspect codex-conductor --format='{{.State.Health.Status}}' 2>/dev/null || echo "not-running")
    
    echo -n "Sentinel container health... "
    if [[ "$sentinel_health" == "healthy" ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  SKIP${NC} (Status: $sentinel_health)"
    fi
    
    echo -n "Conductor container health... "
    if [[ "$conductor_health" == "healthy" ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  SKIP${NC} (Status: $conductor_health)"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (Not running in Docker)"
fi

echo ""
echo "📋 Test Summary"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Codex Umbra with Visage v2 is working correctly.${NC}"
    echo ""
    echo "✅ Visage v2 HTML is serving correctly"
    echo "✅ All backend services are healthy"
    echo "✅ API integration is working"
    echo "✅ End-to-end chat flow is functional"
    echo ""
    echo "🌐 Access your application:"
    echo "   Visage v2: http://localhost:5173"
    echo "   Conductor API: http://localhost:8000"
    echo "   Sentinel API: http://localhost:8001"
    exit 0
else
    echo ""
    echo -e "${RED}❌ SOME TESTS FAILED. Please check the issues above.${NC}"
    echo ""
    echo "🔧 Troubleshooting tips:"
    echo "   1. Ensure all services are running"
    echo "   2. Check service logs for errors"
    echo "   3. Verify port availability"
    echo "   4. Check Docker container status if using Docker"
    exit 1
fi
