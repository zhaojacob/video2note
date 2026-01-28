"""
Prompt templates for image analysis and content processing
"""

PROMPTS = {
    "auto": "Describe the scene, characters, and events within 30 words.",

    "formula": """Identify and explain the mathematical formula in the image:
1. Re-express the formula using LaTeX format.
2. Explain the mathematical meaning of the formula.
3. Define each symbol used.
4. Explain its role and significance in the context.

Ensure the LaTeX format is accurate and the explanation is clear and easy to understand.""",

    "code": """Identify the code in the image:
1. Identify the programming language (Python/Java/C++/JavaScript, etc.).
2. Extract the complete code, maintaining indentation and formatting.
3. Briefly explain the main function of the code.
4. If there is syntax highlighting or comments, please extract them as well.

Ensure the code is complete and the format is correct.""",

    "chart": """Analyze the chart in the image:
1. Identify the chart type (Bar/Line/Pie/Flowchart, etc.).
2. Describe the main content and data of the chart.
3. Extract key data points and trends.
4. Explain the information or conclusion conveyed by the chart.

Accurately extract data information and describe the chart content clearly in text.""",

    "text": """Extract the text content from the image:
1. Extract all visible text.
2. Maintain the logical structure and hierarchy of the text.
3. Identify titles, body text, notes, etc.
4. If it is a document, extract the complete content.

Ensure the text extraction is complete and accurate.""",

    "slide": """Analyze this PowerPoint slide:
1. Extract the title and all text content.
2. Identify the main theme of the slide.
3. Extract key points and list items.
4. Describe visual elements like charts and images.
5. Summarize the core information of the slide.

Organize the extracted information structurally.""",

    "general": """Describe this image:
1. Main objects and characters in the image.
2. Environment and background information.
3. Any visible text or signs.
4. The theme and content of the image.
5. Possible context information.

Describe the image content using natural language."""
}

TRANSCRIPT_POLISH_SYSTEM_PROMPT = """You are an expert content editor. Your task is to structure raw transcript segments into a polished, professional document.

[INPUT FORMAT]
A JSON list of dicts: [{"start": "HH:MM:SS", "text": "combined text block..."}, ...]

[TASK]
1. The input contains merged blocks of text with start timestamps.
2. Structure these blocks into logical SECTIONS with descriptive HEADERS.
3. Break down long text blocks into readable paragraphs.
4. PRESERVE the approximate start timestamp for each paragraph (use the timestamp of the source block).
5. Output strict JSON format.
6. PRESERVE THE ORIGINAL LANGUAGE of the input text. Do NOT translate.

[STRICT RULES - MUST FOLLOW]
1. **ADD PUNCTUATION**: Add proper punctuation marks to make the text readable. Use punctuation appropriate for the input language. This is CRITICAL.
2. **PRESERVE CONTENT**: Do NOT rewrite the meaning. Polish grammar and flow only. Do NOT omit any content.
3. **PRESERVE LANGUAGE**: Keep the same language as the input. Do NOT translate to another language.
4. **PRESERVE TIMESTAMPS**: Each paragraph MUST have a timestamp in "HH:MM:SS" format from the source block.
5. **PROPER PARAGRAPHS**: Break long text into logical paragraphs (3-5 sentences each). Each paragraph should be a complete thought.
6. **SECTION HEADERS**: Create descriptive section headers (3-8 words) in the SAME LANGUAGE as the input text.

[PUNCTUATION GUIDELINES]
- For English: Use periods (.), commas (,), question marks (?), exclamation marks (!)
- For Chinese: Use 。，？！
- For other languages: Use appropriate punctuation for that language

[OUTPUT SCHEMA]
{
  "sections": [
    {
      "title": "Section Title",
      "paragraphs": [
        {
          "timestamp": "HH:MM:SS",
          "content": "Polished paragraph with proper punctuation."
        }
      ]
    }
  ]
}"""

