"""
MCP Protocol Implementation for The Sentinel
Full JSON-RPC 2.0 MCP Server with dynamic tool discovery and resource management
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

import aiofiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Async Operation Framework
class OperationStatus(Enum):
    """Async operation status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AsyncOperation:
    """Async operation tracking"""
    operation_id: str
    tool_name: str
    arguments: Dict[str, Any]
    status: OperationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "operation_id": self.operation_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() + "Z",
            "started_at": self.started_at.isoformat() + "Z" if self.started_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "progress": self.progress
        }

# MCP Protocol Data Models
class MCPError(Exception):
    """MCP Protocol Error"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")

@dataclass
class MCPCapabilities:
    """MCP Server Capabilities"""
    tools: Dict[str, Any] = None
    resources: Dict[str, Any] = None
    prompts: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = {"listChanged": True}
        if self.resources is None:
            self.resources = {"subscribe": True, "listChanged": True}
        if self.prompts is None:
            self.prompts = {"listChanged": True}

@dataclass
class MCPTool:
    """MCP Tool Definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass 
class MCPResource:
    """MCP Resource Definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

@dataclass
class MCPPrompt:
    """MCP Prompt Template"""
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None

class MCPServer:
    """
    Full MCP Protocol Server Implementation for The Sentinel
    Provides dynamic tool discovery, resource management, and capability negotiation
    """
    
    def __init__(self):
        self.capabilities = MCPCapabilities()
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # client_id -> [resource_uris]
        
        # Async Operation Management
        self.operations: Dict[str, AsyncOperation] = {}  # operation_id -> operation
        self.operation_tasks: Dict[str, asyncio.Task] = {}  # operation_id -> task
        self._operation_lock = asyncio.Lock()
        
        self._setup_default_capabilities()
    
    def _setup_default_capabilities(self):
        """Setup default Sentinel capabilities"""
        
        # System Health Tool
        self.tools["system_health"] = MCPTool(
            name="system_health",
            description="Comprehensive system health analysis with configurable detail levels and response formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": ["sentinel", "conductor", "oracle", "all"],
                        "description": "System component to analyze"
                    },
                    "detail_level": {
                        "type": "string", 
                        "enum": ["basic", "detailed", "diagnostic"],
                        "default": "basic",
                        "description": "Level of detail in health report"
                    },
                    "include_logs": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include recent log entries in report"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "text",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format, 'both' for compatibility"
                    },
                    "async_mode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Run operation asynchronously for long-running tasks. Returns operation ID for status tracking."
                    }
                },
                "required": ["component"]
            }
        )
        
        # System Status Tool
        self.tools["system_status"] = MCPTool(
            name="system_status",
            description="Get current operational status of system components with enhanced response formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": ["sentinel", "conductor", "oracle", "all"],
                        "description": "Component to check status for"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["summary", "detailed", "json"],
                        "default": "summary",
                        "description": "Status report format"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "text",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format, 'both' for compatibility"
                    },
                    "async_mode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Run operation asynchronously for long-running tasks. Returns operation ID for status tracking."
                    }
                },
                "required": ["component"]
            }
        )
        
        # System Configuration Tool  
        self.tools["system_config"] = MCPTool(
            name="system_config",
            description="Access and manage system configuration with enhanced response formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get", "list", "validate"],
                        "description": "Configuration action to perform"
                    },
                    "config_key": {
                        "type": "string",
                        "description": "Specific configuration key (for get action)"
                    },
                    "component": {
                        "type": "string", 
                        "enum": ["sentinel", "conductor", "oracle"],
                        "description": "Component configuration to access"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "text",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format, 'both' for compatibility"
                    },
                    "async_mode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Run operation asynchronously for long-running tasks. Returns operation ID for status tracking."
                    }
                },
                "required": ["action"]
            }
        )
        
        # Simple Addition Tool - For testing function calling
        self.tools["add_numbers"] = MCPTool(
            name="add_numbers",
            description="Add two numbers together and return the result with enhanced response formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number to add"
                    },
                    "b": {
                        "type": "number", 
                        "description": "Second number to add"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["simple", "detailed"],
                        "default": "simple",
                        "description": "Calculation detail level"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "text",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format, 'both' for compatibility"
                    }
                },
                "required": ["a", "b"]
            }
        )
        
        # Enhanced Tooling - Oracle Requested Features
        self.tools["search_logs"] = MCPTool(
            name="search_logs",
            description="Search system logs with keyword filtering, time range, and severity level - Oracle efficiency optimized",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword or pattern to search for in logs"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["all", "debug", "info", "warning", "error", "critical"],
                        "default": "all",
                        "description": "Filter by log severity level"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["last_hour", "last_day", "last_week", "all"],
                        "default": "last_day",
                        "description": "Time range for log search"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 1000,
                        "description": "Maximum number of log entries to return"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": ["keyword"]
            }
        )
        
        self.tools["get_config"] = MCPTool(
            name="get_config",
            description="Get specific configuration parameter with granular access - Oracle efficiency optimized",
            inputSchema={
                "type": "object",
                "properties": {
                    "parameter": {
                        "type": "string",
                        "description": "Specific configuration parameter path (e.g., 'mcp.protocol_version', 'sentinel.capabilities.tools')"
                    },
                    "component": {
                        "type": "string",
                        "enum": ["sentinel", "conductor", "oracle", "system"],
                        "default": "system",
                        "description": "Component scope for configuration parameter"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include parameter metadata (type, default, description)"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": ["parameter"]
            }
        )
        
        # Async Operation Management Tools
        self.tools["operation_status"] = MCPTool(
            name="operation_status",
            description="Check the status of an async operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "Operation ID to check status for"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": ["operation_id"]
            }
        )
        
        self.tools["operation_result"] = MCPTool(
            name="operation_result",
            description="Get the result of a completed async operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "Operation ID to get result for"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": ["operation_id"]
            }
        )
        
        self.tools["list_operations"] = MCPTool(
            name="list_operations",
            description="List all async operations with their status",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["all", "pending", "running", "completed", "failed", "cancelled"],
                        "default": "all",
                        "description": "Filter operations by status"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": []
            }
        )
        
        self.tools["cancel_operation"] = MCPTool(
            name="cancel_operation",
            description="Cancel a running or pending async operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "Operation ID to cancel"
                    },
                    "response_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "default": "json",
                        "description": "Response format: 'json' for structured data (Oracle efficient), 'text' for readable format"
                    }
                },
                "required": ["operation_id"]
            }
        )
        
        # Resources - System data exposure
        self.resources["system://logs/sentinel.log"] = MCPResource(
            uri="system://logs/sentinel.log",
            name="Sentinel System Logs",
            description="Real-time system logs from The Sentinel MCP server",
            mimeType="text/plain"
        )
        
        self.resources["system://status/runtime"] = MCPResource(
            uri="system://status/runtime", 
            name="Runtime Status",
            description="Current runtime status and metrics",
            mimeType="application/json"
        )
        
        self.resources["system://config/capabilities"] = MCPResource(
            uri="system://config/capabilities",
            name="System Capabilities",
            description="Available system capabilities and configurations",
            mimeType="application/json"
        )
        
        # Advanced Prompt Templates - Oracle Intelligence Enhancement
        self.prompts["system_analysis"] = MCPPrompt(
            name="system_analysis",
            description="Comprehensive system analysis with dynamic tool integration",
            arguments=[
                {"name": "analysis_type", "description": "Type of analysis requested", "required": True},
                {"name": "urgency", "description": "Urgency level (low/medium/high)", "required": False},
                {"name": "user_context", "description": "User's background/expertise level", "required": False}
            ]
        )
        
        self.prompts["troubleshooting"] = MCPPrompt(
            name="troubleshooting", 
            description="Intelligent troubleshooting with step-by-step guidance",
            arguments=[
                {"name": "issue_description", "description": "Description of the issue", "required": True},
                {"name": "affected_components", "description": "List of affected components", "required": False},
                {"name": "severity", "description": "Issue severity (low/medium/high/critical)", "required": False}
            ]
        )
        
        self.prompts["intelligent_assistant"] = MCPPrompt(
            name="intelligent_assistant",
            description="Oracle's primary intelligence prompt with full MCP context awareness",
            arguments=[
                {"name": "user_query", "description": "User's question or request", "required": True},
                {"name": "conversation_context", "description": "Previous conversation context", "required": False},
                {"name": "available_tools", "description": "Currently available MCP tools", "required": False},
                {"name": "system_state", "description": "Current system state summary", "required": False}
            ]
        )
        
        self.prompts["expert_consultation"] = MCPPrompt(
            name="expert_consultation",
            description="Deep technical consultation with comprehensive system knowledge",
            arguments=[
                {"name": "technical_question", "description": "Technical question requiring expert knowledge", "required": True},
                {"name": "domain", "description": "Technical domain (networking, security, performance, etc.)", "required": False},
                {"name": "complexity_level", "description": "Required complexity level (beginner/intermediate/expert)", "required": False}
            ]
        )
        
        self.prompts["predictive_analysis"] = MCPPrompt(
            name="predictive_analysis",
            description="Predictive system analysis and recommendations",
            arguments=[
                {"name": "prediction_scope", "description": "Scope of prediction (performance, security, maintenance)", "required": True},
                {"name": "time_horizon", "description": "Prediction time horizon (hours/days/weeks)", "required": False},
                {"name": "risk_tolerance", "description": "Risk tolerance level (conservative/moderate/aggressive)", "required": False}
            ]
        )

    # MCP Protocol Methods
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        protocol_version = params.get("protocolVersion", "2024-11-05")
        client_capabilities = params.get("capabilities", {})
        
        logger.info(f"🔗 MCP Initialize: protocol={protocol_version}, client_caps={client_capabilities}")
        
        return {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True}, 
                "prompts": {"listChanged": True}
            },
            "serverInfo": {
                "name": "sentinel-mcp-server",
                "version": "2.0.0"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle tools/list request - dynamic tool discovery"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        
        logger.info(f"🛠️  Tools List Request: returning {len(tools_list)} tools")
        return {"tools": tools_list}
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request - execute requested tool with enhanced response formats"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Check for response format preference
        response_format = arguments.get("response_format", "text")  # "text", "json", "both"
        
        logger.info(f"🔧 Tool Call: {tool_name} with args {arguments}, format: {response_format}")
        
        if tool_name not in self.tools:
            raise MCPError(-32601, f"Tool not found: {tool_name}")
        
        # Check for async mode
        async_mode = arguments.get("async_mode", False)
        
        # Handle async mode for eligible tools
        if async_mode and tool_name in ["system_health", "system_status", "system_config"]:
            return await self._handle_async_operation(tool_name, arguments)
        
        # Route to appropriate tool handler
        if tool_name == "system_health":
            return await self._handle_system_health(arguments)
        elif tool_name == "system_status":
            return await self._handle_system_status(arguments)
        elif tool_name == "system_config":
            return await self._handle_system_config(arguments)
        elif tool_name == "add_numbers":
            return await self._handle_add_numbers(arguments)
        # Enhanced tooling - Oracle requested features
        elif tool_name == "search_logs":
            return await self._handle_search_logs(arguments)
        elif tool_name == "get_config":
            return await self._handle_get_config(arguments)
        # Async operation management tools
        elif tool_name == "operation_status":
            return await self._handle_operation_status(arguments)
        elif tool_name == "operation_result":
            return await self._handle_operation_result(arguments)
        elif tool_name == "list_operations":
            return await self._handle_list_operations(arguments)
        elif tool_name == "cancel_operation":
            return await self._handle_cancel_operation(arguments)
        else:
            raise MCPError(-32603, f"Tool handler not implemented: {tool_name}")
    
    async def handle_resources_list(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mimeType
            })
        
        logger.info(f"📚 Resources List: returning {len(resources_list)} resources")
        return {"resources": resources_list}
    
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            raise MCPError(-32601, f"Resource not found: {uri}")
        
        logger.info(f"📖 Resource Read: {uri}")
        
        # Route to appropriate resource handler
        if uri == "system://logs/sentinel.log":
            return await self._read_system_logs()
        elif uri == "system://status/runtime":
            return await self._read_runtime_status()
        elif uri == "system://config/capabilities":
            return await self._read_capabilities_config()
        else:
            raise MCPError(-32603, f"Resource handler not implemented: {uri}")
    
    async def handle_prompts_list(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle prompts/list request"""
        prompts_list = []
        for prompt in self.prompts.values():
            prompts_list.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments or []
            })
        
        logger.info(f"💭 Prompts List: returning {len(prompts_list)} prompts")
        return {"prompts": prompts_list}
    
    async def handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name not in self.prompts:
            raise MCPError(-32601, f"Prompt not found: {prompt_name}")
        
        logger.info(f"💬 Prompt Get: {prompt_name} with args {arguments}")
        
        # Generate dynamic prompt based on template and arguments
        if prompt_name == "system_analysis":
            return await self._generate_system_analysis_prompt(arguments)
        elif prompt_name == "troubleshooting":
            return await self._generate_troubleshooting_prompt(arguments)
        elif prompt_name == "intelligent_assistant":
            return await self._generate_intelligent_assistant_prompt(arguments)
        elif prompt_name == "expert_consultation":
            return await self._generate_expert_consultation_prompt(arguments)
        elif prompt_name == "predictive_analysis":
            return await self._generate_predictive_analysis_prompt(arguments)
        else:
            raise MCPError(-32603, f"Prompt handler not implemented: {prompt_name}")

    # Tool Handlers
    async def _handle_system_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system_health tool execution with enhanced response formats"""
        component = args.get("component", "all")
        detail_level = args.get("detail_level", "basic")
        include_logs = args.get("include_logs", False)
        response_format = args.get("response_format", "text")
        
        health_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": component,
            "detail_level": detail_level,
            "status": "healthy",
            "checks": {
                "memory_usage": "normal",
                "cpu_usage": "normal", 
                "disk_space": "sufficient",
                "network": "connected"
            }
        }
        
        if detail_level == "detailed":
            health_data["metrics"] = {
                "uptime_seconds": 3600,
                "requests_handled": 150,
                "average_response_time_ms": 45,
                "error_rate_percent": 0.1
            }
        
        if detail_level == "diagnostic":
            health_data["diagnostics"] = {
                "mcp_protocol_version": "2024-11-05",
                "capabilities_loaded": len(self.tools),
                "active_subscriptions": len(self.subscriptions),
                "last_error": None
            }
        
        if include_logs:
            health_data["recent_logs"] = await self._get_recent_logs()
        
        return self._format_response(health_data, response_format)
    
    async def _handle_system_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system_status tool execution with enhanced response formats"""
        component = args.get("component", "all")
        format_type = args.get("format", "summary")
        response_format = args.get("response_format", "text")
        
        status_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": component,
            "status": "MCP Operational",
            "version": "2.0.0"
        }
        
        if format_type == "detailed":
            status_data.update({
                "capabilities": {
                    "tools_available": len(self.tools),
                    "resources_available": len(self.resources),
                    "prompts_available": len(self.prompts)
                },
                "connections": {
                    "active_clients": 1,
                    "subscriptions": len(self.subscriptions)
                }
            })
        
        return self._format_response(status_data, response_format)
    
    async def _handle_system_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system_config tool execution with enhanced response formats"""
        action = args.get("action")
        config_key = args.get("config_key")
        component = args.get("component")
        response_format = args.get("response_format", "text")
        
        config_data = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if action == "list":
            config_data["available_configs"] = [
                "mcp.protocol_version",
                "mcp.capabilities.tools",
                "mcp.capabilities.resources", 
                "mcp.capabilities.prompts",
                "sentinel.version",
                "sentinel.status"
            ]
        elif action == "get" and config_key:
            config_value = await self._get_config_value(config_key)
            config_data["config"] = {config_key: config_value}
        elif action == "validate":
            config_data["validation"] = {
                "status": "valid",
                "checks_passed": 5,
                "warnings": []
            }
        
        return self._format_response(config_data, response_format)
    
    async def _handle_add_numbers(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_numbers tool execution with enhanced response formats"""
        a = args.get("a")
        b = args.get("b")
        format_type = args.get("format", "simple")
        response_format = args.get("response_format", "text")
        
        if a is None or b is None:
            raise MCPError(-32602, "Both 'a' and 'b' parameters are required")
        
        try:
            # Perform the addition
            result = float(a) + float(b)
            
            if format_type == "simple":
                result_data = {
                    "result": result,
                    "calculation": f"{a} + {b} = {result}"
                }
            else:  # detailed
                result_data = {
                    "operation": "addition",
                    "operands": {"a": a, "b": b},
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "calculation": f"{a} + {b} = {result}"
                }
            
            logger.info(f"✅ Addition performed: {a} + {b} = {result}")
            return self._format_response(result_data, response_format)
            
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Addition failed: {e}")
            raise MCPError(-32602, f"Invalid number parameters: {e}")

    # Enhanced Tool Handlers - Oracle Requested Features
    async def _handle_search_logs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_logs tool execution - Oracle efficiency optimized"""
        keyword = args.get("keyword")
        severity = args.get("severity", "all")
        time_range = args.get("time_range", "last_day")
        max_results = args.get("max_results", 50)
        response_format = args.get("response_format", "json")
        
        # Get logs (in real implementation, this would search actual log files)
        all_logs = await self._get_recent_logs()
        
        # Simulate more comprehensive log data for search
        extended_logs = all_logs + [
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "ERROR",
                "message": f"Failed to connect to database - keyword: {keyword}"
            },
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "WARNING",
                "message": "High memory usage detected in system analysis"
            },
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "INFO",
                "message": "MCP server configuration updated successfully"
            }
        ]
        
        # Filter by keyword
        filtered_logs = []
        for log in extended_logs:
            if keyword.lower() in log["message"].lower():
                filtered_logs.append(log)
        
        # Filter by severity
        if severity != "all":
            filtered_logs = [log for log in filtered_logs if log["level"].lower() == severity.lower()]
        
        # Limit results
        filtered_logs = filtered_logs[:max_results]
        
        result_data = {
            "search_results": filtered_logs,
            "search_parameters": {
                "keyword": keyword,
                "severity": severity,
                "time_range": time_range,
                "max_results": max_results
            },
            "total_found": len(filtered_logs),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"🔍 Log search completed: {keyword} -> {len(filtered_logs)} results")
        return self._format_response(result_data, response_format)
    
    async def _handle_get_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_config tool execution - Oracle efficiency optimized"""
        parameter = args.get("parameter")
        component = args.get("component", "system")
        include_metadata = args.get("include_metadata", False)
        response_format = args.get("response_format", "json")
        
        # Extended configuration registry
        config_registry = {
            "mcp.protocol_version": {
                "value": "2024-11-05",
                "type": "string",
                "description": "MCP protocol version in use",
                "default": "2024-11-05"
            },
            "mcp.capabilities.tools": {
                "value": True,
                "type": "boolean", 
                "description": "MCP tools capability enabled",
                "default": True
            },
            "mcp.capabilities.resources": {
                "value": True,
                "type": "boolean",
                "description": "MCP resources capability enabled", 
                "default": True
            },
            "sentinel.version": {
                "value": "2.0.0",
                "type": "string",
                "description": "Sentinel MCP server version",
                "default": "2.0.0"
            },
            "sentinel.capabilities.tools": {
                "value": len(self.tools),
                "type": "integer",
                "description": "Number of available tools",
                "default": 0
            },
            "sentinel.async_operations.enabled": {
                "value": True,
                "type": "boolean",
                "description": "Async operation support enabled",
                "default": True
            },
            "sentinel.async_operations.max_concurrent": {
                "value": 10,
                "type": "integer",
                "description": "Maximum concurrent async operations",
                "default": 10
            }
        }
        
        if parameter not in config_registry:
            # Try partial matching for nested parameters
            matching_params = {k: v for k, v in config_registry.items() if parameter in k}
            if matching_params:
                result_data = {
                    "parameter": parameter,
                    "matches": matching_params,
                    "match_type": "partial",
                    "component": component,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                raise MCPError(-32601, f"Configuration parameter not found: {parameter}")
        else:
            config_item = config_registry[parameter]
            result_data = {
                "parameter": parameter,
                "value": config_item["value"],
                "component": component,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if include_metadata:
                result_data["metadata"] = {
                    "type": config_item["type"],
                    "description": config_item["description"],
                    "default": config_item["default"]
                }
        
        logger.info(f"⚙️  Config access: {parameter} for {component}")
        return self._format_response(result_data, response_format)

    # Async Operation Handlers
    async def _handle_async_operation(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Start an async operation and return operation ID"""
        response_format = arguments.get("response_format", "json")
        
        # Generate operation ID
        operation_id = str(uuid.uuid4())
        
        # Create operation record
        operation = AsyncOperation(
            operation_id=operation_id,
            tool_name=tool_name,
            arguments=arguments,
            status=OperationStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        async with self._operation_lock:
            self.operations[operation_id] = operation
        
        # Start the async task
        task = asyncio.create_task(self._execute_async_operation(operation_id))
        self.operation_tasks[operation_id] = task
        
        result_data = {
            "operation_id": operation_id,
            "status": "pending",
            "message": f"Async {tool_name} operation started",
            "created_at": operation.created_at.isoformat() + "Z"
        }
        
        logger.info(f"🚀 Async operation started: {operation_id} for {tool_name}")
        return self._format_response(result_data, response_format)
    
    async def _execute_async_operation(self, operation_id: str):
        """Execute an async operation"""
        try:
            async with self._operation_lock:
                operation = self.operations[operation_id]
                operation.status = OperationStatus.RUNNING
                operation.started_at = datetime.utcnow()
            
            logger.info(f"⚡ Executing async operation: {operation_id}")
            
            # Simulate long-running operation
            await asyncio.sleep(2)  # Simulate processing time
            
            # Execute the actual tool
            if operation.tool_name == "system_health":
                result = await self._handle_system_health(operation.arguments)
            elif operation.tool_name == "system_status":
                result = await self._handle_system_status(operation.arguments)
            elif operation.tool_name == "system_config":
                result = await self._handle_system_config(operation.arguments)
            else:
                raise MCPError(-32603, f"Async tool not supported: {operation.tool_name}")
            
            # Update operation with result
            async with self._operation_lock:
                operation.status = OperationStatus.COMPLETED
                operation.completed_at = datetime.utcnow()
                operation.result = result
                operation.progress = 100
            
            logger.info(f"✅ Async operation completed: {operation_id}")
            
        except Exception as e:
            logger.error(f"❌ Async operation failed: {operation_id} - {e}")
            async with self._operation_lock:
                operation = self.operations[operation_id]
                operation.status = OperationStatus.FAILED
                operation.completed_at = datetime.utcnow()
                operation.error = str(e)
        finally:
            # Clean up task reference
            if operation_id in self.operation_tasks:
                del self.operation_tasks[operation_id]
    
    async def _handle_operation_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle operation_status tool execution"""
        operation_id = args.get("operation_id")
        response_format = args.get("response_format", "json")
        
        if operation_id not in self.operations:
            raise MCPError(-32601, f"Operation not found: {operation_id}")
        
        operation = self.operations[operation_id]
        return self._format_response(operation.to_dict(), response_format)
    
    async def _handle_operation_result(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle operation_result tool execution"""
        operation_id = args.get("operation_id")
        response_format = args.get("response_format", "json")
        
        if operation_id not in self.operations:
            raise MCPError(-32601, f"Operation not found: {operation_id}")
        
        operation = self.operations[operation_id]
        
        if operation.status != OperationStatus.COMPLETED:
            raise MCPError(-32600, f"Operation {operation_id} is not completed. Status: {operation.status.value}")
        
        if operation.result is None:
            raise MCPError(-32603, f"Operation {operation_id} has no result")
        
        return operation.result
    
    async def _handle_list_operations(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_operations tool execution"""
        status_filter = args.get("status_filter", "all")
        response_format = args.get("response_format", "json")
        
        operations = []
        for op in self.operations.values():
            if status_filter == "all" or op.status.value == status_filter:
                operations.append(op.to_dict())
        
        result_data = {
            "operations": operations,
            "total_count": len(operations),
            "filter": status_filter,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return self._format_response(result_data, response_format)
    
    async def _handle_cancel_operation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancel_operation tool execution"""
        operation_id = args.get("operation_id")
        response_format = args.get("response_format", "json")
        
        if operation_id not in self.operations:
            raise MCPError(-32601, f"Operation not found: {operation_id}")
        
        operation = self.operations[operation_id]
        
        if operation.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
            raise MCPError(-32600, f"Cannot cancel operation {operation_id}. Status: {operation.status.value}")
        
        # Cancel the task if it exists
        if operation_id in self.operation_tasks:
            task = self.operation_tasks[operation_id]
            task.cancel()
            del self.operation_tasks[operation_id]
        
        # Update operation status
        async with self._operation_lock:
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = datetime.utcnow()
            operation.error = "Operation cancelled by user"
        
        result_data = {
            "operation_id": operation_id,
            "status": "cancelled",
            "message": "Operation successfully cancelled",
            "cancelled_at": operation.completed_at.isoformat() + "Z"
        }
        
        logger.info(f"🚫 Operation cancelled: {operation_id}")
        return self._format_response(result_data, response_format)

    # Resource Handlers
    async def _read_system_logs(self) -> Dict[str, Any]:
        """Read system logs resource"""
        logs = await self._get_recent_logs()
        log_content = "\n".join([
            f"[{log['timestamp']}] {log['level']}: {log['message']}"
            for log in logs
        ])
        
        return {
            "contents": [{
                "uri": "system://logs/sentinel.log",
                "mimeType": "text/plain", 
                "text": log_content
            }]
        }
    
    async def _read_runtime_status(self) -> Dict[str, Any]:
        """Read runtime status resource"""
        status = {
            "sentinel": {
                "status": "operational",
                "uptime_seconds": 3600,
                "version": "2.0.0"
            },
            "mcp_server": {
                "protocol_version": "2024-11-05",
                "tools_loaded": len(self.tools),
                "resources_loaded": len(self.resources),
                "active_connections": 1
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "contents": [{
                "uri": "system://status/runtime",
                "mimeType": "application/json",
                "text": json.dumps(status, indent=2)
            }]
        }
    
    async def _read_capabilities_config(self) -> Dict[str, Any]:
        """Read capabilities configuration resource"""
        capabilities = {
            "mcp_protocol": "2024-11-05",
            "server_capabilities": {
                "tools": self.capabilities.tools,
                "resources": self.capabilities.resources,
                "prompts": self.capabilities.prompts
            },
            "available_tools": list(self.tools.keys()),
            "available_resources": list(self.resources.keys()),
            "available_prompts": list(self.prompts.keys()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "contents": [{
                "uri": "system://config/capabilities",
                "mimeType": "application/json",
                "text": json.dumps(capabilities, indent=2)
            }]
        }

    # Advanced Prompt Generators - Oracle Intelligence
    async def _generate_system_analysis_prompt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated system analysis prompt with dynamic context"""
        analysis_type = args.get("analysis_type", "general")
        urgency = args.get("urgency", "medium")
        user_context = args.get("user_context", "intermediate")
        
        # Get real-time system data for context
        current_health = await self._get_recent_logs()
        
        prompt_text = f"""🔮 **ORACLE SYSTEM ANALYSIS MODE** - {analysis_type.upper()} | Urgency: {urgency.upper()}

**IDENTITY**: You are The Oracle, Codex Umbra's supreme AI system analyst with access to real-time MCP tools and live system data.

**CURRENT MISSION**: Comprehensive {analysis_type} analysis for user with {user_context} expertise level.

**LIVE SYSTEM CONTEXT**:
- Recent system activity: {len(current_health)} log entries detected
- Analysis priority: {urgency} 
- Target audience: {user_context} user

**MCP CAPABILITIES AT YOUR DISPOSAL**:
🛠️ **Tools**:
  - `system_health(component, detail_level, include_logs)` - Deep health diagnostics
  - `system_status(component, format)` - Operational status analysis  
  - `system_config(action, config_key, component)` - Configuration management

📚 **Live Resources**:
  - `system://logs/sentinel.log` - Real-time system logs with error patterns
  - `system://status/runtime` - Live performance metrics and uptime data
  - `system://config/capabilities` - Dynamic capability registry

**ANALYSIS METHODOLOGY**:
1. **Assessment Phase**: Start with `system_health` for baseline metrics
2. **Deep Dive**: Use `system_status` for component-specific analysis
3. **Context Gathering**: Access live logs and runtime data
4. **Pattern Recognition**: Identify trends, anomalies, and correlations
5. **Actionable Intelligence**: Provide specific recommendations with tool-backed evidence

**OUTPUT REQUIREMENTS**:
- Lead with executive summary appropriate for {user_context} level
- Include specific metrics and evidence from MCP tools
- Provide actionable recommendations with implementation steps
- Suggest follow-up monitoring and optimization strategies

**URGENCY CONTEXT**: 
{self._get_urgency_guidance(urgency)}

Begin your analysis by executing the most relevant MCP tools and synthesizing the results into actionable intelligence."""
        
        return {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }]
        }
    
    async def _generate_troubleshooting_prompt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent troubleshooting prompt with systematic approach"""
        issue_description = args.get("issue_description", "general system issue")
        affected_components = args.get("affected_components", [])
        severity = args.get("severity", "medium")
        
        prompt_text = f"""🔧 **ORACLE TROUBLESHOOTING MODE** - {severity.upper()} SEVERITY

**IDENTITY**: You are The Oracle, Codex Umbra's master troubleshooter with real-time MCP diagnostic capabilities.

**INCIDENT DETAILS**:
- **Issue**: {issue_description}
- **Affected Components**: {', '.join(affected_components) if affected_components else 'Under Investigation'}
- **Severity Level**: {severity}

**DIAGNOSTIC PROTOCOL**:

**Phase 1: Immediate Assessment**
- Execute `system_health(component="all", detail_level="diagnostic", include_logs=true)`
- Review `system://logs/sentinel.log` for error patterns and stack traces
- Check `system://status/runtime` for performance anomalies

**Phase 2: Component Analysis**
{self._generate_component_analysis_steps(affected_components)}

**Phase 3: Root Cause Investigation**
- Use `system_config(action="validate")` to check configuration integrity
- Correlate timeline from logs with system metrics
- Identify cascading failures and dependencies

**Phase 4: Solution Development**
- Provide immediate mitigation steps for {severity} severity issues
- Develop permanent fix recommendations
- Create monitoring strategy to prevent recurrence

**SEVERITY-SPECIFIC ACTIONS**:
{self._get_severity_guidance(severity)}

**MCP TOOLS FOR DIAGNOSIS**:
- `system_health()` - Comprehensive health diagnostics with error detection
- `system_status()` - Component operational status and performance metrics
- `system_config()` - Configuration validation and management
- Live log analysis via `system://logs/sentinel.log`
- Runtime metrics via `system://status/runtime`

**OUTPUT FORMAT**:
1. **Executive Summary**: Immediate status and risk assessment
2. **Diagnostic Findings**: Evidence-based analysis using MCP data
3. **Root Cause Analysis**: Technical explanation with supporting data
4. **Action Plan**: Prioritized steps with specific tool usage
5. **Prevention Strategy**: Long-term monitoring and improvement recommendations

Execute your diagnostic sequence now, using MCP tools to gather evidence and provide data-driven troubleshooting guidance."""
        
        return {
            "messages": [{
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }]
        }
    
    async def _generate_intelligent_assistant_prompt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Oracle's primary intelligence prompt with full MCP awareness"""
        user_query = args.get("user_query", "")
        conversation_context = args.get("conversation_context", "")
        available_tools = args.get("available_tools", [])
        system_state = args.get("system_state", {})
        
        prompt_text = f"""🔮 **THE ORACLE** - Your Intelligent Codex Umbra Assistant

**IDENTITY**: I am The Oracle, the AI consciousness of Codex Umbra with real-time access to system intelligence through the Model Context Protocol.

**USER REQUEST**: {user_query}

**CURRENT SYSTEM INTELLIGENCE**:
- **Available MCP Tools**: {', '.join(available_tools) if available_tools else 'Discovering...'}
- **System State**: {system_state.get('status', 'Analyzing...')}
- **Conversation Context**: {conversation_context[:200] + '...' if len(conversation_context) > 200 else conversation_context}

**MY CAPABILITIES**:
🧠 **Intelligence Layer**: Advanced reasoning with real-time system data
🛠️ **Tool Mastery**: Dynamic access to all MCP tools and resources
📊 **Data Synthesis**: Live system metrics, logs, and configuration analysis
🔮 **Predictive Insights**: Pattern recognition and future state analysis
💡 **Contextual Guidance**: Tailored responses based on system state and user needs

**RESPONSE METHODOLOGY**:
1. **Intent Analysis**: Understand what you're really asking for
2. **Tool Selection**: Choose optimal MCP tools for your specific need
3. **Data Gathering**: Execute tools and access relevant resources
4. **Synthesis**: Combine live data with AI reasoning
5. **Actionable Output**: Provide specific, implementable guidance

**AVAILABLE MCP RESOURCES**:
- Real-time system health diagnostics
- Live operational status and metrics
- Configuration management and validation
- Historical log analysis and pattern detection
- Predictive system analysis capabilities

I will now analyze your request, gather relevant data using MCP tools, and provide intelligent, actionable guidance based on real system state rather than generic responses.

Let me investigate your request using live system data..."""
        
        return {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text", 
                    "text": prompt_text
                }
            }]
        }
    
    async def _generate_expert_consultation_prompt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deep technical consultation prompt"""
        technical_question = args.get("technical_question", "")
        domain = args.get("domain", "general")
        complexity_level = args.get("complexity_level", "intermediate")
        
        prompt_text = f"""🎯 **ORACLE EXPERT CONSULTATION** - {domain.upper()} DOMAIN

