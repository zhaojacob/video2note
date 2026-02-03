# LLM 集成验证清单

## 快速验证步骤

### 1. 检查配置文件 ✓

- [x] `config/llm_config.yaml` 包含 `use_responses_api: true` (豆包)
- [x] `config/llm_config.yaml` 豆包模型 ID 为 `doubao-seed-1-6-vision-250815`
- [x] `config/settings.py` TEXT_LLM_PROVIDER 为 `deepseek`
- [x] `.env.example` 包含 DEEPSEEK_API_KEY 和 ARK_API_KEY

### 2. 检查代码更新 ✓

- [x] `config/yaml_config_loader.py` ProviderConfig 有 `use_responses_api` 字段
- [x] `utils/llm/provider_registry.py` ProviderInfo 有 `use_responses_api` 字段
- [x] `utils/llm/unified_manager.py` 导入 DoubaoVisionClient
- [x] `utils/llm/unified_manager.py` get_client() 检查 use_responses_api
- [x] `utils/llm/doubao_vision_client.py` 实现豆包专用 API

### 3. 验证 API Keys 配置

```bash
# 检查 .env 文件
cat .env
```

应该包含：
```env
DEEPSEEK_API_KEY=sk-xxxxx
ARK_API_KEY=xxxxx
```

### 4. 运行测试脚本

```bash
# 方式 1: 使用 python
python test_llm_integration.py

# 方式 2: 使用 py
py test_llm_integration.py

# 方式 3: 使用完整路径
F:\anaconda_projects\anaconda3\python.exe test_llm_integration.py
```

预期输出：
```
================================================================================
LLM INTEGRATION TEST SUITE
================================================================================

================================================================================
TEST 4: API Key Configuration
================================================================================
✓ DEEPSEEK_API_KEY configured (length: XX)
✓ ARK_API_KEY configured (length: XX)

================================================================================
TEST 3: Client Type Verification
================================================================================
✓ DeepSeek uses standard LLMClient
✓ Doubao uses DoubaoVisionClient

================================================================================
TEST 1: DeepSeek Text Model (deepseek-chat)
================================================================================
✓ DeepSeek client created successfully
  Model: deepseek-chat
  Base URL: https://api.deepseek.com

[Testing chat completion...]
✓ Chat completion successful
  Response: 你好，DeepSeek！

================================================================================
TEST 2: Doubao Vision Model (doubao-seed-1-6-vision-250815)
================================================================================
✓ Doubao client created successfully
  Client type: DoubaoVisionClient
  Model: doubao-seed-1-6-vision-250815
  Base URL: https://ark.cn-beijing.volces.com/api/v3
✓ Correct client type: DoubaoVisionClient

================================================================================
TEST SUMMARY
================================================================================
✓ PASS: API Keys
✓ PASS: Client Types
✓ PASS: DeepSeek Text
✓ PASS: Doubao Vision

Total: 4/4 tests passed

🎉 All tests passed!
```

### 5. 手动验证 - DeepSeek 文本

```python
from utils.llm.unified_manager import UnifiedLLMManager

manager = UnifiedLLMManager()
client = manager.get_client(provider="deepseek", model="deepseek-chat")

if client:
    response = client.chat_completion([
        {"role": "user", "content": "Say hello in Chinese"}
    ])
    print(response)
else:
    print("❌ DeepSeek client not available")
```

预期输出：
```
你好！
```

### 6. 手动验证 - 豆包视觉

```python
from utils.llm.unified_manager import UnifiedLLMManager
from utils.llm.doubao_vision_client import DoubaoVisionClient

manager = UnifiedLLMManager()
client = manager.get_client(provider="bytedance", model="doubao-seed-1-6-vision-250815")

print(f"Client type: {type(client).__name__}")
print(f"Is DoubaoVisionClient: {isinstance(client, DoubaoVisionClient)}")
```

预期输出：
```
Client type: DoubaoVisionClient
Is DoubaoVisionClient: True
```

### 7. 验证完整流程

```bash
# 测试完整的视频处理流程
python main.py --url "https://www.bilibili.com/video/BV1xx411c7mD"
```

