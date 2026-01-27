"""
Command-line interface for video note generation system
"""
import argparse
import sys
from pathlib import Path

from pipeline.pipeline_orchestrator import PipelineOrchestrator
from pipeline.batch_processor import BatchProcessor
from config.api_config import validate_api_keys, create_env_template
from utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate notes from videos using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all formats from YouTube
  python main.py "https://www.youtube.com/watch?v=xxx"

  # Batch process multiple videos
  python main.py "https://www.youtube.com/watch?v=xxx1" "https://www.youtube.com/watch?v=xxx2"

  # Batch process from file
  python main.py --batch-file videos.txt

  # Generate only Word document
  python main.py "https://www.youtube.com/watch?v=xxx" --formats docx

  # Use local video file
  python main.py "dummy_url" --local-video "path/to/video.mp4"

  # Skip transcription (faster, no subtitles)
  python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription

  # Use CPU instead of GPU
  python main.py "https://www.youtube.com/watch?v=xxx" --whisper-device cpu

  # Use scene detection for fewer frames (saves API calls)
  python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy scene

  # Translate content to English (bilingual output)
  python main.py "https://www.youtube.com/watch?v=xxx" --translate en

  # Translate to Chinese
  python main.py "https://www.youtube.com/watch?v=xxx" --translate zh

