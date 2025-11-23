#!/usr/bin/env python3
"""
Basic usage example for the AI Shorts Factory LLM Pipeline.

This script demonstrates how to:
1. Test connection to the local LLM server
2. Generate a complete prompt package from a logline
3. Access and display the results
4. Save results to JSON

Prerequisites:
- Local LLM server running at http://localhost:8000/v1 (or set LOCAL_LLM_BASE_URL)
- Python dependencies installed (pip install -r requirements.txt)
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run the basic example pipeline."""

    # Import the pipeline
    try:
        from shorts_llm.pipeline import generate_shorts_prompt_package
        from shorts_llm.llm_client import test_connection
    except ImportError as e:
        logger.error(f"Failed to import shorts_llm: {e}")
        logger.error("Make sure you've installed the package: pip install -e .")
        sys.exit(1)

    # Test connection first
    logger.info("Testing connection to local LLM server...")
    if not test_connection():
        logger.error("Cannot connect to LLM server!")
        logger.error("Make sure your local LLM server is running.")
        logger.error("Default URL: http://localhost:8000/v1")
        logger.error("Set LOCAL_LLM_BASE_URL environment variable to override.")
        sys.exit(1)

    logger.info("✓ Connection successful!")
    print()

    # Define the story
    logline = "A lone astronaut discovers an ancient alien artifact on Mars that shows visions of Earth's future."

    logger.info("=" * 80)
    logger.info("AI SHORTS FACTORY - EXAMPLE RUN")
    logger.info("=" * 80)
    logger.info(f"Logline: {logline}")
    logger.info(f"Target Duration: 60 seconds")
    logger.info(f"Tone: mysterious")
    logger.info(f"Genre: sci-fi")
    logger.info("=" * 80)
    print()

    # Generate the complete prompt package
    try:
        result = generate_shorts_prompt_package(
            logline=logline,
            target_duration_seconds=60,
            tone="mysterious",
            genre="sci-fi",
            temperature_outline=0.7,
            temperature_scene_plan=0.6,
            temperature_prompts=0.7,
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

    # Display results
    print()
    logger.info("=" * 80)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 80)

    # Story Outline
    print(f"\n📖 STORY OUTLINE ({len(result.outline.beats)} beats)")
    print(f"   Duration: {result.outline.metadata.estimated_duration_seconds}s")
    print(f"   Tone: {result.outline.metadata.tone}")
    print(f"   Genre: {result.outline.metadata.genre}")
    print()
    for i, beat in enumerate(result.outline.beats, 1):
        print(f"   {i}. {beat.title} ({beat.story_function})")
        print(f"      {beat.summary[:80]}...")

    # Scene Plan
    total_shots = sum(len(scene.shots) for scene in result.scene_plan.scenes)
    print(f"\n🎬 SCENE & SHOT PLAN ({len(result.scene_plan.scenes)} scenes, {total_shots} shots)")
    print()
    for scene in result.scene_plan.scenes:
        print(f"   {scene.scene_id}: {scene.location_description}")
        print(f"      Purpose: {scene.scene_purpose}")
        print(f"      Shots: {len(scene.shots)}")
        for shot in scene.shots[:2]:  # Show first 2 shots
            print(f"         - {shot.shot_id}: {shot.shot_type}, {shot.camera_movement}, {shot.duration_seconds}s")
        if len(scene.shots) > 2:
            print(f"         ... and {len(scene.shots) - 2} more")

    # Prompts
    print(f"\n✨ GENERATED PROMPTS ({len(result.prompts.shots)} shots)")
    print()
    print(f"   Global Style:")
    print(f"      Visual: {result.prompts.global_style.visual_style}")
    print(f"      Colors: {result.prompts.global_style.color_palette}")
    print(f"      Lighting: {result.prompts.global_style.lighting_style}")
    print()
    print(f"   Sample Prompts:")
    for i, shot_prompt in enumerate(result.prompts.shots[:3], 1):  # Show first 3
        print(f"\n   {i}. {shot_prompt.shot_id} ({shot_prompt.duration_seconds}s)")
        print(f"      Positive: {shot_prompt.positive_prompt[:100]}...")
        print(f"      Negative: {shot_prompt.negative_prompt[:60]}...")

    if len(result.prompts.shots) > 3:
        print(f"\n   ... and {len(result.prompts.shots) - 3} more shots")

    # Save to JSON
    output_path = Path("output/example_result.json")
    output_path.parent.mkdir(exist_ok=True)

    try:
        result.to_json_file(str(output_path))
        logger.info(f"\n💾 Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

    print()
    logger.info("=" * 80)
    logger.info("✓ Example complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
