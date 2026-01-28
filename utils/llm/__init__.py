"""
Unified LLM Client Module (Provider-First Architecture)

Provides a unified interface for interacting with various LLM providers
including OpenAI, GLM, Doubao, DeepSeek, and other OpenAI-compatible APIs.

Main components:
- BaseLLMClient: Abstract base class for all LLM clients
- ModelRegistry: Predefined model configurations
- ProviderRegistry: Provider registry with capability filtering
- UnifiedLLMManager: Central manager with provider-level fallback strategies

Usage (Provider-First API):
    from utils.llm import UnifiedLLMManager
    manager = UnifiedLLMManager()
    client = manager.get_client(provider="zhipu", model="glm-4-flash")
    result = client.chat_completion([{"role": "user", "content": "Hello"}])

Legacy API (Still supported):
    from utils.llm import UnifiedLLMManager
    manager = UnifiedLLMManager()
    client = manager.get_client("glm-4-flash")
    result = client.chat_completion([{"role": "user", "content": "Hello"}])
"""
from .base_client import BaseLLMClient
from .model_registry import ModelRegistry, ModelCapability, BUILTIN_MODELS
from .provider_registry import ProviderRegistry, ProviderCapability, ProviderInfo, BUILTIN_PROVIDERS
from .unified_manager import UnifiedLLMManager

__all__ = [
    "BaseLLMClient",
    "ModelRegistry",
    "ModelCapability",
    "BUILTIN_MODELS",
    "ProviderRegistry",
    "ProviderCapability",
    "ProviderInfo",
    "BUILTIN_PROVIDERS",
    "UnifiedLLMManager",
]
