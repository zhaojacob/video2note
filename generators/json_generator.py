"""
JSON generator for structured data export
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logger import get_logger
from utils.file_handler import ensure_dir

logger = get_logger(__name__)


class JsonGenerator:
    """Generate JSON output from structured data"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize JSON generator

        Args:
            output_dir: Output directory for JSON files
        """
        self.output_dir = output_dir or Path("output/notes")
        ensure_dir(self.output_dir)

    def generate(
        self,
        data: Dict[str, Any],
        filename: str = None,
        pretty: bool = True
    ) -> Path:
        """
        Generate JSON file

        Args:
            data: Structured note data
            filename: Output filename (without .json)
            pretty: Pretty-print JSON

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON file")

        if filename is None:
            filename = self._sanitize_filename(data['metadata']['title'])

        output_path = self.output_dir / f"{filename}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)

        logger.info(f"JSON file saved: {output_path}")

        return output_path

    def generate_compact(
        self,
        data: Dict[str, Any],
        filename: str = None
    ) -> Path:
        """
        Generate compact JSON (without images)

        Args:
            data: Structured note data
            filename: Output filename

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating compact JSON")

        # Remove image data
        compact_data = self._make_compact(data)

        return self.generate(compact_data, filename)

    def _make_compact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create compact version without image data"""
        import copy

        compact = copy.deepcopy(data)

        # Remove image paths from sections
        for section in compact.get('sections', []):
            for image in section.get('images', []):
                image.pop('path', None)
                image.pop('caption', None)

        return compact

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100] or "untitled"


def generate_json(
    data: Dict[str, Any],
    output_path: str,
    pretty: bool = True
) -> Path:
    """
    Convenience function to generate JSON file

    Args:
        data: Structured note data
        output_path: Output file path
        pretty: Pretty-print JSON

    Returns:
        Path to generated JSON file
    """
    generator = JsonGenerator()
    return generator.generate(data, Path(output_path).stem, pretty)
