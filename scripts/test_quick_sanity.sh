#!/bin/bash

# Quick Sanity Check for Codex Umbra Integration
# Verifies basic functionality across all components

echo "🚀 Codex Umbra Quick Sanity Check"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    
    if [[ "$method" == "POST" ]]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
    else
        response=$(curl -s "$url" 2>/dev/null)
    fi
    
    if [[ $? -eq 0 && -n "$response" ]]; then
        echo -e "${GREEN}✅ $name${NC}"
        return 0
    else
        echo -e "${RED}❌ $name${NC}"
        return 1
    fi
}

echo "Testing core services..."

# Basic health checks
test_endpoint "Sentinel Health" "http://localhost:8001/health"
test_endpoint "Conductor Health" "http://localhost:8000/health"
test_endpoint "Visage Interface" "http://localhost:5173"

# Integration tests
test_endpoint "Chat API - Status" "http://localhost:8000/api/v1/chat" "POST" '{"message": "status", "user_id": "sanity"}'
test_endpoint "Chat API - Health" "http://localhost:8000/api/v1/chat" "POST" '{"message": "health_check", "user_id": "sanity"}'

# Oracle availability (optional)
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Oracle (Ollama) Available${NC}"
else
    echo -e "${YELLOW}⚠️  Oracle (Ollama) Not Available - Fallback Mode${NC}"
fi

echo -e "\n${GREEN}🎉 Sanity check complete!${NC}"
echo "Access the interface at: http://localhost:5173"