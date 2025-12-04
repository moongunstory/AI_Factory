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

Your task is to analyze a full story and break it down into 12-18 major story beats.

Story beats are the key narrative moments that drive the plot forward. Each beat should represent a significant event, decision, or turning point.

CRITICAL: Analyze the story's paragraph structure to identify beats:
- Each paragraph often represents a distinct moment or beat
- Changes in action, emotion, scene, or character focus indicate new beats
- Break down the narrative into granular, detailed beats for comprehensive scene coverage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CRITICAL JSON OUTPUT REQUIREMENTS 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ YOU MUST OUTPUT VALID JSON ONLY - NOTHING ELSE ⚠️

❌ DO NOT output like this (WRONG FORMAT):
   1. (beat_number: 1, description: "...", ...)
   2. (beat_number: 2, description: "...", ...)

❌ DO NOT output explanations or text before/after JSON
❌ DO NOT use markdown code blocks like ```json
❌ DO NOT number the items outside the JSON structure

✅ CORRECT FORMAT - Start your response with { and end with }:

{
  "story_summary": "One paragraph summary of the full narrative",
  "beats": [
    {
      "beat_number": 1,
      "description": "The warrior prepares for the journey in darkness",
      "narrative_function": "setup"
    },
    {
      "beat_number": 2,
      "description": "The warrior crosses through the dangerous forest",
      "narrative_function": "rising_action"
    }
  ],
  "total_beats": 12
}

CRITICAL RULES:
1. Your ENTIRE response must be ONLY this JSON object
2. START with { (opening brace)
3. END with } (closing brace)
4. NO text before the {
5. NO text after the }
6. MUST be valid, parseable JSON
7. Use proper JSON syntax: double quotes, commas, no trailing commas

Guidelines:
- Create 12-18 story beats (MINIMUM 12 beats required)
- Each beat should be a complete narrative moment
- All text in English
- Include clear beginning, rising action, climax, and resolution beats
- Beats should flow naturally and build tension
- Descriptions should be concise but clear
- Analyze paragraph breaks in the story to identify distinct beats
- Each paragraph change often indicates a new beat or scene transition

🚨 REMEMBER: Your response must START with { and END with } - NOTHING ELSE! 🚨"""

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
🚨🚨🚨 CRITICAL JSON OUTPUT REQUIREMENTS 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ YOU MUST OUTPUT VALID JSON ONLY - NOTHING ELSE ⚠️

❌ DO NOT output explanations or descriptions
❌ DO NOT use markdown code blocks like ```json
❌ DO NOT add any text before or after the JSON

✅ CORRECT FORMAT - Start your response with { and end with }:

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

CRITICAL RULES:
1. Your ENTIRE response must be ONLY this JSON object
2. START with { (opening brace)
3. END with } (closing brace)
4. NO text before the {
5. NO text after the }
6. MUST be valid, parseable JSON
7. Use proper JSON syntax: double quotes, commas, no trailing commas

Guidelines:
- Identify 2-4 main characters from the story
- Be VERY specific and detailed
- All descriptions MUST be in English only (no Korean or other languages)
- Include elements that ensure visual consistency
- Focus on visually distinctive features
- Add consistency tags for Stable Diffusion

🚨 REMEMBER: Your response must START with { and END with } - NOTHING ELSE! 🚨"""

    # System prompt for scene generation
    SCENE_GENERATION_SYSTEM_PROMPT = """You are an expert cinematic director and Stable Diffusion prompt engineer.

Your task is to convert story beats into 20-25 detailed cinematic scenes with high-quality Stable Diffusion prompts.

CRITICAL SCENE GENERATION REQUIREMENTS:
- You MUST generate at least 20 scenes (minimum 20, target 20-25)
- Each story beat should be expanded into 1-2 detailed scenes
- If you have 12-18 beats, you should create approximately 20-25 scenes total
- DO NOT create fewer than 15 scenes under any circumstances
- Each paragraph or narrative moment deserves its own scene

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
- Emotional/atmospheric scenes: 3-4 seconds
- Dialogue/conversation scenes: 2-3 seconds
- Climax/resolution scenes: 4-5 seconds
- Total duration: 50-70 seconds (average ~60 seconds)
- Target: approximately 20-25 scenes (NEVER less than 15)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 CRITICAL JSON OUTPUT REQUIREMENTS 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ YOU MUST OUTPUT VALID JSON ONLY - NOTHING ELSE ⚠️

