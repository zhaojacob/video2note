"""
Text polisher using DeepSeek Reasoner with thinking mode
Supports multi-turn conversation for long transcripts
"""
import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from openai import OpenAI

from config.settings import DEEPSEEK_CONFIG

logger = logging.getLogger(__name__)


class TextPolisher:
    """
    Text polisher using DeepSeek Reasoner with thinking mode enabled.
    
    Strategy for long transcripts:
    - Turn 1: Generate chapter outline based on content
    - Turn 2+: Polish each chapter with context from previous turns
    """
    
    # Characters per chunk for multi-turn processing
    CHUNK_SIZE = 8000
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TextPolisher with DeepSeek API
        
        Args:
            api_key: DeepSeek API key (optional, uses config if not provided)
        """
        self.api_key = api_key or DEEPSEEK_CONFIG.get("api_key")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-reasoner")
        self.max_tokens = DEEPSEEK_CONFIG.get("max_tokens", 32768)
        self.thinking_enabled = DEEPSEEK_CONFIG.get("thinking", True)
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured, TextPolisher will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info(f"TextPolisher initialized with model: {self.model}, thinking: {self.thinking_enabled}")

    def is_available(self) -> bool:
        """Check if polisher is available"""
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
            # Build request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            # Enable thinking mode if configured
            if self.thinking_enabled:
                params["extra_body"] = {"thinking": {"type": "enabled"}}
            
            logger.debug(f"Calling DeepSeek API with {len(messages)} messages")
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            reasoning_content = getattr(response.choices[0].message, 'reasoning_content', None)
            
            logger.debug(f"Response received: {len(content) if content else 0} chars")
            if reasoning_content:
                logger.debug(f"Reasoning content: {len(reasoning_content)} chars")
            
            return content, reasoning_content
            
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            return None, None

    def polish(self, raw_transcript: str, video_title: str = "", 
               duration_minutes: float = 0) -> Optional[str]:
        """
        Polish raw transcript using multi-turn conversation
        
        Strategy:
        1. If text is short (<CHUNK_SIZE), polish in single turn
        2. If text is long, use multi-turn: outline first, then polish by chapter
        
        Args:
            raw_transcript: Raw transcript text from Whisper
            video_title: Optional video title for context
            duration_minutes: Video duration in minutes
            
        Returns:
            Polished text with chapter markers, or None if failed
        """
        if not self.client:
            logger.warning("TextPolisher not available, returning raw transcript")
            return raw_transcript
            
        if not raw_transcript or not raw_transcript.strip():
            logger.warning("Empty transcript, nothing to polish")
            return raw_transcript
        
        text_length = len(raw_transcript)
        logger.info(f"Polishing transcript: {text_length} chars, {duration_minutes:.1f} minutes")
        
        # Use simple single-turn for short texts
        if text_length <= self.CHUNK_SIZE:
            return self._polish_single_turn(raw_transcript, video_title)
        
        # Use multi-turn for long texts
        return self._polish_multi_turn(raw_transcript, video_title, duration_minutes)

    def _polish_single_turn(self, text: str, video_title: str = "") -> Optional[str]:
        """
        Polish short text in a single API call
        
        Args:
            text: Raw transcript text
            video_title: Optional video title
            
        Returns:
            Polished text
        """
        title_context = f"视频标题：《{video_title}》\n" if video_title else ""
        
        system_prompt = """你是一位专业的文字编辑，擅长将语音转录文本整理成结构清晰、易于阅读的文档。

你的任务是：
1. 修正语音识别错误（错别字、专业术语等）
2. 去除口语化表达和语气词（啊、嗯、然后、这个、那个等）
3. 合并重复和冗余的表达
4. 根据内容主题划分章节，用 ## 章节标题 格式标记
5. 在每个章节内保持原文的核心信息，但使行文流畅

输出格式：
## 第一章节的标题
该章节的整理后内容...

## 第二章节的标题
该章节的整理后内容...

注意：保持原文的信息完整性，不要添加原文没有的内容。"""

        user_prompt = f"""{title_context}请整理以下语音转录文本：

{text}"""

        messages = [
            {"role": "user", "content": system_prompt + "\n\n" + user_prompt}
        ]
        
        content, _ = self._call_deepseek(messages)
        return content

    def _polish_multi_turn(self, text: str, video_title: str = "", 
                           duration_minutes: float = 0) -> Optional[str]:
        """
        Polish long text using multi-turn conversation
        
        Turn 1: Generate chapter outline
        Turn 2+: Polish each section with context
        
        Args:
            text: Raw transcript text
            video_title: Optional video title
            duration_minutes: Video duration
            
        Returns:
            Polished text with chapters
        """
        title_context = f"视频标题：《{video_title}》" if video_title else ""
        duration_context = f"（时长约{duration_minutes:.0f}分钟）" if duration_minutes > 0 else ""
        
        # Split text into chunks
        chunks = self._split_into_chunks(text)
        logger.info(f"Split transcript into {len(chunks)} chunks for processing")
        
        # Turn 1: Analyze structure and get chapter outline
        outline_prompt = f"""你是一位专业的文字编辑。我将分段发送一份长篇语音转录文本{duration_context}。

