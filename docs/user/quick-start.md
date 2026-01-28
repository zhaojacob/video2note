# 快速开始指南

## 5 分钟快速上手

### 1. 配置 API Keys

编辑 `.env` 文件：

```env
# 视觉 API（必需）
GLM_API_KEY=your_glm_api_key
ARK_API_KEY=your_ark_api_key

# 文本 LLM（选择一个）
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 2. 获取 API Keys

| Provider | 申请地址 | 用途 |
|----------|----------|------|
| 智谱 AI (GLM) | https://open.bigmodel.cn/ | 图像分析（公式、代码） |
| 字节跳动豆包 | https://console.volcengine.com/ | 图像分析（中文文档） |
| DeepSeek | https://platform.deepseek.com/ | 文本润色、摘要、翻译 |

### 3. 验证配置

```bash
python main.py --setup
```

### 4. 开始使用

```bash
# 处理 YouTube 视频
python main.py "https://www.youtube.com/watch?v=xxxxx"

# 处理 Bilibili 视频
python main.py "https://www.bilibili.com/video/BVxxxxx"
```

---

## 常用命令

### 基础用法

```bash
# 生成所有格式（默认）
python main.py "VIDEO_URL"

# 只生成 Word 文档
python main.py "VIDEO_URL" --formats docx

# 生成 Word 和 Markdown
python main.py "VIDEO_URL" --formats docx markdown
```

### 本地视频

```bash
python main.py "dummy" --local-video "path/to/video.mp4"
```

### 批量处理

```bash
# 创建 videos.txt，每行一个 URL
python main.py --batch-file videos.txt
```

### 翻译功能

```bash
# 翻译为中文（双语输出）
python main.py "VIDEO_URL" --translate zh

# 翻译为英文
python main.py "VIDEO_URL" --translate en
```

### 帧提取策略

```bash
# 场景检测（推荐，节省 API 调用）
python main.py "VIDEO_URL" --frame-strategy scene

# 固定间隔（每 15 秒一帧）
python main.py "VIDEO_URL" --frame-strategy fixed_interval --frame-interval 15
```

---

## 输出文件

生成的文件位于 `output/notes/` 目录：

- `<视频标题>.docx` - Word 文档
- `<视频标题>.md` - Markdown 文档
- `<视频标题>.json` - JSON 数据

---

## 下一步

- [配置指南](configuration.md) - 详细配置说明
- [命令行参考](cli-reference.md) - 完整参数列表
- [故障排查](troubleshooting.md) - 常见问题解决

