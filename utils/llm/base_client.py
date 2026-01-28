"""
Base LLM Client Abstract Class
提供统一的LLM客户端接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class BaseLLMClient(ABC):
    """
    统一的LLM客户端抽象基类

    所有LLM客户端必须实现此接口
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        timeout: float = 60.0,
        max_retries: int = 3,
        **kwargs
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.extra_params = kwargs

    @abstractmethod
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        pass

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> Optional[str]:
        """
        文本聊天补全

        Args:
            messages: 对话消息列表
            max_tokens: 最大生成token数
            temperature: 采样温度

        Returns:
            生成的内容或None（失败时）
        """
        pass

    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> Optional[str]:
        """
        异步文本聊天补全

        默认抛出NotImplementedError，子类可选择实现
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support async chat completion."
        )

    def analyze_image(
        self,
        image_path: Union[str, Path],
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        图像分析（默认实现，子类可重写）

        Args:
            image_path: 图像文件路径
            prompt: 分析提示词
            max_tokens: 最大生成token数

        Returns:
            分析结果字典或None
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support image analysis. "
            "Use a vision-capable model or switch to a different provider."
        )

    async def analyze_image_async(
        self,
        image_path: Union[str, Path],
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """异步图像分析"""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support async image analysis."
        )

    # 工具方法
    @staticmethod
    def _encode_image(image_path: Union[str, Path]) -> str:
        """Base64编码图像"""
        import base64
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def _extract_text_content(result: Union[str, Dict[str, Any]]) -> str:
        """从API响应提取文本内容"""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return result.get("description", "")
        return ""

    @staticmethod
    def _extract_key_points(content: str) -> List[str]:
        """从内容中提取关键点"""
        points = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                points.append(line.lstrip('-•*123456789. '))
        return points[:10]
