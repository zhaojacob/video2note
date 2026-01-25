"""
Content extraction and understanding
"""
from typing import Dict, Any, List, Optional
import re

from utils.logger import get_logger

logger = get_logger(__name__)


class ContentExtractor:
    """
    Extract and structure content from transcripts and frame analyses
    """

    def __init__(self):
        """Initialize content extractor"""
        pass

    def extract_key_topics(
        self,
        transcript: List[Dict[str, Any]],
        num_topics: int = 5
    ) -> List[str]:
        """
        Extract key topics from transcript

        Args:
            transcript: List of transcript segments
            num_topics: Number of topics to extract

        Returns:
            List of topic keywords
        """
        # Combine all transcript text
        full_text = " ".join([s["text"] for s in transcript])

        # Simple keyword extraction (can be improved with NLP)
        # Remove common words
        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这",
            "the", "is", "a", "an", "and", "or", "but", "in", "on", "at",
        }

        # Tokenize (simple for Chinese)
        words = re.findall(r'[\w]+', full_text)

        # Count word frequency
        word_freq = {}
        for word in words:
            if len(word) >= 2 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        topics = [word for word, freq in sorted_words[:num_topics]]

        logger.info(f"Extracted {len(topics)} key topics")

        return topics

    def segment_by_topic(
        self,
        transcript: List[Dict[str, Any]],
        max_segment_length: float = 300.0
    ) -> List[Dict[str, Any]]:
        """
        Segment transcript by topic change

        Args:
            transcript: List of transcript segments
            max_segment_length: Maximum segment length in seconds

        Returns:
            List of topic segments
        """
        segments = []
        current_segment = []
        current_start = transcript[0]["start"] if transcript else 0

        for segment in transcript:
            # Check if segment would exceed max length
            segment_end = segment["end"]
            segment_length = segment_end - current_start

            if segment_length > max_segment_length and current_segment:
                # Finish current segment
                segments.append({
                    "start": current_start,
                    "end": current_segment[-1]["end"],
                    "segments": current_segment.copy(),
                    "text": " ".join([s["text"] for s in current_segment]),
                })

                # Start new segment
                current_segment = [segment]
                current_start = segment["start"]
            else:
                current_segment.append(segment)

        # Add last segment
        if current_segment:
            segments.append({
                "start": current_start,
                "end": current_segment[-1]["end"],
                "segments": current_segment,
                "text": " ".join([s["text"] for s in current_segment]),
            })

        logger.info(f"Created {len(segments)} topic segments")

        return segments

    def extract_summary(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Extract summary from transcript

        Args:
            transcript: List of transcript segments

        Returns:
            Summary text
        """
        # Simple extractive summarization
        # Get first, middle, and last segments as key points
        if len(transcript) <= 3:
            key_points = transcript
        else:
            n = len(transcript)
            key_points = [
                transcript[0],
                transcript[n // 2],
                transcript[-1],
            ]

        summary = " ".join([s["text"] for s in key_points])

        # Limit summary length
        max_length = 500
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary.strip()

    def align_frames_to_segments(
        self,
        transcript_segments: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Align frames to transcript segments

        Args:
            transcript_segments: List of transcript segments
            frame_analyses: List of frame analyses

        Returns:
            List of segments with aligned frames
        """
        for segment in transcript_segments:
            segment_start = segment["start"]
            segment_end = segment["end"]

            # Find frames within this segment
            aligned_frames = []
            for frame in frame_analyses:
                frame_time = frame.get("timestamp", 0)

                if segment_start <= frame_time <= segment_end:
                    aligned_frames.append(frame)

            segment["frames"] = aligned_frames

        logger.info(f"Aligned frames to {len(transcript_segments)} segments")

        return transcript_segments

    def extract_key_points(
        self,
        text: str,
        max_points: int = 5
    ) -> List[str]:
        """
        Extract key points from text

        Args:
            text: Input text
            max_points: Maximum number of points

        Returns:
            List of key points
        """
        # Simple rule-based extraction
        # Look for sentences with keywords
        keywords = ["重要", "关键", "核心", "重点", "注意", "imPortant", "key", "main"]

        sentences = re.split(r'[。！？.!?]', text)
        points = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:
                # Check if contains keyword
                if any(kw in sentence.lower() for kw in keywords):
                    points.append(sentence)

                if len(points) >= max_points:
                    break

        # If not enough points, add first few sentences
        if len(points) < max_points:
            for sentence in sentences:
                sentence = sentence.strip()
                if 10 < len(sentence) < 100 and sentence not in points:
                    points.append(sentence)
                    if len(points) >= max_points:
                        break

        return points[:max_points]


class ContentProcessor:
    """
    High-level content processing
    """

    def __init__(self):
        self.extractor = ContentExtractor()

    def process_transcript(
        self,
        transcript: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process transcript into structured content

        Args:
            transcript: Raw transcript segments

        Returns:
            Structured content dictionary
        """
        # Extract topics
        topics = self.extractor.extract_key_topics(transcript)

        # Create segments
        segments = self.extractor.segment_by_topic(transcript)

        # Generate summary
        summary = self.extractor.extract_summary(transcript)

        return {
            "summary": summary,
            "topics": topics,
            "segments": segments,
            "total_duration": transcript[-1]["end"] if transcript else 0,
        }

    def process_with_frames(
        self,
        transcript: List[Dict[str, Any]],
        frame_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process transcript with aligned frames

        Args:
            transcript: Raw transcript segments
            frame_analyses: Frame analysis results

        Returns:
            Structured content with aligned frames
        """
        content = self.process_transcript(transcript)

        # Align frames to segments
        content["segments"] = self.extractor.align_frames_to_segments(
            content["segments"],
            frame_analyses
        )

        return content
