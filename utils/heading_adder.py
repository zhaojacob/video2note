"""
Heading adder for adding section headings to polished text
"""
import logging
from typing import Optional, List, Dict, Any

from utils.llm_client import LLMClient
from config.settings import TEXT_LLM_PROVIDER, TEXT_LLM_CONFIGS

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
        provider = TEXT_LLM_PROVIDER
        config = TEXT_LLM_CONFIGS.get(provider, TEXT_LLM_CONFIGS.get("modelscope", {}))

        self.provider = provider
        self.api_key = api_key or config.get("api_key")
        self.base_url = config.get("base_url")
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens", 8192)
        self.extra_body = config.get("extra_body")

        if not self.api_key:
            logger.warning("Text LLM API key not configured, HeadingAdder will be disabled")
            self.client = None
        else:
            self.client = LLMClient(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                default_max_tokens=self.max_tokens,
                extra_body=self.extra_body,
                timeout=300.0,  # 5 minute timeout
                max_retries=2
            )
            logger.info(f"HeadingAdder initialized: provider={self.provider}, model={self.model}, max_tokens={self.max_tokens}")

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

    def generate_heading_markers(
        self,
        polished_text: str,
        video_title: str = "",
        max_headings: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Generate heading markers without returning full text.

        Strategy:
        1. Split text into paragraphs
        2. Ask DeepSeek to identify topic transitions and generate headings
        3. Return list of headings with paragraph indices

        Args:
            polished_text: Polished transcript text
            video_title: Video title for context
            max_headings: Maximum number of headings to generate

        Returns:
            List of {"title": str, "paragraph_index": int}
        """
        if not self.client:
            logger.warning("HeadingAdder not available")
            return []

        if not polished_text or not polished_text.strip():
            return []

        # Split into paragraphs for indexing
        paragraphs = polished_text.split('\n\n') if '\n\n' in polished_text else polished_text.split('\n')
        num_paragraphs = len(paragraphs)

        # For very long texts, use a summary approach
        paragraph_sample = self._create_paragraph_sample(paragraphs, max_samples=50)

        title_context = f"Video Title: {video_title}\n" if video_title else ""

        system_prompt = f"""You are an expert at organizing content into clear sections.

[TASK]
Analyze the transcript paragraphs and identify natural topic transitions.
Generate meaningful section headings for these transitions.

[OUTPUT FORMAT]
Return ONLY a JSON array of heading markers:
[
  {{"title": "Heading 1", "paragraph_index": 0}},
  {{"title": "Heading 2", "paragraph_index": 5}},
  ...
]

[REQUIREMENTS]
- Title: 5-15 Chinese characters, descriptive and concise
- Paragraph Index: Zero-based index where this heading should be inserted
- First heading should be at paragraph_index 0 (introduction)
- Distribute headings evenly across the content
- Maximum {max_headings} headings
- Use JSON format only, no other text"""

        user_prompt = f"""{title_context}The transcript has {num_paragraphs} paragraphs.

Here are the paragraphs (index: content):
{paragraph_sample}

Generate {max_headings} or fewer heading markers as JSON.

Important: Ensure paragraph_index values are within range 0-{num_paragraphs-1}."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info("Generating heading markers with DeepSeek...")
        content = self._call_deepseek(messages, max_tokens=2000)  # Only need 2K tokens for JSON

        if not content:
            return []

        # Parse JSON response
        import json
        try:
            # Extract JSON array from response
            content = content.strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            content = content.strip()

            markers = json.loads(content)

            # Validate markers
            valid_markers = []
            for marker in markers:
                if isinstance(marker, dict) and "title" in marker and "paragraph_index" in marker:
                    idx = marker["paragraph_index"]
                    if 0 <= idx < num_paragraphs:
                        valid_markers.append({
                            "title": marker["title"],
                            "paragraph_index": idx
                        })

            logger.info(f"Generated {len(valid_markers)} heading markers")
            return valid_markers

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse heading markers: {e}")
            return []

    def _create_paragraph_sample(self, paragraphs: List[str], max_samples: int = 50) -> str:
        """
        Create a sampled representation of paragraphs for API input.

        Args:
            paragraphs: List of paragraph texts
            max_samples: Maximum number of paragraphs to include

        Returns:
            Formatted string with paragraph indices and content
        """
        num_paragraphs = len(paragraphs)

        if num_paragraphs <= max_samples:
            # Include all paragraphs
            sample = paragraphs
        else:
            # Sample evenly: first 10 + evenly distributed + last 10
            step = (num_paragraphs - 20) // (max_samples - 20) if max_samples > 20 else 1
            sample_indices = list(range(10))  # First 10
            sample_indices.extend(range(10, num_paragraphs - 10, step))  # Middle samples
            sample_indices.extend(range(num_paragraphs - 10, num_paragraphs))  # Last 10
            sample_indices = sorted(set(sample_indices))  # Remove duplicates
            sample = [paragraphs[i] for i in sample_indices]

        # Format as "index: content"
        lines = []
        for i, para in enumerate(sample):
            # Truncate long paragraphs
            para_text = para[:150] + "..." if len(para) > 150 else para
            lines.append(f"{i}: {para_text}")

        return "\n".join(lines)

    def _call_deepseek(
        self,
        messages: List[dict],
        max_tokens: Optional[int] = None,
        retry_count: int = 2
    ) -> Optional[str]:
        """
        Call text LLM with retry logic (using LLMClient)

        Args:
            messages: Conversation messages
            max_tokens: Max tokens for response
            retry_count: Number of retries on failure

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
            temperature=0.5,  # Balanced for heading generation
            retry_count=retry_count
        )

        return content
