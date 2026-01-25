"""
File handling utilities
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_directory(path: str | Path, pattern: str = "*") -> int:
    """
    Clean all files matching pattern in directory

    Args:
        path: Directory path
        pattern: Glob pattern for files to remove

    Returns:
        Number of files removed
    """
    path = Path(path)
    if not path.exists():
        return 0

    count = 0
    for file in path.glob(pattern):
        if file.is_file():
            file.unlink()
            count += 1
            logger.debug(f"Removed file: {file}")

    return count


def get_file_size(file_path: str | Path) -> int:
    """Get file size in bytes"""
    return Path(file_path).stat().st_size


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def find_files(
    directory: str | Path,
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    Find files matching pattern in directory

    Args:
        directory: Directory to search
        pattern: Glob pattern
        recursive: Search recursively

    Returns:
        List of file paths
    """
    directory = Path(directory)
    if recursive:
        return list(directory.rglob(pattern))
    return list(directory.glob(pattern))


def copy_file(src: str | Path, dst: str | Path) -> Path:
    """Copy file from src to dst"""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    logger.debug(f"Copied {src} to {dst}")
    return dst


def move_file(src: str | Path, dst: str | Path) -> Path:
    """Move file from src to dst"""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    logger.debug(f"Moved {src} to {dst}")
    return dst


def get_unique_filename(
    base_path: str | Path,
    extension: str = ""
) -> Path:
    """
    Get a unique filename by adding suffix if file exists

    Args:
        base_path: Base file path
        extension: File extension (e.g., ".txt")

    Returns:
        Unique file path
    """
    base_path = Path(base_path)

    if extension and not base_path.suffix:
        base_path = base_path.with_suffix(extension)

    counter = 1
    unique_path = base_path

    while unique_path.exists():
        stem = base_path.stem
        unique_path = base_path.parent / f"{stem}_{counter}{base_path.suffix}"
        counter += 1

    return unique_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    return filename or "unnamed"


def get_video_info(file_path: str | Path) -> dict:
    """
    Get video file information

    Args:
        file_path: Path to video file

    Returns:
        Dictionary with video information
    """
    import cv2

    file_path = Path(file_path)

    cap = cv2.VideoCapture(str(file_path))

    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {file_path}")

    info = {
        "path": str(file_path),
        "filename": file_path.name,
        "size": get_file_size(file_path),
        "size_formatted": format_size(get_file_size(file_path)),
    }

    # Get video properties
    info["fps"] = cap.get(cv2.CAP_PROP_FPS)
    info["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    info["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    info["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0

    cap.release()

    return info
