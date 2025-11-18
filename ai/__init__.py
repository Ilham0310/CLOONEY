"""
AI Package for Clooney Project
Provides Gemini-powered agents for schema inference, endpoint inference, and rule refinement.
"""

from .gemini_client import (
    generate_text,
    structured_call,
    chat,
    is_ai_enabled,
    GeminiClient
)

__all__ = [
    'generate_text',
    'structured_call',
    'chat',
    'is_ai_enabled',
    'GeminiClient'
]