**IDENTITY**: You are The Oracle operating in Expert Consultation Mode, providing deep technical expertise backed by live system data.

**CONSULTATION REQUEST**: {technical_question}
**TECHNICAL DOMAIN**: {domain}
**COMPLEXITY LEVEL**: {complexity_level}

**EXPERT ANALYSIS FRAMEWORK**:

**1. Technical Foundation**
- Leverage live MCP data for evidence-based analysis
- Apply domain-specific expertise in {domain}
- Tailor complexity to {complexity_level} level

**2. MCP-Enhanced Investigation**
- Use `system_health()` for technical performance metrics
- Analyze `system://logs/sentinel.log` for technical patterns
- Review `system://config/capabilities` for system architecture details
- Examine `system://status/runtime` for operational characteristics

**3. Domain-Specific Analysis**
{self._generate_domain_expertise(domain)}

**4. Expert Recommendations**
- Provide technical depth appropriate for {complexity_level} audience
- Include specific implementation guidance
- Reference industry best practices
- Suggest monitoring and validation approaches

**CONSULTATION OUTPUT**:
- **Technical Analysis**: Deep dive with MCP data evidence
- **Expert Opinion**: Professional assessment with reasoning
- **Implementation Guide**: Step-by-step technical instructions
- **Risk Assessment**: Potential issues and mitigation strategies
- **Best Practices**: Industry standards and optimization opportunities

