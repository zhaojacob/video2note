"""
Main entry point for video note generation system

Usage:
    python main.py <video_url> [options]

Examples:
    # Generate all formats from YouTube
    python main.py "https://www.youtube.com/watch?v=xxx"

    # Generate only Word document
    python main.py "https://www.youtube.com/watch?v=xxx" --formats docx

    # Use local video file
    python main.py "dummy_url" --local-video "path/to/video.mp4"
"""
from cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
