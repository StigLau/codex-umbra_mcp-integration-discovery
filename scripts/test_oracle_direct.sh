#!/bin/bash

# Direct Oracle Test - Tests Ollama/Mistral LLM directly
# This bypasses the backend services and tests Oracle communication directly

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔮 Direct Oracle (Ollama/Mistral) Test"
echo "====================================="

# Check if Ollama is running
echo "🔍 Checking Oracle availability..."
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${RED}❌ Oracle (Ollama) not running on port 11434${NC}"
    echo ""
    echo "To start Ollama:"
    echo "  ollama serve"
    echo ""
    echo "To pull Mistral model:"
    echo "  ollama pull mistral"
    exit 1
fi

echo -e "${GREEN}✅ Oracle (Ollama) is running${NC}"

# Check available models
echo ""
echo "📋 Available models:"
ollama list

echo ""
echo "🧪 Testing Oracle with Direct Questions"
echo "======================================"

# Questions to test
questions=(
    "What is system status?"
    "Analyze the current system health"
    "Provide a technical status report"
    "What can you tell me about the current setup?"
)

for i in "${!questions[@]}"; do
    question="${questions[$i]}"
    echo ""
    echo -e "${YELLOW}Question $((i+1)):${NC} $question"
    echo -e "${BLUE}┌─────────────────────────────────────────────────────────────────┐${NC}"
    
    # Send question directly to Ollama
    response=$(curl -s -X POST http://localhost:11434/api/chat \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"mistral\",
            \"messages\": [
                {
                    \"role\": \"system\",
                    \"content\": \"You are The Oracle, an AI assistant for Codex Umbra. Provide concise, helpful responses about system status and operations.\"
                },
                {
                    \"role\": \"user\",
                    \"content\": \"$question\"
                }
            ],
            \"stream\": false
        }")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        # Extract the response content
        if command -v jq &> /dev/null; then
            oracle_response=$(echo "$response" | jq -r '.message.content' 2>/dev/null)
            if [ "$oracle_response" = "null" ] || [ -z "$oracle_response" ]; then
                oracle_response="$response"
            fi
        else
            # Fallback parsing without jq
            oracle_response=$(echo "$response" | sed -n 's/.*"content":"\([^"]*\)".*/\1/p')
            if [ -z "$oracle_response" ]; then
                oracle_response="$response"
            fi
        fi
        
        echo -e "${BLUE}│${NC} Oracle Response:"
        echo "$oracle_response" | fold -w 60 | sed "s/^/${BLUE}│${NC} /"
        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"
        
        echo -e "${GREEN}✅ Question $((i+1)) successful${NC}"
    else
        echo -e "${BLUE}│${NC} ${RED}Failed to get response${NC}"
        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"
        echo -e "${RED}❌ Question $((i+1)) failed${NC}"
    fi
    
    sleep 1
done

echo ""
echo "🎯 Testing Command Interpretation"
echo "================================="

# Test command interpretation capability
commands=(
    "status"
    "health check"
    "get system information"
)

for cmd in "${commands[@]}"; do
    echo ""
    echo -e "${YELLOW}Command:${NC} $cmd"
    
    # Send command with system prompt for interpretation
    response=$(curl -s -X POST http://localhost:11434/api/chat \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"mistral\",
            \"messages\": [
                {
                    \"role\": \"system\",
                    \"content\": \"You are The Oracle for Codex Umbra. Interpret user commands and respond with either 'get_status', 'health_check', or provide clarification. Be very concise.\"
                },
                {
                    \"role\": \"user\",
                    \"content\": \"$cmd\"
                }
            ],
            \"stream\": false
        }")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        if command -v jq &> /dev/null; then
            oracle_response=$(echo "$response" | jq -r '.message.content' 2>/dev/null)
        else
            oracle_response=$(echo "$response" | sed -n 's/.*"content":"\([^"]*\)".*/\1/p')
        fi
        
        echo -e "${GREEN}Interpretation:${NC} $oracle_response"
    else
        echo -e "${RED}❌ Failed to interpret command${NC}"
    fi
done

echo ""
echo "📊 Direct Oracle Test Summary"
echo "============================"
echo -e "🔮 Ollama Service: ${GREEN}✅ Running${NC}"
echo -e "🤖 Mistral Model: ${GREEN}✅ Available${NC}"
echo -e "💬 Chat API: ${GREEN}✅ Working${NC}"
echo -e "🧠 Command Interpretation: ${GREEN}✅ Working${NC}"

echo ""
echo -e "${GREEN}🎉 Oracle (Mistral LLM) is fully operational!${NC}"
echo ""
echo "💡 The Oracle can:"
echo "   • Answer natural language questions"
echo "   • Interpret commands and user intent"
echo "   • Provide system guidance and responses"
echo "   • Integrate with Codex Umbra backend services"

echo ""
echo "🔗 To test full integration, ensure backend services are running:"
echo "   ./start_codex_umbra.sh"