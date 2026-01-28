# Provider 配置检查报告

本文档记录了代码库中所有 LLM Provider 的准确配置信息。

**生成时间**: 2026-01-28
**状态**: ✅ 已修复关键问题

---

## 📋 Provider 配置总览

### 1. Zhipu (智谱AI)

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Provider ID** | `zhipu` | 内部标识符 |
| **显示名称** | 智谱AI (GLM) | 用户友好的名称 |
| **Base URL** | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | 完整API路径（包含 `/chat/completions`） |
| **API Key 环境变量** | `GLM_API_KEY` | 环境变量名称 |
| **支持模型** | `glm-4-flash`, `glm-4.6v`, `glm-4` | 模型列表 |
| **能力** | TEXT, VISION, THINKING, BILINGUAL, FAST | ProviderCapabilities |
| **超时时间** | 60 秒 | 请求超时 |
| **最大 Tokens** | 8192 | 默认最大生成长度 |

**代码位置**:
- `utils/llm/provider_registry.py:80-95`
- `config/settings.py:54-61` (GLM_CONFIG)

**注意事项**:
- ✅ Base URL 是**完整路径**，包含 `/chat/completions`
- ✅ 与 settings.py 中的配置一致

---

### 2. OpenAI

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Provider ID** | `openai` | 内部标识符 |
| **显示名称** | OpenAI | 用户友好的名称 |
| **Base URL** | `https://api.openai.com/v1` | Base URL（SDK自动添加 `/chat/completions`） |
| **API Key 环境变量** | `OPENAI_API_KEY` | 环境变量名称 |
| **支持模型** | `gpt-4o`, `gpt-4o-mini`, `gpt-4` | 模型列表 |
| **能力** | TEXT, VISION, FAST | ProviderCapabilities |
| **超时时间** | 60 秒 | 请求超时 |
| **最大 Tokens** | 4096 | 默认最大生成长度 |

**代码位置**:
- `utils/llm/provider_registry.py:97-110`

**注意事项**:
- ✅ Base URL 是**基础路径**，OpenAI SDK 会自动添加 `/chat/completions`
- ✅ 最终请求: `https://api.openai.com/v1/chat/completions`

---

### 3. DeepSeek

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Provider ID** | `deepseek` | 内部标识符 |
| **显示名称** | DeepSeek | 用户友好的名称 |
| **Base URL** | `https://api.deepseek.com` | Base URL（SDK自动添加 `/chat/completions`） |
| **API Key 环境变量** | `DEEPSEEK_API_KEY` | 环境变量名称 |
| **支持模型** | `deepseek-chat` | 模型列表 |
| **能力** | TEXT, LONG_CONTEXT, FAST | ProviderCapabilities |
| **超时时间** | 60 秒 | 请求超时 |
| **最大 Tokens** | 8192 | 默认最大生成长度 |

**代码位置**:
- `utils/llm/provider_registry.py:112-125`
- `config/settings.py:92-107` (DEEPSEEK_CONFIG)

**注意事项**:
- ✅ Base URL 是**基础路径**，OpenAI SDK 会自动添加 `/chat/completions`
- ✅ 最终请求: `https://api.deepseek.com/chat/completions`
- ✅ 与 settings.py 中的配置一致

---

### 4. ModelScope

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Provider ID** | `modelscope` | 内部标识符 |
| **显示名称** | ModelScope | 用户友好的名称 |
| **Base URL** | `https://api-inference.modelscope.cn/v1` | Base URL（SDK自动添加 `/chat/completions`） |
| **API Key 环境变量** | `MODELSCOPE_TOKEN` | 环境变量名称 |
| **支持模型** | `deepseek-ai/DeepSeek-V3.2` | 模型列表 |
| **能力** | TEXT, THINKING, LONG_CONTEXT | ProviderCapabilities |
| **超时时间** | 600 秒 | 请求超时 |
| **最大 Tokens** | 8192 | 默认最大生成长度 |
| **Extra Body** | `{"enable_thinking": true}` | 额外请求体参数 |

**代码位置**:
- `utils/llm/provider_registry.py:127-142`
- `config/settings.py:72-90` (MODELSCOPE_CONFIG)

**注意事项**:
- ✅ Base URL 是**基础路径**，OpenAI SDK 会自动添加 `/chat/completions`
- ✅ 最终请求: `https://api-inference.modelscope.cn/v1/chat/completions`
- ✅ 需要启用 thinking chain（思维链）
- ✅ 与 settings.py 中的配置一致

---

