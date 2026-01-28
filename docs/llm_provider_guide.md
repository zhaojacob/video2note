# 如何指定LLM Provider

本文档详细说明如何在统一LLM架构中指定和切换不同的LLM提供商（Provider）。

---

## 目录

1. [快速概览](#快速概览)
2. [方式1：环境变量配置（推荐）](#方式1环境变量配置推荐)
3. [方式2：代码中直接指定](#方式2代码中直接指定)
4. [方式3：编程方式使用](#方式3编程方式使用)
5. [方式4：降级策略配置](#方式4降级策略配置)
6. [常见场景示例](#常见场景示例)
7. [Provider能力对照表](#provider能力对照表)

---

## 快速概览

### 指定Provider的三种层次

| 层次 | 说明 | 适用场景 |
|------|------|----------|
| **全局默认** | 通过环境变量设置系统级默认 | 生产环境、长期使用 |
| **任务级别** | 通过配置模块为特定任务设置 | 开发、测试 |
| **调用级别** | 代码中直接指定模型ID | 一次性使用、特殊需求 |

### 支持的Provider

| Provider | 模型ID | 用途 | 环境变量 |
|----------|--------|------|----------|
| **GLM** | `glm-4-flash` | 文本生成、快速 | `GLM_API_KEY` |
| **GLM** | `glm-4.6v` | 图像分析、思维链 | `GLM_API_KEY` |
| **Doubao** | `doubao-vision` | 中文视觉理解 | `ARK_API_KEY` |
| **DeepSeek** | `deepseek-chat` | 长文本、便宜 | `DEEPSEEK_API_KEY` |
| **DeepSeek** | `deepseek-v3` | 思维链、长上下文 | `MODELSCOPE_TOKEN` |
| **OpenAI** | `gpt-4o` | 通用视觉 | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | 快速通用 | `OPENAI_API_KEY` |

---

## 方式1：环境变量配置（推荐）

### 1.1 启用统一LLM架构

在 `.env` 文件中添加：

```bash
# 启用统一LLM管理器
USE_UNIFIED_LLM=true

# 文本任务默认模型
DEFAULT_TEXT_MODEL=glm-4-flash

# 视觉任务默认模型
DEFAULT_VISION_MODEL=glm-4.6v
```

### 1.2 配置API密钥

```bash
# GLM API (智谱AI)
GLM_API_KEY=your_glm_api_key_here

# Doubao API (字节跳动)
ARK_API_KEY=your_doubao_api_key_here

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ModelScope Token (用于DeepSeek V3)
MODELSCOPE_TOKEN=your_modelscope_token_here

# OpenAI API (可选)
OPENAI_API_KEY=your_openai_api_key_here
```

### 1.3 验证配置

```bash
# 运行测试
python tests/test_unified_llm.py

# 查看可用模型
python -c "from utils.llm.unified_manager import UnifiedLLMManager; print(UnifiedLLMManager().list_available_models())"
```

### 1.4 使用默认Provider

配置完成后，系统会自动使用默认的Provider：

```python
from utils.text_polisher import TextPolisher

# 自动使用 DEFAULT_TEXT_MODEL (glm-4-flash)
polisher = TextPolisher(use_unified_manager=True)
result = polisher.polish("需要打磨的文本")
```

---

## 方式2：代码中直接指定

### 2.1 TextPolisher - 指定模型

```python
from utils.text_polisher import TextPolisher

# 方式1：使用model_id参数（推荐）
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="glm-4-flash"  # 指定使用GLM-4 Flash
)

# 方式2：使用DeepSeek
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="deepseek-chat"
)

# 方式3：使用GPT-4o
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="gpt-4o-mini"
)
```

### 2.2 ImageAnalyzer - 指定模型

```python
from analysis.image_analyzer import ImageAnalyzer

# 启用统一管理器（会自动选择最佳模型）
analyzer = ImageAnalyzer(use_unified_manager=True)

# 分析图像（自动选择：公式用GLM，中文用Doubao）
result = analyzer.analyze_single(frame)
```

### 2.3 直接使用UnifiedLLMManager

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 获取特定模型客户端
glm_client = manager.get_client("glm-4-flash")
deepseek_client = manager.get_client("deepseek-chat")
gpt_client = manager.get_client("gpt-4o-mini")

# 使用指定客户端
result = glm_client.chat_completion([
    {"role": "user", "content": "Hello"}
])
```

### 2.4 自定义Provider

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 创建自定义模型客户端
custom_client = manager.create_client(
    model="my-custom-model",
    api_key="your-api-key",
    base_url="https://api.example.com/v1",
    timeout=120,
    default_max_tokens=4096
)

# 使用自定义客户端
result = custom_client.chat_completion(messages)
```

---

## 方式3：编程方式使用

### 3.1 单次调用指定Provider

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 使用降级策略，指定provider优先级
result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "写一篇文章"}],
    providers=[
        "glm-4-flash",      # 首选
        "deepseek-chat",    # 备选
        "gpt-4o-mini"       # 最后备选
    ]
)
```

### 3.2 图像分析指定Provider

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 为图像分析指定provider优先级
result = manager.analyze_image_with_fallback(
    image_path="frame.jpg",
    prompt="识别图像中的数学公式",
    providers=[
        "glm-4.6v",         # GLM擅长公式
        "doubao-vision"     # 备选
    ]
)
```

### 3.3 动态选择Provider

```python
from utils.llm.unified_manager import UnifiedLLMManager
from utils.llm.model_registry import ModelCapability

manager = UnifiedLLMManager()

# 获取所有支持视觉的模型
vision_models = manager.list_available_models(capability=ModelCapability.VISION)

# 选择第一个可用的视觉模型
if vision_models:
    first_model = list(vision_models.keys())[0]
    client = manager.get_client(first_model)
    print(f"使用模型: {first_model}")
```

---

## 方式4：降级策略配置

### 4.1 使用预定义降级链

```python
from config.llm_config import get_fallback_chain

# 获取文本任务的降级链
text_fallback = get_fallback_chain("text")
# 返回: ["glm-4-flash", "deepseek-chat", "gpt-4o-mini"]

# 获取视觉任务的降级链
vision_fallback = get_fallback_chain("vision")
# 返回: ["glm-4.6v", "doubao-vision", "gpt-4o"]
```

### 4.2 自定义降级链

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 自定义降级顺序（按成本排序）
custom_fallback = [
    "glm-4-flash",      # 免费/最便宜
    "deepseek-chat",    # 便宜
    "gpt-4o-mini"       # 较贵
]

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Hello"}],
    providers=custom_fallback
)
```

### 4.3 任务特定配置

```python
from config.llm_config import get_recommended_models

# 获取不同任务的推荐模型
polish_config = get_recommended_models("polish")
# {"models": ["glm-4-flash", "deepseek-chat"], "fallback": [...], "reason": "..."}

vision_formula_config = get_recommended_models("vision_formula")
# {"models": ["glm-4.6v"], "fallback": ["doubao-vision"], ...}

# 使用推荐配置
manager = UnifiedLLMManager()
result = manager.chat_with_fallback(
    messages=[...],
    providers=polish_config["fallback"]
)
```

---

## 常见场景示例

### 场景1：快速便宜（推荐）

```python
# 环境变量
DEFAULT_TEXT_MODEL=glm-4-flash

# 或代码指定
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="glm-4-flash"
)
```

### 场景2：长文本处理

```python
# 长文本（如30分钟视频转录）使用DeepSeek V3
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="deepseek-v3"  # 128K上下文
)
```

### 场景3：数学公式理解

```python
# 图像分析自动选择GLM（公式识别强）
manager = UnifiedLLMManager()

result = manager.analyze_image_with_fallback(
    image_path="formula.jpg",
    prompt="识别并解释这个数学公式",
    providers=["glm-4.6v", "doubao-vision"]
)
```

### 场景4：中文文档理解

```python
# 中文PPT/文档使用Doubao
result = manager.analyze_image_with_fallback(
    image_path="slide.jpg",
    prompt="提取这张PPT的内容",
    providers=["doubao-vision", "glm-4.6v"]
)
```

### 场景5：多语言支持

```python
# 使用GPT-4o处理多语言内容
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="gpt-4o"  # 多语言能力强
)
```

### 场景6：成本优化

```python
# 设置降级链，优先使用免费/便宜的模型
manager = UnifiedLLMManager()

