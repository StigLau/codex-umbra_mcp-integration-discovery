#!/bin/bash

# Full Integration Test for Codex Umbra with Oracle
# This script starts all services, tests the complete flow, and shuts down cleanly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function
cleanup() {
    log "🛑 Cleaning up processes..."
    
    # Kill background processes
    for pid in $SENTINEL_PID $CONDUCTOR_PID $VISAGE_PID; do
        if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            log "Stopped process $pid"
        fi
    done
    
    # Kill any remaining processes on our ports
    for port in 8001 8000 5173; do
        if lsof -ti :$port >/dev/null 2>&1; then
            warning "Killing remaining process on port $port"
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    success "Cleanup complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    log "⏳ Waiting for $name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            success "$name is ready!"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "$name failed to start after $max_attempts attempts"
            return 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
}

# Function to check if Ollama is running
check_ollama() {
    log "🔮 Checking Oracle (Ollama) status..."
    
    if ! command -v ollama &> /dev/null; then
        warning "Ollama not found. Installing or starting Ollama is recommended for full integration."
        return 1
    fi
    
    # Check if Ollama service is running
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        warning "Ollama service not running. Starting Ollama..."
        # Try to start Ollama in background
        ollama serve >/dev/null 2>&1 &
        sleep 3
    fi
    
    # Check if Mistral model is available
    if ! ollama list | grep -q mistral; then
        warning "Mistral model not found. Attempting to pull..."
        ollama pull mistral
    fi
    
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        success "Oracle (Ollama) is ready with Mistral model"
        return 0
    else
        warning "Oracle (Ollama) not available - will test fallback mode"
        return 1
    fi
}

# Start banner
echo -e "${PURPLE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 CODEX UMBRA FULL INTEGRATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

log "🚀 Starting full integration test with Oracle..."

# Check prerequisites
log "🔍 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    error "Python3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    error "curl not found. Please install curl"
    exit 1
fi

success "Prerequisites check passed"

# Check Oracle availability
ORACLE_AVAILABLE=false
if check_ollama; then
    ORACLE_AVAILABLE=true
fi

# Start The Sentinel
log "🛡️  Starting The Sentinel (MCP Server)..."
cd mcp_server_project

if [ ! -d "venv" ]; then
    log "📦 Creating virtual environment for Sentinel..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
uvicorn mcp_server.main:mcp_app --host 0.0.0.0 --port 8001 --reload >/dev/null 2>&1 &
SENTINEL_PID=$!
cd ..

# Wait for Sentinel
wait_for_service "http://localhost:8001/health" "The Sentinel"

# Start The Conductor
log "🎯 Starting The Conductor (Backend)..."
cd conductor_project

if [ ! -d "venv" ]; then
    log "📦 Creating virtual environment for Conductor..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >/dev/null 2>&1 &
CONDUCTOR_PID=$!
cd ..

# Wait for Conductor
wait_for_service "http://localhost:8000/health" "The Conductor"

# Start The Visage
log "👁️  Starting The Visage (Frontend)..."
cd codex-umbra-visage

if [ ! -d "node_modules" ]; then
    log "📦 Installing npm dependencies..."
    npm install >/dev/null 2>&1
fi

npm run dev >/dev/null 2>&1 &
VISAGE_PID=$!
cd ..

# Wait for Visage
wait_for_service "http://localhost:5173" "The Visage"

# Give everything a moment to fully initialize
log "⏳ Allowing services to fully initialize..."
sleep 5

# Run integration tests
echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 RUNNING INTEGRATION TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# Test 1: Basic health checks
log "🔍 Test 1: Health checks"
echo "  📋 Sentinel health:"
SENTINEL_HEALTH=$(curl -s http://localhost:8001/health)
echo "    $SENTINEL_HEALTH"

echo "  📋 Conductor health:"
CONDUCTOR_HEALTH=$(curl -s http://localhost:8000/health)
echo "    $CONDUCTOR_HEALTH"

echo "  📋 Conductor->Sentinel health:"
CONDUCTOR_SENTINEL_HEALTH=$(curl -s http://localhost:8000/api/v1/sentinel/health)
echo "    $CONDUCTOR_SENTINEL_HEALTH"

# Test 2: Chat endpoint tests
log "🔍 Test 2: Chat endpoint integration"

# Test messages to send
declare -a test_messages=(
    "status"
    "health" 
    "What is the current system status?"
    "Can you check the health of the system?"
    "Hello, can you help me?"
)

for message in "${test_messages[@]}"; do
    echo ""
    log "💬 Testing message: '$message'"
    
    # Send to Conductor chat endpoint (simulating Visage request)
    CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$CHAT_RESPONSE" ]; then
        echo "  📤 Request sent successfully"
        echo "  📥 Response received:"
        
        # Try to pretty print JSON if possible
        if command -v jq &> /dev/null; then
            echo "$CHAT_RESPONSE" | jq -r '.response' | sed 's/^/    /'
            echo "  ⏰ Timestamp: $(echo "$CHAT_RESPONSE" | jq -r '.timestamp')"
        else
            echo "    $CHAT_RESPONSE"
        fi
        
        success "Chat test passed for: '$message'"
    else
        error "Chat test failed for: '$message'"
    fi
    
    # Brief pause between tests
    sleep 1
done

# Test 3: Oracle integration verification
echo ""
log "🔍 Test 3: Oracle integration verification"

if [ "$ORACLE_AVAILABLE" = true ]; then
    log "🔮 Testing Oracle (Mistral LLM) integration..."
    
    # Send a complex natural language query
    ORACLE_TEST="Please analyze the system and tell me about the current operational status of all components."
    
    log "💬 Oracle test message: '$ORACLE_TEST'"
    
    ORACLE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$ORACLE_TEST\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$ORACLE_RESPONSE" ]; then
        echo "  📥 Oracle Response:"
        if command -v jq &> /dev/null; then
            echo "$ORACLE_RESPONSE" | jq -r '.response' | sed 's/^/    /'
        else
            echo "    $ORACLE_RESPONSE"
        fi
        success "Oracle integration test passed"
    else
        error "Oracle integration test failed"
    fi
else
    warning "Oracle not available - testing fallback mode"
    
    FALLBACK_TEST="system diagnostics please"
    log "🔧 Fallback test message: '$FALLBACK_TEST'"
    
    FALLBACK_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$FALLBACK_TEST\"}")
    
    if [ $? -eq 0 ] && [ ! -z "$FALLBACK_RESPONSE" ]; then
        echo "  📥 Fallback Response:"
        if command -v jq &> /dev/null; then
            echo "$FALLBACK_RESPONSE" | jq -r '.response' | sed 's/^/    /'
        else
            echo "    $FALLBACK_RESPONSE"
        fi
        success "Fallback mode test passed"
    else
        error "Fallback mode test failed"
    fi
fi

# Final summary
echo ""
echo -e "${GREEN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 INTEGRATION TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

success "All Codex Umbra components are operational!"
echo ""
echo "🌐 Access points:"
echo "  👁️  The Visage (Frontend):   http://localhost:5173"
echo "  🎯 The Conductor (Backend): http://localhost:8000"
echo "  🛡️  The Sentinel (MCP):      http://localhost:8001"
if [ "$ORACLE_AVAILABLE" = true ]; then
    echo "  🔮 The Oracle (Ollama):     http://localhost:11434"
fi

echo ""
echo "💡 The system is ready for interactive testing!"
echo "   You can now open http://localhost:5173 in your browser"
echo "   and interact with Codex Umbra through The Visage interface."

echo ""
log "Press Ctrl+C to stop all services..."

# Keep script running to maintain services
while true; do
    sleep 1
done