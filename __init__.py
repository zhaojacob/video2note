"""
Video Note Generation System

An intelligent system for generating structured notes from videos.
Supports YouTube and Bilibili platforms with GPU-accelerated transcription
and multi-modal image analysis.
"""

__version__ = "1.0.0"
__author__ = "Video Note System"

from pipeline.pipeline_orchestrator import PipelineOrchestrator, run_pipeline

__all__ = ["PipelineOrchestrator", "run_pipeline"]
