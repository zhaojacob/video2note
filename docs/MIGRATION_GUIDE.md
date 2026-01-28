# 迁移指南：从 Legacy 架构到统一配置系统

**版本**: 1.0  
**更新日期**: 2026-01-28

---

## 概述

本指南帮助你从旧的 Legacy 架构迁移到新的统一配置系统。

### 主要变化

| 方面 | 旧架构 (Legacy) | 新架构 (Unified) |
|------|----------------|------------------|
| **配置方式** | 分散在多个 Python 文件 | 集中在 `llm_config.yaml` |
| **客户端** | `GLMClient`, `DoubaoClient` 等独立客户端 | `UnifiedLLMManager` 统一管理 |
| **降级策略** | 手动实现 | 自动 Provider 级降级 |
| **默认启用** | 需要手动启用 | 默认启用 |
| **Base URL** | 格式不一致 | 统一格式 |

---

## 迁移步骤

### 步骤 1: 备份现有配置

在开始迁移前，备份你的配置文件：

```bash
# 备份 .env 文件
copy .env .env.backup

# 备份 settings.py（如果你修改过）
copy config\settings.py config\settings.py.backup
```

### 步骤 2: 检查 API Keys

确认你的 `.env` 文件包含所有需要的 API Keys：

```env
# 必需（至少配置一个）
GLM_API_KEY=your_glm_key
ARK_API_KEY=your_ark_key
DEEPSEEK_API_KEY=your_deepseek_key
MODELSCOPE_TOKEN=your_modelscope_token

# 可选
OPENAI_API_KEY=your_openai_key
```

### 步骤 3: 更新代码（如果需要）

#### 3.1 ImageAnalyzer

**旧代码**:
```python
from analysis.image_analyzer import ImageAnalyzer
from config.settings import GLM_CONFIG, DOUBAO_CONFIG

# 需要手动传入配置
analyzer = ImageAnalyzer(
    glm_config=GLM_CONFIG,
    doubao_config=DOUBAO_CONFIG,
    use_unified_manager=False  # 旧架构
)
```

**新代码**:
```python
from analysis.image_analyzer import ImageAnalyzer

# 自动使用统一管理器，无需传入配置
analyzer = ImageAnalyzer()  # use_unified_manager=True 是默认值
```

#### 3.2 TextPolisher

**旧代码**:
```python
from utils.text_polisher import TextPolisher
from config.settings import TEXT_LLM_CONFIGS, TEXT_LLM_PROVIDER

config = TEXT_LLM_CONFIGS[TEXT_LLM_PROVIDER]
polisher = TextPolisher(
    api_key=config["api_key"],
    use_unified_manager=False  # 旧架构
)
```

**新代码**:
```python
from utils.text_polisher import TextPolisher

# 自动使用统一管理器，无需传入配置
polisher = TextPolisher()  # use_unified_manager=True 是默认值
```

#### 3.3 直接使用 LLM 客户端

**旧代码**:
```python
from analysis.glm_client import GLMClient
from config.settings import GLM_CONFIG

client = GLMClient(**GLM_CONFIG)
result = client.analyze(image_path, prompt)
```

**新代码**:
```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()
client = manager.get_client(provider="zhipu", model="glm-4.6v")
result = client.analyze_image(image_path, prompt)
```

### 步骤 4: 自定义配置（如果需要）

如果你之前修改过 `settings.py` 中的配置，现在需要在 `llm_config.yaml` 中进行相应修改。

#### 4.1 修改默认 Provider

**旧方式** (`settings.py`):
```python
TEXT_LLM_PROVIDER = "deepseek"  # 修改这里
```

**新方式** (`llm_config.yaml`):
```yaml
defaults:
  text_provider: "deepseek"  # 修改这里
```

#### 4.2 修改超时时间

**旧方式** (`settings.py`):
```python
GLM_CONFIG = {
    "timeout": 120,  # 修改这里
    # ...
}
```

**新方式** (`llm_config.yaml`):
```yaml
providers:
  zhipu:
    timeout: 120  # 修改这里
```

#### 4.3 修改降级策略

**旧方式** (需要在代码中实现):
```python
# 需要手动编写降级逻辑
try:
    result = glm_client.analyze(...)
except:
    result = doubao_client.analyze(...)
```

**新方式** (`llm_config.yaml`):
```yaml
fallback_chains:
  vision: ["zhipu", "bytedance", "openai"]  # 自动降级
```

### 步骤 5: 测试迁移结果

运行测试脚本验证迁移是否成功：

```bash
python test_unified_config.py
```

预期输出：
```
✓ PASS: YAML Loading
✓ PASS: Provider Registry
✓ PASS: UnifiedLLMManager
✓ PASS: ImageAnalyzer
✓ PASS: TextPolisher
✓ PASS: Settings Integration

Total: 6/6 tests passed
🎉 All tests passed! Configuration system is working correctly.
```

---

## 常见迁移问题

### 问题 1: 代码仍在使用旧架构

**症状**: 日志显示 "Initialized with legacy LLMClient"

**原因**: 代码中显式设置了 `use_unified_manager=False`