### 5. Bytedance (Doubao/字节跳动)

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Provider ID** | `bytedance` | 内部标识符 |
| **显示名称** | 字节跳动 (Doubao) | 用户友好的名称 |
| **Base URL** | `https://ark.cn-beijing.volces.com/api/v3` | Base URL（SDK自动添加 `/chat/completions`） |
| **API Key 环境变量** | `ARK_API_KEY` | 环境变量名称 |
| **支持模型** | `doubao-vision` | ✅ **已修复**：统一为 `doubao-vision` |
| **能力** | VISION, BILINGUAL | ProviderCapabilities |
| **超时时间** | 300 秒 | 请求超时 |
| **最大 Tokens** | 1000 | 默认最大生成长度 |

**代码位置**:
- `utils/llm/provider_registry.py:144-156`
- `config/settings.py:63-70` (DOUBAO_CONFIG)

**修复记录**:
- ❌ **之前**: `config/settings.py` 使用 `doubao-seed-1-6-vision-250815`
- ✅ **现在**: 统一为 `doubao-vision`

**注意事项**:
- ✅ Base URL 是**基础路径**，OpenAI SDK 会自动添加 `/chat/completions`
- ✅ 最终请求: `https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- ✅ 与 settings.py 中的配置现已一致

---

## 🔍 关键发现与修复

### ✅ 已修复问题

| 问题 | 描述 | 状态 |
|------|------|------|
| **Doubao 模型名称不一致** | `settings.py` 使用 `doubao-seed-1-6-vision-250815`，`provider_registry.py` 使用 `doubao-vision` | ✅ 已统一为 `doubao-vision` |

### ℹ️ 设计说明

1. **Base URL 格式**：
   - Zhipu 使用完整路径（包含 `/chat/completions`）
   - 其他 provider 使用基础路径（OpenAI SDK 自动添加 `/chat/completions`）
   - 这是正确的设计，因为 Zhipu 的 API 路径特殊

2. **OpenAI SDK 行为**：
   ```python
   from openai import OpenAI

   client = OpenAI(
       base_url="https://api.openai.com/v1",  # 基础路径
       api_key="..."
   )

   # SDK 自动调用: https://api.openai.com/v1/chat/completions
   response = client.chat.completions.create(...)
   ```

3. **Model 命名规范**：
   - 所有 provider 使用统一的模型名称
   - Model ID 在 `provider_registry.py` 的 `models` 列表中定义

---

## 📊 配置一致性检查

### 检查结果

| Provider | provider_registry.py | settings.py | 状态 |
|----------|---------------------|-------------|------|
| zhipu | ✅ | ✅ GLM_CONFIG | ✅ 一致 |
| openai | ✅ | - (未在 settings.py) | N/A |
| deepseek | ✅ | ✅ DEEPSEEK_CONFIG | ✅ 一致 |
| modelscope | ✅ | ✅ MODELSCOPE_CONFIG | ✅ 一致 |
| bytedance | ✅ | ✅ DOUBAO_CONFIG | ✅ **已修复** |

---

## 🚀 使用建议

### 1. 环境变量配置

确保 `.env` 文件包含以下配置：

```bash
# Provider 默认配置
DEFAULT_TEXT_PROVIDER=zhipu
DEFAULT_VISION_PROVIDER=zhipu
DEFAULT_THINKING_PROVIDER=modelscope

# API 密钥
GLM_API_KEY=your_glm_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
MODELSCOPE_TOKEN=your_modelscope_token
ARK_API_KEY=your_ark_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 2. 代码中使用

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# 使用 Provider-First API
client = manager.get_client(provider="zhipu", model="glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```

### 3. 查询可用 Provider

```python
from utils.llm import ProviderRegistry

registry = ProviderRegistry()

# 列出所有 provider
providers = registry.get_all_providers()
for provider_id, provider_info in providers.items():
    print(f"{provider_id}: {provider_info.name}")
    print(f"  Models: {provider_info.models}")
    print(f"  Base URL: {provider_info.base_url}")
```

---

## 📝 变更历史

| 日期 | 变更内容 | 影响范围 |
|------|----------|----------|
| 2026-01-28 | 统一 Doubao 模型名称为 `doubao-vision` | `config/settings.py:DOUBAO_CONFIG` |

---

## ✅ 验证清单

- [x] Provider Registry 配置正确
- [x] Settings.py 配置与 Provider Registry 一致
- [x] 所有 Base URL 格式正确
- [x] 所有模型名称统一
- [x] API Key 环境变量名称正确
- [x] Provider 能力定义准确

---

**报告生成**: Provider-First LLM Architecture Refactor
**审核人**: Claude (Sonnet 4.5)
**最后更新**: 2026-01-28
