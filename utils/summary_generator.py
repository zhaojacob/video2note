"""
Summary generator using DeepSeek Reasoner with thinking mode
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

from config.settings import DEEPSEEK_CONFIG

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate video summaries using DeepSeek Reasoner with thinking mode"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize summary generator with DeepSeek API
        
        Args:
            api_key: DeepSeek API key (optional, uses config if not provided)
        """
        self.api_key = api_key or DEEPSEEK_CONFIG.get("api_key")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-reasoner")
        self.max_tokens = DEEPSEEK_CONFIG.get("max_tokens", 32768)
        self.thinking_enabled = DEEPSEEK_CONFIG.get("thinking", True)
        
        if not self.api_key:
            logger.warning("DeepSeek API key not found. Summary generation will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(f"SummaryGenerator initialized with model: {self.model}, thinking: {self.thinking_enabled}")

    def is_available(self) -> bool:
        """Check if generator is available"""
        return self.client is not None

    def _call_deepseek(self, messages: List[Dict[str, str]], 
                       max_tokens: Optional[int] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Call DeepSeek API with thinking mode
        
        Args:
            messages: Conversation messages
            max_tokens: Max tokens for response
            
        Returns:
            Tuple of (content, reasoning_content)
        """
        if not self.client:
            return None, None
            
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            # Enable thinking mode if configured
            if self.thinking_enabled:
                params["extra_body"] = {"thinking": {"type": "enabled"}}
            
            logger.debug(f"Calling DeepSeek API for summary generation")
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            reasoning_content = getattr(response.choices[0].message, 'reasoning_content', None)
            
            logger.debug(f"Response received: {len(content) if content else 0} chars")
            
            return content, reasoning_content
            
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            return None, None

    def generate_summary(
        self,
        transcript_text: str,
        video_title: str = "",
        max_length: int = 500
    ) -> str:
        """
        Generate a summary from transcript text
        
        Args:
            transcript_text: Full transcript text (polished or raw)
            video_title: Video title for context
            max_length: Maximum summary length in characters
            
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
        
        title_context = f"视频标题：《{video_title}》\n" if video_title else ""
        
        prompt = f"""{title_context}请为以下视频内容生成一个全面的中文摘要。

视频转录文本：
{transcript_text}

要求：
1. 摘要应该概括视频的主要内容、核心观点和关键信息
2. 使用简洁流畅的中文表述
3. 摘要长度控制在{max_length}字以内
4. 不要使用"本视频"、"视频中"等开头，直接陈述内容
5. 如果是英文内容，请翻译成中文摘要
6. 按照逻辑顺序组织摘要内容

请直接输出摘要内容，不要添加任何前缀或标签："""

        messages = [{"role": "user", "content": prompt}]
        
        logger.info("Generating summary with DeepSeek Reasoner...")
        content, reasoning = self._call_deepseek(messages, max_tokens=4096)
        
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
        content, _ = self._call_deepseek(messages, max_tokens=500)
        
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


def generate_summary(transcript_text: str, video_title: str = "") -> str:
    """
    Convenience function to generate summary
    
    Args:
        transcript_text: Full transcript text
        video_title: Video title
        
    Returns:
        Summary string
    """
    generator = SummaryGenerator()
    return generator.generate_summary(transcript_text, video_title)
