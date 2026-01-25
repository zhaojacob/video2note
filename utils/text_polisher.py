"""
Text polisher using DeepSeek API
优化转录文本：添加标点、分段、章节划分
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

from utils.logger import get_logger

logger = get_logger(__name__)


class TextPolisher:
    """Polish transcribed text using DeepSeek LLM"""

    def __init__(self):
        """Initialize text polisher with DeepSeek API"""
        from config.settings import DEEPSEEK_CONFIG
        
        self.api_key = DEEPSEEK_CONFIG.get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-chat")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.timeout = DEEPSEEK_CONFIG.get("timeout", 300)  # Longer timeout for long text
        self.max_tokens_limit = 8000  # DeepSeek limit is 8192, leave some buffer
        
        if not self.api_key:
            logger.warning("DeepSeek API key not found. Text polishing will be skipped.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            logger.info("TextPolisher initialized with DeepSeek API")

    def is_available(self) -> bool:
        """Check if polisher is available"""
        return self.client is not None

    def polish_segments(
        self,
        segments: List[Dict[str, Any]],
        source_language: str = "zh"
    ) -> List[Dict[str, Any]]:
        """
        Polish transcript segments while preserving timestamps.
        Each segment's text gets punctuation added.
        
        Args:
            segments: List of transcript segments with 'start', 'end', 'text'
            source_language: Source language of the audio
            
        Returns:
            List of segments with polished 'text' field
        """
        if not self.client or not segments:
            return segments
        
        # Combine all text for batch processing
        texts = [seg.get('text', '').strip() for seg in segments]
        combined_text = '\n'.join(f"[{i}] {t}" for i, t in enumerate(texts) if t)
        
        # Determine if we should convert to simplified Chinese
        is_chinese = source_language.lower() in ['zh', 'zh-cn', 'zh-tw', 'chinese', 'mandarin', 'cantonese', 'auto']
        
        simplify_instruction = ""
        if is_chinese:
            simplify_instruction = "3. 将繁体字转换为简体字\n"
        
        system_prompt = """你是一个文本标点符号添加助手。用户会给你一系列带编号的语音转录片段，你需要为每个片段添加合适的标点符号。

要求：
- 保持原有的编号格式 [数字]
- 只添加标点符号，不要改变原文内容
- 修正明显的语音识别错误（同音字）
- 直接输出处理后的文本，不要有任何解释"""

        user_prompt = f"""请为以下语音转录片段添加标点符号。

要求：
1. 添加标点符号（句号、逗号、问号、感叹号等）
2. 保持 [数字] 编号格式不变
{simplify_instruction}4. 不要删除或添加实质性内容

转录片段：
{combined_text}

