# video2note - 视频笔记生成器

自动从 YouTube/Bilibili 视频生成结构化、带插图的笔记。

## 功能特性

- **双平台支持**：YouTube 和 Bilibili
- **GPU 加速转录**：Faster Whisper + CUDA，转录速度提升 5-10 倍
- **智能帧提取**：6 种策略（均匀分布、场景检测、段落边界等）
- **多模态 AI 分析**：GLM-4.6V（公式/代码）+ 豆包（中文文档）
- **文本增强**：DeepSeek 润色、摘要生成、多语言翻译
- **批量处理**：支持多视频队列处理，带进度显示
- **断点续传**：自动保存进度，中断后可恢复
- **多格式输出**：Word (.docx)、Markdown、JSON

## 快速开始

### 1. 环境配置

```bash
# 创建 conda 环境
conda create -n video_note python=3.11
conda activate video_note

# 安装 PyTorch（CUDA 12.1）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 国内用户可使用清华镜像
pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥

```bash
python main.py --setup
```

编辑 `.env` 文件：
```bash
# 视觉 API（必需，用于图像分析）
GLM_API_KEY=你的智谱API密钥          # 申请：https://open.bigmodel.cn/
ARK_API_KEY=你的豆包API密钥          # 申请：https://console.volcengine.com/

# 文本 LLM（选择一个）
DEEPSEEK_API_KEY=你的DeepSeek密钥    # 申请：https://platform.deepseek.com/
```

### 3. 生成笔记

```bash
# 基础用法
python main.py "https://www.youtube.com/watch?v=xxx"

# 指定输出格式和翻译
python main.py "https://www.bilibili.com/video/BVxxx" \
    --formats docx markdown \
    --translate en
```

## 使用示例

### 处理本地视频
```bash
python main.py "dummy" --local-video "D:/Videos/lecture.mp4"
```

### 批量处理
```bash
# 创建 videos.txt，每行一个 URL
python main.py --batch-file videos.txt
```

### 场景检测帧提取（推荐）
```bash
python main.py "URL" --frame-strategy scene --max-frames 10
```

### 生成双语笔记
```bash
# 中文视频 + 英文翻译
python main.py "https://www.bilibili.com/video/BVxxx" --translate en

# 英文视频 + 中文翻译
python main.py "https://www.youtube.com/watch?v=xxx" --translate zh
```

### 快速处理（跳过分析）
```bash
python main.py "URL" --skip-analysis --formats docx
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--formats` | 输出格式 (docx/markdown/json/all) | docx markdown json |
| `--frame-strategy` | 帧提取策略 (uniform/scene/paragraph/fixed_interval) | uniform |
| `--max-frames` | 最大提取帧数 | 5 |
| `--translate` | 翻译目标语言 (zh/en/ja/ko/es/fr/de/ru) | - |
| `--whisper-model` | Whisper 模型 (tiny/base/small/medium/large-v3) | medium |
| `--whisper-device` | 运行设备 (cuda/cpu) | cuda |
| `--batch-file` | 批量处理文件（每行一个 URL） | - |
| `--skip-transcription` | 跳过音频转录 | false |
| `--skip-analysis` | 跳过图像分析 | false |
| `-o, --output` | 输出目录 | output/notes |
| `-v, --verbose` | 详细日志 | false |

## 帧提取策略说明

| 策略 | 适用场景 | 说明 |
|------|----------|------|
| `uniform` | 大多数视频 | 开头帧 + 均匀分布的帧 |
| `scene` | 场景变化多的视频 | 基于场景切换检测 |
| `paragraph` | 讲座、演讲 | 基于语音停顿检测 |
| `fixed_interval` | 长视频 | 固定时间间隔（如每 10 秒） |

## 项目结构

```
video_note_system/
├── config/           # 配置文件（设置、LLM 配置）
├── core/             # 核心模块（下载、音频提取、转录）
├── analysis/         # 图像分析（GLM、豆包客户端）
├── utils/            # 工具类（LLM 客户端、文本润色、翻译）
├── generators/       # 文档生成器（docx、markdown、json）
├── pipeline/         # 流程编排、批量处理
├── output/           # 输出文件
│   ├── videos/       # 下载的视频
│   ├── audio/        # 提取的音频
│   ├── frames/       # 提取的帧
│   ├── transcripts/  # 转录文本
│   └── notes/        # 生成的笔记
└── docs/             # 文档
```

## API 选择策略

| 内容类型 | 使用的 API | 原因 |
|----------|-----------|------|
| 数学公式 | GLM-4.6V | STEM 内容理解最佳 |
| 代码片段 | GLM-4.6V | 编程知识丰富 |
| 中文文档/PPT | 豆包 | 中文理解能力强 |
| 文本润色 | DeepSeek | 快速、性价比高 |
| 摘要生成 | DeepSeek | 128K 上下文窗口 |

## 常见问题

### GPU 内存不足
```bash
# 使用 CPU 模式
python main.py "URL" --whisper-device cpu

# 或使用更小的模型
python main.py "URL" --whisper-model small
```

### 视频下载失败
```bash
# 配置代理（编辑 config/settings.py）
VIDEO_CONFIG = {
    "proxy": "http://127.0.0.1:7890"
}
```

### API 调用失败
- 检查 `.env` 文件中的 API 密钥是否正确
- 运行 `python main.py --setup` 验证配置
- 查看 `output/system.log` 获取详细错误信息

## 文档

- [快速开始指南](docs/user/quick-start.md)
- [配置指南](docs/user/configuration.md)
- [命令行参考](docs/user/cli-reference.md)
- [故障排查](docs/user/troubleshooting.md)
- [架构说明](docs/developer/architecture.md)
- [LLM 集成指南](docs/developer/llm-integration.md)

## 许可证

MIT License

