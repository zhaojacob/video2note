"""
Provider Registry - Provider-First LLM Architecture

This module implements the Provider-First architecture where providers are first-class entities.
Models are provided by providers, not the other way around.

Core principles:
1. Provider is an independent entity
2. Provider configuration is separate from Model capabilities
3. Multiple providers can offer the same model name
4. Provider-level fallback strategies
5. Full backward compatibility

Usage:
    from utils.llm.provider_registry import ProviderRegistry, ProviderCapability

    registry = ProviderRegistry()

    # Get provider info
    provider = registry.get_provider("zhipu")

    # List providers by capability
    vision_providers = registry.list_providers(capability=ProviderCapability.VISION)

    # Find providers offering a specific model
    providers_for_gpt4 = registry.get_providers_for_model("gpt-4")
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ProviderCapability(Enum):
    """Provider capability enumeration"""
    TEXT = "text"
    VISION = "vision"
    THINKING = "thinking"
    LONG_CONTEXT = "long_context"
    BILINGUAL = "bilingual"
    FAST = "fast"
    STREAMING = "streaming"


@dataclass
class ProviderInfo:
    """
    Provider information (first-class entity)

    A provider represents an LLM service/API provider (e.g., Zhipu, OpenAI, DeepSeek).
    Each provider has its own base_url, authentication, and list of supported models.
    """
    id: str                          # Provider unique ID
    name: str                        # Display name
    base_url: str                    # API base URL
    api_key_env: str                 # API key environment variable
    models: List[str]                # List of supported models (aliases)
    capabilities: List[ProviderCapability]  # Provider capabilities
    timeout: int = 60
    default_max_tokens: int = 4096
    supports_async: bool = True
    requires_extra_body: bool = False
    extra_body_params: Optional[Dict] = None
    model_aliases: Optional[Dict[str, str]] = None  # Alias -> real model name mapping
    use_responses_api: bool = False  # 是否使用 responses.create() API (豆包专用)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variables"""
        return os.getenv(self.api_key_env)

    def has_model(self, model: str) -> bool:
        """Check if provider supports the specified model"""
        return model in self.models

    def supports_capability(self, cap: ProviderCapability) -> bool:
        """Check if provider supports a specific capability"""
        return cap in self.capabilities

    def get_real_model_name(self, model: str) -> str:
        """
        Get the real model name for API calls

        Handles model aliases. For example, 'deepseek-v3' -> 'deepseek-ai/DeepSeek-V3.2'

        Args:
            model: Model alias or real model name

        Returns:
            Real model name to use in API calls
        """
        if self.model_aliases and model in self.model_aliases:
            return self.model_aliases[model]
        return model


# Built-in providers - now loaded from YAML configuration
def _load_builtin_providers() -> Dict[str, ProviderInfo]:
    """
    Load built-in providers from YAML configuration

    Returns:
        Dictionary of {provider_id: ProviderInfo}
    """
    try:
        from config.yaml_config_loader import get_all_providers as get_yaml_providers

        yaml_providers = get_yaml_providers()
        builtin = {}

        for provider_id, yaml_config in yaml_providers.items():
            # Convert capability strings to ProviderCapability enums
            capabilities = []
            for cap_str in yaml_config.capabilities:
                try:
                    capabilities.append(ProviderCapability(cap_str))
                except ValueError:
                    pass  # Skip unknown capabilities

            builtin[provider_id] = ProviderInfo(
                id=yaml_config.id,
                name=yaml_config.name,
                base_url=yaml_config.base_url,
                api_key_env=yaml_config.api_key_env,
                models=yaml_config.models,
                capabilities=capabilities,
                timeout=yaml_config.timeout,
                default_max_tokens=yaml_config.default_max_tokens,
                supports_async=yaml_config.supports_async,
                requires_extra_body=yaml_config.requires_extra_body,
                extra_body_params=yaml_config.extra_body,
                model_aliases=yaml_config.model_aliases,
                use_responses_api=getattr(yaml_config, 'use_responses_api', False)
            )

        return builtin

    except Exception as e:
        # Fallback to hardcoded providers if YAML loading fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load providers from YAML, using fallback: {e}")

        return {
            "bytedance": ProviderInfo(
                id="bytedance",
                name="字节跳动 (Doubao)",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key_env="ARK_API_KEY",
                models=["doubao-vision"],
                capabilities=[
                    ProviderCapability.VISION,
                    ProviderCapability.BILINGUAL
                ],
                timeout=300,
                default_max_tokens=1000
            ),
            "deepseek": ProviderInfo(
                id="deepseek",
                name="DeepSeek",
                base_url="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
                models=["deepseek-chat", "deepseek-reasoner"],
                capabilities=[
                    ProviderCapability.TEXT,
                    ProviderCapability.LONG_CONTEXT,
                    ProviderCapability.THINKING,
                    ProviderCapability.FAST
                ],
                timeout=60,
                default_max_tokens=8192
            )
        }


