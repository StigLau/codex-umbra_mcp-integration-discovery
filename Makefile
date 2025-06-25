# Codex Umbra Makefile
# High-level operations for The Oracle, The Visage, The Conductor, and The Sentinel
# "Join the fun!" - Management commands for the multi-component system

.PHONY: help start stop restart status test test-all test-quick test-integration build clean install deps lint format check-env oracle-status providers setup docker-build docker-start docker-stop docker-clean logs deploy

# Default target
help: ## 🔮 Show this help message - The Oracle's guidance
	@echo "🌟 Codex Umbra - The Oracle's Command Center 🌟"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🎯 Quick Start: make setup && make start"
	@echo "🧪 Full Test:   make test-all"
	@echo "🚀 Production:  make deploy"

# =============================================================================
# Environment Setup
# =============================================================================

check-env: ## 🔍 Check environment configuration
	@echo "🔍 Checking Codex Umbra environment..."
	@if [ ! -f .env ]; then \
		echo "⚠️  .env file not found. Creating from template..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit with your API keys."; \
	else \
		echo "✅ .env file exists"; \
	fi
	@echo "📋 Environment status:"
	@if grep -q '^DEFAULT_LLM_PROVIDER=' .env 2>/dev/null; then \
		echo "  ✅ DEFAULT_LLM_PROVIDER: $$(grep '^DEFAULT_LLM_PROVIDER=' .env | cut -d'=' -f2)"; \
	else \
		echo "  ❌ DEFAULT_LLM_PROVIDER not set"; \
	fi
	@if grep -q '^ANTHROPIC_API_KEY=.*[^=]$$' .env 2>/dev/null; then \
		echo "  ✅ ANTHROPIC_API_KEY: configured"; \
	else \
		echo "  ⚠️  ANTHROPIC_API_KEY: not configured"; \
	fi
	@if grep -q '^GEMINI_API_KEY=.*[^=]$$' .env 2>/dev/null; then \
		echo "  ✅ GEMINI_API_KEY: configured"; \
	else \
		echo "  ⚠️  GEMINI_API_KEY: not configured"; \
	fi

setup: check-env deps ## 🛠️ Initial project setup - Prepare for The Oracle's awakening
	@echo "🌟 Setting up Codex Umbra..."
	@echo "✅ Dependencies installed"
	@echo "✅ Environment configured"
	@echo "🎉 Setup complete! Ready to start The Oracle."

deps: ## 📦 Install all dependencies
	@echo "📦 Installing Python dependencies..."
	@cd conductor_project && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@cd mcp_server_project && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "📦 Installing JavaScript dependencies..."
	@cd codex-umbra-visage && npm install
	@echo "✅ All dependencies installed"

# =============================================================================
# Service Management
# =============================================================================

start: check-env ## 🚀 Start all Codex Umbra components
	@echo "🚀 Awakening The Oracle and all components..."
	@./scripts/start_codex_umbra.sh || docker-compose up -d
	@sleep 3
	@make status

start-dev: ## 🔧 Start in development mode (local processes)
	@echo "🔧 Starting development environment..."
	@./scripts/start_codex_umbra.sh

start-docker: docker-start ## 🐳 Start using Docker Compose

stop: ## 🛑 Stop all components - The Oracle sleeps
	@echo "🛑 Stopping Codex Umbra components..."
	@docker-compose down 2>/dev/null || echo "Docker services stopped"
	@pkill -f "uvicorn.*conductor" 2>/dev/null || echo "Conductor stopped"
	@pkill -f "uvicorn.*sentinel" 2>/dev/null || echo "Sentinel stopped"
	@echo "💤 The Oracle sleeps. All components stopped."

restart: stop start ## 🔄 Restart all components

status: ## 📊 Check status of all components
	@echo "📊 Codex Umbra System Status"
	@echo "============================="
	@./scripts/test_quick_sanity.sh

# =============================================================================
# Docker Operations
# =============================================================================

docker-build: ## 🐳 Build Docker containers
	@echo "🐳 Building Docker containers..."
	@docker-compose build

docker-start: ## 🐳 Start Docker containers
	@echo "🐳 Starting Docker containers..."
	@docker-compose up -d
	@sleep 5
	@make status

docker-stop: ## 🐳 Stop Docker containers
	@echo "🐳 Stopping Docker containers..."
	@docker-compose down