**解决方法**:
```python
# 移除这个参数，或改为 True
analyzer = ImageAnalyzer(use_unified_manager=True)
# 或者直接不传参数（默认为 True）
analyzer = ImageAnalyzer()
```

### 问题 2: 找不到配置文件

**症状**: `FileNotFoundError: LLM configuration file not found`

**原因**: `llm_config.yaml` 文件不存在或路径错误

**解决方法**:
1. 确认文件存在于 `config/llm_config.yaml`
2. 如果文件不存在，从项目仓库重新获取
3. 检查文件权限

### 问题 3: API Key 未配置

**症状**: `Provider zhipu not available` 或 `API key not configured`

**原因**: `.env` 文件中缺少对应的 API Key

**解决方法**:
1. 检查 `.env` 文件
2. 确认 API Key 变量名正确（如 `GLM_API_KEY`）
3. 确认 API Key 值正确

### 问题 4: 旧配置仍在生效

**症状**: 修改 `llm_config.yaml` 后没有效果

**原因**: 配置被缓存或代码仍在使用旧配置

**解决方法**:
1. 重启 Python 进程
2. 检查代码是否仍在使用 `settings.py` 中的配置
3. 使用 `force_reload=True` 强制重新加载：
   ```python
   from config.yaml_config_loader import load_llm_config
   config = load_llm_config(force_reload=True)
   ```

---

## 回滚到旧架构

如果迁移后遇到问题，可以临时回滚到旧架构：

### 方法 1: 环境变量

在 `.env` 文件中添加：

```env
USE_UNIFIED_LLM=false
```

### 方法 2: 代码参数

在代码中显式指定：

```python
# ImageAnalyzer
analyzer = ImageAnalyzer(
    glm_config=GLM_CONFIG,
    doubao_config=DOUBAO_CONFIG,
    use_unified_manager=False
)

# TextPolisher
polisher = TextPolisher(use_unified_manager=False)
```

### 方法 3: 恢复备份

如果修改了配置文件：

```bash
# 恢复 .env
copy .env.backup .env

# 恢复 settings.py
copy config\settings.py.backup config\settings.py
```

---

## 迁移检查清单

使用此清单确保迁移完整：

### 配置文件

- [ ] `.env` 文件包含所有需要的 API Keys
- [ ] `llm_config.yaml` 文件存在且格式正确
- [ ] 自定义配置已从 `settings.py` 迁移到 `llm_config.yaml`

### 代码更新

- [ ] 移除了 `use_unified_manager=False` 参数
- [ ] 移除了手动传入的配置参数（如 `glm_config`）
- [ ] 更新了直接使用 Legacy 客户端的代码

### 测试验证

- [ ] 运行 `test_unified_config.py` 全部通过
- [ ] 测试图像分析功能正常
- [ ] 测试文本润色功能正常
- [ ] 测试降级策略工作正常

### 文档更新

- [ ] 阅读了 [统一配置指南](UNIFIED_CONFIG_GUIDE.md)
- [ ] 了解了新的配置方式
- [ ] 知道如何添加自定义 Provider

---

## 迁移后的优势

完成迁移后，你将获得以下优势：

### 1. 简化配置

**之前**:
- 需要在多个文件中配置
- 需要手动传入配置参数
- 配置分散难以管理

**现在**:
- 所有配置集中在一个 YAML 文件
- 无需手动传入参数
- 配置清晰易于管理

### 2. 自动降级

**之前**:
- 需要手动编写降级逻辑
- 容易遗漏错误处理
- 代码冗余

**现在**:
- 自动 Provider 级降级
- 统一的错误处理
- 代码简洁

### 3. 灵活扩展

**之前**:
- 添加新 Provider 需要修改多处代码
- 需要创建新的客户端类
- 维护成本高

**现在**:
- 只需在 YAML 中添加配置
- 无需修改代码
- 维护成本低

### 4. 任务优化

**之前**:
- 所有任务使用相同的 Provider
- 无法针对任务类型优化
- 成本和性能不够优化

**现在**:
- 不同任务自动选择最优 Provider
- 基于任务特点的智能推荐
- 成本和性能优化

---

## 获取帮助

如果在迁移过程中遇到问题：

1. **查看日志**: `output/system.log`
2. **运行测试**: `python test_unified_config.py`
3. **查看文档**:
   - [统一配置指南](UNIFIED_CONFIG_GUIDE.md)
   - [实施总结](IMPLEMENTATION_SUMMARY.md)
   - [项目分析](PROJECT_ANALYSIS_AND_FIX_PLAN.md)

---

## 总结

迁移到新的统一配置系统是一个简单的过程：

1. ✅ 确保 API Keys 配置正确
2. ✅ 移除代码中的 `use_unified_manager=False`
3. ✅ 将自定义配置迁移到 `llm_config.yaml`
4. ✅ 运行测试验证

大多数情况下，你**不需要修改任何代码**，因为新架构已经默认启用。

**迁移完成后，你将拥有一个更简单、更强大、更易维护的 LLM 配置系统！**

---

**更新日期**: 2026-01-28  
**版本**: 1.0
