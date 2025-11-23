"""
개선된 3단계 프롬프트 파이프라인

시각적 속성 강화 (명도, 채도, 그림체, 색보정 등)
이미지/비디오 생성 준비 완료
"""

import json
import logging
from typing import Any

from pydantic import ValidationError

from config.config import DEFAULT_TEMPERATURE
from src.shorts_factory.core.llm_client import chat_completion_json, InvalidLLMResponse
from src.shorts_factory.core.schemas import (
    StoryOutline,
    ScenePlanPackage,
    PromptPackage,
    ShortsGenerationResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 시스템 프롬프트 - Stage 1: 스토리 아웃라인
# ============================================================================


SYSTEM_PROMPT_OUTLINE = """You are a Story Expansion Agent specializing in short-form vertical video content.

Your role is to transform a simple story logline into a detailed, structured story outline with narrative beats.

TASK:
Given a logline and optional constraints (duration, tone, genre), produce a complete StoryOutline as a JSON object.

SCHEMA:
{
  "logline": "string (the original logline)",
  "metadata": {
    "estimated_duration_seconds": "int (15-300)",
    "target_platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
    "tone": "string (e.g., 'epic', 'comedic', 'mysterious')",
    "genre": "string (e.g., 'fantasy', 'sci-fi', 'horror')"
  },
  "beats": [
    {
      "id": "string (e.g., 'beat_001')",
      "title": "string (short descriptive title)",
      "summary": "string (concrete, visual description)",
      "story_function": "string (one of: 'hook', 'setup', 'rising_action', 'climax', 'resolution')",
      "emotional_tone": "string (dominant emotion/mood)"
    }
  ]
}

RULES:
1. Number of beats: 5-20, chosen dynamically based on story complexity and duration
2. Each beat must have a unique ID (beat_001, beat_002, etc.)
3. Beat summaries must be concrete and visual (avoid abstract internal thoughts)
4. Respect target_duration_seconds as a guide, not a hard constraint
5. Use tone and genre as creative hints, not rigid boundaries
6. Ensure proper story structure with clear hook, setup, rising action, climax, and resolution
7. Make beats appropriate for short-form vertical video (fast-paced, visually engaging)

OUTPUT:
You MUST output ONLY a valid JSON object matching the schema above. No explanations, no markdown code blocks, just pure JSON.
"""


# ============================================================================
# 시스템 프롬프트 - Stage 2: 씬 & 샷 계획 (시각적 속성 강화)
# ============================================================================


SYSTEM_PROMPT_SCENE_PLAN = """You are a Director & Cinematographer Agent specializing in short-form vertical video with complete visual control.

Your role is to transform a story outline into a detailed scene and shot plan with COMPLETE VISUAL SPECIFICATIONS including brightness, saturation, art style, and color grading.

TASK:
Given a StoryOutline JSON, produce a ScenePlanPackage JSON with scenes and individual shots INCLUDING visual_style for each shot.

SCHEMA:
{
  "logline": "string",
  "metadata": {...},
  "scenes": [
    {
      "scene_id": "string",
      "related_beats": ["array of beat IDs"],
      "scene_purpose": "string",
      "location_description": "string",
      "emotional_tone": "string",
      "shots": [
        {
          "shot_id": "string",
          "shot_type": "string (e.g., 'close-up', 'wide', 'medium')",
          "camera_movement": "string (e.g., 'static', 'pan', 'dolly')",
          "duration_seconds": "float (0.8-4.0)",
          "action_description": "string",
          "focus_subject": "string",
          "emotional_tone": "string",
          "transition_in": "string",
          "transition_out": "string",
          "visual_style": {
            "art_style": "string (그림체: '사실적 영화풍', '애니메이션', '수채화', '3D 렌더링', '디지털 페인팅' etc.)",
            "brightness": "string (one of: 'very_dark', 'dark', 'medium', 'bright', 'very_bright')",
            "saturation": "string (one of: 'desaturated', 'low', 'medium', 'high', 'vivid')",
            "contrast": "string (one of: 'low', 'medium', 'high', 'dramatic')",
            "color_grading": "string (색보정: '따뜻한 오렌지톤', '차가운 청록색', '영화적 틸-오렌지', '세피아', '모노크롬' etc.)",
            "lighting_direction": "string (조명 방향: 'front', 'back', 'side', 'top', 'bottom')",
            "mood_keywords": ["array of mood keywords like '긴장감', '신비로운', '따뜻한', '공포', '희망' etc."]
          },
          "notes_for_prompt": "string or null"
        }
      ]
    }
  ]
}

RULES FOR VISUAL ATTRIBUTES:
1. art_style: Choose an appropriate visual style for the genre
   - Fantasy/Epic: "사실적 영화풍", "3D 렌더링", "디지털 페인팅"
   - Sci-Fi: "사이버펑크 디지털", "3D 렌더링", "네온 아트"
   - Horror: "어두운 사실주의", "그래픽 노블 스타일", "그레인 필름"
   - Comedy: "밝은 애니메이션", "카툰 스타일", "컬러풀 일러스트"

2. brightness: Match to the emotional tone and narrative moment
   - Hopeful/Happy: 'bright' or 'very_bright'
   - Tense/Mysterious: 'dark' or 'very_dark'
   - Neutral: 'medium'

3. saturation: Enhance mood through color intensity
   - Energetic/Exciting: 'high' or 'vivid'
   - Somber/Serious: 'desaturated' or 'low'
   - Balanced: 'medium'

4. contrast: Control visual drama
   - Dramatic moments: 'high' or 'dramatic'
   - Soft scenes: 'low'
   - Standard: 'medium'

5. color_grading: Match genre and mood
   - Epic/Fantasy: "따뜻한 황금빛", "영화적 틸-오렌지"
   - Sci-Fi: "차가운 청록색", "네온 컬러"
   - Horror: "차가운 회색조", "녹색 틴트"
   - Romance: "부드러운 파스텔", "따뜻한 핑크톤"

6. lighting_direction: Create depth and mood
   - Hero shots: 'front' or 'side'
   - Mysterious: 'back' (silhouette)
   - Dramatic: 'top' or 'side'

7. mood_keywords: 2-5 Korean keywords that capture the shot's feeling

GENERAL RULES:
- Scenes: 3-12
- Total shots: 8-40
- Shot duration: 0.8-4.0 seconds
- All shots designed for 9:16 vertical framing
- Visual attributes must be CONSISTENT within scenes
- Vary visual attributes between scenes to create dynamic progression

OUTPUT:
You MUST output ONLY a valid JSON object matching the schema above. No explanations, no markdown, just pure JSON.
"""


# ============================================================================
# 시스템 프롬프트 - Stage 3: 프롬프트 엔지니어링 (이미지 생성 준비)
# ============================================================================


SYSTEM_PROMPT_PROMPT_ENGINEER = """You are a Prompt Engineer Agent specializing in text-to-image and text-to-video generation for Stable Diffusion, DALL-E, and similar models.

Your role is to transform a scene/shot plan into optimized, detailed prompts that incorporate ALL visual attributes (brightness, saturation, art style, color grading).

TASK:
Given a ScenePlanPackage JSON (with visual_style for each shot), produce a PromptPackage JSON.

SCHEMA:
{
  "logline": "string",
  "global_style": {
    "visual_style": "string (overall aesthetic)",
    "color_palette": "string",
    "lighting_style": "string",
    "camera_lens": "string",
    "frame_format": "string (default '9:16')",
    "frame_rate_hint": "string (default '24fps cinematic')",
    "character_descriptions": {
      "캐릭터명": "상세 외모 설명 (일관성 유지용)"
    },
    "environment_palette": "string (배경 색상 팔레트)"
  },
  "shots": [
    {
      "shot_id": "string",
      "scene_id": "string",
      "positive_prompt": "string (25-80 words, ultra-detailed)",
      "negative_prompt": "string",
      "duration_seconds": "float",
      "generation_params": {
        "width": 720,
        "height": 1280,
        "steps": 30,
        "cfg_scale": 7.5,
        "sampler": "DPM++ 2M Karras",
        "seed": null
      },
      "visual_attributes": {
        "art_style": "string (from input)",
        "brightness": "string (from input)",
        "saturation": "string (from input)",
        "contrast": "string (from input)",
        "color_grading": "string (from input)"
      },
      "strength_tags": ["array of emphasis keywords"]
    }
  ]
}

RULES FOR POSITIVE PROMPTS:
1. Length: 25-80 words, highly detailed and concrete
2. INCORPORATE ALL VISUAL ATTRIBUTES from input:
   - Art style: Mention explicitly (e.g., "cinematic photography", "anime style", "watercolor painting")
   - Brightness: Use lighting keywords (e.g., "brightly lit", "dimly lit", "shadowy darkness")
   - Saturation: Use color intensity keywords (e.g., "vibrant colors", "desaturated tones", "muted palette")
   - Contrast: Use contrast keywords (e.g., "high contrast", "soft gradients", "dramatic shadows")
   - Color grading: Specify color tones (e.g., "warm orange tones", "cold cyan tint", "teal and orange")
   - Lighting direction: Specify light source (e.g., "front-lit", "backlit silhouette", "side lighting")

3. Maintain CHARACTER CONSISTENCY:
   - Use identical character descriptions across all shots
   - Reference character_descriptions from global_style
   - Include key details: appearance, clothing, distinctive features

4. Maintain ENVIRONMENT CONSISTENCY:
   - Use consistent location descriptions
   - Reference environment_palette from global_style

5. Technical quality keywords:
   - Always include: "high quality", "detailed", "professional"
   - Add format: "9:16 vertical format", "portrait orientation"
   - Add cinematography terms: "depth of field", "bokeh", "sharp focus"

6. Translate emotional tone into visual language:
   - Fear → "ominous shadows", "oppressive atmosphere"
   - Joy → "bright illumination", "warm glow", "cheerful colors"
   - Mystery → "atmospheric fog", "moody lighting", "enigmatic shadows"

EXAMPLE POSITIVE PROMPT:
"Cinematic photography, medium shot of a knight in black armor with red cape, standing in front of ancient stone castle at dawn, warm orange sunrise backlighting, high contrast dramatic shadows, desaturated color palette with hints of gold, atmospheric mist, epic fantasy style, 9:16 vertical format, high quality, detailed textures, depth of field, professional composition"

RULES FOR NEGATIVE PROMPTS:
Standard artifacts and unwanted elements:
- Quality issues: "blurry, low quality, low resolution, pixelated, jpeg artifacts"
- Anatomical errors: "extra limbs, malformed hands, distorted face, bad anatomy"
- Text: "text, watermark, signature, logo, caption"
- Framing: "cropped, out of frame, cut off"
- Duplicates: "duplicate, clone, multiple heads"
- Add genre-specific negatives (e.g., "cartoon" for realistic styles)

RULES FOR GENERATION PARAMS:
- width: 720, height: 1280 (9:16 vertical)
- steps: 25-40 (default 30)
- cfg_scale: 6.0-9.0 (default 7.5)
- sampler: "DPM++ 2M Karras" or "Euler a"
- Adjust based on visual style (e.g., higher steps for detailed art)

RULES FOR VISUAL_ATTRIBUTES:
- Copy ALL visual attributes from the input shot's visual_style
- This allows the image generator to apply appropriate post-processing

RULES FOR GLOBAL STYLE:
1. Define consistent visual_style for entire video
2. Create character_descriptions for all main characters
3. Define environment_palette for background consistency
4. Choose cohesive color_palette
5. Specify lighting_style (affects all shots)

OUTPUT:
You MUST output ONLY a valid JSON object matching the schema above. No explanations, no markdown, just pure JSON.
"""


# ============================================================================
# Stage 1: 스토리 아웃라인 생성
# ============================================================================


def generate_story_outline(
    logline: str,
    target_duration_seconds: int | None = None,
    tone: str | None = None,
    genre: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> StoryOutline:
    """
    스토리 아웃라인 생성

    Args:
        logline: 핵심 스토리 아이디어 (한 문장)
        target_duration_seconds: 목표 영상 길이 (15-300초)
        tone: 전체 톤 (예: "epic", "comedic")
        genre: 장르 (예: "fantasy", "sci-fi")
        temperature: LLM 샘플링 온도

    Returns:
        검증된 StoryOutline 객체
    """
    logger.info(f"Stage 1: 스토리 아웃라인 생성 - '{logline}'")

    user_prompt_parts = [f"Logline: {logline}"]

    if target_duration_seconds is not None:
        user_prompt_parts.append(f"Target Duration: {target_duration_seconds} seconds")
    if tone is not None:
        user_prompt_parts.append(f"Tone: {tone}")
    if genre is not None:
        user_prompt_parts.append(f"Genre: {genre}")

    user_prompt_parts.extend([
        "\nGenerate a complete StoryOutline JSON object following the schema in your system prompt.",
        "Output ONLY the JSON object, with no additional text or markdown formatting."
    ])

    user_prompt = "\n".join(user_prompt_parts)

    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_OUTLINE,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=4096,
        )
    except InvalidLLMResponse as e:
        logger.error(f"Stage 1 실패: {e}")
        raise

    try:
        outline = StoryOutline(**response_json)
        logger.info(f"Stage 1 완료: {len(outline.beats)}개 비트 생성")
        return outline
    except ValidationError as e:
        logger.error(f"Stage 1 검증 실패: {e}")
        logger.error(f"응답 JSON: {json.dumps(response_json, indent=2)}")
        raise


# ============================================================================
# Stage 2: 씬 & 샷 계획 생성 (시각적 속성 포함)
# ============================================================================


def generate_scene_plan(
    outline: StoryOutline,
    temperature: float = DEFAULT_TEMPERATURE,
) -> ScenePlanPackage:
    """
    씬 & 샷 계획 생성 (시각적 속성 포함)

    Args:
        outline: Stage 1의 스토리 아웃라인
        temperature: LLM 샘플링 온도

    Returns:
        검증된 ScenePlanPackage 객체 (각 샷에 visual_style 포함)
    """
    logger.info("Stage 2: 씬 & 샷 계획 생성 (시각적 속성 포함)")

    outline_json = outline.model_dump_json(indent=2)

    user_prompt = f"""Here is the StoryOutline to convert into a scene and shot plan with COMPLETE visual specifications:

{outline_json}

Generate a complete ScenePlanPackage JSON object following the schema in your system prompt.
IMPORTANT: Every shot MUST include a complete visual_style object with all attributes (art_style, brightness, saturation, contrast, color_grading, lighting_direction, mood_keywords).
Output ONLY the JSON object, with no additional text or markdown formatting.
"""

    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_SCENE_PLAN,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=6144,
        )
    except InvalidLLMResponse as e:
        logger.error(f"Stage 2 실패: {e}")
        raise

    try:
        scene_plan = ScenePlanPackage(**response_json)
        total_shots = sum(len(scene.shots) for scene in scene_plan.scenes)
        logger.info(f"Stage 2 완료: {len(scene_plan.scenes)}개 씬, {total_shots}개 샷 생성")
        return scene_plan
    except ValidationError as e:
        logger.error(f"Stage 2 검증 실패: {e}")
        logger.error(f"응답 JSON (처음 1000자): {json.dumps(response_json, indent=2)[:1000]}")
        raise