cost_optimized_chain = [
    "glm-4-flash",      # 智谱：几乎免费
    "deepseek-chat",    # DeepSeek: 1元/M tokens
    "gpt-4o-mini"       # OpenAI: 最贵
]

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Long text..."}],
    providers=cost_optimized_chain
)
```

---

## Provider能力对照表

### 文本生成能力

| 模型 | 速度 | 成本 | 中文能力 | 长上下文 | 推荐场景 |
|------|------|------|----------|----------|----------|
| `glm-4-flash` | ⚡⚡⚡ | 💰 | ⭐⭐⭐⭐⭐ | 128K | 日常文本、快速处理 |
| `deepseek-chat` | ⚡⚡ | 💰 | ⭐⭐⭐⭐ | 128K | 长文本、代码生成 |
| `deepseek-v3` | ⚡ | 💰💰 | ⭐⭐⭐⭐ | 128K | 复杂推理、思维链 |
| `gpt-4o-mini` | ⚡⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐ | 128K | 多语言、快速通用 |
| `gpt-4o` | ⚡⚡ | 💰💰💰💰 | ⭐⭐⭐⭐ | 128K | 复杂任务、高质量 |

### 视觉理解能力

| 模型 | 公式理解 | 代码理解 | 中文OCR | 图表分析 | 推荐场景 |
|------|----------|----------|---------|----------|----------|
| `glm-4.6v` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 数学、代码、技术 |
| `doubao-vision` | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中文文档、PPT |
| `gpt-4o` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 通用、复杂图像 |
| `gpt-4o-mini` | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 快速、低成本 |

---

## 高级配置

### 1. 修改默认Provider

编辑 `config/llm_config.py`:

```python
# 推荐的模型配置
RECOMMENDED_TEXT_MODELS = [
    "deepseek-chat",    # 改为首选DeepSeek
    "glm-4-flash",
    "gpt-4o-mini",
]

