"""
Unified LLM Manager - 统一的LLM客户端管理器

功能：
1. 根据配置自动创建客户端
2. 智能降级策略
3. 健康检查
4. 批处理支持
5. 统一的错误处理
"""
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from .base_client import BaseLLMClient
from .model_registry import ModelRegistry, ModelCapability
from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedLLMManager:
    """
    统一的LLM管理器

    示例用法：
    ```python
    # 方式1：使用预定义模型
    manager = UnifiedLLMManager()
    client = manager.get_client("glm-4-flash")

    # 方式2：使用自定义配置
    manager = UnifiedLLMManager()
    client = manager.create_client(
        model="custom-model",
        api_key="xxx",
        base_url="https://api.example.com/v1"
    )

    # 方式3：带降级策略
    manager = UnifiedLLMManager()
    result = manager.chat_with_fallback(
        messages=[...],
        providers=["glm-4-flash", "deepseek-chat", "gpt-4o-mini"]
    )
    ```
    """

    def __init__(self):
        self._clients: Dict[str, BaseLLMClient] = {}
        self._registry = ModelRegistry()

    def get_client(
        self,
        model_id: str,
        force_refresh: bool = False
    ) -> Optional[BaseLLMClient]:
        """
        获取或创建LLM客户端

        Args:
            model_id: 模型ID（如 "glm-4-flash"）
            force_refresh: 强制刷新客户端

        Returns:
            LLM客户端实例或None
        """
        # 检查缓存
        if not force_refresh and model_id in self._clients:
            return self._clients[model_id]

        # 获取模型信息
        model_info = self._registry.get_model_info(model_id)
        if not model_info:
            logger.error(f"Unknown model: {model_id}")
            return None

        # 读取API key
        import os
        api_key = os.getenv(model_info.env_key)
        if not api_key:
            logger.warning(
                f"API key not found for {model_id}. "
                f"Set environment variable: {model_info.env_key}"
            )
            return None

        # 创建客户端
        try:
            client = LLMClient(
                model=model_id,
                api_key=api_key,
                base_url=model_info.api_base,
                timeout=model_info.timeout,
                default_max_tokens=model_info.default_max_tokens,
                extra_body=model_info.extra_body_params if model_info.requires_extra_body else None,
            )

            if client.is_available():
                self._clients[model_id] = client
                logger.info(f"Created client for {model_id}")
                return client
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to create client for {model_id}: {e}")
            return None

    def create_client(
        self,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs
    ) -> Optional[BaseLLMClient]:
        """
        创建自定义客户端

        Args:
            model: 模型名称
            api_key: API密钥
            base_url: API base URL
            **kwargs: 其他参数

        Returns:
            LLM客户端实例
        """
        try:
            client = LLMClient(
                model=model,
                api_key=api_key,
                base_url=base_url,
                **kwargs
            )

            if client.is_available():
                # 使用model名称作为缓存key
                cache_key = f"custom_{model}"
                self._clients[cache_key] = client
                return client
            return None

        except Exception as e:
            logger.error(f"Failed to create custom client: {e}")
            return None

    def chat_with_fallback(
        self,
        messages: List[Dict[str, str]],
        providers: List[str],
        **kwargs
    ) -> Optional[str]:
        """
        带降级策略的聊天补全

        依次尝试每个provider，直到成功

        Args:
            messages: 对话消息
            providers: provider列表（按优先级）
            **kwargs: 其他参数

        Returns:
            生成的内容或None（全部失败时）
        """
        for provider in providers:
            client = self.get_client(provider)
            if not client or not client.is_available():
                logger.warning(f"Provider {provider} not available, trying next...")
                continue

            try:
                result = client.chat_completion(messages, **kwargs)
                if result:
                    logger.info(f"Successfully used {provider}")
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}, trying next...")

        logger.error("All providers failed")
        return None

    def analyze_image_with_fallback(
        self,
        image_path: Union[str, Path],
        prompt: str,
        providers: List[str],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        带降级策略的图像分析
        """
        for provider in providers:
            client = self.get_client(provider)
            if not client or not client.is_available():
                continue

            try:
                result = client.analyze_image(image_path, prompt, **kwargs)
                if result:
                    logger.info(f"Image analysis succeeded with {provider}")
                    return result
            except NotImplementedError:
                logger.warning(f"{provider} does not support image analysis")
                continue
            except Exception as e:
                logger.warning(f"{provider} image analysis failed: {e}")
                continue

        logger.error("All image analysis providers failed")
        return None

    def batch_chat(
        self,
        messages_list: List[List[Dict[str, str]]],
        provider: str,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Optional[str]]:
        """
        批量聊天补全（异步并发）

        Args:
            messages_list: 消息列表的列表
            provider: 使用的provider
            max_concurrent: 最大并发数
            **kwargs: 其他参数

        Returns:
            结果列表
        """
        async def _batch_async():
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_one(messages):
                async with semaphore:
                    client = self.get_client(provider)
                    if not client:
                        return None
                    return await client.chat_completion_async(messages, **kwargs)

            tasks = [process_one(msgs) for msgs in messages_list]
            return await asyncio.gather(*tasks, return_exceptions=True)

        return asyncio.run(_batch_async())

    def list_available_models(
        self,
        capability: Optional[ModelCapability] = None
    ) -> Dict[str, Any]:
        """
        列出当前可用的模型（已配置API key）

        Args:
            capability: 按能力筛选

        Returns:
            {model_id: model_info}
        """
        import os

        all_models = self._registry.list_models(capability=capability)
        available = {}

        for model_id, info in all_models.items():
            api_key = os.getenv(info.env_key)
            if api_key:
                available[model_id] = {
                    "name": info.name,
                    "provider": info.provider,
                    "capabilities": [c.value for c in info.capabilities],
                }

        return available

    def health_check(self, model_id: str) -> bool:
        """
        检查模型健康状态

        Args:
            model_id: 模型ID

        Returns:
            是否健康
        """
        client = self.get_client(model_id, force_refresh=True)
        return client is not None and client.is_available()