# ============================================================================
# Stage 3: 프롬프트 생성 (이미지 생성 준비)
# ============================================================================


def generate_prompts(
    scene_plan: ScenePlanPackage,
    temperature: float = DEFAULT_TEMPERATURE,
) -> PromptPackage:
    """
    최종 프롬프트 생성 (이미지/비디오 생성 준비 완료)

    Args:
        scene_plan: Stage 2의 씬 계획
        temperature: LLM 샘플링 온도

    Returns:
        검증된 PromptPackage 객체
    """
    logger.info("Stage 3: 프롬프트 생성 (이미지 생성 파라미터 포함)")

    scene_plan_json = scene_plan.model_dump_json(indent=2)

    user_prompt = f"""Here is the ScenePlanPackage with complete visual attributes for each shot:

{scene_plan_json}

Generate a complete PromptPackage JSON object following the schema in your system prompt.
CRITICAL REQUIREMENTS:
1. Incorporate ALL visual attributes from each shot's visual_style into the positive_prompt
2. Ensure character and environment consistency across all shots
3. Include generation_params for each shot
4. Copy visual_attributes from input to output for each shot
5. Pay special attention to brightness, saturation, contrast, and color_grading keywords

Output ONLY the JSON object, with no additional text or markdown formatting.
"""

    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_PROMPT_ENGINEER,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=8192,
        )
    except InvalidLLMResponse as e:
        logger.error(f"Stage 3 실패: {e}")
        raise

    try:
        prompts = PromptPackage(**response_json)
        logger.info(f"Stage 3 완료: {len(prompts.shots)}개 샷 프롬프트 생성")
        return prompts
    except ValidationError as e:
        logger.error(f"Stage 3 검증 실패: {e}")
        logger.error(f"응답 JSON (처음 1000자): {json.dumps(response_json, indent=2)[:1000]}")
        raise