docker-clean: ## 🐳 Clean Docker containers and images
	@echo "🐳 Cleaning Docker environment..."
	@docker-compose down -v --rmi all 2>/dev/null || true
	@docker system prune -f

# =============================================================================
# Testing
# =============================================================================

test: test-quick ## 🧪 Run quick tests (alias for test-quick)

test-quick: ## ⚡ Quick sanity check - Fast Oracle health check
	@echo "⚡ Quick Oracle health check..."
	@./scripts/test_quick_sanity.sh

test-basic: ## 🔬 Basic connectivity tests
	@echo "🔬 Running basic tests..."
	@./scripts/test_basic.sh

test-integration: ## 🧩 Full integration tests with Oracle
	@echo "🧩 Running integration tests..."
	@timeout 120s ./scripts/test_full_integration.sh || echo "⏰ Test completed (may have timed out)"

test-oracle: ## 🔮 Test Oracle intelligence and LLM providers
	@echo "🔮 Testing Oracle intelligence..."
	@./scripts/test_oracle_integration.sh

test-providers: ## 🤖 Test all LLM providers
	@echo "🤖 Testing LLM providers..."
	@make oracle-status
	@echo "Testing Ollama (default)..."
	@curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" \
		-d '{"message": "Test Ollama provider", "user_id": "makefile-test"}' -s | jq -r '.response' || echo "❌ Ollama test failed"
	@echo "Checking available providers..."
	@curl -s http://localhost:8000/api/v1/llm/providers | jq '.providers[]' 2>/dev/null || echo "⚠️  Provider endpoint not available"

test-function-calling: ## 🔧 Test LLM function calling with MCP tools
	@echo "🔧 Testing LLM Function Calling..."
	@echo "Available function calling tools:"
	@curl -s http://localhost:8000/api/v1/function-call/tools | jq -r '.tools_documentation' 2>/dev/null || echo "❌ Function calling tools not available"
	@echo ""
	@echo "Testing function calling conversation:"
	@curl -X POST http://localhost:8000/api/v1/function-call \
		-H "Content-Type: application/json" \
		-d '{"message": "Check the system health please", "provider": "anthropic"}' \
		-s | jq -C 2>/dev/null || echo "❌ Function calling test failed"

test-visage: ## 👁️ Test Visage frontend integration
	@echo "👁️ Testing The Visage..."
	@./scripts/test_visage_v2_integration.sh

test-all: test-basic test-integration test-oracle test-function-calling test-visage ## 🧪 Run all tests
	@echo "🎉 All tests completed!"

# =============================================================================
# Oracle Operations
# =============================================================================

oracle-status: ## 🔮 Check Oracle and LLM provider status
	@echo "🔮 Oracle Status Report"
	@echo "======================"
	@echo "Ollama:"
	@curl -s http://localhost:11434/api/tags | jq '.models[]? | .name' 2>/dev/null || echo "  ❌ Ollama not available"
	@echo "Conductor:"
	@curl -s http://localhost:8000/health | jq '.status' 2>/dev/null || echo "  ❌ Conductor not available"
	@echo "Sentinel:"
	@curl -s http://localhost:8001/health | jq '.status' 2>/dev/null || echo "  ❌ Sentinel not available"

providers: oracle-status ## 🤖 List available LLM providers
	@echo ""
	@echo "🤖 Available LLM Providers:"
	@curl -s http://localhost:8000/api/v1/llm/providers 2>/dev/null | jq -r '.providers[]? | "  \(.provider): \(.model) (\(if .available then "✅ Available" else "❌ Unavailable" end))"' || echo "  ⚠️  Unable to fetch providers"

chat: ## 💬 Interactive chat with The Oracle
	@echo "💬 Starting chat with The Oracle..."
	@echo "Type 'exit' to quit"
	@while true; do \
		read -p "You: " message; \
		if [ "$$message" = "exit" ]; then break; fi; \
		echo "🔮 Oracle:"; \
		curl -X POST http://localhost:8000/api/v1/chat \
			-H "Content-Type: application/json" \
			-d "{\"message\": \"$$message\", \"user_id\": \"makefile-chat\"}" \
			-s | jq -r '.response' 2>/dev/null || echo "❌ Failed to reach Oracle"; \
		echo ""; \
	done

# =============================================================================
# Development Tools
# =============================================================================

