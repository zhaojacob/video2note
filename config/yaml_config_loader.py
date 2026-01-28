"""
YAML Configuration Loader for LLM Settings

This module loads and validates the llm_config.yaml file, providing a centralized
configuration system for all LLM providers, models, and task recommendations.

Usage:
    from config.yaml_config_loader import load_llm_config, get_provider_config

    # Load full configuration
    config = load_llm_config()

    # Get specific provider configuration
    zhipu_config = get_provider_config("zhipu")

    # Get task recommendation
    polish_config = get_task_recommendation("polish")
"""
import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Use standard logging to avoid circular import with utils.logger
logger = logging.getLogger(__name__)

# Cache for loaded configuration
_config_cache: Optional[Dict[str, Any]] = None


@dataclass
class ProviderConfig:
    """Provider configuration data class"""
    id: str
    name: str
    api_key_env: str
    base_url: str
    timeout: int
    default_max_tokens: int
    models: List[str]
    capabilities: List[str]
    supports_async: bool = True
    requires_extra_body: bool = False
    extra_body: Optional[Dict[str, Any]] = None
    model_aliases: Optional[Dict[str, str]] = None
    use_responses_api: bool = False  # For Doubao special API format

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        return os.getenv(self.api_key_env)

    def has_model(self, model: str) -> bool:
        """Check if provider supports the model"""
        return model in self.models

    def get_real_model_name(self, model: str) -> str:
        """Get real model name (handle aliases)"""
        if self.model_aliases and model in self.model_aliases:
            return self.model_aliases[model]
        return model


def get_config_path() -> Path:
    """Get path to llm_config.yaml"""
    config_dir = Path(__file__).parent
    return config_dir / "llm_config.yaml"


def load_llm_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load LLM configuration from YAML file

    Args:
        force_reload: Force reload from file (ignore cache)

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None and not force_reload:
        return _config_cache

    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"LLM configuration file not found: {config_path}\n"
            f"Please create config/llm_config.yaml"
        )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Validate configuration
        _validate_config(config)

        # Cache the configuration
        _config_cache = config

        logger.info(f"Loaded LLM configuration from {config_path}")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def _validate_config(config: Dict[str, Any]):
    """
    Validate configuration structure

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["version", "defaults", "providers", "task_recommendations", "fallback_chains"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key in configuration: {key}")

    # Validate providers
    if not config["providers"]:
        raise ValueError("No providers configured")

    for provider_id, provider_config in config["providers"].items():
        required_provider_keys = ["name", "api_key_env", "base_url", "models", "capabilities"]
        for key in required_provider_keys:
            if key not in provider_config:
                raise ValueError(f"Provider '{provider_id}' missing required key: {key}")

    logger.debug("Configuration validation passed")


def get_provider_config(provider_id: str) -> Optional[ProviderConfig]:
    """
    Get configuration for a specific provider

    Args:
        provider_id: Provider identifier (e.g., "zhipu", "openai")

    Returns:
        ProviderConfig object or None if not found
    """
    config = load_llm_config()
    providers = config.get("providers", {})

    if provider_id not in providers:
        logger.warning(f"Provider not found in configuration: {provider_id}")
        return None

    provider_data = providers[provider_id]

    return ProviderConfig(
        id=provider_id,
        name=provider_data["name"],
        api_key_env=provider_data["api_key_env"],
        base_url=provider_data["base_url"],
        timeout=provider_data.get("timeout", 60),
        default_max_tokens=provider_data.get("default_max_tokens", 4096),
        models=provider_data["models"],
        capabilities=provider_data["capabilities"],
        supports_async=provider_data.get("supports_async", True),
        requires_extra_body=provider_data.get("requires_extra_body", False),
        extra_body=provider_data.get("extra_body"),
        model_aliases=provider_data.get("model_aliases"),
        use_responses_api=provider_data.get("use_responses_api", False)
    )


def get_all_providers() -> Dict[str, ProviderConfig]:
    """
    Get all provider configurations

    Returns:
        Dictionary of {provider_id: ProviderConfig}
    """
    config = load_llm_config()
    providers = config.get("providers", {})

    return {
        provider_id: get_provider_config(provider_id)
        for provider_id in providers.keys()
    }


def get_task_recommendation(task_type: str) -> Optional[Dict[str, Any]]:
    """
    Get recommended configuration for a specific task

    Args:
        task_type: Task type (e.g., "polish", "vision_formula", "summarize")

    Returns:
        Task recommendation dictionary or None if not found
    """
    config = load_llm_config()
    recommendations = config.get("task_recommendations", {})

    if task_type not in recommendations:
        logger.warning(f"No recommendation found for task type: {task_type}")
        return None

    return recommendations[task_type]


def get_fallback_chain(chain_type: str) -> List[str]:
    """
    Get fallback chain for a specific type

    Args:
        chain_type: Chain type (e.g., "text", "vision", "thinking")

    Returns:
        List of provider IDs in fallback order
    """
    config = load_llm_config()
    chains = config.get("fallback_chains", {})

    if chain_type not in chains:
        logger.warning(f"No fallback chain found for type: {chain_type}")
        return []

    return chains[chain_type]


def get_default_provider(task_type: str) -> Optional[str]:
    """
    Get default provider for a task type

    Args:
        task_type: Task type ("text", "vision", "thinking")

    Returns:
        Provider ID or None
    """
    config = load_llm_config()
    defaults = config.get("defaults", {})

    key = f"{task_type}_provider"
    return defaults.get(key)


def get_default_model(task_type: str) -> Optional[str]:
    """
    Get default model for a task type

    Args:
        task_type: Task type ("text", "vision")

    Returns:
        Model ID or None
    """
    config = load_llm_config()
    defaults = config.get("defaults", {})

    key = f"{task_type}_model"
    return defaults.get(key)


def is_unified_manager_enabled() -> bool:
    """
    Check if unified manager is enabled by default

    Returns:
        True if enabled, False otherwise
    """
    config = load_llm_config()
    defaults = config.get("defaults", {})
    return defaults.get("use_unified_manager", False)


def get_concurrency_config() -> Dict[str, Any]:
    """
    Get concurrency and retry configuration

    Returns:
        Concurrency configuration dictionary
    """
    config = load_llm_config()
    return config.get("concurrency", {
        "max_concurrent": 5,
        "enable_checkpoint": True,
        "checkpoint_dir": "output/checkpoints",
        "max_retries": 3,
        "retry_delay": 2,
        "exponential_backoff": True
    })


def get_cost_reference(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cost reference for a model

    Args:
        model_id: Model identifier

    Returns:
        Cost reference dictionary or None
    """
    config = load_llm_config()
    costs = config.get("cost_reference", {})
    return costs.get(model_id)


