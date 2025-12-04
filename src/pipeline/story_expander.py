"""Story expansion module - converts simple ideas into full short-form stories."""
from typing import Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class StoryExpander:
    """Expand simple story ideas into detailed 1-2 minute short stories."""

    SYSTEM_PROMPT = """You are a creative storytelling AI specialized in creating engaging short-form video content (YouTube Shorts, TikTok, Instagram Reels).

Your task is to take a simple story idea and expand it into a compelling narrative suitable for short-form video.

Guidelines:
- Story should be rich and detailed (approximately 300-500 words in English)
- Create a clear beginning, middle, and end with well-developed scenes
- Include vivid visual descriptions that work well for video
- Make it engaging and emotionally resonant
- Develop the narrative with sufficient depth for 20+ visual scenes
- Include atmospheric details, character emotions, and environmental descriptions
- Write ENTIRELY in English

CRITICAL - PARAGRAPH STRUCTURE REQUIREMENTS:
- Divide the story into clear paragraphs (2-4 sentences per paragraph)
- Add a blank line between paragraphs for readability
- Create new paragraphs when there are changes in:
  * Action or movement
  * Emotion or mood
  * Scene or background
  * Character focus or perspective
- Long sentences should be naturally broken into shorter, readable sentences
- Each paragraph should represent a distinct moment or beat in the story

Example structure:
Paragraph 1: Opening scene (2-3 sentences)

Paragraph 2: Character action or movement (2-4 sentences)

Paragraph 3: Emotional shift or new development (2-3 sentences)

Respond with ONLY the expanded story in English with proper paragraph breaks. No additional explanations or metadata."""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the story expander.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("StoryExpander initialized")

    def expand(self, simple_idea: str, temperature: float = 0.7) -> str:
        """Expand a simple story idea into a full short story.

        Args:
            simple_idea: Simple story idea from user (in English)
            temperature: Sampling temperature for creativity

        Returns:
            Expanded story in English
        """
        logger.info(f"Expanding story idea (length: {len(simple_idea)} chars)")

        user_prompt = f"""Simple story idea: {simple_idea}

Expand this into a compelling, detailed story in English. Create a rich narrative with vivid descriptions, multiple scenes, and emotional depth.

IMPORTANT:
- The story should be substantial enough to generate 20+ visual scenes
- Divide the story into clear paragraphs (2-4 sentences each)
- Add blank lines between paragraphs
- Create new paragraphs for each change in action, emotion, scene, or character focus
- Make each paragraph represent a distinct visual moment that can be turned into a scene"""

        try:
            expanded_story = self.llm.generate(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048,  # Increased from 1024 to support longer stories
            )

            # Clean up the output
            expanded_story = expanded_story.strip()

            logger.info(f"Story expanded successfully (output length: {len(expanded_story)} chars)")
            return expanded_story

        except Exception as e:
            logger.error(f"Failed to expand story: {e}")
            raise


def expand_story(simple_idea: str) -> str:
    """Convenience function to expand a story.

    Args:
        simple_idea: Simple story idea in English

    Returns:
        Expanded story in English
    """
    expander = StoryExpander()
    return expander.expand(simple_idea)
