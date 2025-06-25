"""
LLM Function Calling Service - Orchestrates function calling conversations between LLMs and MCP tools
Handles multi-turn conversations, tool execution, and result processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from .llm_provider_service import multi_llm_service, LLMProvider
from .mcp_service_v2 import MCPServiceV2
from .function_call_orchestrator import LLMFunctionCallOrchestrator, FunctionCallResult
from app.core.config import settings

logger = logging.getLogger(__name__)

class FunctionCallingConversation:
    """Manages a function calling conversation between user, LLM, and MCP tools"""
    
    def __init__(self, conversation_id: str, provider: LLMProvider):
        self.conversation_id = conversation_id
        self.provider = provider
        self.messages = []
        self.tool_results = []
        self.max_turns = 10
        self.current_turn = 0
    
    def add_user_message(self, content: str):
        """Add user message to conversation"""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    def add_assistant_message(self, content: str, tool_calls: List[Dict[str, Any]] = None):
        """Add assistant message to conversation"""
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.messages.append(message)
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: FunctionCallResult):
        """Add tool execution result to conversation"""
        self.tool_results.append({
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Also add as a message for the LLM
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": self._format_tool_result_for_llm(result)
        })
    
    def _format_tool_result_for_llm(self, result: FunctionCallResult) -> str:
        """Format tool result for LLM consumption"""
        if result.success:
            if isinstance(result.result, dict) and "content" in result.result:
                # Extract text content from MCP result
                content_items = result.result["content"]
                text_parts = []
                for item in content_items:
                    if item.get("type") == "text":
                        text_parts.append(item["content"])
                    elif item.get("type") == "json":
                        text_parts.append(f"JSON Result: {item['content']}")
                return "\n".join(text_parts) if text_parts else str(result.result)
            else:
                return str(result.result)
        else:
            return f"Error: {result.error}"

class LLMFunctionCallingService:
    """Service that manages function calling conversations between LLMs and MCP tools"""
    
    def __init__(self):
        self.mcp_service = MCPServiceV2()
        self.orchestrator = LLMFunctionCallOrchestrator(self.mcp_service)
        self.conversations = {}
        self.max_concurrent_conversations = 50
    
    async def initialize(self):
        """Initialize the service and discover available tools"""
        try:
            await self.orchestrator.initialize()
            logger.info("LLM Function Calling Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Function Calling Service: {e}")
            raise
    
    async def start_function_calling_conversation(
        self, 
        user_message: str, 
        provider: str = None,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """Start a new function calling conversation"""
        
        # Create conversation ID if not provided
        if conversation_id is None:
            conversation_id = f"fc_{uuid.uuid4().hex[:8]}"
        
        # Determine provider
        if provider:
            try:
                llm_provider = LLMProvider(provider)
            except ValueError:
                llm_provider = LLMProvider(settings.default_llm_provider)
        else:
            llm_provider = LLMProvider(settings.default_llm_provider)
        
        # Create conversation
        conversation = FunctionCallingConversation(conversation_id, llm_provider)
        conversation.add_user_message(user_message)
        
        # Clean up old conversations if needed
        if len(self.conversations) >= self.max_concurrent_conversations:
            self._cleanup_old_conversations()
        
        self.conversations[conversation_id] = conversation
        
        # Start the conversation loop
        result = await self._process_conversation_turn(conversation)
        
        return {
            "conversation_id": conversation_id,
            "response": result.get("response", ""),
            "tool_calls_made": result.get("tool_calls_made", []),
            "function_calling_enabled": True,
            "provider_used": llm_provider.value,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def continue_function_calling_conversation(
        self, 
        conversation_id: str, 
        user_message: str
    ) -> Dict[str, Any]:
        """Continue an existing function calling conversation"""
        
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Check max turns
        if conversation.current_turn >= conversation.max_turns:
            return {
                "conversation_id": conversation_id,
                "response": "Maximum conversation turns reached. Please start a new conversation.",
                "conversation_ended": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        conversation.add_user_message(user_message)
        result = await self._process_conversation_turn(conversation)
        
        return {
            "conversation_id": conversation_id,
            "response": result.get("response", ""),
            "tool_calls_made": result.get("tool_calls_made", []),
            "turn": conversation.current_turn,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def _process_conversation_turn(self, conversation: FunctionCallingConversation) -> Dict[str, Any]:
        """Process a single turn in the conversation"""
        
        conversation.current_turn += 1
        
        try:
            # Get available tools for the provider
            available_tools = await self.orchestrator.get_available_tools_for_provider(
                conversation.provider.value
            )
            
            # Get the latest user message
            latest_message = conversation.messages[-1]["content"]
            
            # Create system prompt that explains available tools
            system_prompt = self._create_system_prompt_with_tools(available_tools)
            full_prompt = f"{system_prompt}\n\nUser: {latest_message}"
            
            # Check if provider supports function calling
            if conversation.provider == LLMProvider.ANTHROPIC and available_tools:
                # Use Anthropic's tool calling
                provider_instance = multi_llm_service.providers[LLMProvider.ANTHROPIC]
                llm_response = await provider_instance.generate_with_tools(
                    full_prompt, 
                    available_tools
                )
                
                # Process tool calls if any
                if llm_response.get("tool_calls"):
                    tool_results = await self._execute_tool_calls(
                        llm_response["tool_calls"], 
                        conversation
                    )
                    
                    # Add tool results to conversation
                    for tool_call, result in zip(llm_response["tool_calls"], tool_results):
                        conversation.add_tool_result(
                            tool_call.get("id", "unknown"),
                            tool_call["name"],
                            result
                        )
                    
                    # Generate follow-up response with tool results
                    follow_up_prompt = self._create_follow_up_prompt(
                        latest_message, 
                        llm_response["content"], 
                        tool_results
                    )
                    
                    final_response = await multi_llm_service.generate_response(
                        follow_up_prompt,
                        provider=conversation.provider
                    )
                    
                    response_text = final_response.get("response", llm_response["content"])
                    tool_calls_made = [{"name": tc["name"], "arguments": tc["arguments"]} for tc in llm_response["tool_calls"]]
                else:
                    response_text = llm_response["content"]
                    tool_calls_made = []
            
            else:
                # Fallback to regular generation for other providers
                response = await multi_llm_service.generate_response(
                    full_prompt,
                    provider=conversation.provider
                )
                response_text = response.get("response", "")
                tool_calls_made = []
            
            # Add assistant response to conversation
            conversation.add_assistant_message(response_text, tool_calls_made)
            
            return {
                "response": response_text,
                "tool_calls_made": tool_calls_made
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")
            error_response = f"I encountered an error while processing your request: {str(e)}"
            conversation.add_assistant_message(error_response)
            return {"response": error_response, "tool_calls_made": []}
    
    async def _execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]], 
        conversation: FunctionCallingConversation
    ) -> List[FunctionCallResult]:
        """Execute multiple tool calls"""
        
        results = []
        for tool_call in tool_calls:
            result = await self.orchestrator.handle_function_call(
                tool_call["name"],
                tool_call["arguments"],
                conversation.conversation_id
            )
            results.append(result)
        
        return results
    
    def _create_system_prompt_with_tools(self, available_tools: List[Dict[str, Any]]) -> str:
        """Create system prompt that describes available tools"""
        
        base_prompt = """You are The Oracle, an AI assistant with access to system management tools through MCP (Model Context Protocol). You can perform real system operations using the available tools.