def list_available_providers(capability: Optional[str] = None) -> List[str]:
    """
    List available providers (with API keys configured)

    Args:
        capability: Optional capability filter (e.g., "vision", "text")

    Returns:
        List of provider IDs
    """
    all_providers = get_all_providers()
    available = []

    for provider_id, provider_config in all_providers.items():
        # Check if API key is configured
        if not provider_config.get_api_key():
            continue

        # Check capability filter
        if capability and capability not in provider_config.capabilities:
            continue

        available.append(provider_id)

    return available


def list_all_models(capability: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List all models grouped by provider

    Args:
        capability: Optional capability filter

    Returns:
        Dictionary of {provider_id: [model_ids]}
    """
    all_providers = get_all_providers()
    models_by_provider = {}

    for provider_id, provider_config in all_providers.items():
        # Check capability filter
        if capability and capability not in provider_config.capabilities:
            continue

        models_by_provider[provider_id] = provider_config.models

    return models_by_provider


# Convenience function for backward compatibility
def get_recommended_models(task_type: str) -> Dict[str, Any]:
    """
    Get recommended models for a task (backward compatible)

    Args:
        task_type: Task type

    Returns:
        Recommendation dictionary
    """
    recommendation = get_task_recommendation(task_type)
    if not recommendation:
        # Return default fallback
        return {
            "providers": ["zhipu", "deepseek"],
            "models": ["glm-4-flash", "deepseek-chat"],
            "fallback_providers": ["zhipu", "deepseek", "openai"],
            "reason": "General purpose task"
        }
    return recommendation


if __name__ == "__main__":
    # Test configuration loading
    print("Testing YAML configuration loader...")

    try:
        config = load_llm_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  Version: {config['version']}")
        print(f"  Providers: {len(config['providers'])}")

        # Test provider loading
        zhipu = get_provider_config("zhipu")
        if zhipu:
            print(f"✓ Zhipu provider loaded: {zhipu.name}")
            print(f"  Models: {', '.join(zhipu.models)}")
            print(f"  API Key configured: {zhipu.get_api_key() is not None}")

        # Test task recommendation
        polish_rec = get_task_recommendation("polish")
        if polish_rec:
            print(f"✓ Polish task recommendation: {polish_rec['providers']}")

        # Test fallback chain
        text_fallback = get_fallback_chain("text")
        print(f"✓ Text fallback chain: {text_fallback}")

        # List available providers
        available = list_available_providers()
        print(f"✓ Available providers (with API keys): {available}")

        print("\n✓ All tests passed!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
