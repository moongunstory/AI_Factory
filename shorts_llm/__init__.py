"""
AI Shorts Factory - LLM-Powered Prompt Pipeline

A production-quality Python module for generating AI short video content
using a local Llama language model through a 3-stage pipeline:

1. Story Outline Generation (logline → structured beats)
2. Scene & Shot Planning (outline → cinematography plan)
3. Prompt Engineering (shots → text-to-image/video prompts)

Usage:
    >>> from shorts_llm.pipeline import generate_shorts_prompt_package
    >>> result = generate_shorts_prompt_package(
    ...     logline="A knight defeats a dragon and saves the princess.",
    ...     target_duration_seconds=60,
    ...     tone="epic",
    ...     genre="fantasy"
    ... )
    >>> print(result.prompts.shots[0].positive_prompt)
"""

__version__ = "0.1.0"
__author__ = "AI Shorts Factory Team"

from shorts_llm.pipeline import generate_shorts_prompt_package
from shorts_llm.schemas import (
    ShortsGenerationResult,
    StoryOutline,
    ScenePlanPackage,
    PromptPackage,
)

__all__ = [
    "generate_shorts_prompt_package",
    "ShortsGenerationResult",
    "StoryOutline",
    "ScenePlanPackage",
    "PromptPackage",
]
