"""Advanced scene generation module for 20-25 high-quality scenes with global consistency."""
import json
from typing import List, Dict, Any, Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger
from .visual_styles import VisualStyleDefinitions

logger = setup_logger(__name__)


class AdvancedSceneGenerator:
    """Generate 20-25 cinematic scenes with global character sheets and visual consistency."""

    # System prompt for story beats generation
    STORY_BEATS_SYSTEM_PROMPT = """You are an expert story analyst and narrative designer.

Your task is to analyze a full story and break it down into 10-15 major story beats.

Story beats are the key narrative moments that drive the plot forward. Each beat should represent a significant event, decision, or turning point.

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
  "story_summary": "One paragraph summary of the full narrative",
  "beats": [
    {
      "beat_number": 1,
      "description": "The warrior prepares for the journey in darkness",
      "narrative_function": "setup/rising_action/climax/resolution"
    }
  ],
  "total_beats": 12
}

Guidelines:
- Create 10-15 story beats
- Each beat should be a complete narrative moment
- Include clear beginning, rising action, climax, and resolution beats
- Beats should flow naturally and build tension
- Descriptions should be concise but clear

REMEMBER: Output ONLY the JSON object. Nothing else."""

    # System prompt for character sheet generation
    CHARACTER_SHEET_SYSTEM_PROMPT = """You are an expert character designer for visual media.

Your task is to create detailed character sheets for the main characters in a story.

Character sheets should include:
- Physical appearance (face, body, distinctive features)
- Costume/clothing design
- Equipment/weapons/accessories
- Personality traits that affect visual presentation
- Unique identifying elements for consistency

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
      "name": "Warrior",
      "role": "protagonist",
      "physical": "Tall muscular man, battle-scarred face, short dark hair, piercing blue eyes",
      "costume": "Dark leather armor with silver plates, worn travel cloak, heavy boots",
      "equipment": "Ancient rune-engraved longsword, small shield with dragon emblem",
      "personality_visual": "Determined expression, confident stance, weathered appearance",
      "consistency_tags": "same warrior, same armor design, same sword, consistent character"
    }
  ]
}

Guidelines:
- Identify 2-4 main characters from the story
- Be VERY specific and detailed
- Include elements that ensure visual consistency
- Focus on visually distinctive features
- Add consistency tags for Stable Diffusion

REMEMBER: Output ONLY the JSON object. Nothing else."""

    # System prompt for scene generation
    SCENE_GENERATION_SYSTEM_PROMPT = """You are an expert cinematic director and Stable Diffusion prompt engineer.

Your task is to convert story beats into 20-25 detailed cinematic scenes with high-quality Stable Diffusion prompts.

Each scene must follow this 7-part structure:
1. [Subject: character + action]
2. [Environment / background]
3. [Cinematic motion or action details]
4. [Lighting]
5. [Camera / composition]
6. [Style details]
7. [Global Visual Style - will be appended automatically]

Scene Duration Rules:
- Action/combat/travel scenes: 2-3 seconds
- Emotional/atmospheric scenes: 4-5 seconds
- Climax/resolution scenes: 5-6 seconds
- Total duration: 50-70 seconds (average ~60 seconds)

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
      "duration": 3.0,
      "description": "The warrior stands at the edge of the dark forest, gripping his sword",
      "prompt_en": "detailed high-quality prompt following 7-part structure",
      "prompt_ko": "한국어 번역"
    }
  ],
  "total_scenes": 23,
  "total_duration": 62.5
}

Critical Rules:
- MUST generate exactly 20-25 scenes
- Total duration MUST be 50-70 seconds
- Each prompt must follow the 7-part structure
- Character appearance must match the character sheet exactly
- Visual style must remain consistent across all scenes
- Never use generic or vague descriptions
- Every scene must be distinct and cinematic

REMEMBER: Output ONLY the JSON object. Nothing else."""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize the advanced scene generator.

        Args:
            llm_client: Optional LlamaClient instance. If None, creates a new one.
        """
        self.llm = llm_client or LlamaClient()
        logger.info("AdvancedSceneGenerator initialized")

    def generate_story_beats(
        self,
        expanded_story: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate 10-15 story beats from expanded story.

        Args:
            expanded_story: Full expanded story
            temperature: Sampling temperature

        Returns:
            Dictionary with story summary and beats
        """
        logger.info("Generating story beats...")

        user_prompt = f"""Story:
{expanded_story}

Analyze this story and break it down into 10-15 major story beats.
Create a clear narrative arc with proper pacing."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.STORY_BEATS_SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048,
            )

            num_beats = len(result.get('beats', []))
            logger.info(f"Generated {num_beats} story beats")

            return result

        except Exception as e:
            logger.error(f"Failed to generate story beats: {e}")
            raise

    def generate_character_sheet(
        self,
        expanded_story: str,
        story_beats: Dict[str, Any],
        theme: str = "cinematic_realism",
        temperature: float = 0.6
    ) -> Dict[str, Any]:
        """Generate detailed character sheets for main characters.

        Args:
            expanded_story: Full expanded story
            story_beats: Story beats dictionary
            theme: Visual theme
            temperature: Sampling temperature

        Returns:
            Dictionary with character sheets
        """
        logger.info("Generating character sheets...")

        # Get theme style for context
        style = VisualStyleDefinitions.get_style(theme)
        theme_context = f"Visual theme: {style['name']} - {style['atmosphere']} atmosphere"

        user_prompt = f"""Story:
{expanded_story}

