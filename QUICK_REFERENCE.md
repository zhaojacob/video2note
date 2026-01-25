# Quick Reference Guide

## Installation Commands

### Option 1: Manual Setup
```bash
# Create environment
conda create -n video_note python=3.11
conda activate video_note

# Install PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies
cd F:\anaconda_learning\video_note_system
pip install -r requirements.txt

# Setup API keys
python main.py --setup
```

### Option 2: Automated Setup
```bash
cd F:\anaconda_learning\video_note_system
python setup_env.py
```

## Common Usage Patterns

### Basic Usage
```bash
# Generate all formats from YouTube
python main.py "https://www.youtube.com/watch?v=xxx"

# Generate from Bilibili
python main.py "https://www.bilibili.com/video/BVxxx"

# Use local video file
python main.py "dummy" --local-video "path/to/video.mp4"
```

### Format Selection
```bash
# Word document only
python main.py "URL" --formats docx

# Markdown only
python main.py "URL" --formats markdown

# All formats
python main.py "URL" --formats all

# Multiple formats
python main.py "URL" --formats docx markdown
```

### Performance Tuning
```bash
# Faster processing (smaller model)
python main.py "URL" --whisper-model small

# CPU mode (no GPU)
python main.py "URL" --whisper-device cpu

# Skip transcription for speed
python main.py "URL" --skip-transcription

# Skip analysis to save API costs
python main.py "URL" --skip-analysis

# More concurrent API calls
python main.py "URL" --max-concurrent 10
```

## API Key Setup

### Get API Keys
1. **GLM-4.6V**: https://open.bigmodel.cn/
2. **Doubao Vision**: https://www.volcengine.com/

### Configure
Edit `.env` file:
```bash
GLM_API_KEY=your_key_here
DOUBAO_API_KEY=your_key_here
```

### Validate
```bash
python main.py --setup
```

## GPU Check

```bash
# Check if GPU is available
python main.py --check-gpu
```

Expected output:
```
PyTorch version: 2.x.x
CUDA available: True
GPU 0: NVIDIA GeForce RTX ...
  Memory: 8.00 GB
```

## Troubleshooting

### "CUDA not available"
```bash
# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### "API key not found"
```bash
# Create .env file
python main.py --setup

# Edit manually
notepad .env
```

### "Video download failed"
```bash
# For member-only content, export cookies
yt-dlp --cookies-from-browser chrome URL

# Use proxy
export HTTP_PROXY=http://127.0.0.1:7890
```

### "Out of memory"
```bash
# Use smaller model
python main.py "URL" --whisper-model base

# Use CPU
python main.py "URL" --whisper-device cpu
```

## Output Files

Generated files are in `output/notes/`:
- `<title>.docx` - Word document
- `<title>.md` - Markdown file
- `<title>.json` - Structured JSON

Intermediate files in `output/`:
- `videos/` - Downloaded videos
- `audio/` - Extracted audio
- `frames/` - Video frames
- `transcripts/` - Transcription data

## Python API Usage

```python
from pipeline.pipeline_orchestrator import PipelineOrchestrator

# Initialize
orchestrator = PipelineOrchestrator(
    whisper_model_size="medium",
    whisper_device="cuda",
    max_concurrent_api=5
)

# Run pipeline
results = orchestrator.run(
    video_url="https://www.youtube.com/watch?v=xxx",
    output_formats=["docx", "markdown", "json"]
)

# Check results
if results["success"]:
    for fmt, path in results["outputs"].items():
        print(f"{fmt}: {path}")
```

## Module Reference

### Core Modules
- `video_downloader.py` - YouTube/Bilibili download
- `audio_extractor.py` - Audio extraction
- `transcriber.py` - Whisper GPU transcription
- `frame_extractor.py` - Frame extraction & deduplication

### Analysis Modules
- `glm_client.py` - GLM-4.6V API client
- `doubao_client.py` - Doubao Vision API client
- `image_analyzer.py` - Unified image analysis
- `structurer.py` - Content structuring

### Generators
- `docx_generator.py` - Word document
- `markdown_generator.py` - Markdown file
- `json_generator.py` - JSON export

## Performance Benchmarks

| Task | Time (GPU) | Time (CPU) |
|------|-----------|-----------|
| Download 1h video | 2-5 min | 2-5 min |
| Extract audio | <1 min | <1 min |
| Transcribe (medium) | 5-10 min | 30-40 min |
| Extract frames | 2-3 min | 2-3 min |
| Analyze frames | 3-5 min | 3-5 min |
| **Total** | **15-25 min** | **45-60 min** |

## Cost Estimation

Per 1-hour video:
- Whisper: Free (local)
- GLM-4.6V: ¥2-4 (30-40 frames)
- Doubao: ¥1-2 (10-15 frames)
- **Total**: ¥3-6

## Tips & Best Practices

1. **First Time**: Start with short video (<10 min) to test
2. **API Selection**: System auto-selects best API per content type
3. **Frame Rate**: 10 sec interval = ~360 frames/hour
4. **Cost Saving**: Use `--skip-analysis` for no API calls
5. **Speed**: Use `--whisper-model small` for 2x faster transcription
6. **Quality**: Use `--whisper-model medium` for best accuracy

## Contact & Support

- Check logs: `output/system.log`
- Verbose mode: `--verbose` flag
- GPU issues: `python main.py --check-gpu`
- API issues: `python main.py --setup`
