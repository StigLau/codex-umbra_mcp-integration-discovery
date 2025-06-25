from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatMessage(BaseModel):
    message: Optional[str] = None
    text: Optional[str] = None
    user_id: str = "default"
    provider: Optional[str] = None  # Specify preferred LLM provider
    conversation_id: Optional[str] = None  # For continuing function calling conversations
    enable_function_calling: Optional[bool] = False  # Enable function calling mode
    
    @property
    def content(self) -> str:
        """Get message content from either 'message' or 'text' field"""
        return self.message or self.text or ""

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    provider_used: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None
    mcp_enhanced: Optional[bool] = False
    error: Optional[bool] = False
    fallback_from: Optional[str] = None
    # Function calling specific fields
    function_calling_enabled: Optional[bool] = False
    conversation_id: Optional[str] = None
    tool_calls_made: Optional[List[Dict[str, Any]]] = None
    turn: Optional[int] = None

class FunctionCallRequest(BaseModel):
    """Request for function calling conversation"""
    message: str
    provider: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: str = "default"

class FunctionCallResponse(BaseModel):
    """Response from function calling conversation"""
    response: str
    conversation_id: str
    tool_calls_made: List[Dict[str, Any]]
    provider_used: str
    turn: Optional[int] = None
    timestamp: str
    function_calling_enabled: bool = True