添加标点后："""

        try:
            logger.info(f"Polishing {len(segments)} segments ({len(combined_text)} chars)...")
            
            # Split into chunks if text is too long
            max_input_chars = 15000  # Leave room for prompt and response
            if len(combined_text) > max_input_chars:
                return self._polish_segments_in_chunks(segments, source_language)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens_limit,
                temperature=0.1,
            )
            
            polished_text = response.choices[0].message.content
            if not polished_text:
                logger.warning("Empty response, returning original segments")
                return segments
            
            # Parse polished text back into segments
            polished_segments = self._parse_polished_segments(polished_text, segments)
            logger.info(f"Segments polished successfully")
            return polished_segments
            
        except Exception as e:
            logger.error(f"Segment polishing failed: {e}")
            return segments

    def _polish_segments_in_chunks(
        self,
        segments: List[Dict[str, Any]],
        source_language: str
    ) -> List[Dict[str, Any]]:
        """Polish segments in chunks when text is too long"""
        chunk_size = 200  # segments per chunk
        polished_segments = []
        
        for i in range(0, len(segments), chunk_size):
            chunk = segments[i:i + chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} segments)")
            polished_chunk = self._polish_single_chunk(chunk, source_language, i)
            polished_segments.extend(polished_chunk)
        
        return polished_segments

    def _polish_single_chunk(
        self,
        segments: List[Dict[str, Any]],
        source_language: str,
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Polish a single chunk of segments"""
        if not self.client or not segments:
            return segments
        
        texts = [seg.get('text', '').strip() for seg in segments]
        combined_text = '\n'.join(f"[{i}] {t}" for i, t in enumerate(texts) if t)
        
        is_chinese = source_language.lower() in ['zh', 'zh-cn', 'zh-tw', 'chinese', 'mandarin', 'cantonese', 'auto']
        simplify_instruction = "3. 将繁体字转换为简体字\n" if is_chinese else ""
        
        system_prompt = """你是一个文本标点符号添加助手。用户会给你一系列带编号的语音转录片段，你需要为每个片段添加合适的标点符号。保持编号格式，直接输出结果。"""

        user_prompt = f"""为以下转录片段添加标点：
1. 添加标点符号
2. 保持 [数字] 编号
{simplify_instruction}
{combined_text}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens_limit,
                temperature=0.1,
            )
            
            polished_text = response.choices[0].message.content
            if not polished_text:
                return segments
            
            return self._parse_polished_segments(polished_text, segments)
            
        except Exception as e:
            logger.error(f"Chunk polishing failed: {e}")
            return segments

    def _parse_polished_segments(
        self,
        polished_text: str,
        original_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse polished text back into segment format"""
        # Extract polished texts by index
        pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)'
        matches = re.findall(pattern, polished_text, re.DOTALL)
        
        polished_map = {}
        for idx_str, text in matches:
            try:
                idx = int(idx_str)
                polished_map[idx] = text.strip()
            except ValueError:
                continue
        
        # Update segments with polished text
        result = []
        for i, seg in enumerate(original_segments):
            new_seg = seg.copy()
            if i in polished_map:
                new_seg['text'] = polished_map[i]
            result.append(new_seg)
        
        return result

    def polish_transcript(
        self, 
        text: str, 
        duration_minutes: float = 0,
        source_language: str = "zh"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Polish transcribed text: add punctuation, paragraphs, organize into chapters.
        Used for document generation (DOCX/Markdown).
        
        Args:
            text: Raw transcribed text (full text without timestamps)
            duration_minutes: Video duration in minutes (for chapter limit calculation)
            source_language: Source language of the audio (zh/en/ja/ko etc.)
            
        Returns:
            Tuple of (polished_text, chapters)
            - polished_text: Full polished text with chapter markers
            - chapters: List of chapter dicts with 'title' and 'content'
        """
        if not self.client:
            logger.warning("TextPolisher not initialized, returning original text")
            return text, []
        
        if not text or len(text.strip()) < 10:
            return text, []
        
        # Calculate max chapters based on duration (1 chapter per 15 minutes max)
        max_chapters = max(1, int(duration_minutes / 15)) if duration_minutes > 0 else 10
        
        # Determine if we should convert to simplified Chinese
        is_chinese = source_language.lower() in ['zh', 'zh-cn', 'zh-tw', 'chinese', 'mandarin', 'cantonese', 'auto']
        
        simplify_instruction = ""
        if is_chinese:
            simplify_instruction = "4. 将所有繁体字转换为简体字\n"
        
        system_prompt = """你是一位专业的文字编辑和内容整理专家。你的任务是将语音转录的原始文本整理成结构清晰、易于阅读的文章。

你需要：
- 准确添加标点符号，使句子通顺
- 根据内容语义划分段落和章节
- 为每个章节拟定简洁准确的标题
- 保持原文的核心内容和说话者的原意
- 修正明显的语音识别错误（同音字、漏字等）

输出格式要求：
- 使用 "## 章节标题" 格式标记每个章节的开始
- 章节内的段落之间用空行分隔
- 不要添加任何解释性文字，直接输出整理后的内容"""

        user_prompt = f"""请整理以下语音转录文本。

整理要求：
1. 添加合适的标点符号（句号、逗号、问号、感叹号、冒号、引号等）
2. 根据内容大意划分章节，每个章节拟一个简洁的标题（使用 "## 标题" 格式）
3. 章节数量不超过 {max_chapters} 个（视频时长约 {int(duration_minutes)} 分钟）
{simplify_instruction}5. 章节内按语义划分段落（每段3-6句话）
6. 修正明显的语音识别错误，但保持原意
7. 不要删除或添加实质性内容

原始转录文本：
{text}

整理后的文本："""

        try:
            logger.info(f"Polishing text ({len(text)} chars, max {max_chapters} chapters)...")
            
            # If text is too long, truncate for chapter organization
            # (segments are already polished separately)
            if len(text) > 20000:
                logger.warning(f"Text too long ({len(text)} chars), truncating to 20000 for chapter organization")
                text = text[:20000] + "..."
                user_prompt = user_prompt.replace(text[:20000] + "...", text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens_limit,
                temperature=0.1,
            )
            
            polished = response.choices[0].message.content
            if polished:
                polished = polished.strip()
                logger.info(f"Text polished: {len(text)} -> {len(polished)} chars")
                
                # Parse chapters from polished text
                chapters = self._parse_chapters(polished)
                logger.info(f"Extracted {len(chapters)} chapters")
                
                return polished, chapters
            else:
                logger.warning("Empty response from DeepSeek, returning original text")
                return text, []
            
        except Exception as e:
            logger.error(f"Text polishing failed: {e}")
            return text, []

    def _parse_chapters(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse chapters from polished text
        
        Args:
            text: Polished text with ## chapter markers
            
        Returns:
            List of chapter dicts with 'title' and 'content'
        """
        chapters = []
        
        # Split by chapter markers (## Title)
        # Pattern matches "## " at the start of a line
        chapter_pattern = r'^##\s+(.+)$'
        
        lines = text.split('\n')
        current_chapter = None
        current_content = []
        
        for line in lines:
            match = re.match(chapter_pattern, line.strip())
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
        if not chapters and text.strip():
            chapters.append({
                'title': '正文',
                'content': text.strip()
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
        # Replace ## markers with plain text representation
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
