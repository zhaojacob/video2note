# 三大网络问题解决方案

## 📋 问题概览

1. **GitHub Push SSL/TLS Error** - Git推送到GitHub失败
2. **YouTube下载SSL Error** - 视频下载失败 `[SSL: UNEXPECTED_EOF_WHILE_READING]`
3. **ModelScope DeepSeek Rate Limit** - API配额超限

---

## 问题1：GitHub Push SSL/TLS Failed ❌

### 症状
```
fatal: unable to access 'https://github.com/...': schannel: failed to receive handshake, SSL/TLS connection failed
```

### ✅ 解决方案

**推荐：使用GitHub Desktop**
1. 下载 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的GitHub账号
3. 打开仓库 `F:\anaconda_learning\video_note_system`
4. 点击 "Push origin" 按钮

**或者：使用SSH**
```bash
# 1. 生成SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 复制公钥
cat ~/.ssh/id_ed25519.pub

# 3. 在GitHub添加SSH Key
# Settings > SSH and GPG keys > New SSH key
# 粘贴公钥

# 4. 切换远程URL
cd F:\anaconda_learning\video_note_system
git remote set-url origin git@github.com:zhaojacob/video2note.git

# 5. 推送
git push
```

---

## 问题2：YouTube下载SSL Error ❌

### 症状
```
[download] Got error: [SSL: UNEXPECTED_EOF_WHILE_READING]
EOF occurred in violation of protocol (_ssl.c:1016)
HTTP Error 403: Forbidden
```

### 原因分析
- ✗ **网络防火墙**：企业网络/学校网络拦截HTTPS
- ✗ **代理配置错误**：代理设置不正确
- ✗ **YouTube封禁**：IP被临时限制
- ✗ **地区限制**：视频在当前地区不可用

### ✅ 解决方案（按推荐顺序）

#### 方案1：配置HTTP/SOCKS5代理（最有效）

**步骤1：确认你的代理正在运行**
- 常见代理端口：`7890`, `1080`, `10808`, `7891`
- 例如：Clash默认端口 `7890`

**步骤2：修改 `config/settings.py`**
```python
VIDEO_CONFIG = {
    # HTTP代理
    "proxy": "http://127.0.0.1:7890",

    # 或SOCKS5代理
    # "proxy": "socks5://127.0.0.1:1080",
}
```

**步骤3：测试代理**
```bash
# 测试代理是否工作
curl -x http://127.0.0.1:7890 https://www.youtube.com
```

---

#### 方案2：使用YouTube Cookies（绕过限制）

**步骤1：安装浏览器插件导出Cookies**
- Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

**步骤2：导出YouTube Cookies**
1. 打开YouTube并登录
2. 点击插件图标
3. 点击 "Export" → "Download"
4. 保存为 `cookies.txt`

**步骤3：将cookies放到项目目录**
```bash
# 复制cookies.txt到项目根目录
cp ~/Downloads/cookies.txt F:/anaconda_learning/video_note_system/cookies.txt
```

**步骤4：修改 `config/settings.py`**
```python
VIDEO_CONFIG = {
    "cookie_file": "F:/anaconda_learning/video_note_system/cookies.txt",
}
```

---

#### 方案3：使用外部下载工具

**使用aria2c（多线程下载）**

修改 `core/video_downloader.py` 第82-88行：
```python
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
    'quiet': False,
    'no_warnings': False,
    'progress_hooks': [self._progress_hook],
    'external_downloader': 'aria2c',
    'external_downloader_args': ['-x', '16', '-k', '1M'],  # 16线程, 1M分片
}
```

安装aria2：
```bash
# Windows (使用scoop)
scoop install aria2

# 或下载：https://github.com/aria2/aria2/releases
```

---

#### 方案4：禁用SSL验证（不推荐，最后手段）

修改 `core/video_downloader.py` 第82-88行：
```python
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
    'quiet': False,
    'no_warnings': False,
    'progress_hooks': [self._progress_hook],
    'nocheckcertificate': True,  # ⚠️ 跳过SSL证书验证
    'socket_timeout': 120,  # 增加超时时间
}
```

---

### 📊 成功案例参考

从你的日志可以看到：
- ✅ **成功下载**：`https://www.youtube.com/watch?v=uhJJgc-0iTQ` (Building more effective AI agents)
- ❌ **失败**：其他3个视频

成功视频的特点：
- 视频长度：18分钟
- 下载速度：3.18 MB/s
- **没有使用任何代理**

**结论**：网络本身可以连接YouTube，但某些视频可能触发封禁或地区限制。

---

## 问题3：ModelScope DeepSeek Rate Limit ❌

### 症状
```
Error code: 429 - You have exceeded today's quota for model deepseek-ai/DeepSeek-V3.2,
please try again tomorrow, or consider using other models
```

### 原因
- ModelScope的免费DeepSeek模型有每日请求限制
- 当前已达到配额上限

### ✅ 解决方案

#### 方案1：切换到GLM-4（智谱AI）- 推荐

