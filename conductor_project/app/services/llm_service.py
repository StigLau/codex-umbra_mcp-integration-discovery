import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = "mistral"
        self.timeout = 30.0

    async def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False

    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response using Mistral via Ollama."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                messages = []
                
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
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
                        "done": result.get("done", True)
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

    async def interpret_user_request(self, user_input: str) -> Dict[str, Any]:
        """Interpret user request in context of Sentinel interaction."""
        system_prompt = """You are The Oracle, an AI assistant for Codex Umbra. Your role is to understand and interact with The Sentinel, our internal Master Control Program (MCP) server.

Interpret user requests and respond with structured commands or clarification questions. Available Sentinel commands:
- get_status: Get operational status
- health_check: Check system health

If the user wants to check status or health, respond with the exact command. Otherwise, ask for clarification or explain what you can do.

Be concise and efficient. Respond in plain text."""

        return await self.generate_response(user_input, system_prompt)