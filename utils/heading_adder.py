"""
Heading adder for adding section headings to polished text
"""
import logging
from typing import Optional, List
from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError, AuthenticationError

from config.settings import DEEPSEEK_CONFIG

logger = logging.getLogger(__name__)


class HeadingAdder:
    """
    Add section headings to polished transcript text.

    Strategy:
    - Analyze the full polished text to understand content structure
    - Generate meaningful section headings at topic transitions
    - Use ## markers for headings (for compatibility with existing parsers)

    Model: deepseek-chat (128K context, 8K max output)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HeadingAdder with DeepSeek API

        Args:
            api_key: DeepSeek API key (optional, uses config if not provided)
        """
        self.api_key = api_key or DEEPSEEK_CONFIG.get("api_key")
        self.base_url = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
        self.model = DEEPSEEK_CONFIG.get("model", "deepseek-chat")
        self.max_tokens = DEEPSEEK_CONFIG.get("max_tokens", 8192)

        if not self.api_key:
            logger.warning("DeepSeek API key not configured, HeadingAdder will be disabled")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=300.0,  # 5 minute timeout
                max_retries=2
            )
            logger.info(f"HeadingAdder initialized: model={self.model}, max_tokens={self.max_tokens}")

    def is_available(self) -> bool:
        """Check if adder is available"""
        return self.client is not None

    def add_headings(
        self,
        polished_text: str,
        video_title: str = "",
        max_headings: int = 15
    ) -> Optional[str]:
        """
        Add section headings to polished text.

        Args:
            polished_text: Polished transcript text (with \\n\\n paragraph breaks)
            video_title: Video title for context
            max_headings: Maximum number of headings to add (default: 15)

        Returns:
            Text with ## headings added, or None if failed
        """
        if not self.client:
            logger.warning("HeadingAdder not available, returning original text")
            return polished_text

        if not polished_text or not polished_text.strip():
            logger.warning("Empty text, nothing to add headings to")
            return polished_text

        # Truncate very long texts to fit context window
        max_input_chars = 50000  # ~50K chars
        if len(polished_text) > max_input_chars:
            polished_text = polished_text[:max_input_chars] + "\n\n[内容因长度限制被截断]"
            logger.info(f"Text truncated to {max_input_chars} characters for heading generation")

        title_context = f"视频标题：《{video_title}》\n" if video_title else ""

        system_prompt = """You are an expert at organizing content into clear sections. Your task is to add meaningful section headings to a polished transcript.

[REQUIREMENTS]
1. Analyze the entire text to understand the content flow and topic transitions
2. Add section headings at natural topic transitions using ## markers
3. Headings should be concise (5-15 characters) and descriptive
4. Number of headings should be proportional to text length (typically 5-15 headings for a full video)
5. Use ## Heading format (same level for all headings)
6. Preserve ALL original content and paragraph structure

[HEADING QUALITY]
- Headings should reflect the main topic of the following section
- Use clear, professional language
- Avoid generic headings like "Introduction" or "Conclusion"
- Each heading should cover 2-5 paragraphs typically

[FORBIDDEN]
- Do NOT modify any original content
- Do NOT change paragraph structure
- Do NOT add sub-headings (### or ####)
- Do NOT remove any text

[OUTPUT FORMAT]
## First Heading
Original paragraph content...

More paragraph content...

## Second Heading
More paragraph content..."""

        user_prompt = f"""{title_context}Please add section headings to the following polished transcript:

{polished_text}

Requirements:
- Add {max_headings} or fewer section headings (## format)
- Place headings at natural topic transitions
- Preserve all original content and paragraphs
- Use clear, descriptive headings (5-15 Chinese characters)"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info("Adding headings with DeepSeek...")
        content = self._call_deepseek(messages, max_tokens=self.max_tokens)

        if content:
            logger.info(f"Headings added successfully ({len(content)} chars)")
            return content
        else:
            logger.warning("Failed to add headings, returning original text")
            return polished_text

    def _call_deepseek(
        self,
        messages: List[dict],
        max_tokens: Optional[int] = None,
        retry_count: int = 2
    ) -> Optional[str]:
        """
        Call DeepSeek API with retry logic

        Args:
            messages: Conversation messages
            max_tokens: Max tokens for response
            retry_count: Number of retries on failure

        Returns:
            Response content string, or None if failed
        """
        if not self.client:
            logger.error("DeepSeek client not initialized")
            return None

        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": 0.5,  # Balanced for heading generation
            "stream": False,
        }

        input_chars = sum(len(m.get("content", "")) for m in messages)
        logger.info(f"DeepSeek request: input_chars={input_chars}")

        for attempt in range(retry_count + 1):
            try:
                response = self.client.chat.completions.create(**params)
                content = response.choices[0].message.content

                logger.info(f"DeepSeek success: output_chars={len(content) if content else 0}")
                return content

            except AuthenticationError as e:
                logger.error(f"Authentication Error: {e}")
                return None

            except RateLimitError as e:
                logger.warning(f"Rate Limit Error (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    import time
                    time.sleep(60)
                else:
                    return None

            except (APITimeoutError, APIError) as e:
                logger.warning(f"API Error (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    import time
                    time.sleep(10)
                else:
                    return None

            except Exception as e:
                logger.error(f"Unexpected Error: {type(e).__name__}: {e}")
                if attempt < retry_count:
                    import time
                    time.sleep(5)
                else:
                    return None

        return None
