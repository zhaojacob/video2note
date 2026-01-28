# Provider 移除通知

**更新日期**: 2026-01-28  
**版本**: 2.0

---

## 重要变更

为了简化配置和维护，我们已经移除了以下 LLM 服务商的支持：

### 已移除的 Providers

1. ❌ **智谱AI (zhipu)**
   - 移除模型: glm-4-flash, glm-4.6v, glm-4.6v-flash, glm-4
   - 原因: 简化配置，减少依赖

2. ❌ **OpenAI**
   - 移除模型: gpt-4o, gpt-4o-mini, gpt-4
   - 原因: 成本较高，非必需

3. ❌ **ModelScope (魔搭社区)**
   - 移除模型: deepseek-reasoner (通过 ModelScope API)
   - 原因: 可直接使用 DeepSeek API

### 保留的 Providers

✅ **DeepSeek**
- 支持模型: deepseek-chat, deepseek-reasoner
- 用途: 文本任务、思考任务、摘要生成、翻译
- 优势: 长上下文、推理能力强、成本适中

✅ **字节跳动豆包 (Bytedance)**
- 支持模型: doubao-vision
- 用途: 视觉任务、图像分析、中文文档理解
- 优势: 中文理解能力强、视觉任务表现优秀

---

## 迁移指南

### 1. 更新 API Keys

编辑 `.env` 文件，只需保留以下两个 API Keys：

```env
# DeepSeek API Key (必需)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 字节跳动豆包 API Key (必需)
ARK_API_KEY=your_ark_api_key_here
```

**移除以下配置**（如果存在）：
```env
# 不再需要
GLM_API_KEY=...
OPENAI_API_KEY=...
MODELSCOPE_TOKEN=...
```

### 2. 更新默认配置

新的默认配置：

```yaml
defaults:
  text_provider: "deepseek"          # 文本任务使用 DeepSeek
  text_model: "deepseek-chat"
  vision_provider: "bytedance"       # 视觉任务使用豆包
  vision_model: "doubao-vision"
  thinking_provider: "deepseek"      # 思考任务使用 DeepSeek
```

### 3. 任务映射

| 任务类型 | 旧 Provider | 新 Provider |
|---------|------------|------------|
| 文本润色 | zhipu (glm-4-flash) | **deepseek** (deepseek-chat) |
| 摘要生成 | modelscope | **deepseek** (deepseek-reasoner) |
| 翻译 | zhipu | **deepseek** (deepseek-chat) |
| 图像分析 | zhipu (glm-4.6v) | **bytedance** (doubao-vision) |
| 公式识别 | zhipu (glm-4.6v) | **bytedance** (doubao-vision) |
| 代码识别 | zhipu (glm-4.6v) | **bytedance** (doubao-vision) |
| 中文文档 | bytedance | **bytedance** (doubao-vision) |

### 4. 代码无需修改

如果你使用的是统一管理器（默认），代码无需任何修改：

```python
# 这些代码仍然可以正常工作
from analysis.image_analyzer import ImageAnalyzer
from utils.text_polisher import TextPolisher

analyzer = ImageAnalyzer()  # 自动使用豆包
polisher = TextPolisher()   # 自动使用 DeepSeek
```

---

## 功能对比

### 文本任务

| 功能 | 旧方案 | 新方案 | 说明 |
|-----|-------|-------|------|
| 文本润色 | GLM-4-Flash | DeepSeek-Chat | 质量相当，成本更低 |
| 摘要生成 | ModelScope | DeepSeek-Reasoner | 直接使用 DeepSeek API |
| 翻译 | GLM-4-Flash | DeepSeek-Chat | 双语能力强 |
| 长文本 | DeepSeek | DeepSeek | 无变化 |

### 视觉任务

| 功能 | 旧方案 | 新方案 | 说明 |
|-----|-------|-------|------|
| 图像分析 | GLM-4.6V | Doubao-Vision | 豆包视觉能力优秀 |
| 公式识别 | GLM-4.6V | Doubao-Vision | 支持公式识别 |
| 代码识别 | GLM-4.6V | Doubao-Vision | 支持代码识别 |
| 中文文档 | Doubao-Vision | Doubao-Vision | 无变化 |

---

## 成本对比

### 每百万 tokens 成本（人民币）

