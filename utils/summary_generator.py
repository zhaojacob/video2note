"""
Summary generator using DeepSeek API
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

from utils.logger import get_logger

logger = get_logger(__name__)


class SummaryGenerator:
    """Generate video summaries using DeepSeek LLM"""

    def __init__(self):
        """Initialize summary generator with DeepSeek API"""
        from config.settings import DEEPSEEK_CONFIG
        
        self.api_key = DEEPSEEK_CONFIG.get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-chat")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.timeout = DEEPSEEK_CONFIG.get("timeout", 120)
        self.max_tokens = DEEPSEEK_CONFIG.get("max_tokens", 2000)
        
        if not self.api_key:
            logger.warning("DeepSeek API key not found. Summary generation will be skipped.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            logger.info("SummaryGenerator initialized with DeepSeek API")

    def generate_summary(
        self,
        transcript_text: str,
        video_title: str = "",
        max_length: int = 500
    ) -> str:
        """
        Generate a summary from transcript text
        
        Args:
            transcript_text: Full transcript text
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
        max_input_chars = 15000
        if len(transcript_text) > max_input_chars:
            transcript_text = transcript_text[:max_input_chars] + "..."
            logger.info(f"Transcript truncated to {max_input_chars} characters")
        
        prompt = f"""请为以下视频内容生成一个简洁的中文摘要。

视频标题：{video_title}

视频转录文本：
{transcript_text}

要求：
1. 摘要应该概括视频的主要内容、核心观点和关键信息
2. 使用简洁流畅的中文表述
3. 摘要长度控制在{max_length}字以内
4. 不要使用"本视频"、"视频中"等开头，直接陈述内容
5. 如果是英文内容，请翻译成中文摘要

请直接输出摘要内容，不要添加任何前缀或标签："""

        try:
            logger.info("Generating summary with DeepSeek...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容摘要助手，擅长提取视频的核心信息并生成简洁准确的摘要。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
                stream=False
            )
            
            content = response.choices[0].message.content
            if content is None:
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
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return ""

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
        max_input_chars = 8000
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.2,
                stream=False
            )
            
            content = response.choices[0].message.content
            if content is None:
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
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []


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
