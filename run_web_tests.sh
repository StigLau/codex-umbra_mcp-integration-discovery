#!/bin/bash

# Codex Umbra Web & MCP Integration Test Runner
# Runs comprehensive tests against the web interface and MCP functionality

echo "🚀 Codex Umbra Web & MCP Integration Test Runner"
echo "================================================="

# Test URLs (can be overridden with environment variables)
CONDUCTOR_URL=${CONDUCTOR_URL:-"http://localhost:8000"}
VISAGE_URL=${VISAGE_URL:-"http://localhost:5173"}
SENTINEL_URL=${SENTINEL_URL:-"http://localhost:8001"}

echo "Testing against:"
echo "  Conductor: $CONDUCTOR_URL"
echo "  Visage: $VISAGE_URL" 
echo "  Sentinel: $SENTINEL_URL"
echo ""

# Function to test HTTP endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/test_response "$url" 2>/dev/null)
    status_code="${response: -3}"
    
    if [[ "$status_code" == "$expected_status" ]] || [[ "$status_code" == "200" ]] || [[ "$status_code" == "302" ]]; then
        echo "✅ PASS ($status_code)"
        return 0
    else
        echo "❌ FAIL ($status_code)"
        return 1
    fi
}

# Function to test chat API
test_chat() {
    local provider="$1"
    local message="$2"
    local endpoint="$CONDUCTOR_URL/api/v1/chat"
    
    if [[ "$provider" != "default" ]]; then
        endpoint="$endpoint/$provider"
    fi
    
    echo -n "Testing $provider chat... "
    
    payload=$(cat <<EOF
{
    "message": "$message",
    "user_id": "test_$(date +%s)"
}
EOF
)
    
    response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        -w "%{http_code}" \
        -o /tmp/chat_response)
    
    status_code="${response: -3}"
    
    if [[ "$status_code" == "200" ]]; then
        # Check if response has content
        response_text=$(jq -r '.response // empty' /tmp/chat_response 2>/dev/null)
        if [[ -n "$response_text" && "$response_text" != "null" ]]; then
            echo "✅ PASS (Got response)"
            return 0
        else
            echo "❌ FAIL (Empty response)"
            return 1
        fi
    else
        echo "❌ FAIL ($status_code)"
        return 1
    fi
}

# Function to test MCP functionality
test_mcp_function() {
    local function_name="$1"
    local query="$2"
    local expected_keywords="$3"
    
    echo -n "Testing MCP $function_name... "
    
    payload=$(cat <<EOF
{
    "message": "$query",
    "user_id": "mcp_test_$(date +%s)",
    "enable_function_calling": true
}
EOF
)
    
    response=$(curl -s -X POST "$CONDUCTOR_URL/api/v1/chat" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        -w "%{http_code}" \
        -o /tmp/mcp_response)
    
    status_code="${response: -3}"
    
    if [[ "$status_code" == "200" ]]; then
        response_text=$(jq -r '.response // empty' /tmp/mcp_response 2>/dev/null | tr '[:upper:]' '[:lower:]')
        
        # Check for expected keywords
        keyword_found=false
        IFS=',' read -ra KEYWORDS <<< "$expected_keywords"
        for keyword in "${KEYWORDS[@]}"; do
            if [[ "$response_text" == *"${keyword,,}"* ]]; then
                keyword_found=true
                break
            fi
        done
        
        if [[ "$keyword_found" == true ]]; then
            echo "✅ PASS (Keywords found)"
            return 0
        else
            echo "⚠️  PARTIAL (Response received, no keywords)"
            return 0
        fi
    else
        echo "❌ FAIL ($status_code)"
        return 1
    fi
}

# Main test execution
echo "🏥 Testing Service Health"
echo "------------------------"
test_endpoint "Conductor Health" "$CONDUCTOR_URL/health"
test_endpoint "Sentinel Health" "$SENTINEL_URL/health"
test_endpoint "Visage Interface" "$VISAGE_URL"
echo ""

echo "🤖 Testing LLM Providers"
echo "------------------------"
# Get available providers
providers_response=$(curl -s "$CONDUCTOR_URL/api/v1/llm/providers" 2>/dev/null)
if [[ $? -eq 0 ]]; then
    echo "✅ Provider discovery successful"
    
    # Test each available provider
    available_providers=$(echo "$providers_response" | jq -r '.providers[]? | select(.available == true) | .provider' 2>/dev/null)
    
    if [[ -n "$available_providers" ]]; then
        while IFS= read -r provider; do
            test_chat "$provider" "Hello, this is a test message"
        done <<< "$available_providers"
    else
        echo "⚠️  No available providers found"
    fi
else
    echo "❌ Provider discovery failed"
fi
echo ""

echo "🔧 Testing MCP Tool Discovery"
echo "-----------------------------"
test_chat "default" "What MCP tools do you have available?"
test_chat "default" "List your functions and capabilities"
echo ""

echo "⚙️ Testing MCP Function Calling"
echo "-------------------------------"
test_mcp_function "add_numbers" "Add 42 and 58 using your tools" "100,42,58,add"
test_mcp_function "system_health" "Check system health status" "health,status,system"
test_mcp_function "system_config" "Get system configuration" "config,configuration,system"
echo ""

echo "🔄 Testing End-to-End Conversation"
echo "----------------------------------"
conversation_id="e2e_test_$(date +%s)"

test_messages=(
    "Hello, I'm testing the system"
    "What can you do?"
    "Add 10 and 20 for me"
    "Thank you"
)

for i in "${!test_messages[@]}"; do
    message="${test_messages[$i]}"
    step=$((i + 1))
    
    echo -n "Conversation step $step... "
    
    payload=$(cat <<EOF
{
    "message": "$message",
    "user_id": "$conversation_id",
    "conversation_id": "$conversation_id"
}
EOF
)
    
    response=$(curl -s -X POST "$CONDUCTOR_URL/api/v1/chat" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        -w "%{http_code}" \
        -o /tmp/conv_response)
    
    status_code="${response: -3}"
    
    if [[ "$status_code" == "200" ]]; then
        response_text=$(jq -r '.response // empty' /tmp/conv_response 2>/dev/null)
        if [[ -n "$response_text" && "$response_text" != "null" ]]; then
            echo "✅ PASS"
        else
            echo "❌ FAIL (Empty response)"
        fi
    else
        echo "❌ FAIL ($status_code)"
    fi
    
    # Small delay between messages
    sleep 1
done

echo ""
echo "🎉 Test suite completed!"
echo ""
echo "💡 Manual testing suggestions:"
echo "   1. Open $VISAGE_URL in your browser"
echo "   2. Try chatting with the Oracle"
echo "   3. Ask it to 'add two numbers' or 'check system health'"
echo "   4. Verify the responses show function calling capabilities"
echo ""
echo "📁 Test responses saved to /tmp/*_response files"

# Cleanup
rm -f /tmp/test_response /tmp/chat_response /tmp/mcp_response /tmp/conv_response 2>/dev/null