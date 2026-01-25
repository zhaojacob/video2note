"""
Structurer for organizing content into final note format

Pipeline flow:
1. Receive raw transcript from transcription step
2. Call TextPolisher to polish transcript (with chapter organization)
3. Call SummaryGenerator to generate summary
4. Organize into final note structure
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class Structurer:
    """
    Structure raw data into organized note format
    
    Responsible for:
    - Text polishing (via TextPolisher)
    - Summary generation (via SummaryGenerator)
    - Content organization
    """

    def __init__(self):
        """Initialize structurer"""
        self.summary_generator = None
        self.translator = None
        self.text_polisher = None

    def _get_summary_generator(self):
        """Lazy-load summary generator"""
        if self.summary_generator is None:
            from utils.summary_generator import SummaryGenerator
            self.summary_generator = SummaryGenerator()
        return self.summary_generator

    def _get_translator(self):
        """Lazy-load translator"""
        if self.translator is None:
            from utils.translator import Translator
            self.translator = Translator()
        return self.translator

    def _get_text_polisher(self):
        """Lazy-load text polisher"""
        if self.text_polisher is None:
            from utils.text_polisher import TextPolisher
            self.text_polisher = TextPolisher()
        return self.text_polisher

    def structure(
        self,
        video_info: Dict[str, Any],
        transcript: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]],
        summary: str = None,
        keywords: List[str] = None,
        generate_ai_summary: bool = True,
        translate_to: str = None,
        duration_minutes: float = 0,
        enable_polish: bool = True
    ) -> Dict[str, Any]:
        """
        Structure all data into final note format
        
        Pipeline: raw_transcript -> polish -> summary -> organize

        Args:
            video_info: Video metadata
            transcript: Transcript segments (raw from Whisper)
            frame_analyses: Frame analysis results
            summary: Video summary (if None and generate_ai_summary=True, will use DeepSeek)
            keywords: Keywords/tags
            generate_ai_summary: Whether to generate AI summary using DeepSeek
            translate_to: Target language for translation (None = no translation)
            duration_minutes: Video duration in minutes (for polish context)
            enable_polish: Whether to enable text polishing

        Returns:
            Structured note data
        """
        from analysis.content_extractor import ContentProcessor

        logger.info("Structuring data into final format")

        processor = ContentProcessor()

        # Process transcript
        content = processor.process_with_frames(transcript, frame_analyses)

        # Get raw transcript text
        raw_transcript_text = self._get_full_transcript_text(transcript)
        
        # Initialize polish results
        polished_text = ""
        chapters = []
        
        # Step 1: Polish transcript (if enabled)
        if enable_polish and raw_transcript_text:
            logger.info("Polishing transcript with DeepSeek...")
            print("\n[Text Polish] Polishing transcript with DeepSeek...")
            try:
                polisher = self._get_text_polisher()
                if polisher.is_available():
                    polished_text = polisher.polish(
                        raw_transcript_text,
                        video_title=video_info.get("title", ""),
                        duration_minutes=duration_minutes
                    )
                    if polished_text:
                        chapters = polisher.extract_chapters(polished_text)
                        print(f"[Text Polish] Complete ({len(polished_text)} chars, {len(chapters)} chapters)")
                    else:
                        print("[Text Polish] No output, using raw transcript")
                        polished_text = raw_transcript_text
                else:
                    print("[Text Polish] Skipped (no DeepSeek API key)")
                    polished_text = raw_transcript_text
            except Exception as e:
                logger.error(f"Failed to polish transcript: {e}")
                print(f"[Text Polish] Failed: {e}")
                polished_text = raw_transcript_text
        else:
            polished_text = raw_transcript_text
        
        # Use polished text for summary generation
        full_transcript_text = polished_text if polished_text else raw_transcript_text
        
        # Step 2: Generate AI summary
        if summary is None and generate_ai_summary and full_transcript_text:
            logger.info("Generating AI summary with DeepSeek Reasoner...")
            print("\n[AI Summary] Generating summary with DeepSeek Reasoner...")
            try:
                summary_gen = self._get_summary_generator()
                if summary_gen.is_available():
                    summary = summary_gen.generate_summary(
                        full_transcript_text,
                        video_info.get("title", "")
                    )
                    if summary:
                        print(f"[AI Summary] Generated ({len(summary)} chars)")
                    else:
                        print("[AI Summary] Empty response")
                else:
                    print("[AI Summary] Skipped (no DeepSeek API key)")
            except Exception as e:
                logger.error(f"Failed to generate AI summary: {e}")
                print(f"[AI Summary] Failed: {e}")
                summary = ""

        # Translation handling
        title_translated = ""
        summary_translated = ""
        
        if translate_to:
            print(f"\n[Translation] Translating content to {translate_to}...")
            try:
                translator = self._get_translator()
                if translator.is_available():
                    # Translate title
                    title_translated = translator.translate_title(
                        video_info.get("title", ""),
                        translate_to
                    )
                    print(f"[Translation] Title translated")
                    
                    # Translate summary
                    if summary:
                        summary_translated = translator.translate_summary(summary, translate_to)
                        print(f"[Translation] Summary translated")
                    
                    # Translate transcript segments
                    if transcript:
                        transcript = translator.translate_transcript_segments(
                            transcript, translate_to
                        )
                        print(f"[Translation] Transcript translated ({len(transcript)} segments)")
                else:
                    print("[Translation] Skipped (no DeepSeek API key)")
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                print(f"[Translation] Failed: {e}")

        # Build structured data
        structured = {
            "metadata": {
                "title": video_info.get("title", "Untitled"),
                "title_translated": title_translated,
                "source": video_info.get("platform", "unknown"),
                "url": video_info.get("url", ""),
                "duration": video_info.get("duration", 0),
                "created_at": datetime.now().isoformat(),
                "version": "v1.0",
                "thumbnail": video_info.get("thumbnail", ""),
                "uploader": video_info.get("uploader", ""),
                "translate_to": translate_to,
            },
            "summary": summary or "",
            "summary_translated": summary_translated,
            "keywords": keywords or content.get("topics", []),
            # Polished transcript text (with punctuation, paragraphs, simplified Chinese)
            "polished_text": polished_text or "",
            # Chapters from TextPolisher (with titles)
            "chapters": chapters or [],
            # New structure: full transcript with timestamps and images
            "full_transcript": self._create_full_transcript_with_images(
                transcript,
                frame_analyses
            ),
            # Keep sections for backward compatibility
            "sections": self._create_sections(
                content["segments"],
                frame_analyses
            ),
            "timestamp_mapping": self._create_timestamp_mapping(transcript),
            "statistics": {
                "total_segments": len(transcript),
                "total_frames": len(frame_analyses),
                "total_duration": content["total_duration"],
                "successful_analyses": sum(
                    1 for f in frame_analyses if f.get("success")
                ),
                "translated": translate_to is not None,
                "chapter_count": len(chapters) if chapters else 0,
            },
        }

        logger.info(f"Structured {len(structured['sections'])} sections")

        return structured

    def _get_full_transcript_text(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Get full transcript as plain text
        
        Args:
            transcript: List of transcript segments
            
        Returns:
            Full transcript text
        """
        if not transcript:
            return ""
        
        texts = []
        for seg in transcript:
            text = seg.get("text", "").strip()
            if text:
                texts.append(text)
        
        return " ".join(texts)

    def _create_full_transcript_with_images(
        self,
        transcript: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create full transcript with images inserted at appropriate timestamps
        
        Args:
            transcript: Transcript segments
            frame_analyses: Frame analysis results
            
        Returns:
            List of content items (text and images) sorted by timestamp
        """
        content_items = []
        
        # Add transcript segments
        for seg in transcript:
            content_items.append({
                "type": "text",
                "timestamp": seg.get("start", 0),
                "end_time": seg.get("end", 0),
                "content": seg.get("text", "").strip(),
                "content_translated": seg.get("text_translated", "").strip() if seg.get("text_translated") else ""
            })
        
        # Add images at their timestamps
        for frame in frame_analyses:
            if frame.get("success"):
                content_items.append({
                    "type": "image",
                    "timestamp": frame.get("timestamp", 0),
                    "path": frame.get("frame_path", ""),
                    "caption": frame.get("description", "")[:200] if frame.get("description") else "",
                    "image_type": self._classify_frame_type(frame)
                })
        
        # Sort by timestamp
        content_items.sort(key=lambda x: x["timestamp"])
        
        # Group consecutive text items into paragraphs (merge if gap < 3 seconds)
        merged_items = []
        current_paragraph = None
        
        for item in content_items:
            if item["type"] == "text":
                if current_paragraph is None:
                    current_paragraph = {
                        "type": "text",
                        "timestamp": item["timestamp"],
                        "end_time": item["end_time"],
                        "content": item["content"],
                        "content_translated": item.get("content_translated", "")
                    }
                elif item["timestamp"] - current_paragraph["end_time"] < 3.0:
                    # Merge into current paragraph
                    current_paragraph["content"] += " " + item["content"]
                    if item.get("content_translated"):
                        current_paragraph["content_translated"] += " " + item.get("content_translated", "")
                    current_paragraph["end_time"] = item["end_time"]
                else:
                    # Start new paragraph
                    if current_paragraph["content"].strip():
                        merged_items.append(current_paragraph)
                    current_paragraph = {
                        "type": "text",
                        "timestamp": item["timestamp"],
                        "end_time": item["end_time"],
                        "content": item["content"],
                        "content_translated": item.get("content_translated", "")
                    }
            else:
                # Image - flush current paragraph first
                if current_paragraph and current_paragraph["content"].strip():
                    merged_items.append(current_paragraph)
                    current_paragraph = None
                merged_items.append(item)
        
        # Don't forget the last paragraph
        if current_paragraph and current_paragraph["content"].strip():
            merged_items.append(current_paragraph)
        
        return merged_items

    def _create_sections(
        self,
        segments: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create sections from segments

        Args:
            segments: Content segments
            frame_analyses: Frame analyses

        Returns:
            List of sections
        """
        sections = []

        for i, segment in enumerate(segments):
            # Extract key points
            key_points = self._extract_key_points(segment["text"])

            # Process frames in this segment
            section_frames = []
            for frame in segment.get("frames", []):
                if frame.get("success"):
                    section_frames.append({
                        "path": frame["frame_path"],
                        "timestamp": frame["timestamp"],
                        "caption": frame.get("description", "")[:200],
                        "type": self._classify_frame_type(frame),
                    })

            # Create section
            section = {
                "index": i,
                "title": self._generate_section_title(segment, i),
                "start_time": segment["start"],
                "end_time": segment["end"],
                "duration": segment["end"] - segment["start"],
                "content": segment["text"],
                "key_points": key_points,
                "images": section_frames,
            }

            sections.append(section)

        return sections

    def _generate_section_title(
        self,
        segment: Dict[str, Any],
        index: int
    ) -> str:
        """Generate section title from segment content"""
        # Get first sentence or use default
        text = segment.get("text", "")
        sentences = [s.strip() for s in text.split("。") if s.strip()]

        if sentences:
            title = sentences[0][:50]  # First 50 chars
            if len(title) == 50:
                title += "..."
        else:
            title = f"Section {index + 1}"

        return title

    def _extract_key_points(
        self,
        text: str,
        max_points: int = 3
    ) -> List[str]:
        """Extract key points from text"""
        # Simple extraction: get sentences with keywords
        import re

        keywords = ["重要", "关键", "需要", "应该", "必须"]
        sentences = [s.strip() for s in text.split("。") if s.strip()]

        points = []
        for sentence in sentences:
            if len(sentence) > 10 and len(sentence) < 100:
                if any(kw in sentence for kw in keywords):
                    points.append(sentence)

                if len(points) >= max_points:
                    break

        # If no key points found, use first sentences
        if not points and sentences:
            points = sentences[:max_points]

        return points

    def _classify_frame_type(self, frame: Dict[str, Any]) -> str:
        """Classify frame type based on analysis"""
        analysis_type = frame.get("analysis_type", "auto")

        if analysis_type in ["formula", "code", "chart"]:
            return analysis_type
        elif analysis_type == "text":
            return "text"
        else:
            return "general"

    def _create_timestamp_mapping(
        self,
        transcript: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Create timestamp mapping for quick lookup"""
        return {
            f"segment_{i}": seg["start"]
            for i, seg in enumerate(transcript)
        }

    def export_json(self, structured_data: Dict[str, Any]) -> str:
        """
        Export structured data to JSON string

        Args:
            structured_data: Structured note data

        Returns:
            JSON string
        """
        import json

        return json.dumps(structured_data, ensure_ascii=False, indent=2)

    def save_json(
        self,
        structured_data: Dict[str, Any],
        output_path: str
    ):
        """
        Save structured data to JSON file

        Args:
            structured_data: Structured note data
            output_path: Output file path
        """
        import json
        from pathlib import Path

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved JSON to: {output_path}")
