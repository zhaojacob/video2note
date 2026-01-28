# LLM 统一配置系统 - 用户指南

**版本**: 1.0  
**更新日期**: 2026-01-28

---

## 快速开始

### 1. 配置 API Keys

编辑项目根目录的 `.env` 文件，添加你的 API Keys：

```env
# 智谱AI (GLM)
GLM_API_KEY=your_glm_api_key_here

# 字节跳动豆包
ARK_API_KEY=your_ark_api_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ModelScope
MODELSCOPE_TOKEN=your_modelscope_token_here

# OpenAI (可选)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 检查配置

运行测试脚本验证配置：

```bash
python test_unified_config.py
```

### 3. 开始使用

配置完成后，系统会自动使用统一管理器，无需额外代码修改。

---

## 配置文件说明

### 主配置文件: `config/llm_config.yaml`

这是所有 LLM 相关配置的集中管理文件。

#### 1. 默认设置 (defaults)

```yaml
defaults:
  text_provider: "zhipu"          # 文本任务默认 Provider
  text_model: "glm-4-flash"       # 文本任务默认模型
  vision_provider: "zhipu"        # 视觉任务默认 Provider
  vision_model: "glm-4.6v"        # 视觉任务默认模型
  thinking_provider: "modelscope" # 思考任务默认 Provider
  use_unified_manager: true       # 是否启用统一管理器
```

**修改建议**:
- 如果你主要使用 DeepSeek，可以将 `text_provider` 改为 `"deepseek"`
- 如果你想使用豆包做视觉任务，可以将 `vision_provider` 改为 `"bytedance"`

#### 2. Provider 配置 (providers)

每个 Provider 的详细配置：

```yaml
providers:
  zhipu:
    name: "智谱AI"
    api_key_env: "GLM_API_KEY"                          # 对应 .env 中的变量名
    base_url: "https://open.bigmodel.cn/api/paas/v4"   # API 地址
    timeout: 60                                         # 超时时间（秒）
    default_max_tokens: 8192                            # 默认最大 tokens
    models:                                             # 支持的模型列表
      - "glm-4-flash"
      - "glm-4.6v"
      - "glm-4.6v-flash"
      - "glm-4"
    capabilities:                                       # 能力标签
      - "text"
      - "vision"
      - "thinking"
      - "bilingual"
      - "fast"
```

**添加自定义 Provider**:

```yaml
providers:
  my_provider:
    name: "我的自定义 Provider"
    api_key_env: "MY_API_KEY"
    base_url: "https://api.example.com/v1"
    timeout: 60
    default_max_tokens: 4096
    models:
      - "my-model-1"
      - "my-model-2"
    capabilities:
      - "text"
      - "vision"
```

然后在 `.env` 中添加：

```env
MY_API_KEY=your_api_key_here
```

#### 3. 任务推荐 (task_recommendations)

为不同任务推荐最合适的 Provider 和模型：

```yaml
task_recommendations:
  polish:                                    # 文本润色
    providers: ["zhipu", "deepseek"]        # 推荐的 Provider 列表
    models: ["glm-4-flash", "deepseek-chat"] # 推荐的模型列表
    reason: "快速、成本低，适合文本润色"    # 推荐理由
  
  vision_formula:                            # 数学公式识别
    providers: ["zhipu"]
    models: ["glm-4.6v"]
    fallback_providers: ["bytedance"]       # 降级 Provider
    reason: "GLM在数学公式识别方面表现优秀"
```

**修改任务推荐**:

如果你发现某个 Provider 在特定任务上表现更好，可以调整顺序：

```yaml
task_recommendations:
  polish:
    providers: ["deepseek", "zhipu"]  # 优先使用 DeepSeek
    models: ["deepseek-chat", "glm-4-flash"]
```

#### 4. Fallback 策略 (fallback_chains)

定义不同任务类型的降级顺序：

```yaml
fallback_chains:
  text: ["zhipu", "deepseek", "openai"]      # 文本任务降级链
  vision: ["zhipu", "bytedance", "openai"]   # 视觉任务降级链
  thinking: ["modelscope", "zhipu", "deepseek"] # 思考任务降级链
```

**工作原理**:
- 系统会按顺序尝试每个 Provider
- 如果第一个失败，自动尝试第二个
- 直到成功或全部失败

#### 5. 并发和重试配置 (concurrency)

```yaml
concurrency:
  max_concurrent: 5           # 最大并发请求数
  enable_checkpoint: true     # 是否启用断点续传
  checkpoint_dir: "output/checkpoints"  # 断点文件目录
  max_retries: 3              # 最大重试次数
  retry_delay: 2              # 重试延迟（秒）
  exponential_backoff: true   # 是否使用指数退避
```

**调整建议**:
- 如果 API 有速率限制，降低 `max_concurrent`
- 如果网络不稳定，增加 `max_retries` 和 `retry_delay`

---

## 常见使用场景

### 场景 1: 只使用一个 Provider

如果你只有一个 Provider 的 API Key（比如只有 GLM）：

1. 在 `.env` 中只配置 GLM：
   ```env
   GLM_API_KEY=your_key_here
   ```

2. 修改 `llm_config.yaml` 的默认设置：
   ```yaml
   defaults:
     text_provider: "zhipu"
     vision_provider: "zhipu"
   ```

3. 修改 fallback 策略（移除其他 Provider）：
   ```yaml
   fallback_chains:
     text: ["zhipu"]
     vision: ["zhipu"]
   ```

### 场景 2: 优先使用免费额度高的 Provider

如果你想优先使用免费额度高的 Provider：

```yaml
defaults:
  text_provider: "zhipu"  # GLM 免费额度较高
  vision_provider: "zhipu"