# Load providers from YAML
BUILTIN_PROVIDERS: Dict[str, ProviderInfo] = _load_builtin_providers()


class ProviderRegistry:
    """
    Provider registry

    Manages all available providers (built-in and custom).
    Provides methods to query providers by capability or model.
    """

    def __init__(self):
        self._providers = BUILTIN_PROVIDERS.copy()
        self._load_custom_providers()

    def _load_custom_providers(self):
        """
        Load custom providers from .env file

        Supports up to 10 custom providers (CUSTOM_PROVIDER_1_* to CUSTOM_PROVIDER_10_*)

        .env format:
            CUSTOM_PROVIDER_1_NAME=MyProxy
            CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
            CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
            CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o
        """
        for i in range(1, 11):
            prefix = f"CUSTOM_PROVIDER_{i}_"

            name = os.getenv(f"{prefix}NAME")
            if not name:
                break

            base_url = os.getenv(f"{prefix}BASE_URL")
            api_key_env = os.getenv(f"{prefix}API_KEY")
            models_str = os.getenv(f"{prefix}MODELS", "")

            if not base_url or not api_key_env:
                continue

            models = [m.strip() for m in models_str.split(",") if m.strip()]

            # Generate provider ID from name
            provider_id = f"custom-{name.lower().replace(' ', '-')}"

            self._providers[provider_id] = ProviderInfo(
                id=provider_id,
                name=name,
                base_url=base_url,
                api_key_env=api_key_env,
                models=models,
                capabilities=[ProviderCapability.TEXT, ProviderCapability.VISION],
                timeout=60,
                default_max_tokens=4096
            )

    def get_provider(self, provider_id: str) -> Optional[ProviderInfo]:
        """
        Get provider information by ID

        Args:
            provider_id: Provider identifier (e.g., "zhipu", "openai")

        Returns:
            ProviderInfo or None if not found
        """
        return self._providers.get(provider_id)

    def list_providers(
        self,
        capability: Optional[ProviderCapability] = None
    ) -> Dict[str, ProviderInfo]:
        """
        List providers, optionally filtered by capability

        Args:
            capability: Filter by capability (optional)

        Returns:
            Dictionary of {provider_id: ProviderInfo}
        """
        if capability:
            return {
                pid: p for pid, p in self._providers.items()
                if capability in p.capabilities
            }
        return self._providers.copy()

    def get_providers_for_model(self, model: str) -> List[ProviderInfo]:
        """
        Get all providers that support the specified model

        Args:
            model: Model name (e.g., "gpt-4", "glm-4-flash")

        Returns:
            List of ProviderInfo objects

        Example:
            # Find all providers offering gpt-4
            providers = registry.get_providers_for_model("gpt-4")
            for p in providers:
                print(f"{p.name}: {p.base_url}")
        """
        return [
            p for p in self._providers.values()
            if model in p.models
        ]

    def register_custom_provider(self, provider: ProviderInfo):
        """
        Dynamically register a custom provider

        Args:
            provider: ProviderInfo object to register

        Example:
            from utils.llm.provider_registry import ProviderInfo, ProviderCapability

            custom_provider = ProviderInfo(
                id="local-ollama",
                name="Local Ollama",
                base_url="http://localhost:11434/v1",
                api_key_env="OLLAMA_API_KEY",
                models=["llama3", "mistral"],
                capabilities=[ProviderCapability.TEXT]
            )
            registry.register_custom_provider(custom_provider)
        """
        self._providers[provider.id] = provider

    def get_all_providers(self) -> Dict[str, ProviderInfo]:
        """
        Get all registered providers (built-in + custom)

        Returns:
            Dictionary of {provider_id: ProviderInfo}
        """
        return self._providers.copy()