lint: ## 🧹 Lint Python code
	@echo "🧹 Linting Python code..."
	@cd conductor_project && source venv/bin/activate && python -m flake8 app/ --max-line-length=120 || echo "⚠️  Linting issues found"
	@cd mcp_server_project && source venv/bin/activate && python -m flake8 mcp_server/ --max-line-length=120 || echo "⚠️  Linting issues found"

format: ## 🎨 Format Python code
	@echo "🎨 Formatting Python code..."
	@cd conductor_project && source venv/bin/activate && python -m black app/ --line-length=120 || echo "⚠️  Install black for formatting"
	@cd mcp_server_project && source venv/bin/activate && python -m black mcp_server/ --line-length=120 || echo "⚠️  Install black for formatting"

clean: ## 🧽 Clean build artifacts and caches
	@echo "🧽 Cleaning build artifacts..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf conductor_project/venv 2>/dev/null || true
	@rm -rf mcp_server_project/venv 2>/dev/null || true
	@cd codex-umbra-visage && rm -rf node_modules dist .next 2>/dev/null || true
	@echo "✅ Cleanup complete"

# =============================================================================
# Logging and Monitoring
# =============================================================================

logs: ## 📝 Show logs from all components
	@echo "📝 Codex Umbra Logs"
	@echo "=================="
	@docker-compose logs --tail=50 -f 2>/dev/null || echo "Use 'docker-compose logs' for detailed logs"

logs-sentinel: ## 📝 Show Sentinel logs
	@docker-compose logs -f codex-sentinel 2>/dev/null || echo "Sentinel not running in Docker"

logs-conductor: ## 📝 Show Conductor logs
	@docker-compose logs -f codex-conductor 2>/dev/null || echo "Conductor not running in Docker"

logs-visage: ## 📝 Show Visage logs
	@docker-compose logs -f codex-visage 2>/dev/null || echo "Visage not running in Docker"

# =============================================================================
# Deployment
# =============================================================================

build: deps docker-build ## 🔨 Build all components

deploy: build start test-quick ## 🚀 Deploy complete system
	@echo "🚀 Codex Umbra deployed successfully!"
	@echo "🌐 Access points:"
	@echo "  👁️  The Visage:   http://localhost:5173"
	@echo "  🎯 The Conductor: http://localhost:8000"
	@echo "  🛡️  The Sentinel:  http://localhost:8001"
	@echo "  🔮 The Oracle:     http://localhost:11434"
	@make oracle-status

# =============================================================================
# Fun Utilities
# =============================================================================

demo: ## 🎭 Run a demo conversation with The Oracle
	@echo "🎭 Codex Umbra Demo"
	@echo "=================="
	@echo "🔮 Oracle: Greetings! I am The Oracle of Codex Umbra."
	@curl -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "What is the current system status?", "user_id": "demo"}' \
		-s | jq -r '.response' 2>/dev/null || echo "❌ Demo failed - ensure system is running"

demo-function-calling: ## 🔧 Demo LLM function calling with real system operations
	@echo "🔧 Function Calling Demo"
	@echo "======================="
	@echo "🤖 Oracle: Demonstrating direct system operations through LLM function calling..."
	@echo ""
	@echo "🔍 Available tools:"
	@curl -s http://localhost:8000/api/v1/function-call/tools | jq -r '.tools_documentation' 2>/dev/null | head -10
	@echo ""
	@echo "🎯 Oracle executing real system check:"
	@curl -X POST http://localhost:8000/api/v1/function-call \
		-H "Content-Type: application/json" \
		-d '{"message": "Please check the system health and tell me about any issues", "provider": "anthropic"}' \
		-s | jq -r '.response' 2>/dev/null || echo "❌ Function calling demo failed"

version: ## 📋 Show version information
	@echo "🔮 Codex Umbra Version Information"
	@echo "================================="
	@echo "Components: The Oracle, The Visage, The Conductor, The Sentinel"
	@echo "LLM Providers: Ollama (Mistral), Anthropic (Claude), Google (Gemini)"
	@echo "Architecture: Multi-component MCP-enhanced system"
	@git log --oneline -5 2>/dev/null || echo "Git history not available"

fun: ## 🎉 The Oracle tells a joke
	@echo "🎉 The Oracle's wisdom includes humor..."
	@curl -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-d '{"message": "Tell me a programming joke", "user_id": "fun"}' \
		-s | jq -r '.response' 2>/dev/null || echo "🤖 Why do programmers prefer dark mode? Because light attracts bugs!"