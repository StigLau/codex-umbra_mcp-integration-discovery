# Oracle Command Translation Enhancement

## Current State vs. Desired State

### Current: Guidance-Based Translation
```
User: "Check system health"
→ Oracle: "I recommend using the system_health tool"
→ Parser: Detects "system_health" in response
→ System: Executes system_health()
→ Result: Combined Oracle advice + real data
```

### Desired: Direct Command Translation
```
User: "Check system health"
→ Intent Parser: health_check_command
→ System: Directly executes system_health()
→ Oracle: Interprets results for user
→ Result: Natural language response with data
```

## Enhancement Opportunities

### 1. Direct Command Mapping
```python
COMMAND_MAPPINGS = {
    # Health commands
    r"(check|show|get).*health": "system_health",
    r"(check|show|get).*status": "system_status",
    r"(show|get|check).*logs": "system_logs",
    
    # Configuration commands
    r"(show|get|list).*config": "system_config",
    r"(change|set|update).*config": "system_config_update",
    
    # Diagnostic commands
    r"(run|execute|start).*diagnostic": "full_diagnostic",
    r"(check|test).*connectivity": "connectivity_test",
}
```

### 2. Structured Command Execution
```python
async def direct_command_translation(user_input: str) -> Optional[Dict[str, Any]]:
    """Directly translate user input to MCP commands"""
    
    # 1. Extract command intent
    command = extract_command_intent(user_input)
    if not command:
        return None
    
    # 2. Parse parameters
    params = extract_command_parameters(user_input)
    
    # 3. Execute MCP command
    result = await execute_mcp_command(command, params)
    
    # 4. Have Oracle interpret results
    interpretation = await oracle_interpret_results(result, user_input)
    
    return {
        "command_executed": command,
        "raw_result": result,
        "oracle_interpretation": interpretation,
        "execution_mode": "direct_translation"
    }
```

### 3. Enhanced Intent Extraction
```python
class CommandExtractor:
    def __init__(self):
        self.patterns = {
            "health_check": [
                r"(check|show|display).*health",
                r"how.*system.*doing",
                r"is.*system.*(ok|healthy|fine)",
            ],
            "status_inquiry": [
                r"(what|show).*status",
                r"(check|get).*current.*state",
                r"how.*running",
            ],
            "log_access": [
                r"(show|get|check|view).*logs",
                r"what.*happened",
                r"(recent|latest).*errors",
            ]
        }
    
    def extract_intent(self, user_input: str) -> Dict[str, Any]:
        """Extract structured command intent"""
        intent = {
            "command": None,
            "parameters": {},
            "modifiers": [],
            "confidence": 0.0
        }
        
        for command_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    intent["command"] = command_type
                    intent["confidence"] = self.calculate_confidence(pattern, user_input)
                    break
        
        return intent
```

### 4. Parameter Extraction
```python
def extract_command_parameters(user_input: str, command: str) -> Dict[str, Any]:
    """Extract parameters for specific commands"""
    params = {}
    
    if command == "health_check":
        # Extract component if specified
        components = ["sentinel", "conductor", "oracle", "visage"]
        for component in components:
            if component in user_input.lower():
                params["component"] = component
                break
        
        # Extract detail level
        if any(word in user_input.lower() for word in ["detailed", "comprehensive", "full"]):
            params["detail_level"] = "comprehensive"
        elif any(word in user_input.lower() for word in ["quick", "basic", "simple"]):
            params["detail_level"] = "basic"
    
    elif command == "log_access":
        # Extract time range
        if "recent" in user_input.lower() or "latest" in user_input.lower():
            params["time_range"] = "recent"
        elif "today" in user_input.lower():
            params["time_range"] = "today"
    
    return params
```

### 5. Hybrid Approach Implementation
```python
async def enhanced_chat_endpoint(message: ChatMessage, mcp_service, llm_service):
    """Enhanced endpoint with direct command translation"""
    
    user_input = message.content
    
    # 1. Try direct command translation first
    direct_result = await direct_command_translation(user_input)
    if direct_result:
        return ChatResponse(
            response=direct_result["oracle_interpretation"],
            command_executed=direct_result["command_executed"],
            execution_mode="direct",
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    # 2. Fall back to Oracle-guided approach
    oracle_result = await llm_service.interpret_user_request_with_mcp(user_input)
    
    return ChatResponse(
        response=oracle_result["response"],
        execution_mode="oracle_guided",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
```

## Implementation Strategy

### Phase 1: Command Pattern Library
- Build regex patterns for common commands
- Map patterns to MCP tool functions
- Add parameter extraction logic

### Phase 2: Direct Execution Pipeline
- Implement command detection before Oracle
- Add structured parameter parsing
- Create direct MCP execution pathway

### Phase 3: Oracle Result Interpretation
- Oracle focuses on explaining results vs. suggesting tools
- Structured data formatting for user consumption
- Context-aware response generation

### Phase 4: Hybrid Intelligence
- Combine direct commands with Oracle reasoning
- Oracle provides insights on command results
- Intelligent fallback between modes

## Benefits of Enhanced Translation

### 1. Faster Response Times
- Direct command execution bypasses LLM overhead
- Immediate system responses for common queries
- Oracle focuses on interpretation vs. discovery

### 2. More Reliable Command Execution
- Explicit command mapping reduces ambiguity
- Consistent parameter handling
- Predictable system behavior

### 3. Better User Experience
- Natural language commands work reliably
- Immediate feedback for system operations
- Oracle provides intelligent context and insights

### 4. Scalable Command Vocabulary
- Easy to add new command patterns
- Modular command handling
- Extensible parameter systems

## Current vs. Enhanced Flow Comparison

### Current Flow
```
"Check health" → Oracle thinks → "Use system_health" → Parser detects → Execute → Combine
Time: ~3-5 seconds, Reliability: Oracle-dependent
```

### Enhanced Flow
```
"Check health" → Direct pattern match → Execute system_health() → Oracle interprets results
Time: ~1-2 seconds, Reliability: Pattern-based + Oracle insights
```

This enhancement would provide the best of both worlds: fast, reliable command execution with intelligent Oracle interpretation of results.