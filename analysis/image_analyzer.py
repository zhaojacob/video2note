"""
Unified image analyzer with smart API selection

Now uses UnifiedLLMManager for flexible model selection and fallback strategies.

Legacy clients (GLMClient, DoubaoClient) are imported from the same directory
for backward compatibility. New code should use UnifiedLLMManager directly.
"""
import asyncio
import random
from typing import Dict, Any, List, Optional

# Legacy clients (kept for backward compatibility)
from analysis.glm_client import GLMClient
from analysis.doubao_client import DoubaoClient

# New unified manager
from utils.llm.unified_manager import UnifiedLLMManager

from config.prompt_templates import PROMPTS
from config.settings import API_ALLOCATION_CONFIG
from config.llm_config import get_recommended_models, get_fallback_chain
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageAnalyzer:
    """
    Unified image analyzer with intelligent API selection

    Strategy:
    - Formula/Code: GLM-4.6V (STEM strength)
    - Chinese text: Doubao (Chinese understanding)
    - General: 70% GLM, 30% Doubao (load balancing)
    - Fallback: Auto-switch on failure

    New: Can use UnifiedLLMManager for flexible model selection
    """

    def __init__(
        self,
        glm_config: Optional[Dict] = None,
        doubao_config: Optional[Dict] = None,
        allocation_config: Optional[Dict] = None,
        use_unified_manager: bool = False
    ):
        """
        Initialize image analyzer

        Args:
            glm_config: GLM client configuration
            doubao_config: Doubao client configuration
            allocation_config: API allocation strategy
            use_unified_manager: Use new UnifiedLLMManager (recommended)
        """
        self.use_unified_manager = use_unified_manager
        self.allocation_config = allocation_config or API_ALLOCATION_CONFIG

        if use_unified_manager:
            # New implementation using UnifiedLLMManager
            self.manager = UnifiedLLMManager()
            self.glm_client = None
            self.doubao_client = None

            # Get task-specific recommendations
            self.vision_formula = get_recommended_models("vision_formula")
            self.vision_code = get_recommended_models("vision_code")
            self.vision_chinese = get_recommended_models("vision_chinese")
            self.vision_general = get_recommended_models("vision_general")

            logger.info("Initialized image analyzer with UnifiedLLMManager")
        else:
            # Legacy implementation (backward compatible)
            # Try to initialize GLM client (optional)
            self.glm_client = None
            try:
                self.glm_client = GLMClient(**(glm_config or {}))
                logger.info("GLM client initialized")
            except ValueError as e:
                logger.warning(f"GLM client not available: {e}")
                logger.info("Will use Doubao client only")

            # Initialize Doubao client (required)
            self.doubao_client = DoubaoClient(**(doubao_config or {}))
            self.manager = None

            if self.glm_client:
                logger.info("Initialized image analyzer with GLM + Doubao (legacy)")
            else:
                logger.info("Initialized image analyzer with Doubao only (legacy)")

    def _select_api(
        self,
        frame: Dict[str, Any],
        analysis_type: str = "auto"
    ) -> str:
        """
        Select appropriate API for analysis

        Args:
            frame: Frame data with content_type
            analysis_type: Analysis type (auto/formula/code/chart/text/slide/general)

        Returns:
            API name: 'glm' or 'doubao' (legacy) or model_id list (unified)
        """
        if self.use_unified_manager:
            # New implementation - return model ID list for fallback
            content_type = frame.get("content_type", {})

            # Explicit analysis type
            if analysis_type in ["formula", "code"]:
                return self.vision_formula["fallback"]
            elif analysis_type == "chart":
                return self.vision_code["fallback"]
            elif analysis_type in ["text", "slide"]:
                return self.vision_chinese["fallback"]

            # Auto-detect based on content
            if content_type.get("has_formula") or content_type.get("has_code"):
                return self.vision_formula["fallback"]

            if content_type.get("has_text"):
                text = content_type.get("text_content", "")
                if self._is_chinese_dominant(text):
                    return self.vision_chinese["fallback"]

            if content_type.get("has_chart"):
                return self.vision_code["fallback"]

            # Default: use general vision fallback
            return self.vision_general["fallback"]
        else:
            # Legacy implementation
            # If GLM is not available, always use Doubao
            if self.glm_client is None:
                logger.debug("GLM not available, using Doubao")
                return "doubao"

            # Explicit analysis type
            if analysis_type in ["formula", "code", "chart"]:
                return "glm"
            elif analysis_type in ["text", "slide"]:
                return "doubao"

            # Auto-detect based on content
            content_type = frame.get("content_type", {})

            # Formula or code detection
            if content_type.get("has_formula") or content_type.get("has_code"):
                return "glm"

            # Text detection with Chinese
            if content_type.get("has_text"):
                text = content_type.get("text_content", "")
                if self._is_chinese_dominant(text):
                    return "doubao"

            # Chart detection - GLM is better at detailed analysis
            if content_type.get("has_chart"):
                return "glm"

            # Default: load balancing
            glm_ratio = self.allocation_config.get("glm_ratio", 0.7)
            return "glm" if random.random() < glm_ratio else "doubao"

    def _is_chinese_dominant(self, text: str) -> bool:
        """Check if text is predominantly Chinese"""
        if not text:
            return False

        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text.replace(' ', ''))

        if total_chars == 0:
            return False

        chinese_ratio = chinese_chars / total_chars
        return chinese_ratio > 0.3  # 30% threshold

    async def analyze_single_async(
        self,
        frame: Dict[str, Any],
        api: str = None,
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Analyze a single frame asynchronously

        Args:
            frame: Frame data dictionary
            api: API to use (glm/doubao), auto-select if None
            analysis_type: Type of analysis

        Returns:
            Analysis result dictionary
        """
        # Select API
        if api is None:
            api = self._select_api(frame, analysis_type)

        # Get prompt
        prompt = PROMPTS.get(analysis_type, PROMPTS["auto"])

        logger.debug(f"Analyzing {frame['path']} with {api} ({analysis_type})")

        result = {
            "frame_path": frame["path"],
            "timestamp": frame.get("timestamp", 0),
            "api_used": api if isinstance(api, str) else api[0] if isinstance(api, list) else "unknown",
            "analysis_type": analysis_type,
        }

        if self.use_unified_manager:
            # New implementation using UnifiedLLMManager
            providers = api if isinstance(api, list) else [api]
            result["api_used"] = providers[0]

            try:
                analysis = self.manager.analyze_image_with_fallback(
                    image_path=frame["path"],
                    prompt=prompt,
                    providers=providers,
                    max_tokens=1000
                )

                if analysis:
                    result.update(analysis)
                    result["success"] = True
                else:
                    result["success"] = False
                    result["error"] = "All providers failed"

            except Exception as e:
                logger.error(f"Analysis failed with unified manager: {e}")
                result["success"] = False
                result["error"] = str(e)
        else:
            # Legacy implementation
            try:
                if api == "glm":
                    if self.glm_client is None:
                        # GLM was selected but not available, fallback to Doubao
                        logger.warning("GLM selected but not available, using Doubao instead")
                        api = "doubao"
                    analysis = await self.glm_client.analyze_async(
                        frame["path"],
                        prompt,
                        max_tokens=1000
                    )
                else:
                    analysis = await self.doubao_client.analyze_async(
                        frame["path"],
                        prompt,
                        max_tokens=1000
                    )

                result.update(analysis)
                result["success"] = True

            except Exception as e:
                logger.error(f"Analysis failed with {api}: {e}")

                # Retry with alternative API if enabled
                if self.allocation_config.get("retry_with_alternative", True):
                    alternative_api = "doubao" if api == "glm" else "glm"

                    # Skip retry if alternative is GLM but not available
                    if alternative_api == "glm" and self.glm_client is None:
                        logger.warning("Alternative API (GLM) not available, skipping retry")
                        result["success"] = False
                        result["error"] = str(e)
                        return result

                    logger.info(f"Retrying with {alternative_api}")

                    try:
                        if alternative_api == "glm":
                            analysis = await self.glm_client.analyze_async(
                                frame["path"],
                                prompt,
                                max_tokens=1000
                            )
                        else:
                            analysis = await self.doubao_client.analyze_async(
                                frame["path"],
                                prompt,
                                max_tokens=1000
                            )

                        result.update(analysis)
                        result["api_used"] = alternative_api
                        result["success"] = True

                    except Exception as e2:
                        logger.error(f"Alternative API also failed: {e2}")
                        result["success"] = False
                        result["error"] = str(e2)
                else:
                    result["success"] = False
                    result["error"] = str(e)

        return result

    def analyze_single(
        self,
        frame: Dict[str, Any],
        api: str = None,
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """Analyze a single frame (synchronous wrapper)"""
        return asyncio.run(
            self.analyze_single_async(frame, api, analysis_type)
        )

    async def analyze_batch_async(
        self,
        frames: List[Dict[str, Any]],
        analysis_type: str = "auto",
        max_concurrent: int = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple frames concurrently

        Args:
            frames: List of frame dictionaries
            analysis_type: Type of analysis
            max_concurrent: Maximum concurrent requests

        Returns:
            List of analysis results
        """
        max_concurrent = max_concurrent or self.allocation_config.get(
            "max_concurrent", 5
        )

        logger.info(f"Analyzing {len(frames)} frames (max concurrent: {max_concurrent})")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(frame):
            async with semaphore:
                return await self.analyze_single_async(frame, analysis_type=analysis_type)

        tasks = [analyze_with_semaphore(frame) for frame in frames]
        results = await asyncio.gather(*tasks)

        # Log statistics
        success_count = sum(1 for r in results if r.get("success"))
        glm_count = sum(1 for r in results if r.get("api_used") == "glm")
        doubao_count = sum(1 for r in results if r.get("api_used") == "doubao")

        logger.info(f"Analysis complete: {success_count}/{len(results)} successful")
        logger.info(f"API usage: GLM={glm_count}, Doubao={doubao_count}")

        return results

    def analyze_batch(
        self,
        frames: List[Dict[str, Any]],
        analysis_type: str = "auto",
        max_concurrent: int = None
    ) -> List[Dict[str, Any]]:
        """Analyze multiple frames (synchronous wrapper)"""
        return asyncio.run(
            self.analyze_batch_async(frames, analysis_type, max_concurrent)
        )

    def classify_frame(self, frame_path: str) -> Dict[str, Any]:
        """
        Classify frame content type

        Args:
            frame_path: Path to frame image

        Returns:
            Classification result
        """
        from core.frame_extractor import FrameExtractor

        extractor = FrameExtractor()
        return extractor.detect_special_content(frame_path)
