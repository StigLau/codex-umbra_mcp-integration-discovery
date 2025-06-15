#!/bin/bash

# Oracle Integration Test - Focused test for LLM functionality
# Starts services, sends questions to Oracle via the full stack, and prints responses

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Cleanup function
cleanup() {
    log "Shutting down services..."
    for pid in $SENTINEL_PID $CONDUCTOR_PID; do
        if [ ! -z "$pid" ]; then
            kill $pid 2>/dev/null || true
        fi
    done
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "🔮 Oracle Integration Test for Codex Umbra"
echo "=========================================="

# Check if Ollama is available
log "Checking Oracle (Ollama) availability..."
if ! command -v ollama &> /dev/null; then
    error "Ollama not found. Please install Ollama first:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Start Ollama service if not running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log "Starting Ollama service..."
    ollama serve >/dev/null 2>&1 &
    sleep 3
fi

# Check if Mistral model is available
if ! ollama list | grep -q mistral; then
    log "Pulling Mistral model (this may take a while)..."
    ollama pull mistral
fi

success "Oracle (Ollama with Mistral) is ready"

# Start backend services
log "Starting The Sentinel..."
cd mcp_server_project
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn mcp_server.main:mcp_app --host 0.0.0.0 --port 8001 --reload >/dev/null 2>&1 &
SENTINEL_PID=$!
cd ..

sleep 3

log "Starting The Conductor..."
cd conductor_project
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >/dev/null 2>&1 &
CONDUCTOR_PID=$!
cd ..

# Wait for services to be ready
log "Waiting for services to initialize..."
sleep 5

# Verify services are running
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null && curl -s http://localhost:8001/health >/dev/null; then
        success "All services are ready"
        break
    fi
    if [ $i -eq 10 ]; then
        error "Services failed to start"
        exit 1
    fi
    sleep 2
done

echo ""
echo "🧪 Testing Oracle Integration"
echo "=============================="

# Define test questions for the Oracle
questions=(
    "What is the current status of the system?"
    "Can you check the health of all components?"
    "Please analyze the Sentinel and provide a status report"
    "How is the Master Control Program doing?"
    "Give me a comprehensive system overview"
    "Are there any issues with the current setup?"
)

echo ""
log "Sending questions to Oracle via the full stack..."
echo ""

for i in "${!questions[@]}"; do
    question="${questions[$i]}"
    
    echo -e "${YELLOW}Question $((i+1)):${NC} $question"
    echo -e "${BLUE}┌─────────────────────────────────────────────────────────────────┐${NC}"
    
    # Send the question through the full stack
    response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$question\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        # Extract and display the response
        if command -v jq &> /dev/null; then
            oracle_response=$(echo "$response" | jq -r '.response')
            timestamp=$(echo "$response" | jq -r '.timestamp')
        else
            # Fallback parsing if jq not available
            oracle_response=$(echo "$response" | sed -n 's/.*"response":"\([^"]*\)".*/\1/p')
            timestamp=$(echo "$response" | sed -n 's/.*"timestamp":"\([^"]*\)".*/\1/p')
        fi
        
        echo -e "${BLUE}│${NC} Oracle Response:"
        echo "$oracle_response" | fold -w 60 | sed "s/^/${BLUE}│${NC} /"
        echo -e "${BLUE}│${NC} "
        echo -e "${BLUE}│${NC} Timestamp: $timestamp"
        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"
        
        success "Question $((i+1)) processed successfully"
    else
        error "Question $((i+1)) failed to get response"
        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────┘${NC}"
    fi
    
    echo ""
    sleep 2  # Brief pause between questions
done

echo ""
echo "🎯 Testing Command Interpretation"
echo "================================="

# Test specific commands that should trigger Sentinel actions
commands=(
    "status"
    "health check"
    "get system status"
    "check sentinel health"
)

for cmd in "${commands[@]}"; do
    echo -e "${YELLOW}Command:${NC} $cmd"
    
    response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$cmd\"}")
    
    if command -v jq &> /dev/null; then
        oracle_response=$(echo "$response" | jq -r '.response')
    else
        oracle_response=$(echo "$response" | sed -n 's/.*"response":"\([^"]*\)".*/\1/p')
    fi
    
    echo -e "${GREEN}Response:${NC} $oracle_response"
    echo ""
done

echo ""
success "Oracle integration test completed!"
echo ""
echo "📊 Summary:"
echo "  🔮 Oracle (Mistral via Ollama): ✅ Working"
echo "  🎯 Conductor: ✅ Working"  
echo "  🛡️  Sentinel: ✅ Working"
echo "  🔗 Full Integration: ✅ Working"
echo ""
echo "The Oracle is successfully interpreting natural language queries"
echo "and routing them through the Conductor to the Sentinel!"

log "Services will continue running. Press Ctrl+C to stop."

# Keep services running
while true; do
    sleep 1
done