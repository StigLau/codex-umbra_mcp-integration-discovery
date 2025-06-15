"""
JSON-RPC 2.0 Server Implementation for MCP Protocol
Handles WebSocket and HTTP transport layers for MCP communication
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union, Callable
import traceback

import websockets
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from websockets.exceptions import ConnectionClosed

from .mcp_protocol import MCPServer, MCPError

logger = logging.getLogger(__name__)

class JSONRPCError(Exception):
    """JSON-RPC 2.0 Error"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")

class MCPJSONRPCServer:
    """
    JSON-RPC 2.0 Server for MCP Protocol
    Supports both WebSocket and HTTP transport
    """
    
    def __init__(self):
        self.mcp_server = MCPServer()
        self.clients: Dict[str, Any] = {}  # client_id -> connection info
        self.method_handlers = self._setup_method_handlers()
    
    def _setup_method_handlers(self) -> Dict[str, Callable]:
        """Setup JSON-RPC method to handler mapping"""
        return {
            # Core MCP Protocol Methods
            "initialize": self.mcp_server.handle_initialize,
            
            # Tool Methods
            "tools/list": self.mcp_server.handle_tools_list,
            "tools/call": self.mcp_server.handle_tools_call,
            
            # Resource Methods  
            "resources/list": self.mcp_server.handle_resources_list,
            "resources/read": self.mcp_server.handle_resources_read,
            
            # Prompt Methods
            "prompts/list": self.mcp_server.handle_prompts_list,
            "prompts/get": self.mcp_server.handle_prompts_get,
            
            # Legacy compatibility (for gradual migration)
            "ping": self._handle_ping,
            "legacy/status": self._handle_legacy_status,
            "legacy/health": self._handle_legacy_health
        }
    
    async def _handle_ping(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle ping for connection testing"""
        return {"pong": True, "timestamp": "2025-06-15T12:00:00Z"}
    
    async def _handle_legacy_status(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Legacy status endpoint for backward compatibility"""
        return {
            "status": "MCP Operational",
            "version": "2.0.0", 
            "protocol": "mcp",
            "legacy_mode": True
        }
    
    async def _handle_legacy_health(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Legacy health endpoint for backward compatibility"""
        return {
            "status": "healthy",
            "version": "2.0.0",
            "protocol": "mcp",
            "legacy_mode": True,
            "dependencies": {"mcp_server": "operational"}
        }
    
    async def handle_jsonrpc_request(self, request_data: Union[str, bytes, Dict]) -> Dict[str, Any]:
        """
        Handle JSON-RPC 2.0 request
        Supports single requests and batch requests
        """
        try:
            # Parse request if needed
            if isinstance(request_data, (str, bytes)):
                try:
                    request = json.loads(request_data)
                except json.JSONDecodeError as e:
                    return self._create_error_response(
                        None, JSONRPCError.PARSE_ERROR, "Parse error", str(e)
                    )
            else:
                request = request_data
            
            # Handle batch requests
            if isinstance(request, list):
                if not request:  # Empty array
                    return self._create_error_response(
                        None, JSONRPCError.INVALID_REQUEST, "Invalid Request", "Empty batch"
                    )
                
                # Process batch
                responses = []
                for single_request in request:
                    response = await self._handle_single_request(single_request)
                    if response:  # Only add non-notification responses
                        responses.append(response)
                
                return responses if responses else None
            else:
                # Handle single request
                return await self._handle_single_request(request)
                
        except Exception as e:
            logger.error(f"❌ Unexpected error handling JSON-RPC request: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_response(
                None, JSONRPCError.INTERNAL_ERROR, "Internal error", str(e)
            )
    
    async def _handle_single_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a single JSON-RPC 2.0 request"""
        request_id = request.get("id")
        
        try:
            # Validate JSON-RPC 2.0 format
            if request.get("jsonrpc") != "2.0":
                return self._create_error_response(
                    request_id, JSONRPCError.INVALID_REQUEST, "Invalid Request", "Missing or invalid jsonrpc version"
                )
            
            method = request.get("method")
            if not method or not isinstance(method, str):
                return self._create_error_response(
                    request_id, JSONRPCError.INVALID_REQUEST, "Invalid Request", "Missing or invalid method"
                )
            
            params = request.get("params", {})
            
            logger.info(f"🔧 JSON-RPC Method: {method}, Params: {params}, ID: {request_id}")
            
            # Check if method exists
            if method not in self.method_handlers:
                return self._create_error_response(
                    request_id, JSONRPCError.METHOD_NOT_FOUND, "Method not found", f"Method '{method}' not found"
                )
            
            # Execute method handler
            try:
                handler = self.method_handlers[method]
                if params:
                    result = await handler(params)
                else:
                    result = await handler()
                
                # For notifications (no ID), don't send response
                if request_id is None:
                    return None
                
                return self._create_success_response(request_id, result)
                
            except MCPError as e:
                return self._create_error_response(request_id, e.code, e.message, e.data)
            except Exception as e:
                logger.error(f"❌ Method handler error for {method}: {e}")
                logger.error(traceback.format_exc())
                return self._create_error_response(
                    request_id, JSONRPCError.INTERNAL_ERROR, "Internal error", str(e)
                )
                
        except Exception as e:
            logger.error(f"❌ Request processing error: {e}")
            return self._create_error_response(
                request_id, JSONRPCError.INTERNAL_ERROR, "Internal error", str(e)
            )
    
    def _create_success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 success response"""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
    
    def _create_error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 error response"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id
        }
    
    async def handle_websocket_client(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket client connection for MCP communication"""
        await websocket.accept()
        self.clients[client_id] = {"websocket": websocket, "type": "websocket"}
        
        logger.info(f"🔗 WebSocket client connected: {client_id}")
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive_text()
                logger.debug(f"📨 Received from {client_id}: {message[:100]}...")
                
                # Process JSON-RPC request
                response = await self.handle_jsonrpc_request(message)
                
                # Send response if not a notification
                if response is not None:
                    response_text = json.dumps(response)
                    await websocket.send_text(response_text)
                    logger.debug(f"📤 Sent to {client_id}: {response_text[:100]}...")
                    
        except ConnectionClosed:
            logger.info(f"🔌 WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def send_notification(self, client_id: str, method: str, params: Dict[str, Any] = None):
        """Send notification to specific client"""
        if client_id not in self.clients:
            logger.warning(f"⚠️  Client {client_id} not found for notification")
            return
        
        client = self.clients[client_id]
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        try:
            if client["type"] == "websocket":
                await client["websocket"].send_text(json.dumps(notification))
                logger.info(f"🔔 Sent notification to {client_id}: {method}")
        except Exception as e:
            logger.error(f"❌ Failed to send notification to {client_id}: {e}")
    
    async def broadcast_notification(self, method: str, params: Dict[str, Any] = None):
        """Broadcast notification to all connected clients"""
        for client_id in list(self.clients.keys()):
            await self.send_notification(client_id, method, params)

# FastAPI Integration
def create_mcp_fastapi_app() -> FastAPI:
    """Create FastAPI app with MCP JSON-RPC server integration"""
    
    app = FastAPI(
        title="The Sentinel MCP Server",
        description="Model Context Protocol Server with JSON-RPC 2.0 transport",
        version="2.0.0"
    )
    
    jsonrpc_server = MCPJSONRPCServer()
    
    @app.websocket("/mcp")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for MCP communication"""
        client_id = f"ws-{id(websocket)}"
        await jsonrpc_server.handle_websocket_client(websocket, client_id)
    
    @app.post("/mcp/rpc")
    async def http_rpc_endpoint(request: Dict[str, Any]):
        """HTTP endpoint for JSON-RPC 2.0 requests"""
        try:
            response = await jsonrpc_server.handle_jsonrpc_request(request)
            return JSONResponse(content=response)
        except Exception as e:
            logger.error(f"❌ HTTP RPC error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Legacy compatibility endpoints
    @app.get("/")
    async def root():
        """Root endpoint with MCP server info"""
        return {
            "message": "The Sentinel MCP Server is operational",
            "component": "sentinel",
            "protocol": "mcp-2.0",
            "transport": ["websocket", "http"],
            "endpoints": {
                "websocket": "/mcp",
                "http_rpc": "/mcp/rpc",
                "legacy_status": "/legacy/status",
                "legacy_health": "/legacy/health"
            }
        }
    
    @app.get("/legacy/status")
    async def legacy_status():
        """Legacy status endpoint for backward compatibility"""
        result = await jsonrpc_server._handle_legacy_status()
        return result
    
    @app.get("/legacy/health") 
    async def legacy_health():
        """Legacy health endpoint for backward compatibility"""
        result = await jsonrpc_server._handle_legacy_health()
        return result
    
    return app

# Standalone WebSocket Server
async def run_websocket_server(host: str = "localhost", port: int = 8001):
    """Run standalone WebSocket MCP server"""
    jsonrpc_server = MCPJSONRPCServer()
    
    async def websocket_handler(websocket, path):
        client_id = f"ws-{id(websocket)}"
        await jsonrpc_server.handle_websocket_client(websocket, client_id)
    
    logger.info(f"🚀 Starting MCP WebSocket server on {host}:{port}")
    
    async with websockets.serve(websocket_handler, host, port):
        logger.info(f"✅ MCP WebSocket server running on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run standalone WebSocket server
    asyncio.run(run_websocket_server())