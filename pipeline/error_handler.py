"""
Error handling and retry mechanisms
"""
import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

from utils.logger import get_logger

logger = get_logger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline errors"""
    pass


class DownloadError(PipelineError):
    """Video download failed"""
    pass


class TranscriptionError(PipelineError):
    """Transcription failed"""
    pass


class AnalysisError(PipelineError):
    """Image analysis failed"""
    pass


class GenerationError(PipelineError):
    """Document generation failed"""
    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


def handle_pipeline_error(stage: str):
    """
    Decorator to handle pipeline stage errors

    Args:
        stage: Name of the pipeline stage
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Pipeline stage '{stage}' failed: {e}")
                raise PipelineError(f"{stage} failed: {e}") from e

        return wrapper
    return decorator


class ErrorHandler:
    """
    Centralized error handling for the pipeline
    """

    def __init__(self):
        """Initialize error handler"""
        self.errors = []
        self.warnings = []

    def log_error(self, error: Exception, context: str = ""):
        """Log an error"""
        error_msg = f"{context}: {error}" if context else str(error)
        self.errors.append(error_msg)
        logger.error(error_msg)

    def log_warning(self, message: str, context: str = ""):
        """Log a warning"""
        warning_msg = f"{context}: {message}" if context else message
        self.warnings.append(warning_msg)
        logger.warning(warning_msg)

    def has_errors(self) -> bool:
        """Check if any errors occurred"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings occurred"""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get error/warning summary"""
        lines = []

        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        if not self.errors and not self.warnings:
            lines.append("No errors or warnings")

        return "\n".join(lines)

    def clear(self):
        """Clear all errors and warnings"""
        self.errors.clear()
        self.warnings.clear()


class FallbackHandler:
    """
    Handle fallback mechanisms for API failures
    """

    def __init__(self):
        """Initialize fallback handler"""
        self.fallback_count = {}

    def with_fallback(
        self,
        primary: Callable,
        fallback: Callable,
        fallback_name: str = "fallback"
    ) -> Any:
        """
        Execute function with fallback

        Args:
            primary: Primary function to execute
            fallback: Fallback function
            fallback_name: Name of fallback for logging

        Returns:
            Result from primary or fallback function

        Raises:
            Exception: If both primary and fallback fail
        """
        try:
            return primary()
        except Exception as e:
            logger.warning(f"Primary function failed: {e}")
            logger.info(f"Attempting fallback: {fallback_name}")

            self.fallback_count[fallback_name] = \
                self.fallback_count.get(fallback_name, 0) + 1

            try:
                result = fallback()
                logger.info(f"Fallback {fallback_name} succeeded")
                return result
            except Exception as e2:
                logger.error(f"Fallback {fallback_name} also failed: {e2}")
                raise

    def get_fallback_stats(self) -> dict:
        """Get fallback usage statistics"""
        return self.fallback_count.copy()
