"""Prompt generation module - converts stories into Stable Diffusion prompts.

This module implements a multi-layer prompt generation pipeline:
1. Story Layer: Summarizes story into plot beats
2. Film Layer: Analyzes emotion and applies cinematic grammar
3. Camera Layer: Assigns specific camera techniques
4. Prompt Layer: Builds final prompts with all layers integrated
"""
import re
from typing import List, Dict, Any, Optional, Union
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger
from .film_layer import FilmLayer
from .camera_layer import CameraLayer

logger = setup_logger(__name__)


class PromptGenerator:
    """Generate Stable Diffusion prompts from stories."""

    SYSTEM_PROMPT = """You are an expert AI prompt engineer specializing in Stable Diffusion image generation prompts.

Your task is to transform a list of plot beats into a structured sequence of visual scenes and create detailed Stable Diffusion prompts for each scene.

Stable Diffusion prompt format:
- Use comma-separated tags and descriptions
- Include: subject, action, setting, lighting, style, quality tags
- Example: "a lonely robot in abandoned space station, dark corridor, blue emergency lights, cinematic lighting, detailed mechanical parts, sci-fi atmosphere, digital art, highly detailed, 4k, masterpiece"

Scene design principles:
- Determine the number of scenes naturally from the major events in the plot beats.
- Each scene should capture one clear visual event (danger, discovery, battle, decision, dialogue, twist, etc.).
- Do not pad scenes or force a fixed count. Do not remove important events to hit a target number.
- For long battle-royale/action stories, it is common (but not mandatory) for 15-30+ scenes to appear naturally.

Duration guidelines:
- Typical scene duration: 2.0-4.0 seconds.
- Key turning points (game start, climactic fight, final victory, etc.): up to 4.0-6.0 seconds.
- Estimated total duration should roughly fall within 45-75 seconds, based on the sum of all scene durations (guideline, not a hard limit).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL JSON OUTPUT REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. OUTPUT ONLY PURE JSON - NO OTHER TEXT
2. NO explanations, NO comments, NO markdown
3. NO text before or after the JSON object
4. START with { and END with }
5. MUST be valid, parseable JSON

Required JSON Schema:
{
  "scenes": [
    {
      "scene_number": 1,
      "summary": "Short English summary of the scene",
      "description": "More detailed English description of what happens in this scene",
      "prompt_en": "Stable Diffusion prompt in English",
      "duration": 3.5,
      "characters": [
        {
          "id": "sarah",
          "role": "protagonist",
          "description": "short black hair, dusty survival clothes, pistol in hand"
        }
      ]
    }
  ],
  "total_scenes": 18,
  "estimated_duration": 64.0
}

INVALID Examples (DO NOT DO THIS):
❌ "Here is the result: {...}"
❌ "```json\n{...}\n```"
❌ Adding explanatory text before/after JSON
❌ Missing commas, quotes, or brackets

VALID Example (DO THIS):
✓ {"scenes":[{"scene_number":1,"summary":"scene summary","description":"scene description","prompt_en":"prompt","duration":3.5}],"total_scenes":1,"estimated_duration":3.5}

Content Guidelines:
- Prompts should be detailed, visual, and cinematic.
- Use high-quality style tags suitable for Stable Diffusion.
- All text must be English only—do not include Korean or any other language.

REMEMBER: Output ONLY the JSON object. Nothing else."""

    def __init__(
        self,
        llm_client: Optional[LlamaClient] = None,
        enable_film_layer: bool = True,
        enable_camera_layer: bool = True
    ):
        """Initialize the prompt generator.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
            enable_film_layer: Enable Film Layer for cinematic grammar (default: True)
            enable_camera_layer: Enable Camera Layer for technical specs (default: True)
        """
        self.llm = llm_client or LlamaClient()
        self.enable_film_layer = enable_film_layer
        self.enable_camera_layer = enable_camera_layer

        # Initialize multi-layer pipeline
        self.film_layer = FilmLayer() if enable_film_layer else None
        self.camera_layer = CameraLayer() if enable_camera_layer else None

        logger.info(
            f"PromptGenerator initialized (film_layer={enable_film_layer}, "
            f"camera_layer={enable_camera_layer})"
        )

    def generate(
        self,
        expanded_story: str,
        temperature: float = 0.7,
        global_style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Stable Diffusion prompts from a story using multi-layer pipeline.

        Pipeline stages:
        1) Story Layer: Summarize the story into plot beats
        2) Story Layer: Convert beats into basic scene descriptions (LLM)
        3) Film Layer: Analyze scene emotions and apply cinematic grammar
        4) Camera Layer: Assign specific camera techniques
        5) Prompt Layer: Build enhanced prompts with all layers integrated

        Args:
            expanded_story: The expanded story in English
            temperature: Sampling temperature (0.0-1.0)
            global_style: Optional global visual style dict (from visual_styles.py)

        Returns:
            Dictionary containing scenes with enhanced prompts and metadata
        """
        logger.info(f"Generating prompts for story (length: {len(expanded_story)} chars)")
        logger.info(f"Multi-layer pipeline: Film={self.enable_film_layer}, Camera={self.enable_camera_layer}")

        # ====================================================================
        # Stage 1: Story Layer - Summarize into plot beats
        # ====================================================================
        beats = self._summarize_story_to_beats(expanded_story)
        beats_text = "\n".join([f"{idx + 1}) {beat}" for idx, beat in enumerate(beats)])

        # ====================================================================
        # Stage 2: Story Layer - Generate basic scene descriptions
        # ====================================================================
        user_prompt = f"""Here is the story broken into plot beats:

