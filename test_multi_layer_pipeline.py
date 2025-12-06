#!/usr/bin/env python3
"""Test script for the new multi-layer prompt generation pipeline.

This script demonstrates the complete pipeline:
1. Story expansion
2. Film Layer application
3. Camera Layer application
4. Enhanced prompt generation
"""
import json
from pathlib import Path

from src.pipeline import (
    StoryExpander,
    PromptGenerator,
    GlobalStyleConfig,
    get_available_themes,
)
from src.common.logger import setup_logger

logger = setup_logger(__name__)


def test_multi_layer_pipeline():
    """Test the complete multi-layer pipeline."""
    print("=" * 80)
    print("Multi-Layer Prompt Generation Pipeline Test")
    print("=" * 80)
    print()

    # Step 1: Show available themes
    print("Available Themes:")
    print("-" * 80)
    themes = get_available_themes()
    for theme_key, description in themes.items():
        print(f"  • {theme_key}: {description}")
    print()

    # Step 2: Create global style config
    print("Creating Global Style Config...")
    print("-" * 80)
    global_config = GlobalStyleConfig.from_theme("horror")
    print(f"Theme: {global_config.theme}")
    print(f"Film Layer: {global_config.enable_film_layer}")
    print(f"Camera Layer: {global_config.enable_camera_layer}")
    print()

    # Step 3: Expand a simple story
    print("Expanding Story...")
    print("-" * 80)
    simple_idea = """A lone astronaut discovers an abandoned alien space station.
    As they explore the dark corridors, strange sounds echo through the halls.
    The astronaut finds evidence of a terrible experiment gone wrong."""

    print(f"Original idea:\n{simple_idea}")
    print()

    expander = StoryExpander()
    expanded_story = expander.expand(simple_idea)

    print(f"Expanded story (length: {len(expanded_story)} chars):")
    print(expanded_story[:500] + "..." if len(expanded_story) > 500 else expanded_story)
    print()

    # Step 4: Generate prompts with multi-layer pipeline
    print("Generating Prompts with Multi-Layer Pipeline...")
    print("-" * 80)

    generator = PromptGenerator(
        enable_film_layer=global_config.enable_film_layer,
        enable_camera_layer=global_config.enable_camera_layer,
    )

    global_style_dict = global_config.get_global_style_dict()
    result = generator.generate(
        expanded_story=expanded_story,
        temperature=0.7,
        global_style=global_style_dict,
    )

    print(f"Total scenes: {result.get('total_scenes', 0)}")
    print(f"Estimated duration: {result.get('estimated_duration', 0):.1f}s")
    print()

    # Step 5: Display sample scenes with all layers
    print("Sample Scenes (with Film + Camera layers):")
    print("=" * 80)

    scenes = result.get("scenes", [])
    for i, scene in enumerate(scenes[:3], 1):  # Show first 3 scenes
        print(f"\nScene {scene.get('scene_number', i)}")
        print("-" * 80)

        # Basic info
        print(f"Duration: {scene.get('duration', 0)}s")
        print(f"Description: {scene.get('description', 'N/A')}")
        print()

        # Film Layer info
        if "film_style" in scene:
            film = scene["film_style"]
            print("Film Layer:")
            print(f"  • Emotion: {film.get('emotion', 'N/A')}")
            print(f"  • Lighting: {film.get('lighting', 'N/A')}")
            print(f"  • Atmosphere: {film.get('atmosphere', 'N/A')}")
            print()

        # Camera Layer info
        if "camera_style" in scene:
            camera = scene["camera_style"]
            print("Camera Layer:")
            print(f"  • Shot Type: {camera.get('shot_type', 'N/A')} ({camera.get('shot_type_name', '')})")
            print(f"  • Angle: {camera.get('angle', 'N/A')}")
            print(f"  • Lens: {camera.get('lens', 'N/A')}")
            print(f"  • Movement: {camera.get('movement', 'N/A')}")
            print()

        # Final enhanced prompt
        print("Enhanced Prompt:")
        prompt = scene.get("prompt_en", "N/A")
        # Truncate if too long
        if len(prompt) > 300:
            print(f"  {prompt[:300]}...")
        else:
            print(f"  {prompt}")
        print()

    # Step 6: Show camera variety statistics
    if generator.camera_layer:
        print("Camera Variety Statistics:")
        print("=" * 80)
        stats = generator.camera_layer.get_camera_variety_stats()
        print(f"Total scenes: {stats.get('total_scenes', 0)}")
        print(f"Unique shot types: {stats.get('unique_shot_types', 0)}")
        print(f"Unique angles: {stats.get('unique_angles', 0)}")
        print()

        print("Shot Type Distribution:")
        shot_dist = stats.get('shot_type_distribution', {})
        for shot_type, count in sorted(shot_dist.items()):
            print(f"  • {shot_type}: {count}")
        print()

        print("Angle Distribution:")
        angle_dist = stats.get('angle_distribution', {})
        for angle, count in sorted(angle_dist.items()):
            print(f"  • {angle}: {count}")
        print()

    # Step 7: Save results to file
    output_file = Path("output/test_multi_layer_result.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Full results saved to: {output_file}")
    print()

    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_multi_layer_pipeline()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        exit(1)
