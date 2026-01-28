"""
Simplified LLM Configuration System

This module provides recommended model configurations and fallback chains
for the UnifiedLLMManager.

Usage:
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# List available models
print(manager.list_available_models())

# Use model
client = manager.get_client("glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```
"""

# Recommended model configurations (for quick start)

# Text tasks (by recommended priority)
RECOMMENDED_TEXT_MODELS = [
    "glm-4-flash",      # Fast, high free tier, excellent Chinese
    "deepseek-chat",    # Cheap, long context
    "gpt-4o-mini",      # Fast, multi-language
]

# Image analysis tasks
RECOMMENDED_VISION_MODELS = [
    "glm-4.6v",         # Thinking chain, strong formula/code understanding
    "doubao-vision",    # Strong Chinese document understanding
    "gpt-4o",           # Strong general vision capabilities
]

# Fallback strategy configuration
FALLBACK_CHAINS = {
    "text": ["glm-4-flash", "deepseek-chat", "gpt-4o-mini"],
    "vision": ["glm-4.6v", "doubao-vision", "gpt-4o"],
    "thinking": ["deepseek-v3", "glm-4.6v"],
}

# Task-specific model recommendations
TASK_RECOMMENDATIONS = {
    "polish": {
        "models": ["glm-4-flash", "deepseek-chat"],
        "fallback": FALLBACK_CHAINS["text"],
        "reason": "Fast and cost-effective for text polishing"
    },
    "vision_formula": {
        "models": ["glm-4.6v"],
        "fallback": ["doubao-vision"],
        "reason": "GLM excels at mathematical formulas and code"
    },
    "vision_code": {
        "models": ["glm-4.6v"],
        "fallback": ["doubao-vision"],
        "reason": "GLM has strong code understanding capabilities"
    },
    "vision_chinese": {
        "models": ["doubao-vision"],
        "fallback": ["glm-4.6v"],
        "reason": "Doubao excels at Chinese document understanding"
    },
    "vision_general": {
        "models": ["glm-4.6v", "doubao-vision"],
        "fallback": FALLBACK_CHAINS["vision"],
        "reason": "Load balancing for general vision tasks"
    },
    "summarize": {
        "models": ["deepseek-v3", "glm-4-flash"],
        "fallback": FALLBACK_CHAINS["text"],
        "reason": "Long context and thinking capabilities"
    },
}

# Cost per 1M tokens (approximate, for reference)
COST_REFERENCE = {
    "glm-4-flash": {"input": 0.1, "output": 0.1, "currency": "CNY"},
    "glm-4.6v": {"input": 0.1, "output": 0.1, "currency": "CNY"},
    "deepseek-chat": {"input": 1.0, "output": 2.0, "currency": "CNY"},
    "deepseek-v3": {"input": 1.0, "output": 2.0, "currency": "CNY"},
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
