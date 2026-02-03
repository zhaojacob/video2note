# LLM 集成架构图

## 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Video Note System                            │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Video Download │  │ Audio Transcr. │  │ Image Extract  │        │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘        │
│           │                   │                   │                  │
│           └───────────────────┴───────────────────┘                  │
│                               │                                      │
│                               ▼                                      │
│                    ┌──────────────────────┐                         │
│                    │  UnifiedLLMManager   │                         │
│                    │  (智能客户端选择)     │                         │
│                    └──────────┬───────────┘                         │
│                               │                                      │
│              ┌────────────────┴────────────────┐                    │
│              │                                  │                    │
│              ▼                                  ▼                    │
│    ┌─────────────────┐              ┌─────────────────┐            │
│    │  Text Polisher  │              │ Image Analyzer  │            │
│    │  (文本润色)      │              │  (图像分析)      │            │
│    └─────────┬───────┘              └─────────┬───────┘            │
│              │                                  │                    │
│              ▼                                  ▼                    │
│         DeepSeek                           Doubao Vision             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## 客户端选择流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      UnifiedLLMManager.get_client()                  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ 读取 Provider 配置   │
                    │ (llm_config.yaml)   │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ 检查 API Key        │
                    │ (from .env)         │
                    └─────────┬───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ use_responses_api == True?    │
              └───────┬───────────────┬───────┘
                      │               │
                 YES  │               │  NO
                      │               │
                      ▼               ▼
          ┌──────────────────┐  ┌──────────────────┐
          │DoubaoVisionClient│  │    LLMClient     │
          │  (豆包专用)       │  │  (标准 OpenAI)   │
          └──────────────────┘  └──────────────────┘
                      │               │
                      └───────┬───────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  返回客户端实例      │
                    └─────────────────────┘
```

## API 调用流程对比

### DeepSeek 文本处理流程

```
┌─────────────────┐
│  TextPolisher   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ manager.get_client(                     │
│   provider="deepseek",                  │
│   model="deepseek-chat"                 │
│ )                                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LLMClient                               │
│ ├─ model: "deepseek-chat"              │
│ ├─ base_url: "https://api.deepseek.com"│
│ └─ api_key: DEEPSEEK_API_KEY           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ client.chat.completions.create(         │
│   model="deepseek-chat",                │
│   messages=[                            │
│     {"role": "user", "content": "..."}  │
│   ]                                     │
│ )                                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  DeepSeek API   │
│  (标准格式)      │
└─────────────────┘
```

### 豆包视觉分析流程

```
┌─────────────────┐
│ ImageAnalyzer   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ manager.get_client(                          │
│   provider="bytedance",                      │
│   model="doubao-seed-1-6-vision-250815"     │
│ )                                            │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ DoubaoVisionClient                           │
│ ├─ model: "doubao-seed-1-6-vision-250815"   │
│ ├─ base_url: "https://ark.cn-beijing..."    │
│ └─ api_key: ARK_API_KEY                     │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ client.responses.create(                     │
│   model="doubao-seed-1-6-vision-250815",    │
│   input=[{                                   │
│     "role": "user",                          │
│     "content": [                             │
│       {"type": "input_image", ...},          │
│       {"type": "input_text", ...}            │
│     ]                                        │
│   }]                                         │
│ )                                            │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Doubao API    │
│  (特殊格式)      │
└─────────────────┘
```

## 配置文件层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                      .env (环境变量)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ DEEPSEEK_API_KEY=sk-xxxxx                            │  │
│  │ ARK_API_KEY=xxxxx                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              config/llm_config.yaml (结构化配置)             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ providers:                                           │  │
│  │   deepseek:                                          │  │
│  │     api_key_env: "DEEPSEEK_API_KEY"                 │  │
│  │     base_url: "https://api.deepseek.com"            │  │
│  │     models: ["deepseek-chat"]                       │  │
│  │     use_responses_api: false                        │  │
│  │                                                      │  │
│  │   bytedance:                                         │  │
│  │     api_key_env: "ARK_API_KEY"                      │  │
│  │     base_url: "https://ark.cn-beijing..."           │  │
│  │     models: ["doubao-seed-1-6-vision-250815"]      │  │
│  │     use_responses_api: true  ◄── 关键字段            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         config/yaml_config_loader.py (配置加载器)            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ @dataclass                                           │  │
│  │ class ProviderConfig:                                │  │
│  │     id: str                                          │  │
│  │     api_key_env: str                                 │  │
│  │     base_url: str                                    │  │
│  │     models: List[str]                                │  │
│  │     use_responses_api: bool = False  ◄── 新增字段    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│       utils/llm/provider_registry.py (Provider 注册表)       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ @dataclass                                           │  │
│  │ class ProviderInfo:                                  │  │
│  │     id: str                                          │  │
│  │     base_url: str                                    │  │
│  │     models: List[str]                                │  │
│  │     use_responses_api: bool = False  ◄── 新增字段    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│        utils/llm/unified_manager.py (统一管理器)             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ def get_client(provider, model):                     │  │
│  │     provider_info = get_provider(provider)           │  │
│  │                                                      │  │
│  │     if provider_info.use_responses_api:  ◄── 检查    │  │
│  │         return DoubaoVisionClient(...)               │  │
│  │     else:                                            │  │
│  │         return LLMClient(...)                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 客户端类继承关系

```
┌─────────────────────────────────────────────────────────────┐
│                      BaseLLMClient                          │
│                      (抽象基类)                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ + model: str                                         │  │
│  │ + api_key: str                                       │  │
│  │ + base_url: str                                      │  │
│  │ + timeout: float                                     │  │
│  │                                                      │  │
│  │ + is_available() -> bool                            │  │
│  │ + chat_completion() -> str                          │  │
│  │ + analyze_image() -> Dict                           │  │
│  │ + _encode_image() -> str                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌──────────────────────┐      ┌──────────────────────┐
│     LLMClient        │      │ DoubaoVisionClient   │
│  (标准 OpenAI 格式)   │      │   (豆包专用格式)      │
├──────────────────────┤      ├──────────────────────┤
│ + chat_completion()  │      │ + analyze_image()    │
│   使用:               │      │   使用:               │
│   chat.completions   │      │   responses.create() │
│   .create()          │      │                      │
│                      │      │ + _analyze_image_    │
│ + analyze_image()    │      │   standard()         │
│   使用:               │      │   (降级方案)          │
│   chat.completions   │      │                      │
│   .create()          │      │ + chat_completion()  │
│   (vision format)    │      │   (不支持)            │
└──────────────────────┘      └──────────────────────┘
```

## 数据流图

```
┌─────────────┐
│ 用户请求     │
│ (视频 URL)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    main.py                              │
│  1. 下载视频                                             │
│  2. 提取音频 → 转录                                      │
│  3. 提取关键帧                                           │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│  TextPolisher    │              │ ImageAnalyzer    │
│  (文本润色)       │              │  (图像分析)       │
└──────┬───────────┘              └──────┬───────────┘
       │                                 │
       ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│ UnifiedLLMManager│              │ UnifiedLLMManager│
