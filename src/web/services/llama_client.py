"""Llama-server client wrapper for story and scene generation.

This module provides a high-level interface to llama-server
for generating AI short stories and scene breakdowns.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.generators.llm import LlamaClient
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class LlamaStoryClient:
    """High-level client for story and scene generation via llama-server."""

    def __init__(self, server_url: str = "http://127.0.0.1:8080"):
        """Initialize the story client.

        Args:
            server_url: URL of the llama-server instance
        """
        self.client = LlamaClient(server_url=server_url)
        logger.info(f"LlamaStoryClient initialized with server: {server_url}")

    def generate_story_breakdown(
        self,
        theme: str,
        style: str = "cinematic",
        scene_count: int = 4,
        title_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete story breakdown with scenes.

        This generates:
        1. A title and synopsis
        2. N scene descriptions
        3. Image prompts (for SDXL)
        4. Video prompts (for WAN2.2 - camera motion, mood, etc.)

        Args:
            theme: The theme/concept for the short (e.g., "space adventure")
            style: Visual style (e.g., "cinematic", "anime", "watercolor")
            scene_count: Number of scenes to generate (default: 4)
            title_hint: Optional title hint

        Returns:
            Dictionary with structure:
            {
                "title": str,
                "synopsis": str,
                "scenes": [
                    {
                        "id": int,
                        "name": str,
                        "image_prompt": str,  # For SDXL
                        "video_prompt": str,  # For WAN2.2 (camera motion, pacing)
                        "duration_sec": float
                    },
                    ...
                ]
            }
        """
        logger.info(f"Generating story breakdown: theme='{theme}', style='{style}', scenes={scene_count}")

        system_prompt = """You are a professional AI short video scriptwriter.
Your task is to create engaging, visually-driven stories for vertical short videos (60 seconds).
Focus on strong visuals, clear scenes, and cinematic storytelling."""

        user_prompt = f"""Create a {scene_count}-scene short video story with the following requirements:

**Theme:** {theme}
**Visual Style:** {style}
{f'**Title Hint:** {title_hint}' if title_hint else ''}

Generate a complete breakdown in JSON format with:
1. A catchy title
2. A brief synopsis (1-2 sentences)
3. Exactly {scene_count} scenes, each with:
   - Scene ID (1, 2, 3, ...)
   - Scene name (brief, 3-5 words)
   - image_prompt: Detailed visual description for AI image generation (SDXL)
     * Describe composition, lighting, mood, characters, environment
     * Be specific about camera angle and framing
     * Optimized for vertical 9:16 format (portrait)
   - video_prompt: Camera motion and pacing for video generation (WAN2.2)
     * Examples: "slow zoom in", "pan right", "static shot", "dolly forward"
     * Include motion intensity: "subtle", "moderate", "dramatic"
   - duration_sec: Duration in seconds (typically 2-3 sec per scene)

IMPORTANT:
- Each scene should be visually striking and work well in vertical (9:16) format
- Total duration should be around 60 seconds
- Image prompts should be detailed and specific
- Video prompts should describe camera movement and pacing

Return ONLY valid JSON with this exact structure:
{{
  "title": "Story Title",
  "synopsis": "Brief synopsis here...",
  "scenes": [
    {{
      "id": 1,
      "name": "Scene Name",
      "image_prompt": "Detailed visual description for SDXL...",
      "video_prompt": "Camera motion and pacing description...",
      "duration_sec": 2.5
    }}
  ]
}}"""

        try:
            result = self.client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=3000,
                strict=True
            )

            # Validate the structure
            if not all(k in result for k in ["title", "synopsis", "scenes"]):
                raise ValueError("Invalid story breakdown structure")

            if not isinstance(result["scenes"], list) or len(result["scenes"]) == 0:
                raise ValueError("No scenes generated")

            # Ensure scene IDs are sequential
            for i, scene in enumerate(result["scenes"], 1):
                scene["id"] = i
                # Ensure required fields exist
                if "image_prompt" not in scene:
                    scene["image_prompt"] = scene.get("description", "")
                if "video_prompt" not in scene:
                    scene["video_prompt"] = "subtle camera movement, cinematic pacing"
                if "duration_sec" not in scene:
                    scene["duration_sec"] = 2.5
                if "name" not in scene:
                    scene["name"] = f"Scene {i}"

            logger.info(f"Generated story: '{result['title']}' with {len(result['scenes'])} scenes")
            return result

        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            # Return a fallback structure
            return {
                "title": title_hint or "Generated Short",
                "synopsis": f"A {style} short about {theme}",
                "scenes": [
                    {
                        "id": i,
                        "name": f"Scene {i}",
                        "image_prompt": f"{style} style, {theme}, scene {i}, vertical 9:16 composition",
                        "video_prompt": "subtle camera movement, cinematic pacing",
                        "duration_sec": 60.0 / scene_count
                    }
                    for i in range(1, scene_count + 1)
                ]
            }

    def is_healthy(self) -> bool:
        """Check if llama-server is healthy and ready.

        Returns:
            True if server is ready, False otherwise
        """
        return self.client.is_server_ready()

    def get_server_info(self) -> Dict[str, Any]:
        """Get llama-server information.

        Returns:
            Server info dictionary
        """
        return self.client.get_server_info()
