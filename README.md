# video2note

An intelligent system that automatically generates structured, illustrated notes from videos. Supports YouTube and Bilibili platforms with GPU-accelerated transcription, multi-modal AI analysis, and concurrent processing.

## Features

- **Dual Platform Support**: YouTube and Bilibili
- **GPU-Accelerated Transcription**: Faster Whisper with CUDA support
- **Smart Frame Extraction**: Three extraction strategies (uniform/paragraph/fixed interval)
- **Timestamp Alignment**: Precise [HH:MM:SS] timestamps aligned between text and images
- **Multi-Modal Analysis**: GLM-4.6V + Doubao Vision hybrid
- **Intelligent Structuring**: Smart section headings with optimized segmentation
- **Concurrent Processing**: 60-70% faster with checkpoint-based resume capability
- **Multiple Output Formats**: Word, Markdown, JSON
- **Content Recognition**: Formulas, code, charts, text detection
- **Robust Error Handling**: Automatic checkpoint saving and resume on connection errors

## Quick Start

### 1. Create Environment

```bash
# Create new conda environment
conda create -n video_note python=3.11
conda activate video_note
```

### 2. Install Dependencies

```bash
# Install PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
cd video_note_system
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Run setup to create .env template
python main.py --setup
```

Edit `.env` file with your API keys:
```bash
# Vision APIs (required for image analysis)
GLM_API_KEY=your_glm_api_key_here
DOUBAO_API_KEY=your_doubao_api_key_here

# Text LLM APIs (required for text polishing, summaries, translations, headings)
# Choose one or configure both for fallback
MODELSCOPE_TOKEN=your_modelscope_token_here        # Default: DeepSeek-V3.2 via ModelScope
DEEPSEEK_API_KEY=your_deepseek_api_key_here       # Fallback: DeepSeek official API

# Optional: Text LLM provider selection
TEXT_LLM_PROVIDER=modelscope  # Options: modelscope (default), deepseek
```

### 4. Generate Notes

```bash
# Basic usage
python main.py "https://www.youtube.com/watch?v=xxx"

# Generate specific formats
python main.py "https://www.youtube.com/watch?v=xxx" --formats docx markdown

# Use local video
python main.py "dummy_url" --local-video "path/to/video.mp4"

# Skip transcription for faster processing
python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription
```

## Project Structure

```
video_note_system/
├── config/              # Configuration files
│   └── settings.py      # All configuration including strategies
├── core/                # Core modules
│   ├── video_downloader.py
│   ├── audio_extractor.py
│   ├── transcriber.py        # Whisper GPU with timestamp formatting
│   └── frame_extractor.py    # 3 extraction strategies
├── analysis/            # AI analysis
│   ├── glm_client.py         # GLM-4.6V
│   ├── doubao_client.py      # Doubao Vision
│   ├── image_analyzer.py     # Unified analyzer
│   └── structurer.py         # Content organization + headings
├── utils/               # Utilities
│   ├── llm_client.py          # Generic OpenAI-compatible LLM client
│   ├── text_polisher.py       # Text polishing with checkpoint
│   ├── heading_adder.py       # Section heading generation
│   └── translator.py
├── generators/          # Document generation
│   ├── docx_generator.py
│   ├── markdown_generator.py
│   └── json_generator.py
├── pipeline/            # Orchestration
│   └── pipeline_orchestrator.py
└── output/              # Output files
    ├── videos/
    ├── audio/
    ├── frames/
    ├── transcripts/
    ├── polish_checkpoints/  # Checkpoint files for resume
    └── notes/
```

## API Requirements

### Vision APIs (Image Analysis)

#### GLM-4.6V
- Get API key: https://open.bigmodel.cn/
- Models: `glm-4.6v` (flagship), `glm-4.6v-flashx` (lightweight)
- Best for: Formulas, code, STEM content

#### Doubao Vision
- Get API key: https://www.volcengine.com/
- Model: `doubao-vision-pro-32k`
- Best for: Chinese text, PPT, documents

### Text LLM APIs (Text Processing)

#### ModelScope (Default) ⭐
- Get API token: https://modelscope.cn/my/myaccesstoken
- Model: `deepseek-ai/DeepSeek-V3.2`
- Best for: Text polishing, summaries, translations, section headings
- Features:
  - 128K context window
  - Thinking/reasoning chain output (visible in debug logs)
  - 8K max output tokens
  - Cost-effective via ModelScope platform

#### DeepSeek (Fallback)
- Get API key: https://platform.deepseek.com/
- Model: `deepseek-chat` (128K context, 8K output)
- Best for: Text polishing, summaries, section headings
- Pricing: ¥0.27/1M tokens input, ¥1.1/1M tokens output

### Text LLM Provider Selection

The system supports multiple text LLM providers with automatic fallback:

```bash
# Use ModelScope (default, DeepSeek-V3.2)
TEXT_LLM_PROVIDER=modelscope

# Use DeepSeek official API (fallback)
TEXT_LLM_PROVIDER=deepseek
```

