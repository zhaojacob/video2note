"""
Doubao Vision client for image analysis (OpenAI-compatible API)
"""
import asyncio
import base64
from typing import Dict, Any, List

from openai import OpenAI
from openai import AsyncOpenAI

from utils.logger import get_logger
from config.settings import DOUBAO_CONFIG

logger = get_logger(__name__)


class DoubaoClient:
    """
    Doubao Vision API client (OpenAI-compatible)

    Features:
    - Strong Chinese text understanding
    - Support for vision models
    - Excellent for document and PPT analysis
    - Uses OpenAI-compatible API format
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
        timeout: int = None
    ):
        """
        Initialize Doubao client

        Args:
            api_key: Doubao API key (ARK_API_KEY)
            model: Model name (e.g., doubao-seed-1-8-251228)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or DOUBAO_CONFIG.get("api_key")
        if not self.api_key:
            raise ValueError("Doubao API key (ARK_API_KEY) is required")

        self.model = model or DOUBAO_CONFIG.get("model", "doubao-seed-1-8-251228")
        self.base_url = base_url or DOUBAO_CONFIG.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
        self.timeout = timeout or DOUBAO_CONFIG.get("timeout", 60)

        # Initialize synchronous client
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        # Initialize asynchronous client
        self.async_client = None

        logger.info(f"Initialized Doubao client: {self.model}")

    def _get_async_client(self) -> AsyncOpenAI:
        """Get or create async client"""
        if self.async_client is None:
            self.async_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        return self.async_client

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_async(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze image asynchronously

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with analysis results
        """
        try:
            # Encode image
            image_base64 = self._encode_image(image_path)

            # Get async client
            client = self._get_async_client()

            # Prepare request using OpenAI format
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        },
                    ],
                }],
                max_tokens=max_tokens,
            )

            # Parse response
            content = response.choices[0].message.content

            return {
                "description": content,
                "text_content": self._extract_text(content),
                "key_points": self._extract_points(content),
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

        except Exception as e:
            logger.error(f"Doubao API error: {e}")
            raise

    def analyze(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze image (synchronous wrapper)

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with analysis results
        """
        try:
            # Encode image
            image_base64 = self._encode_image(image_path)

            # Prepare request using OpenAI format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        },
                    ],
                }],
                max_tokens=max_tokens,
            )

            # Parse response
            content = response.choices[0].message.content

            return {
                "description": content,
                "text_content": self._extract_text(content),
                "key_points": self._extract_points(content),
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

        except Exception as e:
            logger.error(f"Doubao API error: {e}")
            raise

    async def analyze_batch_async(
        self,
        image_paths: List[str],
        prompt: str,
        max_tokens: int = 1000,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images concurrently

        Args:
            image_paths: List of image paths
            prompt: Analysis prompt
            max_tokens: Maximum tokens per response
            max_concurrent: Maximum concurrent requests

        Returns:
            List of analysis results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(image_path):
            async with semaphore:
                return await self.analyze_async(image_path, prompt, max_tokens)

        tasks = [analyze_with_semaphore(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze {image_paths[i]}: {result}")
                processed_results.append({
                    "error": str(result),
                    "image_path": image_paths[i],
                })
            else:
                result["image_path"] = image_paths[i]
                processed_results.append(result)

        return processed_results

    def analyze_batch(
        self,
        image_paths: List[str],
        prompt: str,
        max_tokens: int = 1000,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images (synchronous wrapper)

        Args:
            image_paths: List of image paths
            prompt: Analysis prompt
            max_tokens: Maximum tokens per response
            max_concurrent: Maximum concurrent requests

        Returns:
            List of analysis results
        """
        return asyncio.run(
            self.analyze_batch_async(image_paths, prompt, max_tokens, max_concurrent)
        )

    def _extract_text(self, content: str) -> str:
        """Extract text content from analysis"""
        lines = content.split('\n')
        text_lines = [line.strip() for line in lines if line.strip()]
        text = '\n'.join(text_lines)
        return text[:1000]

    def _extract_points(self, content: str) -> List[str]:
        """Extract key points from analysis"""
        points = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                points.append(line.lstrip('-•*123456789. '))

        return points[:10]

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
        }

    def __del__(self):
        """Cleanup async client on deletion"""
        if self.async_client:
            try:
                asyncio.get_event_loop().run_until_complete(self.async_client.close())
            except:
                pass
