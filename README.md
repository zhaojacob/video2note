# Video Note Generation System

An intelligent system that automatically generates structured, illustrated notes from videos. Supports YouTube and Bilibili platforms with GPU-accelerated transcription and multi-modal AI analysis.

## Features

- **Dual Platform Support**: YouTube and Bilibili
- **GPU-Accelerated Transcription**: Faster Whisper with CUDA support
- **Smart Frame Extraction**: Scene detection + transcript alignment
- **Multi-Modal Analysis**: GLM-4.6V + Doubao Vision hybrid
- **Multiple Output Formats**: Word, Markdown, JSON
- **Content Recognition**: Formulas, code, charts, text detection

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
```
GLM_API_KEY=your_glm_api_key_here
DOUBAO_API_KEY=your_doubao_api_key_here
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
├── core/                # Core modules
│   ├── video_downloader.py
│   ├── audio_extractor.py
│   ├── transcriber.py        # Whisper GPU
│   └── frame_extractor.py    # Scene detection
├── analysis/            # AI analysis
│   ├── glm_client.py         # GLM-4.6V
│   ├── doubao_client.py      # Doubao Vision
│   └── image_analyzer.py     # Unified analyzer
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
    └── notes/
```

## API Requirements

### GLM-4.6V
- Get API key: https://open.bigmodel.cn/
- Models: `glm-4.6v` (flagship), `glm-4.6v-flashx` (lightweight)
- Best for: Formulas, code, STEM content

### Doubao Vision
- Get API key: https://www.volcengine.com/
- Model: `doubao-vision-pro-32k`
- Best for: Chinese text, PPT, documents

## Performance

| Video Length | Processing Time | Cost |
|-------------|----------------|------|
| 10 minutes   | ~5 minutes     | ¥1-2 |
| 30 minutes   | ~15 minutes    | ¥2-4 |
| 1 hour       | ~25 minutes    | ¥3-6 |

*Assumes GPU acceleration, medium Whisper model*

## CLI Options

```
python main.py <video_url> [options]

Options:
  -f, --formats {docx,markdown,json,all}
                        Output formats (default: docx markdown json)
  --local-video PATH    Use local video file
  --skip-transcription  Skip audio transcription
  --skip-analysis       Skip image analysis
  --whisper-model {tiny,base,small,medium,large-v3}
                        Whisper model size (default: medium)
  --whisper-device {cuda,cpu}
                        Device for Whisper (default: cuda)
  --max-concurrent N    Max concurrent API calls (default: 5)
  --setup               Create .env template and validate keys
  --check-gpu           Check GPU availability
  -v, --verbose         Enable verbose logging
```

## Troubleshooting

### CUDA Not Available
```bash
# Check GPU
python main.py --check-gpu

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### API Key Errors
```bash
# Validate configuration
python main.py --setup

# Check .env file exists in video_note_system/
cat .env
```

### Video Download Fails
- Check your internet connection
- For restricted content, export browser cookies:
  ```bash
  # Chrome
  yt-dlp --cookies-from-browser chrome --cookies cookies.txt
  ```

### Memory Issues
- Use smaller Whisper model: `--whisper-model small`
- Use CPU instead: `--whisper-device cpu`
- Skip analysis: `--skip-analysis`

## Architecture

### Pipeline Flow

1. **Download** → `VideoDownloader` (yt-dlp)
2. **Extract Audio** → `AudioExtractor` (pydub)
3. **Transcribe** → `Transcriber` (faster-whisper + CUDA)
4. **Detect Scenes** → `SceneDetector` (PySceneDetect)
5. **Extract Frames** → `FrameExtractor` (OpenCV)
6. **Analyze Images** → `ImageAnalyzer` (GLM + Doubao)
7. **Structure** → `Structurer` (content organization)
8. **Generate** → `Generators` (Word/MD/JSON)

### API Selection Strategy

| Content Type | API | Reason |
|--------------|-----|--------|
| Formulas | GLM-4.6V | Best STEM accuracy |
| Code | GLM-4.6V | Strong programming knowledge |
| Charts | GLM-4.6V | 128k context, detailed analysis |
| Chinese Text | Doubao | Superior Chinese understanding |
| PPT/Slides | Doubao | Better layout recognition |
| General | GLM 70% / Doubao 30% | Load balancing |

## License

MIT License - feel free to use and modify.

## Contributing

Contributions welcome! Areas for improvement:
- More video platforms
- Speaker diarization
- Better summarization
- Additional output formats
- Web UI

## Support

For issues and questions, please check the troubleshooting section or create an issue in the repository.
