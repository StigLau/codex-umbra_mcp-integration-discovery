from pydantic import BaseModel

class ChatMessage(BaseModel):
    text: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    timestamp: str