"""
Function Call Orchestrator - Handles LLM function calls and routes them to MCP tools
Manages conversation state, tool execution, and result processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from .mcp_service_v2 import MCPServiceV2
from .mcp_schema_converter import mcp_schema_converter

logger = logging.getLogger(__name__)

class FunctionCallResult:
    """Result of a function call execution"""
    def __init__(self, success: bool, result: Any = None, error: str = None, tool_name: str = None):
        self.success = success
        self.result = result
        self.error = error
        self.tool_name = tool_name
        self.timestamp = datetime.utcnow().isoformat() + "Z"

class ConversationState:
    """Maintains state for a function calling conversation"""
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.function_calls = []
        self.results = []
        self.available_tools = []
        self.start_time = datetime.utcnow()
    
    def add_function_call(self, tool_name: str, arguments: Dict[str, Any], result: FunctionCallResult):
        """Add a function call and its result to the conversation history"""
        self.function_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    def get_call_history_summary(self) -> str:
        """Get a summary of function calls made in this conversation"""
        if not self.function_calls:
            return "No function calls made yet."
        
        summary = [f"Function call history ({len(self.function_calls)} calls):"]
        for i, call in enumerate(self.function_calls, 1):
            result_status = "✅ Success" if call["result"].success else "❌ Failed"
            summary.append(f"{i}. {call['tool_name']}() - {result_status}")
        
        return "\n".join(summary)

class LLMFunctionCallOrchestrator:
    """Orchestrates function calls between LLMs and MCP tools"""
    
    def __init__(self, mcp_service: MCPServiceV2):
        self.mcp_service = mcp_service
        self.conversations = {}
        self.max_function_calls_per_conversation = 10
        self.function_call_timeout = 30.0
    
    async def initialize(self):
        """Initialize the orchestrator and discover available tools"""
        try:
            # Discover available MCP tools
            capabilities = await self.mcp_service.discover_capabilities()
            self.available_tools = capabilities.get("tools", [])
            logger.info(f"Function call orchestrator initialized with {len(self.available_tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize function call orchestrator: {e}")
            self.available_tools = []
    
    async def get_available_tools_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get available tools in the format required by the specified LLM provider"""
        if not self.available_tools:
            await self.initialize()
        
        if provider == "anthropic":
            return mcp_schema_converter.convert_all_mcp_tools_to_anthropic(self.available_tools)
        elif provider == "openai":
            return mcp_schema_converter.convert_all_mcp_tools_to_openai(self.available_tools)
        else:
            # Return raw MCP tools for other providers
            return self.available_tools
    
    async def handle_function_call(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        conversation_id: str = None
    ) -> FunctionCallResult:
        """Handle a single function call from an LLM"""
        
        logger.info(f"🔧 Function call: {tool_name} with args: {arguments}")
        
        try:
            # Validate arguments against schema
            validation_result = mcp_schema_converter.validate_function_call_arguments(
                tool_name, arguments, self.available_tools
            )
            
            if not validation_result["valid"]:
                error_msg = f"Invalid arguments: {'; '.join(validation_result['errors'])}"
                logger.error(f"Function call validation failed: {error_msg}")
                return FunctionCallResult(
                    success=False,
                    error=error_msg,
                    tool_name=tool_name
                )
            
            # Execute the MCP tool with validated arguments
            cleaned_arguments = validation_result["cleaned_arguments"]
            
            # Add timeout to prevent hanging
            try:
                result = await asyncio.wait_for(
                    self.mcp_service.call_tool(tool_name, cleaned_arguments),
                    timeout=self.function_call_timeout
                )
            except asyncio.TimeoutError:
                error_msg = f"Function call timed out after {self.function_call_timeout}s"
                logger.error(error_msg)
                return FunctionCallResult(
                    success=False,
                    error=error_msg,
                    tool_name=tool_name
                )
            
            # Check if MCP tool execution was successful
            if "error" in result:
                error_msg = result["error"]
                logger.error(f"MCP tool execution failed: {error_msg}")
                return FunctionCallResult(
                    success=False,
                    error=error_msg,
                    tool_name=tool_name
                )
            
            # Format result for LLM consumption
            formatted_result = self._format_mcp_result_for_llm(result)
            
            function_result = FunctionCallResult(
                success=True,
                result=formatted_result,
                tool_name=tool_name
            )
            
            # Add to conversation history if conversation_id provided
            if conversation_id:
                self._add_to_conversation_history(conversation_id, tool_name, arguments, function_result)
            
            logger.info(f"✅ Function call {tool_name} completed successfully")
            return function_result
            
        except Exception as e:
            error_msg = f"Function call execution error: {str(e)}"
            logger.error(error_msg)
            return FunctionCallResult(
                success=False,
                error=error_msg,
                tool_name=tool_name
            )
    
    async def handle_multiple_function_calls(
        self, 
        function_calls: List[Dict[str, Any]], 
        conversation_id: str = None
    ) -> List[FunctionCallResult]:
        """Handle multiple function calls, potentially in parallel"""
        
        if len(function_calls) > self.max_function_calls_per_conversation:
            logger.warning(f"Too many function calls ({len(function_calls)}), limiting to {self.max_function_calls_per_conversation}")
            function_calls = function_calls[:self.max_function_calls_per_conversation]
        
        tasks = []
        for call in function_calls:
            task = self.handle_function_call(
                call.get("name", call.get("tool_name")),
                call.get("arguments", call.get("parameters", {})),
                conversation_id
            )
            tasks.append(task)
        
        # Execute function calls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        function_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = FunctionCallResult(
                    success=False,
                    error=f"Function call failed: {str(result)}",
                    tool_name=function_calls[i].get("name", "unknown")
                )
                function_results.append(error_result)
            else:
                function_results.append(result)
        
        return function_results
    
    def _format_mcp_result_for_llm(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format MCP tool result for LLM consumption"""
        try:
            # Extract content from MCP response
            content = mcp_result.get("content", [])
            
            if not content:
                return {"text": "No content returned", "type": "text"}
            
            # Handle different content types
            formatted_content = []
            for item in content:
                if "text" in item:
                    formatted_content.append({
                        "type": "text",
                        "content": item["text"]
                    })
                elif "json" in item:
                    formatted_content.append({
                        "type": "json",
                        "content": item["json"]
                    })
                else:
                    # Unknown content type, include as-is
                    formatted_content.append(item)
            
            return {
                "content": formatted_content,
                "tool_result": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Failed to format MCP result: {e}")
            return {
                "type": "error",
                "content": f"Failed to format result: {str(e)}"
            }
    
    def _add_to_conversation_history(
        self, 
        conversation_id: str, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        result: FunctionCallResult
    ):
        """Add function call to conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState(conversation_id)
        
        conversation = self.conversations[conversation_id]
        conversation.add_function_call(tool_name, arguments, result)
    
    def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation state by ID"""
        return self.conversations.get(conversation_id)
    
    def create_conversation(self, conversation_id: str = None) -> str:
        """Create a new conversation and return its ID"""
        if conversation_id is None:
            conversation_id = f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.conversations)}"
        
        self.conversations[conversation_id] = ConversationState(conversation_id)
        logger.debug(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversations to prevent memory leaks"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for conv_id, conversation in self.conversations.items():
            if conversation.start_time.timestamp() < cutoff_time:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old conversations")
    
    async def get_tool_documentation(self) -> str:
        """Get human-readable documentation for available tools"""
        if not self.available_tools:
            await self.initialize()
        
        return mcp_schema_converter.generate_tool_documentation(self.available_tools)
    
    def get_function_call_statistics(self) -> Dict[str, Any]:
        """Get statistics about function call usage"""
        total_conversations = len(self.conversations)
        total_function_calls = sum(len(conv.function_calls) for conv in self.conversations.values())
        
        # Count successful vs failed calls
        successful_calls = 0
        failed_calls = 0
        tool_usage = {}
        
        for conversation in self.conversations.values():
            for call in conversation.function_calls:
                if call["result"].success:
                    successful_calls += 1
                else:
                    failed_calls += 1
                
                tool_name = call["tool_name"]
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "total_function_calls": total_function_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / max(total_function_calls, 1),
            "tool_usage": tool_usage,
            "available_tools_count": len(self.available_tools)
        }