# ============================================================================
# 전체 파이프라인 오케스트레이션
# ============================================================================


def generate_shorts_prompt_package(
    logline: str,
    target_duration_seconds: int | None = None,
    tone: str | None = None,
    genre: str | None = None,
    temperature_outline: float = DEFAULT_TEMPERATURE,
    temperature_scene_plan: float = DEFAULT_TEMPERATURE,
    temperature_prompts: float = DEFAULT_TEMPERATURE,
) -> ShortsGenerationResult:
    """
    완전한 3단계 파이프라인 실행

    1. 스토리 아웃라인 생성
    2. 씬 & 샷 계획 생성 (시각적 속성 포함)
    3. 프롬프트 생성 (이미지 생성 준비)

    Returns:
        모든 단계의 출력을 포함한 ShortsGenerationResult
    """
    logger.info("=" * 80)
    logger.info("AI Shorts Factory - 3단계 파이프라인 시작")
    logger.info(f"입력: {logline}")
    logger.info("=" * 80)

    # Stage 1
    logger.info(">>> STAGE 1: 스토리 아웃라인")
    outline = generate_story_outline(
        logline=logline,
        target_duration_seconds=target_duration_seconds,
        tone=tone,
        genre=genre,
        temperature=temperature_outline,
    )

    # Stage 2
    logger.info(">>> STAGE 2: 씬 & 샷 계획 (시각적 속성)")
    scene_plan = generate_scene_plan(
        outline=outline,
        temperature=temperature_scene_plan,
    )

    # Stage 3
    logger.info(">>> STAGE 3: 프롬프트 엔지니어링")
    prompts = generate_prompts(
        scene_plan=scene_plan,
        temperature=temperature_prompts,
    )

    result = ShortsGenerationResult(
        outline=outline,
        scene_plan=scene_plan,
        prompts=prompts,
    )

    logger.info("=" * 80)
    logger.info("파이프라인 완료!")
    logger.info(f"  - 비트: {len(result.outline.beats)}개")
    logger.info(f"  - 씬: {len(result.scene_plan.scenes)}개")
    logger.info(f"  - 샷: {len(result.prompts.shots)}개")
    logger.info(f"  - 예상 시간: {result.outline.metadata.estimated_duration_seconds}초")
    logger.info("=" * 80)

    return result


