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
    """模型信息"""
    name: str  # 模型显示名称
    provider: str  # 提供商
    api_base: str  # API base URL
    default_max_tokens: int  # 默认最大tokens
    capabilities: List[ModelCapability]  # 能力列表
    env_key: str  # 环境变量key
    timeout: int = 60
    supports_async: bool = True
    requires_extra_body: bool = False
    extra_body_params: Optional[Dict[str, Any]] = None


# 预定义模型库
BUILTIN_MODELS: Dict[str, ModelInfo] = {
    # GLM系列
    "glm-4.6v": ModelInfo(
        name="GLM-4.6V",
        provider="zhipu",
        api_base="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        default_max_tokens=1000,
        capabilities=[ModelCapability.VISION, ModelCapability.THINKING, ModelCapability.LONG_CONTEXT],
        env_key="GLM_API_KEY",
        timeout=60,
    ),

    "glm-4-flash": ModelInfo(
        name="GLM-4 Flash",
        provider="zhipu",
        api_base="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.FAST, ModelCapability.BILINGUAL],
        env_key="GLM_API_KEY",
        timeout=30,
    ),

    # Doubao系列
    "doubao-vision": ModelInfo(
        name="Doubao Vision",
        provider="bytedance",
        api_base="https://ark.cn-beijing.volces.com/api/v3",
        default_max_tokens=1000,
        capabilities=[ModelCapability.VISION, ModelCapability.BILINGUAL],
        env_key="ARK_API_KEY",
        timeout=300,
    ),

    # DeepSeek系列
    "deepseek-chat": ModelInfo(
        name="DeepSeek Chat",
        provider="deepseek",
        api_base="https://api.deepseek.com",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.LONG_CONTEXT, ModelCapability.FAST],
        env_key="DEEPSEEK_API_KEY",
        timeout=60,
    ),

    "deepseek-v3": ModelInfo(
        name="DeepSeek V3 (via ModelScope)",
        provider="modelscope",
        api_base="https://api-inference.modelscope.cn/v1",
        default_max_tokens=8192,
        capabilities=[ModelCapability.TEXT, ModelCapability.THINKING, ModelCapability.LONG_CONTEXT],
        env_key="MODELSCOPE_TOKEN",
        timeout=600,
        requires_extra_body=True,
        extra_body_params={"enable_thinking": True},
    ),

    # OpenAI系列（预留）
    "gpt-4o": ModelInfo(
        name="GPT-4o",
        provider="openai",
        api_base="https://api.openai.com/v1",
        default_max_tokens=4096,
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION],
        env_key="OPENAI_API_KEY",
        timeout=60,
    ),

    "gpt-4o-mini": ModelInfo(
        name="GPT-4o Mini",
        provider="openai",
        api_base="https://api.openai.com/v1",
        default_max_tokens=4096,
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION, ModelCapability.FAST],
        env_key="OPENAI_API_KEY",
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
