"""Story expansion module - converts simple ideas into full short-form stories."""
from typing import Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class StoryExpander:
    """Expand simple story ideas into detailed 1-2 minute short stories."""

    SYSTEM_PROMPT = """You are a creative storytelling AI specialized in creating engaging short-form video content (YouTube Shorts, TikTok, Instagram Reels).

Your task is to take a simple story idea and expand it into a compelling 1-2 minute narrative suitable for short-form video.

Guidelines:
- Story should be 1-2 minutes when narrated (approximately 150-300 words in Korean)
- Create a clear beginning, middle, and end
- Include vivid visual descriptions that work well for video
- Make it engaging and emotionally resonant
- Keep the pacing fast and dynamic
- Write ENTIRELY in Korean (한국어로만 작성)

Respond with ONLY the expanded story in Korean. No additional explanations or metadata."""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the story expander.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("StoryExpander initialized")

    def expand(self, simple_idea: str, temperature: float = 0.8) -> str:
        """Expand a simple story idea into a full short story.

        Args:
            simple_idea: Simple story idea from user
            temperature: Sampling temperature for creativity (0.0-1.0)

        Returns:
            Expanded story in Korean
        """
        logger.info(f"Expanding story idea (length: {len(simple_idea)} chars)")

        user_prompt = f"""Simple story idea: {simple_idea}

Expand this into a compelling 1-2 minute story in Korean. Make it vivid, engaging, and perfect for short-form video."""

        try:
            expanded_story = self.llm.generate(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=1024,
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
        simple_idea: Simple story idea

    Returns:
        Expanded story in Korean
    """
    expander = StoryExpander()
    return expander.expand(simple_idea)
