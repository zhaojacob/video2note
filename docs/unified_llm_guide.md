# 统一LLM架构使用指南

## 目录

1. [简介](#简介)
2. [命令行快速开始](#命令行快速开始)
3. [核心组件](#核心组件)
4. [使用示例](#使用示例)
5. [配置说明](#配置说明)
6. [迁移指南](#迁移指南)
7. [最佳实践](#最佳实践)
8. [故障排查](#故障排查)

---

## 简介

统一LLM架构提供了一个统一的接口来管理多个大语言模型（LLM）提供商，包括：

- **GLM (智谱AI)** - glm-4.6v, glm-4-flash
- **Doubao (字节跳动)** - doubao-vision
- **DeepSeek** - deepseek-chat, deepseek-v3
- **OpenAI** - gpt-4o, gpt-4o-mini
- **自定义模型** - 任何OpenAI兼容的API

### 主要特性

✅ **统一接口** - 一个管理器控制所有模型
✅ **智能降级** - 主模型失败时自动切换到备用模型
✅ **健康检查** - 自动检测模型可用性
✅ **零代码配置** - 添加新模型只需注册即可
✅ **向后兼容** - 现有代码无需修改即可运行

---

## 命令行快速开始

### 基础命令格式

```bash
python main.py <video_url> [options]
```

### 最简单的使用方式

```bash
# 处理单个YouTube视频（生成所有格式）
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**输出文件位置：**
- `output/notes/<视频标题>.docx` - Word文档
- `output/notes/<视频标题>.md` - Markdown文档
- `output/notes/<视频标题>.json` - JSON数据

### 常用命令示例

#### 1. 生成指定格式

```bash
# 只生成Word文档
python main.py "https://www.youtube.com/watch?v=xxx" --formats docx

# 只生成Markdown文档
python main.py "https://www.youtube.com/watch?v=xxx" --formats markdown

# 生成Word和Markdown（不生成JSON）
python main.py "https://www.youtube.com/watch?v=xxx" --formats docx markdown

# 生成所有格式
python main.py "https://www.youtube.com/watch?v=xxx" --formats all
```

#### 2. 批量处理多个视频

```bash
# 方式1：直接指定多个URL
python main.py \
    "https://www.youtube.com/watch?v=xxx1" \
    "https://www.youtube.com/watch?v=xxx2" \
    "https://www.youtube.com/watch?v=xxx3"

# 方式2：从文件读取URL列表
python main.py --batch-file videos.txt
```

**`videos.txt` 文件格式：**
```text
https://www.youtube.com/watch?v=xxx1
https://www.youtube.com/watch?v=xxx2
# 这是注释，会被忽略
https://bilibili.com/video/BV1xx411c7mD
```

#### 3. 处理本地视频文件

```bash
# 跳过下载，直接处理本地视频
python main.py "dummy_url" --local-video "path/to/video.mp4"
```

#### 4. 控制处理步骤

```bash
# 跳过音频转录（更快，但不生成字幕）
python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription

# 跳过图像分析（不分析视频画面）
python main.py "https://www.youtube.com/watch?v=xxx" --skip-analysis

# 同时跳过转录和分析（只下载视频）
python main.py "https://www.youtube.com/watch?v=xxx" --skip-transcription --skip-analysis
```

#### 5. 帧提取策略

```bash
# 默认策略：均匀分布（开头+4张均匀分布的帧）
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy uniform

# 场景检测策略（根据场景变化提取，节省API调用）
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy scene

# 固定间隔策略（每10秒一帧）
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy fixed_interval --frame-interval 10

# 段落边界策略（根据语音停顿提取）
python main.py "https://www.youtube.com/watch?v=xxx" --frame-strategy paragraph

# 自定义最大帧数
python main.py "https://www.youtube.com/watch?v=xxx" --max-frames 10
```

#### 6. 翻译功能

```bash
# 翻译为英文（双语输出）
python main.py "https://www.youtube.com/watch?v=xxx" --translate en

# 翻译为中文
python main.py "https://www.youtube.com/watch?v=xxx" --translate zh

# 翻译为日文
python main.py "https://www.youtube.com/watch?v=xxx" --translate ja

# 翻译为韩文
python main.py "https://www.youtube.com/watch?v=xxx" --translate ko
```

#### 7. Whisper语音识别选项

```bash
# 使用CPU而非GPU（如果没有GPU）
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-device cpu

# 使用不同的Whisper模型
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-model small   # 更快但精度较低
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-model medium  # 默认，平衡
python main.py "https://www.youtube.com/watch?v=xxx" --whisper-model large-v3 # 最精确但较慢
```

#### 8. 性能调优

```bash
# 控制API并发数（默认5）
python main.py "https://www.youtube.com/watch?v=xxx" --max-concurrent 3

# 指定输出目录
python main.py "https://www.youtube.com/watch?v=xxx" --output "my_notes"

# 启用详细日志
python main.py "https://www.youtube.com/watch?v=xxx" --verbose
```

### 实用命令

#### 系统设置和检查

```bash
# 初始化设置（创建.env模板，验证API密钥）
python main.py --setup

# 检查GPU可用性
python main.py --check-gpu

# 查看帮助信息
python main.py --help
```

### Bilibili视频支持

```bash
# 处理Bilibili视频
python main.py "https://www.bilibili.com/video/BV1xx411c7mD"

# 批量处理Bilibili视频（在videos.txt中）
python main.py --batch-file bilibili_videos.txt
```

### 完整参数列表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `urls` | 视频URL（可多个） | - |
| `--batch-file` | 从文件读取URL列表 | - |
| `-f, --formats` | 输出格式（docx/markdown/json/all） | docx markdown json |
| `-o, --output` | 输出目录 | output/notes |
| `--local-video` | 本地视频路径 | - |
| `--skip-transcription` | 跳过音频转录 | False |
| `--skip-analysis` | 跳过图像分析 | False |
| `--frame-strategy` | 帧提取策略 | uniform |
| `--frame-interval` | 固定间隔秒数 | 10.0 |
| `--max-frames` | 最大帧数 | 5 |
| `--translate` | 翻译目标语言（zh/en/ja/ko等） | - |
| `--whisper-model` | Whisper模型大小 | medium |
| `--whisper-device` | Whisper设备（cuda/cpu） | cuda |
| `--max-concurrent` | 最大并发API数 | 5 |
| `--setup` | 初始化设置 | - |
| `--check-gpu` | 检查GPU | - |
| `-v, --verbose` | 详细日志 | - |

### 组合示例

```bash
# 示例1：快速生成Word笔记（跳过分析，使用场景检测）
python main.py "https://www.youtube.com/watch?v=xxx" \
    --formats docx \
    --skip-analysis \
    --frame-strategy scene

# 示例2：高质量完整处理（所有格式，大模型，10帧）
python main.py "https://www.youtube.com/watch?v=xxx" \
    --formats all \
    --whisper-model large-v3 \
    --max-frames 10 \
    --max-concurrent 3

# 示例3：批量处理Bilibili视频，翻译为英文
python main.py --batch-file bilibili_videos.txt \
    --translate en \
    --formats docx markdown

# 示例4：本地视频，使用CPU，详细日志
python main.py "dummy" \
    --local-video "D:/Videos/tutorial.mp4" \
    --whisper-device cpu \
    --verbose \
    --formats all
```

---

## 快速开始（编程方式）

### 1. 环境变量配置

在 `.env` 文件中设置API密钥：

```bash
# GLM API (智谱AI)
GLM_API_KEY=your_glm_api_key

# Doubao API (字节跳动)
ARK_API_KEY=your_doubao_api_key

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# ModelScope Token (用于DeepSeek V3)
MODELSCOPE_TOKEN=your_modelscope_token

# OpenAI API (可选)
OPENAI_API_KEY=your_openai_api_key
```

### 2. 基础使用

```python
from utils.llm.unified_manager import UnifiedLLMManager

# 创建管理器
manager = UnifiedLLMManager()

# 列出可用模型
available = manager.list_available_models()
print(f"可用模型: {list(available.keys())}")

# 获取客户端
client = manager.get_client("glm-4-flash")

# 发送聊天请求
result = client.chat_completion([
    {"role": "user", "content": "你好，请介绍一下你自己"}
])
print(result)
```

---

## 核心组件

### 1. UnifiedLLMManager (统一管理器)

中央管理器，负责创建和管理所有LLM客户端。

**主要方法：**

| 方法 | 说明 |
|------|------|
| `get_client(model_id)` | 获取指定模型的客户端 |
| `create_client(model, api_key, base_url)` | 创建自定义客户端 |
| `chat_with_fallback(messages, providers)` | 带降级策略的聊天 |
| `analyze_image_with_fallback(image_path, prompt, providers)` | 带降级的图像分析 |
| `list_available_models()` | 列出已配置的模型 |
| `health_check(model_id)` | 检查模型健康状态 |

### 2. ModelRegistry (模型注册表)

预定义的模型配置库。

**内置模型：**

| 模型ID | 名称 | 能力 | 环境变量 |
|--------|------|------|----------|
| `glm-4-flash` | GLM-4 Flash | 文本、快速、双语 | `GLM_API_KEY` |
| `glm-4.6v` | GLM-4.6V | 视觉、思维链 | `GLM_API_KEY` |
| `doubao-vision` | Doubao Vision | 视觉、中文 | `ARK_API_KEY` |
| `deepseek-chat` | DeepSeek Chat | 文本、长上下文 | `DEEPSEEK_API_KEY` |
| `deepseek-v3` | DeepSeek V3 | 思维链、长上下文 | `MODELSCOPE_TOKEN` |
| `gpt-4o` | GPT-4o | 文本、视觉 | `OPENAI_API_KEY` |
| `gpt-4o-mini` | GPT-4o Mini | 文本、视觉、快速 | `OPENAI_API_KEY` |

### 3. BaseLLMClient (抽象基类)

所有LLM客户端的基类，定义了统一的接口。

**核心方法：**

```python
# 文本生成
chat_completion(messages, max_tokens=None, temperature=0.3)

# 异步文本生成
await chat_completion_async(messages, max_tokens=None, temperature=0.3)

# 图像分析
analyze_image(image_path, prompt, max_tokens=1000)

# 异步图像分析
await analyze_image_async(image_path, prompt, max_tokens=1000)

# 可用性检查
is_available() -> bool
```

---

## 编程方式使用示例

### 示例1：文本生成（带自动降级）

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 按优先级尝试多个模型
messages = [{"role": "user", "content": "写一篇关于人工智能的文章"}]

result = manager.chat_with_fallback(
    messages=messages,
    providers=[
        "glm-4-flash",      # 首选：快速、便宜
        "deepseek-chat",    # 备选：长上下文
        "gpt-4o-mini"       # 最后备选
    ]
)

if result:
    print("生成成功:", result)
else:
    print("所有模型都失败了")
```

### 示例2：图像分析（智能选择）

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 分析包含数学公式的图像
result = manager.analyze_image_with_fallback(
    image_path="frames/frame_001.jpg",
    prompt="请识别并解释图像中的数学公式",
    providers=[
        "glm-4.6v",         # GLM擅长公式理解
        "doubao-vision"     # 备选
    ]
)

print(result["description"])
print("关键点:", result["key_points"])
```

### 示例3：使用TextPolisher（文本打磨）

```python
from utils.text_polisher import TextPolisher

# 新方式：使用统一管理器（推荐）
polisher = TextPolisher(use_unified_manager=True)

# 或者指定特定模型
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="glm-4-flash"
)

# 打磨文本
raw_text = "这是一段需要打磨的原始文本..."
polished = polisher.polish(raw_text, video_title="测试视频")

# 旧方式：仍然支持（向后兼容）
polisher_legacy = TextPolisher(use_unified_manager=False)
```

### 示例4：使用ImageAnalyzer（图像分析）

```python
from analysis.image_analyzer import ImageAnalyzer

# 新方式：使用统一管理器（推荐）
analyzer = ImageAnalyzer(use_unified_manager=True)

# 分析单张图像
frame = {
    "path": "frames/frame_001.jpg",
    "timestamp": 10.5,
    "content_type": {
        "has_formula": True,
        "has_code": False
    }
}

result = analyzer.analyze_single(frame)
print("使用模型:", result["api_used"])
print("分析结果:", result["description"])

# 批量分析
frames = [...]  # 多个帧
results = analyzer.analyze_batch(frames, max_concurrent=5)
```

### 示例5：自定义模型

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 创建自定义客户端（例如：使用本地部署的模型）
custom_client = manager.create_client(
    model="my-custom-model",
    api_key="any-key",
    base_url="http://localhost:8000/v1",
    timeout=120,
    default_max_tokens=4096
)

# 使用自定义客户端
if custom_client and custom_client.is_available():
    result = custom_client.chat_completion([
        {"role": "user", "content": "Hello"}
    ])
    print(result)
```

### 示例6：查询可用模型

```python
from utils.llm.unified_manager import UnifiedLLMManager
from utils.llm.model_registry import ModelRegistry, ModelCapability

manager = UnifiedLLMManager()

# 方式1：列出所有已配置的模型
available = manager.list_available_models()
for model_id, info in available.items():
    print(f"{model_id}: {info['name']}")

# 方式2：按能力筛选
vision_models = ModelRegistry.list_models(capability=ModelCapability.VISION)
for model_id, model_info in vision_models.items():
    print(f"{model_id}: {model_info.name}")

# 方式3：获取特定模型信息
glm_info = ModelRegistry.get_model_info("glm-4-flash")
print(f"提供商: {glm_info.provider}")
print(f"超时: {glm_info.timeout}秒")
print(f"能力: {[c.value for c in glm_info.capabilities]}")
```

---

## 配置说明

### 任务推荐配置

系统为不同任务提供了预定义的模型推荐：

```python
from config.llm_config import get_recommended_models, get_fallback_chain

# 文本打磨任务
polish_config = get_recommended_models("polish")
print("推荐模型:", polish_config["models"])
print("降级链:", polish_config["fallback"])

# 图像公式识别任务
formula_config = get_recommended_models("vision_formula")
print("推荐模型:", formula_config["models"])

# 获取降级链
text_fallback = get_fallback_chain("text")
print("文本任务降级链:", text_fallback)
```

### 全局配置（settings.py）

```python
# config/settings.py

UNIFIED_LLM_CONFIG = {
    # 启用统一管理器
    "enabled": True,

    # 默认文本模型
    "default_text_model": "glm-4-flash",

    # 默认视觉模型
    "default_vision_model": "glm-4.6v",

    # 启用降级策略
    "enable_fallback": True,

    # 最大降级重试次数
    "max_fallback_retries": 3,

    # 启用健康检查
    "enable_health_check": True,
}
```

### 环境变量控制

```bash
# .env文件

# 启用统一管理器（默认false）
USE_UNIFIED_LLM=true

# 默认文本模型
DEFAULT_TEXT_MODEL=glm-4-flash

# 默认视觉模型
DEFAULT_VISION_MODEL=glm-4.6v
```

---

## 迁移指南

### 从旧代码迁移到新架构

#### 场景1：直接使用LLMClient

**旧代码：**
```python
from utils.llm_client import LLMClient

client = LLMClient(
    api_key="xxx",
    base_url="https://api.example.com/v1",
    model="model-name"
)
result = client.chat_completion(messages)
```

**新代码：**
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()
client = manager.get_client("glm-4-flash")
result = client.chat_completion(messages)
```

#### 场景2：使用GLMClient

**旧代码：**
```python
from analysis.glm_client import GLMClient

client = GLMClient()
result = client.analyze("image.jpg", "描述这个图像")
```

**新代码：**
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()
result = manager.analyze_image_with_fallback(
    image_path="image.jpg",
    prompt="描述这个图像",
    providers=["glm-4.6v", "doubao-vision"]
)
```

#### 场景3：启用TextPolisher新架构

**修改代码：**
```python
# 只需添加一个参数
polisher = TextPolisher(use_unified_manager=True)
```

**或在环境变量中设置：**
```bash
USE_UNIFIED_LLM=true
```

---

## 最佳实践

### 1. 选择合适的模型

| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| 文本打磨 | `glm-4-flash` | 快速、便宜、中文优秀 |
| 长文本总结 | `deepseek-v3` | 128K上下文、思维链 |
| 数学公式 | `glm-4.6v` | 思维链、公式理解强 |
| 代码识别 | `glm-4.6v` | 代码理解能力强 |
| 中文文档 | `doubao-vision` | 中文文档理解优秀 |
| 通用视觉 | `glm-4.6v` | 综合能力强 |

### 2. 设置合理的降级链

```python
# 好的降级链：按成本和速度排序
fallback_chain = [
    "glm-4-flash",      # 免费/便宜、快速
    "deepseek-chat",    # 便宜、可靠
    "gpt-4o-mini"       # 最后备选
]

# 避免全部使用昂贵的模型
bad_fallback = [
    "gpt-4o",           # 太贵
    "gpt-4o",           # 重复
    "gpt-4o"            # 没有备选
]
```

### 3. 处理错误

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Hello"}],
    providers=["glm-4-flash", "deepseek-chat"]
)

if result is None:
    # 所有模型都失败了
    print("错误：所有模型都不可用")
    # 检查配置
    available = manager.list_available_models()
    if not available:
        print("请检查环境变量中的API密钥配置")
    else:
        print(f"可用模型: {list(available.keys())}")
else:
    print("成功:", result)
```

### 4. 性能优化

```python
# 批量处理（使用统一的并发控制）
messages_list = [msg1, msg2, msg3, ...]

results = manager.batch_chat(
    messages_list=messages_list,
    provider="glm-4-flash",
    max_concurrent=5  # 控制并发数
)
```

---

## 故障排查

### 问题1：模型不可用

**症状：**
```
WARNING: API key not found for glm-4-flash
```

**解决方案：**
1. 检查 `.env` 文件是否存在
2. 确认环境变量已设置：`GLM_API_KEY=xxx`
3. 重启应用以加载新的环境变量

### 问题2：所有模型都失败

**症状：**
```
ERROR: All providers failed
```

**诊断步骤：**
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 1. 检查可用模型
available = manager.list_available_models()
print(f"可用模型: {list(available.keys())}")

# 2. 健康检查
for model_id in available.keys():
    is_healthy = manager.health_check(model_id)
    print(f"{model_id}: {'健康' if is_healthy else '不健康'}")
```

### 问题3：超时错误

**症状：**
```
WARNING: Request timeout
```

**解决方案：**
```python
# 创建自定义客户端，增加超时时间
client = manager.create_client(
    model="your-model",
    api_key="xxx",
    base_url="https://api.example.com/v1",
    timeout=300  # 5分钟超时
)
```

### 问题4：Unicode编码错误（Windows）

**症状：**
```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**解决方案：**
在代码开头添加：
```python
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## 附录

### 完整API参考

#### UnifiedLLMManager

```python
class UnifiedLLMManager:
    def __init__(self)

    def get_client(
        self,
        model_id: str,
        force_refresh: bool = False
    ) -> Optional[BaseLLMClient]

    def create_client(
        self,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs
    ) -> Optional[BaseLLMClient]

    def chat_with_fallback(
        self,
        messages: List[Dict[str, str]],
        providers: List[str],
        **kwargs
    ) -> Optional[str]

    def analyze_image_with_fallback(
        self,
        image_path: Union[str, Path],
        prompt: str,
        providers: List[str],
        **kwargs
    ) -> Optional[Dict[str, Any]]

    def list_available_models(
        self,
        capability: Optional[ModelCapability] = None
    ) -> Dict[str, Any]

    def health_check(self, model_id: str) -> bool
```

#### ModelRegistry

```python
class ModelRegistry:
    @staticmethod
    def get_model_info(model_id: str) -> Optional[ModelInfo]

    @staticmethod
    def list_models(
        capability: Optional[ModelCapability] = None,
        provider: Optional[str] = None
    ) -> Dict[str, ModelInfo]

    @staticmethod
    def register_custom_model(
        model_id: str,
        model_info: ModelInfo
    )

    @staticmethod
    def get_vision_models() -> Dict[str, ModelInfo]

    @staticmethod
    def get_text_models() -> Dict[str, ModelInfo]

    @staticmethod
    def get_thinking_models() -> Dict[str, ModelInfo]
```

### 更新日志

- **v1.0** (2025-01) - 初始版本
  - 创建统一LLM架构
  - 支持7个预定义模型
  - 实现智能降级策略
  - 添加完整的测试套件

### 相关文档

- [测试文档](../tests/test_unified_llm.py) - 完整的测试用例
- [API文档](./api_reference.md) - 详细的API参考（待创建）
- [架构设计](./architecture.md) - 系统架构说明（待创建）

---

## 支持

如有问题或建议，请：
1. 查看 [故障排查](#故障排查) 部分
2. 运行测试：`python tests/test_unified_llm.py`
3. 提交 Issue 到 GitHub 仓库
