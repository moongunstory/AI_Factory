"""
3-Stage Prompt Pipeline Orchestration.

Implements the complete pipeline for generating AI short video content:
1. Story Outline Generation (logline → beats)
2. Scene & Shot Planning (outline → cinematography)
3. Prompt Engineering (shots → generation prompts)
"""

import json
import logging
from typing import Any

from pydantic import ValidationError

from shorts_llm.config import DEFAULT_TEMPERATURE
from shorts_llm.llm_client import chat_completion_json, InvalidLLMResponse
from shorts_llm.schemas import (
    StoryOutline,
    ScenePlanPackage,
    PromptPackage,
    ShortsGenerationResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# System Prompts for Each Stage
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


SYSTEM_PROMPT_SCENE_PLAN = """You are a Director & Shot Planner Agent specializing in short-form vertical video content.

Your role is to transform a story outline into a detailed scene and shot plan suitable for video production.

TASK:
Given a StoryOutline JSON, produce a ScenePlanPackage JSON with scenes and individual shots.

SCHEMA:
{
  "logline": "string (original logline)",
  "metadata": {
    "estimated_duration_seconds": "int",
    "target_platforms": ["array of strings"],
    "tone": "string",
    "genre": "string"
  },
  "scenes": [
    {
      "scene_id": "string (e.g., 'scene_001')",
      "related_beats": ["array of beat IDs this scene covers"],
      "scene_purpose": "string (narrative purpose)",
      "location_description": "string (where scene takes place)",
      "emotional_tone": "string (scene mood)",
      "shots": [
        {
          "shot_id": "string (e.g., 'shot_001')",
          "shot_type": "string (e.g., 'close-up', 'wide', 'medium', 'extreme close-up')",
          "camera_movement": "string (e.g., 'static', 'pan', 'tilt', 'dolly', 'tracking')",
          "duration_seconds": "float (0.8-4.0)",
          "action_description": "string (what happens)",
          "focus_subject": "string (primary subject)",
          "emotional_tone": "string (shot mood)",
          "transition_in": "string (e.g., 'cut', 'fade in', 'dissolve')",
          "transition_out": "string (e.g., 'cut', 'fade out', 'dissolve')",
          "notes_for_prompt": "string or null (optional notes)"
        }
      ]
    }
  ]
}

RULES:
1. Number of scenes: 3-12
2. Total number of shots: 8-40
3. Each shot duration: 0.8-4.0 seconds (fast-paced for short-form)
4. Vary shot_type and camera_movement for visual interest
5. All shots must be designed for 9:16 vertical framing
6. Ensure smooth transitions between shots
7. Maintain visual continuity within scenes
8. Balance pacing: mix quick cuts with occasional longer shots for emphasis
9. Focus on visual storytelling (what the audience will SEE)
10. shots array must have at least one shot per scene

OUTPUT:
You MUST output ONLY a valid JSON object matching the schema above. No explanations, no markdown, just pure JSON.
"""


SYSTEM_PROMPT_PROMPT_ENGINEER = """You are a Prompt Engineer Agent specializing in text-to-image and text-to-video generation.

Your role is to transform a scene/shot plan into detailed, optimized prompts for AI generation models.

TASK:
Given a ScenePlanPackage JSON, produce a PromptPackage JSON with prompts for each shot.

SCHEMA:
{
  "logline": "string (original logline)",
  "global_style": {
    "visual_style": "string (e.g., 'cinematic realism', 'anime', 'watercolor')",
    "color_palette": "string (color scheme description)",
    "lighting_style": "string (e.g., 'dramatic chiaroscuro', 'soft natural light')",
    "camera_lens": "string (e.g., '35mm anamorphic', '50mm portrait')",
    "frame_format": "string (default '9:16')",
    "frame_rate_hint": "string (default '24fps cinematic')"
  },
  "shots": [
    {
      "shot_id": "string (must match shot from input)",
      "scene_id": "string (must match scene from input)",
      "positive_prompt": "string (25-80 words, detailed, concrete, visual)",
      "negative_prompt": "string (artifacts to avoid)",
      "duration_seconds": "float (must match shot duration)",
      "seed_hint": "string or null (optional seed suggestion)",
      "strength_tags": ["array of emphasis tags"]
    }
  ]
}

RULES FOR POSITIVE PROMPTS:
1. Length: 25-80 words per prompt
2. Be concrete and visual (describe what you SEE, not what you feel)
3. Maintain character consistency across shots:
   - Use consistent character descriptions
   - Reference the same character details (appearance, clothing, etc.)
4. Maintain environment consistency across scenes:
   - Use consistent location descriptions
   - Keep lighting and atmosphere coherent
5. Include technical details: lighting, camera angle, composition
6. Use cinematic vocabulary: "establishing shot", "rack focus", "depth of field"
7. Specify 9:16 vertical framing where relevant
8. Reference the emotional tone through visual elements (colors, lighting, composition)
9. Avoid abstract concepts; translate emotion into visual language

RULES FOR NEGATIVE PROMPTS:
1. Standard artifacts: blurry, low quality, low resolution, pixelated
2. Anatomical errors: extra limbs, malformed hands, distorted face
3. Text and watermarks: text, watermark, signature, logo
4. Unwanted elements: cropped, out of frame, duplicate
5. Quality issues: jpeg artifacts, compression artifacts
6. Customize based on genre (e.g., "cartoony" for realistic styles)

RULES FOR GLOBAL STYLE:
1. Define a consistent visual style for the entire short
2. Choose a cohesive color palette
3. Specify lighting approach (affects mood)
4. Define camera/lens characteristics
5. Ensure style is appropriate for the genre and tone

RULES FOR CONSISTENCY:
- Characters must be described identically across shots (same clothing, same appearance)
- Environments must maintain coherent visual language
- Lighting should be consistent within scenes
- Use character names or identifiers ("the knight", "the princess") consistently

OUTPUT:
You MUST output ONLY a valid JSON object matching the schema above. No explanations, no markdown, just pure JSON.
"""


# ============================================================================
# Stage 1: Story Outline Generation
# ============================================================================


def generate_story_outline(
    logline: str,
    target_duration_seconds: int | None = None,
    tone: str | None = None,
    genre: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> StoryOutline:
    """
    Generate a structured story outline from a logline.

    This is Stage 1 of the pipeline. It transforms a simple story idea
    into a detailed outline with narrative beats.

    Args:
        logline: The core story idea (one sentence)
        target_duration_seconds: Target video duration (15-300)
        tone: Overall narrative tone (e.g., "epic", "comedic")
        genre: Story genre (e.g., "fantasy", "sci-fi")
        temperature: LLM sampling temperature (0.0-1.0)

    Returns:
        A validated StoryOutline object

    Raises:
        InvalidLLMResponse: If LLM returns invalid JSON
        ValidationError: If JSON doesn't match schema

    Example:
        >>> outline = generate_story_outline(
        ...     logline="A knight defeats a dragon and saves the princess.",
        ...     target_duration_seconds=60,
        ...     tone="epic",
        ...     genre="fantasy"
        ... )
        >>> print(len(outline.beats))
        8
    """
    logger.info(f"Stage 1: Generating story outline for logline: '{logline}'")

    # Build user prompt
    user_prompt_parts = [
        f"Logline: {logline}",
    ]

    if target_duration_seconds is not None:
        user_prompt_parts.append(f"Target Duration: {target_duration_seconds} seconds")

    if tone is not None:
        user_prompt_parts.append(f"Tone: {tone}")

    if genre is not None:
        user_prompt_parts.append(f"Genre: {genre}")

    user_prompt_parts.append(
        "\nGenerate a complete StoryOutline JSON object following the schema in your system prompt."
    )
    user_prompt_parts.append(
        "Output ONLY the JSON object, with no additional text or markdown formatting."
    )

    user_prompt = "\n".join(user_prompt_parts)

    logger.debug(f"User prompt for outline: {user_prompt}")

    # Call LLM
    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_OUTLINE,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=4096,
        )

    except InvalidLLMResponse as e:
        logger.error(f"Stage 1 failed: {e}")
        raise

    # Validate with Pydantic
    try:
        outline = StoryOutline(**response_json)
        logger.info(f"Stage 1 complete: Generated {len(outline.beats)} beats")
        return outline

    except ValidationError as e:
        logger.error(f"Stage 1 validation failed: {e}")
        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)}")
        raise


