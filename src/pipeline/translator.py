"""Translation module - translates English prompts to Korean."""
from typing import Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class Translator:
    """Translate English Stable Diffusion prompts to Korean."""

    SYSTEM_PROMPT = """You are a professional translator specializing in AI image generation prompts.

Your task is to translate Stable Diffusion prompts from English to Korean while preserving their meaning and technical terms.

Guidelines:
- Translate the overall meaning and descriptions to Korean
- Keep technical terms and style tags that are commonly used in English (like "4k", "masterpiece", "cinematic")
- Make it readable and natural in Korean
- Respond with ONLY the translated text, no additional explanations"""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the translator.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("Translator initialized")

    def translate(self, english_prompt: str, temperature: float = 0.3) -> str:
        """Translate an English prompt to Korean.

        Args:
            english_prompt: English Stable Diffusion prompt
            temperature: Sampling temperature (lower for more consistent translation)

        Returns:
            Translated prompt in Korean
        """
        logger.info(f"Translating prompt (length: {len(english_prompt)} chars)")

        user_prompt = f"""English prompt: {english_prompt}

Translate this to Korean while keeping technical terms and style tags."""

        try:
            translated = self.llm.generate(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=512,
            )

            translated = translated.strip()
            logger.info(f"Translation completed (output length: {len(translated)} chars)")
            return translated

        except Exception as e:
            logger.error(f"Failed to translate: {e}")
            raise


def translate_prompt(english_prompt: str) -> str:
    """Convenience function to translate a prompt.

    Args:
        english_prompt: English prompt

    Returns:
        Korean translation
    """
    translator = Translator()
    return translator.translate(english_prompt)
