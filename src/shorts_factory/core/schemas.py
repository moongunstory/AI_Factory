"""
개선된 데이터 스키마 - 시각적 속성 강화

유저의 궁극적 목표를 위한 스키마:
  1. 스토리 확장
  2. 장면 계산
  3. 프롬프트 생성 (명도, 채도, 그림체 포함)
  4. 이미지 생성 준비
  5. 영상 생성 준비
"""

from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Stage 1: Story Outline Schemas
# ============================================================================


class StoryBeat(BaseModel):
    """스토리의 단일 비트 (서사 단위)"""
    id: str = Field(..., description="고유 ID (예: beat_001)")
    title: str = Field(..., description="비트 제목")
    summary: str = Field(..., description="시각적 설명")
    story_function: Literal["hook", "setup", "rising_action", "climax", "resolution"] = Field(
        ..., description="서사 기능"
    )
    emotional_tone: str = Field(..., description="감정 톤")


class StoryMetadata(BaseModel):
    """스토리 메타데이터"""
    estimated_duration_seconds: int = Field(..., ge=15, le=300)
    target_platforms: list[str] = Field(
        default_factory=lambda: ["TikTok", "Instagram Reels", "YouTube Shorts"]
    )
    tone: str = Field(..., description="전체 톤")
    genre: str = Field(..., description="장르")


class StoryOutline(BaseModel):
    """스토리 아웃라인 (Stage 1 출력)"""
    logline: str = Field(..., description="원본 스토리 아이디어")
    metadata: StoryMetadata
    beats: list[StoryBeat] = Field(..., min_length=5, max_length=20)


# ============================================================================
# Stage 2: Scene & Shot Planning Schemas (시각적 속성 강화)
# ============================================================================


class VisualStyle(BaseModel):
    """
    샷의 시각적 스타일 속성

    이미지 생성에 필요한 모든 시각적 파라미터 포함:
    - 명도 (brightness)
    - 채도 (saturation)
    - 대비 (contrast)
    - 그림체 (art_style)
    - 색보정 (color_grading)
    """
    art_style: str = Field(
        ...,
        description="그림체/아트 스타일 (예: '사실적 영화풍', '애니메이션', '수채화', '3D 렌더링')"
    )
    brightness: Literal["very_dark", "dark", "medium", "bright", "very_bright"] = Field(
        default="medium",
        description="명도 수준"
    )
    saturation: Literal["desaturated", "low", "medium", "high", "vivid"] = Field(
        default="medium",
        description="채도 수준"
    )
    contrast: Literal["low", "medium", "high", "dramatic"] = Field(
        default="medium",
        description="대비 강도"
    )
    color_grading: str = Field(
        ...,
        description="색보정 스타일 (예: '따뜻한 오렌지톤', '차가운 청록색', '영화적 틸-오렌지')"
    )
    lighting_direction: str = Field(
        default="front",
        description="조명 방향 (예: 'front', 'back', 'side', 'top')"
    )
    mood_keywords: list[str] = Field(
        default_factory=list,
        description="분위기 키워드 (예: ['긴장감', '신비로운', '따뜻한'])"
    )


class ShotPlan(BaseModel):
    """
    개별 샷 계획 (시각적 속성 강화)

    이미지/비디오 생성에 필요한 모든 정보 포함
    """
    shot_id: str = Field(..., description="샷 ID (예: shot_001)")
    shot_type: str = Field(..., description="샷 타입 (클로즈업, 와이드 등)")
    camera_movement: str = Field(..., description="카메라 움직임")
    duration_seconds: float = Field(..., ge=0.8, le=4.0, description="지속 시간 (초)")
    action_description: str = Field(..., description="액션 설명")
    focus_subject: str = Field(..., description="초점 대상")
    emotional_tone: str = Field(..., description="감정 톤")
    transition_in: str = Field(..., description="전환 인")
    transition_out: str = Field(..., description="전환 아웃")

    # 시각적 속성 강화
    visual_style: VisualStyle = Field(..., description="시각적 스타일 속성")

    notes_for_prompt: str | None = Field(None, description="프롬프트 노트")


class ScenePlan(BaseModel):
    """씬 계획 (여러 샷 포함)"""
    scene_id: str = Field(..., description="씬 ID")
    related_beats: list[str] = Field(..., description="관련 비트 ID")
    scene_purpose: str = Field(..., description="씬 목적")
    location_description: str = Field(..., description="장소 설명")
    emotional_tone: str = Field(..., description="감정 톤")
    shots: list[ShotPlan] = Field(..., min_length=1)


class ScenePlanPackage(BaseModel):
    """전체 씬/샷 계획 (Stage 2 출력)"""
    logline: str
    metadata: StoryMetadata
    scenes: list[ScenePlan] = Field(..., min_length=3, max_length=12)


