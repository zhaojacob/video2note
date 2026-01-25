"""
Data validation utilities
"""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_video_url(url: str) -> Dict[str, Any]:
    """
    Validate and detect video platform from URL

    Args:
        url: Video URL

    Returns:
        Dictionary with platform and validation status
    """
    if not validate_url(url):
        return {
            "valid": False,
            "platform": None,
            "error": "Invalid URL format"
        }

    # YouTube patterns
    youtube_patterns = [
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
    ]

    # Bilibili patterns
    bilibili_patterns = [
        r'bilibili\.com/video/',
        r'b23\.tv/',
    ]

    for pattern in youtube_patterns:
        if re.search(pattern, url):
            return {
                "valid": True,
                "platform": "youtube",
                "url": url
            }

    for pattern in bilibili_patterns:
        if re.search(pattern, url):
            return {
                "valid": True,
                "platform": "bilibili",
                "url": url
            }

    return {
        "valid": False,
        "platform": None,
        "error": "Unsupported video platform"
    }


def validate_transcript_segments(segments: List[Dict]) -> bool:
    """
    Validate transcript segments structure

    Args:
        segments: List of transcript segments

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(segments, list):
        logger.error("Transcript segments must be a list")
        return False

    required_keys = {"start", "end", "text"}

    for i, segment in enumerate(segments):
        if not isinstance(segment, dict):
            logger.error(f"Segment {i} is not a dictionary")
            return False

        if not required_keys.issubset(segment.keys()):
            logger.error(f"Segment {i} missing required keys: {required_keys}")
            return False

        if not isinstance(segment["text"], str) or not segment["text"].strip():
            logger.error(f"Segment {i} has invalid or empty text")
            return False

        if not isinstance(segment["start"], (int, float)) or segment["start"] < 0:
            logger.error(f"Segment {i} has invalid start time")
            return False

        if not isinstance(segment["end"], (int, float)) or segment["end"] <= segment["start"]:
            logger.error(f"Segment {i} has invalid end time")
            return False

    return True


def validate_frame_data(frame: Dict) -> bool:
    """
    Validate frame data structure

    Args:
        frame: Frame data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = {"path", "timestamp"}

    if not isinstance(frame, dict):
        logger.error("Frame data must be a dictionary")
        return False

    if not required_keys.issubset(frame.keys()):
        logger.error(f"Frame missing required keys: {required_keys}")
        return False

    # Validate timestamp
    if not isinstance(frame["timestamp"], (int, float)) or frame["timestamp"] < 0:
        logger.error(f"Frame has invalid timestamp: {frame['timestamp']}")
        return False

    return True


def validate_structured_data(data: Dict) -> bool:
    """
    Validate structured note data

    Args:
        data: Structured data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = {"title", "summary", "sections"}

    if not isinstance(data, dict):
        logger.error("Structured data must be a dictionary")
        return False

    if not required_keys.issubset(data.keys()):
        logger.error(f"Structured data missing required keys: {required_keys}")
        return False

    # Validate sections
    if not isinstance(data["sections"], list):
        logger.error("Sections must be a list")
        return False

    for i, section in enumerate(data["sections"]):
        if not isinstance(section, dict):
            logger.error(f"Section {i} is not a dictionary")
            return False

        if "title" not in section:
            logger.error(f"Section {i} missing title")
            return False

        if "content" not in section:
            logger.error(f"Section {i} missing content")
            return False

    return True


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text by removing excessive whitespace and controlling length

    Args:
        text: Text to sanitize
        max_length: Maximum length (None for no limit)

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Control length
    if max_length and len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Text truncated to {max_length} characters")

    return text


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format

    Args:
        api_key: API key string

    Returns:
        True if format appears valid, False otherwise
    """
    if not isinstance(api_key, str):
        return False

    # Basic validation: should be reasonably long
    if len(api_key) < 10:
        return False

    # Should not contain whitespace
    if re.search(r'\s', api_key):
        return False

    return True
