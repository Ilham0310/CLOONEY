"""
Gemini Client Wrapper
Provides a thin wrapper around Google's Gemini API for easy integration and model swapping.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from functools import lru_cache

logger = logging.getLogger(__name__)

# Try to import Gemini SDK - supports multiple possible package names
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    SDK_TYPE = "google-generativeai"
except ImportError:
    try:
        from google import genai
        GEMINI_AVAILABLE = True
        SDK_TYPE = "google-genai"
    except ImportError:
        GEMINI_AVAILABLE = False
        SDK_TYPE = None


class GeminiClient:
    """Wrapper for Gemini API client with safety and cost controls."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name (defaults to GEMINI_MODEL env var or "gemini-2.0-flash-exp")
            temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Maximum tokens in response (optional)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Gemini SDK not available. Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable."
            )
        
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", temperature))
        self.max_tokens = max_tokens or int(os.getenv("GEMINI_MAX_TOKENS", "0") or "0") or None
        
        # Configure based on SDK type
        if SDK_TYPE == "google-generativeai":
            genai.configure(api_key=self.api_key)
            self.client = genai
        elif SDK_TYPE == "google-genai":
            self.client = genai.Client(api_key=self.api_key)
        else:
            raise RuntimeError("Unknown Gemini SDK type")
        
        logger.info(f"Gemini client initialized with model: {self.model}")
    
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: Input prompt
            model: Override default model
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        model_name = model or self.model
        
        try:
            if SDK_TYPE == "google-generativeai":
                # Use GenerativeModel API
                model_instance = genai.GenerativeModel(model_name)
                generation_config = {
                    "temperature": kwargs.get("temperature", self.temperature),
                }
                if self.max_tokens:
                    generation_config["max_output_tokens"] = self.max_tokens
                
                response = model_instance.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return response.text
            
            elif SDK_TYPE == "google-genai":
                # Use Client API
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": kwargs.get("temperature", self.temperature),
                        "max_output_tokens": self.max_tokens
                    } if self.max_tokens else {
                        "temperature": kwargs.get("temperature", self.temperature)
                    }
                )
                return response.text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            raise
    
    def structured_call(
        self,
        prompt: str,
        schema_description: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response using Gemini.
        
        Args:
            prompt: Input prompt
            schema_description: Description of expected JSON schema
            model: Override default model
            
        Returns:
            Parsed JSON response as dict
        """
        full_prompt = f"""{prompt}

Please respond with valid JSON matching this schema:
{schema_description}

Return ONLY the JSON object, no markdown formatting, no code blocks, no explanation."""
        
        response_text = self.generate_text(full_prompt, model=model)
        
        # Clean response (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
    
    def chat(
        self,
        history: List[Dict[str, str]],
        new_message: str,
        model: Optional[str] = None
    ) -> str:
        """
        Chat with conversation history.
        
        Args:
            history: List of message dicts with 'role' and 'content' keys
            new_message: New user message
            model: Override default model
            
        Returns:
            Assistant response
        """
        model_name = model or self.model
        
        try:
            if SDK_TYPE == "google-generativeai":
                # Build conversation
                model_instance = genai.GenerativeModel(model_name)
                chat_instance = model_instance.start_chat(history=history)
                response = chat_instance.send_message(new_message)
                return response.text
            
            elif SDK_TYPE == "google-genai":
                # Build messages list
                messages = history + [{"role": "user", "content": new_message}]
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=messages
                )
                return response.text
            
        except Exception as e:
            logger.error(f"Error in chat with Gemini: {e}")
            raise


# Global client instance (lazy initialization)
_client_instance: Optional[GeminiClient] = None


@lru_cache(maxsize=1)
def is_ai_enabled() -> bool:
    """Check if AI is enabled (API key available)."""
    return bool(os.getenv("GEMINI_API_KEY")) and GEMINI_AVAILABLE


def get_client() -> Optional[GeminiClient]:
    """Get or create global Gemini client instance."""
    global _client_instance
    
    if not is_ai_enabled():
        return None
    
    if _client_instance is None:
        try:
            _client_instance = GeminiClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            return None
    
    return _client_instance


def generate_text(prompt: str, *, model: str = "gemini-2.0-flash-exp") -> str:
    """
    Convenience function to generate text.
    
    Args:
        prompt: Input prompt
        model: Model name (optional)
        
    Returns:
        Generated text
        
    Raises:
        ValueError: If AI is not enabled
    """
    client = get_client()
    if not client:
        raise ValueError("AI is not enabled. Set GEMINI_API_KEY environment variable.")
    return client.generate_text(prompt, model=model)


def structured_call(prompt: str, schema_description: str) -> Dict[str, Any]:
    """
    Convenience function for structured JSON generation.
    
    Args:
        prompt: Input prompt
        schema_description: Expected JSON schema description
        
    Returns:
        Parsed JSON response
        
    Raises:
        ValueError: If AI is not enabled
    """
    client = get_client()
    if not client:
        raise ValueError("AI is not enabled. Set GEMINI_API_KEY environment variable.")
    return client.structured_call(prompt, schema_description)


def chat(history: List[Dict[str, str]], new_message: str) -> str:
    """
    Convenience function for chat with history.
    
    Args:
        history: Conversation history
        new_message: New user message
        
    Returns:
        Assistant response
        
    Raises:
        ValueError: If AI is not enabled
    """
    client = get_client()
    if not client:
        raise ValueError("AI is not enabled. Set GEMINI_API_KEY environment variable.")
    return client.chat(history, new_message)

