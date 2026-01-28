# LLM Configuration System Guide

This guide explains how to configure the LLM system, including providers, models, API keys, and default settings.

---

## 📋 Table of Contents

1. [Configuration System Overview](#configuration-system-overview)
2. [Configuration Files Explained](#configuration-files-explained)
3. [Configuration Steps](#configuration-steps)
4. [Configuration Reference](#configuration-reference)
5. [Common Questions](#common-questions)
6. [Configuration Verification](#configuration-verification)

---

## Configuration System Overview

### Configuration Hierarchy (Low to High Priority)

```
1. Hard-coded Configuration (Lowest Priority)
   └─ utils/llm/provider_registry.py (BUILTIN_PROVIDERS)

2. Environment Variables (Medium Priority)
   └─ .env file

3. Runtime Configuration (Highest Priority)
   └─ Dynamic modifications in code
```

### Configuration Flow

```
.env File (User Configuration)
    ↓
config/settings.py (_load_env_file)
    ↓
os.getenv()
    ↓
ProviderRegistry / UnifiedLLMManager
    ↓
Create LLMClient
```

---

## Configuration Files Explained

### 1. `.env` - User Configuration File

**Location**: Project root directory

**Purpose**: Store all sensitive configurations (API keys, default provider, etc.)

**Key Configuration Items**:

```bash
# ============================================================================
# API Keys (Required)
# ============================================================================
GLM_API_KEY=your_glm_api_key_here          # Zhipu AI
DEEPSEEK_API_KEY=your_deepseek_key_here   # DeepSeek
MODELSCOPE_TOKEN=your_modelscope_token   # ModelScope
ARK_API_KEY=your_ark_key_here            # ByteDance
OPENAI_API_KEY=your_openai_key_here      # OpenAI

# ============================================================================
# Provider Default Configuration (New)
# ============================================================================
DEFAULT_TEXT_PROVIDER=zhipu               # Default provider for text tasks
DEFAULT_VISION_PROVIDER=zhipu             # Default provider for vision tasks
DEFAULT_THINKING_PROVIDER=modelscope    # Default provider for thinking tasks

# ============================================================================
# Model Default Configuration (Optional)
# ============================================================================
DEFAULT_TEXT_MODEL=glm-4-flash          # Default model for text tasks
DEFAULT_VISION_MODEL=glm-4.6v            # Default model for vision tasks

# ============================================================================
# Custom Providers (Optional, up to 10)
# ============================================================================
CUSTOM_PROVIDER_1_NAME=MyProxy
CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o
```

### 2. `utils/llm/provider_registry.py` - Provider Registry

**Purpose**: Define all built-in provider configurations

**Key Content**:

```python
BUILTIN_PROVIDERS = {
    "zhipu": ProviderInfo(
        id="zhipu",
        name="智谱AI (GLM)",
        base_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        api_key_env="GLM_API_KEY",           # ← Corresponds to GLM_API_KEY in .env
        models=["glm-4-flash", "glm-4.6v", "glm-4"],
        capabilities=[...],
        timeout=60,
    ),

    "deepseek": ProviderInfo(
        id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",     # ← Corresponds to DEEPSEEK_API_KEY in .env
        models=["deepseek-chat"],
        capabilities=[...],
    ),
    # ... other providers
}
```

**How to Add a New Provider**:

1. Add a new `ProviderInfo` in `BUILTIN_PROVIDERS`
2. Add the corresponding API key in `.env`

### 3. `config/settings.py` - Global Configuration

**Purpose**: Store global configuration and Provider/Model defaults

**Key Content**:

```python
# Provider defaults (read from environment variables with fallbacks)
PROVIDER_DEFAULTS = {
    "text": os.getenv("DEFAULT_TEXT_PROVIDER", "zhipu"),
    "vision": os.getenv("DEFAULT_VISION_PROVIDER", "zhipu"),
    "thinking": os.getenv("DEFAULT_THINKING_PROVIDER", "modelscope"),
}

# Model defaults (read from environment variables with fallbacks)
MODEL_DEFAULTS = {
    "text": os.getenv("DEFAULT_TEXT_MODEL", "glm-4-flash"),
    "vision": os.getenv("DEFAULT_VISION_MODEL", "glm-4.6v"),
}

# Legacy configuration (backward compatible)
GLM_CONFIG = {
    "api_key": os.getenv("GLM_API_KEY", ""),
    "model": "glm-4.6v",
    "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    ...
}
```

**Environment Variable Loading Mechanism**:

```python
def _load_env_file():
    """Automatically loads .env file at startup"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

_load_env_file()  # ← Executes immediately when module is imported
```

### 4. `config/llm_config.py` - Fallback Strategy Configuration

**Purpose**: Define provider-level fallback chains and task recommendations

**Key Content**:

```python
# Provider-level fallback chains
PROVIDER_FALLBACK_CHAINS = {
    "text": ["zhipu", "deepseek", "openai"],      # Try in priority order
    "vision": ["zhipu", "bytedance", "openai"],
    "thinking": ["modelscope", "zhipu", "deepseek"],
}

# Task recommendations (provider-aware)
TASK_RECOMMENDATIONS = {
    "polish": {
        "providers": ["zhipu", "deepseek"],
        "models": ["glm-4-flash", "deepseek-chat"],
        "fallback_providers": ["zhipu", "deepseek", "openai"],
        "reason": "Fast and cost-effective"
    },
    ...
}
```

### 5. `utils/llm/unified_manager.py` - Unified Manager

**Purpose**: Use configuration to create and manage LLM clients

**Core Logic**:

```python
class UnifiedLLMManager:
    def __init__(self):
        self._provider_registry = ProviderRegistry()  # Load all providers
        self._model_registry = ModelRegistry()

    def get_client(self, provider=None, model=None, ...):
        # 1. Get ProviderInfo
        provider_info = self._provider_registry.get_provider(provider)

        # 2. Get API key (from environment variables)
        api_key = provider_info.get_api_key()  # os.getenv(api_key_env)

        # 3. Create LLMClient
        client = LLMClient(
            model=model,
            api_key=api_key,
            base_url=provider_info.base_url,
            ...
        )
```

---

## Configuration Steps

### Step 1: Set API Keys (Required)

Configure in `.env` file:

```bash
# Zhipu AI
GLM_API_KEY=your_actual_api_key

# DeepSeek
DEEPSEEK_API_KEY=your_actual_api_key

# ModelScope
MODELSCOPE_TOKEN=your_actual_token

# ByteDance
ARK_API_KEY=your_actual_api_key

# OpenAI (optional)
OPENAI_API_KEY=your_actual_api_key
```

### Step 2: Set Default Provider (Optional)

Configure in `.env` file:

```bash
DEFAULT_TEXT_PROVIDER=zhipu           # Use zhipu for text tasks
DEFAULT_VISION_PROVIDER=zhipu         # Use zhipu for vision tasks
DEFAULT_THINKING_PROVIDER=modelscope  # Use modelscope for thinking tasks
```

### Step 3: Set Default Model (Optional)

Configure in `.env` file:

```bash
DEFAULT_TEXT_MODEL=glm-4-flash     # Default model for text tasks
DEFAULT_VISION_MODEL=glm-4.6v       # Default model for vision tasks
```

### Step 4: Add Custom Provider (Optional)

Two methods available:

**Method 1: Configure via .env (up to 10)**

```bash
CUSTOM_PROVIDER_1_NAME=MyProxy
CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o
```

**Method 2: Register via Code**

```python
from utils.llm.provider_registry import ProviderRegistry, ProviderInfo, ProviderCapability

# Create custom provider
custom = ProviderInfo(
    id="local-ollama",
    name="Local Ollama",
    base_url="http://localhost:11434/v1",
    api_key_env="OLLAMA_API_KEY",
    models=["llama3", "mistral"],
    capabilities=[ProviderCapability.TEXT, ProviderCapability.FAST],
)

# Register to system
registry = ProviderRegistry()
registry.register_custom_provider(custom)
```

---

## Configuration Reference

### Provider ID → API Key Environment Variable

| Provider ID | API Key Environment Variable | .env Configuration |
|------------|-----------------------------|-------------------|
| `zhipu` | `GLM_API_KEY` | `GLM_API_KEY=...` |
| `deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_API_KEY=...` |
| `modelscope` | `MODELSCOPE_TOKEN` | `MODELSCOPE_TOKEN=...` |
| `bytedance` | `ARK_API_KEY` | `ARK_API_KEY=...` |
| `openai` | `OPENAI_API_KEY` | `OPENAI_API_KEY=...` |

### Provider ID → Base URL

| Provider ID | Base URL |
|------------|----------|
| `zhipu` | `https://open.bigmodel.cn/api/paas/v4/chat/completions` |
| `deepseek` | `https://api.deepseek.com` |
| `modelscope` | `https://api-inference.modelscope.cn/v1` |
| `bytedance` | `https://ark.cn-beijing.volces.com/api/v3` |
| `openai` | `https://api.openai.com/v1` |

### Provider ID → Models

| Provider ID | Supported Models |
|------------|------------------|
| `zhipu` | `glm-4-flash`, `glm-4.6v`, `glm-4` |
| `deepseek` | `deepseek-chat` |
| `modelscope` | `deepseek-v3` (alias) → `deepseek-ai/DeepSeek-V3.2` (real) |
| `bytedance` | `doubao-vision` |
| `openai` | `gpt-4o`, `gpt-4o-mini`, `gpt-4` |

### Environment Variable List

| Environment Variable | Purpose | Default Value | Required |
|---------------------|---------|---------------|----------|
| `GLM_API_KEY` | Zhipu AI API key | - | Yes (for vision) |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - | No |
| `MODELSCOPE_TOKEN` | ModelScope token | - | No |
| `ARK_API_KEY` | ByteDance API key | - | No |
| `OPENAI_API_KEY` | OpenAI API key | - | No |
| `DEFAULT_TEXT_PROVIDER` | Default provider for text tasks | `zhipu` | No |
| `DEFAULT_VISION_PROVIDER` | Default provider for vision tasks | `zhipu` | No |
| `DEFAULT_THINKING_PROVIDER` | Default provider for thinking tasks | `modelscope` | No |
| `DEFAULT_TEXT_MODEL` | Default model for text tasks | `glm-4-flash` | No |
| `DEFAULT_VISION_MODEL` | Default model for vision tasks | `glm-4.6v` | No |
| `USE_UNIFIED_LLM` | Enable unified manager | `false` | No |

---

## Common Questions

### Q1: How do I modify the default Provider?

**Answer**: Edit `.env` file:

```bash
DEFAULT_TEXT_PROVIDER=deepseek
DEFAULT_VISION_PROVIDER=zhipu
DEFAULT_THINKING_PROVIDER=modelscope
```

### Q2: How do I add a custom Provider?

**Answer**: Two methods:

**Method 1: Configure via .env**

```bash
CUSTOM_PROVIDER_1_NAME=MyProxy
CUSTOM_PROVIDER_1_BASE_URL=https://my-proxy.com/v1
CUSTOM_PROVIDER_1_API_KEY=MY_PROXY_KEY
CUSTOM_PROVIDER_1_MODELS=gpt-4,gpt-4o
```

**Method 2: Register via code**

```python
from utils.llm.provider_registry import ProviderRegistry, ProviderInfo, ProviderCapability

registry = ProviderRegistry()
custom = ProviderInfo(
    id="my-provider",
    name="My Custom Provider",
    base_url="https://api.example.com/v1",
    api_key_env="MY_API_KEY",
    models=["model-1", "model-2"],
    capabilities=[ProviderCapability.TEXT],
)
registry.register_custom_provider(custom)
```

### Q3: How do I switch models?

**Answer**: Two methods:

**Method 1: Via .env (affects defaults)**

```bash
DEFAULT_TEXT_MODEL=deepseek-chat
DEFAULT_VISION_MODEL=doubao-vision
```

**Method 2: Via code (specific call)**

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()
client = manager.get_client(provider="zhipu", model="glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```

### Q4: Where are default values set?

**Answer**: Default values are set in three places:

1. **Hard-coded defaults** (lowest priority):
   - `config/settings.py`: `PROVIDER_DEFAULTS` and `MODEL_DEFAULTS`

2. **Environment variables** (medium priority):
   - `.env` file: `DEFAULT_TEXT_PROVIDER`, `DEFAULT_TEXT_MODEL`, etc.

3. **Runtime configuration** (highest priority):
   - Explicit parameters in code: `manager.get_client(provider="zhipu", model="glm-4-flash")`

---

## Configuration Verification

### View All Available Providers

```python
from utils.llm import ProviderRegistry

registry = ProviderRegistry()

# List all providers
all_providers = registry.get_all_providers()
for pid, provider in all_providers.items():
    print(f"Provider ID: {pid}")
    print(f"  Name: {provider.name}")
    print(f"  Base URL: {provider.base_url}")
    print(f"  API Key Env: {provider.api_key_env}")
    print(f"  Models: {provider.models}")
    print()
```

### View Providers with Configured API Keys

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# View available providers
available = manager.list_available_providers()
print("Available providers:", list(available.keys()))
```

### Verify Configuration Consistency

Run the verification script:

```bash
python verify_provider_config.py
```

---

## Usage Examples

### Example 1: Use Default Provider

```python
from utils.llm import UnifiedLLMManager

manager = UnifiedLLMManager()

# Use default provider and model (read from .env)
client = manager.get_client(provider="zhipu", model="glm-4-flash")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```

### Example 2: Provider-Level Fallback

```python
from config.llm_config import PROVIDER_FALLBACK_CHAINS

manager = UnifiedLLMManager()

result = manager.chat_with_fallback(
    messages=[{"role": "user", "content": "Hello"}],
    providers=PROVIDER_FALLBACK_CHAINS["text"]  # ["zhipu", "deepseek", "openai"]
)
```

### Example 3: Query Provider Capabilities

```python
from utils.llm import ProviderRegistry, ProviderCapability

registry = ProviderRegistry()

# Find all providers supporting vision
vision_providers = registry.list_providers(capability=ProviderCapability.VISION)

for pid, provider in vision_providers.items():
    print(f"{provider.name}: {provider.models}")
```

---

## Related Documentation

- [LLM Provider Guide](llm_provider_guide.md) - Comprehensive provider selection guide
- [Unified LLM Architecture Guide](unified_llm_guide.md) - New architecture usage guide
- [Network Issues Troubleshooting](network_troubleshooting.md) - Network problem solutions

---

## Quick Reference

### Configuration File Locations

```
Project Root/
├── .env                          # User configuration (API keys, defaults)
├── config/
│   ├── settings.py              # Global configuration and defaults
│   └── llm_config.py            # Fallback strategies and recommendations
└── utils/
    └── llm/
        ├── provider_registry.py  # Provider definitions
        ├── model_registry.py     # Model definitions
        └── unified_manager.py    # Unified manager
```

### Configuration Priority

```
Runtime Parameters > .env File > Hard-coded Defaults
```

### Common Configuration Tasks

| Task | File | Example |
|------|------|---------|
| Set API key | `.env` | `GLM_API_KEY=xxx` |
| Set default provider | `.env` | `DEFAULT_TEXT_PROVIDER=zhipu` |
| Set default model | `.env` | `DEFAULT_TEXT_MODEL=glm-4-flash` |
| Add custom provider | `.env` or code | See above |
| Add built-in provider | `provider_registry.py` | Add to `BUILTIN_PROVIDERS` |

---

**Last Updated**: 2026-01-28
