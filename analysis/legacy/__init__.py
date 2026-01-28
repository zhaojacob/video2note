"""
Legacy LLM Clients Module

This module contains the old GLM and Doubao clients that have been superseded
by the UnifiedLLMManager. They are kept here for backward compatibility.

New code should use UnifiedLLMManager instead:
    from utils.llm.unified_manager import UnifiedLLMManager
    manager = UnifiedLLMManager()
    client = manager.get_client("glm-4-flash")
"""

from .glm_client import GLMClient
from .doubao_client import DoubaoClient

__all__ = ["GLMClient", "DoubaoClient"]
