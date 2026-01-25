"""
Word document generator - New format with proper fonts
字体规范：
- 英文字体：Times New Roman
- 中文字体：宋体
- 字号：小四 (12pt)
- 颜色：黑色正文，灰色图片标注
"""
from pathlib import Path
from typing import Dict, Any, Optional, List

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn

from utils.logger import get_logger
from utils.file_handler import ensure_dir

logger = get_logger(__name__)

# Font constants
FONT_CHINESE = "宋体"
FONT_ENGLISH = "Times New Roman"
FONT_SIZE_NORMAL = Pt(12)  # 小四
FONT_SIZE_TITLE = Pt(18)
FONT_SIZE_HEADING = Pt(14)
FONT_SIZE_CAPTION = Pt(10)
COLOR_BLACK = RGBColor(0, 0, 0)
COLOR_GRAY = RGBColor(128, 128, 128)


class DocxGenerator:
    """Generate Word documents from structured data with proper fonts"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize DOCX generator

        Args:
            output_dir: Output directory for documents
        """
        self.output_dir = output_dir or Path("output/notes")
        ensure_dir(self.output_dir)

    def generate(
        self,
        data: Dict[str, Any],
        filename: str = None
    ) -> Path:
        """
        Generate Word document with new structure

        Args:
            data: Structured note data
            filename: Output filename (without .docx)

        Returns:
            Path to generated document
        """
        logger.info("Generating Word document (new format)")

        # Create document
        doc = Document()

        # Set document properties
        self._setup_styles(doc)

        # Add title (with translation if available)
        self._add_title(
            doc, 
            data["metadata"]["title"],
            data["metadata"].get("title_translated", "")
        )

        # Add metadata line (时间 | 来源 | 作者 | 链接)
        self._add_metadata_line(doc, data["metadata"])

        # Add version line
        self._add_version_line(doc, data["metadata"])

        # Add summary section (with translation if available)
        self._add_summary(
            doc, 
            data.get("summary", ""),
            data.get("summary_translated", "")
        )

        # Add transcript section with images
        # Use chapters if available (with titles), otherwise polished_text or raw transcript
        self._add_transcript_section(
            doc,
            data.get("full_transcript", []),
            data.get("sections", []),
            data.get("polished_text", ""),
            data.get("chapters", [])
        )

        # Add statistics
        self._add_statistics(doc, data["statistics"])

        # Save document
        if filename is None:
            filename = self._sanitize_filename(data["metadata"]["title"])

        # Add timestamp suffix (YYYYMMDD_HHMMSS)
        from datetime import datetime
        timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{filename}_{timestamp_suffix}.docx"
        doc.save(str(output_path))

        logger.info(f"Word document saved: {output_path}")

        return output_path

    def _setup_styles(self, doc: Document):
        """Setup document styles with proper fonts"""
        # Default font - 小四 (12pt)
        style = doc.styles['Normal']
        font = style.font
        font.name = FONT_ENGLISH  # Times New Roman for English
        font.size = FONT_SIZE_NORMAL
        font.color.rgb = COLOR_BLACK

        # Set Chinese font - 宋体
        style.element.rPr.rFonts.set(
            qn('w:eastAsia'),
            FONT_CHINESE
        )

    def _set_run_font(self, run, size=None, color=None, bold=False, italic=False):
        """Helper to set run font properties"""
        run.font.name = FONT_ENGLISH
        run.font.size = size or FONT_SIZE_NORMAL
        run.font.color.rgb = color or COLOR_BLACK
        run.font.bold = bold
        run.font.italic = italic
        # Set Chinese font
        run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_CHINESE)

    def _add_title(self, doc: Document, title: str, title_translated: str = ""):
        """Add document title with optional translation"""
        heading = doc.add_heading(title, level=1)
        heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        for run in heading.runs:
            self._set_run_font(run, size=FONT_SIZE_TITLE, bold=True)
        
        # Add translated title if available
        if title_translated:
            p = doc.add_paragraph()
            run = p.add_run(title_translated)
            self._set_run_font(run, size=Pt(14), color=COLOR_GRAY, italic=True)
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    def _add_metadata_line(self, doc: Document, metadata: Dict[str, Any]):
        """Add single metadata line: 时间 | 来源 | 作者 | 链接"""
        p = doc.add_paragraph()
        
        parts = []
        
        # 时间
        created_at = metadata.get('created_at', '')
        if created_at:
            date_str = created_at[:10] if len(created_at) >= 10 else created_at
            parts.append(date_str)
        
        # 来源
        source = metadata.get('source', 'unknown')
        parts.append(source.capitalize())
        
        # 作者
        uploader = metadata.get('uploader', '')
        if uploader:
            parts.append(uploader)
        
        # 链接
        url = metadata.get('url', '')
        if url:
            parts.append(url)
        
        metadata_text = " | ".join(parts)
        run = p.add_run(metadata_text)
        self._set_run_font(run, size=FONT_SIZE_CAPTION, color=COLOR_GRAY)
        
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    def _add_version_line(self, doc: Document, metadata: Dict[str, Any]):
        """Add version line"""
        p = doc.add_paragraph()
        
        version = metadata.get('version', 'v1.0')
        created_at = metadata.get('created_at', '')
        if created_at:
            created_at = created_at[:19].replace('T', ' ')
        
        run = p.add_run(f"生成版本: {version} - {created_at}")
        self._set_run_font(run, size=FONT_SIZE_CAPTION, color=COLOR_GRAY, italic=True)
        
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        doc.add_paragraph()  # Empty line

    def _add_summary(self, doc: Document, summary: str, summary_translated: str = ""):
        """Add summary section with optional translation"""
        heading = doc.add_heading("摘要", level=2)
        for run in heading.runs:
            self._set_run_font(run, size=FONT_SIZE_HEADING, bold=True)
        
        if summary:
            p = doc.add_paragraph()
            run = p.add_run(summary)
            self._set_run_font(run)
            p.paragraph_format.line_spacing = 1.5
            
            # Add translated summary
            if summary_translated:
                p2 = doc.add_paragraph()
                run2 = p2.add_run(summary_translated)
                self._set_run_font(run2, color=COLOR_GRAY, italic=True)
                p2.paragraph_format.line_spacing = 1.5
        else:
            p = doc.add_paragraph()
            run = p.add_run("（摘要生成中或未配置 DeepSeek API）")
            self._set_run_font(run, color=COLOR_GRAY, italic=True)
        
        doc.add_paragraph()

    def _add_transcript_section(
        self,
        doc: Document,
        full_transcript: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        polished_text: str = "",
        chapters: List[Dict[str, Any]] = None
    ):
        """Add transcript section with images"""
        heading = doc.add_heading("正文", level=2)
        for run in heading.runs:
            self._set_run_font(run, size=FONT_SIZE_HEADING, bold=True)
        
        # Prefer chapters (with titles and structured content)
        if chapters:
            self._render_chapters(doc, chapters)
        # Fallback to polished text (with punctuation, paragraphs)
        elif polished_text:
            self._render_polished_text(doc, polished_text)
        # Fallback to full_transcript format
        elif full_transcript:
            self._render_full_transcript(doc, full_transcript)
        elif sections:
            # Fallback to old sections format
            self._render_sections_as_transcript(doc, sections)
        else:
            p = doc.add_paragraph()
            run = p.add_run("（无转录内容）")
            self._set_run_font(run, color=COLOR_GRAY, italic=True)

    def _render_chapters(self, doc: Document, chapters: List[Dict[str, Any]]):
        """Render chapters with titles and content"""
        from docx.shared import RGBColor
        
        for i, chapter in enumerate(chapters):
            title = chapter.get('title', f'章节 {i + 1}')
            content = chapter.get('content', '')
            
            # Add chapter title as heading level 3
            chapter_heading = doc.add_heading(title, level=3)
            for run in chapter_heading.runs:
                # Style: bold, slightly larger, dark blue color for emphasis
                run.font.name = FONT_ENGLISH
                run.font.size = Pt(14)  # 14pt for chapter titles
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
                run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_CHINESE)
            
            # Add chapter content
            if content:
                # Split content into paragraphs
                paragraphs = content.split('\n\n') if '\n\n' in content else content.split('\n')
                
                for para_text in paragraphs:
                    para_text = para_text.strip()
                    if not para_text:
                        continue
                    
                    p = doc.add_paragraph()
                    # First line indent for Chinese style
                    p.paragraph_format.first_line_indent = Inches(0.5)
                    p.paragraph_format.line_spacing = 1.5
                    
                    run = p.add_run(para_text)
                    self._set_run_font(run)
            
            # Add spacing between chapters
            doc.add_paragraph()

    def _render_polished_text(self, doc: Document, text: str):
        """Render polished transcript text with proper paragraphs"""
        # Check if text contains chapter markers (## Title)
        if '## ' in text:
            # Parse and render as chapters
            from utils.text_polisher import TextPolisher
            polisher = TextPolisher()
            chapters = polisher._parse_chapters(text)
            if chapters:
                self._render_chapters(doc, chapters)
                return
        
        # Split by double newlines (paragraphs) or single newlines
        paragraphs = text.split('\n\n') if '\n\n' in text else text.split('\n')
        
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue
            
            p = doc.add_paragraph()
            # First line indent for Chinese style
            p.paragraph_format.first_line_indent = Inches(0.5)
            p.paragraph_format.line_spacing = 1.5
            
            run = p.add_run(para_text)
            self._set_run_font(run)

    def _render_full_transcript(self, doc: Document, items: List[Dict[str, Any]]):
        """Render full transcript with embedded images and translations"""
        for item in items:
            if item["type"] == "text":
                timestamp = self._format_timestamp(item["timestamp"])
                content = item.get("content", "").strip()
                content_translated = item.get("content_translated", "").strip()
                
                if content:
                    p = doc.add_paragraph()
                    # Timestamp in bold
                    ts_run = p.add_run(f"[{timestamp}] ")
                    self._set_run_font(ts_run, bold=True)
                    # Content
                    content_run = p.add_run(content)
                    self._set_run_font(content_run)
                    p.paragraph_format.line_spacing = 1.5
                    
                    # Add translation if available
                    if content_translated:
                        p2 = doc.add_paragraph()
                        # Indent for translation
                        p2.paragraph_format.left_indent = Inches(0.3)
                        trans_run = p2.add_run(content_translated)
                        self._set_run_font(trans_run, color=COLOR_GRAY, italic=True)
                        p2.paragraph_format.line_spacing = 1.5
                    
            elif item["type"] == "image":
                self._add_transcript_image(doc, item)

    def _render_sections_as_transcript(self, doc: Document, sections: List[Dict[str, Any]]):
        """Fallback: render old sections format as transcript"""
        for section in sections:
            timestamp = self._format_timestamp(section.get('start_time', 0))
            content = section.get('content', '').strip()
            
            # Add images first
            for image in section.get('images', []):
                self._add_image(doc, image, section.get('start_time', 0))
            
            # Add text content
            if content:
                p = doc.add_paragraph()
                ts_run = p.add_run(f"[{timestamp}] ")
                self._set_run_font(ts_run, bold=True)
                content_run = p.add_run(content)
                self._set_run_font(content_run)
                p.paragraph_format.line_spacing = 1.5

    def _add_transcript_image(self, doc: Document, item: Dict[str, Any]):
        """Add image from transcript item"""
        try:
            img_path = Path(item.get("path", ""))
            if not img_path.exists():
                logger.warning(f"Image not found: {img_path}")
                return
            
            # Add image
            doc.add_picture(str(img_path), width=Inches(5))
            
            # Center the image
            last_para = doc.paragraphs[-1]
            last_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Add caption in gray
            timestamp = self._format_timestamp(item.get("timestamp", 0))
            caption = item.get("caption", "")
            img_type = item.get("image_type", "general")
            type_label = self._get_type_label(img_type)
            
            caption_text = f"{type_label}[{timestamp}]"
            if caption:
                caption_text += f" {caption[:150]}"
            
            p = doc.add_paragraph()
            run = p.add_run(caption_text)
            self._set_run_font(run, size=FONT_SIZE_CAPTION, color=COLOR_GRAY, italic=True)
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            doc.add_paragraph()  # Space after image
            
        except Exception as e:
            logger.error(f"Failed to add image: {e}")

    def _add_section(self, doc: Document, section: Dict[str, Any]):
        """Add a content section (legacy support)"""
        # Section heading with timestamp
        heading_text = f"{section['title']} [{self._format_timestamp(section['start_time'])}]"
        doc.add_heading(heading_text, level=3)

        # Add images
        for image in section.get("images", []):
            self._add_image(doc, image, section['start_time'])

        # Add content
        if section.get("content"):
            p = doc.add_paragraph(section["content"])
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.first_line_indent = Inches(0.3)

        # Add key points
        if section.get("key_points"):
            doc.add_paragraph("要点:")
            for point in section["key_points"]:
                p = doc.add_paragraph(point, style='List Bullet')

        doc.add_paragraph()

    def _add_image(self, doc: Document, image: Dict[str, Any], section_time: float):
        """Add image with caption"""
        try:
            img_path = Path(image["path"])
            if not img_path.exists():
                logger.warning(f"Image not found: {img_path}")
                return

            # Add image
            doc.add_picture(str(img_path), width=Inches(5))

            # Add caption with type label
            img_type = image.get("type", "general")
            type_label = self._get_type_label(img_type)

            caption_text = f"{type_label} {self._format_timestamp(image['timestamp'])}"
            if image.get("caption"):
                caption_text += f" - {image['caption'][:100]}"

            p = doc.paragraphs[-1]
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            caption = p.add_run(f"\n{caption_text}")
            self._set_run_font(caption, size=FONT_SIZE_CAPTION, color=COLOR_GRAY, italic=True)

            doc.add_paragraph()

        except Exception as e:
            logger.error(f"Failed to add image: {e}")

    def _add_statistics(self, doc: Document, statistics: Dict[str, Any]):
        """Add statistics section"""
        heading = doc.add_heading("统计信息", level=2)
        for run in heading.runs:
            self._set_run_font(run, size=FONT_SIZE_HEADING, bold=True)

        stats = [
            f"视频时长: {self._format_duration(statistics.get('total_duration', 0))}",
            f"转录片段: {statistics.get('total_segments', 0)}",
            f"截取帧数: {statistics.get('total_frames', 0)}",
            f"成功分析: {statistics.get('successful_analyses', 0)}",
        ]

        for stat in stats:
            p = doc.add_paragraph(stat, style='List Bullet')
            for run in p.runs:
                self._set_run_font(run)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for Windows"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100] or "untitled"

    def _format_duration(self, seconds: float) -> str:
        """Format duration as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_type_label(self, img_type: str) -> str:
        """Get type label for image"""
        labels = {
            "formula": "【公式】",
            "code": "【代码】",
            "chart": "【图表】",
            "text": "【文字】",
            "general": "",
        }
        return labels.get(img_type, "")


def generate_docx(data: Dict[str, Any], output_path: str) -> Path:
    """
    Convenience function to generate Word document

    Args:
        data: Structured note data
        output_path: Output file path

    Returns:
        Path to generated document
    """
    generator = DocxGenerator()
    return generator.generate(data, Path(output_path).stem)
