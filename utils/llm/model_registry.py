"""
Model Registry - 预定义的模型配置库
让用户可以轻松选择和配置模型
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT = "text"
    VISION = "vision"  # 图像理解
    THINKING = "thinking"  # 思维链
    LONG_CONTEXT = "long_context"  # 长上下文
    BILINGUAL = "bilingual"  # 双语支持
    FAST = "fast"  # 快速响应


@dataclass
class ModelInfo:
    """
    模型信息 (Provider-Aware)

    Note: This is being refactored to use provider_id instead of hardcoded provider info.
    Legacy properties (provider, env_key, api_base) are maintained for backward compatibility.
    """
    name: str  # 模型显示名称
    provider_id: str  # Provider ID (references ProviderRegistry)
    capabilities: List[ModelCapability]  # 能力列表
    timeout: int = 60
    default_max_tokens: int = 4096
    supports_async: bool = True
    requires_extra_body: bool = False
    extra_body_params: Optional[Dict[str, Any]] = None

    # Legacy properties (for backward compatibility)
    @property
    def provider(self) -> str:
        """Legacy: Return provider_id"""
        return self.provider_id

    @property
    def env_key(self) -> str:
        """Legacy: Get env_key from ProviderRegistry"""
        try:
            from .provider_registry import ProviderRegistry
            registry = ProviderRegistry()
            provider = registry.get_provider(self.provider_id)
            return provider.api_key_env if provider else ""
        except Exception:
            # Fallback for legacy code that doesn't have ProviderRegistry
            return self._get_legacy_env_key()

    @property
    def api_base(self) -> str:
        """Legacy: Get base_url from ProviderRegistry"""
        try:
            from .provider_registry import ProviderRegistry
            registry = ProviderRegistry()
            provider = registry.get_provider(self.provider_id)
            return provider.base_url if provider else ""
        except Exception:
            # Fallback for legacy code
            return self._get_legacy_api_base()

    def _get_legacy_env_key(self) -> str:
        """Fallback env_key mapping for legacy code"""
        legacy_map = {
            "zhipu": "GLM_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "modelscope": "MODELSCOPE_TOKEN",
            "bytedance": "ARK_API_KEY",
        }
        return legacy_map.get(self.provider_id, "")

    def _get_legacy_api_base(self) -> str:
        """Fallback api_base mapping for legacy code"""
        legacy_map = {
            "zhipu": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com",
            "modelscope": "https://api-inference.modelscope.cn/v1",
            "bytedance": "https://ark.cn-beijing.volces.com/api/v3",
        }
        return legacy_map.get(self.provider_id, "")


# 预定义模型库 (Provider-Aware)
BUILTIN_MODELS: Dict[str, ModelInfo] = {
    # GLM系列
    "glm-4.6v": ModelInfo(
        name="GLM-4.6V",
        provider_id="zhipu",
        default_max_tokens=1000,
        capabilities=[ModelCapability.VISION, ModelCapability.THINKING, ModelCapability.LONG_CONTEXT],
        timeout=60,
    ),

    "glm-4-flash": ModelInfo(
        name="GLM-4 Flash",
        provider_id="zhipu",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.FAST, ModelCapability.BILINGUAL],
        timeout=30,
    ),

    # Doubao系列
    "doubao-vision": ModelInfo(
        name="Doubao Vision",
        provider_id="bytedance",
        default_max_tokens=1000,
        capabilities=[ModelCapability.VISION, ModelCapability.BILINGUAL],
        timeout=300,
    ),

    # DeepSeek系列
    "deepseek-chat": ModelInfo(
        name="DeepSeek Chat",
        provider_id="deepseek",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.LONG_CONTEXT, ModelCapability.FAST],
        timeout=60,
    ),

    "deepseek-reasoner": ModelInfo(
        name="DeepSeek Reasoner (Thinking Mode)",
        provider_id="deepseek",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.THINKING, ModelCapability.LONG_CONTEXT],
        timeout=60,
    ),

    # ModelScope 系列（通过 ModelScope API 访问 DeepSeek V3）
    "deepseek-reasoner-ms": ModelInfo(
        name="DeepSeek V3 (via ModelScope)",
        provider_id="modelscope",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.THINKING, ModelCapability.LONG_CONTEXT],
        timeout=600,
        requires_extra_body=True,
        extra_body_params={"enable_thinking": True},
    ),

    # OpenAI系列（预留）
    "gpt-4o": ModelInfo(
        name="GPT-4o",
        provider_id="openai",
        default_max_tokens=4096,
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION],
        timeout=60,
    ),

    "gpt-4o-mini": ModelInfo(
        name="GPT-4o Mini",
        provider_id="openai",
        default_max_tokens=4096,
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION, ModelCapability.FAST],
        timeout=30,
    ),
}


class ModelRegistry:
    """模型注册表"""

    @staticmethod
    def get_model_info(model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return BUILTIN_MODELS.get(model_id)

    @staticmethod
    def list_models(
        capability: Optional[ModelCapability] = None,
        provider: Optional[str] = None
    ) -> Dict[str, ModelInfo]:
        """
        列出可用模型

        Args:
            capability: 按能力筛选
            provider: 按提供商筛选

        Returns:
            模型字典 {model_id: ModelInfo}
        """
        models = BUILTIN_MODELS.copy()

        if capability:
            models = {
                k: v for k, v in models.items()
                if capability in v.capabilities
            }

        if provider:
            models = {
                k: v for k, v in models.items()
                if v.provider == provider
            }

        return models

    @staticmethod
    def register_custom_model(
        model_id: str,
        model_info: ModelInfo
    ):
        """注册自定义模型"""
        BUILTIN_MODELS[model_id] = model_info

    @staticmethod
    def get_vision_models() -> Dict[str, ModelInfo]:
        """获取所有支持视觉的模型"""
        return ModelRegistry.list_models(capability=ModelCapability.VISION)

    @staticmethod
    def get_text_models() -> Dict[str, ModelInfo]:
        """获取所有支持文本的模型"""
        return ModelRegistry.list_models(capability=ModelCapability.TEXT)

    @staticmethod
    def get_thinking_models() -> Dict[str, ModelInfo]:
        """获取所有支持思维链的模型"""
        return ModelRegistry.list_models(capability=ModelCapability.THINKING)
