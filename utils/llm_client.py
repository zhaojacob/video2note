"""
Generic LLM Client wrapper for OpenAI-compatible APIs.
Provides robust error handling, retry logic, and detailed logging.
"""
import logging
import time
from typing import List, Dict, Optional, Any, Union

from openai import OpenAI, APIError, RateLimitError, APITimeoutError, AuthenticationError, APIConnectionError

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Generic client for interacting with LLM APIs (OpenAI compatible).
    
    Features:
    - Robust error handling and retries
    - Detailed payload logging
    - Configurable timeouts and parameters
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str, 
        model: str, 
        timeout: float = 300.0,
        max_retries: int = 3,
        default_max_tokens: int = 4096,
        extra_body: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API
            model: Model identifier
            timeout: Request timeout in seconds
            max_retries: Number of connection retries
            default_max_tokens: Default max tokens for generation
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.extra_body = extra_body
        
        if not self.api_key:
            logger.warning(f"API key not provided for model {model}, client will be disabled")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=timeout,
                max_retries=max_retries
            )
            logger.info(f"LLMClient initialized: model={self.model}, base_url={self.base_url}, timeout={timeout}s")

    def is_available(self) -> bool:
        """Check if client is initialized and available"""
        return self.client is not None

    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        retry_count: int = 3,
        stream: bool = False
    ) -> Optional[str]:
        """
        Call the chat completion API.
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            retry_count: Number of application-level retries
            stream: Whether to stream response (currently unused, defaults to False)
            
        Returns:
            Generated text content or None if failed
        """
        if not self.client:
            logger.error("LLM client not initialized")
            return None

        # Prepare parameters
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if self.extra_body:
            params["extra_body"] = self.extra_body

        # Log request details
        self._log_request(params)

        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"Calling LLM API (attempt {attempt + 1}/{retry_count + 1})")
                
                response = self.client.chat.completions.create(**params)
                
                message = response.choices[0].message
                content = message.content
                reasoning_content = getattr(message, "reasoning_content", None)
                
                # Log success
                logger.info(f"LLM API success: output_chars={len(content) if content else 0}")
                
                # Print full response as requested
                print(f"\n[DEBUG] LLM Response:")
                if reasoning_content:
                    print(reasoning_content)
                    print("\n\n === Final Answer ===\n")
                print(content)
                print("-" * 60)
                
                return content

            except AuthenticationError as e:
                self._handle_auth_error(e)
                return None  # Don't retry auth errors

            except RateLimitError as e:
                if not self._handle_rate_limit(e, attempt, retry_count):
                    return None

            except APITimeoutError as e:
                if not self._handle_timeout(e, attempt, retry_count):
                    return None

            except APIConnectionError as e:
                if not self._handle_connection_error(e, attempt, retry_count):
                    return None

            except APIError as e:
                if not self._handle_api_error(e, attempt, retry_count):
                    return None

            except Exception as e:
                if not self._handle_unexpected_error(e, attempt, retry_count):
                    return None

        return None

    def _log_request(self, params: Dict[str, Any]):
        """Log detailed request information"""
        messages = params.get("messages", [])
        input_chars = sum(len(str(m.get("content", ""))) for m in messages)
        
        logger.info(f"LLM Request: model={self.model}, max_tokens={params.get('max_tokens')}, input_chars={input_chars}")
        
        print(f"\n[DEBUG] LLM Request Payload:")
        print(f"  Model: {self.model}")
        print(f"  Max Tokens: {params.get('max_tokens')}")
        print(f"  Temperature: {params.get('temperature')}")
        print(f"  Messages: {len(messages)} messages")
        if params.get("extra_body"):
            print(f"  Extra Body: {params.get('extra_body')}")
        
        if messages:
            last_msg = messages[-1]
            content = str(last_msg.get("content", ""))
            preview = content[:500] + "..." if len(content) > 500 else content
            print(f"  Last Message Preview: {preview}")
            print(f"  Total Input Chars: {input_chars}")
        print("-" * 60)

    def _handle_auth_error(self, e: Exception):
        logger.error(f"LLM Auth Error: {e}")
        print(f"\n[ERROR] Authentication failed: {e}")
        print(f"[ERROR] Please check your API key")

    def _handle_rate_limit(self, e: Exception, attempt: int, max_retries: int) -> bool:
        logger.warning(f"LLM Rate Limit (attempt {attempt + 1}): {e}")
        print(f"\n[WARNING] Rate limit exceeded")
        
        if attempt < max_retries:
            wait_time = 60
            print(f"[INFO] Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            return True
        return False

    def _handle_timeout(self, e: Exception, attempt: int, max_retries: int) -> bool:
        logger.warning(f"LLM Timeout (attempt {attempt + 1}): {e}")
        print(f"\n[WARNING] Request timeout")
        
        if attempt < max_retries:
            wait_time = (attempt + 1) * 20  # Exponential backoff
            print(f"[INFO] Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return True
        return False

    def _handle_connection_error(self, e: Exception, attempt: int, max_retries: int) -> bool:
        logger.warning(f"LLM Connection Error (attempt {attempt + 1}): {e}")
        print(f"\n[WARNING] Connection failed: {e}")
        
        if attempt < max_retries:
            wait_time = (attempt + 1) * 10
            print(f"[INFO] Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return True
        return False

    def _handle_api_error(self, e: APIError, attempt: int, max_retries: int) -> bool:
        status_code = getattr(e, 'status_code', 'unknown')
        logger.error(f"LLM API Error (attempt {attempt + 1}): status={status_code}, msg={e}")
        print(f"\n[ERROR] API Error (status={status_code}): {e}")
        
        # Don't retry client errors (4xx) except 429 (handled separately)
        if isinstance(status_code, int) and 400 <= status_code < 500 and status_code != 429:
            return False
            
        if attempt < max_retries:
            wait_time = (attempt + 1) * 5
            print(f"[INFO] Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return True
        return False

    def _handle_unexpected_error(self, e: Exception, attempt: int, max_retries: int) -> bool:
        logger.error(f"LLM Unexpected Error (attempt {attempt + 1}): {type(e).__name__}: {e}")
        print(f"\n[ERROR] Unexpected error: {e}")
        
        if attempt < max_retries:
            wait_time = (attempt + 1) * 5
            print(f"[INFO] Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return True
        return False
