"""
Intelligent frame extraction from video
"""
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

import cv2
import imagehash
import numpy as np
from PIL import Image
from pytesseract import pytesseract

from utils.logger import get_logger
from utils.file_handler import ensure_dir, sanitize_filename
from config.settings import FRAME_CONFIG, OUTPUT_DIRS

logger = get_logger(__name__)


class FrameExtractor:
    """
    Extract frames from video with intelligent strategies:
    - Scene-based extraction
    - Transcript-aligned extraction
    - Content-aware extraction (text, formulas, code)
    - Deduplication
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize frame extractor

        Args:
            output_dir: Output directory for frames
        """
        self.output_dir = output_dir or OUTPUT_DIRS["frames"]
        ensure_dir(self.output_dir)

    def extract_frames_by_interval(
        self,
        video_path: str | Path,
        interval_sec: float = None,
        max_frames: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract frames at regular intervals

        Args:
            video_path: Path to video file
            interval_sec: Interval in seconds between frames (auto-calculated if None)
            max_frames: Maximum number of frames to extract (default: 5)

        Returns:
            List of frame dictionaries
        """
        video_path = Path(video_path)

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # Auto-calculate interval to get exactly max_frames evenly distributed
            if interval_sec is None:
                interval_sec = duration / (max_frames + 1)  # +1 to avoid first/last frame edges
            
            logger.info(f"Extracting frames every {interval_sec:.1f} seconds (max {max_frames} frames)")

            interval_frames = int(interval_sec * fps)
            frames = []

            for frame_number in range(0, total_frames, interval_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if ret:
                    timestamp = frame_number / fps

                    frame_filename = f"frame_{frame_number:06d}.jpg"
                    frame_path = self.output_dir / frame_filename

                    cv2.imwrite(str(frame_path), frame)

                    frames.append({
                        "path": str(frame_path),
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                        "type": "interval",
                    })

                else:
                    logger.warning(f"Failed to extract frame {frame_number}")

            # Limit to max_frames (evenly sample if exceeded)
            if len(frames) > max_frames:
                indices = np.linspace(0, len(frames) - 1, max_frames, dtype=int)
                frames = [frames[i] for i in indices]
                logger.info(f"Sampled down to {len(frames)} frames")

            logger.info(f"Extracted {len(frames)} frames")

            return frames

        finally:
            cap.release()

    def extract_frames_by_transcript(
        self,
        video_path: str | Path,
        transcript: List[Dict[str, Any]],
        interval_sec: float = 10.0,
        max_frames: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract frames aligned with transcript segments

        Args:
            video_path: Path to video file
            transcript: List of transcript segments
            interval_sec: Minimum interval between frames
            max_frames: Maximum number of frames to extract (default: 5)

        Returns:
            List of frame dictionaries
        """
        video_path = Path(video_path)

        logger.info(f"Extracting frames aligned with {len(transcript)} transcript segments (max {max_frames})")

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            frames = []
            last_timestamp = -interval_sec

            for segment in transcript:
                timestamp = (segment["start"] + segment["end"]) / 2

                # Check minimum interval
                if timestamp - last_timestamp < interval_sec:
                    continue

                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_number = int(timestamp * fps)

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if ret:
                    frame_filename = f"transcript_{len(frames):04d}.jpg"
                    frame_path = self.output_dir / frame_filename

                    cv2.imwrite(str(frame_path), frame)

                    frames.append({
                        "path": str(frame_path),
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                        "type": "transcript",
                        "segment_text": segment["text"][:100],  # Store first 100 chars
                    })

                    last_timestamp = timestamp

                else:
                    logger.warning(f"Failed to extract frame at {timestamp:.2f}s")

            # Randomly sample if exceeded max_frames
            if len(frames) > max_frames:
                sampled_frames = random.sample(frames, max_frames)
                # Sort by timestamp to maintain chronological order
                sampled_frames.sort(key=lambda x: x["timestamp"])
                logger.info(f"Randomly sampled {len(sampled_frames)} frames from {len(frames)} candidates")
                frames = sampled_frames

            logger.info(f"Extracted {len(frames)} frames from transcript")

            return frames

        finally:
            cap.release()

    def detect_special_content(self, frame_path: str | Path) -> Dict[str, Any]:
        """
        Detect special content in frame (text, formulas, code, etc.)

        Args:
            frame_path: Path to frame image

        Returns:
            Dictionary with detection results
        """
        frame_path = Path(frame_path)

        if not frame_path.exists():
            raise FileNotFoundError(f"Frame not found: {frame_path}")

        logger.debug(f"Detecting content in: {frame_path.name}")

        # Load image
        image = cv2.imread(str(frame_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = {
            "has_text": False,
            "has_formula": False,
            "has_code": False,
            "has_chart": False,
            "text_content": "",
        }

        # Try OCR if available
        try:
            text = pytesseract.image_to_string(gray, lang='chi_sim+eng')
            result["has_text"] = len(text.strip()) > 50  # Has significant text

            # Detect formula indicators
            formula_indicators = ['∑', '∫', '∂', '√', '∞', '±', '≤', '≥', '≈', '≠']
            result["has_formula"] = any(indicator in text for indicator in formula_indicators)

            # Detect code indicators
            code_indicators = ['def ', 'class ', 'import ', 'function', '=>', 'var ', 'let ']
            result["has_code"] = any(indicator in text for indicator in code_indicators)

            result["text_content"] = text[:500]  # Store first 500 chars

        except Exception as e:
            logger.debug(f"OCR not available or failed: {e}")

        # Detect charts using edge detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Count rectangular contours (potential charts/tables)
        rect_count = 0
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                rect_count += 1

        result["has_chart"] = rect_count > 3

        logger.debug(f"Content detection: text={result['has_text']}, "
                    f"formula={result['has_formula']}, "
                    f"code={result['has_code']}, "
                    f"chart={result['has_chart']}")

        return result

    def deduplicate_frames(
        self,
        frame_paths: List[str | Path],
        threshold: float = None
    ) -> List[str]:
        """
        Remove duplicate frames using perceptual hashing

        Args:
            frame_paths: List of frame paths
            threshold: Similarity threshold (0-1)

        Returns:
            List of unique frame paths
        """
        threshold = threshold or FRAME_CONFIG.get("similarity_threshold", 0.95)

        logger.info(f"Deduplicating {len(frame_paths)} frames with threshold {threshold}")

        if len(frame_paths) == 0:
            return []

        # Calculate hashes
        hashes = []
        for frame_path in frame_paths:
            try:
                image = Image.open(frame_path)
                img_hash = imagehash.phash(image)
                hashes.append((str(frame_path), img_hash))
            except Exception as e:
                logger.warning(f"Failed to hash {frame_path}: {e}")

        # Remove duplicates
        unique_frames = []
        unique_hashes = []

        for frame_path, img_hash in hashes:
            is_duplicate = False

            for unique_hash in unique_hashes:
                similarity = 1 - (img_hash - unique_hash) / 64  # Normalize to 0-1

                if similarity >= threshold:
                    is_duplicate = True
                    logger.debug(f"Duplicate found: {frame_path} "
                               f"(similarity: {similarity:.2f})")
                    break

            if not is_duplicate:
                unique_frames.append(frame_path)
                unique_hashes.append(img_hash)

        logger.info(f"Removed {len(frame_paths) - len(unique_frames)} duplicates")

        return unique_frames

    def extract_key_frames(
        self,
        video_path: str | Path,
        max_frames: int = None
    ) -> List[Dict[str, Any]]:
        """
        Extract key frames using scene detection

        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to extract

        Returns:
            List of frame dictionaries
        """
        from core.scene_detector import SceneDetector

        max_frames = max_frames or FRAME_CONFIG.get("max_frames_per_minute", 6)

        logger.info(f"Extracting key frames (max: {max_frames})")

        # Detect scenes
        scene_detector = SceneDetector(self.output_dir)
        scenes = scene_detector.detect_scenes(video_path)

        # Limit number of frames
        if len(scenes) > max_frames:
            # Sample scenes evenly
            indices = np.linspace(0, len(scenes) - 1, max_frames, dtype=int)
            scenes = [scenes[i] for i in indices]

        # Extract frames from scenes
        frames = scene_detector.extract_scene_frames(video_path, scenes)

        logger.info(f"Extracted {len(frames)} key frames")

        return frames


def extract_frames(
    video_path: str | Path,
    strategy: str = "interval",
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract frames

    Args:
        video_path: Path to video file
        strategy: Extraction strategy (interval/transcript/keyframes)
        **kwargs: Additional arguments

    Returns:
        List of frame dictionaries
    """
    extractor = FrameExtractor()

    if strategy == "interval":
        return extractor.extract_frames_by_interval(video_path, **kwargs)
    elif strategy == "transcript":
        return extractor.extract_frames_by_transcript(video_path, **kwargs)
    elif strategy == "keyframes":
        return extractor.extract_key_frames(video_path, **kwargs)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
