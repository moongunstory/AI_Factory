"""Character extraction module - extracts characters from stories."""
import json
from typing import Dict, Any, List, Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class CharacterExtractor:
    """Extract character information from expanded stories."""

    SYSTEM_PROMPT = """You are an expert character analyst for visual storytelling.

Your task is to identify and extract all major characters from a story, providing detailed visual descriptions suitable for consistent AI image generation.

For each character, provide:
- name_en: Character's name in English
- role: Their role (protagonist, antagonist, supporting, etc.)
- physical_en: Physical appearance (face, body, age, distinctive features)
- costume_en: Clothing and outfit details
- equipment_en: Tools, weapons, or items they carry (optional)

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
  "characters": [
    {
      "name_en": "Character Name",
      "role": "protagonist",
      "physical_en": "detailed physical appearance",
      "costume_en": "detailed clothing description",
      "equipment_en": "weapons or items (if any)"
    }
  ]
}

INVALID Examples (DO NOT DO THIS):
❌ "Here are the characters: {...}"
❌ "```json\n{...}\n```"
❌ Adding explanatory text before/after JSON
❌ Missing commas, quotes, or brackets

VALID Example (DO THIS):
✓ {"characters":[{"name_en":"Sarah","role":"protagonist","physical_en":"short black hair, athletic build","costume_en":"dusty survival clothes","equipment_en":"pistol"}]}

Guidelines:
- Extract 2-6 major characters (don't include every minor character)
- Descriptions should be visual and concrete
- Use consistent names throughout
- All text must be English only
- If a character has no equipment, use empty string ""

REMEMBER: Output ONLY the JSON object. Nothing else."""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the character extractor.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("CharacterExtractor initialized")

    def extract(
        self,
        expanded_story: str,
        temperature: float = 0.5
    ) -> Dict[str, Any]:
        """Extract characters from an expanded story.

        Args:
            expanded_story: The expanded story in English
            temperature: Sampling temperature (0.0-1.0), lower for consistency

        Returns:
            Dictionary with 'characters' list
        """
        logger.info(f"Extracting characters from story (length: {len(expanded_story)} chars)")

        user_prompt = f"""Story:

{expanded_story}

Extract all major characters from this story and provide detailed visual descriptions for each.
Follow the JSON schema strictly and provide English-only content."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=1024
            )

            validated = self._validate_and_normalize_result(result)
            num_characters = len(validated.get('characters', []))
            logger.info(f"Extracted {num_characters} characters")

            return validated

        except Exception as e:
            logger.error(f"Failed to extract characters: {e}")
            # Return empty result instead of failing completely
            logger.warning("Returning empty character list due to extraction failure")
            return {"characters": []}

    def _validate_and_normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LLM JSON output and ensure required fields are present.

        Args:
            result: Raw LLM output

        Returns:
            Validated and normalized character data
        """
        # Handle case where LLM returns array directly
        if isinstance(result, list):
            logger.warning("LLM returned array instead of object, wrapping in characters key")
            characters = result
        else:
            characters = result.get("characters", [])

        if not isinstance(characters, list):
            logger.error("LLM response missing characters list")
            return {"characters": []}

        valid_characters = []
        for char in characters:
            # Required fields
            required_fields = ["name_en", "role", "physical_en", "costume_en"]
            missing_fields = [field for field in required_fields if field not in char]

            if missing_fields:
                logger.warning(
                    f"Skipping character due to missing fields: {', '.join(missing_fields)}"
                )
                continue

            # Ensure equipment_en exists (optional field)
            if "equipment_en" not in char:
                char["equipment_en"] = ""

            valid_characters.append(char)

        if not valid_characters:
            logger.warning("No valid characters found after validation")

        return {"characters": valid_characters}


def extract_characters(expanded_story: str) -> Dict[str, Any]:
    """Convenience function to extract characters.

    Args:
        expanded_story: Expanded story in English

    Returns:
        Dictionary with character list
    """
    extractor = CharacterExtractor()
    return extractor.extract(expanded_story)
