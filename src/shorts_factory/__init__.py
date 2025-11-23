"""
AI Shorts Factory - Core Package

통합 비디오 생성 파이프라인:
  스토리 입력 → LLM 확장 → 장면 계획 → 프롬프트 생성 → 이미지 생성 → 영상 합성
"""

__version__ = "0.2.0"
__author__ = "AI Shorts Factory"

from src.shorts_factory.core.pipeline import (
    generate_shorts_prompt_package,
    ShortsGenerationPipeline,
)
from src.shorts_factory.core.schemas import (
    ShortsGenerationResult,
    StoryOutline,
    ScenePlanPackage,
    PromptPackage,
)

__all__ = [
    "generate_shorts_prompt_package",
    "ShortsGenerationPipeline",
    "ShortsGenerationResult",
    "StoryOutline",
    "ScenePlanPackage",
    "PromptPackage",
]
