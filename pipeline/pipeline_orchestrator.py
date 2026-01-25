"""
Main pipeline orchestrator for video note generation
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.video_downloader import VideoDownloader
from core.audio_extractor import AudioExtractor
from core.transcriber import Transcriber
from core.frame_extractor import FrameExtractor

from analysis.image_analyzer import ImageAnalyzer
from analysis.structurer import Structurer

from generators.docx_generator import DocxGenerator
from generators.markdown_generator import MarkdownGenerator
from generators.json_generator import JsonGenerator

from pipeline.error_handler import ErrorHandler, retry
from utils.logger import get_logger
from utils.file_handler import get_video_info

logger = get_logger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the complete video note generation pipeline

    Pipeline steps:
    1. Download video (or use local)
    2. Extract audio
    3. Transcribe audio (Whisper GPU)
    4. Extract frames (scene detection)
    5. Analyze frames (GLM/Doubao)
    6. Structure data
    7. Generate documents
    """

    def __init__(
        self,
        whisper_model_size: str = "medium",
        whisper_device: str = "cuda",
        max_concurrent_api: int = 5
    ):
        """
        Initialize pipeline orchestrator

        Args:
            whisper_model_size: Whisper model size
            whisper_device: Device for Whisper (cuda/cpu)
            max_concurrent_api: Max concurrent API calls
        """
        self.error_handler = ErrorHandler()
        self.whisper_model_size = whisper_model_size
        self.whisper_device = whisper_device
        self.max_concurrent_api = max_concurrent_api

        # Initialize lightweight components immediately
        self.video_downloader = VideoDownloader()
        self.audio_extractor = AudioExtractor()
        self.frame_extractor = FrameExtractor()
        self.image_analyzer = ImageAnalyzer()
        self.structurer = Structurer()

        # Lazy-load heavy components
        self.transcriber = None

        # Generators
        self.generators = {
            "docx": DocxGenerator(),
            "markdown": MarkdownGenerator(),
            "json": JsonGenerator(),
        }

        logger.info("Pipeline orchestrator initialized")

    def _get_transcriber(self) -> Transcriber:
        """Lazy-load the transcriber only when needed"""
        if self.transcriber is None:
            print("\n" + "=" * 60)
            print("[INIT] Loading Whisper model...")
            print(f"[INFO] Model: {self.whisper_model_size}")
            print(f"[INFO] Device: {self.whisper_device}")
            print("=" * 60)

            self.transcriber = Transcriber(
                model_size=self.whisper_model_size,
                device=self.whisper_device
            )

            print("[OK] Whisper model loaded successfully!")

        return self.transcriber

    @retry(max_attempts=2, delay=2.0)
    def run(
        self,
        video_url: str,
        output_formats: List[str] = None,
        local_video: str = None,
        skip_transcription: bool = False,
        skip_analysis: bool = False,
        frame_strategy: str = "interval",
        translate_to: str = None
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline

        Args:
            video_url: Video URL (or dummy if using local_video)
            frame_strategy: Frame extraction strategy ('transcript', 'interval', 'scene')
            output_formats: List of output formats (docx, markdown, json)
            local_video: Path to local video file (skip download)
            skip_transcription: Skip transcription step
            skip_analysis: Skip image analysis step
            translate_to: Target language for translation (None = no translation)

        Returns:
            Dictionary with results and outputs
        """
        print("\n" + "=" * 60)
        print("VIDEO NOTE GENERATION PIPELINE")
        print("=" * 60)
        print(f"[CONFIG] Model: {self.whisper_model_size}, Device: {self.whisper_device}")
        print(f"[CONFIG] Output formats: {', '.join(output_formats or ['docx', 'markdown', 'json'])}")
        print(f"[CONFIG] Max concurrent API calls: {self.max_concurrent_api}")
        if translate_to:
            from utils.translator import SUPPORTED_LANGUAGES
            lang_name = SUPPORTED_LANGUAGES.get(translate_to, translate_to)
            print(f"[CONFIG] Translation: Enabled -> {lang_name}")
        print("=" * 60)

        results = {
            "success": True,
            "outputs": {},
            "errors": [],
        }

        try:
            # Step 1: Download video (or use local)
            print("\n" + "=" * 60)
            print("[Step 1/7] Downloading video...")
            print("=" * 60)

            if local_video:
                print(f"[INFO] Using local video: {local_video}")
                video_info = self.video_downloader.download_from_local(local_video)
            else:
                print(f"[INFO] Downloading from: {video_url}")
                print("[PROGRESS] Please wait...", end="", flush=True)
                video_info = self.video_downloader.download(video_url)
                print(" Complete!")

            print(f"[OK] Video: {video_info['title']}")
            print(f"[OK] Duration: {video_info['duration']:.2f}s ({int(video_info['duration']//60)}m {int(video_info['duration']%60)}s)")
            print(f"[OK] Saved to: {video_info['filepath']}")

            # Step 2: Extract audio
            print("\n" + "=" * 60)
            print("[Step 2/7] Extracting audio...")
            print("=" * 60)

            print("[PROGRESS] Extracting...", end="", flush=True)
            audio_path = self.audio_extractor.extract(video_info["filepath"])
            print(" Complete!")
            print(f"[OK] Audio saved to: {audio_path}")

            # Step 3: Transcribe audio
            if not skip_transcription:
                print("\n" + "=" * 60)
                print("[Step 3/7] Transcribing audio with Whisper...")
                print("=" * 60)

                # Lazy-load transcriber here
                transcriber = self._get_transcriber()

                print(f"[INFO] Processing: {audio_path}")
                print("[PROGRESS] Transcribing...", end="", flush=True)
                transcript = transcriber.transcribe_long_audio(str(audio_path))
                print(" Complete!")
                print(f"[OK] Transcription: {len(transcript)} segments")
                
                # Save original Whisper transcript (polish will happen in Structuring phase)
                from config.settings import OUTPUT_DIRS
                from utils.file_handler import sanitize_filename
                
                # Generate filename with timestamp
                base_name = sanitize_filename(video_info.get("title", "video"))
                timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
                transcript_base = f"{base_name}_{timestamp_suffix}"
                
                # Save JSON (original Whisper output)
                json_path = OUTPUT_DIRS["transcripts"] / f"{transcript_base}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
                print(f"[OK] Transcript JSON: {json_path}")
                
                # Save TXT (original Whisper output with timestamps)
                txt_path = OUTPUT_DIRS["transcripts"] / f"{transcript_base}.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"# {video_info.get('title', 'Video Transcript')}\n")
                    f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Whisper Model: {video_info.get('whisper_model', 'medium')}\n\n")
                    for seg in transcript:
                        start = seg.get('start', 0)
                        end = seg.get('end', 0)
                        text = seg.get('text', '')
                        f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
                print(f"[OK] Transcript TXT: {txt_path}")
            else:
                print("\n" + "=" * 60)
                print("[Step 3/7] Skipping transcription (--skip-transcription)")
                print("=" * 60)
                transcript = []

            # Step 4: Extract frames
            print("\n" + "=" * 60)
            print("[Step 4/7] Extracting frames...")
            print("=" * 60)

            # Determine extraction method based on strategy
            if frame_strategy == "scene":
                method_name = "Scene detection (fewer frames, saves API calls)"
            elif frame_strategy == "interval" or skip_transcription:
                method_name = "Interval-based"
            else:
                method_name = "Transcript-aligned"
            
            print(f"[INFO] Method: {method_name}")
            print("[PROGRESS] Extracting...", end="", flush=True)

            if frame_strategy == "scene":
                # Use scene detection for key frames (fewer frames, fewer API calls)
                frames = self.frame_extractor.extract_key_frames(
                    video_info["filepath"],
                    max_frames=5  # Limit to 5 key frames max
                )
            elif skip_transcription or frame_strategy == "interval":
                # Use interval-based extraction (max 5 frames)
                frames = self.frame_extractor.extract_frames_by_interval(
                    video_info["filepath"],
                    max_frames=5
                )
            else:
                # Use transcript-aligned extraction (default, max 5 frames)
                frames = self.frame_extractor.extract_frames_by_transcript(
                    video_info["filepath"],
                    transcript,
                    max_frames=5
                )

            print(" Complete!")
            print(f"[OK] Extracted {len(frames)} frames")

            # Step 5: Detect content in frames
            print("\n" + "=" * 60)
            print("[Step 5/7] Detecting content in frames...")
            print("=" * 60)

            print("[PROGRESS] Analyzing frames...", end="", flush=True)
            for i, frame in enumerate(frames):
                try:
                    frame["content_type"] = self.frame_extractor.detect_special_content(
                        frame["path"]
                    )
                except Exception as e:
                    logger.warning(f"Content detection failed for frame {i}: {e}")
                    frame["content_type"] = {}

            print(" Complete!")

            # Step 6: Deduplicate frames
            print("\n" + "=" * 60)
            print("[Step 6/7] Deduplicating frames...")
            print("=" * 60)

            frame_paths = [f["path"] for f in frames]
            unique_paths = self.frame_extractor.deduplicate_frames(frame_paths)

            # Keep only unique frames
            unique_frames = [f for f in frames if f["path"] in unique_paths]
            duplicates = len(frames) - len(unique_frames)

            print(f"[OK] Removed {duplicates} duplicate frames")
            print(f"[OK] Unique frames: {len(unique_frames)}")

            # Step 7: Analyze frames
            if not skip_analysis and unique_frames:
                print("\n" + "=" * 60)
                print(f"[Step 7/7] Analyzing {len(unique_frames)} frames with AI...")
                print("=" * 60)
                print("[INFO] This may take several minutes depending on frame count")

                # Run async analysis
                frame_analyses = asyncio.run(
                    self.image_analyzer.analyze_batch_async(
                        unique_frames,
                        analysis_type="auto",
                        max_concurrent=self.max_concurrent_api
                    )
                )

                # Log statistics
                glm_count = sum(1 for f in frame_analyses if f.get("api_used") == "glm")
                doubao_count = sum(1 for f in frame_analyses if f.get("api_used") == "doubao")
                success_count = sum(1 for f in frame_analyses if f.get("success"))

                print(f"\n[OK] Analysis complete: {success_count}/{len(frame_analyses)} successful")
                print(f"[INFO] GLM API: {glm_count} frames")
                print(f"[INFO] Doubao API: {doubao_count} frames")

            else:
                print("\n" + "=" * 60)
                print("[Step 7/7] Skipping image analysis (--skip-analysis)")
                print("=" * 60)
                frame_analyses = []

            # Structure data (includes Polish and Summary generation)
            print("\n" + "=" * 60)
            print("[Structuring] Polishing text, generating summary, organizing content...")
            print("=" * 60)
            
            # Get video duration for chapter calculation
            duration_minutes = video_info.get("duration", 0) / 60

            structured_data = self.structurer.structure(
                video_info=video_info,
                transcript=transcript,
                frame_analyses=frame_analyses,
                translate_to=translate_to,
                duration_minutes=duration_minutes,
            )

            print(f"[OK] Created {len(structured_data['sections'])} sections")
            if structured_data.get('chapters'):
                print(f"[OK] Chapters: {len(structured_data['chapters'])}")

            # Generate documents
            print("\n" + "=" * 60)
            print(f"[Generating] Creating documents: {', '.join(output_formats or ['docx', 'markdown', 'json'])}")
            print("=" * 60)

            output_formats = output_formats or ["docx", "markdown", "json"]

            for fmt in output_formats:
                try:
                    print(f"[PROGRESS] Generating {fmt.upper()}...", end="", flush=True)
                    generator = self.generators[fmt]
                    output_path = generator.generate(structured_data)
                    results["outputs"][fmt] = str(output_path)
                    print(f" Complete!")
                    print(f"  → {output_path}")
                except Exception as e:
                    logger.error(f"Failed to generate {fmt}: {e}")
                    results["errors"].append(f"{fmt} generation failed: {e}")
                    print(f"[X] Failed to generate {fmt}: {e}")

            # Check for errors
            if results["errors"]:
                results["success"] = False

            # Final summary
            print("\n" + "=" * 60)
            if results["success"]:
                print("✓ GENERATION COMPLETE!")
            else:
                print("✗ GENERATION COMPLETED WITH ERRORS")
            print("=" * 60)

            if results["outputs"]:
                print("\n[OUTPUTS] Generated files:")
                for fmt, path in results["outputs"].items():
                    print(f"  • {fmt.upper()}: {path}")

            if results["errors"]:
                print(f"\n[ERRORS] {len(results['errors'])} error(s) occurred:")
                for error in results["errors"]:
                    print(f"  • {error}")

            return results

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            print(f"\n[X] FATAL ERROR: {e}")
            results["success"] = False
            results["errors"].append(str(e))
            raise

    def run_simple(
        self,
        video_url: str,
        output_format: str = "docx"
    ) -> str:
        """
        Run simplified pipeline (single output format)

        Args:
            video_url: Video URL
            output_format: Output format (docx/markdown/json)

        Returns:
            Path to output file
        """
        results = self.run(video_url, output_formats=[output_format])

        if not results["success"]:
            raise RuntimeError(f"Pipeline failed: {results['errors']}")

        return results["outputs"].get(output_format)


async def run_pipeline_async(
    video_url: str,
    output_formats: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Async wrapper for pipeline execution

    Args:
        video_url: Video URL
        output_formats: Output formats
        **kwargs: Additional arguments for run()

    Returns:
        Results dictionary
    """
    orchestrator = PipelineOrchestrator()
    return orchestrator.run(video_url, output_formats, **kwargs)


def run_pipeline(
    video_url: str,
    output_formats: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to run the pipeline

    Args:
        video_url: Video URL
        output_formats: Output formats
        **kwargs: Additional arguments

    Returns:
        Results dictionary
    """
    orchestrator = PipelineOrchestrator()
    return orchestrator.run(video_url, output_formats, **kwargs)
