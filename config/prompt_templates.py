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

[STRICT RULES]
- Do NOT rewrite the meaning. Polish grammar and flow only.
- Do NOT omit content.
- Headers should be descriptive (5-15 chars).
- Timestamps MUST be in "HH:MM:SS" format.

[OUTPUT SCHEMA]
{
  "sections": [
    {
      "title": "Section Title",
      "paragraphs": [
        {
          "timestamp": "HH:MM:SS",
          "content": "Polished paragraph text..."
        }
      ]
    }
  ]
}"""

TRANSCRIPT_POLISH_USER_PROMPT = """Video Title: {video_title}
Context: {context}
Part {chunk_index} of {total_chunks}

Raw Segments:
{chunk_json}

Please structure this content into sections and paragraphs with timestamps. Return JSON only."""


STRUCTURE_PROMPTS = {
    "summarize": """Video Title: {video_title}

Please generate a high-quality, structured summary based on the following video transcript.

{transcript}

Your summary should mirror the depth and structure of a professional briefing. Please provide:

1. **Title & Theme**: A concise title and a one-sentence theme statement.
2. **Keywords**: 3-5 relevant keywords.
3. **Executive Summary**: A comprehensive narrative (200-300 words) that captures the core thesis, context, and main arguments. Focus on the "So What?" – why this matters.
4. **Key Points & Strategic Insights**:
   - Break down the main arguments or events logically (or chronologically if appropriate).
   - Use bullet points for clarity.
   - Highlight any strategic shifts, specific proposals, or critical data mentioned.
5. **Q&A / Specific Highlights** (if applicable): Summarize key questions addressed or specific detailed examples given.
6. **Conclusion**: A concluding statement about the speaker's final message or the broader implication of the content.

**Style Guidelines**:
- Use professional, objective language.
- Ensure logical flow between paragraphs.
- Avoid generic phrases like "The speaker said"; instead, use "He argued," "She emphasized," "The presentation outlined."
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