{beats_text}

Based on these beats, create a sequence of visual scenes suitable for a vertical short-form video.
Each scene should represent one beat or a small group of adjacent beats while keeping a coherent flow.
Follow the JSON schema strictly and provide English-only content."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048
            )

            validated = self._validate_and_normalize_result(result)
            scenes = validated.get('scenes', [])
            num_scenes = len(scenes)
            logger.info(f"Generated {num_scenes} base scenes from story beats")

            # ====================================================================
            # Stage 3: Film Layer - Apply cinematic grammar
            # ====================================================================
            if self.enable_film_layer and self.film_layer:
                logger.info("Applying Film Layer (cinematic grammar analysis)...")
                scenes = self.film_layer.batch_analyze_scenes(scenes)
                logger.info(f"✓ Film layer applied to {len(scenes)} scenes")

            # ====================================================================
            # Stage 4: Camera Layer - Assign camera techniques
            # ====================================================================
            if self.enable_camera_layer and self.camera_layer:
                logger.info("Applying Camera Layer (shot types, angles, lenses)...")
                scenes = self.camera_layer.batch_assign_cameras(scenes)

                # Log variety statistics
                stats = self.camera_layer.get_camera_variety_stats()
                logger.info(
                    f"✓ Camera layer applied: {stats.get('unique_shot_types', 0)} unique shot types, "
                    f"{stats.get('unique_angles', 0)} unique angles"
                )

            # ====================================================================
            # Stage 5: Prompt Layer - Build enhanced prompts
            # ====================================================================
            logger.info("Building enhanced prompts with Film + Camera layers...")
            for scene in scenes:
                # Build enhanced prompt incorporating all layers
                enhanced_prompt = self._build_enhanced_prompt(
                    scene=scene,
                    global_style=global_style
                )
                scene["prompt_en"] = enhanced_prompt

            logger.info(f"✓ Enhanced prompts generated for {num_scenes} scenes")

            # Update validated result
            validated['scenes'] = scenes

            return validated

        except Exception as e:
            logger.error(f"Failed to generate prompts: {e}")
            raise

    def _summarize_story_to_beats(
        self,
        expanded_story: str,
        temperature: float = 0.5,
    ) -> List[str]:
        """Summarize a full story into concise plot beats.

        Args:
            expanded_story: Full story text in English
            temperature: Sampling temperature for summarization

        Returns:
            List of plot beat strings in English

        Raises:
            RuntimeError: If no beats can be extracted
        """
        system_prompt = (
            "You are an expert story analyst. Convert the following story into 8-20 concise "
            "English plot beats that capture the key events. Return only a bullet list or "
            "numbered list without any additional commentary."
        )
        user_prompt = f"""Story:
{expanded_story}

Summarize into 8-20 plot beats (one sentence each)."""

        logger.info("Summarizing story into plot beats")
        output = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=1024,
        )

        beats: List[str] = []
        for line in output.splitlines():
            cleaned = line.strip()
            cleaned = re.sub(r"^[\d\-•]+[\).\-\s]*", "", cleaned)
            if cleaned:
                beats.append(cleaned)

        if not beats:
            logger.error("No plot beats generated from summary step")
            raise RuntimeError("Failed to summarize story into plot beats")

        logger.info(f"Generated {len(beats)} plot beats for scene construction")
        return beats

    def _validate_and_normalize_result(self, result: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate LLM JSON output and ensure required fields are consistent."""
        # Handle case where LLM returns array directly instead of object with "scenes" key
        if isinstance(result, list):
            logger.warning("LLM returned array instead of object, wrapping in scenes key")
            scenes = result
        else:
            scenes = result.get("scenes")

        if not scenes or not isinstance(scenes, list):
            logger.error("LLM response missing scenes list")
            raise RuntimeError("LLM did not return any scenes")

        valid_scenes = []
        for scene in scenes:
            missing_fields = [
                field for field in ("scene_number", "prompt_en", "duration")
                if field not in scene
            ]
            if missing_fields:
                logger.warning(
                    "Skipping scene due to missing fields: %s", ", ".join(missing_fields)
                )
                continue
            valid_scenes.append(scene)

        if len(valid_scenes) < 2:
            logger.error("Insufficient valid scenes after validation")
            raise RuntimeError("LLM returned fewer than 2 valid scenes")

        # Sort by scene_number to ensure stable ordering
        valid_scenes.sort(key=lambda s: s.get("scene_number", 0))

        # Recalculate durations to guard against missing estimated_duration
        total_duration = 0.0
        for scene in valid_scenes:
            try:
                total_duration += float(scene.get("duration", 0.0))
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid duration type for scene %s; defaulting to 0",
                    scene.get("scene_number"),
                )
                scene["duration"] = 0.0

        normalized = {
            "scenes": valid_scenes,
            "total_scenes": len(valid_scenes),
            "estimated_duration": float(total_duration),
        }

        # Preserve optional keys from the model output if present
        for key in ("summary", "description", "title"):
            if key in result:
                normalized[key] = result[key]

        return normalized

    def regenerate_scene(
        self,
        scene_number: int,
        scene_description: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Regenerate a single scene prompt.

        Args:
            scene_number: The scene number to regenerate
            scene_description: English description of the scene
            temperature: Sampling temperature

        Returns:
            Dictionary with regenerated scene data
        """
        logger.info(f"Regenerating scene {scene_number}")

        regenerate_prompt = f"""Scene {scene_number} description: {scene_description}

Create a new Stable Diffusion prompt for this scene.

CRITICAL: Output ONLY valid JSON. No text before or after.

Required JSON format:
{{
  "scene_number": {scene_number},
  "description": "Scene description in English",
  "prompt_en": "New Stable Diffusion prompt in English",
  "duration": 5.0
}}"""

        regenerate_system = """You are a Stable Diffusion prompt expert.

CRITICAL: You MUST output ONLY valid JSON. No explanations, no markdown, no extra text.
Start with { and end with }. Nothing before or after."""

        try:
            result = self.llm.generate_json(
                prompt=regenerate_prompt,
                system_prompt=regenerate_system,
                temperature=temperature,
                max_tokens=512
            )

            logger.info(f"Scene {scene_number} regenerated successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to regenerate scene {scene_number}: {e}")
            raise


    def _build_enhanced_prompt(
        self,
        scene: Dict[str, Any],
        global_style: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced prompt incorporating Film + Camera layers.

        Constructs a structured Stable Diffusion prompt in this format:
        [Scene Description] + [Camera Specs] + [Film Style] + [Global Style] + [Quality Tags]

        Args:
            scene: Scene dictionary with description, film_style, camera_style
            global_style: Optional global visual style settings

        Returns:
            Enhanced prompt string for Stable Diffusion
        """
        components = []

        # 1. Base scene description (from LLM)
        base_description = scene.get("description") or scene.get("summary", "")
        if base_description:
            components.append(base_description)

        # 2. Camera specifications (if Camera Layer enabled)
        if "camera_style" in scene:
            camera = scene["camera_style"]
            camera_spec = (
                f"{camera.get('shot_type_name', '')}, "
                f"{camera.get('angle_description', '')}, "
                f"{camera.get('lens_description', '')}, "
                f"{camera.get('movement_description', '')}"
            )
            components.append(camera_spec)

        # 3. Film style (lighting, color, atmosphere)
        if "film_style" in scene:
            film = scene["film_style"]

            # Lighting
            if film.get("lighting"):
                components.append(film["lighting"])

            # Color grading
            if film.get("color_grading"):
                components.append(film["color_grading"])

            # Composition style
            if film.get("composition"):
                components.append(film["composition"])

            # Atmosphere
            if film.get("atmosphere"):
                components.append(f"{film['atmosphere']} atmosphere")

        # 4. Global visual style (theme-wide consistency)
        if global_style:
            # Add global texture/quality if not already covered by film style
            if global_style.get("texture"):
                components.append(global_style["texture"])

            # Add consistency tags for cross-scene coherence
            if global_style.get("consistency_tags"):
                components.append(global_style["consistency_tags"])

            # Add quality tags
            if global_style.get("quality_tags"):
                components.append(global_style["quality_tags"])
        else:
            # Default quality tags if no global style
            components.append(
                "masterpiece, best quality, ultra detailed, 8k, "
                "photorealistic, cinematic composition"
            )

        # Combine all components with proper formatting
        enhanced_prompt = ", ".join(filter(None, components))

        return enhanced_prompt


def generate_prompts(expanded_story: str) -> Dict[str, Any]:
    """Convenience function to generate prompts.

    Args:
        expanded_story: Expanded story in English

    Returns:
        Dictionary with scene prompts
    """
    generator = PromptGenerator()
    return generator.generate(expanded_story)
