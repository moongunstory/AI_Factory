"""Output formatter for scene generation results."""
from typing import Dict, Any


class SceneFormatter:
    """Format scene generation results into user-friendly output."""

    @staticmethod
    def format_complete_output(result: Dict[str, Any]) -> str:
        """Format complete scene generation result into structured text.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Formatted string with all sections
        """
        output = []

        # Header
        output.append("=" * 80)
        output.append("Story Video Scene Generation Results")
        output.append("=" * 80)
        output.append("")

        # Story Idea
        output.append("[Story Idea]")
        output.append(result.get('story_idea', 'N/A'))
        output.append("")
        output.append(f"Theme: {result.get('theme', 'N/A')}")
        output.append("")

        # Story Summary
        output.append("=" * 80)
        output.append("[Story Summary]")
        output.append("=" * 80)
        output.append(result.get('story_summary', 'N/A'))
        output.append("")

        # Story Beats
        output.append("=" * 80)
        output.append("[Story Beats]")
        output.append("=" * 80)
        for beat in result.get('story_beats', []):
            beat_num = beat.get('beat_number', '?')
            description = beat.get('description', 'N/A')
            function = beat.get('narrative_function', 'N/A')
            output.append(f"{beat_num}. {description}")
            output.append(f"   Function: {function}")
            output.append("")

        # Characters
        output.append("=" * 80)
        output.append("[Characters]")
        output.append("=" * 80)
        for char in result.get('characters', []):
            name = char.get('name', 'N/A')
            role = char.get('role', 'N/A')
            output.append(f"● {name} ({role})")
            output.append(f"  Physical: {char.get('physical', 'N/A')}")
            output.append(f"  Costume: {char.get('costume', 'N/A')}")
            output.append(f"  Equipment: {char.get('equipment', 'N/A')}")
            output.append(f"  Personality Visuals: {char.get('personality_visual', 'N/A')}")
            output.append(f"  Consistency Tags: {char.get('consistency_tags', 'N/A')}")
            output.append("")

        # Global Visual Style
        output.append("=" * 80)
        output.append("[Global Visual Style]")
        output.append("=" * 80)
        style = result.get('global_visual_style', {})
        output.append(f"Theme: {style.get('theme_name', 'N/A')}")
        output.append(f"Color Palette: {style.get('color_palette', 'N/A')}")
        output.append(f"Lighting: {style.get('lighting', 'N/A')}")
        output.append(f"Camera: {style.get('camera', 'N/A')}")
        output.append(f"Texture: {style.get('texture', 'N/A')}")
        output.append(f"Atmosphere: {style.get('atmosphere', 'N/A')}")
        output.append(f"Consistency Tags: {style.get('consistency_tags', 'N/A')}")
        output.append(f"Quality Tags: {style.get('quality_tags', 'N/A')}")
        output.append("")

        # Scenes
        output.append("=" * 80)
        output.append("[Scenes]")
        output.append("=" * 80)
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        output.append(f"Total Scenes: {total_scenes}")
        output.append(f"Total Duration: {total_duration} seconds")
        output.append("")

        for scene in result.get('scenes', []):
            scene_num = scene.get('scene_number', '?')
            duration = scene.get('duration', 0)
            description = scene.get('description', 'N/A')
            prompt_en = scene.get('prompt_en', 'N/A')

            output.append("-" * 80)
            output.append(f"Scene {scene_num}")
            output.append("-" * 80)
            output.append(f"Duration: {duration} seconds")
            output.append(f"Description: {description}")
            output.append("")
            output.append("Prompt (English):")
            output.append(prompt_en)
            output.append("")

        # Footer
        output.append("=" * 80)
        output.append("Generation Complete")
        output.append("=" * 80)

        return "\n".join(output)

    @staticmethod
    def format_markdown_output(result: Dict[str, Any]) -> str:
        """Format complete scene generation result into markdown.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Formatted markdown string
        """
        output = []

        # Header
        output.append("# Story Video Scene Generation Results")
        output.append("")

        # Story Idea
        output.append("## Story Idea")
        output.append(result.get('story_idea', 'N/A'))
        output.append("")
        output.append(f"**Theme:** {result.get('theme', 'N/A')}")
        output.append("")

        # Story Summary
        output.append("## Story Summary")
        output.append(result.get('story_summary', 'N/A'))
        output.append("")

        # Story Beats
        output.append("## Story Beats")
        for beat in result.get('story_beats', []):
            beat_num = beat.get('beat_number', '?')
            description = beat.get('description', 'N/A')
            function = beat.get('narrative_function', 'N/A')
            output.append(f"{beat_num}. **{description}**")
            output.append(f"   - Function: *{function}*")

        output.append("")

        # Characters
        output.append("## Characters")
        for char in result.get('characters', []):
            name = char.get('name', 'N/A')
            role = char.get('role', 'N/A')
            output.append(f"### {name} ({role})")
            output.append(f"- **Physical:** {char.get('physical', 'N/A')}")
            output.append(f"- **Costume:** {char.get('costume', 'N/A')}")
            output.append(f"- **Equipment:** {char.get('equipment', 'N/A')}")
            output.append(f"- **Personality Visuals:** {char.get('personality_visual', 'N/A')}")
            output.append(f"- **Consistency Tags:** {char.get('consistency_tags', 'N/A')}")
            output.append("")

        # Global Visual Style
        output.append("## Global Visual Style")
        style = result.get('global_visual_style', {})
        output.append(f"- **Theme:** {style.get('theme_name', 'N/A')}")
        output.append(f"- **Color Palette:** {style.get('color_palette', 'N/A')}")
        output.append(f"- **Lighting:** {style.get('lighting', 'N/A')}")
        output.append(f"- **Camera:** {style.get('camera', 'N/A')}")
        output.append(f"- **Texture:** {style.get('texture', 'N/A')}")
        output.append(f"- **Atmosphere:** {style.get('atmosphere', 'N/A')}")
        output.append(f"- **Consistency Tags:** {style.get('consistency_tags', 'N/A')}")
        output.append(f"- **Quality Tags:** {style.get('quality_tags', 'N/A')}")
        output.append("")

        # Scenes
        output.append("## Scenes")
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        output.append(f"**Total Scenes:** {total_scenes}  ")
        output.append(f"**Total Duration:** {total_duration} seconds")
        output.append("")

        for scene in result.get('scenes', []):
            scene_num = scene.get('scene_number', '?')
            duration = scene.get('duration', 0)
            description = scene.get('description', 'N/A')
            prompt_en = scene.get('prompt_en', 'N/A')

            output.append(f"### Scene {scene_num}")
            output.append(f"- **Duration:** {duration} seconds")
            output.append(f"- **Description:** {description}")
            output.append("")
            output.append("**Prompt (English):**")
            output.append(f"> {prompt_en}")
            output.append("")

        output.append("---")
        output.append("*Generation complete*")

        return "\n".join(output)

    @staticmethod
    def format_summary(result: Dict[str, Any]) -> str:
        """Format a brief summary of the results.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Brief summary string
        """
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        theme = result.get('theme', 'N/A')
        num_characters = len(result.get('characters', []))
        num_beats = len(result.get('story_beats', []))

        return f"""
Scene generation complete!
────────────────────────────────────────
Theme: {theme}
Story beats: {num_beats}
Characters: {num_characters}
Generated scenes: {total_scenes}
Total duration: {total_duration} seconds
────────────────────────────────────────
"""