**修改 `config/settings.py`：**
```python
TEXT_LLM_CONFIG = {
    "provider": "glm",  # 从 "modelscope" 改为 "glm"
    "model": "glm-4-flash",  # 或 "glm-4-plus", "glm-4-air"
    "api_key": "your_glm_api_key",  # 从环境变量读取
    "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "temperature": 0.3,
    "max_tokens": 8192,
}
```

**获取GLM API Key：**
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录
3. 获取API Key
4. 设置环境变量：
```bash
# Windows PowerShell
$env:GLM_API_KEY = "your_api_key_here"

# 或在 .env 文件中添加
echo GLM_API_KEY=your_api_key_here >> .env
```

**GLM模型优势：**
- ✅ 每日免费额度更高
- ✅ 响应速度快
- ✅ 中文支持优秀
- ✅ 支持长文本（glm-4-long最高128k tokens）

---

#### 方案2：使用DeepSeek官方API

**修改 `config/settings.py`：**
```python
TEXT_LLM_CONFIG = {
    "provider": "deepseek",
    "api_key": os.getenv("DEEPSEEK_API_KEY"),
    "base_url": "https://api.deepseek.com/v1/chat/completions",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 8192,
}
```

**获取DeepSeek API Key：**
1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册账号
3. 获取API Key
4. 设置环境变量：
```bash
echo DEEPSEEK_API_KEY=your_api_key_here >> .env
```

**DeepSeek定价：**
- 🆓 免费额度：500万 tokens/天
- 💰 超出后：¥1/百万tokens（非常便宜）

---

#### 方案3：等待配额重置

ModelScope免费配额通常在**UTC 00:00**（北京时间08:00）重置。

等待到第二天早上再运行。

---

#### 方案4：降低API调用频率

修改 `analysis/structurer.py` 中的文本polish逻辑：
```python
# 增加每个chunk的大小，减少API调用次数
CHUNK_SIZE = 6000  # 从4500增加到6000
MAX_CHUNKS = 3     # 从5减少到3
```

---

### 📊 API对比

| Provider | Model | 免费额度 | 价格 | 中文支持 | 长文本 |
|----------|-------|---------|------|---------|--------|
| **GLM** | glm-4-flash | 高 | ¥0.1/万tokens | ⭐⭐⭐⭐⭐ | 128k |
| **DeepSeek官方** | deepseek-chat | 500万/天 | ¥1/万tokens | ⭐⭐⭐⭐ | 32k |
| **ModelScope** | DeepSeek-V3.2 | 低（已用尽）| 免费 | ⭐⭐⭐⭐ | 32k |

**推荐顺序**：
1. **GLM-4-Flash**（最快，免费额度高）
2. **DeepSeek官方API**（便宜，额度大）
3. 等待ModelScope配额重置

---

## 🚀 快速修复指南

### 1分钟修复YouTube下载
```bash
# 1. 修改config/settings.py，添加代理
echo 'VIDEO_CONFIG = {"proxy": "http://127.0.0.1:7890"}' >> config/settings.py

# 2. 测试下载
python main.py "https://www.youtube.com/watch?v=uhJJgc-0iTQ" --formats docx
```

### 1分钟修复DeepSeek限流
```bash
# 1. 获取GLM API Key并设置
export GLM_API_KEY="your_key"

# 2. 修改config/settings.py
# 将 TEXT_LLM_CONFIG 的 provider 改为 "glm"

# 3. 测试
python main.py "https://www.youtube.com/watch?v=uhJJgc-0iTQ"
```

### 1分钟修复GitHub Push
```bash
# 下载并使用GitHub Desktop
# 或使用SSH（需要先配置SSH密钥）
```

---

## 📝 总结

| 问题 | 推荐方案 | 优先级 |
|------|---------|--------|
| GitHub Push | GitHub Desktop / SSH | 🔴 高 |
| YouTube SSL | 配置代理 + Cookies | 🔴 高 |
| DeepSeek限流 | 切换GLM-4 | 🟡 中 |

**实施顺序**：
1. 先修复DeepSeek限流（5分钟）
2. 再修复YouTube下载（10分钟）
3. 最后处理GitHub Push（使用GitHub Desktop，2分钟）

---

## 🔍 调试技巧

### 测试网络连接
```bash
# 测试YouTube连接
curl -I https://www.youtube.com

# 测试代理
curl -x http://127.0.0.1:7890 https://www.google.com

# 测试API连接
curl https://open.bigmodel.cn/api/paas/v4/models
```

### 查看详细日志
```bash
# 启用详细日志
python main.py "video_url" --verbose
```

### 测试单个视频
```bash
# 先用短视频测试
python main.py "short_video_url" --formats json --skip-analysis
```

---

## 📞 需要帮助？

如果以上方案都无法解决问题：
1. 检查防火墙/杀毒软件设置
2. 尝试切换网络（手机热点）
3. 确认代理软件正常运行
4. 查看完整的错误日志
