"""Main CLI entry point for AI Short Factory."""
import argparse
import sys
from pathlib import Path

from .pipeline.story_to_prompts import create_prompts_from_story
from .common.logger import setup_logger
from .common.config import Config

logger = setup_logger("ai_short_factory", log_file="factory.log")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Short Factory - Generate video prompts from stories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate prompts from a story
  python -m src "A brave knight battles a dragon in the mountains"

  # Use a story from a file
  python -m src --file story.txt

  # Specify style and duration
  python -m src "Space adventure story" --style anime --duration 30
        """
    )

    parser.add_argument(
        "story",
        nargs="?",
        help="The story text (or use --file to read from file)"
    )

    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Read story from file"
    )

    parser.add_argument(
        "--style", "-s",
        default="cinematic",
        choices=["cinematic", "anime", "realistic", "cartoon", "3d"],
        help="Visual style (default: cinematic)"
    )

    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=20.0,
        help="Target duration in seconds (default: 20.0)"
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path (default: auto-generated in output/prompts/)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logger.setLevel("DEBUG")

    # Get story text
    if args.file:
        if not args.file.exists():
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

        story = args.file.read_text(encoding='utf-8')
        logger.info(f"Loaded story from {args.file}")

    elif args.story:
        story = args.story

    else:
        logger.error("Please provide a story (as argument or --file)")
        parser.print_help()
        sys.exit(1)

    # Generate prompts
    try:
        logger.info("=" * 60)
        logger.info("AI Short Factory - Story to Prompts Conversion")
        logger.info("=" * 60)
        logger.info(f"Story length: {len(story)} characters")
        logger.info(f"Style: {args.style}")
        logger.info(f"Duration: {args.duration}s")
        logger.info("-" * 60)

        result = create_prompts_from_story(
            story=story,
            style=args.style,
            duration=args.duration,
        )

        # Display results
        print("\n" + "=" * 60)
        print("GENERATED PROMPTS")
        print("=" * 60)

        metadata = result.get("metadata", {})
        print(f"\nTitle: {metadata.get('title', 'N/A')}")
        print(f"Style: {metadata.get('style', 'N/A')}")
        print(f"Total Duration: {metadata.get('total_duration', 0)}s")
        print(f"Number of Scenes: {len(result.get('scenes', []))}")

        print("\n" + "-" * 60)
        print("SCENES")
        print("-" * 60)

        for scene in result.get("scenes", []):
            print(f"\n[Scene {scene.get('scene_number')}] - {scene.get('duration', 0)}s")
            print(f"Description: {scene.get('description', '')}")
            print(f"\nImage Prompt:")
            print(f"  {scene.get('image_prompt', '')}")
            print(f"\nNarration:")
            print(f"  {scene.get('narration', '')}")
            print(f"Audio Mood: {scene.get('audio_mood', '')}")
            print("-" * 60)

        logger.info("\n✓ Conversion completed successfully!")
        logger.info(f"✓ Results saved to: {Config.PROMPTS_DIR}")

    except Exception as e:
        logger.error(f"Failed to generate prompts: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
