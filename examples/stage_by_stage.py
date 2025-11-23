#!/usr/bin/env python3
"""
Stage-by-stage usage example for the AI Shorts Factory LLM Pipeline.

This script demonstrates how to run each stage independently and inspect
the intermediate results between stages.

This is useful for:
- Debugging individual stages
- Understanding the data flow
- Customizing the pipeline
- Manual review/editing between stages
"""

import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run each pipeline stage independently."""

    from shorts_llm.pipeline import (
        generate_story_outline,
        generate_scene_plan,
        generate_prompts,
    )
    from shorts_llm.schemas import ShortsGenerationResult

    # Create output directory
    output_dir = Path("output/stage_by_stage")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Story parameters
    logline = "A street magician discovers real magic and must save the city from a dark sorcerer."
    target_duration = 75
    tone = "thrilling"
    genre = "urban fantasy"

    logger.info("=" * 80)
    logger.info("STAGE-BY-STAGE PIPELINE EXAMPLE")
    logger.info("=" * 80)
    logger.info(f"Logline: {logline}")
    logger.info("=" * 80)
    print()

    # ========================================================================
    # STAGE 1: Story Outline
    # ========================================================================

    logger.info(">>> STAGE 1: Generating Story Outline")
    print()

    outline = generate_story_outline(
        logline=logline,
        target_duration_seconds=target_duration,
        tone=tone,
        genre=genre,
        temperature=0.7,
    )

    logger.info(f"✓ Generated {len(outline.beats)} story beats")
    print()
    print("Story Beats:")
    for beat in outline.beats:
        print(f"  - {beat.title} ({beat.story_function})")

    # Save Stage 1 output
    stage1_path = output_dir / "01_outline.json"
    with open(stage1_path, 'w') as f:
        json.dump(outline.model_dump(), f, indent=2)
    logger.info(f"💾 Saved to {stage1_path}")

    # ========================================================================
    # STAGE 2: Scene & Shot Planning
    # ========================================================================

    print()
    logger.info(">>> STAGE 2: Generating Scene & Shot Plan")
    print()

    scene_plan = generate_scene_plan(
        outline=outline,
        temperature=0.6,
    )

    total_shots = sum(len(scene.shots) for scene in scene_plan.scenes)
    logger.info(f"✓ Generated {len(scene_plan.scenes)} scenes with {total_shots} shots")
    print()
    print("Scene Breakdown:")
    for scene in scene_plan.scenes:
        print(f"  {scene.scene_id}: {scene.location_description}")
        print(f"    Shots: {len(scene.shots)}")
        total_duration = sum(shot.duration_seconds for shot in scene.shots)
        print(f"    Duration: {total_duration:.1f}s")

    # Save Stage 2 output
    stage2_path = output_dir / "02_scene_plan.json"
    with open(stage2_path, 'w') as f:
        json.dump(scene_plan.model_dump(), f, indent=2)
    logger.info(f"💾 Saved to {stage2_path}")

    # ========================================================================
    # STAGE 3: Prompt Engineering
    # ========================================================================

    print()
    logger.info(">>> STAGE 3: Generating Prompts")
    print()

    prompts = generate_prompts(
        scene_plan=scene_plan,
        temperature=0.7,
    )

    logger.info(f"✓ Generated {len(prompts.shots)} shot prompts")
    print()
    print("Global Style:")
    print(f"  Visual: {prompts.global_style.visual_style}")
    print(f"  Colors: {prompts.global_style.color_palette}")
    print(f"  Lighting: {prompts.global_style.lighting_style}")
    print()
    print("Sample Prompts (first 2 shots):")
    for shot_prompt in prompts.shots[:2]:
        print(f"\n  {shot_prompt.shot_id}:")
        print(f"    Positive: {shot_prompt.positive_prompt}")
        print(f"    Negative: {shot_prompt.negative_prompt}")
        print(f"    Duration: {shot_prompt.duration_seconds}s")

    # Save Stage 3 output
    stage3_path = output_dir / "03_prompts.json"
    with open(stage3_path, 'w') as f:
        json.dump(prompts.model_dump(), f, indent=2)
    logger.info(f"💾 Saved to {stage3_path}")

    # ========================================================================
    # Assemble Final Result
    # ========================================================================

    print()
    logger.info(">>> Assembling Final Result")
    print()

    result = ShortsGenerationResult(
        outline=outline,
        scene_plan=scene_plan,
        prompts=prompts,
    )

    # Save complete result
    final_path = output_dir / "complete_result.json"
    result.to_json_file(str(final_path))
    logger.info(f"💾 Complete result saved to {final_path}")

    # ========================================================================
    # Summary
    # ========================================================================

    print()
    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETE - SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Beats: {len(result.outline.beats)}")
    logger.info(f"Scenes: {len(result.scene_plan.scenes)}")
    logger.info(f"Shots: {len(result.prompts.shots)}")

    total_duration = sum(shot.duration_seconds for shot in result.prompts.shots)
    logger.info(f"Total Duration: {total_duration:.1f}s")
    logger.info(f"Target Duration: {target_duration}s")
    logger.info(f"Difference: {total_duration - target_duration:+.1f}s")

    logger.info("=" * 80)
    logger.info(f"All outputs saved to: {output_dir}/")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
