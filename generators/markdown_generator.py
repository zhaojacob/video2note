"""
Markdown document generator - New format with improved structure
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.logger import get_logger
from utils.file_handler import ensure_dir

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generate Markdown documents from structured data with improved format"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize Markdown generator

        Args:
            output_dir: Output directory for documents
        """
        self.output_dir = output_dir or Path("output/notes")
        ensure_dir(self.output_dir)

    def generate(
        self,
        data: Dict[str, Any],
        filename: str = None,
        relative_images: bool = True
    ) -> Path:
        """
        Generate Markdown document with new structure

        Args:
            data: Structured note data
            filename: Output filename (without .md)
            relative_images: Use relative paths for images

        Returns:
            Path to generated document
        """
        logger.info("Generating Markdown document (new format)")

        lines = []

        # Add YAML metadata block
        lines.extend(self._generate_yaml_metadata(data))

        # Add title
        lines.append(f"# {data['metadata']['title']}\n")

        # Add metadata line (时间 | 来源 | 作者 | 链接)
        lines.extend(self._generate_metadata_line(data['metadata']))

        # Add version line
        lines.extend(self._generate_version_line(data['metadata']))

        lines.append("---\n")

        # Add AI-generated summary
        lines.extend(self._generate_summary_section(data.get('summary', '')))

        lines.append("---\n")

        # Add full transcript with images (new format)
        lines.extend(self._generate_transcript_section(
            data.get('full_transcript', []),
            data.get('sections', []),
            relative_images
        ))

        lines.append("---\n")

        # Add statistics
        lines.extend(self._generate_statistics(data['statistics']))

        # Join and save
        content = "\n".join(lines)

        if filename is None:
            filename = self._sanitize_filename(data['metadata']['title'])

        # Add timestamp suffix (YYYYMMDD_HHMMSS)
        timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{filename}_{timestamp_suffix}.md"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Markdown document saved: {output_path}")

        return output_path

    def _generate_yaml_metadata(self, data: Dict[str, Any]) -> List[str]:
        """Generate YAML metadata block"""
        metadata = data.get('metadata', {})

        lines = [
            "---",
            f"title: {metadata.get('title', 'Untitled')}",
            f"source: {metadata.get('source', 'unknown')}",
            f"duration: {metadata.get('duration', 0)}",
            f"created: {metadata.get('created_at', '')}",
            f"version: {metadata.get('version', 'v1.0')}",
            "---",
            "",
        ]

        return lines

    def _generate_metadata_line(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate single metadata line: 时间 | 来源 | 作者 | 链接"""
        parts = []
        
        # 时间 (creation date)
        created_at = metadata.get('created_at', '')
        if created_at:
            # Extract date part
            date_str = created_at[:10] if len(created_at) >= 10 else created_at
            parts.append(date_str)
        
        # 来源
        source = metadata.get('source', 'unknown')
        parts.append(source.capitalize())
        
        # 作者/UP主
        uploader = metadata.get('uploader', '')
        if uploader:
            parts.append(uploader)
        
        # 链接
        url = metadata.get('url', '')
        if url:
            parts.append(f"[原视频]({url})")
        
        metadata_line = " | ".join(parts)
        
        return [
            f"**{metadata_line}**",
            "",
        ]

    def _generate_version_line(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate version line"""
        version = metadata.get('version', 'v1.0')
        created_at = metadata.get('created_at', datetime.now().isoformat())
        
        return [
            f"*生成版本: {version} - {created_at[:19].replace('T', ' ')}*",
            "",
        ]

    def _generate_summary_section(self, summary: str) -> List[str]:
        """Generate summary section"""
        lines = [
            "## 摘要",
            "",
        ]
        
        if summary:
            lines.append(summary)
        else:
            lines.append("*（摘要生成中或未配置 DeepSeek API）*")
        
        lines.append("")
        
        return lines

    def _generate_transcript_section(
        self,
        full_transcript: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        relative_images: bool
    ) -> List[str]:
        """
        Generate transcript section with images inserted at timestamps
        
        Uses full_transcript if available, otherwise falls back to sections
        """
        lines = [
            "## 正文",
            "",
        ]
        
        # Prefer new full_transcript format
        if full_transcript:
            lines.extend(self._render_full_transcript(full_transcript, relative_images))
        elif sections:
            # Fallback to old sections format
            lines.extend(self._render_sections_as_transcript(sections, relative_images))
        else:
            lines.append("*（无转录内容）*")
            lines.append("")
        
        return lines

    def _render_full_transcript(
        self,
        items: List[Dict[str, Any]],
        relative_images: bool
    ) -> List[str]:
        """Render full transcript with embedded images"""
        lines = []
        
        for item in items:
            if item["type"] == "text":
                timestamp = self._format_timestamp(item["timestamp"])
                content = item.get("content", "").strip()
                
                if content:
                    lines.append(f"**[{timestamp}]** {content}")
                    lines.append("")
                    
            elif item["type"] == "image":
                timestamp = self._format_timestamp(item["timestamp"])
                img_path = item.get("path", "")
                caption = item.get("caption", "")
                img_type = item.get("image_type", "general")
                
                if relative_images and img_path:
                    img_path = Path(img_path).name
                
                type_label = self._get_type_label(img_type)
                
                # Image markdown
                lines.append(f"![{timestamp}]({img_path})")
                
                # Caption in gray (using HTML for styling)
                if caption:
                    # Truncate long captions
                    if len(caption) > 150:
                        caption = caption[:150] + "..."
                    lines.append(f'<span style="color:gray">*{type_label}[{timestamp}] {caption}*</span>')
                else:
                    lines.append(f'<span style="color:gray">*{type_label}[{timestamp}]*</span>')
                
                lines.append("")
        
        return lines

    def _render_sections_as_transcript(
        self,
        sections: List[Dict[str, Any]],
        relative_images: bool
    ) -> List[str]:
        """Fallback: render old sections format as transcript"""
        lines = []
        
        for section in sections:
            timestamp = self._format_timestamp(section.get('start_time', 0))
            content = section.get('content', '').strip()
            
            # Add images first (at their timestamps)
            for image in section.get('images', []):
                img_timestamp = self._format_timestamp(image.get('timestamp', 0))
                img_path = image.get('path', '')
                caption = image.get('caption', '')
                img_type = image.get('type', 'general')
                
                if relative_images and img_path:
                    img_path = Path(img_path).name
                
                type_label = self._get_type_label(img_type)
                
                lines.append(f"![{img_timestamp}]({img_path})")
                if caption:
                    lines.append(f'<span style="color:gray">*{type_label}[{img_timestamp}] {caption[:150]}*</span>')
                lines.append("")
            
            # Add text content
            if content:
                lines.append(f"**[{timestamp}]** {content}")
                lines.append("")
        
        return lines

    def _generate_statistics(self, statistics: Dict[str, Any]) -> List[str]:
        """Generate statistics section"""
        lines = [
            "## 统计信息",
            "",
            f"- **视频时长**: {self._format_duration(statistics.get('total_duration', 0))}",
            f"- **转录片段**: {statistics.get('total_segments', 0)}",
            f"- **截取帧数**: {statistics.get('total_frames', 0)}",
            f"- **成功分析**: {statistics.get('successful_analyses', 0)}",
            "",
        ]

        return lines

    def _slugify(self, text: str) -> str:
        """Convert text to URL slug"""
        import re
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100] or "untitled"

    def _format_duration(self, seconds: float) -> str:
        """Format duration"""
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
        """Format timestamp"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_type_label(self, img_type: str) -> str:
        """Get type label"""
        labels = {
            "formula": "【公式】",
            "code": "【代码】",
            "chart": "【图表】",
            "text": "【文字】",
            "general": "",
        }
        return labels.get(img_type, "")


def generate_markdown(
    data: Dict[str, Any],
    output_path: str
) -> Path:
    """
    Convenience function to generate Markdown document

    Args:
        data: Structured note data
        output_path: Output file path

    Returns:
        Path to generated document
    """
    generator = MarkdownGenerator()
    return generator.generate(data, Path(output_path).stem)
