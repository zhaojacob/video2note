"""
Global configuration for video2note system
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"  # Whisper models directory

# Create directories
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Create output subdirectories
OUTPUT_DIRS = {
    "videos": OUTPUT_DIR / "videos",
    "audio": OUTPUT_DIR / "audio",
    "frames": OUTPUT_DIR / "frames",
    "transcripts": OUTPUT_DIR / "transcripts",
    "notes": OUTPUT_DIR / "notes",
}

for dir_path in OUTPUT_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# Whisper configuration
WHISPER_CONFIG = {
    "model_size": "medium",  # tiny/base/small/medium/large-v3
    "device": "cuda",  # cuda or cpu
    "compute_type": "int8_float16",  # int8, float16, int8_float16
    "language": "auto",  # auto-detect language, or use "zh" for Chinese, "en" for English
    "vad_filter": True,
    "word_timestamps": True,
}

# GLM-4.6V configuration
GLM_CONFIG = {
    "api_key": os.getenv("GLM_API_KEY", ""),
    "model": "glm-4.6v",  # glm-4.6v / glm-4.6v-flashx / glm-4.6v-flash
    "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "timeout": 60,
    "max_tokens": 1000,
    "thinking_enabled": True,
}

# Doubao configuration (OpenAI-compatible API)
DOUBAO_CONFIG = {
    "api_key": os.getenv("ARK_API_KEY", ""),
    "model": "doubao-seed-1-8-251228",  # Updated model name
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",  # Base URL without /chat/completions
    "timeout": 180,
#    "max_tokens": 1000,
}

# DeepSeek configuration (for summary generation and text polishing)
# All use deepseek-chat model with 128K context window and 8K max output
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "model": "deepseek-chat",  # Use chat model for all tasks (128K context, 8K output)
    "base_url": "https://api.deepseek.com",
    "max_tokens": 8192,  # Maximum output tokens (8K)
    "thinking": False,  # Thinking mode disabled (not needed for polish/summary)

    # 并发/检查点配置
    "enable_concurrent": True,  # Enable concurrent processing
    "max_concurrent": 3,  # Maximum concurrent requests
    "enable_checkpoint": True,  # Enable checkpoint/resume functionality
    "checkpoint_dir": OUTPUT_DIR / "polish_checkpoints",  # Checkpoint directory
    "max_chunk_retries": 3,  # Maximum retries per chunk
    "retry_delay": 5,  # Base retry delay in seconds
}

# Frame extraction configuration
FRAME_CONFIG = {
    "default_strategy": "uniform",  # uniform/paragraph/fixed_interval
    "max_frames": 5,  # Total frames to extract (including opening frame)
    "strategies": {
        "uniform": {
            "name": "均匀分布",
            "description": "开头帧 + 4个均匀分布帧（时间轴均匀分布）"
        },
        "paragraph": {
            "name": "段落边界",
            "description": "开头帧 + 4个段落边界帧（根据文字段落/章节切换）"
        },
        "fixed_interval": {
            "name": "固定间隔",
            "description": "开头帧 + 每10秒一帧",
            "interval_sec": 10.0
        }
    },
    "interval_sec": 10.0,  # Extract frame every N seconds
    "scene_threshold": 30.0,  # Scene detection threshold
    "similarity_threshold": 0.95,  # For deduplication
    "max_frames_per_minute": 6,  # Maximum frames to extract per minute
}

# API allocation strategy
API_ALLOCATION_CONFIG = {
    "glm_ratio": 0.7,  # 70% GLM, 30% Doubao
    "max_concurrent": 5,  # Maximum concurrent API calls
    "retry_with_alternative": True,  # Switch to alternative API on failure
    "max_retries": 3,
    "retry_delay": 2,  # Base retry delay in seconds (exponential backoff)
}

# Video download configuration
VIDEO_CONFIG = {
    "cookie_file": os.path.join(OUTPUT_DIR, "cookies.txt"),
    "proxy": None,  # e.g., "http://127.0.0.1:7890"
    "quality": "best",  # best, worst, or specific format
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": str(OUTPUT_DIR / "system.log"),
}