fallback_chains:
  text: ["zhipu", "deepseek", "openai"]  # 优先 GLM
  vision: ["zhipu", "bytedance", "openai"]
```

### 场景 3: 不同任务使用不同 Provider

通过任务推荐配置：

```yaml
task_recommendations:
  polish:
    providers: ["zhipu"]  # 文本润色用 GLM（快速）
  
  vision_formula:
    providers: ["zhipu"]  # 公式识别用 GLM（准确）
  
  vision_chinese:
    providers: ["bytedance"]  # 中文文档用豆包（理解好）
  
  summarize:
    providers: ["deepseek"]  # 摘要用 DeepSeek（长上下文）
```

### 场景 4: 成本优化

根据成本参考调整：

```yaml
# 成本参考（每百万 tokens，单位：元）
cost_reference:
  glm-4-flash: {input: 0.1, output: 0.1}      # 最便宜
  deepseek-chat: {input: 1.0, output: 2.0}    # 中等
  gpt-4o: {input: 2.5, output: 10.0}          # 最贵（USD）
```

优先使用便宜的模型：

```yaml
defaults:
  text_model: "glm-4-flash"  # 最便宜的文本模型

fallback_chains:
  text: ["zhipu", "deepseek", "openai"]  # 从便宜到贵
```

---

## 高级配置

### 1. 模型别名

某些 Provider 的模型名称在 API 调用时需要映射：

```yaml
providers:
  modelscope:
    models:
      - "deepseek-reasoner"
    model_aliases:
      deepseek-reasoner: "deepseek-ai/DeepSeek-V3.2"  # API 调用时使用真实名称
```

### 2. 额外参数

某些 Provider 需要额外的请求参数：

```yaml
providers:
  modelscope:
    requires_extra_body: true
    extra_body:
      enable_thinking: true  # 启用思考模式
```

### 3. 超时设置

不同 Provider 可以设置不同的超时时间：

```yaml
providers:
  zhipu:
    timeout: 60  # 1分钟
  
  bytedance:
    timeout: 300  # 5分钟（视觉任务较慢）
  
  modelscope:
    timeout: 600  # 10分钟（思考模式很慢）
```

---

## 故障排查

### 问题 1: 配置加载失败

**错误信息**: `FileNotFoundError: LLM configuration file not found`

**解决方法**:
1. 确认 `config/llm_config.yaml` 文件存在
2. 检查文件路径是否正确
3. 检查文件权限

### 问题 2: Provider 不可用

**错误信息**: `Provider zhipu not available`

**解决方法**:
1. 检查 `.env` 文件中是否配置了对应的 API Key
2. 检查 API Key 是否正确
3. 检查网络连接
4. 运行测试脚本查看详细信息：
   ```bash
   python test_unified_config.py
   ```

### 问题 3: YAML 解析错误

**错误信息**: `yaml.YAMLError: ...`

**解决方法**:
1. 检查 YAML 语法是否正确（缩进、冒号、引号等）
2. 使用在线 YAML 验证器验证文件
3. 查看错误信息中的行号

### 问题 4: 所有 Provider 都失败

**错误信息**: `All providers failed`

**解决方法**:
1. 检查网络连接
2. 检查所有 API Keys 是否有效
3. 检查 API 配额是否用完
4. 查看日志文件 `output/system.log`

---

## 最佳实践

### 1. API Key 管理

✅ **推荐做法**:
- API Keys 存储在 `.env` 文件中
- `.env` 文件不要提交到 Git
- 使用 `.env.example` 作为模板

❌ **不推荐做法**:
- 不要在 YAML 文件中直接写 API Key
- 不要在代码中硬编码 API Key

### 2. 配置版本控制

✅ **推荐做法**:
- `llm_config.yaml` 提交到 Git
- `.env` 添加到 `.gitignore`
- 团队共享 `llm_config.yaml`

### 3. 降级策略

✅ **推荐做法**:
- 至少配置 2-3 个 Provider
- 按成本从低到高排序
- 定期测试降级链是否工作

### 4. 性能优化

✅ **推荐做法**:
- 根据任务类型选择合适的模型
- 使用 `max_concurrent` 控制并发
- 启用 `checkpoint` 避免重复处理

---

## 参考资料

### 相关文档

- [项目分析与修复计划](PROJECT_ANALYSIS_AND_FIX_PLAN.md)
- [实施总结](IMPLEMENTATION_SUMMARY.md)
- [快速参考](../QUICK_REFERENCE.md)

### Provider 官方文档

- [智谱AI (GLM)](https://open.bigmodel.cn/dev/api)
- [字节跳动豆包](https://www.volcengine.com/docs/82379)
- [DeepSeek](https://platform.deepseek.com/api-docs/)
- [ModelScope](https://www.modelscope.cn/docs)
- [OpenAI](https://platform.openai.com/docs/api-reference)

### 获取 API Keys

- [智谱AI 注册](https://open.bigmodel.cn/)
- [字节跳动火山引擎](https://console.volcengine.com/)
- [DeepSeek 注册](https://platform.deepseek.com/)
- [ModelScope 注册](https://www.modelscope.cn/)
- [OpenAI 注册](https://platform.openai.com/)

---

## 更新日志

### v1.0 (2026-01-28)
- ✅ 初始版本
- ✅ 实现 YAML 配置系统
- ✅ 统一 LLM 架构
- ✅ 修复 Base URL 问题
- ✅ 默认启用统一管理器

---

**如有问题，请查看 `output/system.log` 日志文件或运行 `python test_unified_config.py` 进行诊断。**
