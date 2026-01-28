"""
Provider-First LLM Configuration System

This module provides recommended provider configurations and provider-level
fallback chains for the UnifiedLLMManager.

The new architecture prioritizes providers first, then models within each provider.

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

# Provider-level fallback chains (by task type)
# These define the order in which providers are tried for each task type
PROVIDER_FALLBACK_CHAINS = {
    "text": ["zhipu", "deepseek", "openai"],
    "vision": ["zhipu", "bytedance", "openai"],
    "thinking": ["modelscope", "zhipu", "deepseek"],
    "bilingual": ["zhipu", "bytedance", "deepseek"],
}

# Task recommendations (provider-aware)
TASK_RECOMMENDATIONS = {
    "polish": {
        "providers": ["zhipu", "deepseek"],
        "models": ["glm-4-flash", "deepseek-chat"],
        "fallback_providers": PROVIDER_FALLBACK_CHAINS["text"],
        "reason": "Fast, cost-effective for text polishing"
    },
    "vision_formula": {
        "providers": ["zhipu"],
        "models": ["glm-4.6v"],
        "fallback_providers": ["bytedance"],
        "reason": "GLM excels at mathematical formulas and code"
    },
    "vision_code": {
        "providers": ["zhipu"],
        "models": ["glm-4.6v"],
        "fallback_providers": ["bytedance"],
        "reason": "GLM has strong code understanding capabilities"
    },
    "vision_chinese": {
        "providers": ["bytedance"],
        "models": ["doubao-vision"],
        "fallback_providers": ["zhipu"],
        "reason": "Doubao excels at Chinese document understanding"
    },
    "vision_general": {
        "providers": ["zhipu", "bytedance"],
        "models": ["glm-4.6v", "doubao-vision"],
        "fallback_providers": PROVIDER_FALLBACK_CHAINS["vision"],
        "reason": "Load balancing for general vision tasks"
    },
    "summarize": {
        "providers": ["modelscope", "deepseek"],
        "models": ["deepseek-reasoner", "deepseek-chat"],
        "fallback_providers": PROVIDER_FALLBACK_CHAINS["text"],
        "reason": "Long context and thinking capabilities"
    },
    "translate": {
        "providers": ["zhipu", "deepseek"],
        "models": ["glm-4-flash", "deepseek-chat"],
        "fallback_providers": PROVIDER_FALLBACK_CHAINS["text"],
        "reason": "Strong bilingual support"
    },
}

# Legacy compatibility - Model-level fallback chains (deprecated)
# These are maintained for backward compatibility but should not be used in new code
FALLBACK_CHAINS = {
    "text": ["glm-4-flash", "deepseek-chat", "gpt-4o-mini"],
    "vision": ["glm-4.6v", "doubao-vision", "gpt-4o"],
    "thinking": ["deepseek-reasoner", "glm-4.6v"],
}

# Recommended model configurations (for quick start)
RECOMMENDED_TEXT_MODELS = [
    "glm-4-flash",        # Fast, high free tier, excellent Chinese
    "deepseek-chat",      # Cheap, long context, non-thinking
    "deepseek-reasoner",  # Thinking mode for complex reasoning
    "gpt-4o-mini",        # Fast, multi-language
]

RECOMMENDED_VISION_MODELS = [
    "glm-4.6v",         # Thinking chain, strong formula/code understanding
    "doubao-vision",    # Strong Chinese document understanding
    "gpt-4o",           # Strong general vision capabilities
]

# Thinking models (for complex reasoning tasks)
RECOMMENDED_THINKING_MODELS = [
    "deepseek-reasoner",  # DeepSeek reasoning mode (via DeepSeek API)
    "glm-4.6v",          # GLM with thinking chain
]

# Cost per 1M tokens (approximate, for reference)
COST_REFERENCE = {
    "glm-4-flash": {"input": 0.1, "output": 0.1, "currency": "CNY"},
    "glm-4.6v": {"input": 0.1, "output": 0.1, "currency": "CNY"},
    "deepseek-chat": {"input": 1.0, "output": 2.0, "currency": "CNY"},
    "deepseek-reasoner": {"input": 1.0, "output": 2.0, "currency": "CNY"},
    "doubao-vision": {"input": 0.5, "output": 1.0, "currency": "CNY"},
    "gpt-4o": {"input": 2.5, "output": 10.0, "currency": "USD"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6, "currency": "USD"},
}


def get_recommended_models(task_type: str) -> dict:
    """
    Get recommended models for a specific task

    Args:
        task_type: Task type (polish, vision_formula, vision_code, etc.)

    Returns:
        Dictionary with models, fallback, and reason
    """
    return TASK_RECOMMENDATIONS.get(task_type, {
        "models": RECOMMENDED_TEXT_MODELS,
        "fallback": FALLBACK_CHAINS["text"],
        "reason": "General purpose text task"
    })


def get_fallback_chain(task_type: str) -> list:
    """
    Get fallback chain for a task type

    Args:
        task_type: Task type (text, vision, thinking)

    Returns:
        List of model IDs in priority order
    """
    return FALLBACK_CHAINS.get(task_type, FALLBACK_CHAINS["text"])


def list_all_vision_models() -> list:
    """List all models that support vision"""
    return RECOMMENDED_VISION_MODELS


def list_all_text_models() -> list:
    """List all models that support text"""
    return RECOMMENDED_TEXT_MODELS
