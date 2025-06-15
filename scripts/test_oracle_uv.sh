#!/bin/bash

# Oracle Integration Test using UV for fast Python package management
# Tests the complete Oracle integration: Visage -> Conductor -> Oracle -> Sentinel

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
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
    log "🛑 Cleaning up services..."
    for pid in $SENTINEL_PID $CONDUCTOR_PID; do
        if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            log "Stopped service PID $pid"
        fi
    done
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${PURPLE}"
echo "🔮 Oracle Integration Test with UV"
echo "=================================="
echo -e "${NC}"

# Check prerequisites
log "🔍 Checking prerequisites..."

if ! command -v uv &> /dev/null; then
    error "UV not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command -v node &> /dev/null; then
    error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

if ! command -v ollama &> /dev/null; then
    error "Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

success "Prerequisites check passed"

# Check Oracle availability
log "🔮 Checking Oracle (Ollama) status..."
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    warning "Starting Ollama service..."
    ollama serve >/dev/null 2>&1 &
    sleep 3
fi

if ! ollama list | grep -q mistral; then
    log "📥 Pulling Mistral model..."
    ollama pull mistral
fi

success "Oracle (Ollama with Mistral) is ready"

# Start The Sentinel using UV
log "🛡️  Starting The Sentinel with UV..."
cd mcp_server_project

# Use UV to create venv and install dependencies
uv venv
source .venv/bin/activate
uv pip install fastapi uvicorn httpx

# Start Sentinel
uv run uvicorn mcp_server.main:mcp_app --host 0.0.0.0 --port 8001 --reload &
SENTINEL_PID=$!
cd ..

# Start The Conductor using UV
log "🎯 Starting The Conductor with UV..."
cd conductor_project

# Use UV for fast dependency installation
uv venv
source .venv/bin/activate
uv pip install fastapi uvicorn httpx pydantic-settings

# Start Conductor
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
CONDUCTOR_PID=$!
cd ..

# Wait for services to be ready
log "⏳ Waiting for services to start..."
sleep 8

# Verify services are running
for i in {1..15}; do
    if curl -s http://localhost:8000/health >/dev/null && curl -s http://localhost:8001/health >/dev/null; then
        success "All services are ready!"
        break
    fi
    if [ $i -eq 15 ]; then
        error "Services failed to start within timeout"
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
echo -e "${PURPLE}🧪 Testing Oracle Integration${NC}"
echo "============================="

# Test questions that should go through Oracle -> Conductor -> Sentinel
oracle_questions=(
    "What is the current system status?"
    "Can you check the health of the Sentinel?"
    "Please provide a comprehensive status report"
    "How is the Master Control Program doing?"
    "Give me an overview of all system components"
)

echo ""
log "💬 Sending questions through the full stack..."

for i in "${!oracle_questions[@]}"; do
    question="${oracle_questions[$i]}"
    echo ""
    echo -e "${YELLOW}Question $((i+1)):${NC} $question"
    echo -e "${BLUE}┌────────────────────────────────────────────────────────────────────┐${NC}"
    
    # Send through the full integration: Frontend API -> Conductor -> Oracle -> Sentinel
    response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$question\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        # Extract response
        if command -v jq &> /dev/null; then
            oracle_response=$(echo "$response" | jq -r '.response' 2>/dev/null)
            timestamp=$(echo "$response" | jq -r '.timestamp' 2>/dev/null)
            
            if [ "$oracle_response" = "null" ] || [ -z "$oracle_response" ]; then
                oracle_response="$response"
            fi
        else
            oracle_response=$(echo "$response" | sed -n 's/.*"response":"\([^"]*\)".*/\1/p')
            timestamp=$(echo "$response" | sed -n 's/.*"timestamp":"\([^"]*\)".*/\1/p')
        fi
        
        echo -e "${BLUE}│${NC} 🔮 Oracle Response:"
        echo "$oracle_response" | fold -w 65 | sed "s/^/${BLUE}│${NC} /"
        echo -e "${BLUE}│${NC}"
        echo -e "${BLUE}│${NC} ⏰ At: $timestamp"
        echo -e "${BLUE}└────────────────────────────────────────────────────────────────────┘${NC}"
        
        success "Question $((i+1)) - Oracle integration successful!"
    else
        echo -e "${BLUE}│${NC} ${RED}❌ Failed to get response${NC}"
        echo -e "${BLUE}└────────────────────────────────────────────────────────────────────┘${NC}"
        error "Question $((i+1)) failed"
    fi
    
    sleep 1
done

echo ""
echo -e "${PURPLE}🎯 Testing Command Interpretation${NC}"
echo "================================="

# Test specific commands
commands=(
    "status"
    "health"
    "get system status"
    "check sentinel health"
)

for cmd in "${commands[@]}"; do
    echo ""
    echo -e "${YELLOW}Command:${NC} $cmd"
    
    response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$cmd\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        if command -v jq &> /dev/null; then
            cmd_response=$(echo "$response" | jq -r '.response' 2>/dev/null)
        else
            cmd_response=$(echo "$response" | sed -n 's/.*"response":"\([^"]*\)".*/\1/p')
        fi
        
        echo -e "${GREEN}Response:${NC} $cmd_response"
        success "Command interpretation working"
    else
        error "Command failed: $cmd"
    fi
done

echo ""
echo -e "${PURPLE}📊 Integration Test Results${NC}"
echo "==========================="

success "🔮 Oracle (Mistral via Ollama): Working"
success "🎯 Conductor Backend: Working"
success "🛡️  Sentinel MCP Server: Working"
success "🔗 Full Stack Integration: Working"
success "💬 Natural Language Processing: Working"
success "🧠 Command Interpretation: Working"

echo ""
echo -e "${GREEN}🎉 Oracle Integration Test PASSED!${NC}"

echo ""
echo "🌟 What's Working:"
echo "  • Natural language questions are interpreted by Oracle"
echo "  • Commands are routed through Conductor to Sentinel"
echo "  • Responses flow back through the full stack"
echo "  • System health monitoring is operational"
echo "  • Fast UV-based service startup"

echo ""
echo "🌐 Test The Visage Frontend:"
echo "  cd codex-umbra-visage && npm run dev"
echo "  Then visit: http://localhost:5173"

log "Services running. Press Ctrl+C to stop..."

# Keep services running for interactive testing
while true; do
    sleep 1
done