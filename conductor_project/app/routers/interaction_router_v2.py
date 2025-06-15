"""
Enhanced Interaction Router for The Conductor
Full MCP integration with dynamic tool discovery and intelligent routing
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
import logging
import asyncio
from typing import Dict, Any, Optional

from app.schemas.request_schemas import ChatMessage, ChatResponse
from app.services.mcp_service_v2 import MCPServiceV2
from app.services.llm_service_v2 import LLMServiceV2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["interaction"])

# Service instances with enhanced MCP capabilities
def get_mcp_service() -> MCPServiceV2:
    return MCPServiceV2()

def get_llm_service() -> LLMServiceV2:
    return LLMServiceV2()

@router.post("/chat", response_model=ChatResponse)
async def enhanced_chat_endpoint(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    mcp_service: MCPServiceV2 = Depends(get_mcp_service),
    llm_service: LLMServiceV2 = Depends(get_llm_service)
):
    """
    Enhanced chat endpoint with full MCP integration
    Features dynamic tool discovery, intelligent routing, and context-aware responses
    """
    try:
        user_input = message.content
        user_id = message.user_id
        
        logger.info(f"🎯 Enhanced Chat Request: '{user_input}' from user: {user_id}")
        
        # Check LLM availability
        llm_available = await llm_service.is_available()
        logger.info(f"🔮 Oracle available: {llm_available}")
        
        if llm_available:
            # Use enhanced MCP-aware LLM service
            response_data = await _handle_mcp_enhanced_request(user_input, mcp_service, llm_service)
        else:
            # Fallback to direct MCP interaction
            response_data = await _handle_direct_mcp_request(user_input, mcp_service)
        
        # Schedule background optimization task
        background_tasks.add_task(_optimize_mcp_cache, mcp_service)
        
        logger.info(f"📤 Enhanced Response Generated: {len(response_data.get('response', ''))} chars")
        
        return ChatResponse(
            response=response_data.get("response", "No response generated"),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"💥 Enhanced chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

async def _handle_mcp_enhanced_request(user_input: str, mcp_service: MCPServiceV2, llm_service: LLMServiceV2) -> Dict[str, Any]:
    """
    Handle request with full MCP enhancement
    Uses dynamic tool discovery and context-aware LLM generation
    """
    try:
        logger.info("🧠 Processing with MCP-enhanced Oracle...")
        
        # Get MCP-enhanced LLM response
        llm_response = await llm_service.interpret_user_request_with_mcp(user_input)
        
        if "error" in llm_response:
            logger.warning(f"⚠️  MCP-enhanced LLM failed: {llm_response['error']}")
            # Fallback to intelligent MCP routing
            return await _handle_intelligent_mcp_routing(user_input, mcp_service)
        
        oracle_response = llm_response.get("response", "")
        
        # Check if Oracle is requesting specific MCP tool execution
        if await _should_execute_mcp_tools(oracle_response, user_input):
            tool_results = await _execute_suggested_mcp_tools(oracle_response, user_input, mcp_service)
            
            if tool_results:
                # Combine Oracle guidance with actual MCP tool results
                combined_response = await _combine_oracle_and_mcp_results(oracle_response, tool_results, llm_service)
                return {"response": combined_response}
        
        return {"response": oracle_response}
        
    except Exception as e:
        logger.error(f"❌ MCP-enhanced request failed: {e}")
        # Fallback to intelligent routing
        return await _handle_intelligent_mcp_routing(user_input, mcp_service)

async def _handle_intelligent_mcp_routing(user_input: str, mcp_service: MCPServiceV2) -> Dict[str, Any]:
    """
    Intelligent routing to MCP tools based on user intent
    Uses pattern matching and MCP capability discovery
    """
    logger.info("🎯 Using intelligent MCP routing...")
    
    try:
        # Use MCP service's intelligent query routing
        mcp_result = await mcp_service.intelligent_query(user_input)
        
        if "error" in mcp_result:
            return {"response": f"System unavailable: {mcp_result['error']}"}
        
        # Format MCP result for user consumption
        formatted_response = await _format_mcp_result_for_user(mcp_result, user_input)
        return {"response": formatted_response}
        
    except Exception as e:
        logger.error(f"❌ Intelligent MCP routing failed: {e}")
        return {"response": f"System error during intelligent routing: {str(e)}"}

async def _handle_direct_mcp_request(user_input: str, mcp_service: MCPServiceV2) -> Dict[str, Any]:
    """
    Handle request with direct MCP tool access (Oracle offline)
    Provides system functionality without LLM interpretation
    """
    logger.info("🔧 Processing with direct MCP access (Oracle offline)...")
    
    try:
        # Discover available capabilities
        capabilities = await mcp_service.discover_capabilities()
        
        # Use intelligent routing for direct access
        mcp_result = await mcp_service.intelligent_query(user_input)
        
        if "error" in mcp_result:
            available_tools = capabilities.get("tools", [])
            return {
                "response": f"Oracle offline. MCP system available with tools: {', '.join(available_tools)}. "
                           f"Your query: '{user_input}' could not be processed. Error: {mcp_result['error']}"
            }
        
        # Format result with capability information
        formatted_response = await _format_mcp_result_for_user(mcp_result, user_input)
        tool_count = len(capabilities.get("tools", []))
        
        response_with_status = f"Oracle offline - MCP System Operational ({tool_count} tools available)\n\n{formatted_response}"
        return {"response": response_with_status}
        
    except Exception as e:
        logger.error(f"❌ Direct MCP request failed: {e}")
        return {"response": f"Oracle offline. MCP system error: {str(e)}"}

async def _should_execute_mcp_tools(oracle_response: str, user_input: str) -> bool:
    """Determine if Oracle response suggests executing MCP tools"""
    oracle_lower = oracle_response.lower()
    user_lower = user_input.lower()
    
    # Check for explicit tool suggestions in Oracle response
    tool_indicators = [
        "use system_health", "call system_health", "system_health tool",
        "use system_status", "call system_status", "system_status tool",
        "use system_config", "call system_config", "system_config tool",
        "check the logs", "view logs", "system logs",
        "get metrics", "runtime metrics", "performance data"
    ]
    
    return any(indicator in oracle_lower for indicator in tool_indicators)

async def _execute_suggested_mcp_tools(oracle_response: str, user_input: str, mcp_service: MCPServiceV2) -> Optional[Dict[str, Any]]:
    """Execute MCP tools suggested by Oracle response"""
    try:
        oracle_lower = oracle_response.lower()
        results = {}
        
        # Execute specific tools based on Oracle suggestions
        if "system_health" in oracle_lower:
            health_result = await mcp_service.get_comprehensive_health()
            if "error" not in health_result:
                results["health"] = health_result
        
        if "system_status" in oracle_lower:
            status_result = await mcp_service.get_operational_status()
            if "error" not in status_result:
                results["status"] = status_result
        
        if "system_config" in oracle_lower:
            config_result = await mcp_service.get_system_configuration()
            if "error" not in config_result:
                results["config"] = config_result
        
        if any(keyword in oracle_lower for keyword in ["logs", "log entries"]):
            logs_result = await mcp_service.get_live_system_logs()
            if "error" not in logs_result:
                results["logs"] = logs_result
        
        if any(keyword in oracle_lower for keyword in ["metrics", "runtime", "performance"]):
            metrics_result = await mcp_service.get_runtime_metrics()
            if "error" not in metrics_result:
                results["metrics"] = metrics_result
        
        return results if results else None
        
    except Exception as e:
        logger.error(f"❌ Failed to execute suggested MCP tools: {e}")
        return None

async def _combine_oracle_and_mcp_results(oracle_response: str, tool_results: Dict[str, Any], llm_service: LLMServiceV2) -> str:
    """Combine Oracle guidance with actual MCP tool results"""
    try:
        # Format tool results
        formatted_results = []
        
        for tool_type, result in tool_results.items():
            if "content" in result and len(result["content"]) > 0:
                content = result["content"][0]
                if "text" in content:
                    formatted_results.append(f"**{tool_type.title()} Data:**\n{content['text']}")
        
        if not formatted_results:
            return oracle_response
        
        # Combine Oracle response with actual data
        combined_text = f"{oracle_response}\n\n**Live System Data:**\n\n" + "\n\n".join(formatted_results)
        
        # Optionally ask Oracle to summarize the combined data
        if len(combined_text) > 1000:  # Only summarize if response is getting long
            summary_prompt = f"Summarize this system analysis concisely:\n\n{combined_text}"
            summary_response = await llm_service.generate_response(summary_prompt)
            
            if "error" not in summary_response:
                return summary_response.get("response", combined_text)
        
        return combined_text
        
    except Exception as e:
        logger.error(f"❌ Failed to combine Oracle and MCP results: {e}")
        return oracle_response

async def _format_mcp_result_for_user(mcp_result: Dict[str, Any], user_query: str) -> str:
    """Format MCP tool result for user-friendly display"""
    try:
        if "content" in mcp_result and len(mcp_result["content"]) > 0:
            content = mcp_result["content"][0]
            
            if "text" in content:
                # Parse JSON content if possible for better formatting
                text = content["text"]
                try:
                    import json
                    data = json.loads(text)
                    
                    # Format based on data type
                    if "status" in data:
                        return f"System Status: {data['status']}\nVersion: {data.get('version', 'unknown')}\nTimestamp: {data.get('timestamp', 'unknown')}"
                    elif "component" in data and "checks" in data:
                        checks = data["checks"]
                        check_status = ", ".join([f"{k}: {v}" for k, v in checks.items()])
                        return f"Health Check - {data['component']}: {data.get('status', 'unknown')}\nChecks: {check_status}"
                    else:
                        # Generic JSON formatting
                        formatted_json = json.dumps(data, indent=2)
                        return f"System Response:\n```\n{formatted_json}\n```"
                        
                except json.JSONDecodeError:
                    # Return as plain text
                    return f"System Response:\n{text}"
            
            return str(content)
        
        return f"No detailed response available for query: '{user_query}'"
        
    except Exception as e:
        logger.error(f"❌ Failed to format MCP result: {e}")
        return f"System response formatting error: {str(e)}"

async def _optimize_mcp_cache(mcp_service: MCPServiceV2):
    """Background task to optimize MCP caching and connections"""
    try:
        # Refresh capabilities cache
        await mcp_service.discover_capabilities()
        logger.debug("🔄 MCP cache optimized")
    except Exception as e:
        logger.warning(f"⚠️  MCP cache optimization failed: {e}")

# Enhanced endpoint for MCP tool discovery
@router.get("/mcp/capabilities")
async def get_mcp_capabilities(mcp_service: MCPServiceV2 = Depends(get_mcp_service)):
    """Get available MCP capabilities and tools"""
    try:
        capabilities = await mcp_service.discover_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"❌ Failed to get MCP capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/tool/{tool_name}")
async def call_mcp_tool_directly(
    tool_name: str, 
    arguments: Dict[str, Any] = None,
    mcp_service: MCPServiceV2 = Depends(get_mcp_service)
):
    """Direct MCP tool execution endpoint"""
    try:
        result = await mcp_service.call_tool(tool_name, arguments)
        return result
    except Exception as e:
        logger.error(f"❌ Direct MCP tool call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/resource")
async def read_mcp_resource(
    uri: str,
    mcp_service: MCPServiceV2 = Depends(get_mcp_service)
):
    """Direct MCP resource read endpoint"""
    try:
        result = await mcp_service.read_resource(uri)
        return result
    except Exception as e:
        logger.error(f"❌ Direct MCP resource read failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy compatibility endpoints
@router.get("/sentinel/health")
async def sentinel_health_legacy(mcp_service: MCPServiceV2 = Depends(get_mcp_service)):
    """Legacy health endpoint - now uses MCP"""
    return await mcp_service.health_check()

@router.get("/sentinel/status")
async def sentinel_status_legacy(mcp_service: MCPServiceV2 = Depends(get_mcp_service)):
    """Legacy status endpoint - now uses MCP"""
    return await mcp_service.get_status()