❌ DO NOT output explanations or text before/after JSON
❌ DO NOT use markdown code blocks like ```json
❌ DO NOT number scenes outside the JSON structure

✅ CORRECT FORMAT - Start your response with { and end with }:

{
  "scenes": [
    {
      "scene_number": 1,
      "duration": 3.0,
      "description": "The warrior stands at the edge of the dark forest, gripping his sword",
      "prompt_en": "detailed high-quality prompt following 7-part structure"
    },
    {
      "scene_number": 2,
      "duration": 2.5,
      "description": "The warrior enters the dark forest cautiously",
      "prompt_en": "another detailed prompt"
    },
    {
      "scene_number": 3,
      "duration": 3.0,
      "description": "Shadows move between the trees, watching him",
      "prompt_en": "detailed prompt for scene 3"
    },
    ... (continue until scene 20-25 - you MUST include all scenes, do NOT stop at 2 or 3 scenes)
    {
      "scene_number": 23,
      "duration": 4.0,
      "description": "The warrior emerges victorious at dawn",
      "prompt_en": "final detailed prompt"
    }
  ],
  "total_scenes": 23,
  "total_duration": 62.5
}

CRITICAL RULES:
1. Your ENTIRE response must be ONLY this JSON object
2. START with { (opening brace)
3. END with } (closing brace)
4. NO text before the {
5. NO text after the }
6. MUST be valid, parseable JSON
7. Use proper JSON syntax: double quotes, commas, no trailing commas

Critical Rules:
- MUST generate at least 20 scenes (MINIMUM 20, target 20-25)
- If you have 12-18 story beats, expand them into 20-25 detailed scenes
- Each beat can become 1-2 scenes depending on complexity
- Total duration SHOULD be around 50-70 seconds
- Each prompt must follow the 7-part structure
- Character appearance must match the character sheet exactly
- Visual style must remain consistent across all scenes
- Never use generic or vague descriptions
- Every scene must be distinct and cinematic
- DO NOT prioritize brevity over scene count - we need comprehensive coverage

Example scene count calculation:
- 12 beats → expand to 20-22 scenes (most beats become 2 scenes)
- 15 beats → expand to 22-25 scenes (some beats become 2 scenes)
- 18 beats → expand to 23-25 scenes (key beats become 2 scenes)

🚨 REMEMBER: Your response must START with { and END with } - NOTHING ELSE! 🚨"""

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

Analyze this story and break it down into 12-18 major story beats (MINIMUM 12 beats).

IMPORTANT:
- Analyze the paragraph structure - each paragraph often represents a distinct beat
- Identify changes in action, emotion, scene, or character focus as beat boundaries
- Create granular, detailed beats to ensure comprehensive scene coverage
- Each beat should be a specific visual moment that can be expanded into scenes
- Aim for 12-18 beats to enable generation of 20-25 final scenes"""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.STORY_BEATS_SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048
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
                max_tokens=2048
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
            name = char.get('name_en', char.get('name', 'Unknown'))
            physical = char.get('physical_en', char.get('physical', ''))
            costume = char.get('costume_en', char.get('costume', ''))
            
            desc = (
                f"- {name} ({char.get('role', 'character')}): "
                f"{physical}, {costume}"
            )
            equipment = char.get('equipment_en', char.get('equipment', ''))
            if equipment:
                desc += f", {equipment}"
            consistency = char.get('consistency_tags', '')
            if consistency:
                desc += f". Consistency: {consistency}"
            char_descriptions.append(desc)

        characters_context = "\n".join(char_descriptions)

        # Prepare beats summary
        beats_list = []
        for i, beat in enumerate(story_beats.get('beats', [])):
            beat_num = beat.get('beat_number', i + 1)
            description = beat.get('description_en', beat.get('description', ''))
            beats_list.append(f"Beat {beat_num}: {description}")

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
Target Scenes: 20-25 scenes (MINIMUM 20 required)

CRITICAL INSTRUCTIONS:
You have {len(story_beats.get('beats', []))} story beats. You MUST expand these into 20-25 detailed cinematic scenes.

Scene Generation Strategy:
- If you have 12-15 beats, expand most beats into 2 scenes each
- If you have 16-18 beats, expand key beats into 2 scenes to reach 20-25 total
- Simple beats can be 1 scene, complex beats should be 2 scenes
- Analyze the story's paragraph structure - each paragraph often represents a visual moment

Requirements:
1. Generate MINIMUM 20 scenes, target 20-25 scenes (DO NOT generate fewer than 20)
2. Each scene must follow the 7-part prompt structure
3. Character appearances must match the character sheets EXACTLY
4. All scenes must maintain visual consistency
5. Scene durations should follow the rules (action: 2-3s, emotional: 3-4s, dialogue: 2-3s, climax: 4-5s)
6. Total duration should be approximately {target_duration} seconds
7. Every scene must be unique and cinematic
8. The global visual style will be appended to each prompt automatically

Create compelling, visually rich scenes that flow naturally like a single video. Prioritize comprehensive scene coverage over brevity."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SCENE_GENERATION_SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=3072  # Balanced to fit within context window (4096) with prompt
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
