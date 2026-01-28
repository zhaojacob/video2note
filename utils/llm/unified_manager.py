"""
Unified LLM Manager - 统一的LLM客户端管理器 (Provider-First Architecture)

功能：
1. 根据配置自动创建客户端
2. 智能降级策略（Provider级）
3. 健康检查
4. 批处理支持
5. 统一的错误处理

Provider-First API:
    # New API (Recommended)
    client = manager.get_client(provider="zhipu", model="glm-4-flash")

    # Legacy API (Still supported)
    client = manager.get_client("glm-4-flash")
"""
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from .base_client import BaseLLMClient
from .model_registry import ModelRegistry, ModelCapability
from .provider_registry import ProviderRegistry
from utils.llm_client import LLMClient
from .doubao_vision_client import DoubaoVisionClient
from utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedLLMManager:
    """
    统一的LLM管理器 (Provider-First Architecture)

    示例用法：
    ```python
    # 方式1：Provider-First API (推荐)
    manager = UnifiedLLMManager()
    client = manager.get_client(provider="zhipu", model="glm-4-flash")

    # 方式2：Legacy API (向后兼容)
    manager = UnifiedLLMManager()
    client = manager.get_client("glm-4-flash")

    # 方式3：自定义配置
    manager = UnifiedLLMManager()
    client = manager.create_client(
        model="custom-model",
        api_key="xxx",
        base_url="https://api.example.com/v1"
    )

    # 方式4：Provider级降级策略
    manager = UnifiedLLMManager()
    result = manager.chat_with_fallback(
        messages=[...],
        providers=["zhipu", "deepseek", "openai"]
    )
    ```
    """

    def __init__(self):
        self._clients: Dict[str, BaseLLMClient] = {}
        self._model_registry = ModelRegistry()
        self._provider_registry = ProviderRegistry()

    def get_client(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Optional[BaseLLMClient]:
        """
        获取或创建LLM客户端 (Provider-First API)

        New API (Recommended):
            client = manager.get_client(provider="zhipu", model="glm-4-flash")

        Legacy API (Still supported):
            client = manager.get_client("glm-4-flash")

        Args:
            model: Model name (e.g., "glm-4-flash")
            provider: Provider ID (e.g., "zhipu", "openai")
            model_id: Legacy parameter - model identifier (deprecated, use model instead)
            force_refresh: Force refresh client

        Returns:
            LLM客户端实例或None
        """
        # Handle legacy parameter
        if model_id and not model:
            model = model_id

        # Legacy mode: only model provided
        if model and not provider:
            model_info = self._model_registry.get_model_info(model)
            if model_info:
                provider = model_info.provider_id
            else:
                # Try to find any provider that offers this model
                providers = self._provider_registry.get_providers_for_model(model)
                if providers:
                    provider = providers[0].id
                    logger.info(f"Auto-selected provider '{provider}' for model '{model}'")

        if not model or not provider:
            logger.error("必须指定model（可选择性指定provider）")
            return None

        # Cache key: "provider:model"
        cache_key = f"{provider}:{model}"

        # Check cache
        if not force_refresh and cache_key in self._clients:
            return self._clients[cache_key]

        # Get ProviderInfo
        provider_info = self._provider_registry.get_provider(provider)
        if not provider_info:
            logger.error(f"Provider不存在: {provider}")
            return None

        # Verify model
        if not provider_info.has_model(model):
            logger.warning(
                f"模型{model}不在provider {provider}的模型列表中，尝试使用..."
            )

        # Get API key
        api_key = provider_info.get_api_key()
        if not api_key:
            logger.warning(
                f"Provider {provider}的API密钥未配置: {provider_info.api_key_env}"
            )
            return None

        # Get real model name (handle aliases)
        real_model = provider_info.get_real_model_name(model)

        # Create client
        try:
            # Check if provider uses special responses API (Doubao)
            if provider_info.use_responses_api:
                logger.info(f"Using DoubaoVisionClient for {provider}:{model}")
                client = DoubaoVisionClient(
                    api_key=api_key,
                    base_url=provider_info.base_url,
                    model=real_model,
                    timeout=provider_info.timeout,
                    max_retries=3,
                    default_max_tokens=provider_info.default_max_tokens
                )
            else:
                # Standard OpenAI-compatible client
                client = LLMClient(
                    model=real_model,  # Use real model name for API calls
                    api_key=api_key,
                    base_url=provider_info.base_url,
                    timeout=provider_info.timeout,
                    default_max_tokens=provider_info.default_max_tokens,
                    extra_body=provider_info.extra_body_params if provider_info.requires_extra_body else None,
                )

            if client.is_available():
                self._clients[cache_key] = client
                logger.info(f"Created client for {provider}:{model} (real_model={real_model})")
                return client
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to create client for {provider}:{model}: {e}")
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
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Provider-level fallback strategy

        依次尝试每个provider，直到成功

        Args:
            messages: 对话消息
            providers: Provider列表（按优先级）
            model: 可选模型名称（仅用于支持该模型的provider）
            **kwargs: 其他参数

        Returns:
            生成的内容或None（全部失败时）

        Example:
            result = manager.chat_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
                providers=["zhipu", "deepseek", "openai"],
                model="glm-4-flash"  # Optional, only used for zhipu
            )
        """
        for provider_id in providers:
            provider_info = self._provider_registry.get_provider(provider_id)
            if not provider_info:
                logger.warning(f"Provider {provider_id} not found, trying next...")
                continue

            # Determine which model to use
            use_model = model
            if not use_model and provider_info.models:
                use_model = provider_info.models[0]  # Use provider's default model

            if not use_model:
                logger.warning(f"No model available for provider {provider_id}")
                continue

            client = self.get_client(provider=provider_id, model=use_model)
            if not client or not client.is_available():
                logger.warning(f"Provider {provider_id} not available, trying next...")
                continue

            try:
                result = client.chat_completion(messages, **kwargs)
                if result:
                    logger.info(f"Successfully used {provider_id}:{use_model}")
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider_id} failed: {e}, trying next...")

        logger.error("All providers failed")
        return None

    def analyze_image_with_fallback(
        self,
        image_path: Union[str, Path],
        prompt: str,
        providers: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Provider-level fallback for image analysis

        Args:
            image_path: Path to image
            prompt: Analysis prompt
            providers: List of provider IDs to try (in priority order)
            model: Optional model name
            **kwargs: Other parameters
        """
        for provider_id in providers:
            provider_info = self._provider_registry.get_provider(provider_id)
            if not provider_info:
                continue

            # Determine which model to use
            use_model = model
            if not use_model and provider_info.models:
                use_model = provider_info.models[0]

            if not use_model:
                continue

            client = self.get_client(provider=provider_id, model=use_model)
            if not client or not client.is_available():
                continue

            try:
                result = client.analyze_image(image_path, prompt, **kwargs)
                if result:
                    logger.info(f"Image analysis succeeded with {provider_id}:{use_model}")
                    return result
            except NotImplementedError:
                logger.warning(f"{provider_id} does not support image analysis")
                continue
            except Exception as e:
                logger.warning(f"{provider_id} image analysis failed: {e}")
                continue

        logger.error("All image analysis providers failed")
        return None

    def batch_chat(
        self,
        messages_list: List[List[Dict[str, str]]],
        provider: str,
        model: Optional[str] = None,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Optional[str]]:
        """
        批量聊天补全（异步并发）

        Args:
            messages_list: 消息列表的列表
            provider: 使用的provider ID
            model: 可选模型名称
            max_concurrent: 最大并发数
            **kwargs: 其他参数

        Returns:
            结果列表
        """
        # Get provider info to determine default model if needed
        provider_info = self._provider_registry.get_provider(provider)
        if not provider_info:
            logger.error(f"Provider not found: {provider}")
            return [None] * len(messages_list)

        use_model = model
        if not use_model and provider_info.models:
            use_model = provider_info.models[0]

        if not use_model:
            logger.error(f"No model available for provider {provider}")
            return [None] * len(messages_list)

        async def _batch_async():
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_one(messages):
                async with semaphore:
                    client = self.get_client(provider=provider, model=use_model)
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
        all_models = self._model_registry.list_models(capability=capability)
        available = {}

        for model_id, info in all_models.items():
            provider_info = self._provider_registry.get_provider(info.provider_id)
            if provider_info and provider_info.get_api_key():
                available[model_id] = {
                    "name": info.name,
                    "provider": info.provider_id,
                    "capabilities": [c.value for c in info.capabilities],
                }

        return available

    def list_available_providers(
        self,
        capability: Optional[ModelCapability] = None
    ) -> Dict[str, Any]:
        """
        列出当前可用的providers（已配置API key）

        Args:
            capability: 按能力筛选

        Returns:
            {provider_id: provider_info}
        """
        from .provider_registry import ProviderCapability

        all_providers = self._provider_registry.list_providers()

        # Convert ModelCapability to ProviderCapability if needed
        filter_cap = None
        if capability:
            cap_map = {
                ModelCapability.TEXT: ProviderCapability.TEXT,
                ModelCapability.VISION: ProviderCapability.VISION,
                ModelCapability.THINKING: ProviderCapability.THINKING,
                ModelCapability.LONG_CONTEXT: ProviderCapability.LONG_CONTEXT,
                ModelCapability.BILINGUAL: ProviderCapability.BILINGUAL,
                ModelCapability.FAST: ProviderCapability.FAST,
            }
            filter_cap = cap_map.get(capability)

        if filter_cap:
            all_providers = self._provider_registry.list_providers(capability=filter_cap)

        available = {}
        for provider_id, info in all_providers.items():
            if info.get_api_key():
                available[provider_id] = {
                    "name": info.name,
                    "models": info.models,
                    "capabilities": [c.value for c in info.capabilities],
                }

        return available

    def health_check(self, model: Optional[str] = None, provider: Optional[str] = None) -> bool:
        """
        检查模型健康状态

        Args:
            model: 模型名称
            provider: Provider ID

        Returns:
            是否健康
        """
        client = self.get_client(model=model, provider=provider, force_refresh=True)
        return client is not None and client.is_available()