# ============================================================================
# Stage 2: Scene & Shot Planning
# ============================================================================


def generate_scene_plan(
    outline: StoryOutline,
    temperature: float = DEFAULT_TEMPERATURE,
) -> ScenePlanPackage:
    """
    Generate a detailed scene and shot plan from a story outline.

    This is Stage 2 of the pipeline. It transforms the narrative beats
    into concrete scenes and camera shots suitable for video production.

    Args:
        outline: The story outline from Stage 1
        temperature: LLM sampling temperature (0.0-1.0)

    Returns:
        A validated ScenePlanPackage object

    Raises:
        InvalidLLMResponse: If LLM returns invalid JSON
        ValidationError: If JSON doesn't match schema

    Example:
        >>> scene_plan = generate_scene_plan(outline)
        >>> total_shots = sum(len(scene.shots) for scene in scene_plan.scenes)
        >>> print(total_shots)
        24
    """
    logger.info("Stage 2: Generating scene and shot plan")

    # Convert outline to JSON string for the user prompt
    outline_json = outline.model_dump_json(indent=2)

    user_prompt = f"""Here is the StoryOutline to convert into a scene and shot plan:

{outline_json}

Generate a complete ScenePlanPackage JSON object following the schema in your system prompt.
Output ONLY the JSON object, with no additional text or markdown formatting.
"""

    logger.debug(f"User prompt for scene plan (outline length: {len(outline_json)} chars)")

    # Call LLM
    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_SCENE_PLAN,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=6144,
        )

    except InvalidLLMResponse as e:
        logger.error(f"Stage 2 failed: {e}")
        raise

    # Validate with Pydantic
    try:
        scene_plan = ScenePlanPackage(**response_json)
        total_shots = sum(len(scene.shots) for scene in scene_plan.scenes)
        logger.info(
            f"Stage 2 complete: Generated {len(scene_plan.scenes)} scenes, {total_shots} total shots"
        )
        return scene_plan

    except ValidationError as e:
        logger.error(f"Stage 2 validation failed: {e}")
        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)[:1000]}")
        raise


