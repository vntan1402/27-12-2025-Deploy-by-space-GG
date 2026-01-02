# Wrapper module to replace emergentintegrations for cloud deployment
# This provides a compatible interface using google-generativeai directly

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class UserMessage:
    """User message wrapper - compatible with emergentintegrations"""
    def __init__(self, content: str = None, text: str = None):
        # Support both 'content' and 'text' parameters for compatibility
        self.content = content or text or ""
        self.text = self.content  # Alias for compatibility
        self.role = "user"

class LlmChat:
    """LLM Chat wrapper that uses Google Generative AI directly
    
    Compatible with emergentintegrations LlmChat interface
    """
    
    def __init__(
        self, 
        api_key: str, 
        provider: str = "gemini", 
        model: Optional[str] = None,
        session_id: Optional[str] = None,  # Accept but ignore for compatibility
        system_message: Optional[str] = None  # Store for use in prompts
    ):
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self.session_id = session_id  # For compatibility, not used
        self.system_message = system_message
        self._client = None
        
    def with_model(self, provider: str, model: str) -> "LlmChat":
        """Fluent method to set provider and model - returns self for chaining"""
        self.provider = provider.lower()
        self.model = model
        return self
        
    def _get_client(self):
        """Initialize the appropriate client based on provider"""
        if self._client is not None:
            return self._client
            
        if self.provider in ["gemini", "google"]:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model_name = self.model or "gemini-1.5-flash"
                
                # Configure generation settings
                generation_config = {
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                # Add system instruction if provided
                if self.system_message:
                    self._client = genai.GenerativeModel(
                        model_name,
                        generation_config=generation_config,
                        system_instruction=self.system_message
                    )
                else:
                    self._client = genai.GenerativeModel(
                        model_name,
                        generation_config=generation_config
                    )
                return self._client
            except ImportError:
                logger.error("google-generativeai not installed")
                raise ImportError("Please install google-generativeai: pip install google-generativeai")
        elif self.provider in ["openai", "gpt"]:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                return self._client
            except ImportError:
                logger.error("openai not installed")
                raise ImportError("Please install openai: pip install openai")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def send_message(self, message: UserMessage) -> str:
        """Send a message and get response (sync version)"""
        client = self._get_client()
        
        # Get message content - support both .content and .text
        msg_content = getattr(message, 'content', None) or getattr(message, 'text', str(message))
        
        try:
            if self.provider in ["gemini", "google"]:
                response = client.generate_content(msg_content)
                return response.text
            elif self.provider in ["openai", "gpt"]:
                model_name = self.model or "gpt-4o-mini"
                messages = []
                if self.system_message:
                    messages.append({"role": "system", "content": self.system_message})
                messages.append({"role": "user", "content": msg_content})
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
    
    async def send_message_async(self, message: UserMessage) -> str:
        """Async version of send_message - for compatibility with async code"""
        # For now, just call sync version since google-generativeai doesn't have native async
        return self.send_message(message)

# Make send_message work as both sync and async
# This is a workaround for code that uses 'await chat.send_message()'
_original_send_message = LlmChat.send_message

def _make_awaitable_send_message(self, message: UserMessage):
    """Make send_message return an awaitable result"""
    class AwaitableResult:
        def __init__(self, func, *args, **kwargs):
            self._func = func
            self._args = args
            self._kwargs = kwargs
            self._result = None
            
        def __await__(self):
            # Execute the function and yield the result
            self._result = self._func(*self._args, **self._kwargs)
            yield
            return self._result
            
        def __str__(self):
            if self._result is None:
                self._result = self._func(*self._args, **self._kwargs)
            return str(self._result)
            
        def strip(self):
            if self._result is None:
                self._result = self._func(*self._args, **self._kwargs)
            return self._result.strip() if self._result else ""
    
    return AwaitableResult(_original_send_message, self, message)

# Replace send_message with awaitable version
LlmChat.send_message = _make_awaitable_send_message

# For compatibility with existing imports
__all__ = ["LlmChat", "UserMessage"]
