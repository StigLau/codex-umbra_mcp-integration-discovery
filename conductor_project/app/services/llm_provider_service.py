"""
Multi-LLM Provider Service for The Oracle
Supports Ollama (local), Anthropic Claude, and Google Gemini
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import httpx
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "top_p": kwargs.get("top_p", 0.9),
                            "max_tokens": kwargs.get("max_tokens", 2048)
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "type": "local"
        }

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider with function calling support"""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens
        self.temperature = settings.anthropic_temperature
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic Claude"""
        try:
            # Import anthropic only when needed
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            message = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text if message.content else ""
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Generate response with tool calling capability"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Add tools if provided
            message_kwargs = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "messages": messages
            }
            
            if tools:
                message_kwargs["tools"] = tools
            
            message = await client.messages.create(**message_kwargs)
            
            # Process response and tool calls
            result = {
                "content": "",
                "tool_calls": [],
                "finish_reason": "stop"
            }
            
            for content_block in message.content:
                if content_block.type == "text":
                    result["content"] += content_block.text
                elif content_block.type == "tool_use":
                    result["tool_calls"].append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "arguments": content_block.input
                    })
            
            if result["tool_calls"]:
                result["finish_reason"] = "tool_calls"
            
            return result
            
        except Exception as e:
            logger.error(f"Anthropic tool calling error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Anthropic API is available"""
        if not self.api_key:
            return False
        
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Test with a simple message
            await client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "type": "cloud"
        }

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider"""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.max_tokens = settings.gemini_max_tokens
        self.temperature = settings.gemini_temperature
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Google Gemini"""
        try:
            # Import google-generativeai only when needed
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(self.model)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
            )
            
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text if response.text else ""
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if Gemini API is available"""
        if not self.api_key:
            return False
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async("test")
            return True
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "type": "cloud"
        }

class MultiLLMService:
    """Service that manages multiple LLM providers"""
    
    def __init__(self):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.default_provider = LLMProvider(settings.default_llm_provider)
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers"""
        
        # Always initialize Ollama (local)
        try:
            self.providers[LLMProvider.OLLAMA] = OllamaProvider()
            logger.info("Ollama provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        # Initialize Anthropic if API key is available
        if settings.anthropic_api_key:
            try:
                self.providers[LLMProvider.ANTHROPIC] = AnthropicProvider()
                logger.info("Anthropic provider initialized (key configured)")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")
        else:
            logger.info("Anthropic provider skipped (no API key configured)")
        
        # Initialize Gemini if API key is available
        if settings.gemini_api_key:
            try:
                self.providers[LLMProvider.GEMINI] = GeminiProvider()
                logger.info("Gemini provider initialized (key configured)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")
        else:
            logger.info("Gemini provider skipped (no API key configured)")
        
        logger.info(f"Initialized {len(self.providers)} LLM providers")
    
    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available and healthy providers"""
        available = []
        
        for provider_enum, provider in self.providers.items():
            try:
                is_available = await provider.is_available()
                model_info = provider.get_model_info()
                model_info["available"] = is_available
                available.append(model_info)
            except Exception as e:
                logger.error(f"Error checking provider {provider_enum.value}: {e}")
        
        return available
    
    async def generate_response(
        self, 
        prompt: str, 
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using specified or default provider"""
        
        # Use specified provider or fall back to default
        target_provider = provider or self.default_provider
        
        # Check if provider is available
        if target_provider not in self.providers:
            # Try to find an available provider
            for fallback_provider in self.providers.keys():
                if await self.providers[fallback_provider].is_available():
                    target_provider = fallback_provider
                    logger.info(f"Falling back to {target_provider.value} provider")
                    break
            else:
                raise RuntimeError("No LLM providers are available")
        
        provider_instance = self.providers[target_provider]
        
        try:
            # Check availability before generating
            if not await provider_instance.is_available():
                raise RuntimeError(f"{target_provider.value} provider is not available")
            
            response_text = await provider_instance.generate_response(prompt, **kwargs)
            model_info = provider_instance.get_model_info()
            
            return {
                "response": response_text,
                "provider_used": target_provider.value,
                "model_info": model_info,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error generating response with {target_provider.value}: {e}")
            
            # Try fallback to other providers
            for fallback_provider in self.providers.keys():
                if fallback_provider != target_provider:
                    try:
                        fallback_instance = self.providers[fallback_provider]
                        if await fallback_instance.is_available():
                            logger.info(f"Falling back to {fallback_provider.value}")
                            response_text = await fallback_instance.generate_response(prompt, **kwargs)
                            model_info = fallback_instance.get_model_info()
                            
                            return {
                                "response": response_text,
                                "provider_used": fallback_provider.value,
                                "model_info": model_info,
                                "fallback_from": target_provider.value,
                                "timestamp": self._get_timestamp()
                            }
                    except Exception as fallback_error:
                        logger.error(f"Fallback to {fallback_provider.value} also failed: {fallback_error}")
                        continue
            
            # If all providers fail
            raise RuntimeError(f"All LLM providers failed. Last error: {e}")
    
    async def set_default_provider(self, provider: LLMProvider):
        """Set the default LLM provider"""
        if provider in self.providers:
            self.default_provider = provider
            logger.info(f"Default provider set to {provider.value}")
        else:
            raise ValueError(f"Provider {provider.value} is not available")
    
    def get_default_provider(self) -> LLMProvider:
        """Get the current default provider"""
        return self.default_provider
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

# Global instance
multi_llm_service = MultiLLMService()