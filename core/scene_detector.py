"""
Scene detection for video frames
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

import cv2
import numpy as np
from scenedetect import detect, ContentDetector, ThresholdDetector
from scenedetect.scene_manager import save_images

from utils.logger import get_logger
from utils.file_handler import ensure_dir
from config.settings import FRAME_CONFIG, OUTPUT_DIRS

logger = get_logger(__name__)


class SceneDetector:
    """Detect scene changes in video"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize scene detector

        Args:
            output_dir: Output directory for scene frames
        """
        self.output_dir = output_dir or OUTPUT_DIRS["frames"]
        ensure_dir(self.output_dir)

    def detect_scenes(
        self,
        video_path: str | Path,
        threshold: float = None,
        min_scene_length: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Detect scenes in video

        Args:
            video_path: Path to video file
            threshold: Scene detection threshold (higher = fewer scenes)
            min_scene_length: Minimum scene length in frames

        Returns:
            List of scene dictionaries with start/end times
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        threshold = threshold or FRAME_CONFIG.get("scene_threshold", 30.0)

        logger.info(f"Detecting scenes in: {video_path.name}")
        logger.info(f"Threshold: {threshold}")

        try:
            # Detect scenes
            scene_list = detect(
                str(video_path),
                ContentDetector(
                    threshold=threshold,
                    min_scene_len=min_scene_length
                )
            )

            # Convert to list of dictionaries
            scenes = []
            for i, scene in enumerate(scene_list):
                start_time = scene.get_timecodes()[0].get_seconds()
                end_time = scene.get_timecodes()[1].get_seconds()

                scenes.append({
                    "index": i,
                    "start": start_time,
                    "end": end_time,
                    "duration": end_time - start_time,
                    "start_frame": scene.get_frames()[0],
                    "end_frame": scene.get_frames()[1],
                })

            logger.info(f"Detected {len(scenes)} scenes")

            return scenes

        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            # Fallback: return entire video as one scene
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()

            return [{
                "index": 0,
                "start": 0.0,
                "end": duration,
                "duration": duration,
                "start_frame": 0,
                "end_frame": frame_count,
            }]

    def extract_scene_frames(
        self,
        video_path: str | Path,
        scenes: List[Dict[str, Any]],
        frame_position: str = "middle"
    ) -> List[Dict[str, Any]]:
        """
        Extract representative frames from scenes

        Args:
            video_path: Path to video file
            scenes: List of scene dictionaries
            frame_position: Position of frame to extract (start/middle/end)

        Returns:
            List of frame dictionaries with paths
        """
        video_path = Path(video_path)

        logger.info(f"Extracting {len(scenes)} scene frames")

        frames = []
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            for scene in scenes:
                # Determine frame position
                if frame_position == "start":
                    timestamp = scene["start"]
                elif frame_position == "end":
                    timestamp = scene["end"]
                else:  # middle
                    timestamp = (scene["start"] + scene["end"]) / 2

                # Calculate frame number
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_number = int(timestamp * fps)

                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if ret:
                    # Save frame
                    frame_filename = f"scene_{scene['index']:04d}.jpg"
                    frame_path = self.output_dir / frame_filename

                    cv2.imwrite(str(frame_path), frame)

                    frames.append({
                        "path": str(frame_path),
                        "timestamp": timestamp,
                        "scene_index": scene["index"],
                        "type": "scene",
                    })

                else:
                    logger.warning(f"Failed to extract frame at {timestamp:.2f}s")

            logger.info(f"Extracted {len(frames)} frames")

            return frames

        finally:
            cap.release()

    def detect_with_threshold(
        self,
        video_path: str | Path,
        threshold: float = 27.0
    ) -> List[Dict[str, Any]]:
        """
        Detect scenes using threshold detector

        Args:
            video_path: Path to video file
            threshold: Threshold value (default 27.0)

        Returns:
            List of scene dictionaries
        """
        video_path = Path(video_path)

        logger.info(f"Using threshold detector: {threshold}")

        scene_list = detect(
            str(video_path),
            ThresholdDetector(threshold=threshold)
        )

        scenes = []
        for i, scene in enumerate(scene_list):
            start_time = scene.get_timecodes()[0].get_seconds()
            end_time = scene.get_timecodes()[1].get_seconds()

            scenes.append({
                "index": i,
                "start": start_time,
                "end": end_time,
                "duration": end_time - start_time,
            })

        logger.info(f"Detected {len(scenes)} scenes with threshold detector")

        return scenes


def detect_scenes(video_path: str | Path) -> List[Dict[str, Any]]:
    """
    Convenience function to detect scenes

    Args:
        video_path: Path to video file

    Returns:
        List of scene dictionaries
    """
    detector = SceneDetector()
    return detector.detect_scenes(video_path)
