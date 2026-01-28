# Video Note System - 快速开始指南 v2.0

**版本**: 2.0  
**更新日期**: 2026-01-28

---

## 🚀 5 分钟快速开始

### 1️⃣ 配置 API Keys

编辑 `.env` 文件（如果不存在，复制 `.env.example`）：

```env
# DeepSeek API Key (文本任务)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 字节跳动豆包 API Key (视觉任务)
ARK_API_KEY=your_ark_api_key_here
```

### 2️⃣ 获取 API Keys

#### DeepSeek
- 访问: https://platform.deepseek.com/
- 注册并创建 API Key
- 复制到 `.env` 文件

#### 字节跳动豆包
- 访问: https://console.volcengine.com/
- 注册火山引擎账号
- 开通豆包服务并创建 API Key
- 复制到 `.env` 文件

### 3️⃣ 测试配置

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
🎉 All tests passed!
```

### 4️⃣ 开始使用

```bash
# 处理视频
python main.py --url "https://www.youtube.com/watch?v=xxxxx"

# 或使用 CLI
python cli.py
```

---

## 📋 系统配置

### 支持的 Providers

| Provider | 用途 | 模型 |
|----------|------|------|
| **DeepSeek** | 文本任务、思考任务 | deepseek-chat, deepseek-reasoner |
| **字节跳动豆包** | 视觉任务 | doubao-vision |

### 任务映射

| 任务类型 | 使用的 Provider | 模型 |
|---------|----------------|------|
| 文本润色 | DeepSeek | deepseek-chat |
| 摘要生成 | DeepSeek | deepseek-reasoner |
| 翻译 | DeepSeek | deepseek-chat |
| 图像分析 | 豆包 | doubao-vision |
| 公式识别 | 豆包 | doubao-vision |
| 代码识别 | 豆包 | doubao-vision |
| 中文文档 | 豆包 | doubao-vision |

---

## 🔧 配置文件

### 主配置: `config/llm_config.yaml`

```yaml
# 默认设置
defaults:
  text_provider: "deepseek"
  text_model: "deepseek-chat"
  vision_provider: "bytedance"
  vision_model: "doubao-vision"
  use_unified_manager: true

# Providers
providers:
  deepseek:
    name: "DeepSeek"
    api_key_env: "DEEPSEEK_API_KEY"
    base_url: "https://api.deepseek.com"
    models:
      - "deepseek-chat"
      - "deepseek-reasoner"
  
  bytedance:
    name: "字节跳动豆包"
    api_key_env: "ARK_API_KEY"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    models:
      - "doubao-vision"
```

---

## 💡 使用示例

### Python 代码

```python
# 图像分析
from analysis.image_analyzer import ImageAnalyzer

analyzer = ImageAnalyzer()  # 自动使用豆包
result = analyzer.analyze_single(frame_data)

# 文本润色
from utils.text_polisher import TextPolisher

polisher = TextPolisher()  # 自动使用 DeepSeek
polished = polisher.polish(raw_transcript)

# 直接使用 LLM
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()
client = manager.get_client(provider="deepseek", model="deepseek-chat")
result = client.chat_completion([{"role": "user", "content": "Hello"}])
```

---

## 📊 成本参考

| Provider | 模型 | 输入 (CNY/M tokens) | 输出 (CNY/M tokens) |
|----------|-----|-------------------|-------------------|
| DeepSeek | deepseek-chat | 1.0 | 2.0 |
| DeepSeek | deepseek-reasoner | 1.0 | 2.0 |
| 豆包 | doubao-vision | 0.5 | 1.0 |

**说明**: M = 百万 (Million)

---

## ⚙️ 高级配置

### 修改默认 Provider

编辑 `config/llm_config.yaml`:

```yaml
defaults:
  text_provider: "deepseek"  # 修改这里
  vision_provider: "bytedance"  # 修改这里
```

### 修改超时时间

```yaml
providers:
  deepseek:
    timeout: 120  # 改为 120 秒
```

### 修改并发数

```yaml
concurrency:
  max_concurrent: 10  # 改为 10 个并发
```

---

## 🐛 故障排查

### 问题 1: API Key 未配置

**错误**: `Provider deepseek not available`

**解决**:
1. 检查 `.env` 文件是否存在
2. 确认 `DEEPSEEK_API_KEY` 已配置
3. 确认 API Key 正确

### 问题 2: 配置文件错误

**错误**: `FileNotFoundError: LLM configuration file not found`

**解决**:
1. 确认 `config/llm_config.yaml` 存在
2. 检查文件权限
3. 运行测试: `python test_unified_config.py`

### 问题 3: 网络连接失败

**错误**: `Connection failed` 或 `Timeout`

**解决**:
1. 检查网络连接
2. 检查防火墙设置
3. 尝试增加超时时间

---

## 📚 文档

- 📖 [统一配置指南](docs/UNIFIED_CONFIG_GUIDE.md) - 详细配置说明
- 📖 [Provider 移除通知](docs/PROVIDER_REMOVAL_NOTICE.md) - 变更说明
- 📖 [迁移指南](docs/MIGRATION_GUIDE.md) - 从旧版本迁移
- 📖 [实施总结](docs/IMPLEMENTATION_SUMMARY.md) - 技术细节

---

## 🆚 版本对比

### v1.0 vs v2.0

| 项目 | v1.0 | v2.0 |
|-----|------|------|
| Providers | 5 个 | 2 个 ✅ |
| API Keys | 5 个 | 2 个 ✅ |
| 配置复杂度 | 高 | 低 ✅ |
| 维护成本 | 高 | 低 ✅ |
| 性能 | 优秀 | 优秀 ✅ |

---

## ❓ 常见问题

### Q: 为什么只有 2 个 Provider？

**A**: DeepSeek 覆盖所有文本任务，豆包覆盖所有视觉任务，已经满足所有需求。

### Q: 可以添加其他 Provider 吗？

**A**: 可以。在 `llm_config.yaml` 中添加配置即可。

### Q: 成本会增加吗？

**A**: 不会。移除了高成本的 OpenAI，整体成本持平或更低。

### Q: 性能会下降吗？

**A**: 不会。DeepSeek 和豆包在各自领域表现优秀。

---

## 🎯 下一步

1. ✅ 配置 API Keys
2. ✅ 运行测试验证
3. ✅ 开始处理视频
4. 📖 阅读详细文档（可选）

---

**🎉 配置完成！开始使用 Video Note System 吧！**

**需要帮助？** 查看 [统一配置指南](docs/UNIFIED_CONFIG_GUIDE.md) 或提交 Issue。
