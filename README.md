# Codex Umbra - Phase 4 Implementation Complete

An evolving nexus for system interaction with four interconnected components following the Prime Directive: **Concise, Efficient, Maintainable**.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│ The Visage  │───▶│ Conductor   │───▶│ The Oracle  │    │ The Sentinel│
│ (Frontend)  │    │ (Backend)   │    │ (Mistral)   │    │ (MCP Server)│
│             │    │             │├──▶│ via Ollama  │    │             │
│ React/TS    │    │ FastAPI     │    │             │    │ FastAPI     │
│ Port 5173   │    │ Port 8000   │    │ Port 11434  │    │ Port 8001   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Start All Services
```bash
./start_codex_umbra.sh
```

### Test Basic Connectivity
```bash
./test_basic.sh
```

### Manual Component Startup

#### 1. The Sentinel (MCP Server)
```bash
cd mcp_server_project
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn mcp_server.main:mcp_app --reload --port 8001
```

#### 2. The Conductor (Backend Orchestrator)
```bash
cd conductor_project
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. The Visage (Frontend)
```bash
cd codex-umbra-visage
npm install
npm run dev
```

#### 4. The Oracle (Optional - Mistral via Ollama)
```bash
ollama pull mistral
ollama run mistral
```

## ✅ Phase 4 Features Implemented

### 🔗 End-to-End Integration
- **User Input Flow**: Visage → Conductor → Oracle/Fallback → Sentinel → Response
- **Intelligent Routing**: Oracle interpretation with fallback to pattern matching
- **Error Handling**: Graceful degradation when Oracle unavailable

### 🛠️ Service Communication
- **Conductor ↔ Sentinel**: Health checks, status queries, command execution
- **Conductor ↔ Oracle**: Request interpretation via Ollama API
- **Visage ↔ Conductor**: REST API with proper TypeScript types

### 📊 Testing & Monitoring
- **Health Endpoints**: All services expose `/health` endpoints
- **Integration Testing**: Automated testing scripts
- **Logging**: Comprehensive logging throughout the request flow
- **Error Handling**: Robust error handling with user-friendly messages

## 🎯 Available Commands

### Via The Visage Interface
- **"status"** - Get Sentinel operational status
- **"health"** - Check Sentinel health
- **Any message** - Oracle interprets and routes or provides guidance

### Direct API Testing
```bash
# Check Conductor health
curl http://localhost:8000/health

# Check Sentinel via Conductor
curl http://localhost:8000/api/v1/sentinel/health

# Send chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "status"}'
```

## 🧪 Testing

### Unit Tests
```bash
# Conductor tests
cd conductor_project
pytest

# Sentinel tests  
cd mcp_server_project
pytest
```

### Integration Tests
```bash
# Basic connectivity
./test_basic.sh

# Full integration (requires httpx)
python3 test_integration.py
```

## 🔮 Oracle Integration

The system intelligently uses The Oracle (Mistral LLM) when available:

- **Available**: Uses LLM to interpret user requests and generate structured commands
- **Unavailable**: Falls back to simple pattern matching
- **Graceful Degradation**: System remains functional without Oracle

## 📁 Project Structure

```
mcp-integrator/
├── 📋 CLAUDE.md                    # Claude Code documentation
├── 🚀 start_codex_umbra.sh        # Startup script
├── 🧪 test_basic.sh               # Basic connectivity test
├── 🛡️  mcp_server_project/         # The Sentinel
├── 🎯 conductor_project/          # The Conductor  
├── 👁️  codex-umbra-visage/         # The Visage
└── 📚 docs/                       # Documentation
```

## 🔧 Operational Modes

- **✅ Architect Mode**: System learning and configuration (current)
- **🚧 Running Mode**: Standard operation (ready for Phase 5)
- **🔮 In the Wild Mode**: Autonomous operation (future)

## 🎉 What's Working

1. **Complete Request Flow**: User → Visage → Conductor → Oracle/Fallback → Sentinel → Response
2. **Service Health Monitoring**: All services expose health endpoints
3. **Intelligent Command Interpretation**: Oracle provides natural language understanding
4. **Robust Error Handling**: Graceful degradation and user-friendly error messages
5. **Comprehensive Testing**: Unit tests, integration tests, and manual testing tools
6. **Production-Ready Logging**: Request tracking throughout the system

## 🔮 Next Steps (Phase 5+)

- Enhanced Oracle prompting for complex interactions
- Additional Sentinel capabilities
- Advanced error recovery
- Performance optimization
- Security hardening
- Self-modification capabilities (future)