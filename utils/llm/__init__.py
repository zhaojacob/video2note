"""
Unified LLM Client Module

Provides a unified interface for interacting with various LLM providers
including OpenAI, GLM, Doubao, DeepSeek, and other OpenAI-compatible APIs.

Main components:
- BaseLLMClient: Abstract base class for all LLM clients
- ModelRegistry: Predefined model configurations
- UnifiedLLMManager: Central manager with fallback strategies

Usage:
    from utils.llm.unified_manager import UnifiedLLMManager
    manager = UnifiedLLMManager()
    client = manager.get_client("glm-4-flash")
    result = client.chat_completion([{"role": "user", "content": "Hello"}])
"""
from .base_client import BaseLLMClient
from .model_registry import ModelRegistry, ModelCapability, BUILTIN_MODELS
from .unified_manager import UnifiedLLMManager

__all__ = [
    "BaseLLMClient",
    "ModelRegistry",
    "ModelCapability",
    "BUILTIN_MODELS",
    "UnifiedLLMManager",
]