# ============================================================================
# Stage 3: Prompt Engineering
# ============================================================================


def generate_prompts(
    scene_plan: ScenePlanPackage,
    temperature: float = DEFAULT_TEMPERATURE,
) -> PromptPackage:
    """
    Generate detailed text-to-image/video prompts from a scene plan.

    This is Stage 3 of the pipeline. It transforms the shot plan into
    optimized prompts ready for AI generation models.

    Args:
        scene_plan: The scene plan from Stage 2
        temperature: LLM sampling temperature (0.0-1.0)

    Returns:
        A validated PromptPackage object

    Raises:
        InvalidLLMResponse: If LLM returns invalid JSON
        ValidationError: If JSON doesn't match schema

    Example:
        >>> prompts = generate_prompts(scene_plan)
        >>> print(prompts.shots[0].positive_prompt)
        "Epic establishing shot of a medieval castle at dawn..."
    """
    logger.info("Stage 3: Generating prompts for each shot")

    # Convert scene plan to JSON string for the user prompt
    scene_plan_json = scene_plan.model_dump_json(indent=2)

    user_prompt = f"""Here is the ScenePlanPackage to convert into generation prompts:

{scene_plan_json}

Generate a complete PromptPackage JSON object following the schema in your system prompt.
Pay special attention to character and environment consistency across all shots.
Output ONLY the JSON object, with no additional text or markdown formatting.
"""

    logger.debug(f"User prompt for prompts (scene plan length: {len(scene_plan_json)} chars)")

    # Call LLM
    try:
        response_json = chat_completion_json(
            system_prompt=SYSTEM_PROMPT_PROMPT_ENGINEER,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=8192,
        )

    except InvalidLLMResponse as e:
        logger.error(f"Stage 3 failed: {e}")
        raise

    # Validate with Pydantic
    try:
        prompts = PromptPackage(**response_json)
        logger.info(f"Stage 3 complete: Generated {len(prompts.shots)} shot prompts")
        return prompts

    except ValidationError as e:
        logger.error(f"Stage 3 validation failed: {e}")
        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)[:1000]}")
        raise


