"""
Provider-First LLM Configuration System

This module provides recommended provider configurations and provider-level
fallback chains for the UnifiedLLMManager.

The new architecture prioritizes providers first, then models within each provider.

Configuration is now loaded from config/llm_config.yaml for centralized management.

Usage:
```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# Provider-First API
client = manager.get_client(provider="zhipu", model="glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])

# Provider-level fallback
result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Hello"}],
    providers=["zhipu", "deepseek", "openai"],
    model="glm-4-flash"
)
```
"""

# Import YAML configuration loader
from config.yaml_config_loader import (
    load_llm_config,
    get_task_recommendation,
    get_fallback_chain as get_yaml_fallback_chain,
    get_cost_reference as get_yaml_cost_reference,
    list_all_models
)

# Load configuration from YAML
_config = load_llm_config()

# Provider-level fallback chains (loaded from YAML)
PROVIDER_FALLBACK_CHAINS = _config.get("fallback_chains", {
    "text": ["zhipu", "deepseek", "openai"],
    "vision": ["zhipu", "bytedance", "openai"],
    "thinking": ["modelscope", "zhipu", "deepseek"],
    "bilingual": ["zhipu", "bytedance", "deepseek"],
})

# Task recommendations (loaded from YAML)
TASK_RECOMMENDATIONS = _config.get("task_recommendations", {})

# Legacy compatibility - Model-level fallback chains (deprecated)
# These are maintained for backward compatibility but should not be used in new code
FALLBACK_CHAINS = {
    "text": ["deepseek-chat", "deepseek-reasoner"],
    "vision": ["doubao-vision"],
    "thinking": ["deepseek-reasoner"],
}

# Recommended model configurations (loaded from YAML)
_all_models = list_all_models()

RECOMMENDED_TEXT_MODELS = []
RECOMMENDED_VISION_MODELS = []
RECOMMENDED_THINKING_MODELS = []

for provider_id, models in _all_models.items():
    provider_config = _config["providers"].get(provider_id, {})
    capabilities = provider_config.get("capabilities", [])

    if "text" in capabilities:
        RECOMMENDED_TEXT_MODELS.extend(models)
    if "vision" in capabilities:
        RECOMMENDED_VISION_MODELS.extend(models)
    if "thinking" in capabilities:
        RECOMMENDED_THINKING_MODELS.extend(models)

# Remove duplicates while preserving order
RECOMMENDED_TEXT_MODELS = list(dict.fromkeys(RECOMMENDED_TEXT_MODELS))
RECOMMENDED_VISION_MODELS = list(dict.fromkeys(RECOMMENDED_VISION_MODELS))
RECOMMENDED_THINKING_MODELS = list(dict.fromkeys(RECOMMENDED_THINKING_MODELS))

# Cost reference (loaded from YAML)
COST_REFERENCE = _config.get("cost_reference", {})


def get_recommended_models(task_type: str) -> dict:
    """
    Get recommended models for a specific task

    Args:
        task_type: Task type (polish, vision_formula, vision_code, etc.)

    Returns:
        Dictionary with models, fallback, and reason
    """
    recommendation = get_task_recommendation(task_type)
    if recommendation:
        return recommendation

    # Fallback to default
    return {
        "providers": ["deepseek"],
        "models": RECOMMENDED_TEXT_MODELS[:2] if RECOMMENDED_TEXT_MODELS else ["deepseek-chat"],
        "fallback_providers": PROVIDER_FALLBACK_CHAINS.get("text", ["deepseek"]),
        "reason": "General purpose text task"
    }


def get_fallback_chain(task_type: str) -> list:
    """
    Get fallback chain for a task type

    Args:
        task_type: Task type (text, vision, thinking)

    Returns:
        List of model IDs in priority order (legacy) or provider IDs (new)
    """
    # Try to get from YAML first (provider-level)
    yaml_chain = get_yaml_fallback_chain(task_type)
    if yaml_chain:
        return yaml_chain

    # Fallback to legacy model-level chains
    return FALLBACK_CHAINS.get(task_type, FALLBACK_CHAINS["text"])



def list_all_vision_models() -> list:
    """List all models that support vision"""
    return RECOMMENDED_VISION_MODELS


def list_all_text_models() -> list:
    """List all models that support text"""
    return RECOMMENDED_TEXT_MODELS
