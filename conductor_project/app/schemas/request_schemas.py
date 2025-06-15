from pydantic import BaseModel
from typing import Optional

class ChatMessage(BaseModel):
    message: Optional[str] = None
    text: Optional[str] = None
    user_id: str = "default"
    
    @property
    def content(self) -> str:
        """Get message content from either 'message' or 'text' field"""
        return self.message or self.text or ""

class ChatResponse(BaseModel):
    response: str
    timestamp: str