# ============================================================================
# Stage 3: Prompt Engineering Schemas (이미지 생성 준비)
# ============================================================================


class GlobalStyle(BaseModel):
    """
    전체 비디오의 글로벌 스타일

    모든 샷에 일관되게 적용되는 시각적 가이드
    """
    visual_style: str = Field(..., description="전체 비주얼 스타일")
    color_palette: str = Field(..., description="컬러 팔레트")
    lighting_style: str = Field(..., description="조명 스타일")
    camera_lens: str = Field(..., description="카메라 렌즈 특성")
    frame_format: str = Field(default="9:16", description="화면 비율")
    frame_rate_hint: str = Field(default="24fps cinematic", description="프레임레이트")

    # 일관성 유지를 위한 캐릭터/환경 디스크립션
    character_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="캐릭터 일관성 유지 (예: {'주인공': '검은 갑옷의 기사, 붉은 망토'})"
    )
    environment_palette: str = Field(
        default="",
        description="환경 색상 팔레트 (배경 일관성)"
    )


class ImageGenerationParams(BaseModel):
    """
    이미지 생성 파라미터

    Stable Diffusion, DALL-E, Midjourney 등에 사용
    """
    width: int = Field(default=720, description="이미지 너비 (9:16 = 720x1280)")
    height: int = Field(default=1280, description="이미지 높이")
    steps: int = Field(default=30, ge=20, le=150, description="생성 스텝 수")
    cfg_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="CFG 스케일")
    sampler: str = Field(default="DPM++ 2M Karras", description="샘플러")
    seed: int | None = Field(None, description="랜덤 시드 (일관성)")


class ShotPrompt(BaseModel):
    """
    개별 샷의 최종 프롬프트

    이미지/비디오 생성에 바로 사용 가능
    """
    shot_id: str
    scene_id: str
    positive_prompt: str = Field(..., min_length=25, description="포지티브 프롬프트")
    negative_prompt: str = Field(..., description="네거티브 프롬프트")
    duration_seconds: float = Field(..., ge=0.8, le=4.0)

    # 이미지 생성 파라미터
    generation_params: ImageGenerationParams = Field(
        default_factory=ImageGenerationParams,
        description="이미지 생성 파라미터"
    )

    # 시각적 속성 (프롬프트에서 재참조)
    visual_attributes: dict[str, str] = Field(
        default_factory=dict,
        description="시각적 속성 (명도, 채도 등)"
    )

    strength_tags: list[str] = Field(default_factory=list, description="강조 태그")


class PromptPackage(BaseModel):
    """최종 프롬프트 패키지 (Stage 3 출력)"""
    logline: str
    global_style: GlobalStyle
    shots: list[ShotPrompt] = Field(..., min_length=8, max_length=40)


# ============================================================================
# Stage 4-5: 이미지 및 비디오 생성 결과
# ============================================================================


class GeneratedImage(BaseModel):
    """생성된 이미지 정보"""
    shot_id: str
    image_path: str = Field(..., description="생성된 이미지 파일 경로")
    thumbnail_path: str | None = Field(None, description="썸네일 경로")
    generation_time_seconds: float = Field(..., description="생성 소요 시간")
    seed_used: int | None = Field(None, description="사용된 시드")
    metadata: dict[str, any] = Field(default_factory=dict, description="추가 메타데이터")


class GeneratedVideo(BaseModel):
    """생성된 비디오 정보"""
    video_path: str = Field(..., description="최종 비디오 파일 경로")
    duration_seconds: float = Field(..., description="총 재생 시간")
    resolution: str = Field(..., description="해상도 (예: 720x1280)")
    fps: int = Field(..., description="FPS")
    filesize_mb: float = Field(..., description="파일 크기 (MB)")
    shot_count: int = Field(..., description="총 샷 개수")
    generation_time_seconds: float = Field(..., description="생성 소요 시간")


# ============================================================================
# 최종 파이프라인 결과 (확장)
# ============================================================================


class ShortsGenerationResult(BaseModel):
    """
    전체 파이프라인 결과

    Stage 1-6 모든 단계의 출력 포함:
      1. 스토리 아웃라인
      2. 씬/샷 계획
      3. 프롬프트 패키지
      4. 생성된 이미지들 (선택사항)
      5. 최종 비디오 (선택사항)
    """
    outline: StoryOutline
    scene_plan: ScenePlanPackage
    prompts: PromptPackage

    # 선택적: 생성된 콘텐츠
    generated_images: list[GeneratedImage] = Field(
        default_factory=list,
        description="생성된 이미지 목록"
    )
    generated_video: GeneratedVideo | None = Field(
        None,
        description="최종 생성된 비디오"
    )

    def to_json_file(self, filepath: str) -> None:
        """결과를 JSON 파일로 저장"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json_file(cls, filepath: str) -> "ShortsGenerationResult":
        """JSON 파일에서 결과 로드"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