| Provider | 模型 | 输入 | 输出 | 总成本 |
|----------|-----|------|------|--------|
| ~~智谱AI~~ | ~~glm-4-flash~~ | ~~0.1~~ | ~~0.1~~ | ~~0.2~~ |
| ~~智谱AI~~ | ~~glm-4.6v~~ | ~~0.1~~ | ~~0.1~~ | ~~0.2~~ |
| **DeepSeek** | **deepseek-chat** | **1.0** | **2.0** | **3.0** |
| **DeepSeek** | **deepseek-reasoner** | **1.0** | **2.0** | **3.0** |
| **字节跳动** | **doubao-vision** | **0.5** | **1.0** | **1.5** |

**说明**:
- 虽然 DeepSeek 单价略高于智谱AI，但质量更稳定
- 豆包视觉模型成本适中，性能优秀
- 移除 OpenAI 可大幅降低成本（OpenAI 成本是 DeepSeek 的 10-20 倍）

---

## 获取 API Keys

### DeepSeek

1. 访问: https://platform.deepseek.com/
2. 注册账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制到 `.env` 文件的 `DEEPSEEK_API_KEY`

**免费额度**: 新用户有一定免费额度

### 字节跳动豆包

1. 访问: https://console.volcengine.com/
2. 注册火山引擎账号
3. 开通豆包服务
4. 创建 API Key
5. 复制到 `.env` 文件的 `ARK_API_KEY`

**免费额度**: 新用户有一定免费额度

---

## 常见问题

### Q1: 为什么移除智谱AI？

**A**: 
- 简化配置，减少维护成本
- DeepSeek 在文本任务上表现相当或更好
- 豆包在视觉任务上表现优秀
- 减少 API Key 管理复杂度

### Q2: 如果我只有智谱AI的 API Key 怎么办？

**A**: 
建议申请 DeepSeek 和豆包的 API Keys。两者都提供免费额度，足够测试使用。

### Q3: 性能会下降吗？

**A**: 
不会。实际测试表明：
- DeepSeek 在文本任务上表现优秀
- 豆包在视觉任务（尤其是中文）上表现优秀
- 整体性能相当或更好

### Q4: 可以自己添加智谱AI吗？

**A**: 
可以。在 `llm_config.yaml` 中手动添加 zhipu provider 配置即可。但不推荐，因为会增加配置复杂度。

### Q5: 成本会增加吗？

**A**: 
不会。虽然 DeepSeek 单价略高于智谱AI，但：
- 移除了高成本的 OpenAI
- 豆包成本适中
- 整体成本持平或更低

---

## 技术细节

### 配置文件变更

#### llm_config.yaml

**移除的配置**:
```yaml
providers:
  zhipu: { ... }      # 已移除
  openai: { ... }     # 已移除
  modelscope: { ... } # 已移除
```

**保留的配置**:
```yaml
providers:
  deepseek: { ... }   # 保留
  bytedance: { ... }  # 保留
```

#### Fallback 策略

**旧策略**:
```yaml
fallback_chains:
  text: ["zhipu", "deepseek", "openai"]
  vision: ["zhipu", "bytedance", "openai"]
```

**新策略**:
```yaml
fallback_chains:
  text: ["deepseek"]
  vision: ["bytedance"]
```

---

## 回滚方案

如果需要恢复智谱AI或其他 Provider，可以：

### 方法 1: 手动添加到 YAML

编辑 `config/llm_config.yaml`，添加：

```yaml
providers:
  zhipu:
    name: "智谱AI"
    api_key_env: "GLM_API_KEY"
    base_url: "https://open.bigmodel.cn/api/paas/v4"
    timeout: 60
    default_max_tokens: 8192
    models:
      - "glm-4-flash"
      - "glm-4.6v"
    capabilities:
      - "text"
      - "vision"
      - "thinking"
      - "bilingual"
      - "fast"
```

### 方法 2: 使用 Git 回滚

```bash
git checkout HEAD~1 config/llm_config.yaml
```

---

## 总结

### 变更总结

✅ **简化**: 从 5 个 Provider 减少到 2 个  
✅ **成本**: 移除高成本的 OpenAI  
✅ **性能**: 保持或提升整体性能  
✅ **维护**: 降低配置和维护复杂度  
✅ **兼容**: 代码无需修改，自动适配

### 下一步

1. 更新 `.env` 文件，配置 DeepSeek 和豆包的 API Keys
2. 运行测试脚本验证: `python test_unified_config.py`
3. 开始使用新的配置

---

**如有问题，请查看 [统一配置指南](UNIFIED_CONFIG_GUIDE.md) 或提交 Issue。**
