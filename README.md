# video2note

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

Frame Extraction:
  --frame-strategy {transcript,interval,scene}
                        Frame extraction strategy (default: transcript)
                        - transcript: Align frames with speech timestamps, random sample
                        - interval: Fixed interval based on video duration
                        - scene: PySceneDetect scene change detection

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

### Examples

```bash
# Basic usage
python main.py "https://www.youtube.com/watch?v=xxx"

# Local video with translation to English
python main.py "dummy" --local-video "lecture.mp4" --translate en

# Scene detection + Chinese translation + DOCX only
python main.py "https://www.youtube.com/watch?v=xxx" \
    --frame-strategy scene \
    --translate zh \
    --formats docx

# Fast processing (skip transcription)
python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription

# CPU mode (no GPU)
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-device cpu
```

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
