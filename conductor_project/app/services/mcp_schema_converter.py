"""
MCP Schema Converter - Convert MCP tool definitions to LLM function calling schemas
Supports OpenAI Functions, Anthropic Tools, and custom formats
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPSchemaConverter:
    """Converts MCP tool definitions to LLM function calling schemas"""
    
    def __init__(self):
        self.schema_cache = {}
        self.last_update = None
    
    def convert_mcp_tool_to_anthropic_schema(self, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP tool to Anthropic tool use schema"""
        try:
            tool_name = mcp_tool.get("name", "unknown_tool")
            description = mcp_tool.get("description", f"Execute {tool_name}")
            input_schema = mcp_tool.get("inputSchema", {})
            
            # Convert MCP input schema to Anthropic format
            anthropic_schema = {
                "name": tool_name,
                "description": description,
                "input_schema": self._convert_json_schema_to_anthropic(input_schema)
            }
            
            logger.debug(f"Converted MCP tool '{tool_name}' to Anthropic schema")
            return anthropic_schema
            
        except Exception as e:
            logger.error(f"Failed to convert MCP tool to Anthropic schema: {e}")
            return None
    
    def convert_mcp_tool_to_openai_schema(self, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP tool to OpenAI function calling schema"""
        try:
            tool_name = mcp_tool.get("name", "unknown_tool")
            description = mcp_tool.get("description", f"Execute {tool_name}")
            input_schema = mcp_tool.get("inputSchema", {})
            
            # Convert to OpenAI function format
            openai_schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": input_schema if input_schema else {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            logger.debug(f"Converted MCP tool '{tool_name}' to OpenAI schema")
            return openai_schema
            
        except Exception as e:
            logger.error(f"Failed to convert MCP tool to OpenAI schema: {e}")
            return None
    
    def _convert_json_schema_to_anthropic(self, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON schema to Anthropic input schema format"""
        if not json_schema:
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        # Anthropic uses standard JSON Schema, so minimal conversion needed
        anthropic_schema = {
            "type": json_schema.get("type", "object"),
            "properties": json_schema.get("properties", {}),
        }
        
        if "required" in json_schema:
            anthropic_schema["required"] = json_schema["required"]
        
        return anthropic_schema
    
    def convert_all_mcp_tools_to_anthropic(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert all MCP tools to Anthropic tool use format"""
        anthropic_tools = []
        
        for mcp_tool in mcp_tools:
            converted = self.convert_mcp_tool_to_anthropic_schema(mcp_tool)
            if converted:
                anthropic_tools.append(converted)
        
        logger.info(f"Converted {len(anthropic_tools)} MCP tools to Anthropic format")
        return anthropic_tools
    
    def convert_all_mcp_tools_to_openai(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert all MCP tools to OpenAI function calling format"""
        openai_tools = []
        
        for mcp_tool in mcp_tools:
            converted = self.convert_mcp_tool_to_openai_schema(mcp_tool)
            if converted:
                openai_tools.append(converted)
        
        logger.info(f"Converted {len(openai_tools)} MCP tools to OpenAI format")
        return openai_tools
    
    def generate_tool_documentation(self, mcp_tools: List[Dict[str, Any]]) -> str:
        """Generate human-readable documentation for available tools"""
        if not mcp_tools:
            return "No tools available."
        
        docs = ["Available MCP Tools:", "=" * 20]
        
        for tool in mcp_tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            input_schema = tool.get("inputSchema", {})
            
            docs.append(f"\n**{name}**")
            docs.append(f"Description: {description}")
            
            properties = input_schema.get("properties", {})
            if properties:
                docs.append("Parameters:")
                for param_name, param_info in properties.items():
                    param_type = param_info.get("type", "unknown")
                    param_desc = param_info.get("description", "No description")
                    required = param_name in input_schema.get("required", [])
                    req_str = " (required)" if required else " (optional)"
                    docs.append(f"  - {param_name} ({param_type}){req_str}: {param_desc}")
            else:
                docs.append("Parameters: None")
        
        return "\n".join(docs)
    
    def validate_function_call_arguments(self, tool_name: str, arguments: Dict[str, Any], mcp_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate function call arguments against MCP tool schema"""
        result = {
            "valid": False,
            "errors": [],
            "cleaned_arguments": {}
        }
        
        # Find the tool schema
        tool_schema = None
        for tool in mcp_tools:
            if tool.get("name") == tool_name:
                tool_schema = tool
                break
        
        if not tool_schema:
            result["errors"].append(f"Tool '{tool_name}' not found")
            return result
        
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Check required parameters
        for req_param in required:
            if req_param not in arguments:
                result["errors"].append(f"Required parameter '{req_param}' missing")
        
        # Validate and clean arguments
        cleaned_args = {}
        for arg_name, arg_value in arguments.items():
            if arg_name in properties:
                param_schema = properties[arg_name]
                # Basic type validation and conversion
                try:
                    cleaned_value = self._validate_and_convert_parameter(arg_value, param_schema)
                    cleaned_args[arg_name] = cleaned_value
                except ValueError as e:
                    result["errors"].append(f"Parameter '{arg_name}': {str(e)}")
            else:
                # Unknown parameter - include with warning
                cleaned_args[arg_name] = arg_value
                logger.warning(f"Unknown parameter '{arg_name}' for tool '{tool_name}'")
        
        result["cleaned_arguments"] = cleaned_args
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    def _validate_and_convert_parameter(self, value: Any, schema: Dict[str, Any]) -> Any:
        """Validate and convert parameter value according to schema"""
        expected_type = schema.get("type", "string")
        
        if expected_type == "string":
            return str(value)
        elif expected_type == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert to integer: {value}")
        elif expected_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert to number: {value}")
        elif expected_type == "boolean":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            else:
                return bool(value)
        elif expected_type == "array":
            if not isinstance(value, list):
                raise ValueError(f"Expected array, got {type(value)}")
            return value
        elif expected_type == "object":
            if not isinstance(value, dict):
                raise ValueError(f"Expected object, got {type(value)}")
            return value
        else:
            # Unknown type, return as-is
            return value
    
    def get_tool_by_name(self, tool_name: str, mcp_tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get MCP tool definition by name"""
        for tool in mcp_tools:
            if tool.get("name") == tool_name:
                return tool
        return None
    
    def clear_cache(self):
        """Clear schema conversion cache"""
        self.schema_cache.clear()
        self.last_update = None
        logger.debug("Schema conversion cache cleared")

# Global instance
mcp_schema_converter = MCPSchemaConverter()