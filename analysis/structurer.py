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
        
        # Initialize polish results
        polished_sections = []
        polished_text = raw_transcript_text
        
        # Step 1: Polish transcript (JSON structured)
        if enable_polish and transcript:
            logger.info("Polishing transcript with text LLM (Structured JSON)...")
            print("\n[Text Polish] Polishing transcript with text LLM (Structured JSON)...")
            try:
                polisher = self._get_text_polisher()
                if polisher.is_available():
                    # Use new JSON polishing method
                    polish_result = polisher.polish_transcript_json(
                        transcript,
                        video_title=video_info.get("title", "")
                    )
                    
                    polished_sections = polish_result.get("sections", [])
                    
                    if polished_sections:
                        # NEW: Align timestamps using fuzzy matching
                        # The LLM often fails to preserve accurate timestamps, so we align back to raw transcript
                        print("[Text Polish] Aligning timestamps using fuzzy matching...")
                        self._align_timestamps_fuzzy(polished_sections, transcript)
                        
                        # Reconstruct polished text for summary generation
                        all_paragraphs = []
                        for section in polished_sections:
                            for para in section.get("paragraphs", []):
                                all_paragraphs.append(para.get("content", ""))
                        polished_text = "\n\n".join(all_paragraphs)
                        
                        print(f"[Text Polish] Complete ({len(polished_sections)} sections)")
                        
                        # Interleave images into sections
                        self._interleave_images_into_sections(polished_sections, frame_analyses)
                    else:
                        print("[Text Polish] No structured output, using raw transcript")
                else:
                    print("[Text Polish] Skipped (no text LLM API key)")
            except Exception as e:
                logger.error(f"Failed to polish transcript: {e}")
                print(f"[Text Polish] Failed: {e}")
                import traceback
                traceback.print_exc()

        # Step 2: Generate AI summary
        if summary is None and generate_ai_summary and polished_text:
            logger.info("Generating AI summary with text LLM...")
            print("\n[AI Summary] Generating summary with text LLM...")
            try:
                summary_gen = self._get_summary_generator()
                if summary_gen.is_available():
                    # Calculate video duration in minutes
                    video_duration_seconds = video_info.get("duration", 0)
                    video_duration_minutes = video_duration_seconds / 60 if video_duration_seconds else 0

                    summary = summary_gen.generate_summary(
                        polished_text,
                        video_info.get("title", ""),
                        video_duration=video_duration_minutes
                    )
                    if summary:
                        print(f"[AI Summary] Generated ({len(summary)} chars)")
                    else:
                        print("[AI Summary] Empty response")
                else:
                    print("[AI Summary] Skipped (no text LLM API key)")
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
            # Polished transcript text (reconstructed)
            "polished_text": polished_text or "",
            # Structured sections (the source of truth)
            "structured_sections": polished_sections,
            # Legacy fields for backward compatibility
            "chapters": [{"title": s.get("title", ""), "content": "\n".join([p.get("content", "") for p in s.get("paragraphs", [])])} for s in polished_sections] if polished_sections else [],
            "heading_markers": [],
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

    def _align_timestamps_fuzzy(
        self,
        polished_sections: List[Dict[str, Any]],
        raw_transcript: List[Dict[str, Any]]
    ):
        """
        Align polished paragraphs with raw transcript using fuzzy text matching.
        Updates timestamps in polished_sections in-place.
        """
        import difflib
        
        # Helper to normalize text for matching
        def normalize(text):
            return "".join(c.lower() for c in text if c.isalnum())

        if not raw_transcript or not polished_sections:
            logger.warning("Cannot align timestamps: empty transcript or sections")
            return

        # Prepare raw transcript index
        # We'll search through raw segments sequentially
        current_raw_idx = 0
        total_raw = len(raw_transcript)
        last_timestamp = 0.0  # Track last successful timestamp for fallback
        
        matched_count = 0
        total_paras = 0
        
        for section in polished_sections:
            for para in section.get("paragraphs", []):
                total_paras += 1
                para_text = para.get("content", "")
                if not para_text:
                    # Set default timestamp if no content
                    if not para.get("timestamp"):
                        para["timestamp"] = "00:00:00"
                        para["timestamp_seconds"] = 0.0
                    continue
                    
                # Take first ~100 chars of normalized paragraph text as query
                query = normalize(para_text[:100])
                if len(query) < 10:
                    # Very short text, use last timestamp
                    if not para.get("timestamp"):
                        hours = int(last_timestamp // 3600)
                        minutes = int((last_timestamp % 3600) // 60)
                        secs = int(last_timestamp % 60)
                        para["timestamp"] = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                        para["timestamp_seconds"] = last_timestamp
                    continue
                    
                best_ratio = 0.0
                best_idx = current_raw_idx
                
                # Search window: current position + next 50 segments (optimization)
                search_end = min(current_raw_idx + 50, total_raw)
                
                # First pass: local search
                for i in range(current_raw_idx, search_end):
                    raw_text = normalize(raw_transcript[i].get("text", ""))
                    if not raw_text:
                        continue
                        
                    # Check similarity
                    ratio = difflib.SequenceMatcher(None, query, raw_text).ratio()
                    
                    # Also check if query is a substring of raw (or vice versa)
                    if query in raw_text or raw_text in query:
                        ratio = max(ratio, 0.8) # Boost substring matches
                    
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_idx = i
                
                # If match is good enough, update timestamp and advance cursor
                if best_ratio > 0.4: # Threshold for fuzzy match
                    current_raw_idx = best_idx
                    matched_count += 1
                    
                    # Update timestamp
                    start_time = raw_transcript[best_idx].get("start", 0)
                    last_timestamp = start_time  # Update last successful timestamp
                    
                    # Format as HH:MM:SS
                    hours = int(start_time // 3600)
                    minutes = int((start_time % 3600) // 60)
                    secs = int(start_time % 60)
                    para["timestamp"] = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                    # Also store seconds for image interleaving
                    para["timestamp_seconds"] = start_time
                else:
                    # If no good match found, use last timestamp as fallback
                    if not para.get("timestamp"):
                        hours = int(last_timestamp // 3600)
                        minutes = int((last_timestamp % 3600) // 60)
                        secs = int(last_timestamp % 60)
                        para["timestamp"] = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                        para["timestamp_seconds"] = last_timestamp
        
        logger.info(f"Timestamp alignment: {matched_count}/{total_paras} paragraphs matched")
        print(f"[Text Polish] Timestamp alignment: {matched_count}/{total_paras} paragraphs matched")

    def _interleave_images_into_sections(
        self,
        sections: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]]
    ):
        """
        Interleave images into structured sections based on timestamps
        """
        # Sort frames by timestamp
        sorted_frames = sorted(
            [f for f in frame_analyses if f.get("success")], 
            key=lambda x: x.get("timestamp", 0)
        )
        
        if not sorted_frames:
            logger.info("No frames to interleave")
            return
            
        logger.info(f"Interleaving {len(sorted_frames)} frames into sections")
        
        # Flatten paragraphs for easy iteration
        all_paragraphs = []
        for section in sections:
            for para in section.get("paragraphs", []):
                # Parse timestamp to seconds (use timestamp_seconds if already set)
                if "timestamp_seconds" not in para:
                    ts_str = para.get("timestamp", "00:00:00")
                    parts = ts_str.split(":")
                    seconds = 0
                    try:
                        if len(parts) == 3:
                            seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
                        elif len(parts) == 2:
                            seconds = int(parts[0])*60 + int(parts[1])
                    except ValueError:
                        seconds = 0
                    para["timestamp_seconds"] = seconds
                
                all_paragraphs.append(para)
        
        if not all_paragraphs:
            logger.warning("No paragraphs to interleave images into")
            return
                
        # Distribute images
        current_frame_idx = 0
        images_distributed = 0
        
        for i, para in enumerate(all_paragraphs):
            para_start = para.get("timestamp_seconds", 0)
            # Next paragraph start or end of video (infinity)
            para_end = all_paragraphs[i+1].get("timestamp_seconds", float('inf')) if i < len(all_paragraphs)-1 else float('inf')
            
            para["images"] = []
            
            while current_frame_idx < len(sorted_frames):
                frame = sorted_frames[current_frame_idx]
                frame_ts = frame.get("timestamp", 0)
                
                if frame_ts < para_start:
                    # Frame is before this paragraph (should have been attached to previous, or it's very early)
                    # Attach to this one if it's the first
                    if i == 0:
                        self._add_frame_to_para(para, frame)
                        images_distributed += 1
                    current_frame_idx += 1
                elif frame_ts >= para_start and frame_ts < para_end:
                    # Frame belongs to this paragraph
                    self._add_frame_to_para(para, frame)
                    images_distributed += 1
                    current_frame_idx += 1
                else:
                    # Frame is after this paragraph
                    break
        
        logger.info(f"Distributed {images_distributed} images into {len(all_paragraphs)} paragraphs")
        print(f"[Text Polish] Distributed {images_distributed} images into {len(all_paragraphs)} paragraphs")
                    
    def _add_frame_to_para(self, para, frame):
        """Add frame to paragraph images list"""
        para["images"].append({
            "path": str(frame.get("frame_path", "")),
            "timestamp": frame.get("timestamp", 0),
            "caption": frame.get("description", "")[:200] if frame.get("description") else "",
            "image_type": self._classify_frame_type(frame)
        })

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
                "timestamp_formatted": seg.get("timestamp_formatted", ""),
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
                    "path": str(frame.get("frame_path", "")),
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
                        "path": str(frame["frame_path"]),
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
