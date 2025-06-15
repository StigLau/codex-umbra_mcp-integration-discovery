"""
Enhanced LLM Service for The Oracle
Uses MCP prompt templates and dynamic tool discovery for intelligent responses
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .mcp_service_v2 import MCPServiceV2
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMServiceV2:
    """
    Enhanced LLM Service that leverages MCP capabilities
    Uses dynamic prompt templates and tool discovery for optimal Oracle performance
    """
    
    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = "mistral"
        self.timeout = 30.0
        self.mcp_service = MCPServiceV2()
        
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response using Mistral via Ollama with optional context"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                messages = []
                
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                # Add context if provided
                if context:
                    context_info = self._format_context(context)
                    if context_info:
                        messages.append({
                            "role": "system",
                            "content": f"Additional Context: {context_info}"
                        })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": result.get("message", {}).get("content", ""),
                        "model": result.get("model", self.model),
                        "done": result.get("done", True),
                        "context_used": bool(context)
                    }
                else:
                    return {
                        "error": f"Ollama API error: HTTP {response.status_code}",
                        "details": response.text
                    }
                    
        except httpx.RequestError as e:
            return {
                "error": f"Connection to Ollama failed: {str(e)}",
                "available": False
            }
        except Exception as e:
            return {
                "error": f"LLM service error: {str(e)}"
            }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for LLM consumption"""
        formatted_parts = []
        
        if "available_tools" in context:
            tools = context["available_tools"]
            formatted_parts.append(f"Available MCP Tools: {', '.join(tools)}")
        
        if "available_resources" in context:
            resources = context["available_resources"]  
            formatted_parts.append(f"Available MCP Resources: {', '.join(resources)}")
        
        if "system_status" in context:
            status = context["system_status"]
            formatted_parts.append(f"Current System Status: {status}")
        
        if "user_intent" in context:
            intent = context["user_intent"]
            formatted_parts.append(f"Detected User Intent: {intent}")
        
        return " | ".join(formatted_parts)
    
    async def interpret_user_request_with_mcp(self, user_input: str) -> Dict[str, Any]:
        """
        Interpret user request using MCP capabilities for enhanced context
        Gets dynamic prompt templates and system information from MCP server
        """
        try:
            # Analyze user intent
            intent = await self._analyze_user_intent(user_input)
            
            # Get appropriate MCP prompt template based on intent
            prompt_template = await self._get_mcp_prompt_template(intent, user_input)
            
            # Gather relevant context from MCP
            mcp_context = await self._gather_mcp_context(intent)
            
            # Generate enhanced system prompt
            system_prompt = await self._build_enhanced_system_prompt(intent, mcp_context, prompt_template)
            
            # Generate Oracle response with full context
            response = await self.generate_response(
                user_input,
                system_prompt=system_prompt,
                context=mcp_context
            )
            
            if "error" not in response:
                # Enhance response with MCP tool suggestions if appropriate
                response = await self._enhance_response_with_tools(response, intent, mcp_context)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ MCP-enhanced interpretation failed: {e}")
            # Fallback to basic interpretation
            return await self.interpret_user_request(user_input)
    
    async def _analyze_user_intent(self, user_input: str) -> str:
        """Analyze user input to determine intent"""
        user_lower = user_input.lower().strip()
        
        if any(keyword in user_lower for keyword in ["health", "diagnostic", "check"]):
            return "health_analysis"
        elif any(keyword in user_lower for keyword in ["status", "operational", "running"]):
            return "status_inquiry"
        elif any(keyword in user_lower for keyword in ["problem", "issue", "error", "troubleshoot"]):
            return "troubleshooting"
        elif any(keyword in user_lower for keyword in ["config", "configuration", "settings"]):
            return "configuration"
        elif any(keyword in user_lower for keyword in ["help", "how", "what", "explain"]):
            return "guidance"
        else:
            return "general_inquiry"
    
    async def _get_mcp_prompt_template(self, intent: str, user_input: str) -> Dict[str, Any]:
        """Get appropriate MCP prompt template based on user intent"""
        try:
            if intent in ["health_analysis", "troubleshooting"]:
                if intent == "troubleshooting":
                    return await self.mcp_service.get_prompt_template("troubleshooting", {
                        "issue_description": user_input,
                        "affected_components": ["sentinel", "conductor", "oracle"]
                    })
                else:
                    return await self.mcp_service.get_prompt_template("system_analysis", {
                        "analysis_type": "health_assessment",
                        "urgency": "medium"
                    })
            else:
                # Default to system analysis prompt
                return await self.mcp_service.get_prompt_template("system_analysis", {
                    "analysis_type": "general",
                    "urgency": "low"
                })
        except Exception as e:
            logger.warning(f"⚠️  Failed to get MCP prompt template: {e}")
            return {}
    
    async def _gather_mcp_context(self, intent: str) -> Dict[str, Any]:
        """Gather relevant context from MCP server based on intent"""
        context = {}
        
        try:
            # Always get capabilities for tool awareness
            capabilities = await self.mcp_service.discover_capabilities()
            context.update({
                "available_tools": capabilities.get("tools", []),
                "available_resources": capabilities.get("resources", []),
                "available_prompts": capabilities.get("prompts", [])
            })
            
            # Get context specific to intent
            if intent == "health_analysis":
                health_data = await self.mcp_service.get_comprehensive_health()
                if "error" not in health_data:
                    context["system_health"] = health_data
            
            elif intent == "status_inquiry":
                status_data = await self.mcp_service.get_operational_status()
                if "error" not in status_data:
                    context["system_status"] = status_data
            
            elif intent == "troubleshooting":
                # Get logs and runtime metrics for troubleshooting
                logs = await self.mcp_service.get_live_system_logs()
                metrics = await self.mcp_service.get_runtime_metrics()
                if "error" not in logs:
                    context["system_logs"] = logs
                if "error" not in metrics:
                    context["runtime_metrics"] = metrics
            
            elif intent == "configuration":
                config_data = await self.mcp_service.get_system_configuration()
                if "error" not in config_data:
                    context["system_config"] = config_data
            
            context["user_intent"] = intent
            context["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to gather MCP context: {e}")
        
        return context
    
    async def _build_enhanced_system_prompt(self, intent: str, mcp_context: Dict[str, Any], prompt_template: Dict[str, Any]) -> str:
        """Build enhanced system prompt using MCP template and context"""
        
        # Base Oracle identity
        base_prompt = """You are The Oracle, the AI interface for Codex Umbra system management.
You have access to real-time system data through MCP (Model Context Protocol) tools and resources."""
        
        # Add MCP template content if available
        template_content = ""
        if prompt_template and "messages" in prompt_template:
            messages = prompt_template["messages"]
            if messages and len(messages) > 0:
                template_content = messages[0].get("content", {}).get("text", "")
        
        # Add available capabilities
        capabilities_info = ""
        if "available_tools" in mcp_context:
            tools = mcp_context["available_tools"]
            capabilities_info = f"\n\nAvailable MCP Tools: {', '.join(tools)}"
        
        if "available_resources" in mcp_context:
            resources = mcp_context["available_resources"]
            capabilities_info += f"\nAvailable MCP Resources: {', '.join(resources)}"
        
        # Add context-specific guidance
        context_guidance = ""
        if intent == "health_analysis":
            context_guidance = "\n\nFor health analysis, use system_health tool and reference system logs."
        elif intent == "status_inquiry":
            context_guidance = "\n\nFor status inquiries, use system_status tool and runtime metrics."
        elif intent == "troubleshooting":
            context_guidance = "\n\nFor troubleshooting, analyze logs, use diagnostic tools, and provide actionable steps."
        elif intent == "configuration":
            context_guidance = "\n\nFor configuration queries, use system_config tool and validate settings."
        
        # Combine all parts
        enhanced_prompt = base_prompt
        if template_content:
            enhanced_prompt += f"\n\n{template_content}"
        enhanced_prompt += capabilities_info + context_guidance
        enhanced_prompt += "\n\nProvide helpful, actionable responses based on real system data."
        
        return enhanced_prompt
    
    async def _enhance_response_with_tools(self, response: Dict[str, Any], intent: str, mcp_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance LLM response with MCP tool suggestions"""
        
        oracle_response = response.get("response", "")
        
        # Add tool suggestions based on intent
        tool_suggestions = []
        
        if intent == "health_analysis":
            tool_suggestions.append("💡 Try: Use `system_health` tool for detailed health metrics")
        elif intent == "status_inquiry":
            tool_suggestions.append("💡 Try: Use `system_status` tool for operational details")
        elif intent == "troubleshooting":
            tool_suggestions.append("💡 Try: Check system logs via `system://logs/sentinel.log` resource")
        elif intent == "configuration":
            tool_suggestions.append("💡 Try: Use `system_config` tool to explore settings")
        
        # Add available tools hint
        if "available_tools" in mcp_context:
            tools = mcp_context["available_tools"]
            if len(tools) > 0:
                tool_suggestions.append(f"🛠️  Available tools: {', '.join(tools)}")
        
        # Enhance response
        if tool_suggestions:
            enhanced_response = oracle_response + "\n\n" + "\n".join(tool_suggestions)
            response["response"] = enhanced_response
            response["mcp_enhanced"] = True
        
        return response
    
    # Legacy compatibility method
    async def interpret_user_request(self, user_input: str) -> Dict[str, Any]:
        """Legacy method - now enhanced with basic MCP awareness"""
        
        # Try MCP-enhanced interpretation first
        try:
            return await self.interpret_user_request_with_mcp(user_input)
        except Exception as e:
            logger.warning(f"⚠️  MCP-enhanced interpretation failed, using fallback: {e}")
        
        # Fallback to basic interpretation with limited MCP awareness
        system_prompt = """You are The Oracle, an AI assistant for Codex Umbra. Your role is to understand and interact with The Sentinel, our MCP server.

Available capabilities (if MCP is operational):
- System health analysis via MCP tools
- Real-time status monitoring
- Configuration management
- Log analysis and troubleshooting

If MCP tools are available, suggest their use. Otherwise, provide helpful guidance based on the user's request.

Be concise and efficient. Respond in plain text."""
        
        return await self.generate_response(user_input, system_prompt)