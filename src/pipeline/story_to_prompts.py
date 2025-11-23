"""Story to prompts conversion pipeline."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..generators.llm import LlamaClient
from ..common.config import Config
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class StoryToPromptsConverter:
    """Convert user stories to AI generation prompts."""

    SYSTEM_PROMPT = """You are an expert AI prompt engineer specializing in creating detailed prompts for image generation, video creation, and audio synthesis.

Your task is to analyze a story and generate structured prompts for creating a short-form video (YouTube Shorts, TikTok, Instagram Reels).

You must respond with ONLY valid JSON in this exact format:
{
  "scenes": [
    {
      "scene_number": 1,
      "description": "Brief scene description",
      "image_prompt": "Detailed image generation prompt (Stable Diffusion style)",
      "duration": 3.0,
      "narration": "Text to be spoken",
      "audio_mood": "background music mood (epic, calm, suspenseful, etc.)"
    }
  ],
  "metadata": {
    "title": "Video title",
    "total_duration": 15.0,
    "style": "Visual style (cinematic, anime, realistic, etc.)",
    "target_platform": "shorts"
  }
}

Guidelines:
- Break the story into 3-5 scenes for a 15-30 second short
- Each image_prompt should be detailed and specific (camera angle, lighting, mood, style)
- Keep narration concise and impactful
- Ensure scenes flow naturally
- Total duration should be 15-30 seconds"""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the converter.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        Config.ensure_output_dirs()

    def convert(
        self,
        story: str,
        style: str = "cinematic",
        duration_target: float = 20.0,
        save_output: bool = True,
    ) -> Dict[str, Any]:
        """Convert a story to structured prompts.

        Args:
            story: The input story text
            style: Visual style preference
            duration_target: Target video duration in seconds
            save_output: Whether to save output to file

        Returns:
            Dictionary containing scenes and metadata
        """
        logger.info(f"Converting story (length: {len(story)} chars)")

        # Build the user prompt
        user_prompt = f"""Story: {story}

Style preference: {style}
Target duration: {duration_target} seconds

Analyze this story and create a structured breakdown for a short-form video."""

        # Generate prompts using LLM
        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=2048,
            )

            logger.info(f"Generated {len(result.get('scenes', []))} scenes")

            # Save output if requested
            if save_output:
                self._save_prompts(result, story)

            return result

        except Exception as e:
            logger.error(f"Failed to convert story: {e}")
            raise

    def _save_prompts(self, prompts: Dict[str, Any], original_story: str) -> Path:
        """Save prompts to file.

        Args:
            prompts: Generated prompts dictionary
            original_story: Original story text

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompts_{timestamp}.json"
        filepath = Config.PROMPTS_DIR / filename

        output = {
            "timestamp": timestamp,
            "original_story": original_story,
            "generated_prompts": prompts,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved prompts to {filepath}")
        return filepath

    def convert_batch(
        self,
        stories: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Convert multiple stories to prompts.

        Args:
            stories: List of story texts
            **kwargs: Additional arguments for convert()

        Returns:
            List of prompt dictionaries
        """
        results = []
        for i, story in enumerate(stories, 1):
            logger.info(f"Processing story {i}/{len(stories)}")
            try:
                result = self.convert(story, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process story {i}: {e}")
                results.append({"error": str(e)})

        return results


def create_prompts_from_story(
    story: str,
    style: str = "cinematic",
    duration: float = 20.0,
) -> Dict[str, Any]:
    """Convenience function to convert a story to prompts.

    Args:
        story: Input story text
        style: Visual style
        duration: Target duration

    Returns:
        Generated prompts dictionary
    """
    converter = StoryToPromptsConverter()
    return converter.convert(story, style=style, duration_target=duration)
