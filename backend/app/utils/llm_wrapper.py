# Wrapper module to replace emergentintegrations for cloud deployment
# This provides a compatible interface using google-generativeai directly

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class UserMessage:
    """User message wrapper"""
    def __init__(self, content: str):
        self.content = content
        self.role = "user"

class LlmChat:
    """LLM Chat wrapper that uses Google Generative AI directly"""
    
    def __init__(self, api_key: str, provider: str = "gemini", model: Optional[str] = None):
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self._client = None
        
    def _get_client(self):
        """Initialize the appropriate client based on provider"""
        if self._client is not None:
            return self._client
            
        if self.provider in ["gemini", "google"]:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model_name = self.model or "gemini-1.5-flash"
                self._client = genai.GenerativeModel(model_name)
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
        """Send a message and get response"""
        client = self._get_client()
        
        try:
            if self.provider in ["gemini", "google"]:
                response = client.generate_content(message.content)
                return response.text
            elif self.provider in ["openai", "gpt"]:
                model_name = self.model or "gpt-4o-mini"
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": message.content}]
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

# For compatibility with existing imports
__all__ = ["LlmChat", "UserMessage"]