FALLBACK_CHAINS = {
    "text": ["deepseek-chat", "glm-4-flash", "gpt-4o-mini"],
    "vision": ["doubao-vision", "glm-4.6v", "gpt-4o"],
}
```

### 2. 注册自定义Provider

```python
from utils.llm.model_registry import ModelRegistry, ModelInfo, ModelCapability

# 定义自定义模型
custom_model = ModelInfo(
    name="My Custom Model",
    provider="custom",
    api_base="https://my-api.com/v1",
    default_max_tokens=4096,
    capabilities=[ModelCapability.TEXT, ModelCapability.FAST],
    env_key="MY_API_KEY",
    timeout=60,
)

# 注册到系统
ModelRegistry.register_custom_model("my-custom-model", custom_model)

# 使用
from utils.llm.unified_manager import UnifiedLLMManager
manager = UnifiedLLMManager()
client = manager.get_client("my-custom-model")
```

### 3. 条件性Provider选择

```python
def select_provider_by_content_type(content_type: dict) -> str:
    """根据内容类型智能选择Provider"""

    if content_type.get("has_formula"):
        return "glm-4.6v"  # 公式用GLM

    if content_type.get("has_code"):
        return "glm-4.6v"  # 代码用GLM

    if content_type.get("has_text"):
        text = content_type.get("text_content", "")
        # 检测中文比例
        chinese_ratio = sum(1 for c in text if '\u4e00' <= c <= '\u9fff') / len(text)
        if chinese_ratio > 0.3:
            return "doubao-vision"  # 中文用Doubao

    # 默认
    return "glm-4.6v"
```

---

## 故障排查

### 问题1：Provider不可用

**症状：**
```
WARNING: API key not found for glm-4-flash
```

**解决方案：**
1. 检查 `.env` 文件中是否配置了 `GLM_API_KEY`
2. 确认环境变量已加载：运行 `python -c "import os; print(os.getenv('GLM_API_KEY'))"`
3. 重启应用以加载新的环境变量

### 问题2：所有Provider都失败

**症状：**
```
ERROR: All providers failed
```

**诊断：**
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()

# 检查可用模型
available = manager.list_available_models()
print("可用模型:", list(available.keys()))

# 健康检查
for model_id in available.keys():
    is_ok = manager.health_check(model_id)
    print(f"{model_id}: {'✓' if is_ok else '✗'}")
```

### 问题3：想使用某Provider但未配置

**解决方案：**
1. 去Provider官网申请API密钥
2. 添加到 `.env` 文件
3. 重启应用

**各Provider申请地址：**
- GLM: https://open.bigmodel.cn/
- Doubao: https://console.volcengine.com/ark
- DeepSeek: https://platform.deepseek.com/
- OpenAI: https://platform.openai.com/
- ModelScope: https://modelscope.cn/

---

## 总结

### 推荐配置（按使用场景）

| 场景 | 推荐Provider | 备选Provider |
|------|--------------|--------------|
| **日常文本** | `glm-4-flash` | `deepseek-chat` |
| **长文本总结** | `deepseek-v3` | `glm-4-flash` |
| **数学公式** | `glm-4.6v` | `gpt-4o` |
| **代码理解** | `glm-4.6v` | `gpt-4o` |
| **中文文档** | `doubao-vision` | `glm-4.6v` |
| **多语言** | `gpt-4o` | `gpt-4o-mini` |
| **成本优先** | `glm-4-flash` | `deepseek-chat` |
| **质量优先** | `gpt-4o` | `glm-4.6v` |

### 快速配置模板

```bash
# .env 文件模板

# 启用统一LLM架构
USE_UNIFIED_LLM=true
DEFAULT_TEXT_MODEL=glm-4-flash
DEFAULT_VISION_MODEL=glm-4.6v

# API密钥（至少配置一个）
GLM_API_KEY=your_glm_key
# DEEPSEEK_API_KEY=your_deepseek_key
# ARK_API_KEY=your_doubao_key
# MODELSCOPE_TOKEN=your_modelscope_token
# OPENAI_API_KEY=your_openai_key
```

配置完成后即可使用，系统会自动处理降级和错误恢复！
