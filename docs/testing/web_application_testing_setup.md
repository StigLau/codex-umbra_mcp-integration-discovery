# Web Application Testing Setup

## Overview

This document describes the comprehensive testing setup implemented for the Codex Umbra web application, including natural language processing tests and automated CI/CD workflows.

## Testing Components

### 1. Frontend Tests (Vitest + React Testing Library)

Located in `codex-umbra-visage/src/test/`:
- **Unit Tests**: Component testing for ChatInput and MessageList
- **E2E Tests**: Full application integration tests
- **Setup**: Configured with jsdom environment and testing library utilities

#### Running Frontend Tests
```bash
cd codex-umbra-visage
npm test          # Run unit tests
npm run test:ui   # Run tests with UI
```

### 2. Natural Language Integration Tests

**File**: `test_natural_language_integration.py`

This comprehensive test suite validates:
- Service health (Conductor, Sentinel)
- LLM provider availability
- Natural language query processing
- Response quality and performance

#### Test Categories
- **Introduction**: Basic system understanding
- **General Query**: Weather, news, etc.
- **Calculation**: Math problems
- **Creative**: Jokes, stories
- **Educational**: Explanations
- **System Specific**: Codex Umbra components

#### Running Natural Language Tests
```bash
# Using virtual environment (recommended)
python3 -m venv test_env
source test_env/bin/activate
pip install -r test_requirements.txt
python test_natural_language_integration.py

# Results saved to: test_results_natural_language.json
```

### 3. Web Application Test Suite

**File**: `test_web_application.sh`

Quick validation script covering:
- Service health checks
- API functionality
- Natural language processing
- Frontend accessibility
- Performance benchmarks

#### Running Web Application Tests
```bash
./test_web_application.sh
```

## GitHub Actions CI/CD

The CI workflow (`.github/workflows/ci.yml`) includes:

### Test Stages
1. **Frontend Tests**: Linting, unit tests, build
2. **Backend Tests**: Python linting, type checking, unit tests
3. **Integration Tests**: Full system testing with natural language validation
4. **Docker Build**: Multi-platform container builds
5. **Security Scanning**: Vulnerability detection

### Key Features
- **Multi-provider LLM Support**: Tests with Ollama, Anthropic, Gemini
- **Natural Language Validation**: Automated testing of conversational AI
- **Performance Monitoring**: Response time tracking
- **Artifact Collection**: Test results and reports

## Test Results

Recent test execution shows:
- **Success Rate**: 100% for natural language queries
- **Average Response Time**: ~11.4 seconds
- **Service Health**: All components operational
- **Keywords Detection**: Proper context understanding

## Dependencies

### Python Testing
```
aiohttp>=3.8.0
asyncio
```

### Frontend Testing
```
vitest
jsdom
@testing-library/react
@testing-library/jest-dom
@testing-library/user-event
@vitest/ui
```

## Configuration

### Environment Variables
- `VITE_API_URL`: Frontend API endpoint
- `DEFAULT_LLM_PROVIDER`: Backend LLM provider
- Test timeouts and thresholds in test files

### Service Requirements
- **Conductor**: http://localhost:8000
- **Sentinel**: http://localhost:8001 (or via Conductor)
- **Frontend**: http://localhost:5173
- **Ollama**: http://localhost:11434 (if using local LLM)

## Monitoring

Test results are automatically:
- Logged with timestamps
- Saved to JSON files
- Uploaded as GitHub Actions artifacts
- Used for pass/fail determination

## Troubleshooting

### Common Issues
1. **Service Not Running**: Check health endpoints
2. **Port Conflicts**: Verify service ports
3. **Timeout Errors**: Increase timeout values
4. **Missing Dependencies**: Install test requirements

### Debug Commands
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/sentinel/health

# Test basic API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","user_id":"debug"}'
```

## Future Enhancements

- Visual regression testing
- Load testing scenarios
- Multi-browser E2E tests
- Automated accessibility testing
- Performance benchmarking