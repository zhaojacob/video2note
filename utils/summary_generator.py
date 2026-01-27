"""
Summary generator using DeepSeek Chat model
"""
import logging
from typing import List, Dict, Any, Optional

from utils.llm_client import LLMClient
from config.settings import TEXT_LLM_PROVIDER, TEXT_LLM_CONFIGS
from config.prompt_templates import STRUCTURE_PROMPTS

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate video summaries using DeepSeek Chat model (128K context, 8K output)"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize summary generator with DeepSeek API

        Args:
            api_key: DeepSeek API key (optional, uses config if not provided)
        """
        provider = TEXT_LLM_PROVIDER
        config = TEXT_LLM_CONFIGS.get(provider, TEXT_LLM_CONFIGS.get("modelscope", {}))

        self.provider = provider
        self.api_key = api_key or config.get("api_key")
        self.base_url = config.get("base_url")
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens", 8192)
        self.extra_body = config.get("extra_body")

        if not self.api_key:
            logger.warning("Text LLM API key not found. Summary generation will be disabled.")
            self.client = None
        else:
            self.client = LLMClient(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                default_max_tokens=self.max_tokens,
                extra_body=self.extra_body
            )
            logger.info(f"SummaryGenerator initialized: provider={self.provider}, model={self.model}, max_tokens={self.max_tokens}")

    def is_available(self) -> bool:
        """Check if generator is available"""
        return self.client is not None

    def _call_text_llm(self, messages: List[Dict[str, str]],
                       max_tokens: Optional[int] = None,
                       temperature: float = 0.7) -> Optional[str]:
        """
        Call text LLM with detailed error reporting (using LLMClient)

        Args:
            messages: Conversation messages
            max_tokens: Max tokens for response
            temperature: Sampling temperature

        Returns:
            Response content string, or None if failed
        """
        if not self.client:
            logger.error("Text LLM client not initialized")
            return None

        # Use LLMClient's chat_completion method with built-in error handling and retries
        content = self.client.chat_completion(
            messages=messages,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature,
            retry_count=2
        )

        return content

    def generate_summary(
        self,
        transcript_text: str,
        video_title: str = "",
        video_duration: float = 0,
        max_length: int = 500,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a summary from transcript text

        Args:
            transcript_text: Full transcript text (polished or raw)
            video_title: Video title for context
            video_duration: Video duration in minutes (for calculating summary length)
            max_length: Maximum summary length in characters (deprecated, kept for compatibility)
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature

        Returns:
            Generated summary string
        """
        if not self.client:
            logger.warning("DeepSeek client not initialized, returning empty summary")
            return ""

        if not transcript_text or len(transcript_text.strip()) < 50:
            logger.warning("Transcript too short for summary generation")
            return ""

        # Truncate very long transcripts to fit context window
        max_input_chars = 30000  # Increased for thinking mode
        if len(transcript_text) > max_input_chars:
            transcript_text = transcript_text[:max_input_chars] + "..."
            logger.info(f"Transcript truncated to {max_input_chars} characters")

        # Calculate summary length based on video duration (duration * 25)
        summary_length = int(video_duration * 25) if video_duration > 0 else 250
        logger.info(f"Video duration: {video_duration:.1f}min, target summary length: {summary_length} chars")

        prompt = STRUCTURE_PROMPTS["summarize"].format(
            video_title=video_title or "Untitled",
            video_duration=f"{video_duration:.1f}",
            transcript=transcript_text,
            summary_length=summary_length
        )

        messages = [{"role": "user", "content": prompt}]

        logger.info(f"Generating summary with text LLM ({self.provider})...")
        content = self._call_text_llm(messages, max_tokens=max_tokens or 4096, temperature=temperature)

        if not content:
            logger.warning("Empty response from DeepSeek")
            return ""

        summary = content.strip()

        # Remove common prefixes if present
        prefixes_to_remove = ["摘要：", "摘要:", "Summary:", "总结：", "总结:"]
        for prefix in prefixes_to_remove:
            if summary.startswith(prefix):
                summary = summary[len(prefix):].strip()

        logger.info(f"Summary generated successfully ({len(summary)} chars)")
        return summary

    def generate_keywords(
        self,
        transcript_text: str,
        max_keywords: int = 10
    ) -> List[str]:
        """
        Extract keywords from transcript
        
        Args:
            transcript_text: Full transcript text
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
        """
        if not self.client:
            return []
        
        if not transcript_text or len(transcript_text.strip()) < 50:
            return []
        
        # Truncate for keyword extraction
        max_input_chars = 15000
        if len(transcript_text) > max_input_chars:
            transcript_text = transcript_text[:max_input_chars]
        
        prompt = f"""请从以下文本中提取{max_keywords}个最重要的关键词或短语。

文本内容：
{transcript_text}

要求：
1. 关键词应该代表文本的核心主题和概念
2. 优先选择专有名词、技术术语、人名、地名等
3. 每个关键词用逗号分隔
4. 只输出关键词列表，不要其他内容

关键词："""

        messages = [{"role": "user", "content": prompt}]
        content = self._call_text_llm(messages, max_tokens=500)
        
        if not content:
            return []
        
        keywords_text = content.strip()
        
        # Parse keywords
        keywords = []
        for sep in [",", "，", "、", "\n"]:
            if sep in keywords_text:
                keywords = [k.strip() for k in keywords_text.split(sep) if k.strip()]
                break
        
        if not keywords:
            keywords = [keywords_text]
        
        return keywords[:max_keywords]


def generate_summary(transcript_text: str, video_title: str = "", video_duration: float = 0) -> str:
    """
    Convenience function to generate summary

    Args:
        transcript_text: Full transcript text
        video_title: Video title
        video_duration: Video duration in minutes

    Returns:
        Summary string
    """
    generator = SummaryGenerator()
    return generator.generate_summary(transcript_text, video_title, video_duration)