Story Summary:
{story_beats.get('story_summary', '')}

{theme_context}

Create detailed character sheets for the 2-4 main characters in this story.
Ensure the character designs fit the visual theme and are highly specific for consistency."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.CHARACTER_SHEET_SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048,
            )

            num_chars = len(result.get('characters', []))
            logger.info(f"Generated {num_chars} character sheets")

            return result

        except Exception as e:
            logger.error(f"Failed to generate character sheets: {e}")
            raise

    def generate_scenes(
        self,
        expanded_story: str,
        story_beats: Dict[str, Any],
        character_sheets: Dict[str, Any],
        theme: str = "cinematic_realism",
        target_duration: float = 60.0,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate 20-25 detailed scenes with high-quality prompts.

        Args:
            expanded_story: Full expanded story
            story_beats: Story beats dictionary
            character_sheets: Character sheets dictionary
            theme: Visual theme
            target_duration: Target total duration in seconds (50-70)
            temperature: Sampling temperature

        Returns:
            Dictionary with scenes
        """
        logger.info(f"Generating 20-25 scenes (target duration: {target_duration}s)...")

        # Get global visual style
        global_style = VisualStyleDefinitions.get_global_style_prompt(theme)

        # Prepare character descriptions for consistency
        char_descriptions = []
        for char in character_sheets.get('characters', []):
            desc = (
                f"- {char.get('name', 'Unknown')} ({char.get('role', 'character')}): "
                f"{char.get('physical', '')}, {char.get('costume', '')}"
            )
            equipment = char.get('equipment', '')
            if equipment:
                desc += f", {equipment}"
            consistency = char.get('consistency_tags', '')
            if consistency:
                desc += f". Consistency: {consistency}"
            char_descriptions.append(desc)

        characters_context = "\n".join(char_descriptions)

        # Prepare beats summary
        beats_list = []
        for beat in story_beats.get('beats', []):
            beats_list.append(f"Beat {beat['beat_number']}: {beat['description']}")

        beats_context = "\n".join(beats_list)

        user_prompt = f"""Story:
{expanded_story}

Story Beats:
{beats_context}

Character Sheets (MUST maintain exact consistency):
{characters_context}

Global Visual Style:
{global_style}

Target Duration: {target_duration} seconds
Required Scenes: 20-25

Generate 20-25 cinematic scenes following these requirements:
1. Expand the {len(story_beats.get('beats', []))} story beats into 20-25 detailed scenes
2. Each scene must follow the 7-part prompt structure
3. Character appearances must match the character sheets EXACTLY
4. All scenes must maintain visual consistency
5. Scene durations should follow the rules (action: 2-3s, emotional: 4-5s, climax: 5-6s)
6. Total duration must be approximately {target_duration} seconds
7. Every scene must be unique and cinematic
8. The global visual style will be appended to each prompt automatically

Create compelling, visually rich scenes that flow naturally like a single video."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SCENE_GENERATION_SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=4096,
            )

            # Append global style to each prompt
            if 'scenes' in result:
                for scene in result['scenes']:
                    if 'prompt_en' in scene:
                        # Append global style to prompt
                        scene['prompt_en'] = f"{scene['prompt_en']}, {global_style}"

            num_scenes = len(result.get('scenes', []))
            total_duration = result.get('total_duration', 0)
            logger.info(f"Generated {num_scenes} scenes (total duration: {total_duration}s)")

            return result

        except Exception as e:
            logger.error(f"Failed to generate scenes: {e}")
            raise

    def generate_complete_scene_sequence(
        self,
        story_idea: str,
        theme: str = "cinematic_realism",
        target_duration: float = 60.0,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate complete scene sequence with all components.

        This is the main entry point that orchestrates the entire pipeline.

        Args:
            story_idea: Simple story idea
            theme: Visual theme
            target_duration: Target total duration in seconds
            temperature: Sampling temperature

        Returns:
            Complete dictionary with all components
        """
        logger.info("=== Starting Complete Scene Generation Pipeline ===")
        logger.info(f"Theme: {theme}, Target Duration: {target_duration}s")

        # Import story expander here to avoid circular imports
        from .story_expander import StoryExpander

        try:
            # Step 1: Expand story
            logger.info("Step 1: Expanding story...")
            expander = StoryExpander(self.llm)
            expanded_story = expander.expand(story_idea, temperature=0.8)

            # Step 2: Generate story beats
            logger.info("Step 2: Generating story beats...")
            story_beats = self.generate_story_beats(expanded_story, temperature=0.7)

            # Step 3: Generate character sheets
            logger.info("Step 3: Generating character sheets...")
            character_sheets = self.generate_character_sheet(
                expanded_story,
                story_beats,
                theme,
                temperature=0.6
            )

            # Step 4: Generate scenes
            logger.info("Step 4: Generating 20-25 scenes...")
            scenes_result = self.generate_scenes(
                expanded_story,
                story_beats,
                character_sheets,
                theme,
                target_duration,
                temperature=0.7
            )

            # Step 5: Get global visual style
            logger.info("Step 5: Preparing global visual style...")
            style = VisualStyleDefinitions.get_style(theme)
            global_style = VisualStyleDefinitions.get_global_style_prompt(theme)

            # Compile final result
            final_result = {
                "story_idea": story_idea,
                "theme": theme,
                "expanded_story": expanded_story,
                "story_summary": story_beats.get('story_summary', ''),
                "story_beats": story_beats.get('beats', []),
                "characters": character_sheets.get('characters', []),
                "global_visual_style": {
                    "theme": theme,
                    "theme_name": style['name'],
                    "color_palette": style['color_palette'],
                    "lighting": style['lighting'],
                    "camera": style['camera'],
                    "texture": style['texture'],
                    "atmosphere": style['atmosphere'],
                    "consistency_tags": style['consistency_tags'],
                    "quality_tags": style['quality_tags'],
                    "full_prompt": global_style
                },
                "scenes": scenes_result.get('scenes', []),
                "total_scenes": len(scenes_result.get('scenes', [])),
                "total_duration": scenes_result.get('total_duration', 0),
                "target_duration": target_duration,
            }

            logger.info("=== Scene Generation Pipeline Complete ===")
            logger.info(f"Generated {final_result['total_scenes']} scenes")
            logger.info(f"Total duration: {final_result['total_duration']}s")

            return final_result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

    def regenerate_scene(
        self,
        scene_number: int,
        scene_description: str,
        character_sheets: Dict[str, Any],
        global_style: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Regenerate a single scene.

        Args:
            scene_number: Scene number to regenerate
            scene_description: Description of the scene
            character_sheets: Character sheets for consistency
            global_style: Global visual style prompt
            temperature: Sampling temperature

        Returns:
            Regenerated scene dictionary
        """
        logger.info(f"Regenerating scene {scene_number}...")

        # Prepare character descriptions
        char_descriptions = []
        for char in character_sheets.get('characters', []):
            desc = f"{char.get('name', 'Unknown')}: {char.get('physical', '')}, {char.get('costume', '')}"
            equipment = char.get('equipment', '')
            if equipment:
                desc += f", {equipment}"
            char_descriptions.append(desc)

        characters_context = "\n".join(char_descriptions)

        regenerate_system = """You are a Stable Diffusion prompt expert.

Create a high-quality scene prompt following the 7-part structure:
1. [Subject: character + action]
2. [Environment / background]
3. [Cinematic motion or action details]
4. [Lighting]
5. [Camera / composition]
6. [Style details]
7. [Global Visual Style - provided separately]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: You MUST output ONLY valid JSON. No explanations, no markdown, no extra text.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Required JSON format:
{
  "scene_number": N,
  "duration": X.X,
  "description": "scene description",
  "prompt_en": "detailed prompt",
  "prompt_ko": "한국어 번역"
}"""

        regenerate_prompt = f"""Scene {scene_number}: {scene_description}

Characters (maintain exact consistency):
{characters_context}

Create a detailed Stable Diffusion prompt for this scene.
Follow the 7-part structure and ensure character consistency."""

        try:
            result = self.llm.generate_json(
                prompt=regenerate_prompt,
                system_prompt=regenerate_system,
                temperature=temperature,
                max_tokens=1024,
            )

            # Append global style
            if 'prompt_en' in result:
                result['prompt_en'] = f"{result['prompt_en']}, {global_style}"

            logger.info(f"Scene {scene_number} regenerated successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to regenerate scene {scene_number}: {e}")
            raise


def generate_advanced_scenes(
    story_idea: str,
    theme: str = "cinematic_realism",
    target_duration: float = 60.0
) -> Dict[str, Any]:
    """Convenience function for complete scene generation.

    Args:
        story_idea: Simple story idea
        theme: Visual theme
        target_duration: Target duration in seconds

    Returns:
        Complete scene sequence dictionary
    """
    generator = AdvancedSceneGenerator()
    return generator.generate_complete_scene_sequence(
        story_idea,
        theme,
        target_duration
    )
