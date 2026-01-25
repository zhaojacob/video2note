"""
Audio extraction from video files
"""
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks

from utils.logger import get_logger
from utils.file_handler import ensure_dir
from config.settings import OUTPUT_DIRS

logger = get_logger(__name__)


class AudioExtractor:
    """Extract audio from video files"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize audio extractor

        Args:
            output_dir: Output directory for audio files
        """
        self.output_dir = output_dir or OUTPUT_DIRS["audio"]
        ensure_dir(self.output_dir)

    def extract(
        self,
        video_path: str | Path,
        audio_format: str = "wav",
        sample_rate: int = 16000,
        channels: int = 1,
        bitrate: str = "64k"
    ) -> Path:
        """
        Extract audio from video file

        Args:
            video_path: Path to video file
            audio_format: Output audio format (wav, mp3, etc.)
            sample_rate: Audio sample rate in Hz (16000 for Whisper)
            channels: Number of audio channels (1 for mono)
            bitrate: Audio bitrate for compressed formats

        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Determine output path
        output_filename = f"{video_path.stem}.{audio_format}"
        output_path = self.output_dir / output_filename

        # Check if audio already exists (cache)
        if output_path.exists():
            logger.info(f"Audio already exists, skipping extraction: {output_path.name}")
            return output_path

        logger.info(f"Extracting audio from: {video_path.name}")

        try:
            # Method 1: Use pydub (supports more formats)
            logger.info("Loading video with pydub...")

            # Determine input format
            input_format = self._get_audio_format(video_path)

            # Load audio from video
            audio = AudioSegment.from_file(
                str(video_path),
                format=input_format
            )

            # Convert to desired format
            audio = audio.set_frame_rate(sample_rate)
            audio = audio.set_channels(channels)

            # Export
            logger.info(f"Exporting audio to: {output_path}")
            audio.export(
                str(output_path),
                format=audio_format,
                bitrate=bitrate if audio_format != 'wav' else None
            )

            duration = len(audio) / 1000.0  # Convert to seconds
            logger.info(f"Audio extraction completed: {duration:.2f} seconds")

            return output_path

        except Exception as e:
            logger.error(f"Audio extraction with pydub failed: {e}")

            # Fallback: Use OpenCV
            try:
                logger.info("Trying OpenCV fallback method...")
                return self._extract_with_opencv(
                    video_path,
                    output_path,
                    sample_rate
                )
            except Exception as e2:
                logger.error(f"OpenCV extraction also failed: {e2}")
                raise

    def _get_audio_format(self, video_path: Path) -> str:
        """Get audio format from video file extension"""
        ext_map = {
            '.mp4': 'mp4',
            '.mkv': 'mkv',
            '.avi': 'avi',
            '.mov': 'mov',
            '.webm': 'webm',
            '.flv': 'flv',
            '.wmv': 'asf',  # Windows Media Video
        }

        return ext_map.get(video_path.suffix.lower(), 'mp4')

    def _extract_with_opencv(
        self,
        video_path: Path,
        output_path: Path,
        sample_rate: int
    ) -> Path:
        """
        Extract audio using OpenCV (fallback method)

        Note: OpenCV doesn't directly support audio extraction.
        This is a placeholder for future implementation.
        """
        raise NotImplementedError(
            "OpenCV audio extraction not implemented. "
            "Please install ffmpeg for pydub to work properly."
        )

    def get_audio_info(self, audio_path: str | Path) -> dict:
        """
        Get audio file information

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio information
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        audio = AudioSegment.from_file(str(audio_path))

        return {
            "path": str(audio_path),
            "filename": audio_path.name,
            "duration": len(audio) / 1000.0,  # seconds
            "frame_rate": audio.frame_rate,
            "channels": audio.channels,
            "sample_width": audio.sample_width,
        }

    def split_audio(
        self,
        audio_path: str | Path,
        chunk_length_ms: int = 10 * 60 * 1000  # 10 minutes
    ) -> list[Path]:
        """
        Split audio into chunks

        Args:
            audio_path: Path to audio file
            chunk_length_ms: Length of each chunk in milliseconds

        Returns:
            List of chunk file paths
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Splitting audio into {chunk_length_ms/1000/60} minute chunks")

        audio = AudioSegment.from_file(str(audio_path))
        chunks = make_chunks(audio, chunk_length_ms)

        chunk_paths = []

        for i, chunk in enumerate(chunks):
            chunk_filename = f"{audio_path.stem}_part{i+1}{audio_path.suffix}"
            chunk_path = self.output_dir / chunk_filename

            chunk.export(str(chunk_path), format=audio_path.suffix[1:])
            chunk_paths.append(chunk_path)

            logger.info(f"Created chunk {i+1}/{len(chunks)}: {chunk_path.name}")

        return chunk_paths


def extract_audio(
    video_path: str | Path,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Convenience function to extract audio from video

    Args:
        video_path: Path to video file
        output_dir: Output directory (optional)

    Returns:
        Path to extracted audio file
    """
    extractor = AudioExtractor(output_dir)
    return extractor.extract(video_path)
