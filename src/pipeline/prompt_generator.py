"""Prompt generation module - converts stories into Stable Diffusion prompts."""
import json
from typing import List, Dict, Any, Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class PromptGenerator:
    """Generate Stable Diffusion prompts from stories."""

    SYSTEM_PROMPT = """You are an expert AI prompt engineer specializing in Stable Diffusion image generation prompts.

Your task is to analyze a Korean story and break it down into visual scenes, creating detailed Stable Diffusion prompts for each scene.

Stable Diffusion prompt format:
- Use comma-separated tags and descriptions
- Include: subject, action, setting, lighting, style, quality tags
- Example: "a lonely robot in abandoned space station, dark corridor, blue emergency lights, cinematic lighting, detailed mechanical parts, sci-fi atmosphere, digital art, highly detailed, 4k, masterpiece"

You must respond with ONLY valid JSON in this exact format:
{
  "scenes": [
    {
      "scene_number": 1,
      "description_kr": "장면 설명 (한국어)",
      "prompt_en": "Stable Diffusion prompt in English",
      "duration": 3.5
    }
  ],
  "total_scenes": 5,
  "estimated_duration": 60.0
}

Guidelines:
- Determine the optimal number of scenes (usually 8-15 for a 1-2 minute video)
- Each scene should be 5-10 seconds
- Prompts should be detailed and visually descriptive
- Use cinematic and high-quality style tags
- Scene descriptions (description_kr) in Korean
- Prompts (prompt_en) in English for Stable Diffusion"""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the prompt generator.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("PromptGenerator initialized")

    def generate(
        self,
        expanded_story: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate Stable Diffusion prompts from a story.

        Args:
            expanded_story: The expanded story in Korean
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dictionary containing scenes with prompts
        """
        logger.info(f"Generating prompts for story (length: {len(expanded_story)} chars)")

        user_prompt = f"""Story (in Korean):
{expanded_story}

Analyze this story and create a scene breakdown with Stable Diffusion prompts.
Determine the optimal number of scenes and create detailed prompts for each."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048,
            )

            num_scenes = len(result.get('scenes', []))
            logger.info(f"Generated {num_scenes} scene prompts")

            return result

        except Exception as e:
            logger.error(f"Failed to generate prompts: {e}")
            raise

    def regenerate_scene(
        self,
        scene_number: int,
        scene_description: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Regenerate a single scene prompt.

        Args:
            scene_number: The scene number to regenerate
            scene_description: Korean description of the scene
            temperature: Sampling temperature

        Returns:
            Dictionary with regenerated scene data
        """
        logger.info(f"Regenerating scene {scene_number}")

        regenerate_prompt = f"""Scene {scene_number} description: {scene_description}

Create a new Stable Diffusion prompt for this scene. Respond with JSON:
{{
  "scene_number": {scene_number},
  "description_kr": "장면 설명 (한국어)",
  "prompt_en": "New Stable Diffusion prompt in English",
  "duration": 5.0
}}"""

        try:
            result = self.llm.generate_json(
                prompt=regenerate_prompt,
                system_prompt="You are a Stable Diffusion prompt expert. Create detailed, high-quality prompts.",
                temperature=temperature,
                max_tokens=512,
            )

            logger.info(f"Scene {scene_number} regenerated successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to regenerate scene {scene_number}: {e}")
            raise


def generate_prompts(expanded_story: str) -> Dict[str, Any]:
    """Convenience function to generate prompts.

    Args:
        expanded_story: Expanded story in Korean

    Returns:
        Dictionary with scene prompts
    """
    generator = PromptGenerator()
    return generator.generate(expanded_story)