When a user asks you to check system status, analyze health, or perform system operations, you should use the appropriate tools to get real data rather than providing generic responses.

Available tools:"""
        
        if not available_tools:
            return base_prompt + "\nNo tools currently available."
        
        tool_descriptions = []
        for tool in available_tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            tool_descriptions.append(f"- {name}: {description}")
        
        tools_text = "\n".join(tool_descriptions)
        
        return f"""{base_prompt}
{tools_text}

Use these tools when appropriate to provide accurate, real-time information about the system. Always explain what you're doing and why you're using specific tools."""
    
    def _create_follow_up_prompt(
        self, 
        user_message: str, 
        initial_response: str, 
        tool_results: List[FunctionCallResult]
    ) -> str:
        """Create follow-up prompt after tool execution"""
        
        results_summary = []
        for result in tool_results:
            if result.success:
                results_summary.append(f"✅ {result.tool_name}: Success")
            else:
                results_summary.append(f"❌ {result.tool_name}: {result.error}")
        
        return f"""User asked: {user_message}

I executed the following tools:
{chr(10).join(results_summary)}

Based on the tool execution results, provide a comprehensive response to the user's question. Include relevant data from the tool results and explain what the results mean in context of their request."""
    
    def _cleanup_old_conversations(self):
        """Remove old conversations to prevent memory leaks"""
        # Simple cleanup: remove oldest conversations
        if len(self.conversations) >= self.max_concurrent_conversations:
            # Sort by turn count and remove oldest
            sorted_convs = sorted(
                self.conversations.items(), 
                key=lambda x: x[1].current_turn,
                reverse=True
            )
            
            # Keep only the most recent conversations
            keep_count = self.max_concurrent_conversations // 2
            to_keep = dict(sorted_convs[:keep_count])
            
            removed_count = len(self.conversations) - len(to_keep)
            self.conversations = to_keep
            
            logger.info(f"Cleaned up {removed_count} old conversations")
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of a conversation"""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        return {
            "conversation_id": conversation_id,
            "provider": conversation.provider.value,
            "turn_count": conversation.current_turn,
            "message_count": len(conversation.messages),
            "tool_results_count": len(conversation.tool_results),
            "last_activity": conversation.messages[-1]["timestamp"] if conversation.messages else None
        }
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        orchestrator_stats = self.orchestrator.get_function_call_statistics()
        
        return {
            "active_conversations": len(self.conversations),
            "function_call_stats": orchestrator_stats,
            "service_status": "active"
        }

# Global instance
llm_function_calling_service = LLMFunctionCallingService()