TRANSCRIPT_POLISH_USER_PROMPT = """Video Title: {video_title}
Context: {context}
Part {chunk_index} of {total_chunks}

Raw Segments (JSON):
{chunk_json}

IMPORTANT REQUIREMENTS:
1. ADD PUNCTUATION to every sentence (use punctuation appropriate for the input language)
2. PRESERVE the timestamp from each source block
3. Break into logical paragraphs (3-5 sentences each)
4. Create descriptive section headers IN THE SAME LANGUAGE as the input
5. DO NOT TRANSLATE - keep the original language

Return ONLY valid JSON in the specified schema. No markdown, no explanation."""


STRUCTURE_PROMPTS = {
    "summarize": """视频标题：{video_title}
视频时长：约{video_duration}分钟

请根据以下视频字幕生成高质量的中文摘要。

{transcript}

请按照以下结构生成摘要（使用括号标签）：

【标题】[视频的简洁标题]
【主题】[一句话概括视频的核心主题]

【关键词】[3-5个关键词，用顿号分隔。如果某些专有名词、技术术语或品牌名称没有合适的中文翻译，或保留原文更准确，请在中文后的括号中注明原文。例如："Transformer模型"或"深度学习（Deep Learning）"或"注意力机制（Self-Attention）"]

【内容概述】
[请生成约{summary_length}字的执行摘要，涵盖核心论点、背景和主要内容。重点回答"这意味着什么"——为什么这个内容重要。摘要长度应为视频时长的25倍左右。对于没有合适中文翻译的专有名词、技术术语或品牌名称，在首次出现时可以在括号中注明原文，例如："Transformer（Transformer模型架构）"或"GitHub（代码托管平台）"。]

【要点解析】
• 要点1
• 要点2
• 要点3
[按逻辑或时间顺序分解主要论点，使用项目符号列表，突出战略转变、具体建议或关键数据。如果有具体案例或数据，请在此处包含。]

【总结】
[对演讲者最终信息或内容 broader implication 的结论陈述。]

**格式要求**：
- 使用专业的中文表达
- 确保段落间逻辑流畅
- 避免使用"演讲者说"等泛泛之词，改用"他强调"、"她指出"、"内容包括"等具体表述
- 严格使用上述括号标签格式（如【标题】、【主题】等），不要使用markdown标记（不要使用**或*）
- 不需要生成英文版本
- 【内容概述】长度应约为视频时长的25倍（例如：10分钟视频→约250字，20分钟→约500字）
- **专有名词处理**：对于没有合适中文翻译的专有名词、技术术语、品牌名称等，应在中文后的括号中注明原文，例如：
  - "Transformer（Transformer模型架构）"
  - "GitHub（代码托管平台）"
  - "Docker（容器化平台）"
  - 或直接使用原文如"ChatGPT"、"Transformer"等
""",

    "segment": """Please divide the following video transcript into chapters by topic:

{transcript}

Requirements:
1. Each chapter must have a clear topic.
2. Chapters must be arranged chronologically.
3. Each chapter must include a time range.
4. Extract key points for each chapter.

Please return in JSON format:
{{
    "sections": [
        {{
            "title": "Chapter Title",
            "start_time": 0.0,
            "end_time": 120.0,
            "key_points": ["Point 1", "Point 2"]
        }}
    ]
}}""",

    "extract_key_points": """Please extract key points from the following text:

{text}

Requirements:
1. Extract 3-7 most important points.
2. Each point should be concise and clear (one sentence).
3. Sort by importance.
4. Return in a list format."""
}


IMAGE_CLASSIFICATION_PROMPT = """Please analyze the content type of this image and determine if it contains:
1. Mathematical formula (formula)
2. Code (code)
3. Chart (chart)
4. Large amount of text (text)
5. PowerPoint slide (slide)
6. General scene (general)

Please return in JSON format:
{{
    "primary_type": "Primary Type",
    "has_formula": true/false,
    "has_code": true/false,
    "has_chart": true/false,
    "has_text": true/false,
    "is_slide": true/false,
    "confidence": 0.95
}}"""