检查日志输出：
- [ ] 视频下载成功
- [ ] 音频转录成功
- [ ] 图像分析使用 DoubaoVisionClient
- [ ] 文本润色使用 DeepSeek
- [ ] 摘要生成成功

### 8. 检查日志文件

```bash
# 查看最新日志
cat logs/video_note_system.log | tail -100
```

应该看到：
```
[INFO] DoubaoVisionClient initialized: model=doubao-seed-1-6-vision-250815
[INFO] Using DoubaoVisionClient for bytedance:doubao-seed-1-6-vision-250815
[INFO] Created client for bytedance:doubao-seed-1-6-vision-250815
[INFO] LLMClient initialized: model=deepseek-chat
[INFO] Created client for deepseek:deepseek-chat
```

## 常见问题排查

### 问题 1: API Key 未读取

**症状**:
```
[Text Polish] Skipped (no text LLM API key)
```

**检查**:
1. `.env` 文件是否存在
2. API Key 名称是否正确 (DEEPSEEK_API_KEY, ARK_API_KEY)
3. `config/settings.py` 中 TEXT_LLM_PROVIDER 是否为 "deepseek"

**解决**:
```bash
# 检查环境变量
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DEEPSEEK:', os.getenv('DEEPSEEK_API_KEY')[:10] if os.getenv('DEEPSEEK_API_KEY') else 'NOT FOUND')"
```

### 问题 2: 豆包模型 ID 错误

**症状**:
```
[ERROR] Model not found: doubao-vision
```

**检查**:
1. `config/llm_config.yaml` 中模型 ID 是否为 `doubao-seed-1-6-vision-250815`
2. `config/settings.py` 中 VISION_MODEL_ID 是否正确

**解决**:
```bash
# 检查配置
python -c "from config.yaml_config_loader import get_provider_config; p = get_provider_config('bytedance'); print('Models:', p.models if p else 'NOT FOUND')"
```

### 问题 3: 客户端类型错误

**症状**:
```
[WARNING] Expected DoubaoVisionClient, got LLMClient
```

**检查**:
1. `config/llm_config.yaml` 中豆包是否有 `use_responses_api: true`
2. `utils/llm/unified_manager.py` 是否导入 DoubaoVisionClient
3. `utils/llm/unified_manager.py` 是否检查 use_responses_api

**解决**:
```bash
# 检查配置
python -c "from config.yaml_config_loader import get_provider_config; p = get_provider_config('bytedance'); print('use_responses_api:', p.use_responses_api if p else 'NOT FOUND')"
```

### 问题 4: 豆包 API 调用失败

**症状**:
```
[ERROR] Doubao image analysis failed: ...
```

**检查**:
1. ARK_API_KEY 是否正确
2. Base URL 是否为 `https://ark.cn-beijing.volces.com/api/v3`
3. 模型 ID 是否为 `doubao-seed-1-6-vision-250815`

**解决**:
```python
# 测试豆包连接
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv('ARK_API_KEY'),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# 测试 responses API
try:
    response = client.responses.create(
        model="doubao-seed-1-6-vision-250815",
        input=[{
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello"}]
        }]
    )
    print("✓ Doubao API working")
except Exception as e:
    print(f"❌ Doubao API failed: {e}")
```

## 验证完成标准

所有以下项目都应该通过：

- [x] 配置文件正确更新
- [x] 代码正确修改
- [ ] API Keys 已配置
- [ ] 测试脚本全部通过
- [ ] DeepSeek 文本调用成功
- [ ] 豆包视觉调用成功
- [ ] 客户端类型正确
- [ ] 完整流程运行成功

## 下一步行动

验证完成后，可以：

1. **运行完整流程**
   ```bash
   python main.py --url "https://www.bilibili.com/video/BV1xx411c7mD"
   ```

2. **测试批量处理**
   ```bash
   python main.py --batch urls.txt
   ```

3. **查看生成的笔记**
   ```bash
   cat output/notes/*.md
   ```

---

**最后更新**: 2026-01-28
**状态**: 等待用户验证
