"""
Command-line interface for video note generation system
"""
import argparse
import sys
from pathlib import Path

from pipeline.pipeline_orchestrator import PipelineOrchestrator
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
        """
    )

    # Positional arguments (optional when using --setup or --check-gpu)
    parser.add_argument(
        "video_url",
        nargs="?",
        help="Video URL (YouTube/Bilibili) or dummy URL when using --local-video"
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
        choices=["transcript", "interval", "scene"],
        default="transcript",
        help="Frame extraction strategy: transcript (align to speech), interval (fixed interval), scene (scene detection, fewer frames) (default: transcript)"
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

    # Check if video_url is provided
    if not args.video_url:
        parser.error("video_url is required when not using --setup or --check-gpu")

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
        logger.info("Starting video note generation")
        logger.info(f"URL: {args.video_url}")
        logger.info(f"Formats: {', '.join(formats)}")

        orchestrator = PipelineOrchestrator(
            whisper_model_size=args.whisper_model,
            whisper_device=args.whisper_device,
            max_concurrent_api=args.max_concurrent
        )

        results = orchestrator.run(
            video_url=args.video_url,
            output_formats=formats,
            local_video=args.local_video,
            skip_transcription=args.skip_transcription,
            skip_analysis=args.skip_analysis,
            frame_strategy=args.frame_strategy,
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
