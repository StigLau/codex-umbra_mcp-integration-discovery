"""
Enhanced MCP Service for The Conductor
Uses proper MCP protocol client for dynamic tool discovery and resource access
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .mcp_client import MCPClient, MCPClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

class MCPServiceV2:
    """
    Enhanced MCP Service using proper MCP protocol
    Provides dynamic tool discovery, resource access, and intelligent routing
    """
    
    def __init__(self):
        self.client = MCPClient(
            server_url=f"http://{settings.mcp_host}:{settings.mcp_port}",
            websocket_url=f"ws://{settings.mcp_host}:{settings.mcp_port}/mcp"
        )
        self._connection_ready = False
    
    async def _ensure_connection(self):
        """Ensure MCP client is connected and ready"""
        if not self._connection_ready:
            success = await self.client.connect()
            if success:
                self._connection_ready = True
                logger.info("🔗 MCP Service connected to The Sentinel")
            else:
                logger.error("❌ Failed to connect MCP Service to The Sentinel")
                raise MCPClientError(-32603, "Failed to connect to MCP server")
    
    # Dynamic Tool Access
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call any available MCP tool dynamically"""
        await self._ensure_connection()
        
        logger.info(f"🔧 MCP Tool Call: {tool_name} with args: {arguments}")
        
        try:
            result = await self.client.call_tool(tool_name, arguments)
            
            if "error" in result:
                logger.error(f"❌ Tool call failed: {result['error']}")
                return {"error": result["error"]}
            
            logger.info(f"✅ Tool call successful: {tool_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP tool call exception: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    async def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Read any available MCP resource dynamically"""
        await self._ensure_connection()
        
        logger.info(f"📖 MCP Resource Read: {resource_uri}")
        
        try:
            result = await self.client.read_resource(resource_uri)
            
            if "error" in result:
                logger.error(f"❌ Resource read failed: {result['error']}")
                return {"error": result["error"]}
            
            logger.info(f"✅ Resource read successful: {resource_uri}")
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP resource read exception: {e}")
            return {"error": f"Resource read failed: {str(e)}"}
    
    async def get_prompt_template(self, prompt_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get dynamic prompt template from MCP server"""
        await self._ensure_connection()
        
        logger.info(f"💬 MCP Prompt Request: {prompt_name} with args: {arguments}")
        
        try:
            result = await self.client.get_prompt(prompt_name, arguments)
            
            if "error" in result:
                logger.error(f"❌ Prompt get failed: {result['error']}")
                return {"error": result["error"]}
            
            logger.info(f"✅ Prompt template retrieved: {prompt_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP prompt get exception: {e}")
            return {"error": f"Prompt get failed: {str(e)}"}
    
    # High-Level System Operations
    async def get_comprehensive_health(self, component: str = "all", detail_level: str = "detailed") -> Dict[str, Any]:
        """Get comprehensive system health analysis"""
        return await self.call_tool("system_health", {
            "component": component,
            "detail_level": detail_level,
            "include_logs": True
        })
    
    async def get_operational_status(self, component: str = "all", format_type: str = "detailed") -> Dict[str, Any]:
        """Get detailed operational status"""
        return await self.call_tool("system_status", {
            "component": component,
            "format": format_type
        })
    
    async def get_system_configuration(self, action: str = "list", config_key: str = None) -> Dict[str, Any]:
        """Access system configuration"""
        args = {"action": action}
        if config_key:
            args["config_key"] = config_key
        
        return await self.call_tool("system_config", args)
    
    async def get_live_system_logs(self) -> Dict[str, Any]:
        """Get live system logs via MCP resource"""
        return await self.read_resource("system://logs/sentinel.log")
    
    async def get_runtime_metrics(self) -> Dict[str, Any]:
        """Get runtime metrics via MCP resource"""
        return await self.read_resource("system://status/runtime")
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities configuration"""
        return await self.read_resource("system://config/capabilities")
    
    # Intelligent Query Routing
    async def intelligent_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Intelligently route user queries to appropriate MCP tools/resources
        Uses dynamic discovery to determine best response strategy
        """
        await self._ensure_connection()
        
        query_lower = user_query.lower().strip()
        logger.info(f"🧠 Intelligent query routing for: '{user_query}'")
        
        # Determine query intent and route to appropriate MCP capabilities
        if any(keyword in query_lower for keyword in ["health", "diagnostic", "check", "status"]):
            if "detailed" in query_lower or "comprehensive" in query_lower:
                return await self.get_comprehensive_health(detail_level="diagnostic")
            else:
                return await self.get_comprehensive_health(detail_level="basic")
        
        elif any(keyword in query_lower for keyword in ["status", "operational", "running"]):
            return await self.get_operational_status(format_type="detailed")
        
        elif any(keyword in query_lower for keyword in ["config", "configuration", "settings"]):
            return await self.get_system_configuration(action="list")
        
        elif any(keyword in query_lower for keyword in ["logs", "log", "entries"]):
            return await self.get_live_system_logs()
        
        elif any(keyword in query_lower for keyword in ["metrics", "performance", "runtime"]):
            return await self.get_runtime_metrics()
        
        elif any(keyword in query_lower for keyword in ["capabilities", "tools", "available"]):
            return await self.get_system_capabilities()
        
        else:
            # Default: get general status
            return await self.get_operational_status()
    
    # Discovery and Introspection
    async def discover_capabilities(self) -> Dict[str, Any]:
        """Discover all available MCP capabilities"""
        await self._ensure_connection()
        
        capabilities = {
            "tools": self.client.list_available_tools(),
            "resources": self.client.list_available_resources(),
            "prompts": self.client.list_available_prompts(),
            "connection_status": self.client.is_connected(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"📋 MCP Capabilities discovered: {len(capabilities['tools'])} tools, {len(capabilities['resources'])} resources, {len(capabilities['prompts'])} prompts")
        
        return capabilities
    
    async def get_tool_documentation(self, tool_name: str) -> Dict[str, Any]:
        """Get documentation for a specific tool"""
        await self._ensure_connection()
        
        schema = self.client.get_tool_schema(tool_name)
        if not schema:
            return {"error": f"Tool '{tool_name}' not found"}
        
        return {
            "tool_name": tool_name,
            "description": schema.get("description", "No description available"),
            "input_schema": schema.get("inputSchema", {}),
            "usage_examples": self._generate_tool_examples(tool_name, schema)
        }
    
    def _generate_tool_examples(self, tool_name: str, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate usage examples for a tool based on its schema"""
        examples = []
        
        if tool_name == "system_health":
            examples = [
                {"description": "Basic health check", "arguments": {"component": "all"}},
                {"description": "Detailed health with logs", "arguments": {"component": "sentinel", "detail_level": "detailed", "include_logs": True}},
                {"description": "Diagnostic analysis", "arguments": {"component": "all", "detail_level": "diagnostic"}}
            ]
        elif tool_name == "system_status":
            examples = [
                {"description": "Summary status", "arguments": {"component": "all", "format": "summary"}},
                {"description": "Detailed status", "arguments": {"component": "conductor", "format": "detailed"}}
            ]
        elif tool_name == "system_config":
            examples = [
                {"description": "List configurations", "arguments": {"action": "list"}},
                {"description": "Get specific config", "arguments": {"action": "get", "config_key": "mcp.protocol_version"}},
                {"description": "Validate configuration", "arguments": {"action": "validate"}}
            ]
        
        return examples
    
    # Legacy Compatibility
    async def get_status(self) -> Dict[str, Any]:
        """Legacy status method - now uses MCP tools"""
        try:
            # Use new MCP tool instead of legacy endpoint
            result = await self.get_operational_status(component="sentinel", format_type="summary")
            
            if "error" in result:
                # Fallback to legacy if MCP fails
                return await self.client.legacy_status()
            
            # Extract status from MCP tool result
            content = result.get("content", [])
            if content and len(content) > 0:
                status_text = content[0].get("text", "{}")
                try:
                    import json
                    status_data = json.loads(status_text)
                    return {
                        "status": status_data.get("status", "Unknown"),
                        "version": status_data.get("version", "2.0.0"),
                        "mcp_enabled": True
                    }
                except:
                    pass
            
            return {"status": "MCP Operational", "version": "2.0.0", "mcp_enabled": True}
            
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return {"error": f"Status check failed: {str(e)}"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Legacy health check - now uses MCP tools"""
        try:
            # Use new MCP tool instead of legacy endpoint
            result = await self.get_comprehensive_health(component="sentinel", detail_level="basic")
            
            if "error" in result:
                # Fallback to legacy if MCP fails
                return await self.client.legacy_health()
            
            # Extract health from MCP tool result
            content = result.get("content", [])
            if content and len(content) > 0:
                health_text = content[0].get("text", "{}")
                try:
                    import json
                    health_data = json.loads(health_text)
                    return {
                        "status": health_data.get("status", "unknown"),
                        "version": "2.0.0",
                        "timestamp": health_data.get("timestamp"),
                        "mcp_enabled": True,
                        "dependencies": {"mcp_server": "operational"}
                    }
                except:
                    pass
            
            return {
                "status": "healthy",
                "version": "2.0.0", 
                "mcp_enabled": True,
                "dependencies": {"mcp_server": "operational"}
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {"error": f"Health check failed: {str(e)}"}
    
    # Cleanup
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self._connection_ready:
            await self.client.disconnect()
            self._connection_ready = False
            logger.info("🔌 MCP Service disconnected")