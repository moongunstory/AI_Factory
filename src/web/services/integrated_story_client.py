"""Integrated story client that uses the multi-layer prompt generation pipeline.

This replaces the simple LlamaStoryClient with a proper multi-layer pipeline that:
1. Generates theme-aware stories
2. Extracts characters with visual descriptions
3. Builds world/atmosphere layers
4. Applies film grammar and camera techniques
5. Injects character descriptions into every scene
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.pipeline import (
    StoryExpander,
    CharacterExtractor,
    PromptGenerator,
    GlobalStyleConfig,
)
from src.generators.llm import LlamaClient
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class IntegratedStoryClient:
    """Multi-layer story generation client with theme/character consistency."""

    def __init__(self, server_url: str = "http://127.0.0.1:8080"):
        """Initialize the integrated story client.

        Args:
            server_url: URL of the llama-server instance
        """
        self.llm = LlamaClient(server_url=server_url)
        self.story_expander = StoryExpander(llm_client=self.llm)
        self.character_extractor = CharacterExtractor(llm_client=self.llm)
        self.prompt_generator = PromptGenerator(
            llm_client=self.llm,
            enable_film_layer=True,
            enable_camera_layer=True,
        )
        logger.info(f"IntegratedStoryClient initialized with server: {server_url}")

    def generate_story_breakdown(
        self,
        theme: str,
        style: str = "cinematic",
        scene_count: int = 20,
        title_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete story breakdown with multi-layer pipeline.

        This generates:
        1. Theme-aware expanded story (300-500 words)
        2. Character sheet with visual descriptions
        3. World/atmosphere layer for theme consistency
        4. Scene breakdown with film grammar + camera techniques
        5. Character-injected prompts for each scene

        Args:
            theme: The theme/concept for the short (e.g., "zombie apocalypse horror")
            style: Visual style (e.g., "cinematic", "horror", "anime")
            scene_count: Target number of scenes (default: 20)
            title_hint: Optional title hint

        Returns:
            Dictionary with structure compatible with pipeline.py:
            {
                "title": str,
                "synopsis": str,
                "scenes": [
                    {
                        "id": int,
                        "name": str,
                        "image_prompt": str,  # Enhanced with all layers
                        "video_prompt": str,
                        "duration_sec": float
                    },
                    ...
                ]
            }
        """
        logger.info(f"Generating integrated story: theme='{theme}', style='{style}', scenes={scene_count}")

        # ====================================================================
        # Step 1: Create initial story concept based on theme
        # ====================================================================
        logger.info("Step 1: Creating theme-aware story concept...")

        story_concept = self._create_story_concept(theme, title_hint)
        logger.info(f"Story concept: {story_concept[:100]}...")

        # ====================================================================
        # Step 2: Expand story to 300-500 words with rich visual details
        # ====================================================================
        logger.info("Step 2: Expanding story with visual details...")

        expanded_story = self.story_expander.expand(story_concept)
        logger.info(f"Expanded story length: {len(expanded_story)} chars")

        # ====================================================================
        # Step 3: Extract character sheet
        # ====================================================================
        logger.info("Step 3: Extracting character sheet...")

        character_data = self.character_extractor.extract(expanded_story)
        characters = character_data.get("characters", [])
        logger.info(f"Extracted {len(characters)} characters: {[c['name_en'] for c in characters]}")

        # Build character prompt blocks for injection
        character_blocks = self._build_character_blocks(characters)

        # ====================================================================
        # Step 4: Configure global style based on theme
        # ====================================================================
        logger.info(f"Step 4: Configuring global style for theme '{style}'...")

        # Map style to visual theme (horror, dark_fantasy, etc.)
        theme_mapping = {
            "horror": "horror",
            "zombie": "horror",
            "apocalypse": "horror",
            "dark": "dark_fantasy",
            "fantasy": "fantasy_adventure",
            "sci-fi": "sci_fi",
            "cyberpunk": "cyber_fantasy",
            "anime": "anime",
            "disney": "disney",
            "cinematic": "cinematic_realism",
        }

        visual_theme = theme_mapping.get(style.lower(), "cinematic_realism")
        for keyword in theme.lower().split():
            if keyword in theme_mapping:
                visual_theme = theme_mapping[keyword]
                break

        global_config = GlobalStyleConfig.from_theme(visual_theme)
        global_style_dict = global_config.get_global_style_dict()
        logger.info(f"Using visual theme: {visual_theme}")

        # ====================================================================
        # Step 5: Add world/atmosphere layer to global style
        # ====================================================================
        logger.info("Step 5: Building world/atmosphere layer...")

        world_layer = self._build_world_layer(theme, style, expanded_story)
        logger.info(f"World layer: {world_layer[:100]}...")

        # Inject world layer into global style
        if "consistency_tags" in global_style_dict:
            global_style_dict["consistency_tags"] = (
                f"{world_layer}, {global_style_dict['consistency_tags']}"
            )
        else:
            global_style_dict["consistency_tags"] = world_layer

        # ====================================================================
        # Step 6: Generate scenes with multi-layer pipeline
        # ====================================================================
        logger.info("Step 6: Generating scenes with multi-layer pipeline...")

        scene_result = self.prompt_generator.generate(
            expanded_story=expanded_story,
            temperature=0.7,
            global_style=global_style_dict,
        )

        scenes = scene_result.get("scenes", [])
        logger.info(f"Generated {len(scenes)} scenes from pipeline")

        # ====================================================================
        # Step 7: Inject character descriptions into prompts
        # ====================================================================
        logger.info("Step 7: Injecting character descriptions into prompts...")

        for scene in scenes:
            # Inject character visual descriptions into prompt_en
            scene_characters = scene.get("characters", [])
            character_prompts = []

            for char in scene_characters:
                char_id = char.get("id", "").lower()
                if char_id in character_blocks:
                    character_prompts.append(character_blocks[char_id])

            # Rebuild prompt with character blocks at the front
            original_prompt = scene.get("prompt_en", "")
            if character_prompts:
                character_section = ", ".join(character_prompts)
                scene["prompt_en"] = f"{character_section}, {original_prompt}"

        logger.info("✓ Character descriptions injected into all scenes")

        # ====================================================================
        # Step 8: Generate title and synopsis
        # ====================================================================
        logger.info("Step 8: Generating title and synopsis...")

        title = self._generate_title(expanded_story, title_hint)
        synopsis = self._generate_synopsis(expanded_story)

        # ====================================================================
        # Step 9: Convert to pipeline-compatible format
        # ====================================================================
        logger.info("Step 9: Converting to pipeline format...")

        formatted_scenes = []
        for i, scene in enumerate(scenes, 1):
            formatted_scenes.append({
                "id": i,
                "name": scene.get("summary", f"Scene {i}"),
                "image_prompt": scene.get("prompt_en", ""),
                "video_prompt": self._generate_video_prompt(scene),
                "duration_sec": scene.get("duration", 3.0),
            })

        result = {
            "title": title,
            "synopsis": synopsis,
            "scenes": formatted_scenes,
        }

        logger.info(f"✓ Story generation complete: '{title}' with {len(formatted_scenes)} scenes")
        return result

    def _create_story_concept(self, theme: str, title_hint: Optional[str] = None) -> str:
        """Create initial story concept based on theme.

        Args:
            theme: User-provided theme
            title_hint: Optional title hint

        Returns:
            Story concept (2-3 sentences)
        """
        system_prompt = """You are a creative story writer. Based on the given theme, write a brief story concept (2-3 sentences) that captures the essence of the theme with vivid visual details."""

        user_prompt = f"""Theme: {theme}
{f'Title hint: {title_hint}' if title_hint else ''}

Write a brief story concept (2-3 sentences) that captures this theme with strong visual elements suitable for a short video."""

        concept = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=200,
        )

        return concept.strip()

    def _build_character_blocks(self, characters: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build character prompt blocks for injection.

        Args:
            characters: List of character dicts from character extractor

        Returns:
            Dict mapping character ID to prompt block
        """
        character_blocks = {}

        for char in characters:
            name = char.get("name_en", "")
            physical = char.get("physical_en", "")
            costume = char.get("costume_en", "")
            equipment = char.get("equipment_en", "")

            # Build comprehensive character prompt
            parts = [name]
            if physical:
                parts.append(physical)
            if costume:
                parts.append(costume)
            if equipment:
                parts.append(equipment)

            prompt_block = ", ".join(parts)
            character_id = name.lower().replace(" ", "_")
            character_blocks[character_id] = prompt_block

            logger.debug(f"Character block '{character_id}': {prompt_block}")

        return character_blocks

    def _build_world_layer(self, theme: str, style: str, expanded_story: str) -> str:
        """Build world/atmosphere layer from theme and story.

        Args:
            theme: User theme
            style: Visual style
            expanded_story: Expanded story text

        Returns:
            World layer description for consistency across scenes
        """
        # Extract key world-building elements from theme and story
        world_keywords = []

        # Theme-based world elements
        theme_lower = theme.lower()

        if any(kw in theme_lower for kw in ["zombie", "apocalypse", "post-apocalyptic"]):
            world_keywords.extend([
                "post-apocalyptic ruined city",
                "zombie-infested world",
                "collapsed buildings",
                "abandoned cars",
                "broken windows",
                "burned debris",
                "bloodstains",
                "scattered corpses",
                "smoke and dust in the air",
                "eerie silence",
                "constant danger",
            ])
        elif any(kw in theme_lower for kw in ["horror", "terror", "nightmare"]):
            world_keywords.extend([
                "dark ominous atmosphere",
                "creeping shadows",
                "unsettling silence",
                "decay and rot",
                "ominous presence",
            ])
        elif any(kw in theme_lower for kw in ["space", "sci-fi", "alien"]):
            world_keywords.extend([
                "futuristic space environment",
                "metallic corridors",
                "holographic displays",
                "zero gravity",
                "distant stars",
            ])
        elif any(kw in theme_lower for kw in ["fantasy", "magic", "medieval"]):
            world_keywords.extend([
                "mystical fantasy realm",
                "ancient ruins",
                "magical energy",
                "mysterious artifacts",
            ])

        # If no specific keywords matched, create generic atmospheric description
        if not world_keywords:
            world_keywords.append(f"{style} style atmosphere")

        return ", ".join(world_keywords[:8])  # Limit to 8 key elements

    def _generate_title(self, story: str, title_hint: Optional[str] = None) -> str:
        """Generate a catchy title for the story.

        Args:
            story: Full expanded story
            title_hint: Optional title hint

        Returns:
            Generated title
        """
        if title_hint:
            return title_hint

        system_prompt = "You are a creative title writer. Generate a short, catchy title (3-6 words) for the given story. Return ONLY the title, nothing else."

        user_prompt = f"""Story:
{story[:500]}

Generate a short, catchy title (3-6 words):"""

        title = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=50,
        )

        return title.strip().strip('"').strip("'")

    def _generate_synopsis(self, story: str) -> str:
        """Generate a brief synopsis of the story.

        Args:
            story: Full expanded story

        Returns:
            Synopsis (1-2 sentences)
        """
        system_prompt = "You are a story summarizer. Create a brief synopsis (1-2 sentences) that captures the essence of the story. Return ONLY the synopsis."

        user_prompt = f"""Story:
{story}

Create a brief synopsis (1-2 sentences):"""

        synopsis = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=150,
        )

        return synopsis.strip()

    def _generate_video_prompt(self, scene: Dict[str, Any]) -> str:
        """Generate video prompt (camera motion) from scene data.

        Args:
            scene: Scene dict with film_style and camera_style

        Returns:
            Video prompt string
        """
        camera_style = scene.get("camera_style", {})
        film_style = scene.get("film_style", {})

        # Extract camera movement
        movement = camera_style.get("movement", "static")

        # Map movement to video prompt style
        movement_mapping = {
            "static": "static shot, locked camera",
            "slow-pan": "slow pan, smooth camera movement",
            "fast-pan": "fast pan, dynamic movement",
            "handheld": "handheld camera, natural shake",
            "steadicam": "steadicam smooth movement",
            "dolly-in": "dolly in, push forward",
            "dolly-out": "dolly out, pull back",
            "crane-up": "crane up, ascending movement",
            "crane-down": "crane down, descending movement",
            "orbit": "orbital movement, circling subject",
            "tracking": "tracking shot, following subject",
        }

        base_prompt = movement_mapping.get(movement, "subtle camera movement")

        # Add intensity based on film emotion
        emotion = film_style.get("emotion", "calm")
        intensity_map = {
            "horror": "tense pacing",
            "action": "fast pacing, intense",
            "calm": "gentle pacing",
            "tension": "slow suspenseful pacing",
        }

        intensity = intensity_map.get(emotion, "cinematic pacing")

        return f"{base_prompt}, {intensity}"

    def is_healthy(self) -> bool:
        """Check if llama-server is healthy and ready.

        Returns:
            True if server is ready, False otherwise
        """
        return self.llm.is_server_ready()

    def get_server_info(self) -> Dict[str, Any]:
        """Get llama-server information.

        Returns:
            Server info dictionary
        """
        return self.llm.get_server_info()