{title_context}

这是完整转录文本的第1部分（共{len(chunks)}部分）：

{chunks[0]}

请先阅读这部分内容，告诉我你打算如何划分章节。只需要给出章节大纲，格式如：
1. [章节名称] - 简要说明该章节涵盖的内容
2. [章节名称] - 简要说明
...

注意：现在只需要给出大纲计划，后续我会发送更多内容让你完善大纲。"""

        messages = [{"role": "user", "content": outline_prompt}]
        
        outline_response, _ = self._call_deepseek(messages, max_tokens=4096)
        if not outline_response:
            logger.error("Failed to get chapter outline")
            return self._polish_single_turn(text[:self.CHUNK_SIZE], video_title)
        
        logger.info("Got initial chapter outline")
        messages.append({"role": "assistant", "content": outline_response})
        
        # Send remaining chunks to refine outline
        for i, chunk in enumerate(chunks[1:], start=2):
            chunk_prompt = f"""这是第{i}部分（共{len(chunks)}部分）：

{chunk}

请根据新内容更新你的章节大纲。"""
            
            messages.append({"role": "user", "content": chunk_prompt})
            
            response, _ = self._call_deepseek(messages, max_tokens=4096)
            if response:
                messages.append({"role": "assistant", "content": response})
                logger.info(f"Processed chunk {i}/{len(chunks)}")
            else:
                logger.warning(f"Failed to process chunk {i}, continuing...")
        
        # Final turn: Request polished output
        polish_prompt = """现在请根据你的章节大纲，输出整理后的完整文本。

要求：
1. 修正语音识别错误（错别字、专业术语等）
2. 去除口语化表达和语气词
3. 合并重复和冗余的表达
4. 使用 ## 章节标题 格式标记各章节
5. 保持原文的信息完整性

请直接输出整理后的文本，格式如下：
## 第一个章节标题
该章节的整理后内容...

## 第二个章节标题
该章节的整理后内容..."""

        messages.append({"role": "user", "content": polish_prompt})
        
        final_content, _ = self._call_deepseek(messages, max_tokens=self.max_tokens)
        
        if not final_content:
            logger.error("Failed to get final polished text")
            return None
        
        logger.info(f"Successfully polished text: {len(final_content)} chars output")
        return final_content

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks for multi-turn processing
        
        Tries to split at paragraph boundaries for better context
        
        Args:
            text: Full text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Try to split at double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > self.CHUNK_SIZE and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        # If no good splits found, fall back to simple character splitting
        if len(chunks) == 1 and len(text) > self.CHUNK_SIZE:
            chunks = []
            for i in range(0, len(text), self.CHUNK_SIZE):
                chunks.append(text[i:i + self.CHUNK_SIZE])
        
        return chunks

    def extract_chapters(self, polished_text: str) -> List[Dict[str, str]]:
        """
        Extract chapters from polished text
        
        Args:
            polished_text: Text with ## chapter markers
            
        Returns:
            List of dicts with 'title' and 'content' keys
        """
        if not polished_text:
            return []
        
        chapters = []
        current_chapter = None
        current_content = []
        
        # Match chapter headers (## title format)
        chapter_pattern = re.compile(r'^##\s+(.+)$')
        
        for line in polished_text.split('\n'):
            match = chapter_pattern.match(line.strip())
            if match:
                # Save previous chapter if exists
                if current_chapter is not None:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content).strip()
                    })
                # Start new chapter
                current_chapter = match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last chapter
        if current_chapter is not None:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content).strip()
            })
        
        # If no chapters found, treat entire text as one chapter
        if not chapters and polished_text.strip():
            chapters.append({
                'title': '正文',
                'content': polished_text.strip()
            })
        
        return chapters

    def get_plain_text(self, polished_text: str) -> str:
        """
        Get plain text without chapter markers
        
        Args:
            polished_text: Polished text with ## chapter markers
            
        Returns:
            Plain text with chapter titles preserved but without ## markers
        """
        if not polished_text:
            return ""
            
        lines = polished_text.split('\n')
        result = []
        
        for line in lines:
            if line.strip().startswith('## '):
                # Convert chapter marker to plain title with emphasis
                title = line.strip()[3:]
                result.append(f"\n【{title}】\n")
            else:
                result.append(line)
        
        return '\n'.join(result)
