#!/bin/bash

# Quick Oracle Integration Test - Tests existing running services
# This script assumes services might already be running and tests them directly

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔮 Quick Oracle Integration Test"
echo "==============================="

# Check if services are running
echo "🔍 Checking service availability..."

# Check Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Oracle (Ollama) is running${NC}"
    ORACLE_OK=true
else
    echo -e "${RED}❌ Oracle (Ollama) not available${NC}"
    ORACLE_OK=false
fi

# Check Conductor
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Conductor is running${NC}"
    CONDUCTOR_OK=true
else
    echo -e "${RED}❌ Conductor not available${NC}"
    CONDUCTOR_OK=false
fi

# Check Sentinel  
if curl -s http://localhost:8001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Sentinel is running${NC}"
    SENTINEL_OK=true
else
    echo -e "${RED}❌ Sentinel not available${NC}"
    SENTINEL_OK=false
fi

echo ""

if [ "$CONDUCTOR_OK" = true ]; then
    echo "🧪 Testing Oracle Integration via Conductor"
    echo "==========================================="
    
    # Test questions
    questions=(
        "What is the system status?"
        "Check the health of the Sentinel"
        "Please provide a status report"
    )
    
    for i in "${!questions[@]}"; do
        question="${questions[$i]}"
        echo ""
        echo -e "${YELLOW}Question $((i+1)):${NC} $question"
        
        # Send request
        response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"$question\"}" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ ! -z "$response" ]; then
            echo -e "${BLUE}Response:${NC}"
            
            # Try to extract response with jq, fallback to basic parsing
            if command -v jq &> /dev/null; then
                oracle_response=$(echo "$response" | jq -r '.response' 2>/dev/null)
                if [ "$oracle_response" != "null" ] && [ ! -z "$oracle_response" ]; then
                    echo "$oracle_response" | fold -w 70 | sed 's/^/  /'
                else
                    echo "$response" | sed 's/^/  /'
                fi
            else
                echo "$response" | sed 's/^/  /'
            fi
            
            echo -e "${GREEN}✅ Success${NC}"
        else
            echo -e "${RED}❌ Failed to get response${NC}"
        fi
    done
    
    echo ""
    echo "🎯 Testing Simple Commands"
    echo "=========================="
    
    simple_commands=("status" "health")
    
    for cmd in "${simple_commands[@]}"; do
        echo ""
        echo -e "${YELLOW}Command:${NC} $cmd"
        
        response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"$cmd\"}" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ ! -z "$response" ]; then
            if command -v jq &> /dev/null; then
                oracle_response=$(echo "$response" | jq -r '.response' 2>/dev/null)
                if [ "$oracle_response" != "null" ] && [ ! -z "$oracle_response" ]; then
                    echo -e "${BLUE}Response:${NC} $oracle_response"
                else
                    echo -e "${BLUE}Response:${NC} $response"
                fi
            else
                echo -e "${BLUE}Response:${NC} $response"
            fi
            echo -e "${GREEN}✅ Success${NC}"
        else
            echo -e "${RED}❌ Failed${NC}"
        fi
    done
    
else
    echo -e "${RED}❌ Cannot test - Conductor not running${NC}"
    echo ""
    echo "To start services, run:"
    echo "  ./start_codex_umbra.sh"
    echo "Or manually start:"
    echo "  cd conductor_project && uvicorn app.main:app --reload --port 8000"
fi

echo ""
echo "📊 Test Summary:"
echo "================"
if [ "$ORACLE_OK" = true ]; then
    echo -e "🔮 Oracle: ${GREEN}✅ Available${NC}"
else
    echo -e "🔮 Oracle: ${RED}❌ Not available${NC}"
fi

if [ "$CONDUCTOR_OK" = true ]; then
    echo -e "🎯 Conductor: ${GREEN}✅ Running${NC}"
else
    echo -e "🎯 Conductor: ${RED}❌ Not running${NC}"
fi

if [ "$SENTINEL_OK" = true ]; then
    echo -e "🛡️  Sentinel: ${GREEN}✅ Running${NC}"
else
    echo -e "🛡️  Sentinel: ${RED}❌ Not running${NC}"
fi

if [ "$ORACLE_OK" = true ] && [ "$CONDUCTOR_OK" = true ] && [ "$SENTINEL_OK" = true ]; then
    echo ""
    echo -e "${GREEN}🎉 Full Oracle integration is working!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Some services need to be started for full integration${NC}"
fi