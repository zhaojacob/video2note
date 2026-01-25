"""
GLM-4.6V client for image analysis
"""
import asyncio
import base64
from typing import Dict, Any, Optional

import aiohttp
import httpx

from utils.logger import get_logger
from config.settings import GLM_CONFIG

logger = get_logger(__name__)


class GLMClient:
    """
    GLM-4.6V API client

    Features:
    - 128k context window
    - Thinking mode for complex reasoning
    - Support for multiple image formats
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
        timeout: int = None
    ):
        """
        Initialize GLM client

        Args:
            api_key: GLM API key
            model: Model name (glm-4.6v, glm-4.6v-flashx, glm-4.6v-flash)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or GLM_CONFIG.get("api_key")
        if not self.api_key:
            raise ValueError("GLM API key is required")

        self.model = model or GLM_CONFIG.get("model", "glm-4.6v")
        self.base_url = base_url or GLM_CONFIG.get("base_url")
        self.timeout = timeout or GLM_CONFIG.get("timeout", 60)
        self.thinking_enabled = GLM_CONFIG.get("thinking_enabled", True)

        logger.info(f"Initialized GLM client: {self.model}")

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

            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }],
                "max_tokens": max_tokens,
            }

            # Add thinking parameter if enabled
            if self.thinking_enabled:
                payload["thinking"] = {"type": "enabled"}

            # Make request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

            # Parse response
            content = result["choices"][0]["message"]["content"]

            return {
                "description": content,
                "text_content": self._extract_text(content),
                "key_points": self._extract_points(content),
                "model": self.model,
                "usage": result.get("usage", {}),
            }

        except httpx.HTTPError as e:
            logger.error(f"GLM API error: {e}")
            raise
        except Exception as e:
            logger.error(f"GLM analysis failed: {e}")
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
        return asyncio.run(self.analyze_async(image_path, prompt, max_tokens))

    async def analyze_batch_async(
        self,
        image_paths: list[str],
        prompt: str,
        max_tokens: int = 1000,
        max_concurrent: int = 5
    ) -> list[Dict[str, Any]]:
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
        image_paths: list[str],
        prompt: str,
        max_tokens: int = 1000,
        max_concurrent: int = 5
    ) -> list[Dict[str, Any]]:
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
        # Simple extraction - can be improved with better parsing
        lines = content.split('\n')
        text_lines = [line.strip() for line in lines if line.strip()]

        # Try to identify code blocks, formulas, etc.
        text = '\n'.join(text_lines)
        return text[:1000]  # Limit to 1000 chars

    def _extract_points(self, content: str) -> list[str]:
        """Extract key points from analysis"""
        points = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered lists
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                points.append(line.lstrip('-•*123456789. '))

        return points[:10]  # Limit to 10 points

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model": self.model,
            "thinking_enabled": self.thinking_enabled,
            "timeout": self.timeout,
        }
