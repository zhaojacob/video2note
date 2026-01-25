"""
Text polisher using DeepSeek Chat model
Supports incremental polishing for long transcripts
"""
import logging
import re
from typing import Optional, List, Dict, Any
from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError, AuthenticationError, APIConnectionError

from config.settings import DEEPSEEK_CONFIG

logger = logging.getLogger(__name__)


class TextPolisher:
    """
    Text polisher using DeepSeek Chat model.

    Strategy:
    - Short texts (<6000 chars): Single-turn processing
    - Long texts (>6000 chars): Multi-turn incremental polishing (polish each chunk independently, then merge)

    Model: deepseek-chat (128K context, 8K max output)
    Chunk size: 6000 chars (~2000-3000 tokens input, safe for 8K output)
    """

    # Characters per chunk - 4500 chars for better timeout tolerance
    # 4500 chars ≈ 1500-2250 tokens input
    # Output max 8192 tokens (~16000-24000 chars) - ample headroom
    CHUNK_SIZE = 4500

    # Max characters for single-turn processing
    MAX_SINGLE_TURN = 4500
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TextPolisher with DeepSeek API

        Args:
            api_key: DeepSeek API key (optional, uses config if not provided)
        """
        self.api_key = api_key or DEEPSEEK_CONFIG.get("api_key")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-chat")
        self.max_tokens = DEEPSEEK_CONFIG.get("max_tokens", 8192)
        self.thinking_enabled = DEEPSEEK_CONFIG.get("thinking", False)

        if not self.api_key:
            logger.warning("DeepSeek API key not configured, TextPolisher will be disabled")
            self.client = None
        else:
            # Initialize client following DeepSeek official example
            # Set timeout to 300 seconds (5 minutes) to handle long text generation
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=300.0,  # 5 minute timeout for long responses
                max_retries=2    # Client-level retry for connection errors
            )
            logger.info(f"TextPolisher initialized: model={self.model}, max_tokens={self.max_tokens}, timeout=300s")

    def is_available(self) -> bool:
        """Check if polisher is available"""
        return self.client is not None

    def _call_deepseek(self, messages: List[Dict[str, str]],
                       max_tokens: Optional[int] = None,
                       retry_count: int = 2) -> Optional[str]:
        """
        Call DeepSeek API with retry logic and detailed error reporting

        Args:
            messages: Conversation messages (should include system and user roles)
            max_tokens: Max tokens for response
            retry_count: Number of retries on failure

        Returns:
            Response content string, or None if failed
        """
        if not self.client:
            logger.error("DeepSeek client not initialized")
            return None

        # Build request parameters following DeepSeek official example
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": 0.3,  # Lower temperature for consistent polish results
            "stream": False,  # Disable streaming
        }

        # Log request details for debugging
        input_chars = sum(len(m.get("content", "")) for m in messages)
        logger.info(f"DeepSeek API request: model={self.model}, max_tokens={params['max_tokens']}, input_chars={input_chars}")

        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"Calling DeepSeek API (attempt {attempt + 1}/{retry_count + 1})")
                response = self.client.chat.completions.create(**params)

                content = response.choices[0].message.content

                # Log success details
                logger.info(f"DeepSeek API success: output_chars={len(content) if content else 0}")
                return content

            except AuthenticationError as e:
                # Authentication error (401) - don't retry
                error_code = getattr(e, 'code', 'unknown')
                error_msg = str(e)
                logger.error(f"DeepSeek API Authentication Error (code={error_code}): {error_msg}")
                print(f"\n[ERROR] Authentication failed: {error_msg}")
                print(f"[ERROR] Please check your API key in .env file")
                return None

            except RateLimitError as e:
                # Rate limit error (429) - retry with longer wait
                error_code = getattr(e, 'code', 'rate_limit_exceeded')
                error_msg = str(e)
                logger.warning(f"DeepSeek API Rate Limit Error (attempt {attempt + 1}): {error_msg}")
                print(f"\n[WARNING] Rate limit exceeded: {error_code}")

                if attempt < retry_count:
                    wait_time = 60  # Wait 60 seconds for rate limit
                    print(f"[INFO] Waiting {wait_time}s before retry...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Rate limit: {error_msg}")
                    return None

            except APITimeoutError as e:
                # Timeout error - retry
                error_msg = str(e)
                logger.warning(f"DeepSeek API Timeout (attempt {attempt + 1}): {error_msg}")
                print(f"\n[WARNING] Request timeout: {error_msg}")

                if attempt < retry_count:
                    import time
                    wait_time = (attempt + 1) * 10  # 10s, 20s backoff for timeout
                    print(f"[INFO] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Request timeout after {retry_count + 1} attempts")
                    return None

            except APIConnectionError as e:
                # Connection error (network issue, server dropped connection, etc.)
                error_msg = str(e)
                logger.warning(f"DeepSeek Connection Error (attempt {attempt + 1}): {error_msg}")
                print(f"\n[WARNING] Connection dropped/failed: {error_msg}")

                if attempt < retry_count:
                    import time
                    wait_time = (attempt + 1) * 5  # 5s, 10s backoff
                    print(f"[INFO] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Connection failed after {retry_count + 1} attempts")
                    return None

            except APIError as e:
                # API error with status code
                status_code = getattr(e, 'status_code', 'unknown')
                error_code = getattr(e, 'code', None)
                error_body = getattr(e, 'body', {})
                error_msg = str(e)

                # Extract detailed error info
                error_detail = self._extract_error_detail(error_body)

                logger.error(f"DeepSeek API Error (attempt {attempt + 1}): status={status_code}, code={error_code}, detail={error_detail}")
                print(f"\n[ERROR] API Error (status={status_code})")
                if error_code:
                    print(f"[ERROR] Error code: {error_code}")
                if error_detail:
                    print(f"[ERROR] Message: {error_detail}")
                else:
                    print(f"[ERROR] {error_msg}")

                # Don't retry on client errors (4xx), but retry on server errors (5xx)
                if isinstance(status_code, int) and 400 <= status_code < 500:
                    logger.error(f"Client error {status_code} - not retrying")
                    print(f"[ERROR] Client error - check request parameters")
                    return None
                elif attempt < retry_count:
                    import time
                    wait_time = (attempt + 1) * 5  # 5s, 10s backoff
                    print(f"[INFO] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Failed after {retry_count + 1} attempts")
                    return None

            except Exception as e:
                # Unknown error
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"DeepSeek API Unexpected Error (attempt {attempt + 1}): {error_type}: {error_msg}")
                print(f"\n[ERROR] Unexpected error: {error_type}")
                print(f"[ERROR] {error_msg}")

                if attempt < retry_count:
                    import time
                    wait_time = (attempt + 1) * 5
                    print(f"[INFO] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Failed after {retry_count + 1} attempts")
                    return None

        return None

    def _extract_error_detail(self, error_body: Dict[str, Any]) -> str:
        """
        Extract detailed error message from error body

        Args:
            error_body: Error response body

        Returns:
            Formatted error message
        """
        if not error_body:
            return ""

        # Try to get error message from different possible structures
        if isinstance(error_body, dict):
            # OpenAI error format
            if 'error' in error_body:
                error = error_body['error']
                if isinstance(error, dict):
                    return error.get('message', str(error))
                return str(error)

            # Direct message field
            if 'message' in error_body:
                return error_body['message']

        return str(error_body)

    def polish(self, raw_transcript: str, video_title: str = "", 
               duration_minutes: float = 0) -> Optional[str]:
        """
        Polish raw transcript
        
        Strategy:
        1. If text is short (<MAX_SINGLE_TURN), polish in single turn
        2. If text is long, use multi-turn conversation
        
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
        print(f"  → Text length: {text_length} chars")
        
        # Use simple single-turn for texts under 25000 chars (~100 min video usually ~35000)
        if text_length <= self.MAX_SINGLE_TURN:
            print(f"  → Using single-turn processing...")
            return self._polish_single_turn(raw_transcript, video_title)
        
        # Use multi-turn for very long texts
        print(f"  → Text too long for single turn, using multi-turn processing...")
        return self._polish_multi_turn(raw_transcript, video_title, duration_minutes)

    def _polish_single_turn(self, text: str, video_title: str = "") -> Optional[str]:
        """
        Polish text in a single API call (for texts under 25000 chars)
        
        Args:
            text: Raw transcript text
            video_title: Optional video title
            
        Returns:
            Polished text
        """
        title_context = f"Video title: {video_title}\n" if video_title else ""
        
        system_prompt = """You are a professional transcript proofreader. Your task is to clean up speech-to-text transcripts.

[STRICT REQUIREMENTS]
- You can ONLY proofread and format. You must NOT rewrite, paraphrase, summarize, or condense the original text.
- Every sentence from the original MUST be preserved. You are only making it more readable.

[ALLOWED OPERATIONS]
1. Add punctuation marks (periods, commas, question marks, exclamation marks, colons, etc.)
2. Fix obvious speech recognition errors (homophones, typos)
3. Remove consecutive filler words (like "um um um", "uh uh", "you know you know")
4. Divide into chapters at topic transitions, using ## markers

[FORBIDDEN OPERATIONS]
- Do NOT delete any substantive content
- Do NOT change the speaker's original meaning
- Do NOT add information not in the original
- Do NOT rephrase in your own words
- Do NOT summarize or condense

[OUTPUT FORMAT]
## Chapter Title (brief, based on content)
Proofread original content...

## Next Chapter Title
Proofread original content..."""

        user_prompt = f"""{title_context}Please proofread the following speech transcript (only add punctuation and chapter divisions, preserve ALL original content):

{text}"""

        # Follow DeepSeek API format: system + user messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        print(f"  → Calling DeepSeek (this may take 1-2 minutes)...", end="", flush=True)
        content = self._call_deepseek(messages)
        
        if content:
            print(" Done!")
        else:
            print(" Failed!")
        
        return content

    def _polish_multi_turn(self, text: str, video_title: str = "",
                           duration_minutes: float = 0) -> Optional[str]:
        """
        Polish long text using incremental strategy (polish each chunk independently, then merge).

        Strategy:
        - Turn 1: Polish chunk 1 (start with chapter structure)
        - Turn 2+: Polish chunk N with previous context (maintain continuity)
        - Final: Merge all polished chunks

        This avoids the large final generation that causes timeout/context overflow.

        Args:
            text: Raw transcript text
            video_title: Optional video title
            duration_minutes: Video duration

        Returns:
            Polished text with chapters
        """
        try:
            # Split text into chunks
            chunks = self._split_into_chunks(text)
            logger.info(f"Split transcript into {len(chunks)} chunks for incremental polishing")
            print(f"  → Split into {len(chunks)} chunks, polishing incrementally...")

            print(f"     [DEBUG] Total text: {len(text)} chars")
            for i, c in enumerate(chunks):
                print(f"     [DEBUG] Chunk {i+1}: {len(c)} chars", flush=True)

            # Base system prompt with all strict requirements (unchanged from original)
            base_system_prompt = """You are a professional transcript proofreader. Your task is to clean up speech-to-text transcripts.

[STRICT REQUIREMENTS]
- You can ONLY proofread and format. You must NOT rewrite, paraphrase, summarize, or condense the original text.
- Every sentence from the original MUST be preserved. You are only making it more readable.

[ALLOWED OPERATIONS]
1. Add punctuation marks (periods, commas, question marks, exclamation marks, colons, etc.)
2. Fix obvious speech recognition errors (homophones, typos)
3. Remove consecutive filler words (like "um um um", "uh uh", "you know you know")
4. Divide into chapters at topic transitions, using ## markers

[FORBIDDEN OPERATIONS]
- Do NOT delete any substantive content
- Do NOT change the speaker's original meaning
- Do NOT add information not in the original
- Do NOT rephrase in your own words
- Do NOT summarize or condense

[OUTPUT FORMAT]
## Chapter Title (brief, based on content)
Proofread original content...

## Next Chapter Title
Proofread original content..."""

            polished_chunks = []
            previous_content = ""

            for i, chunk in enumerate(chunks):
                print(f"\n  → [{i+1}/{len(chunks)}] Polishing chunk {i+1} ({len(chunk)} chars)...", flush=True)

                # Debug: Log chunk info
                logger.info(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

                try:
                    # Build messages following DeepSeek API format (system + user roles)
                    if i == 0:
                        # First chunk: establish chapter structure
                        user_content = f"""{self._get_title_context(video_title, duration_minutes)}
Please proofread the following speech transcript (part 1 of {len(chunks)} parts):

{chunk}

Note: Start with chapter 1 and use ## markers for chapter divisions."""
                    else:
                        # Subsequent chunks: provide context from previous chunk
                        previous_ending = self._get_last_section(previous_content)
                        user_content = f"""This is part {i+1} of {len(chunks)} parts of the transcript.

For context, here's how the previous part ended:
{previous_ending}

Please continue proofreading this part:

{chunk}

Note: Maintain chapter continuity with ## markers. Continue from where the previous part ended."""

                    # Follow DeepSeek API format: system + user messages
                    messages = [
                        {"role": "system", "content": base_system_prompt},
                        {"role": "user", "content": user_content}
                    ]

                    # Debug: Log message info
                    total_input_chars = sum(len(m.get("content", "")) for m in messages)
                    logger.info(f"Messages prepared: {len(messages)} messages, {total_input_chars} chars total")
                    print(f"     [DEBUG] Total input: {total_input_chars} chars", flush=True)

                    # Polish this chunk with 8K max output
                    print(f"     Calling API...", end="", flush=True)
                    polished_chunk = self._call_deepseek(messages, max_tokens=self.max_tokens)

                    if polished_chunk:
                        polished_chunks.append(polished_chunk)
                        previous_content = polished_chunk
                        print(f" Done! ({len(polished_chunk)} chars)")
                        logger.info(f"Polished chunk {i+1}/{len(chunks)}: {len(polished_chunk)} chars")
                    else:
                        # Fallback to original chunk on failure
                        logger.warning(f"Failed to polish chunk {i+1}, using raw text")
                        print(f" Failed! Using raw chunk {i+1}")
                        polished_chunks.append(chunk)
                        previous_content = chunk

                except Exception as chunk_error:
                    # Catch any error during chunk processing
                    logger.error(f"Exception while processing chunk {i+1}: {type(chunk_error).__name__}: {chunk_error}")
                    print(f"\n[ERROR] Exception in chunk {i+1}: {type(chunk_error).__name__}")
                    print(f"[ERROR] {chunk_error}")
                    print(f"     Using raw chunk {i+1}")
                    polished_chunks.append(chunk)
                    previous_content = chunk
                    # Continue to next chunk instead of crashing

            # Merge all polished chunks
            result = "\n\n".join(polished_chunks)
            print(f"\n  → Combined polished text: {len(result)} chars, {len(polished_chunks)} chunks")
            logger.info(f"Successfully polished text: {len(result)} chars from {len(chunks)} chunks")
            return result

        except Exception as e:
            # Catch any unexpected error at function level
            logger.error(f"Fatal error in _polish_multi_turn: {type(e).__name__}: {e}")
            print(f"\n[FATAL ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Return original text as fallback
            return text

    def _get_last_section(self, text: str) -> str:
        """
        Extract the last section from previous chunk as context for the next chunk.

        Args:
            text: Previous polished chunk

        Returns:
            Last chapter or last 200 characters for context
        """
        lines = text.split('\n')

        # Find the last ## chapter marker
        last_chapter_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('## '):
                last_chapter_idx = i
                break

        if last_chapter_idx >= 0:
            # Return the last chapter content (limited to 500 chars)
            last_section = '\n'.join(lines[last_chapter_idx:])
            return last_section[:500] if len(last_section) > 500 else last_section
        else:
            # No chapter markers found, return last 200 chars
            return text[-200:] if len(text) > 200 else text

    def _get_title_context(self, video_title: str, duration_minutes: float) -> str:
        """
        Build title and duration context for the first chunk.

        Args:
            video_title: Video title
            duration_minutes: Video duration in minutes

        Returns:
            Formatted context string
        """
        parts = []
        if video_title:
            parts.append(f"Video title: {video_title}")
        if duration_minutes > 0:
            parts.append(f"Duration: {duration_minutes:.0f} minutes")
        return "\n".join(parts) + "\n" if parts else ""

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
