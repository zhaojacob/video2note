"""
Batch video processor - Serial processing version
"""
import time
from typing import List, Dict, Any, Callable, Optional

from pipeline.pipeline_orchestrator import PipelineOrchestrator
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """
    Batch video processor

    Features:
    - Serial processing (one video at a time)
    - Immediate save after each video (zero data loss)
    - Progress tracking
    - Error isolation (single failure doesn't affect others)
    """

    def __init__(
        self,
        whisper_model_size: str = "medium",
        whisper_device: str = "cuda",
        max_concurrent_api: int = 5
    ):
        """
        Initialize batch processor

        Args:
            whisper_model_size: Whisper model size
            whisper_device: Device for Whisper (cuda/cpu)
            max_concurrent_api: Max concurrent API calls
        """
        self.orchestrator = PipelineOrchestrator(
            whisper_model_size=whisper_model_size,
            whisper_device=whisper_device,
            max_concurrent_api=max_concurrent_api
        )
        self.results = []

    def process_batch(
        self,
        video_urls: List[str],
        output_formats: List[str] = None,
        **options
    ) -> Dict[str, Any]:
        """
        Process multiple videos in batch (serial mode)

        Args:
            video_urls: List of video URLs
            output_formats: Output format list
            **options: Other pipeline parameters

        Returns:
            Batch processing result summary
        """
        total = len(video_urls)
        success_count = 0
        failed_count = 0
        start_time = time.time()

        # Print batch processing header
        print(f"\n{'='*60}")
        print(f"📦 Batch Processing Mode: {total} video(s)")
        print(f"{'='*60}\n")

        # Process each video serially
        for i, url in enumerate(video_urls, 1):
            print(f"\n[{i}/{total}] Processing: {url}")
            print(f"{'─'*60}")

            try:
                # Call existing pipeline
                result = self.orchestrator.run(
                    video_url=url,
                    output_formats=output_formats,
                    **options
                )

                # Record success
                if result.get("success"):
                    success_count += 1
                    print(f"✅ Success: {url}")

                    # Show generated files
                    outputs = result.get("outputs", {})
                    for fmt, path in outputs.items():
                        print(f"   {fmt.upper()}: {path}")

                    self.results.append({
                        "url": url,
                        "status": "success",
                        "outputs": outputs
                    })
                else:
                    # Processing failed but didn't raise exception
                    failed_count += 1
                    errors = result.get("errors", [])
                    print(f"❌ Failed: {url}")
                    print(f"   Error(s): {', '.join(errors)}")

                    self.results.append({
                        "url": url,
                        "status": "failed",
                        "errors": errors
                    })

            except Exception as e:
                # Catch exception, continue to next video
                failed_count += 1
                logger.error(f"Processing failed for {url}: {e}", exc_info=True)
                print(f"❌ Exception: {url}")
                print(f"   Error: {str(e)}")

                self.results.append({
                    "url": url,
                    "status": "error",
                    "error": str(e)
                })

            # Show progress after each video
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            eta = avg_time * (total - i)

            print(f"\n📊 Batch Progress: {i}/{total} | "
                  f"✅{success_count} ❌{failed_count} ⏳{total-i} | "
                  f"Elapsed: {self._format_time(elapsed)} | "
                  f"ETA: {self._format_time(eta)}")

        # Generate batch processing report
        total_time = time.time() - start_time
        return self._generate_report(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            total_time=total_time
        )

    def _generate_report(
        self,
        total: int,
        success_count: int,
        failed_count: int,
        total_time: float
    ) -> Dict[str, Any]:
        """Generate batch processing report"""

        print(f"\n{'='*60}")
        print("📊 Batch Processing Complete")
        print(f"{'='*60}")
        print(f"Total: {total} video(s)")
        print(f"✅ Success: {success_count} ({success_count/total*100:.1f}%)")
        print(f"❌ Failed: {failed_count} ({failed_count/total*100:.1f}%)")
        print(f"⏱️  Total Time: {self._format_time(total_time)}")

        if total > 0:
            avg_time = total_time / total
            print(f"⏱️  Average: {self._format_time(avg_time)}/video")

        print(f"{'='*60}\n")

        # If there are failures, list them
        if failed_count > 0:
            print("Failed videos:")
            for result in self.results:
                if result["status"] in ["failed", "error"]:
                    url = result["url"]
                    error = result.get("error") or result.get("errors", ["Unknown error"])
                    print(f"  ❌ {url}")
                    if isinstance(error, list):
                        print(f"     {', '.join(error)}")
                    else:
                        print(f"     {error}")
            print()

        return {
            "total": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_time": total_time,
            "results": self.results
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time display"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h{minutes}m{secs}s"
        elif minutes > 0:
            return f"{minutes}m{secs}s"
        else:
            return f"{secs}s"
