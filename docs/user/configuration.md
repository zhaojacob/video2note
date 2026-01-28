# 配置指南

## API Keys 配置

### 必需的 API Keys

编辑项目根目录的 `.env` 文件：

```env
# 视觉 API（必需，用于图像分析）
GLM_API_KEY=your_glm_api_key          # 智谱 AI
ARK_API_KEY=your_ark_api_key          # 字节跳动豆包

# 文本 LLM（选择一个）
DEEPSEEK_API_KEY=your_deepseek_key    # DeepSeek（推荐，性价比高）
```

### 获取 API Keys

| Provider | 申请地址 | 用途 |
|----------|----------|------|
| 智谱 AI (GLM) | https://open.bigmodel.cn/ | 图像分析（公式、代码） |
| 字节跳动豆包 | https://console.volcengine.com/ | 图像分析（中文文档） |
| DeepSeek | https://platform.deepseek.com/ | 文本润色、摘要、翻译 |
| ModelScope | https://www.modelscope.cn/ | 深度思考（可选） |
| OpenAI | https://platform.openai.com/ | 备选（可选） |

### 验证配置

```bash
python main.py --setup
```

---

## Provider 配置

### 默认 Provider 设置

在 `.env` 中配置默认使用的 Provider：

```env
# Provider 默认配置
DEFAULT_TEXT_PROVIDER=zhipu           # 文本任务
DEFAULT_VISION_PROVIDER=zhipu         # 视觉任务
DEFAULT_THINKING_PROVIDER=modelscope  # 深度思考任务

# 模型默认配置
DEFAULT_TEXT_MODEL=glm-4-flash
DEFAULT_VISION_MODEL=glm-4.6v
```

### 内置 Provider 列表

| Provider ID | 名称 | 支持模型 | 能力 |
|-------------|------|----------|------|
| `zhipu` | 智谱 AI | glm-4-flash, glm-4.6v, glm-4 | 文本、视觉、双语 |
| `deepseek` | DeepSeek | deepseek-chat | 文本、长上下文 |
| `bytedance` | 豆包 | doubao-vision | 视觉、双语 |
| `modelscope` | ModelScope | deepseek-v3 | 文本、深度思考 |
| `openai` | OpenAI | gpt-4o, gpt-4o-mini | 文本、视觉 |

### API 选择策略

| 内容类型 | 推荐 Provider | 原因 |
|----------|---------------|------|
| 数学公式 | GLM-4.6V | STEM 内容理解最佳 |
| 代码片段 | GLM-4.6V | 编程知识丰富 |
| 中文文档/PPT | 豆包 | 中文理解能力强 |
| 文本润色 | DeepSeek | 快速、性价比高 |
| 摘要生成 | DeepSeek | 128K 上下文窗口 |

---

## 视频下载配置

### 代理设置

编辑 `config/settings.py`：

```python
VIDEO_CONFIG = {
    "proxy": "http://127.0.0.1:7890",  # 代理地址
    "timeout": 60,
}
```

或在 `.env` 中设置：

```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### Cookie 配置（Bilibili）

对于需要登录的 Bilibili 视频：

```bash
# 导出浏览器 cookies
python main.py "URL" --cookies-from-browser chrome
```

---

## Whisper 配置

### 模型选择

| 模型 | 大小 | 速度 | 准确度 | 推荐场景 |
|------|------|------|--------|----------|
| `tiny` | 39M | 最快 | 较低 | 快速测试 |
| `base` | 74M | 快 | 一般 | 简单内容 |
| `small` | 244M | 中等 | 良好 | 日常使用 |
| `medium` | 769M | 较慢 | 很好 | 默认推荐 |
| `large-v3` | 1.5G | 最慢 | 最佳 | 高质量需求 |

### GPU 配置

```bash
# 使用 GPU（默认）
python main.py "URL" --whisper-device cuda

# 使用 CPU（显存不足时）
python main.py "URL" --whisper-device cpu

# 使用更小的模型
python main.py "URL" --whisper-model small
```

---

## 输出配置

### 输出目录结构

```
output/
├── videos/       # 下载的视频
├── audio/        # 提取的音频
├── frames/       # 提取的帧
├── transcripts/  # 转录文本
├── notes/        # 生成的笔记
└── checkpoints/  # 断点续传文件
```

### 自定义输出目录

```bash
python main.py "URL" -o "D:/MyNotes"
```

---

## 高级配置

### 并发和重试

在 `config/llm_config.yaml` 中配置：

```yaml
concurrency:
  max_concurrent: 5           # 最大并发请求数
  max_retries: 3              # 最大重试次数
  retry_delay: 2              # 重试延迟（秒）
  exponential_backoff: true   # 指数退避
```

### 断点续传

```yaml
concurrency:
  enable_checkpoint: true
  checkpoint_dir: "output/checkpoints"
```

### 添加自定义 Provider

在 `.env` 中添加（最多支持 10 个）：

```env
CUSTOM_PROVIDER_1_NAME=MyProxy
CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o
```

---

## 配置优先级

```
运行时参数 > .env 文件 > 默认值
```

示例：
```bash
# 命令行参数优先级最高
python main.py "URL" --whisper-model large-v3
```

---

## 下一步

- [命令行参考](cli-reference.md) - 完整参数列表
- [故障排查](troubleshooting.md) - 常见问题解决
