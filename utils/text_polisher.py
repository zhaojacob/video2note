"""
Text polisher using DeepSeek Chat model
Supports incremental polishing for long transcripts

Now uses UnifiedLLMManager for flexible model selection and fallback strategies.
"""
import logging
import re
from typing import Optional, List, Dict, Any
from utils.llm_client import LLMClient
from utils.llm.unified_manager import UnifiedLLMManager
from config.settings import TEXT_LLM_PROVIDER, TEXT_LLM_CONFIGS
from config.llm_config import get_recommended_models, get_fallback_chain
from config.prompt_templates import TRANSCRIPT_POLISH_SYSTEM_PROMPT, TRANSCRIPT_POLISH_USER_PROMPT

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
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_temperature: float = 0.3,
        use_unified_manager: bool = True,  # Changed default to True
        model_id: Optional[str] = None,
        provider: Optional[str] = None
    ):
        """
        Initialize TextPolisher

        Args:
            api_key: DeepSeek API key (optional, uses config if not provided) - legacy only
            default_temperature: Default temperature for LLM generation
            use_unified_manager: Use new UnifiedLLMManager (now default=True)
            model_id: Specific model ID to use (requires use_unified_manager=True)
            provider: Specific provider ID to use (Provider-First API, requires use_unified_manager=True)
        """
        self.provider = provider or TEXT_LLM_PROVIDER
        self.use_unified_manager = use_unified_manager
        self.default_temperature = default_temperature

        if use_unified_manager:
            # New implementation using UnifiedLLMManager
            self.manager = UnifiedLLMManager()
            self.model_id = model_id
            self.llm_client = None  # Will use manager instead

            # Get recommended providers for polish task
            self.recommendation = get_recommended_models("polish")
            self.fallback_providers = self.recommendation.get("fallback_providers",
                self.recommendation.get("fallback", ["deepseek"]))

            logger.info(f"TextPolisher initialized with UnifiedLLMManager (default, provider: {provider}, fallback: {self.fallback_providers})")
        else:
            # Legacy implementation (backward compatible)
            config = TEXT_LLM_CONFIGS.get(self.provider, TEXT_LLM_CONFIGS.get("modelscope", {}))

            self.api_key = api_key or config.get("api_key")
            self.base_url = config.get("base_url")
            self.model = config.get("model")
            self.max_tokens = config.get("max_tokens", 8192)
            self.extra_body = config.get("extra_body")
            self.manager = None
            self.model_id = None

            if not self.api_key:
                logger.warning("Text LLM API key not configured, TextPolisher will be disabled")
                self.llm_client = None
            else:
                self.llm_client = LLMClient(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model,
                    timeout=600.0,
                    max_retries=3,
                    default_max_tokens=self.max_tokens,
                    extra_body=self.extra_body
                )

            logger.info(f"TextPolisher initialized with legacy LLMClient (model={self.model})")

    def is_available(self) -> bool:
        """Check if polisher is available"""
        if self.use_unified_manager:
            # Check if any provider in fallback chain is available
            check_providers = [self.provider] if self.provider else self.fallback_providers
            for provider_id in check_providers:
                # Get provider info to determine default model
                from utils.llm.provider_registry import ProviderRegistry
                registry = ProviderRegistry()
                provider_info = registry.get_provider(provider_id)
                if provider_info and provider_info.models:
                    model = provider_info.models[0]
                    client = self.manager.get_client(provider=provider_id, model=model)
                    if client and client.is_available():
                        return True
            return False
        else:
            return self.llm_client is not None and self.llm_client.is_available()

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        retry_count: int = 2
    ) -> Optional[str]:
        """
        Call LLM API with appropriate implementation

        Args:
            messages: Conversation messages
            max_tokens: Max tokens for response
            temperature: Sampling temperature
            retry_count: Number of retries

        Returns:
            Response content string, or None if failed
        """
        temp = temperature if temperature is not None else self.default_temperature

        if self.use_unified_manager:
            # Use UnifiedLLMManager with provider-level fallback
            if self.provider:
                # Provider-First API: Use specific provider
                return self.manager.chat_with_fallback(
                    messages=messages,
                    providers=[self.provider] + self.fallback_providers,
                    model=self.model_id,
                    max_tokens=max_tokens,
                    temperature=temp,
                    retry_count=retry_count
                )
            else:
                # Legacy mode: Use fallback chain directly
                providers = [self.model_id] if self.model_id else self.fallback_providers
                return self.manager.chat_with_fallback(
                    messages=messages,
                    providers=providers,
                    max_tokens=max_tokens,
                    temperature=temp,
                    retry_count=retry_count
                )
        else:
            # Use legacy LLMClient
            return self.llm_client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temp,
                retry_count=retry_count
            )

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
        
        # DEBUG: Print exact payload for user inspection
        print(f"\n[DEBUG] DeepSeek Request Payload:")
        print(f"  Model: {self.model}")
        print(f"  Max Tokens: {params['max_tokens']}")
        print(f"  Messages: {len(messages)} messages")
        # Print the last user message (usually the content)
        if messages:
            last_msg = messages[-1]
            content_preview = last_msg.get("content", "")[:500] + "..." if len(last_msg.get("content", "")) > 500 else last_msg.get("content", "")
            print(f"  Last Message Preview: {content_preview}")
            print(f"  Total Input Chars: {input_chars}")
        print("-" * 60)

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
                    wait_time = (attempt + 1) * 20  # 20s, 40s, 60s backoff for timeout
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
                
                # Print detailed connection error info if available
                if hasattr(e, 'request'):
                    print(f"[DEBUG] Request URL: {e.request.url}")

                if attempt < retry_count:
                    import time
                    wait_time = (attempt + 1) * 10  # 10s, 20s, 30s backoff
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
                
                # Print full error body for debugging
                print(f"[DEBUG] Full Error Body: {error_body}")

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

    def _get_checkpoint_path(self, video_title: str):
        """Generate checkpoint file path from video title"""
        from utils.file_handler import sanitize_filename
        from pathlib import Path
        from config.settings import TEXT_LLM_CONFIGS, TEXT_LLM_PROVIDER, OUTPUT_DIR

        config = TEXT_LLM_CONFIGS.get(TEXT_LLM_PROVIDER, {})
        safe_title = sanitize_filename(video_title or "untitled")
        checkpoint_dir = Path(config.get("checkpoint_dir", OUTPUT_DIR / "transcripts"))
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        return checkpoint_dir / f"{safe_title}_polish_checkpoint.json"

    def _save_checkpoint(self, checkpoint_data: dict, video_title: str):
        """Atomically save checkpoint to disk"""
        import json
        from datetime import datetime
        from pathlib import Path

        checkpoint_path = self._get_checkpoint_path(video_title)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        # Use temporary file for atomic write
        temp_path = checkpoint_path.with_suffix('.tmp')

        checkpoint_data["metadata"]["last_updated"] = datetime.now().isoformat()

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        # Atomic rename
        temp_path.replace(checkpoint_path)

        logger.info(f"Checkpoint saved: {checkpoint_path.name}")

    def _load_checkpoint(self, video_title: str) -> dict:
        """Load checkpoint file if exists"""
        import json
        from pathlib import Path

        checkpoint_path = self._get_checkpoint_path(video_title)
        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def polish_transcript_json(
        self,
        segments: List[Dict[str, Any]],
        video_title: str = "",
        max_chars: int = 5000,
        system_prompt: str = None,
        user_prompt_template: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Polish transcript from JSON segments, returning structured data.
        
        Args:
            segments: List of transcript segments [{"start": 0.0, "text": "..."}]
            video_title: Video title
            max_chars: Target characters per chunk (approx. 2500 tokens)
            system_prompt: Optional override for system prompt
            user_prompt_template: Optional override for user prompt template
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            
        Returns:
            Structured data with sections, headers, and timestamped paragraphs
        """
        if not self.llm_client:
            logger.warning("TextPolisher not available")
            return {"sections": []}
            
        if not segments:
            return {"sections": []}
            
        # Step 1: Pre-process segments (merge small sequential segments)
        # This reduces the number of items in the JSON list and removes unnecessary keys
        # Use larger size (4500 chars) for better context, timestamps will be handled by fuzzy alignment later
        merged_segments = self._merge_sequential_segments(segments, max_chars_per_item=4500)
        logger.info(f"Merged {len(segments)} raw segments into {len(merged_segments)} chunks")
        
        # Step 2: Split merged segments into chunks for LLM processing
        chunks = self._chunk_merged_segments(merged_segments, max_chars)
        logger.info(f"Split into {len(chunks)} LLM input chunks (target {max_chars} chars)")
        print(f"  → Merged {len(segments)} segments into {len(merged_segments)} blocks, split into {len(chunks)} API calls...")
        
        all_sections = []
        
        for i, chunk in enumerate(chunks):
            # Calculate actual char count for logging
            chunk_chars = sum(len(s.get("text", "")) for s in chunk)
            print(f"\n  → [{i+1}/{len(chunks)}] Polishing chunk {i+1} ({len(chunk)} blocks, {chunk_chars} chars)...", flush=True)
            
            # Format chunk for LLM (using merged dict format)
            chunk_json = self._format_segments_for_llm(chunk)
            
            # Context from previous chunk (last section title)
            previous_context = ""
            if all_sections:
                last_section = all_sections[-1]
                previous_context = f"Previous section: {last_section.get('title', 'Introduction')}"
            
            structured_chunk = self._polish_json_chunk(
                chunk_json, 
                video_title, 
                previous_context, 
                i, 
                len(chunks),
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if structured_chunk and "sections" in structured_chunk:
                # Merge logic: if first section of new chunk has same title as last section of previous, merge them
                if all_sections and structured_chunk["sections"]:
                    last_old = all_sections[-1]
                    first_new = structured_chunk["sections"][0]
                    
                    if last_old.get("title") == first_new.get("title"):
                        # Merge paragraphs
                        last_old["paragraphs"].extend(first_new["paragraphs"])
                        # Add remaining sections
                        all_sections.extend(structured_chunk["sections"][1:])
                    else:
                        all_sections.extend(structured_chunk["sections"])
                else:
                    all_sections.extend(structured_chunk.get("sections", []))
            else:
                logger.warning(f"Chunk {i+1} failed to produce valid structure")
                
        return {"sections": all_sections}

    def _merge_sequential_segments(self, segments: List[Dict[str, Any]], max_chars_per_item: int = 5000) -> List[Dict[str, Any]]:
        """
        Merge sequential transcript segments into larger blocks.
        
        Logic:
        - Combine text from sequential segments
        - Keep start time of first segment
        - Keep end time of last segment
        - Discard confidence and no_speech_prob
        - Limit each merged block to max_chars_per_item
        """
        if not segments:
            return []
            
        merged = []
        current_block = None
        
        for seg in segments:
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "").strip()
            
            if not text:
                continue
                
            if current_block is None:
                current_block = {
                    "start": start,
                    "end": end,
                    "text": text
                }
            else:
                # Check if adding this segment would exceed the limit
                if len(current_block["text"]) + len(text) + 1 > max_chars_per_item:
                    # Finalize current block and start new one
                    merged.append(current_block)
                    current_block = {
                        "start": start,
                        "end": end,
                        "text": text
                    }
                else:
                    # Merge into current block
                    current_block["text"] += " " + text
                    current_block["end"] = end
                    
        # Add last block
        if current_block:
            merged.append(current_block)
            
        return merged

    def _chunk_merged_segments(self, segments: List[Dict[str, Any]], max_chars: int) -> List[List[Dict[str, Any]]]:
        """Split merged segments into chunks based on accumulated character count"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for seg in segments:
            text_len = len(seg.get("text", ""))
            # Heuristic: Text + 50 chars overhead for JSON structure
            item_size = text_len + 50
            
            # If adding this segment exceeds limit AND we have content, start new chunk
            if current_size + item_size > max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [seg]
                current_size = item_size
            else:
                current_chunk.append(seg)
                current_size += item_size
                
        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _format_segments_for_llm(self, segments: List[Dict[str, Any]]) -> str:
        """Format segments as JSON list of dicts (standard format)"""
        import json
        
        # Prepare list of dicts with only necessary fields
        formatted_segs = []
        for seg in segments:
            # Format timestamp as HH:MM:SS
            seconds = seg.get("start", 0)
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            ts = f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
            formatted_segs.append({
                "start": ts,
                "text": seg.get("text", "").strip()
            })
            
        return json.dumps(formatted_segs, ensure_ascii=False)

    def _polish_json_chunk(
        self, 
        chunk_json: str, 
        video_title: str, 
        context: str,
        chunk_index: int,
        total_chunks: int,
        system_prompt: str = None,
        user_prompt_template: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Call LLM to polish a chunk of segments into structured JSON"""
        
        system_prompt = system_prompt or TRANSCRIPT_POLISH_SYSTEM_PROMPT
        user_prompt_tmpl = user_prompt_template or TRANSCRIPT_POLISH_USER_PROMPT

        user_prompt = user_prompt_tmpl.format(
            video_title=video_title,
            context=context,
            chunk_index=chunk_index+1,
            total_chunks=total_chunks,
            chunk_json=chunk_json
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"     Calling API...", end="", flush=True)
        content = self._call_llm(
            messages,
            max_tokens=max_tokens or 8192,
            temperature=temperature
        )
        
        if not content:
            print(" Failed!")
            return None
            
        print(f" Done! ({len(content)} chars)")
        
        # Parse JSON
        import json
        try:
            # Extract JSON from markdown code block if present
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content: # generic block
                content = content.split("```")[-1].split("```")[0].strip()
                
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw content: {content}")
            return None

    def polish(self, raw_transcript: str, video_title: str = "", 
               duration_minutes: float = 0, max_tokens: Optional[int] = None, 
               temperature: Optional[float] = None) -> Optional[str]:
        """
        Polish raw transcript
        
        Strategy:
        1. If text is short (<MAX_SINGLE_TURN), polish in single turn
        2. If text is long, use multi-turn conversation
        
        Args:
            raw_transcript: Raw transcript text from Whisper
            video_title: Optional video title for context
            duration_minutes: Video duration in minutes
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature
            
        Returns:
            Polished text with chapter markers, or None if failed
        """
        if not self.llm_client:
            logger.warning("TextPolisher not available, returning raw transcript")
            return raw_transcript
            
        if not raw_transcript or not raw_transcript.strip():
            logger.warning("Empty transcript, nothing to polish")
            return raw_transcript
        
        text_length = len(raw_transcript)
        logger.info(f"Polishing transcript: {text_length} chars, {duration_minutes:.1f} minutes")
        print(f"  → Text length: {text_length} chars")

        # Check if checkpoint exists (if enabled)
        config = TEXT_LLM_CONFIGS.get(self.provider, {})
        if config.get("enable_checkpoint", False):
            checkpoint = self._load_checkpoint(video_title)
            if checkpoint:
                print(f"\n[RESUME] Found checkpoint for: {video_title}")
                print(f"[RESUME] Total chunks: {checkpoint['metadata'].get('total_chunks', '?')}")
                # For now, just notify user. Full resume logic can be implemented later
                print("[RESUME] Checkpoint found. For now, processing will start fresh.")

        # Use simple single-turn for texts under 4500 chars
        if text_length <= self.MAX_SINGLE_TURN:
            print(f"  → Using single-turn processing...")
            return self._polish_single_turn(raw_transcript, video_title, max_tokens, temperature)

        # Use concurrent/checkpoint processing for long texts (if enabled)
        if config.get("enable_concurrent", False):
            print(f"  → Using concurrent processing with checkpoint...")
            return self._polish_with_checkpoint(raw_transcript, video_title, duration_minutes, max_tokens, temperature)

        # Fall back to multi-turn processing
        print(f"  → Using multi-turn processing...")
        return self._polish_multi_turn(raw_transcript, video_title, duration_minutes, max_tokens, temperature)

    def _polish_single_turn(
        self,
        text: str,
        video_title: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """
        Polish short text in a single turn.

        Args:
            text: Raw transcript text
            video_title: Optional video title
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature

        Returns:
            Polished text, or original text if failed
        """
        title_context = self._get_title_context(video_title, 0)

        system_prompt = """You are a professional transcript proofreader. Your task is to clean up speech-to-text transcripts.

[STRICT REQUIREMENTS]
- You can ONLY proofread and format. You must NOT rewrite, paraphrase, summarize, or condense the original text.
- Every sentence from the original MUST be preserved. You are only making it more readable.

[ALLOWED OPERATIONS]
1. Add punctuation marks (periods, commas, question marks, exclamation marks, colons, etc.)
2. Fix obvious speech recognition errors (homophones, typos)
3. Remove consecutive filler words (like "um um um", "uh uh", "you know you know")
4. Divide into logical paragraphs using blank lines (\\n\\n)

[FORBIDDEN OPERATIONS]
- Do NOT delete any substantive content
- Do NOT change the speaker's original meaning
- Do NOT add information not in the original
- Do NOT rephrase in your own words
- Do NOT summarize or condense
- Do NOT add chapter markers or section headers

[OUTPUT FORMAT]
Proofread content divided into paragraphs with blank lines (\\n\\n) between paragraphs.
Use blank lines to separate different topics or speakers.
Do NOT use ## markers or any section headers."""

        user_prompt = f"""{title_context}Please proofread the following speech transcript:

{text}

Requirements:
- Only add punctuation and paragraph divisions (use \\n\\n for paragraph breaks)
- Preserve ALL original content
- Do NOT add chapter markers or section headers"""

        # Follow DeepSeek API format: system + user messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        print(f"  → Calling LLM (this may take 1-2 minutes)...", end="", flush=True)
        content = self._call_llm(
            messages,
            max_tokens=max_tokens or 8192,
            temperature=temperature
        )

        if content:
            print(" Done!")
            return content

        print(" Failed!")
        return text
    def _polish_multi_turn(self, text: str, video_title: str = "",
                           duration_minutes: float = 0,
                           max_tokens: Optional[int] = None,
                           temperature: Optional[float] = None) -> Optional[str]:
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
            max_tokens: Optional override for max tokens
            temperature: Optional override for temperature

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

            # Base system prompt with all strict requirements
            base_system_prompt = """You are a professional transcript proofreader. Your task is to clean up speech-to-text transcripts.

[STRICT REQUIREMENTS]
- You can ONLY proofread and format. You must NOT rewrite, paraphrase, summarize, or condense the original text.
- Every sentence from the original MUST be preserved. You are only making it more readable.

[ALLOWED OPERATIONS]
1. Add punctuation marks (periods, commas, question marks, exclamation marks, colons, etc.)
2. Fix obvious speech recognition errors (homophones, typos)
3. Remove consecutive filler words (like "um um um", "uh uh", "you know you know")
4. Divide into logical paragraphs using blank lines (\\n\\n)

[FORBIDDEN OPERATIONS]
- Do NOT delete any substantive content
- Do NOT change the speaker's original meaning
- Do NOT add information not in the original
- Do NOT rephrase in your own words
- Do NOT summarize or condense
- Do NOT add chapter markers or section headers

[OUTPUT FORMAT]
Proofread content divided into paragraphs with blank lines (\\n\\n) between paragraphs.
Use blank lines to separate different topics or speakers.
Do NOT use ## markers or any section headers."""

            polished_chunks = []
            previous_content = ""

            for i, chunk in enumerate(chunks):
                print(f"\n  → [{i+1}/{len(chunks)}] Polishing chunk {i+1} ({len(chunk)} chars)...", flush=True)

                # Debug: Log chunk info
                logger.info(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

                try:
                    # Build messages following DeepSeek API format (system + user roles)
                    if i == 0:
                        # First chunk
                        user_content = f"""{self._get_title_context(video_title, duration_minutes)}
Please proofread the following speech transcript (part 1 of {len(chunks)} parts):

{chunk}

Note: Use paragraph breaks (\\n\\n) to separate different topics. Do NOT use ## markers."""
                    else:
                        # Subsequent chunks: provide context from previous chunk
                        previous_ending = self._get_last_section(previous_content)
                        user_content = f"""This is part {i+1} of {len(chunks)} parts of the transcript.

For context, here's how the previous part ended:
{previous_ending}

Please continue proofreading this part:

{chunk}

Note: Use paragraph breaks (\\n\\n). Do NOT use ## markers."""

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
                    polished_chunk = self._call_llm(
                        messages,
                        max_tokens=max_tokens or 8192,
                        temperature=temperature
                    )

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

    def _build_chunk_messages(self, chunk_id: int, chunk: str, chunks: list, video_title: str, total_chunks: int) -> list:
        """Build messages for chunk processing"""
        base_system_prompt = """You are a professional transcript proofreader. Your task is to clean up speech-to-text transcripts.

[STRICT REQUIREMENTS]
- You can ONLY proofread and format. You must NOT rewrite, paraphrase, summarize, or condense the original text.
- Every sentence from the original MUST be preserved. You are only making it more readable.

[ALLOWED OPERATIONS]
1. Add punctuation marks (periods, commas, question marks, exclamation marks, colons, etc.)
2. Fix obvious speech recognition errors (homophones, typos)
3. Remove consecutive filler words (like "um um um", "uh uh", "you know you know")
4. Divide into logical paragraphs using blank lines (\\n\\n)

[FORBIDDEN OPERATIONS]
- Do NOT delete any substantive content
- Do NOT change the speaker's original meaning
- Do NOT add information not in the original
- Do NOT rephrase in your own words
- Do NOT summarize or condense
- Do NOT add chapter markers or section headers

[OUTPUT FORMAT]
Proofread content divided into paragraphs with blank lines (\\n\\n) between paragraphs.
Use blank lines to separate different topics or speakers.
Do NOT use ## markers or any section headers."""

        title_context = self._get_title_context(video_title, 0)

        if chunk_id == 0:
            user_content = f"""{title_context}Please proofread the following speech transcript (part 1 of {total_chunks} parts):

{chunk}

Note: Use paragraph breaks (\\n\\n) to separate different topics. Do NOT use ## markers."""
        else:
            user_content = f"""This is part {chunk_id+1} of {total_chunks} parts of the transcript.

Please continue proofreading this part:

{chunk}

Note: Use paragraph breaks (\\n\\n). Do NOT use ## markers."""

        return [
            {"role": "system", "content": base_system_prompt},
            {"role": "user", "content": user_content}
        ]

    def _process_single_chunk(self, chunk_id: int, chunk: str, messages: list, checkpoint_data: dict, video_title: str,
                            max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Process single chunk with retry and checkpoint saving"""
        from config.settings import TEXT_LLM_CONFIGS
        config = TEXT_LLM_CONFIGS.get(self.provider, {})
        max_retries = config.get("max_chunk_retries", 3)

        for attempt in range(max_retries):
            try:
                print(f"[PROCESSING] Chunk {chunk_id+1} (attempt {attempt+1}/{max_retries})", end="", flush=True)

                polished = self._call_llm(
                    messages,
                    max_tokens=max_tokens or 8192,
                    temperature=temperature
                )

                if polished:
                    # Update checkpoint
                    checkpoint_data["chunks"][chunk_id] = {
                        "chunk_id": chunk_id,
                        "status": "completed",
                        "polished_text": polished
                    }
                    self._save_checkpoint(checkpoint_data, video_title)

                    print(f" Done! ({len(polished)} chars)")
                    return polished

            except Exception as e:
                print(f" Failed!")
                logger.warning(f"Chunk {chunk_id+1} attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(config.get("retry_delay", 5))

        raise Exception(f"Failed to process chunk {chunk_id} after {max_retries} attempts")

    def _polish_with_checkpoint(self, text: str, video_title: str, duration_minutes: float,
                              max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
        """Polish with checkpoint and concurrent processing"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from datetime import datetime
        from config.settings import TEXT_LLM_CONFIGS
        config = TEXT_LLM_CONFIGS.get(self.provider, {})

        chunks = self._split_into_chunks(text)
        total_chunks = len(chunks)

        print(f"\n[CHECKPOINT] Starting polish with {total_chunks} chunks")

        # Initialize checkpoint
        checkpoint_data = {
            "metadata": {
                "video_title": video_title,
                "total_chunks": total_chunks,
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens
            },
            "chunks": [
                {
                    "chunk_id": i,
                    "status": "pending",
                    "polished_text": None
                }
                for i in range(total_chunks)
            ],
            "errors": []
        }

        self._save_checkpoint(checkpoint_data, video_title)

        # Process chunks concurrently
        polished_chunks = [None] * total_chunks
        max_workers = config.get("max_concurrent", 3)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}

            for chunk_id, chunk in enumerate(chunks):
                messages = self._build_chunk_messages(chunk_id, chunk, chunks, video_title, total_chunks)
                future = executor.submit(
                    self._process_single_chunk,
                    chunk_id, chunk, messages, checkpoint_data, video_title, max_tokens, temperature
                )
                futures[future] = chunk_id

            for future in as_completed(futures):
                chunk_id = futures[future]
                try:
                    result = future.result()
                    polished_chunks[chunk_id] = result
                    print(f"[DONE] Chunk {chunk_id+1}/{total_chunks} completed")
                except Exception as e:
                    logger.error(f"Chunk {chunk_id} failed: {e}")
                    checkpoint_data["errors"].append({
                        "chunk_id": chunk_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

        # Merge results
        result = "\n\n".join([c for c in polished_chunks if c])

        # Clean up checkpoint on success
        checkpoint_path = self._get_checkpoint_path(video_title)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            print(f"[CLEANUP] Removed checkpoint file")

        return result

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
