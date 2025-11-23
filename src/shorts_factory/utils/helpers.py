"""
유틸리티 헬퍼 함수들
"""

import json
import logging
from pathlib import Path
from typing import Any

from config.config import LOG_LEVEL, LOG_FORMAT


def setup_logging(level: str | None = None) -> None:
    """
    로깅 설정 초기화

    Args:
        level: 로그 레벨 (None이면 config에서 가져옴)
    """
    if level is None:
        level = LOG_LEVEL

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"로깅 초기화: {level}")


def save_json(data: Any, filepath: str | Path, indent: int = 2) -> None:
    """
    데이터를 JSON 파일로 저장

    Args:
        data: 저장할 데이터 (dict, list, Pydantic 모델 등)
        filepath: 저장 경로
        indent: JSON 들여쓰기
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Pydantic 모델인 경우
    if hasattr(data, 'model_dump'):
        data = data.model_dump()

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(filepath: str | Path) -> dict:
    """
    JSON 파일 로드

    Args:
        filepath: JSON 파일 경로

    Returns:
        파싱된 JSON 데이터
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """
    초 단위 시간을 보기 좋게 포맷

    Args:
        seconds: 초 단위 시간

    Returns:
        포맷된 문자열 (예: "1m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    secs = seconds % 60

    if minutes < 60:
        return f"{minutes}m {secs:.1f}s"

    hours = int(minutes // 60)
    minutes = minutes % 60

    return f"{hours}h {minutes}m {secs:.1f}s"


def print_pipeline_summary(result: Any) -> None:
    """
    파이프라인 결과 요약 출력

    Args:
        result: ShortsGenerationResult 객체
    """
    print("\n" + "=" * 80)
    print("AI SHORTS FACTORY - 생성 결과")
    print("=" * 80)

    # 스토리 정보
    print(f"\n📖 스토리: {result.outline.logline}")
    print(f"   장르: {result.outline.metadata.genre}")
    print(f"   톤: {result.outline.metadata.tone}")
    print(f"   비트: {len(result.outline.beats)}개")

    # 씬 정보
    print(f"\n🎬 씬: {len(result.scene_plan.scenes)}개")
    total_shots = len(result.prompts.shots)
    print(f"   샷: {total_shots}개")

    # 총 시간
    total_duration = sum(shot.duration_seconds for shot in result.prompts.shots)
    print(f"   총 시간: {format_duration(total_duration)}")

    # 비주얼 스타일
    print(f"\n✨ 비주얼 스타일:")
    print(f"   {result.prompts.global_style.visual_style}")
    print(f"   색상: {result.prompts.global_style.color_palette}")
    print(f"   조명: {result.prompts.global_style.lighting_style}")

    # 생성된 콘텐츠
    if result.generated_images:
        print(f"\n🖼️  생성된 이미지: {len(result.generated_images)}개")

    if result.generated_video:
        print(f"\n🎥 생성된 비디오:")
        print(f"   경로: {result.generated_video.video_path}")
        print(f"   시간: {format_duration(result.generated_video.duration_seconds)}")
        print(f"   크기: {result.generated_video.filesize_mb:.1f} MB")

    print("\n" + "=" * 80 + "\n")
