"""
MCP Client Implementation for The Conductor
Full JSON-RPC 2.0 client with dynamic tool discovery and resource access
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import traceback

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class MCPClientError(Exception):
    """MCP Client Error"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Client Error {code}: {message}")

class MCPClient:
    """
    Full MCP Protocol Client for communicating with The Sentinel
    Supports dynamic tool discovery, resource access, and prompt templates
    """
    
    def __init__(self, server_url: str = "http://localhost:8001", websocket_url: str = "ws://localhost:8001/mcp"):
        self.server_url = server_url
        self.websocket_url = websocket_url
        self.websocket = None
        self.request_id = 0
        self.capabilities = {}
        self.available_tools: Dict[str, Any] = {}
        self.available_resources: Dict[str, Any] = {}
        self.available_prompts: Dict[str, Any] = {}
        self.initialized = False
        
    async def connect(self, use_websocket: bool = True) -> bool:
        """Connect to MCP server and initialize"""
        try:
            if use_websocket:
                await self._connect_websocket()
            
            # Initialize MCP session
            await self._initialize_session()
            
            # Discover capabilities
            await self._discover_capabilities()
            
            self.initialized = True
            logger.info("✅ MCP Client connected and initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.initialized = False
        logger.info("🔌 MCP Client disconnected")
    
    async def _connect_websocket(self):
        """Connect to MCP server via WebSocket"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info(f"🔗 Connected to MCP server via WebSocket: {self.websocket_url}")
        except Exception as e:
            logger.warning(f"⚠️  WebSocket connection failed: {e}, falling back to HTTP")
            self.websocket = None
    
    async def _initialize_session(self):
        """Initialize MCP session with capability negotiation"""
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "conductor-mcp-client",
                "version": "2.0.0"
            }
        }
        
        response = await self._send_request("initialize", init_params)
        
        if "error" in response:
            raise MCPClientError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        result = response.get("result", {})
        self.capabilities = result.get("capabilities", {})
        server_info = result.get("serverInfo", {})
        
        logger.info(f"🤝 MCP Session initialized with server: {server_info.get('name', 'unknown')}")
        logger.info(f"📋 Server capabilities: {list(self.capabilities.keys())}")
    
    async def _discover_capabilities(self):
        """Discover available tools, resources, and prompts"""
        
        # Discover tools
        if self.capabilities.get("tools"):
            tools_response = await self._send_request("tools/list")
            if "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                for tool in tools:
                    self.available_tools[tool["name"]] = tool
                logger.info(f"🛠️  Discovered {len(self.available_tools)} tools: {list(self.available_tools.keys())}")
        
        # Discover resources
        if self.capabilities.get("resources"):
            resources_response = await self._send_request("resources/list")
            if "result" in resources_response:
                resources = resources_response["result"].get("resources", [])
                for resource in resources:
                    self.available_resources[resource["uri"]] = resource
                logger.info(f"📚 Discovered {len(self.available_resources)} resources: {list(self.available_resources.keys())}")
        
        # Discover prompts
        if self.capabilities.get("prompts"):
            prompts_response = await self._send_request("prompts/list")
            if "result" in prompts_response:
                prompts = prompts_response["result"].get("prompts", [])
                for prompt in prompts:
                    self.available_prompts[prompt["name"]] = prompt
                logger.info(f"💭 Discovered {len(self.available_prompts)} prompts: {list(self.available_prompts.keys())}")
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 request to MCP server"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id
        }
        
        if params:
            request["params"] = params
        
        logger.debug(f"📤 Sending MCP request: {method} (ID: {self.request_id})")
        
        try:
            if self.websocket:
                # Use WebSocket transport
                await self.websocket.send(json.dumps(request))
                response_text = await self.websocket.recv()
                response = json.loads(response_text)
            else:
                # Use HTTP transport
                async with httpx.AsyncClient(timeout=30.0) as client:
                    http_response = await client.post(
                        f"{self.server_url}/mcp/rpc",
                        json=request
                    )
                    response = http_response.json()
            
            logger.debug(f"📨 Received MCP response for {method}: {response.get('result', response.get('error', 'unknown'))}")
            return response
            
        except Exception as e:
            logger.error(f"❌ MCP request failed for {method}: {e}")
            return {"error": {"code": -32603, "message": f"Transport error: {str(e)}"}}
    
    # High-level MCP Operations
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool with dynamic discovery"""
        if not self.initialized:
            await self.connect()
        
        if tool_name not in self.available_tools:
            return {"error": f"Tool '{tool_name}' not available. Available tools: {list(self.available_tools.keys())}"}
        
        tool_params = {"name": tool_name}
        if arguments:
            tool_params["arguments"] = arguments
        
        logger.info(f"🔧 Calling tool: {tool_name} with args: {arguments}")
        
        response = await self._send_request("tools/call", tool_params)
        
        if "error" in response:
            logger.error(f"❌ Tool call failed: {response['error']}")
            return {"error": response["error"]["message"]}
        
        return response.get("result", {})
    
    async def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Read an MCP resource"""
        if not self.initialized:
            await self.connect()
        
        if resource_uri not in self.available_resources:
            return {"error": f"Resource '{resource_uri}' not available. Available resources: {list(self.available_resources.keys())}"}
        
        logger.info(f"📖 Reading resource: {resource_uri}")
        
        response = await self._send_request("resources/read", {"uri": resource_uri})
        
        if "error" in response:
            logger.error(f"❌ Resource read failed: {response['error']}")
            return {"error": response["error"]["message"]}
        
        return response.get("result", {})
    
    async def get_prompt(self, prompt_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get an MCP prompt template"""
        if not self.initialized:
            await self.connect()
        
        if prompt_name not in self.available_prompts:
            return {"error": f"Prompt '{prompt_name}' not available. Available prompts: {list(self.available_prompts.keys())}"}
        
        prompt_params = {"name": prompt_name}
        if arguments:
            prompt_params["arguments"] = arguments
        
        logger.info(f"💬 Getting prompt: {prompt_name} with args: {arguments}")
        
        response = await self._send_request("prompts/get", prompt_params)
        
        if "error" in response:
            logger.error(f"❌ Prompt get failed: {response['error']}")
            return {"error": response["error"]["message"]}
        
        return response.get("result", {})
    
    # Convenience methods for common operations
    async def get_system_health(self, component: str = "all", detail_level: str = "basic", include_logs: bool = False) -> Dict[str, Any]:
        """Get comprehensive system health via MCP tool"""
        return await self.call_tool("system_health", {
            "component": component,
            "detail_level": detail_level,
            "include_logs": include_logs
        })
    
    async def get_system_status(self, component: str = "all", format_type: str = "summary") -> Dict[str, Any]:
        """Get system status via MCP tool"""
        return await self.call_tool("system_status", {
            "component": component,
            "format": format_type
        })
    
    async def get_system_config(self, action: str = "list", config_key: str = None, component: str = None) -> Dict[str, Any]:
        """Access system configuration via MCP tool"""
        args = {"action": action}
        if config_key:
            args["config_key"] = config_key
        if component:
            args["component"] = component
        
        return await self.call_tool("system_config", args)
    
    async def get_system_logs(self) -> Dict[str, Any]:
        """Get system logs via MCP resource"""
        return await self.read_resource("system://logs/sentinel.log")
    
    async def get_runtime_status(self) -> Dict[str, Any]:
        """Get runtime status via MCP resource"""
        return await self.read_resource("system://status/runtime")
    
    async def get_capabilities_config(self) -> Dict[str, Any]:
        """Get capabilities configuration via MCP resource"""
        return await self.read_resource("system://config/capabilities")
    
    async def get_analysis_prompt(self, analysis_type: str, urgency: str = "medium") -> Dict[str, Any]:
        """Get system analysis prompt template"""
        return await self.get_prompt("system_analysis", {
            "analysis_type": analysis_type,
            "urgency": urgency
        })
    
    async def get_troubleshooting_prompt(self, issue_description: str, affected_components: List[str] = None) -> Dict[str, Any]:
        """Get troubleshooting prompt template"""
        args = {"issue_description": issue_description}
        if affected_components:
            args["affected_components"] = affected_components
        
        return await self.get_prompt("troubleshooting", args)
    
    # Legacy compatibility methods
    async def legacy_status(self) -> Dict[str, Any]:
        """Legacy status method for backward compatibility"""
        response = await self._send_request("legacy/status")
        return response.get("result", {"status": "unknown"})
    
    async def legacy_health(self) -> Dict[str, Any]:
        """Legacy health method for backward compatibility"""  
        response = await self._send_request("legacy/health")
        return response.get("result", {"status": "unknown"})
    
    # Utility methods
    def list_available_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.available_tools.keys())
    
    def list_available_resources(self) -> List[str]:
        """List all available resources"""
        return list(self.available_resources.keys())
    
    def list_available_prompts(self) -> List[str]:
        """List all available prompts"""
        return list(self.available_prompts.keys())
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool"""
        return self.available_tools.get(tool_name)
    
    def is_connected(self) -> bool:
        """Check if client is connected and initialized"""
        return self.initialized and (self.websocket is not None or self.server_url is not None)