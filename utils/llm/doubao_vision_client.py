"""
Doubao Vision Client - 豆包视觉模型专用客户端

豆包使用特殊的 API 格式:
- 使用 client.responses.create() 而不是 client.chat.completions.create()
- 使用 input 参数而不是 messages
- 图像格式使用 input_image 和 input_text

官方文档: https://www.volcengine.com/docs/82379/1399008
"""
import logging
import time
import base64
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError, AuthenticationError, APIConnectionError
from utils.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class DoubaoVisionClient(BaseLLMClient):
    """
    豆包视觉模型专用客户端
    
    使用豆包特有的 responses.create() API
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 300.0,
        max_retries: int = 3,
        default_max_tokens: int = 1000
    ):
        """
        Initialize Doubao Vision client
        
        Args:
            api_key: ARK API Key
            base_url: Base URL (https://ark.cn-beijing.volces.com/api/v3)
            model: Model ID (doubao-seed-1-6-vision-250815)
            timeout: Request timeout
            max_retries: Max retries
            default_max_tokens: Default max tokens
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.default_max_tokens = default_max_tokens
        
        if not self.api_key:
            logger.warning(f"API key not provided for Doubao model {model}")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=timeout,
                max_retries=max_retries
            )
            logger.info(f"DoubaoVisionClient initialized: model={self.model}")
    
    def is_available(self) -> bool:
        """Check if client is available"""
        return self.client is not None
    
    def analyze_image(
        self,
        image_path: Union[str, Path],
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze image using Doubao vision model
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with analysis results
        """
        if not self.client:
            logger.error("Doubao client not initialized")
            return None
        
        try:
            # Encode image to base64
            image_base64 = self._encode_image(image_path)
            
            # Prepare request using Doubao format
            # 注意: 豆包使用 responses.create() 和 input 参数
            params = {
                "model": self.model,
                "input": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_base64}"
                        },
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }]
            }
            
            logger.info(f"Analyzing image {image_path} with Doubao model {self.model}")
            print(f"\n[DEBUG] Doubao Request:")
            print(f"  Model: {self.model}")
            print(f"  Prompt: {prompt[:100]}...")
            print("-" * 60)
            
            # 使用 responses.create() API
            try:
                response = self.client.responses.create(**params)
            except AttributeError as e:
                # 如果 responses.create() 方法不存在，降级到标准 API
                logger.warning(f"Doubao responses.create() method not available: {e}")
                return self._analyze_image_standard(image_path, prompt, max_tokens)
            
            # Parse response
            # 豆包返回的是列表格式: [ResponseReasoningItem, ResponseOutputMessage]
            content = None
            
            if isinstance(response, list):
                # 处理列表格式的响应
                for item in response:
                    # 查找 ResponseOutputMessage
                    if hasattr(item, 'content') and item.content:
                        # content 是一个列表，包含 ResponseOutputText
                        if isinstance(item.content, list) and len(item.content) > 0:
                            first_content = item.content[0]
                            if hasattr(first_content, 'text'):
                                content = first_content.text
                                break
            elif hasattr(response, 'choices') and response.choices:
                # 标准 OpenAI 格式
                content = response.choices[0].message.content
            elif hasattr(response, 'output'):
                # 其他格式
                content = response.output
            
            if not content:
                # 如果无法解析，转换为字符串
                content = str(response)
            
            # 确保 content 是字符串
            if isinstance(content, list):
                # 如果是列表，尝试提取文本
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                content = " ".join(text_parts) if text_parts else str(content)
            
            logger.info(f"Doubao analysis success: {len(content)} chars")
            print(f"\n[DEBUG] Doubao Response:")
            print(content)
            print("-" * 60)
            
            return {
                "description": content,
                "text_content": self._extract_text_content(content),
                "key_points": self._extract_key_points(content),
                "model": self.model,
            }
            
        except Exception as e:
            logger.error(f"Doubao image analysis failed: {e}")
            print(f"\n[ERROR] Doubao analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _analyze_image_standard(
        self,
        image_path: Union[str, Path],
        prompt: str,
        max_tokens: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Fallback to standard OpenAI-compatible API
        """
        try:
            image_base64 = self._encode_image(image_path)
            
            params = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }],
                "max_tokens": max_tokens
            }
            
            logger.info("Using standard API format for Doubao")
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            
            return {
                "description": content,
                "text_content": self._extract_text_content(content),
                "key_points": self._extract_key_points(content),
                "model": self.model,
            }
            
        except Exception as e:
            logger.error(f"Standard API also failed: {e}")
            return None
    
    async def analyze_image_async(
        self,
        image_path: Union[str, Path],
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Async version - currently not implemented for Doubao
        Falls back to sync version
        """
        logger.warning("Async not implemented for Doubao, using sync version")
        return self.analyze_image(image_path, prompt, max_tokens, **kwargs)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        retry_count: int = 3,
        stream: bool = False
    ) -> Optional[str]:
        """
        Chat completion - not supported for vision-only model
        """
        logger.error("Chat completion not supported for Doubao vision model")
        return None
    
    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """
        Async chat completion - not supported
        """
        logger.error("Async chat completion not supported for Doubao vision model")
        return None
