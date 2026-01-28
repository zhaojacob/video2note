# 命令行参考

## 基本语法

```bash
python main.py [URL...] [OPTIONS]
```

---

## 输入选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `URL` | 视频 URL（支持多个） | `python main.py "URL1" "URL2"` |
| `--batch-file` | 批量处理文件（每行一个 URL） | `--batch-file videos.txt` |
| `--local-video` | 本地视频文件路径 | `--local-video "D:/video.mp4"` |

---

## 输出选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--formats` | 输出格式 | `docx markdown json` |
| `-o, --output` | 输出目录 | `output/notes` |

可选格式：`docx`, `markdown`, `json`, `all`

```bash
# 只生成 Word
python main.py "URL" --formats docx

# 生成 Word 和 Markdown
python main.py "URL" --formats docx markdown

# 生成所有格式
python main.py "URL" --formats all
```

---

## 帧提取选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--frame-strategy` | 帧提取策略 | `uniform` |
| `--max-frames` | 最大提取帧数 | `5` |
| `--frame-interval` | 固定间隔（秒） | `15` |

### 帧提取策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `uniform` | 均匀分布 + 开头帧 | 大多数视频 |
| `scene` | 场景切换检测 | 场景变化多的视频 |
| `paragraph` | 语音停顿检测 | 讲座、演讲 |
| `fixed_interval` | 固定时间间隔 | 长视频 |
| `keyframe` | 关键帧提取 | 技术视频 |
| `hybrid` | 混合策略 | 复杂内容 |

```bash
# 场景检测（推荐）
python main.py "URL" --frame-strategy scene --max-frames 10

# 固定间隔（每 30 秒）
python main.py "URL" --frame-strategy fixed_interval --frame-interval 30
```

---

## 转录选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--whisper-model` | Whisper 模型 | `medium` |
| `--whisper-device` | 运行设备 | `cuda` |
| `--skip-transcription` | 跳过转录 | `false` |

### Whisper 模型

| 模型 | 大小 | 速度 | 准确度 |
|------|------|------|--------|
| `tiny` | 39M | ★★★★★ | ★★ |
| `base` | 74M | ★★★★ | ★★★ |
| `small` | 244M | ★★★ | ★★★★ |
| `medium` | 769M | ★★ | ★★★★★ |
| `large-v3` | 1.5G | ★ | ★★★★★ |

```bash
# 使用 CPU（显存不足时）
python main.py "URL" --whisper-device cpu

# 使用更小的模型
python main.py "URL" --whisper-model small
```

---

## 分析选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--skip-analysis` | 跳过图像分析 | `false` |

```bash
# 快速处理（跳过 AI 图像分析）
python main.py "URL" --skip-analysis
```

---

## 翻译选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--translate` | 翻译目标语言 | - |

支持语言：`zh`（中文）, `en`（英文）, `ja`（日语）, `ko`（韩语）, `es`（西班牙语）, `fr`（法语）, `de`（德语）, `ru`（俄语）

```bash
# 英文视频翻译为中文
python main.py "https://youtube.com/..." --translate zh

# 中文视频翻译为英文
python main.py "https://bilibili.com/..." --translate en
```

---

## 其他选项

| 参数 | 说明 |
|------|------|
| `--setup` | 运行配置向导 |
| `-v, --verbose` | 详细日志输出 |
| `--help` | 显示帮助信息 |

---

## 使用示例

### 基础用法

```bash
# 处理单个视频
python main.py "https://www.youtube.com/watch?v=xxx"

# 处理 Bilibili 视频
python main.py "https://www.bilibili.com/video/BVxxx"
```

### 本地视频

```bash
python main.py "dummy" --local-video "D:/Videos/lecture.mp4"
```

### 批量处理

```bash
# 创建 videos.txt
# https://youtube.com/watch?v=xxx1
# https://youtube.com/watch?v=xxx2
# # 这是注释，会被忽略

python main.py --batch-file videos.txt
```

### 高质量输出

```bash
python main.py "URL" \
    --whisper-model large-v3 \
    --frame-strategy scene \
    --max-frames 15 \
    --formats docx markdown
```

### 快速处理

```bash
python main.py "URL" \
    --whisper-model small \
    --skip-analysis \
    --formats docx
```

### 双语笔记

```bash
# 英文视频 + 中文翻译
python main.py "https://youtube.com/..." \
    --translate zh \
    --formats docx
```

---

## 批量文件格式

`videos.txt` 示例：

```
# 教程视频
https://www.youtube.com/watch?v=abc123
https://www.youtube.com/watch?v=def456

# Bilibili 视频
https://www.bilibili.com/video/BVxxx

# 空行会被忽略
```

---

## 退出码

| 退出码 | 说明 |
|--------|------|
| `0` | 成功 |
| `1` | 处理失败（批量模式下部分失败也返回 1） |

---

## 下一步

- [配置指南](configuration.md) - 详细配置说明
- [故障排查](troubleshooting.md) - 常见问题解决
