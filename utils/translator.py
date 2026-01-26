"""
Translator using DeepSeek API for bilingual output
"""
from typing import List, Dict, Any, Optional

from utils.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "ru": "Русский",
}


class Translator:
    """Translate text using text LLM"""

    def __init__(self):
        """Initialize translator with text LLM API"""
        from config.settings import TEXT_LLM_PROVIDER, TEXT_LLM_CONFIGS

        provider = TEXT_LLM_PROVIDER
        config = TEXT_LLM_CONFIGS.get(provider, TEXT_LLM_CONFIGS.get("modelscope", {}))

        self.provider = provider
        self.api_key = config.get("api_key") or ""
        self.model = config.get("model")
        self.base_url = config.get("base_url")
        self.extra_body = config.get("extra_body")
        self.max_tokens = config.get("max_tokens", 8192)

        if not self.api_key:
            logger.warning("Text LLM API key not found. Translation will be skipped.")
            self.client = None
        else:
            self.client = LLMClient(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                default_max_tokens=self.max_tokens,
                extra_body=self.extra_body
            )
            logger.info(f"Translator initialized: provider={self.provider}, model={self.model}")

    def is_available(self) -> bool:
        """Check if translator is available"""
        return self.client is not None

    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from code"""
        return SUPPORTED_LANGUAGES.get(lang_code, lang_code)

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> str:
        """
        Translate a single text to target language
        
        Args:
            text: Text to translate
            target_lang: Target language code (zh/en/ja/ko etc.)
            source_lang: Source language code (auto-detect if None)
            
        Returns:
            Translated text
        """
        if not self.client:
            logger.warning("Translator not initialized, returning original text")
            return ""
        
        if not text or len(text.strip()) < 2:
            return ""
        
        target_name = self.get_language_name(target_lang)
        
        prompt = f"""Translate the following text to {target_name}.

Rules:
1. Preserve the original meaning and tone
2. Keep proper nouns, technical terms, and numbers as appropriate
3. Output ONLY the translated text, no explanations or prefixes
4. If the text is already in {target_name}, return it as is

Text to translate:
{text}

Translation:"""

        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate text accurately to {target_name}. Output only the translation, nothing else."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            translated = self.client.chat_completion(
                messages=messages,
                max_tokens=len(text) * 3,
                temperature=0.1,
                retry_count=2
            )

            return translated.strip() if translated else ""

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return ""

    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        batch_size: int = 10
    ) -> List[str]:
        """
        Translate multiple texts in batches to reduce API calls
        
        Args:
            texts: List of texts to translate
            target_lang: Target language code
            batch_size: Number of texts per API call
            
        Returns:
            List of translated texts (same order as input)
        """
        if not self.client:
            logger.warning("Translator not initialized")
            return [""] * len(texts)
        
        if not texts:
            return []
        
        target_name = self.get_language_name(target_lang)
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Skip empty texts but preserve positions
            non_empty_indices = []
            non_empty_texts = []
            for j, text in enumerate(batch):
                if text and len(text.strip()) >= 2:
                    non_empty_indices.append(j)
                    non_empty_texts.append(text)
            
            if not non_empty_texts:
                results.extend([""] * len(batch))
                continue
            
            # Create numbered format for batch translation
            numbered_text = "\n".join([
                f"[{idx+1}] {text}" 
                for idx, text in enumerate(non_empty_texts)
            ])
            
            prompt = f"""Translate each numbered item to {target_name}.

Rules:
1. Keep the [number] prefix for each translation
2. Translate each item on its own line
3. Preserve meaning and tone
4. Output ONLY the translations with numbers, no explanations

Items to translate:
{numbered_text}

Translations:"""

            try:
                messages = [
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate each numbered item to {target_name}. Keep the [number] format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                response_text = self.client.chat_completion(
                    messages=messages,
                    max_tokens=sum(len(t) * 3 for t in non_empty_texts),
                    temperature=0.1,
                    retry_count=2
                )

                response_text = response_text.strip() if response_text else ""

                # Parse response - extract translations by number
                translations = self._parse_batch_response(response_text, len(non_empty_texts))

                # Reconstruct full batch with empty strings for skipped items
                batch_results = [""] * len(batch)
                for j, idx in enumerate(non_empty_indices):
                    if j < len(translations):
                        batch_results[idx] = translations[j]

                results.extend(batch_results)

            except Exception as e:
                logger.error(f"Batch translation failed: {e}")
                results.extend([""] * len(batch))
        
        return results

    def _parse_batch_response(self, response: str, expected_count: int) -> List[str]:
        """Parse batch translation response"""
        translations = []
        lines = response.strip().split("\n")
        
        current_num = 1
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a number marker
            import re
            match = re.match(r'^\[(\d+)\]\s*(.*)$', line)
            
            if match:
                # Save previous if exists
                if current_text:
                    translations.append(" ".join(current_text))
                    current_text = []
                
                # Start new translation
                current_num = int(match.group(1))
                text = match.group(2).strip()
                if text:
                    current_text.append(text)
            else:
                # Continuation of previous
                current_text.append(line)
        
        # Don't forget the last one
        if current_text:
            translations.append(" ".join(current_text))
        
        # Pad if needed
        while len(translations) < expected_count:
            translations.append("")
        
        return translations[:expected_count]

    def translate_title(self, title: str, target_lang: str) -> str:
        """Translate video title"""
        return self.translate_text(title, target_lang)

    def translate_summary(self, summary: str, target_lang: str) -> str:
        """Translate summary text"""
        if not summary:
            return ""
        return self.translate_text(summary, target_lang)

    def translate_transcript_segments(
        self,
        segments: List[Dict[str, Any]],
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """
        Translate transcript segments, adding translated field
        
        Args:
            segments: List of transcript segments with 'text' field
            target_lang: Target language code
            
        Returns:
            Segments with added 'text_translated' field
        """
        if not segments:
            return segments
        
        # Extract texts
        texts = [seg.get("text", "") for seg in segments]
        
        # Batch translate
        print(f"[Translating] {len(texts)} segments to {self.get_language_name(target_lang)}...")
        translations = self.translate_batch(texts, target_lang)
        
        # Add translations to segments
        for seg, translation in zip(segments, translations):
            seg["text_translated"] = translation
        
        return segments


def get_supported_languages() -> Dict[str, str]:
    """Get dictionary of supported language codes and names"""
    return SUPPORTED_LANGUAGES.copy()
