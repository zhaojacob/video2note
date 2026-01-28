# Provider-First LLM架构指南

本文档详细说明如何在Provider-First架构中指定和切换不同的LLM提供商（Provider）。

> **核心变化**：新架构中，Provider是一等实体。先选Provider，再选Model。多个Provider可以提供同名模型。

---

## 目录

1. [架构概述](#架构概述)
2. [快速开始](#快速开始)
3. [Provider-First API](#provider-first-api)
4. [配置Provider](#配置provider)
5. [降级策略](#降级策略)
6. [常见场景](#常见场景)
7. [高级用法](#高级用法)
8. [迁移指南](#迁移指南)

---

## 架构概述

### 核心概念

```
Provider (提供商)
    ↓
ProviderInfo (提供商信息)
    ├─ base_url (API地址)
    ├─ api_key_env (密钥环境变量)
    ├─ models: [...]  (支持的模型列表)
    └─ capabilities: [...]  (能力列表)
    ↓
选择 Provider → 选择 Model → 创建客户端
```

### 为什么要Provider-First？

**旧架构的问题**：
- ❌ Model ID → Provider 硬编码映射（1:1）
- ❌ 无法处理同名模型（多个provider提供`gpt-4`）
- ❌ Provider只是字符串，不是实体

**新架构的优势**：
- ✅ Provider是独立实体，有自己的配置
- ✅ 多个Provider可以提供同名模型
- ✅ Provider级降级策略
- ✅ 支持自定义Provider（代码 + 配置）
- ✅ 完全向后兼容

### 内置Provider

| Provider ID | 名称 | 模型示例 | 能力 | 环境变量 |
|-------------|------|----------|------|----------|
| `zhipu` | 智谱AI | `glm-4-flash`, `glm-4.6v` | Text, Vision, Thinking | `GLM_API_KEY` |
| `deepseek` | DeepSeek | `deepseek-chat` | Text, Long Context | `DEEPSEEK_API_KEY` |
| `modelscope` | ModelScope | `deepseek-ai/DeepSeek-V3.2` | Text, Thinking | `MODELSCOPE_TOKEN` |
| `openai` | OpenAI | `gpt-4o`, `gpt-4o-mini` | Text, Vision | `OPENAI_API_KEY` |
| `bytedance` | 字节跳动 | `doubao-vision` | Vision, Bilingual | `ARK_API_KEY` |

---

## 快速开始

### 1. 配置环境变量

```bash
# .env 文件

# 启用统一LLM架构
USE_UNIFIED_LLM=true

# 按任务类型指定默认Provider
DEFAULT_TEXT_PROVIDER=zhipu
DEFAULT_VISION_PROVIDER=zhipu
DEFAULT_THINKING_PROVIDER=modelscope

# 指定默认模型（可选）
DEFAULT_TEXT_MODEL=glm-4-flash
DEFAULT_VISION_MODEL=glm-4.6v

# 配置API密钥
GLM_API_KEY=your_glm_api_key
DEEPSEEK_API_KEY=your_deepseek_key
MODELSCOPE_TOKEN=your_modelscope_token
```

### 2. 使用Provider-First API

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 新API：Provider-First
client = manager.get_client(provider="zhipu", model="glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```

### 3. 使用Provider级降级

```python
# Provider级降级（跨provider）
result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "写一篇文章"}],
    providers=["zhipu", "deepseek", "openai"]  # 按优先级尝试provider
)
```

---

## Provider-First API

### 基础用法

#### 获取客户端（推荐方式）

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 新API：Provider-First（推荐）
client = manager.get_client(
    provider="zhipu",      # 指定provider
    model="glm-4-flash"    # 指定模型
)

# Legacy API（仍支持）
client = manager.get_client("glm-4-flash")
```

#### 查询Provider信息

```python
from utils.llm import ProviderRegistry, ProviderCapability

registry = ProviderRegistry()

# 获取特定provider
zhipu = registry.get_provider("zhipu")
print(f"{zhipu.name}: {zhipu.models}")

# 列出所有支持视觉的provider
vision_providers = registry.list_providers(capability=ProviderCapability.VISION)
for pid, info in vision_providers.items():
    print(f"{info.name}: {info.models}")

# 查找提供某模型的所有provider
providers_for_gpt4 = registry.get_providers_for_model("gpt-4")
for p in providers_for_gpt4:
    print(f"{p.name}: {p.base_url}")
```

### TextPolisher（新增provider参数）

```python
from utils.text_polisher import TextPolisher

# Provider-First方式
polisher = TextPolisher(
    use_unified_manager=True,
    provider="zhipu",          # 指定provider
    model_id="glm-4-flash"     # 指定模型
)

# Legacy方式（仍支持）
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="glm-4-flash"
)
```

### ImageAnalyzer（Provider级选择）

```python
from analysis.image_analyzer import ImageAnalyzer

# 启用统一管理器（自动使用provider级降级）
analyzer = ImageAnalyzer(use_unified_manager=True)

# 分析图像（自动选择provider）
# 公式/代码 → ["zhipu", "bytedance"]
# 中文文档 → ["bytedance", "zhipu"]
result = analyzer.analyze_single(frame)
```

---

## 配置Provider

### 方式1：通过.env配置（最多10个）

```bash
# .env 文件

# 自定义Provider 1: OpenAI兼容代理
CUSTOM_PROVIDER_1_NAME=MyProxy
CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o

# 自定义Provider 2: 本地LLM (Ollama)
CUSTOM_PROVIDER_2_NAME=LocalOllama
CUSTOM_PROVIDER_2_BASE_URL=http://localhost:11434/v1
CUSTOM_PROVIDER_2_API_KEY=ollama
CUSTOM_PROVIDER_2_MODELS=llama3,mistral
```

### 方式2：通过代码注册

```python
from utils.llm import ProviderRegistry, ProviderInfo, ProviderCapability

# 创建自定义provider
custom_provider = ProviderInfo(
    id="local-ollama",
    name="Local Ollama",
    base_url="http://localhost:11434/v1",
    api_key_env="OLLAMA_API_KEY",
    models=["llama3", "mistral", "codellama"],
    capabilities=[ProviderCapability.TEXT, ProviderCapability.FAST],
    timeout=120,
    default_max_tokens=4096
)

# 注册到系统
registry = ProviderRegistry()
registry.register_custom_provider(custom_provider)

# 使用
from utils.llm import UnifiedLLMManager
manager = UnifiedLLMManager()
client = manager.get_client(provider="local-ollama", model="llama3")
```

---

## 降级策略

### Provider级降级（推荐）

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 按provider优先级降级
result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "写一篇文章"}],
    providers=["zhipu", "deepseek", "openai"],  # Provider级降级
    model="glm-4-flash"  # 可选：仅用于支持该模型的provider
)
```

### 预定义降级链

```python
from config.llm_config import PROVIDER_FALLBACK_CHAINS

# Provider级降级链
PROVIDER_FALLBACK_CHAINS = {
    "text": ["zhipu", "deepseek", "openai"],
    "vision": ["zhipu", "bytedance", "openai"],
    "thinking": ["modelscope", "zhipu", "deepseek"],
}

# 使用预定义降级链
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()
result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Hello"}],
    providers=PROVIDER_FALLBACK_CHAINS["text"]
)
```

### 任务特定配置

```python
from config.llm_config import TASK_RECOMMENDATIONS

# 获取任务推荐（包含provider和fallback）
polish_config = TASK_RECOMMENDATIONS["polish"]
# {
#     "providers": ["zhipu", "deepseek"],
#     "models": ["glm-4-flash", "deepseek-chat"],
#     "fallback_providers": ["zhipu", "deepseek", "openai"],
#     "reason": "Fast and cost-effective for text polishing"
# }
```

---

## 常见场景

### 场景1：同名模型，不同Provider

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 使用OpenAI的GPT-4
client1 = manager.get_client(provider="openai", model="gpt-4")
result1 = client1.chat_completion([{"role": "user", "content": "Hello"}])

# 使用自定义代理的GPT-4
client2 = manager.get_client(provider="custom-my-proxy", model="gpt-4")
result2 = client2.chat_completion([{"role": "user", "content": "Hello"}])
```

### 场景2：快速便宜（推荐）

```python
# 环境变量配置
DEFAULT_TEXT_PROVIDER=zhipu
DEFAULT_TEXT_MODEL=glm-4-flash

# 或代码指定
from utils.text_polisher import TextPolisher

polisher = TextPolisher(
    use_unified_manager=True,
    provider="zhipu",
    model_id="glm-4-flash"
)
```

### 场景3：长文本处理

```python
# 使用ModelScope的DeepSeek V3（思维链）
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "长文本..."}],
    providers=["modelscope", "deepseek", "zhipu"],  # 优先用思维链
)
```

### 场景4：数学公式理解

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 公式识别：GLM优先
result = manager.analyze_image_with_fallback(
    image_path="formula.jpg",
    prompt="识别并解释这个数学公式",
    providers=["zhipu", "bytedance", "openai"]
)
```

### 场景5：中文文档理解

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 中文文档：Doubao优先
result = manager.analyze_image_with_fallback(
    image_path="slide.jpg",
    prompt="提取这张PPT的内容",
    providers=["bytedance", "zhipu"]
)
```

### 场景6：成本优化

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 按成本排序的provider级降级
cost_optimized_chain = [
    "zhipu",      # 智谱：几乎免费
    "deepseek",   # DeepSeek: 1元/M tokens
    "openai"      # OpenAI: 最贵
]

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Long text..."}],
    providers=cost_optimized_chain
)
```

---

## 高级用法

### 查询Provider能力

```python
from utils.llm import ProviderRegistry, ProviderCapability

registry = ProviderRegistry()

# 列出所有支持思维链的provider
thinking_providers = registry.list_providers(capability=ProviderCapability.THINKING)
for pid, info in thinking_providers.items():
    print(f"{info.name}: {info.models}")

# 检查provider是否支持某能力
zhipu = registry.get_provider("zhipu")
if zhipu.supports_capability(ProviderCapability.VISION):
    print("Zhipu supports vision!")

# 检查provider是否提供某模型
if zhipu.has_model("glm-4.6v"):
    print("Zhipu provides glm-4.6v!")
```

### 列出可用Provider

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 列出所有已配置API密钥的provider
available_providers = manager.list_available_providers()
print("Available providers:", list(available_providers.keys()))

# 按能力筛选
from utils.llm import ModelCapability

vision_providers = manager.list_available_providers(capability=ModelCapability.VISION)
print("Vision providers:", list(vision_providers.keys()))
```

### 动态Provider选择

```python
from utils.llm import ProviderRegistry

def select_provider_by_content(content_type: dict) -> str:
    """根据内容类型智能选择Provider"""
    registry = ProviderRegistry()

    if content_type.get("has_formula") or content_type.get("has_code"):
        return "zhipu"  # GLM擅长公式和代码

    if content_type.get("has_text"):
        text = content_type.get("text_content", "")
        chinese_ratio = sum(1 for c in text if '\u4e00' <= c <= '\u9fff') / len(text)
        if chinese_ratio > 0.3:
            return "bytedance"  # Doubao擅长中文

    return "zhipu"  # 默认
```

---

## 迁移指南

### 从旧API迁移到Provider-First API

#### 变更1：获取客户端

**旧代码**：
```python
client = manager.get_client("glm-4-flash")
```

**新代码（推荐）**：
```python
client = manager.get_client(provider="zhipu", model="glm-4-flash")
```

**兼容性**：旧代码仍可继续使用！

#### 变更2：降级策略

**旧代码**（模型级）：
```python
result = manager.chat_with_fallback(
    messages=[...],
    providers=["glm-4-flash", "deepseek-chat", "gpt-4o-mini"]
)
```

**新代码**（Provider级）：
```python
result = manager.chat_with_fallback(
    messages=[...],
    providers=["zhipu", "deepseek", "openai"],  # Provider ID
    model="glm-4-flash"  # 可选模型名称
)
```

#### 变更3：TextPolisher

**旧代码**：
```python
polisher = TextPolisher(
    use_unified_manager=True,
    model_id="glm-4-flash"
)
```

**新代码（推荐）**：
```python
polisher = TextPolisher(
    use_unified_manager=True,
    provider="zhipu",
    model_id="glm-4-flash"
)
```

### 迁移检查清单

- [ ] 更新环境变量：添加 `DEFAULT_TEXT_PROVIDER`、`DEFAULT_VISION_PROVIDER`
- [ ] 更新降级策略配置：使用Provider ID而非Model ID
- [ ] 可选：更新代码使用Provider-First API
- [ ] 测试：验证所有功能正常工作

---

## 总结

### Provider-First架构优势

| 特性 | 旧架构 | 新架构 |
|------|--------|--------|
| Provider实体 | 字符串 | 一等实体（ProviderInfo） |
| 同名模型 | ❌ 不支持 | ✅ 支持 |
| 降级策略 | 模型级 | Provider级 |
| 自定义Provider | 仅代码 | 代码 + .env配置 |
| 配置灵活性 | 受限 | 高度灵活 |

### 推荐配置

```bash
# .env 文件

USE_UNIFIED_LLM=true

# Provider默认
DEFAULT_TEXT_PROVIDER=zhipu
DEFAULT_VISION_PROVIDER=zhipu
DEFAULT_THINKING_PROVIDER=modelscope

# 模型默认（可选）
DEFAULT_TEXT_MODEL=glm-4-flash
DEFAULT_VISION_MODEL=glm-4.6v

# API密钥
GLM_API_KEY=your_glm_key
DEEPSEEK_API_KEY=your_deepseek_key
MODELSCOPE_TOKEN=your_modelscope_token
```

配置完成后，系统自动处理Provider选择、降级和错误恢复！

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