# ============================================================================
# High-Level Pipeline Orchestration
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
    Complete 3-stage pipeline for AI short video generation.

    This is the main high-level function that orchestrates the entire pipeline:
    1. Generate story outline from logline
    2. Generate scene and shot plan from outline
    3. Generate text-to-image/video prompts from shot plan

    Args:
        logline: The core story idea (one sentence)
        target_duration_seconds: Target video duration (15-300)
        tone: Overall narrative tone (e.g., "epic", "comedic")
        genre: Story genre (e.g., "fantasy", "sci-fi")
        temperature_outline: Temperature for Stage 1 (story outline)
        temperature_scene_plan: Temperature for Stage 2 (shot planning)
        temperature_prompts: Temperature for Stage 3 (prompt engineering)

    Returns:
        A ShortsGenerationResult containing all intermediate and final outputs

    Raises:
        InvalidLLMResponse: If any LLM call fails
        ValidationError: If any stage produces invalid data
        LLMConnectionError: If unable to connect to LLM server

    Example:
        >>> result = generate_shorts_prompt_package(
        ...     logline="A knight defeats a dragon and saves the princess.",
        ...     target_duration_seconds=60,
        ...     tone="epic",
        ...     genre="fantasy"
        ... )
        >>> print(f"Generated {len(result.prompts.shots)} shots")
        >>> result.to_json_file("output.json")
    """
    logger.info("=" * 80)
    logger.info("Starting 3-stage AI Shorts pipeline")
    logger.info(f"Logline: {logline}")
    logger.info("=" * 80)

    # Stage 1: Story Outline
    logger.info(">>> STAGE 1: Story Outline Generation")
    outline = generate_story_outline(
        logline=logline,
        target_duration_seconds=target_duration_seconds,
        tone=tone,
        genre=genre,
        temperature=temperature_outline,
    )

    # Stage 2: Scene & Shot Planning
    logger.info(">>> STAGE 2: Scene & Shot Planning")
    scene_plan = generate_scene_plan(
        outline=outline,
        temperature=temperature_scene_plan,
    )

    # Stage 3: Prompt Engineering
    logger.info(">>> STAGE 3: Prompt Engineering")
    prompts = generate_prompts(
        scene_plan=scene_plan,
        temperature=temperature_prompts,
    )

    # Assemble final result
    result = ShortsGenerationResult(
        outline=outline,
        scene_plan=scene_plan,
        prompts=prompts,
    )

    logger.info("=" * 80)
    logger.info("Pipeline complete!")
    logger.info(f"  - Story beats: {len(result.outline.beats)}")
    logger.info(f"  - Scenes: {len(result.scene_plan.scenes)}")
    logger.info(f"  - Total shots: {len(result.prompts.shots)}")
    logger.info(f"  - Estimated duration: {result.outline.metadata.estimated_duration_seconds}s")
    logger.info("=" * 80)

    return result