│ .get_client(     │              │ .get_client(     │
│   "deepseek",    │              │   "bytedance",   │
│   "deepseek-chat"│              │   "doubao-..."   │
│ )                │              │ )                │
└──────┬───────────┘              └──────┬───────────┘
       │                                 │
       ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│   LLMClient      │              │DoubaoVisionClient│
└──────┬───────────┘              └──────┬───────────┘
       │                                 │
       ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│  DeepSeek API    │              │   Doubao API     │
│  (文本处理)       │              │  (视觉分析)       │
└──────┬───────────┘              └──────┬───────────┘
       │                                 │
       └─────────────┬───────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  合并结果     │
              │  生成笔记     │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ output/notes │
              │  (Markdown)  │
              └──────────────┘
```

## 关键决策点

### 1. 为什么需要 DoubaoVisionClient？

```
豆包 API 格式                    标准 OpenAI 格式
─────────────────────────────────────────────────────
client.responses.create()   vs   client.chat.completions.create()
input=[...]                 vs   messages=[...]
input_image                 vs   image_url
input_text                  vs   text
```

### 2. 如何选择客户端？

```python
# 在 UnifiedLLMManager.get_client() 中:

if provider_info.use_responses_api:
    # 豆包使用特殊 API
    return DoubaoVisionClient(...)
else:
    # 其他 provider 使用标准 API
    return LLMClient(...)
```

### 3. 配置如何传递？

```
.env 文件
  ↓ (环境变量)
llm_config.yaml
  ↓ (YAML 解析)
ProviderConfig (dataclass)
  ↓ (转换)
ProviderInfo (dataclass)
  ↓ (使用)
UnifiedLLMManager
  ↓ (创建)
LLMClient / DoubaoVisionClient
```

## 扩展性设计

### 添加新 Provider

1. **更新 llm_config.yaml**
```yaml
providers:
  new_provider:
    name: "New Provider"
    api_key_env: "NEW_PROVIDER_KEY"
    base_url: "https://api.newprovider.com"
    models: ["model-1", "model-2"]
    capabilities: ["text", "vision"]
    use_responses_api: false  # 或 true，如果需要特殊 API
```

2. **如果需要特殊 API 格式**
```python
# 创建新的客户端类
class NewProviderClient(BaseLLMClient):
    def chat_completion(self, messages, **kwargs):
        # 实现特殊 API 调用
        pass
```

3. **更新 UnifiedLLMManager**
```python
if provider_info.use_special_api_format:
    return NewProviderClient(...)
elif provider_info.use_responses_api:
    return DoubaoVisionClient(...)
else:
    return LLMClient(...)
```

---

**创建时间**: 2026-01-28
**版本**: 1.0
