"""
Speech transcription using Faster Whisper (GPU-accelerated)
"""
import gc
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from faster_whisper import WhisperModel

from utils.logger import get_logger
from utils.file_handler import ensure_dir
from config.settings import WHISPER_CONFIG, OUTPUT_DIRS

logger = get_logger(__name__)


class Transcriber:
    """
    GPU-accelerated speech transcription using Faster Whisper

    Performance optimizations:
    - CUDA GPU acceleration
    - 8-bit quantization
    - VAD (Voice Activity Detection)
    - Chunked processing for long audio
    """

    def __init__(
        self,
        model_size: str = None,
        device: str = None,
        compute_type: str = None
    ):
        """
        Initialize Whisper model

        Args:
            model_size: Model size (tiny/base/small/medium/large-v3)
            device: Device to use (cuda/cpu)
            compute_type: Compute type (int8/float16/int8_float16)
        """
        self.model_size = model_size or WHISPER_CONFIG.get("model_size", "medium")
        self.device = device or WHISPER_CONFIG.get("device", "cuda")
        self.compute_type = compute_type or WHISPER_CONFIG.get("compute_type", "int8_float16")

        logger.info(f"Initializing Whisper model: {self.model_size}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Compute type: {self.compute_type}")

        # Check CUDA availability
        if self.device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available, falling back to CPU")
            self.device = "cpu"
            self.compute_type = "int8"

        # Check if model files exist (支持两种目录格式)
        import os
        from pathlib import Path
        from config.settings import MODELS_DIR
        
        # 格式1: 直接下载的平铺格式 (faster-whisper-medium/)
        local_model_dir = MODELS_DIR / f"faster-whisper-{self.model_size}"
        # 格式2: HuggingFace 缓存格式 (models--Systran--faster-whisper-medium/)
        hf_cache_dir = MODELS_DIR / f"models--Systran--faster-whisper-{self.model_size}"
        
        # 检查本地平铺格式是否存在 model.bin
        local_model_exists = (local_model_dir / "model.bin").exists()
        hf_cache_exists = hf_cache_dir.exists() and any(hf_cache_dir.iterdir())
        
        model_found = local_model_exists or hf_cache_exists
        
        # 确定使用哪个路径
        if local_model_exists:
            model_path = str(local_model_dir)
            logger.info(f"Using local model from: {model_path}")
        elif hf_cache_exists:
            model_path = self.model_size  # 使用 HF 缓存，faster-whisper 会自动查找
            logger.info(f"Using HuggingFace cached model: {self.model_size}")
        else:
            model_path = self.model_size  # 会触发下载
            print("\n" + "=" * 60)
            print(f"[DOWNLOADING] Whisper {self.model_size} model (first time only)")
            print(f"[INFO] Model size: ~1.5GB for medium model")
            print(f"[INFO] Please wait... this will take 5-10 minutes depending on network speed")
            print(f"[INFO] Model will be cached for future use")
            print("=" * 60)
            print("[PROGRESS] Downloading...", end="", flush=True)

        # Initialize model
        start_time = time.time()
        self.model = WhisperModel(
            model_path,
            device=self.device,
            compute_type=self.compute_type,
            download_root=str(MODELS_DIR)
        )

        if not model_found:
            print(" Complete!")

        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")

        # Log GPU info if available
        if self.device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def transcribe(
        self,
        audio_path: str | Path,
        language: str = None,
        vad_filter: bool = None,
        word_timestamps: bool = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file
            language: Language code (zh, en, auto)
            vad_filter: Enable VAD (Voice Activity Detection)
            word_timestamps: Include word-level timestamps

        Returns:
            List of transcription segments with timestamps
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        language = language or WHISPER_CONFIG.get("language", "zh")
        vad_filter = vad_filter if vad_filter is not None else WHISPER_CONFIG.get("vad_filter", True)
        word_timestamps = word_timestamps if word_timestamps is not None else WHISPER_CONFIG.get("word_timestamps", True)

        logger.info(f"Transcribing: {audio_path.name}")
        logger.info(f"Language: {language}, VAD: {vad_filter}")

        start_time = time.time()

        try:
            # Transcribe
            segments, info = self.model.transcribe(
                str(audio_path),
                language=language if language != "auto" else None,
                vad_filter=vad_filter,
                word_timestamps=word_timestamps,
                beam_size=5,
                best_of=5,
            )

            # Convert to list of dictionaries
            results = []
            for segment in segments:
                start_formatted = self._format_timestamp(segment.start)
                end_formatted = self._format_timestamp(segment.end)

                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "timestamp_formatted": f"[{start_formatted}]",
                    "time_range": f"[{start_formatted} - {end_formatted}]",
                    "text": segment.text.strip(),
                    "confidence": segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0,
                    "no_speech_prob": segment.no_speech_prob if hasattr(segment, 'no_speech_prob') else 0.0,
                })

            # Log transcription info
            duration = info.duration
            inference_time = time.time() - start_time
            speed_ratio = duration / inference_time if inference_time > 0 else 0

            logger.info(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            logger.info(f"Duration: {duration:.2f}s, Inference time: {inference_time:.2f}s")
            logger.info(f"Speed ratio: {speed_ratio:.2f}x real-time")
            logger.info(f"Segments: {len(results)}")

            return results

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_long_audio(
        self,
        audio_path: str | Path,
        chunk_length: int = 30 * 60,  # 30 minutes
        cache_dir: Path = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Transcribe long audio by splitting into chunks with checkpoint support

        Args:
            audio_path: Path to audio file
            chunk_length: Chunk length in seconds
            cache_dir: Directory to cache chunk transcripts (for resume)
            **kwargs: Additional arguments for transcribe()

        Returns:
            List of transcription segments with adjusted timestamps
        """
        import json
        from core.audio_extractor import AudioExtractor

        audio_path = Path(audio_path)
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = OUTPUT_DIRS["transcripts"]
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache file naming based on audio file
        cache_prefix = f"{audio_path.stem}_transcript"

        # Get audio duration
        audio_extractor = AudioExtractor()
        audio_info = audio_extractor.get_audio_info(audio_path)
        duration = audio_info["duration"]

        logger.info(f"Audio duration: {duration:.2f} seconds")

        # If audio is short enough, transcribe directly
        if duration <= chunk_length:
            return self.transcribe(audio_path, **kwargs)

        # Split audio into chunks
        logger.info(f"Splitting audio into {chunk_length/60:.0f} minute chunks")

        from pydub import AudioSegment
        from pydub.utils import make_chunks

        audio = AudioSegment.from_file(str(audio_path))
        chunk_length_ms = chunk_length * 1000
        chunks = make_chunks(audio, chunk_length_ms)
        total_chunks = len(chunks)

        logger.info(f"Created {total_chunks} chunks")

        # Transcribe each chunk with checkpoint
        all_segments = []
        time_offset = 0

        for i, chunk in enumerate(chunks):
            part_num = i + 1
            cache_file = cache_dir / f"{cache_prefix}_part{part_num}.json"
            
            # Check if this chunk was already transcribed
            if cache_file.exists():
                logger.info(f"Loading cached transcript for chunk {part_num}/{total_chunks}")
                print(f"\n[CACHE] Loading part {part_num}/{total_chunks} from cache...")
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    segments = cached_data.get("segments", [])
                    chunk_duration = cached_data.get("chunk_duration", len(chunk) / 1000.0)
                    all_segments.extend(segments)
                    time_offset += chunk_duration
                    print(f"[CACHE] Loaded {len(segments)} segments from part {part_num}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to load cache, re-transcribing: {e}")
            
            logger.info(f"Transcribing chunk {part_num}/{total_chunks}")

            # Save chunk to temporary file
            chunk_path = OUTPUT_DIRS["audio"] / f"{audio_path.stem}_chunk{i}.wav"
            chunk.export(str(chunk_path), format="wav")
            
            chunk_duration = len(chunk) / 1000.0  # seconds

            try:
                # Transcribe chunk
                segments = self.transcribe(str(chunk_path), **kwargs)

                # Adjust timestamps
                for segment in segments:
                    segment["start"] += time_offset
                    segment["end"] += time_offset

                # Save checkpoint immediately after transcription
                checkpoint_data = {
                    "part": part_num,
                    "total_parts": total_chunks,
                    "chunk_duration": chunk_duration,
                    "time_offset_start": time_offset,
                    "segments": segments,
                    "segment_count": len(segments)
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Saved checkpoint: {cache_file.name} ({len(segments)} segments)")
                print(f"[CHECKPOINT] Saved part {part_num}/{total_chunks}: {len(segments)} segments")

                all_segments.extend(segments)
                time_offset += chunk_duration

            finally:
                # Clean up temporary file
                if chunk_path.exists():
                    chunk_path.unlink()

                # Clear GPU cache
                if self.device == "cuda":
                    gc.collect()
                    torch.cuda.empty_cache()

        logger.info(f"Transcription completed: {len(all_segments)} segments total")

        return all_segments

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }


def transcribe_audio(
    audio_path: str | Path,
    model_size: str = "medium",
    device: str = "cuda"
) -> List[Dict[str, Any]]:
    """
    Convenience function to transcribe audio

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        device: Device to use

    Returns:
        List of transcription segments
    """
    transcriber = Transcriber(model_size=model_size, device=device)
    return transcriber.transcribe(audio_path)


if __name__ == "__main__":
    # Test transcription
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <audio_file>")
        sys.exit(1)

    audio_file = sys.argv[1]

    transcriber = Transcriber(model_size="base", device="cuda")
    segments = transcriber.transcribe(audio_file)

    for i, segment in enumerate(segments[:5]):  # Print first 5 segments
        print(f"[{i+1}] {segment['start']:.2f}s - {segment['end']:.2f}s")
        print(f"    {segment['text']}")
        print()

    print(f"Total segments: {len(segments)}")
