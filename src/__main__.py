"""Main CLI entry point for AI Short Factory.

DEPRECATION WARNING:
This CLI interface uses the old advanced_scene_generator module which has been
replaced by the multi-layer pipeline (IntegratedStoryClient).

This module is kept for backward compatibility but may not work correctly.
Please use the web UI or update this CLI to use IntegratedStoryClient.
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# WARNING: advanced_scene_generator module no longer exists
# This import will fail - CLI needs to be updated to use IntegratedStoryClient
try:
    from .pipeline.advanced_scene_generator import generate_advanced_scenes
except ImportError:
    print("ERROR: CLI is deprecated. advanced_scene_generator module removed.")
    print("Please use the web UI instead: python -m src.web.app")
    sys.exit(1)

from .pipeline.scene_formatter import SceneFormatter
from .pipeline.visual_styles import VisualStyleDefinitions
from .common.logger import setup_logger
from .common.config import Config

logger = setup_logger("ai_short_factory", log_file="factory.log")


def main():
    """Main CLI function."""
    # Get available themes
    available_themes = VisualStyleDefinitions.list_themes()

    parser = argparse.ArgumentParser(
        description="AI Short Factory - Generate 20-25 scene video sequences with Stable Diffusion prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Generate prompts from a story
  python -m src "A brave knight battles a dragon in the mountains"

  # Use a story from a file
  python -m src --file story.txt

  # Specify theme and duration
  python -m src "Space adventure story" --theme cyber_fantasy --duration 60

  # List available themes
  python -m src --list-themes

Available Themes:
  {', '.join(available_themes)}
        """
    )

    parser.add_argument(
        "story",
        nargs="?",
        help="The story idea text (or use --file to read from file)"
    )

    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Read story from file"
    )

    parser.add_argument(
        "--theme", "-t",
        default="cinematic_realism",
        choices=available_themes,
        help="Visual theme (default: cinematic_realism)"
    )

    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=60.0,
        help="Target total duration in seconds (default: 60.0, range: 50-70)"
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path (default: auto-generated in output/prompts/)"
    )

    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "markdown", "json"],
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List all available visual themes and exit"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Handle list-themes command
    if args.list_themes:
        print("\n사용 가능한 테마:")
        print("=" * 60)
        for theme in available_themes:
            info = VisualStyleDefinitions.get_theme_info(theme)
            print(f"  • {theme}")
            print(f"    {info}")
            print()
        sys.exit(0)

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
        logger.error("Please provide a story idea (as argument or --file)")
        parser.print_help()
        sys.exit(1)

    # Generate prompts
    try:
        logger.info("=" * 60)
        logger.info("AI Short Factory - Advanced Scene Generation")
        logger.info("=" * 60)
        logger.info(f"Story idea length: {len(story)} characters")
        logger.info(f"Theme: {args.theme}")
        logger.info(f"Target Duration: {args.duration}s")
        logger.info("-" * 60)

        result = generate_advanced_scenes(
            story_idea=story,
            theme=args.theme,
            target_duration=args.duration,
        )

        # Display summary
        print(SceneFormatter.format_summary(result))

        # Display results based on format
        if args.format == "json":
            output_text = json.dumps(result, ensure_ascii=False, indent=2)
        elif args.format == "markdown":
            output_text = SceneFormatter.format_markdown_output(result)
        else:  # text
            output_text = SceneFormatter.format_complete_output(result)

        print(output_text)

        # Save to file
        if args.output:
            output_path = args.output
        else:
            # Auto-generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "json" if args.format == "json" else "md" if args.format == "markdown" else "txt"
            output_path = Config.PROMPTS_DIR / f"scenes_{args.theme}_{timestamp}.{ext}"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        if args.format == "json":
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        else:
            output_path.write_text(output_text, encoding='utf-8')

        logger.info(f"\n✓ Scene generation completed successfully!")
        logger.info(f"✓ Results saved to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate scenes: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
