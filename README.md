# video2note

Automatically generate structured, illustrated notes from YouTube/Bilibili videos using AI.

## Demo

### Local Demo
<video src="demo_video/demo.mp4" controls="controls" style="max-width: 100%;">
</video>

### Bilibili Demo
[![Bilibili Demo](https://i0.hdslb.com/bfs/archive/8f8e078701987d65689100790886101560938743.jpg)](https://www.bilibili.com/video/BV17LFVzSEsM/)
> Click image to watch on Bilibili

## Features

- **Multi-Platform**: YouTube & Bilibili support
- **GPU Transcription**: Faster Whisper with CUDA acceleration
- **Smart Frame Extraction**: 6 strategies (uniform, scene, paragraph, etc.)
- **Multi-Modal AI**: GLM-4.6V + Doubao Vision for image analysis
- **Text Enhancement**: DeepSeek for polishing, summaries, and translations
- **Batch Processing**: Process multiple videos with progress tracking
- **Checkpoint Resume**: Auto-save progress, resume on interruption
- **Multiple Formats**: Word (.docx), Markdown, JSON output

## Quick Start

### 1. Environment Setup

```bash
conda create -n video_note python=3.11
conda activate video_note

# PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
python main.py --setup
```

Edit `.env`:
```bash
# Vision APIs (required)
GLM_API_KEY=your_glm_key          # https://open.bigmodel.cn/
ARK_API_KEY=your_doubao_key       # https://console.volcengine.com/

# Text LLM (choose one)
DEEPSEEK_API_KEY=your_key         # https://platform.deepseek.com/
```

### 3. Generate Notes

```bash
# Basic usage
python main.py "https://www.youtube.com/watch?v=xxx"

# With options
python main.py "https://www.youtube.com/watch?v=xxx" \
    --formats docx markdown \
    --translate zh \
    --frame-strategy scene
```

## Usage Examples

```bash
# Local video file
python main.py "dummy" --local-video "lecture.mp4"

# Batch processing
python main.py --batch-file videos.txt

# Scene-based frame extraction
python main.py "URL" --frame-strategy scene --max-frames 10

# Bilingual output (Chinese translation)
python main.py "URL" --translate zh --formats docx
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--formats` | Output formats (docx/markdown/json/all) | docx markdown json |
| `--frame-strategy` | Frame extraction (uniform/scene/paragraph/fixed_interval) | uniform |
| `--max-frames` | Maximum frames to extract | 5 |
| `--translate` | Target language (zh/en/ja/ko/es/fr/de/ru) | - |
| `--whisper-model` | Whisper model size (tiny/base/small/medium/large-v3) | medium |
| `--whisper-device` | Device for Whisper (cuda/cpu) | cuda |
| `--batch-file` | File with video URLs (one per line) | - |
| `--skip-transcription` | Skip audio transcription | false |
| `--skip-analysis` | Skip image analysis | false |

## Project Structure

```
video_note_system/
├── config/           # Configuration (settings, LLM config)
├── core/             # Video download, audio extraction, transcription
├── analysis/         # Image analysis (GLM, Doubao clients)
├── utils/            # LLM client, text polisher, translator
├── generators/       # Document generators (docx, markdown, json)
├── pipeline/         # Orchestration, batch processing
├── output/           # Generated files
└── docs/             # Documentation
```

## API Selection

| Content Type | API | Reason |
|--------------|-----|--------|
| Math formulas | GLM-4.6V | Best STEM accuracy |
| Code snippets | GLM-4.6V | Strong programming knowledge |
| Chinese text/PPT | Doubao | Superior Chinese understanding |
| Text polishing | DeepSeek | Fast, cost-effective |

## Documentation

- [Quick Start Guide](docs/user/quick-start.md)
- [Configuration Guide](docs/user/configuration.md)
- [CLI Reference](docs/user/cli-reference.md)
- [Troubleshooting](docs/user/troubleshooting.md)
- [Architecture](docs/developer/architecture.md)
- [LLM Integration](docs/developer/llm-integration.md)

## Disclaimer

This tool is for **personal learning and research only**. Users are responsible for ensuring their use complies with copyright laws and platform terms of service. See [DISCLAIMER.md](DISCLAIMER.md) for details.

## License

MIT License

