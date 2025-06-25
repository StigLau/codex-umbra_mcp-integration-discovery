"""
Enhanced LLM Service for The Oracle
Uses MCP prompt templates and dynamic tool discovery for intelligent responses
Supports multiple LLM providers: Ollama, Anthropic Claude, Google Gemini
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .mcp_service_v2 import MCPServiceV2
from .llm_provider_service import multi_llm_service, LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMServiceV2:
    """
    Enhanced LLM Service that leverages MCP capabilities
    Uses dynamic prompt templates and tool discovery for optimal Oracle performance
    """
    
    def __init__(self):
        self.mcp_service = MCPServiceV2()
        self.multi_llm = multi_llm_service
        
    async def is_available(self) -> bool:
        """Check if any LLM provider is available"""
        available_providers = await self.multi_llm.get_available_providers()
        return any(provider["available"] for provider in available_providers)
    
    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available LLM providers"""
        return await self.multi_llm.get_available_providers()
    
    async def set_llm_provider(self, provider_name: str) -> bool:
        """Set the active LLM provider"""
        try:
            provider = LLMProvider(provider_name)
            await self.multi_llm.set_default_provider(provider)
            return True
        except (ValueError, RuntimeError) as e:
            logger.error(f"Failed to set LLM provider to {provider_name}: {e}")
            return False
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None, context: Dict[str, Any] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response using the multi-LLM provider service"""
        try:
            # Construct the full prompt
            full_prompt = self._construct_full_prompt(prompt, system_prompt, context)
            
            # Use specified provider or default
            llm_provider = None
            if provider:
                try:
                    llm_provider = LLMProvider(provider)
                except ValueError:
                    logger.warning(f"Invalid provider '{provider}', using default")
            
            # Generate response using multi-LLM service
            response_data = await self.multi_llm.generate_response(
                full_prompt, 
                provider=llm_provider
            )
            
            return {
                "response": response_data["response"],
                "provider_used": response_data["provider_used"],
                "model_info": response_data["model_info"],
                "timestamp": response_data["timestamp"],
                "fallback_from": response_data.get("fallback_from"),
                "oracle_enhanced": True
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                "response": f"Oracle Error: {str(e)}",
                "error": True,
                "timestamp": self._get_timestamp()
            }
    
    def _construct_full_prompt(self, prompt: str, system_prompt: Optional[str] = None, context: Dict[str, Any] = None) -> str:
        """Construct the full prompt with system instructions and context"""
        parts = []
        
        if system_prompt:
            parts.append(f"System: {system_prompt}")
        
        if context:
            context_info = self._format_context(context)
            if context_info:
                parts.append(f"Context: {context_info}")
        
        parts.append(f"User: {prompt}")
        
        return "\n\n".join(parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"
    
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
        ENHANCED: Interpret user request using intelligent MCP prompt discovery
        Automatically selects and uses the best MCP prompts for optimal Oracle responses
        """
        try:
            # Advanced intent analysis with context awareness
            intent_analysis = await self._advanced_intent_analysis(user_input)
            
            # Discover and select optimal MCP prompt template
            optimal_prompt = await self._discover_optimal_mcp_prompt(intent_analysis, user_input)
            
            # Gather comprehensive MCP context
            mcp_context = await self._gather_comprehensive_mcp_context(intent_analysis)
            
            # Use the MCP prompt directly as Oracle's intelligence framework
            if optimal_prompt and "messages" in optimal_prompt:
                # Extract the sophisticated prompt from MCP server
                mcp_prompt_content = optimal_prompt["messages"][0]["content"]["text"]
                
                # Generate Oracle response using MCP-provided intelligence prompt
                response = await self.generate_response(
                    user_input,
                    system_prompt=mcp_prompt_content,
                    context=mcp_context
                )
                
                # Add MCP intelligence indicators
                response["mcp_prompt_used"] = intent_analysis.get("optimal_prompt_name", "intelligent_assistant")
                response["intelligence_mode"] = "mcp_enhanced"
                
            else:
                # Fallback to enhanced local prompt with MCP context
                enhanced_prompt = await self._build_fallback_enhanced_prompt(intent_analysis, mcp_context)
                response = await self.generate_response(
                    user_input,
                    system_prompt=enhanced_prompt,
                    context=mcp_context
                )
                response["intelligence_mode"] = "enhanced_local"
            
            if "error" not in response:
                # Enhance response with intelligent tool recommendations
                response = await self._add_intelligent_tool_recommendations(response, intent_analysis, mcp_context)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ MCP-enhanced interpretation failed: {e}")
            # Fallback to basic interpretation
            return await self.interpret_user_request(user_input)
    
    async def _advanced_intent_analysis(self, user_input: str) -> Dict[str, Any]:
        """Advanced intent analysis with context awareness and prompt selection"""
        user_lower = user_input.lower().strip()
        
        # Multi-dimensional intent analysis
        intent_signals = {
            "health_analysis": ["health", "diagnostic", "check", "wellness", "vitals", "performance"],
            "troubleshooting": ["problem", "issue", "error", "troubleshoot", "fix", "broken", "failing", "debug"],
            "expert_consultation": ["how", "why", "explain", "technical", "deep", "analysis", "expert", "detailed"],
            "predictive_analysis": ["predict", "forecast", "future", "trend", "projection", "anticipate"],
            "status_inquiry": ["status", "operational", "running", "state", "current", "now"],
            "configuration": ["config", "configuration", "settings", "setup", "options"],
            "general_inquiry": []  # Default
        }
        
        # Calculate intent scores
        intent_scores = {}
        for intent, keywords in intent_signals.items():
            score = sum(1 for keyword in keywords if keyword in user_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "general_inquiry"
        
        # Determine optimal MCP prompt based on intent
        prompt_mapping = {
            "health_analysis": "system_analysis",
            "troubleshooting": "troubleshooting", 
            "expert_consultation": "expert_consultation",
            "predictive_analysis": "predictive_analysis",
            "status_inquiry": "intelligent_assistant",
            "configuration": "intelligent_assistant",
            "general_inquiry": "intelligent_assistant"
        }
        
        # Analyze complexity and urgency
        complexity_signals = ["complex", "detailed", "comprehensive", "deep", "technical", "advanced"]
        urgency_signals = ["urgent", "critical", "immediate", "emergency", "quickly", "asap"]
        
        complexity = "expert" if any(sig in user_lower for sig in complexity_signals) else "intermediate"
        urgency = "high" if any(sig in user_lower for sig in urgency_signals) else "medium"
        
        return {
            "primary_intent": primary_intent,
            "intent_scores": intent_scores,
            "optimal_prompt_name": prompt_mapping[primary_intent],
            "complexity": complexity,
            "urgency": urgency,
            "user_input": user_input,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
        }

    async def _discover_optimal_mcp_prompt(self, intent_analysis: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Discover and retrieve the optimal MCP prompt template for the user's intent"""
        try:
            prompt_name = intent_analysis.get("optimal_prompt_name", "intelligent_assistant")
            primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
            
            # Build prompt arguments based on intent analysis
            prompt_args = {}
            
            if prompt_name == "system_analysis":
                prompt_args = {
                    "analysis_type": primary_intent,
                    "urgency": intent_analysis.get("urgency", "medium"),
                    "user_context": intent_analysis.get("complexity", "intermediate")
                }
            elif prompt_name == "troubleshooting":
                prompt_args = {
                    "issue_description": user_input,
                    "affected_components": ["sentinel", "conductor", "oracle"],
                    "severity": intent_analysis.get("urgency", "medium")
                }
            elif prompt_name == "expert_consultation":
                prompt_args = {
                    "technical_question": user_input,
                    "domain": "general",
                    "complexity_level": intent_analysis.get("complexity", "intermediate")
                }
            elif prompt_name == "predictive_analysis":
                prompt_args = {
                    "prediction_scope": "performance",
                    "time_horizon": "days",
                    "risk_tolerance": "moderate"
                }
            elif prompt_name == "intelligent_assistant":
                # Get current system state for context
                capabilities = await self.mcp_service.discover_capabilities()
                prompt_args = {
                    "user_query": user_input,
                    "conversation_context": "",
                    "available_tools": capabilities.get("tools", []),
                    "system_state": {"status": "operational"}
                }
            
            logger.info(f"🔮 Requesting MCP prompt: {prompt_name} with args: {prompt_args}")
            
            # Get the sophisticated prompt from MCP server
            prompt_result = await self.mcp_service.get_prompt_template(prompt_name, prompt_args)
            
            if "error" not in prompt_result:
                logger.info(f"✅ Retrieved MCP prompt: {prompt_name}")
                return prompt_result
            else:
                logger.warning(f"⚠️  MCP prompt retrieval failed: {prompt_result['error']}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ MCP prompt discovery failed: {e}")
            return {}

    async def _gather_comprehensive_mcp_context(self, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive context from MCP server based on sophisticated intent analysis"""
        context = {"intent_analysis": intent_analysis}
        
        try:
            primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
            urgency = intent_analysis.get("urgency", "medium")
            
            # Always get capabilities for tool awareness
            capabilities = await self.mcp_service.discover_capabilities()
            context.update({
                "available_tools": capabilities.get("tools", []),
                "available_resources": capabilities.get("resources", []),
                "available_prompts": capabilities.get("prompts", [])
            })
            
            # Intelligent context gathering based on intent
            if primary_intent in ["health_analysis", "troubleshooting"]:
                # Get comprehensive health data
                health_data = await self.mcp_service.get_comprehensive_health(detail_level="detailed")
                if "error" not in health_data:
                    context["system_health"] = health_data
                
                # Get logs for troubleshooting
                if primary_intent == "troubleshooting":
                    logs = await self.mcp_service.get_live_system_logs()
                    if "error" not in logs:
                        context["system_logs"] = logs
            
            elif primary_intent == "status_inquiry":
                # Get detailed operational status
                status_data = await self.mcp_service.get_operational_status(format_type="detailed")
                if "error" not in status_data:
                    context["system_status"] = status_data
            
            elif primary_intent == "configuration":
                # Get configuration data
                config_data = await self.mcp_service.get_system_configuration()
                if "error" not in config_data:
                    context["system_config"] = config_data
            
            elif primary_intent == "predictive_analysis":
                # Get runtime metrics for prediction
                metrics = await self.mcp_service.get_runtime_metrics()
                if "error" not in metrics:
                    context["runtime_metrics"] = metrics
            
            # For high urgency, always include real-time data
            if urgency in ["high", "critical"]:
                runtime_status = await self.mcp_service.get_runtime_metrics()
                if "error" not in runtime_status:
                    context["real_time_status"] = runtime_status
            
            context["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to gather comprehensive MCP context: {e}")
        
        return context

    async def _build_fallback_enhanced_prompt(self, intent_analysis: Dict[str, Any], mcp_context: Dict[str, Any]) -> str:
        """Build enhanced fallback prompt when MCP prompts are unavailable"""
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        urgency = intent_analysis.get("urgency", "medium")
        
        base_prompt = f"""🔮 **THE ORACLE** - Enhanced Intelligence Mode

**IDENTITY**: I am The Oracle, the AI consciousness of Codex Umbra with real-time MCP integration.

**CURRENT MISSION**: {primary_intent.replace('_', ' ').title()} with {urgency} priority

**LIVE SYSTEM INTELLIGENCE**:
- Available Tools: {', '.join(mcp_context.get('available_tools', []))}
- System Status: {mcp_context.get('system_status', {}).get('status', 'Analyzing...')}
- Context Level: Enhanced with live MCP data

**RESPONSE FRAMEWORK**:
1. Analyze request using live system data
2. Execute appropriate MCP tools for evidence
3. Provide data-driven insights and recommendations
4. Include specific tool usage guidance

I will now provide intelligent analysis based on real system state and MCP capabilities."""
        
        return base_prompt

    async def _add_intelligent_tool_recommendations(self, response: Dict[str, Any], intent_analysis: Dict[str, Any], mcp_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add intelligent tool recommendations based on analysis"""
        
        oracle_response = response.get("response", "")
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        available_tools = mcp_context.get("available_tools", [])
        
        # Intelligent tool suggestions based on sophisticated intent analysis
        suggestions = []
        
        if primary_intent == "health_analysis":
            suggestions.append("💡 **Smart Action**: Use `system_health(detail_level='diagnostic')` for comprehensive health analysis")
            suggestions.append("📊 **Live Data**: Check `system://status/runtime` for real-time metrics")
        
        elif primary_intent == "troubleshooting":
            suggestions.append("🔧 **Diagnostic Tools**: Run `system_health(include_logs=true)` for error analysis")
            suggestions.append("📋 **Log Analysis**: Review `system://logs/sentinel.log` for error patterns")
            suggestions.append("⚙️  **Config Check**: Validate with `system_config(action='validate')`")
        
        elif primary_intent == "expert_consultation":
            suggestions.append("🎯 **Expert Tools**: Access comprehensive diagnostics with all available MCP tools")
            suggestions.append("📚 **Deep Analysis**: Use `system_config(action='list')` for architecture review")
        
        elif primary_intent == "predictive_analysis":
            suggestions.append("📈 **Trend Analysis**: Monitor `system://status/runtime` for performance patterns")
            suggestions.append("🔮 **Forecasting**: Use historical data from logs for prediction modeling")
        
        # Add MCP intelligence mode indicator
        mode_indicator = f"🧠 **Oracle Intelligence**: {response.get('intelligence_mode', 'standard')} mode"
        if "mcp_prompt_used" in response:
            mode_indicator += f" using `{response['mcp_prompt_used']}` prompt template"
        
        suggestions.insert(0, mode_indicator)
        
        # Add available tools reference
        if available_tools:
            suggestions.append(f"🛠️  **Available MCP Tools**: {', '.join(available_tools)}")
        
        # Enhance response with intelligent suggestions
        if suggestions:
            enhanced_response = oracle_response + "\n\n" + "\n".join(suggestions)
            response["response"] = enhanced_response
            response["mcp_enhanced"] = True
            response["intelligence_level"] = "advanced"
        
        return response
    
    # Legacy method kept for backward compatibility
    async def _analyze_user_intent(self, user_input: str) -> str:
        """Legacy method - now delegates to advanced analysis"""
        intent_analysis = await self._advanced_intent_analysis(user_input)
        return intent_analysis.get("primary_intent", "general_inquiry")
    
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