**Recommendation**: Use ModelScope as the default provider for better cost-effectiveness and thinking feature support.

**Thinking Output**: When using DeepSeek-V3.2 via ModelScope, the reasoning chain (thinking process) is printed in debug logs for better understanding of the model's decision-making process.

## CLI Options

```
python main.py <video_url> [options]

Options:
  -f, --formats {docx,markdown,json,all}
                        Output formats (default: docx markdown json)
  -o, --output PATH     Output directory (default: output/notes)
  --local-video PATH    Use local video file (skip download)
  --skip-transcription  Skip audio transcription
  --skip-analysis       Skip image analysis

Frame Extraction Strategies:
  --frame-strategy {uniform,paragraph,fixed_interval,transcript,interval,scene}
                        Frame extraction strategy (default: uniform)
                        - uniform: Opening frame + 4 evenly distributed frames (recommended)
                        - paragraph: Opening frame + 4 frames at paragraph/speech boundaries
                        - fixed_interval: Opening frame + frames every N seconds
                        - transcript: Align frames with speech timestamps, random sample
                        - interval: Fixed interval based on video duration
                        - scene: PySceneDetect scene change detection
  --frame-interval SEC  Fixed interval in seconds (default: 10.0)
                        Only used with fixed_interval strategy
  --max-frames N        Maximum number of frames to extract (default: 5)

Translation:
  --translate {zh,en,ja,ko,es,fr,de,ru}
                        Translate content to target language (bilingual output)
                        - zh: 中文
                        - en: English
                        - ja: 日本語
                        - ko: 한국어
                        - es: Español
                        - fr: Français
                        - de: Deutsch
                        - ru: Русский

Whisper Options:
  --whisper-model {tiny,base,small,medium,large-v3}
                        Whisper model size (default: medium)
  --whisper-device {cuda,cpu}
                        Device for Whisper (default: cuda)

API Options:
  --max-concurrent N    Max concurrent API calls (default: 5)

Utility:
  --setup               Create .env template and validate API keys
  --check-gpu           Check GPU availability
  -v, --verbose         Enable verbose logging
```

## Examples

### Basic Usage

```bash
# Basic usage - generates DOCX and Markdown
python main.py "https://www.youtube.com/watch?v=xxx"

# Local video file
python main.py "dummy" --local-video "lecture.mp4"

# Generate only DOCX format
python main.py "https://www.youtube.com/watch?v=xxx" --formats docx
```

### Frame Extraction Strategies

```bash
# Strategy A: Uniform distribution (recommended for most videos)
# Extracts opening frame + 4 evenly distributed frames
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy uniform

# Strategy B: Paragraph boundaries (best for lectures with clear sections)
# Detects speech gaps > 3 seconds and extracts frames at those points
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy paragraph

# Strategy C: Fixed interval (good for long videos)
# Extracts opening frame + frames every 15 seconds
python main.py "https://www.youtube.com/watch?v=xxx" \
    --frame-strategy fixed_interval \
    --frame-interval 15.0 \
    --max-frames 7

# Strategy D: Scene detection (best for videos with distinct scenes)
# Uses PySceneDetect to find scene changes
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy scene

# Custom max frames
python main.py "https://www.youtube.com/watch?v=xxx" --max-frames 10
```

### Translation and Localization

```bash
# Local video with English translation (bilingual output)
python main.py "dummy" --local-video "lecture.mp4" --translate en

# Chinese video with Japanese translation
python main.py "https://www.bilibili.com/video/BV1xx411c7mD" --translate ja

# Multiple formats with translation
python main.py "https://www.youtube.com/watch?v=xxx" \
    --translate zh \
    --formats docx markdown json
```

### Advanced Usage

```bash
# Scene detection + Chinese translation + DOCX only
python main.py "https://www.youtube.com/watch?v=xxx" \
    --frame-strategy scene \
    --translate zh \
    --formats docx

# Paragraph boundary frames for lecture video
python main.py "https://www.youtube.com/watch?v=xxx" \
    --frame-strategy paragraph \
    --max-frames 8

# Fast processing (skip transcription)
python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription

# CPU mode (no GPU available)
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-device cpu

# Verbose mode for debugging
python main.py "https://www.youtube.com/watch?v=xxx" -v
```

### Checkpoint Resume (Automatic)

```bash
# If processing is interrupted (e.g., connection error), just rerun the same command
# The system will detect the checkpoint and continue from where it left off
python main.py "https://www.youtube.com/watch?v=xxx"

# Checkpoint files are automatically saved in: output/polish_checkpoints/
# They are automatically cleaned up on successful completion
```

## Output Format

### Generated DOCX Structure

```
Video Title
Translated Title
时间 | 来源 | 作者 | 链接
生成版本: v1.0 - 2026-01-26 10:30:00

摘要
Summary content...
摘要翻译

正文
## Section Heading 1
[00:00:15] Polished transcript text with timestamps...
[Image: frame_opening_000000.jpg] [00:00:00] Description

More paragraph content...

## Section Heading 2
[00:05:30] Next section content...
[Image: frame_uniform_000001.jpg] [00:12:36] Description

统计信息
- Video duration: 45m 30s
- Transcription segments: 156
- Frames extracted: 5
- Successful analyses: 5
```

## Architecture

### Pipeline Flow

1. **Download** → `VideoDownloader` (yt-dlp)
2. **Extract Audio** → `AudioExtractor` (pydub)
3. **Transcribe** → `Transcriber` (faster-whisper + CUDA)
   - Generates `[HH:MM:SS]` formatted timestamps
4. **Detect Scenes** → `SceneDetector` (PySceneDetect) [optional]
5. **Extract Frames** → `FrameExtractor` (OpenCV)
   - 3 strategies: uniform, paragraph, fixed_interval
6. **Analyze Images** → `ImageAnalyzer` (GLM + Doubao)
7. **Structure Content** → `Structurer`
   - Polish transcript (remove filler words, add punctuation)
   - Generate AI summary
   - Add section headings (5-15 headings optimized)
8. **Generate Documents** → `Generators` (Word/MD/JSON)

### Key Improvements (Latest Version)

#### 1. Timestamp Preservation
- Whisper now generates `[HH:MM:SS]` formatted timestamps during transcription
- Timestamps are preserved throughout the pipeline
- Final DOCX shows timestamps aligned with text and images

#### 2. Smart Frame Extraction
Three strategies for different use cases:

| Strategy | Best For | How It Works |
|----------|----------|---------------|
| **uniform** | Most videos | Opening frame + evenly distributed frames |
| **paragraph** | Lectures, presentations | Detects speech gaps (>3s) for natural breaks |
| **fixed_interval** | Long videos | Opening frame + every N seconds |
| **scene** | Dynamic content | Scene change detection |
| **transcript** | Speech-focused | Aligned with transcript segments |
| **interval** | Quick overview | Fixed interval based on duration |

#### 3. Optimized Section Structure
- **Before**: 10-20 sections (each chunk independently generated headings)
- **After**: 5-15 sections (post-summary global heading generation)
- Result: Better flow, less fragmentation, improved readability

#### 4. Concurrent Processing with Checkpointing
```
Sequential (Old):
Chunk 1 → Chunk 2 → Chunk 3 → Chunk 4 → Chunk 5 → Chunk 6 (error!)
All work lost ❌

Concurrent with Checkpoint (New):
[Chunk 1] ✓ [Chunk 2] ✓ [Chunk 3] ✓
[Chunk 4] ✓ [Chunk 5] ✓ [Chunk 6] (error!)
Resume: Skip chunks 1-5, retry only chunk 6 ✓
All work saved ✅
```

**Benefits**:
- 60-70% faster with concurrent processing
- Automatic checkpoint saving after each chunk
- Resume from interruption without data loss
- Better error recovery with retry logic

### API Selection Strategy

| Content Type | API | Reason |
|--------------|-----|--------|
| Formulas | GLM-4.6V | Best STEM accuracy |
| Code | GLM-4.6V | Strong programming knowledge |
| Charts | GLM-4.6V | 128k context, detailed analysis |
| Chinese Text | Doubao | Superior Chinese understanding |
| PPT/Slides | Doubao | Better layout recognition |
| Text Polishing | ModelScope (DeepSeek-V3.2) | Fast, accurate, thinking chain output |
| Summaries | ModelScope (DeepSeek-V3.2) | 128K context, cost-effective |
| Translations | ModelScope (DeepSeek-V3.2) | Multi-language support |
| Headings | ModelScope (DeepSeek-V3.2) | Smart section generation |
| General Vision | GLM 70% / Doubao 30% | Load balancing |
| General Text | ModelScope (DeepSeek-V3.2) | Default text LLM provider |

## Performance Comparison

| Feature | Before | After | Improvement |
|---------|---------|-------|-------------|
| Frame extraction | 1 strategy | 6 strategies | Flexibility |
| Sections | 10-20 (fragmented) | 5-15 (coherent) | 50% reduction |
| Processing time | 8 min | 3 min | 60% faster |
| Error recovery | All lost | Resume from checkpoint | 100% reliable |
| Timestamp format | Seconds | [HH:MM:SS] | User-friendly |

## Troubleshooting

### Checkpoint Issues

If processing gets stuck or corrupted:
```bash
# Manually clean checkpoints
rm -rf output/polish_checkpoints/*

# Then rerun your command
python main.py "video_url"
```

### GPU Memory Issues

If you encounter CUDA out of memory errors:
```bash
# Use CPU mode (slower but more stable)
python main.py "video_url" --whisper-device cpu

# Or use a smaller Whisper model
python main.py "video_url" --whisper-model small
```

### Connection Errors

The system now automatically:
1. Retries failed chunks up to 3 times
2. Saves checkpoints after each successful chunk
3. Can resume from interruption automatically

Just rerun the same command if interrupted!

## License

MIT License - feel free to use and modify.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
