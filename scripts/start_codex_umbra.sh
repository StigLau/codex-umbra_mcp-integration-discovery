#!/bin/bash

# Codex Umbra Startup Script for Phase 4 Testing
echo "🚀 Starting Codex Umbra System..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check ports
if ! check_port 8000; then
    echo "❌ Port 8000 (Conductor) is in use"
    exit 1
fi

if ! check_port 8001; then
    echo "❌ Port 8001 (Sentinel) is in use"
    exit 1
fi

if ! check_port 5173; then
    echo "❌ Port 5173 (Visage) is in use"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Start The Sentinel (MCP Server)
echo "🛡️  Starting The Sentinel (MCP Server) on port 8001..."
cd mcp_server_project
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment for Sentinel..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn mcp_server.main:mcp_app --host 0.0.0.0 --port 8001 --reload &
SENTINEL_PID=$!
cd ..

# Wait for Sentinel to start
sleep 3

# Start The Conductor (Backend Orchestrator)
echo "🎯 Starting The Conductor (Backend) on port 8000..."
cd conductor_project
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment for Conductor..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
CONDUCTOR_PID=$!
cd ..

# Wait for Conductor to start
sleep 3

# Start The Visage (Frontend)
echo "👁️  Starting The Visage (Frontend) on port 5173..."
cd codex-umbra-visage
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi
npm run dev &
VISAGE_PID=$!
cd ..

# Wait for all services to initialize
echo "⏳ Waiting for all services to initialize..."
sleep 5

echo ""
echo "🎉 Codex Umbra is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  The Sentinel (MCP):       http://localhost:8001"
echo "🎯 The Conductor (Backend):  http://localhost:8000"
echo "👁️  The Visage (Frontend):    http://localhost:5173"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Quick test commands:"
echo "   curl http://localhost:8001/health"
echo "   curl http://localhost:8000/health"
echo "   curl -X POST http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"message\":\"status\"}'"
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Codex Umbra services..."
    kill $SENTINEL_PID 2>/dev/null
    kill $CONDUCTOR_PID 2>/dev/null
    kill $VISAGE_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait