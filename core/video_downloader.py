"""
Video downloader supporting YouTube and Bilibili
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp

from utils.logger import get_logger
from utils.file_handler import sanitize_filename, ensure_dir
from config.settings import VIDEO_CONFIG, OUTPUT_DIRS

logger = get_logger(__name__)


class VideoDownloader:
    """Download videos from YouTube and Bilibili"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize video downloader

        Args:
            output_dir: Output directory for downloaded videos
        """
        self.output_dir = output_dir or OUTPUT_DIRS["videos"]
        ensure_dir(self.output_dir)

    def detect_platform(self, url: str) -> str:
        """
        Detect video platform from URL

        Args:
            url: Video URL

        Returns:
            Platform name: 'youtube' or 'bilibili'
        """
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/shorts/',
        ]

        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return 'youtube'

        bilibili_patterns = [
            r'bilibili\.com/video/',
            r'b23\.tv/',
        ]

        for pattern in bilibili_patterns:
            if re.search(pattern, url):
                return 'bilibili'

        raise ValueError(f"Unsupported video platform: {url}")

    def download(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Download video from URL

        Args:
            url: Video URL
            **kwargs: Additional options for yt-dlp

        Returns:
            Dictionary with download information:
                - filepath: Path to downloaded video
                - title: Video title
                - duration: Video duration in seconds
                - platform: Source platform
                - thumbnail: URL to thumbnail (if available)
        """
        platform = self.detect_platform(url)
        logger.info(f"Detected platform: {platform}")

        # Common yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
        }

        # Add cookies if available
        cookie_file = VIDEO_CONFIG.get("cookie_file")
        if cookie_file and Path(cookie_file).exists():
            ydl_opts['cookiefile'] = cookie_file
            logger.info(f"Using cookies from: {cookie_file}")

        # Add proxy if configured
        proxy = VIDEO_CONFIG.get("proxy") or kwargs.get("proxy")
        if proxy:
            ydl_opts['proxy'] = proxy
            logger.info(f"Using proxy: {proxy}")

        # Platform-specific options
        if platform == 'bilibili':
            ydl_opts.update({
                'extractor_args': {
                    'bilibili': {
                        'session': 'Warranty',
                    }
                }
            })

        try:
            # Extract info first to get title
            logger.info(f"Extracting video info from: {url}")
            temp_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(temp_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Sanitize title
            title = sanitize_filename(info.get('title', 'video'))

            # Set output template with sanitized title
            ydl_opts['outtmpl'] = str(self.output_dir / f'{title}.%(ext)s')

            # Download video
            logger.info(f"Starting download: {title}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Get downloaded file path
                downloaded_file = ydl.prepare_filename(info)

                # Verify file exists
                if not Path(downloaded_file).exists():
                    # Try to find the file with the correct extension
                    for ext in ['mp4', 'mkv', 'webm']:
                        potential_file = self.output_dir / f"{title}.{ext}"
                        if potential_file.exists():
                            downloaded_file = str(potential_file)
                            break

                result = {
                    'filepath': downloaded_file,
                    'title': title,
                    'duration': info.get('duration', 0),
                    'platform': platform,
                    'url': url,
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count'),
                }

                logger.info(f"Download completed: {downloaded_file}")
                logger.info(f"Duration: {result['duration']:.2f} seconds")

                return result

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise

    def _progress_hook(self, d: Dict[str, Any]):
        """Progress hook for yt-dlp"""
        # Handle different data types from yt-dlp
        if not isinstance(d, dict):
            return

        if d.get('status') == 'downloading':
            try:
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                logger.debug(f"Download progress: {percent} - Speed: {speed} - ETA: {eta}")
            except Exception:
                pass
        elif d.get('status') == 'finished':
            logger.info("Download finished, processing...")

    def download_from_local(self, video_path: str) -> Dict[str, Any]:
        """
        Use a local video file instead of downloading

        Args:
            video_path: Path to local video file

        Returns:
            Dictionary with video information
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Using local video: {video_path}")

        # Get video info using OpenCV
        import cv2
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {
            'filepath': str(video_path),
            'title': video_path.stem,
            'duration': duration,
            'platform': 'local',
            'url': str(video_path),
        }


def download_video(url: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to download a video

    Args:
        url: Video URL
        output_dir: Output directory (optional)

    Returns:
        Video information dictionary
    """
    downloader = VideoDownloader(output_dir)
    return downloader.download(url)
