# Wrapper module to replace emergentintegrations for cloud deployment
# This provides a compatible interface using google-generativeai directly

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

def get_ai_api_key() -> str:
    """Get the appropriate AI API key based on environment.
    
    Priority:
    1. GOOGLE_AI_API_KEY - Direct Google API key (for Cloud Run)
    2. EMERGENT_LLM_KEY - Emergent platform key (for Emergent deployment)
    """
    # First try Google AI API key (for cloud deployment)
    google_key = os.getenv('GOOGLE_AI_API_KEY')
    if google_key:
        logger.info("🔑 Using GOOGLE_AI_API_KEY for AI requests")
        return google_key
    
    # Fall back to Emergent key
    emergent_key = os.getenv('EMERGENT_LLM_KEY')
    if emergent_key:
        logger.info("🔑 Using EMERGENT_LLM_KEY for AI requests")
        return emergent_key
    
    raise ValueError("No AI API key configured. Set GOOGLE_AI_API_KEY or EMERGENT_LLM_KEY")

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
        api_key: str = None, 
        provider: str = "gemini", 
        model: Optional[str] = None,
        session_id: Optional[str] = None,  # Accept but ignore for compatibility
        system_message: Optional[str] = None  # Store for use in prompts
    ):
        # If no api_key provided, try to get from environment
        if api_key is None:
            self.api_key = get_ai_api_key()
        else:
            # Check if the provided key is Emergent key and we have Google key available
            google_key = os.getenv('GOOGLE_AI_API_KEY')
            if google_key:
                # Prefer Google key for direct API calls
                self.api_key = google_key
                logger.info("🔑 Overriding with GOOGLE_AI_API_KEY for direct API access")
            else:
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
                logger.info(f"✅ Initialized Gemini model: {model_name}")
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
    
    def _send_message_sync(self, message: UserMessage) -> str:
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
    
    def send_message(self, message: UserMessage):
        """Send a message - returns an awaitable result for async compatibility"""
        return AwaitableResult(self._send_message_sync, message)


class AwaitableResult:
    """Wrapper that makes sync results awaitable for async code compatibility"""
    
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        self._executed = False
        
    def _execute(self):
        if not self._executed:
            self._result = self._func(*self._args, **self._kwargs)
            self._executed = True
        return self._result
        
    def __await__(self):
        # Execute the function and yield the result
        result = self._execute()
        yield
        return result
        
    def __str__(self):
        return str(self._execute())
        
    def strip(self):
        result = self._execute()
        return result.strip() if result else ""
    
    def __bool__(self):
        result = self._execute()
        return bool(result)


# For compatibility with existing imports
__all__ = ["LlmChat", "UserMessage", "get_ai_api_key"]