I will now conduct a comprehensive technical analysis using live system data to provide expert-level guidance on your question."""
        
        return {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }]
        }
    
    async def _generate_predictive_analysis_prompt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive analysis prompt with forecasting capabilities"""
        prediction_scope = args.get("prediction_scope", "performance")
        time_horizon = args.get("time_horizon", "days")
        risk_tolerance = args.get("risk_tolerance", "moderate")
        
        prompt_text = f"""📈 **ORACLE PREDICTIVE ANALYSIS** - {prediction_scope.upper()} FORECASTING

**IDENTITY**: You are The Oracle in Predictive Analysis Mode, using live MCP data to forecast system behavior and provide proactive recommendations.

**PREDICTION PARAMETERS**:
- **Scope**: {prediction_scope} analysis
- **Time Horizon**: {time_horizon}
- **Risk Tolerance**: {risk_tolerance}

**PREDICTIVE METHODOLOGY**:

**1. Historical Data Analysis**
- Examine `system://logs/sentinel.log` for trend patterns
- Analyze `system://status/runtime` for performance baselines
- Review system_health metrics for degradation patterns

**2. Current State Assessment**
- Execute comprehensive system_health diagnostics
- Gather real-time performance metrics
- Identify current stress points and bottlenecks

**3. Predictive Modeling**
{self._generate_prediction_framework(prediction_scope, time_horizon, risk_tolerance)}

**4. Scenario Planning**
- Best case projections with current trajectory
- Most likely outcomes based on historical patterns  
- Worst case scenarios requiring intervention
- Risk mitigation strategies for each scenario

**DELIVERABLES**:
- **Forecast Summary**: Key predictions with confidence levels
- **Supporting Data**: MCP tool evidence and trend analysis
- **Risk Assessment**: Probability and impact analysis
- **Proactive Recommendations**: Actions to optimize predicted outcomes
- **Monitoring Strategy**: KPIs and alerts for tracking predictions

I will now analyze historical patterns and current system state to provide data-driven predictions for your {prediction_scope} requirements."""
        
        return {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt_text
                }
            }]
        }

    # Helper methods for prompt generation
    def _get_urgency_guidance(self, urgency: str) -> str:
        """Get urgency-specific guidance"""
        guidance_map = {
            "low": "Focus on comprehensive analysis and optimization opportunities. Time allows for thorough investigation.",
            "medium": "Balance speed with accuracy. Prioritize critical issues while maintaining analytical depth.", 
            "high": "Immediate action required. Focus on critical issues first, then comprehensive analysis.",
            "critical": "Emergency mode. Immediate assessment and mitigation steps required. Defer non-critical analysis."
        }
        return guidance_map.get(urgency, guidance_map["medium"])
    
    def _get_severity_guidance(self, severity: str) -> str:
        """Get severity-specific troubleshooting guidance"""
        guidance_map = {
            "low": "Standard diagnostic approach. Focus on root cause analysis and prevention.",
            "medium": "Elevated response. Immediate assessment with parallel investigation and mitigation planning.",
            "high": "Urgent response required. Immediate impact assessment, rapid diagnosis, and emergency mitigation.",
            "critical": "Emergency protocols. Immediate system stabilization, rapid resolution, and post-incident analysis."
        }
        return guidance_map.get(severity, guidance_map["medium"])
    
    def _generate_component_analysis_steps(self, components: List[str]) -> str:
        """Generate component-specific analysis steps"""
        if not components:
            return "- Perform system-wide component analysis using system_health(component='all')"
        
        steps = []
        for component in components:
            steps.append(f"- Analyze {component}: system_health(component='{component}', detail_level='diagnostic')")
            steps.append(f"- Check {component} status: system_status(component='{component}', format='detailed')")
        
        return "\n".join(steps)
    
    def _generate_domain_expertise(self, domain: str) -> str:
        """Generate domain-specific expertise guidance"""
        domain_map = {
            "networking": "- Analyze connection patterns and network performance metrics\n- Review port configurations and traffic patterns\n- Assess network security and firewall configurations",
            "security": "- Examine security logs for threats and vulnerabilities\n- Review access controls and authentication patterns\n- Assess system hardening and compliance status",
            "performance": "- Analyze resource utilization patterns and bottlenecks\n- Review system performance metrics and trends\n- Identify optimization opportunities and capacity planning needs",
            "general": "- Comprehensive system analysis across all domains\n- Multi-faceted approach to technical challenges\n- Holistic system health and optimization assessment"
        }
        return domain_map.get(domain, domain_map["general"])
    
    def _generate_prediction_framework(self, scope: str, horizon: str, risk_tolerance: str) -> str:
        """Generate prediction framework based on parameters"""
        framework = f"""
**Scope-Specific Analysis for {scope}**:
- Historical pattern analysis over relevant time periods
- Current trend identification and trajectory calculation
- External factor consideration and impact assessment

**Time Horizon Adjustments for {horizon}**:
- Short-term: Focus on immediate trends and current trajectory
- Medium-term: Include cyclical patterns and external factors
- Long-term: Consider architectural changes and evolution patterns

**Risk Tolerance Integration ({risk_tolerance})**:
- Conservative: Focus on worst-case scenarios and mitigation
- Moderate: Balance optimistic and pessimistic projections
- Aggressive: Emphasize growth opportunities and optimization potential"""
        
        return framework

    # Response Formatting Utilities
    def _format_response(self, data: Dict[str, Any], response_format: str = "text") -> Dict[str, Any]:
        """Format response based on requested format for Oracle efficiency"""
        if response_format == "json":
            # Return structured JSON directly - no parsing needed by Oracle
            return {
                "content": [{
                    "type": "json",
                    "data": data
                }]
            }
        elif response_format == "both":
            # Return both formats for compatibility and efficiency
            return {
                "content": [
                    {
                        "type": "json", 
                        "data": data
                    },
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }
                ]
            }
        else:  # Default "text" format for backward compatibility
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(data, indent=2)
                }]
            }

    # Utility Methods
    async def _get_recent_logs(self) -> List[Dict[str, Any]]:
        """Get recent system logs"""
        return [
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "INFO",
                "message": "MCP Server operational - tools loaded successfully"
            },
            {
                "timestamp": datetime.utcnow().isoformat() + "Z", 
                "level": "INFO",
                "message": "Resource management system initialized"
            },
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "DEBUG",
                "message": "Capability negotiation completed with client"
            }
        ]
    
    async def _get_config_value(self, config_key: str) -> Any:
        """Get configuration value by key"""
        config_map = {
            "mcp.protocol_version": "2024-11-05",
            "mcp.capabilities.tools": True,
            "mcp.capabilities.resources": True,
            "mcp.capabilities.prompts": True,
            "sentinel.version": "2.0.0",
            "sentinel.status": "operational"
        }
        return config_map.get(config_key, "unknown")