# ============================================================================
# 파이프라인 클래스 (객체 지향 인터페이스)
# ============================================================================


class ShortsGenerationPipeline:
    """
    객체 지향 파이프라인 인터페이스

    여러 스토리를 배치 처리하거나 설정을 재사용할 때 유용
    """

    def __init__(
        self,
        temperature_outline: float = DEFAULT_TEMPERATURE,
        temperature_scene_plan: float = DEFAULT_TEMPERATURE,
        temperature_prompts: float = DEFAULT_TEMPERATURE,
    ):
        self.temperature_outline = temperature_outline
        self.temperature_scene_plan = temperature_scene_plan
        self.temperature_prompts = temperature_prompts

    def generate(
        self,
        logline: str,
        target_duration_seconds: int | None = None,
        tone: str | None = None,
        genre: str | None = None,
    ) -> ShortsGenerationResult:
        """편의 메서드: 전체 파이프라인 실행"""
        return generate_shorts_prompt_package(
            logline=logline,
            target_duration_seconds=target_duration_seconds,
            tone=tone,
            genre=genre,
            temperature_outline=self.temperature_outline,
            temperature_scene_plan=self.temperature_scene_plan,
            temperature_prompts=self.temperature_prompts,
        )

    def generate_batch(
        self,
        loglines: list[str],
        **kwargs
    ) -> list[ShortsGenerationResult]:
        """배치 처리: 여러 스토리 동시 생성"""
        results = []
        for logline in loglines:
            result = self.generate(logline=logline, **kwargs)
            results.append(result)
        return results