Batch file format (videos.txt):
  https://www.youtube.com/watch?v=xxx1
  https://www.youtube.com/watch?v=xxx2
  # This is a comment, will be ignored
  https://bilibili.com/video/BV1xx411c7mD
        """
    )

    # Positional arguments (optional when using --setup or --check-gpu)
    parser.add_argument(
        "urls",
        nargs="*",
        help="Video URL(s) (YouTube/Bilibili) - supports multiple URLs for batch processing"
    )

    parser.add_argument(
        "--batch-file",
        help="Read video URLs from file (one URL per line, # for comments)"
    )

    # Output options
    parser.add_argument(
        "-f", "--formats",
        nargs="+",
        choices=["docx", "markdown", "json", "all"],
        default=["docx", "markdown", "json"],
        help="Output formats (default: docx markdown json)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output directory (default: output/notes)"
    )

    # Video source
    parser.add_argument(
        "--local-video",
        help="Path to local video file (skip download)"
    )

    # Processing options
    parser.add_argument(
        "--skip-transcription",
        action="store_true",
        help="Skip audio transcription"
    )

    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip image analysis"
    )

    # Frame extraction options
    parser.add_argument(
        "--frame-strategy",
        choices=["uniform", "paragraph", "fixed_interval", "transcript", "interval", "scene"],
        default="uniform",
        help="Frame extraction strategy: uniform (opening + 4 evenly distributed, default), paragraph (opening + speech boundaries), fixed_interval (opening + every N seconds), transcript (align to speech), interval (fixed interval), scene (scene detection)"
    )

    parser.add_argument(
        "--frame-interval",
        type=float,
        default=10.0,
        help="Fixed interval in seconds for fixed_interval strategy (default: 10.0)"
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=5,
        help="Maximum number of frames to extract (default: 5)"
    )

    # Translation options
    parser.add_argument(
        "--translate",
        choices=["zh", "en", "ja", "ko", "es", "fr", "de", "ru"],
        default=None,
        help="Translate content to target language (zh=Chinese, en=English, ja=Japanese, ko=Korean, etc.)"
    )

    # Whisper options
    parser.add_argument(
        "--whisper-model",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        default="medium",
        help="Whisper model size (default: medium)"
    )

    parser.add_argument(
        "--whisper-device",
        choices=["cuda", "cpu"],
        default="cuda",
        help="Device for Whisper (default: cuda)"
    )

    # API options
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent API calls (default: 5)"
    )

    # Utility commands
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create .env template and validate API keys"
    )

    parser.add_argument(
        "--check-gpu",
        action="store_true",
        help="Check GPU availability for Whisper"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()


def load_urls_from_file(file_path: str) -> list:
    """
    Load URL list from file

    File format:
    - One URL per line
    - Empty lines are ignored
    - Lines starting with # are treated as comments
    """
    from pathlib import Path

    urls = []
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Batch file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            urls.append(line)

    logger.info(f"Loaded {len(urls)} URL(s) from file: {file_path}")
    return urls


def setup_command():
    """Handle setup command"""
    print("Setting up video note system...\n")

    # Create .env template
    create_env_template()
    print()

    # Validate API keys
    validate_api_keys()

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            print(f"\n[OK] GPU available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            print("\n[!] GPU not available, Whisper will use CPU (slower)")
            print("  Install PyTorch with CUDA support for GPU acceleration")
    except ImportError:
        print("\n[!] PyTorch not installed")


def check_gpu_command():
    """Handle GPU check command"""
    print("Checking GPU availability...\n")

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  Memory: {props.total_memory / 1024**3:.2f} GB")
                print(f"  Compute capability: {props.major}.{props.minor}")

        return 0

    except ImportError:
        print("PyTorch not installed")
        print("Install with: pip install torch torchvision torchaudio")
        return 1


def main():
    """Main entry point"""
    args = parse_args()

    # Setup logging
    if args.verbose:
        setup_logger("video_note_system", level="DEBUG")

    # Handle utility commands
    if args.setup:
        setup_command()
        return 0

    if args.check_gpu:
        return check_gpu_command()

    # Collect all video URLs
    video_urls = []

    # Method 1: Command line arguments
    if args.urls:
        video_urls.extend(args.urls)

    # Method 2: Batch file
    if args.batch_file:
        file_urls = load_urls_from_file(args.batch_file)
        video_urls.extend(file_urls)

    # Check if we have any URLs
    if not video_urls:
        parser.error("Please provide at least one video URL (as argument or via --batch-file)")

    # Validate API keys before running
    try:
        from config.api_config import get_glm_api_key, get_doubao_api_key
        get_glm_api_key()
        get_doubao_api_key()
    except ValueError as e:
        logger.error(f"API key validation failed: {e}")
        logger.error("Run 'python main.py --setup' to configure API keys")
        return 1

    # Process output formats
    formats = args.formats
    if "all" in formats:
        formats = ["docx", "markdown", "json"]

    # Run pipeline
    try:
        # Batch mode (multiple URLs)
        if len(video_urls) > 1:
            logger.info(f"Starting batch processing: {len(video_urls)} video(s)")

            processor = BatchProcessor(
                whisper_model_size=args.whisper_model,
                whisper_device=args.whisper_device,
                max_concurrent_api=args.max_concurrent
            )

            result = processor.process_batch(
                video_urls=video_urls,
                output_formats=formats,
                local_video=args.local_video,
                skip_transcription=args.skip_transcription,
                skip_analysis=args.skip_analysis,
                frame_strategy=args.frame_strategy,
                frame_interval=args.frame_interval,
                max_frames=args.max_frames,
                translate_to=args.translate
            )

            return 0 if result["failed_count"] == 0 else 1

        # Single video mode (backward compatible)
        else:
            logger.info("Starting video note generation")
            logger.info(f"URL: {video_urls[0]}")
            logger.info(f"Formats: {', '.join(formats)}")

            orchestrator = PipelineOrchestrator(
                whisper_model_size=args.whisper_model,
                whisper_device=args.whisper_device,
                max_concurrent_api=args.max_concurrent
            )

            results = orchestrator.run(
                video_url=video_urls[0],
                output_formats=formats,
                local_video=args.local_video,
                skip_transcription=args.skip_transcription,
                skip_analysis=args.skip_analysis,
                frame_strategy=args.frame_strategy,
                frame_interval=args.frame_interval,
                max_frames=args.max_frames,
                translate_to=args.translate
            )

            if results["success"]:
                print("\n" + "=" * 60)
                print("[OK] Generation complete!")
                print("=" * 60)

                for fmt, path in results["outputs"].items():
                    print(f"  {fmt.upper()}: {path}")

                return 0
            else:
                print("\n" + "=" * 60)
                print("[X] Generation completed with errors")
                print("=" * 60)

                for error in results["errors"]:
                    print(f"  • {error}")

                return 1

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
