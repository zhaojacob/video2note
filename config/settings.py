"""
Global configuration for video2note system
"""
import os
from pathlib import Path


# Load .env file into environment variables immediately
def _load_env_file():
    """Load .env file into environment variables"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

_load_env_file()  # Execute immediately to ensure env vars are loaded before os.getenv() calls


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
    "model": "doubao-vision",  # 统一使用 provider_registry.py 中的名称
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",  # Base URL without /chat/completions
    "timeout": 300,
    "max_tokens": 1000,
}

# ModelScope configuration (text LLM default)
MODELSCOPE_CONFIG = {
    "api_key": os.getenv("MODELSCOPE_TOKEN", ""),
    "model": "deepseek-reasoner",  # 使用与 DeepSeek API 兼容的名称（会自动映射到 deepseek-ai/DeepSeek-V3.2）
    "base_url": "https://api-inference.modelscope.cn/v1",
    "max_tokens": 8192,
    "thinking": True,
    "extra_body": {
        "enable_thinking": True
    },

    # Concurrency/Checkpoint configuration (shared with DeepSeek)
    "enable_concurrent": True,
    "max_concurrent": 3,
    "enable_checkpoint": True,
    "checkpoint_dir": OUTPUT_DIR / "polish_checkpoints",
    "max_chunk_retries": 3,
    "retry_delay": 5,
}

# DeepSeek configuration (text LLM fallback)
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "max_tokens": 8192,
    "thinking": False,

    # 并发/检查点配置
    "enable_concurrent": True,  # Enable concurrent processing
    "max_concurrent": 3,  # Maximum concurrent requests
    "enable_checkpoint": True,  # Enable checkpoint/resume functionality
    "checkpoint_dir": OUTPUT_DIR / "polish_checkpoints",  # Checkpoint directory
    "max_chunk_retries": 3,  # Maximum retries per chunk
    "retry_delay": 5,  # Base retry delay in seconds
}

TEXT_LLM_PROVIDER = os.getenv("TEXT_LLM_PROVIDER", "modelscope")

TEXT_LLM_CONFIGS = {
    "modelscope": MODELSCOPE_CONFIG,
    "deepseek": DEEPSEEK_CONFIG,
}

# ============================================================================
# PROVIDER-FIRST ARCHITECTURE (NEW)
# ============================================================================
# Provider defaults by task type
PROVIDER_DEFAULTS = {
    "text": os.getenv("DEFAULT_TEXT_PROVIDER", "zhipu"),
    "vision": os.getenv("DEFAULT_VISION_PROVIDER", "zhipu"),
    "thinking": os.getenv("DEFAULT_THINKING_PROVIDER", "modelscope"),
}

# Model defaults (optional overrides)
MODEL_DEFAULTS = {
    "text": os.getenv("DEFAULT_TEXT_MODEL", "glm-4-flash"),
    "vision": os.getenv("DEFAULT_VISION_MODEL", "glm-4.6v"),
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

# ============================================================================
# NEW: Unified LLM Configuration (Recommended)
# ============================================================================
# The new unified architecture provides:
# - Single interface for all LLM providers
# - Automatic fallback strategies
# - Dynamic model selection
# - Health checking
#
# To use the new architecture:
# from utils.llm.unified_manager import UnifiedLLMManager
# manager = UnifiedLLMManager()
# client = manager.get_client("glm-4-flash")
UNIFIED_LLM_CONFIG = {
    # Enable/disable unified manager globally
    "enabled": os.getenv("USE_UNIFIED_LLM", "false").lower() == "true",

    # Text task default model
    "default_text_model": os.getenv("DEFAULT_TEXT_MODEL", "glm-4-flash"),

    # Vision task default model
    "default_vision_model": os.getenv("DEFAULT_VISION_MODEL", "glm-4.6v"),

    # Enable fallback strategy
    "enable_fallback": True,

    # Fallback retry attempts
    "max_fallback_retries": 3,

    # Enable automatic health checking
    "enable_health_check": True,
}

# ============================================================================
# LEGACY: Individual LLM Configurations (Backward Compatible)
# ============================================================================
# The following configurations are maintained for backward compatibility.
# New code should use UnifiedLLMManager instead.
# The legacy clients (GLMClient, DoubaoClient) will be moved to analysis/legacy/
#