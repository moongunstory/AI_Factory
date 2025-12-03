"""Full pipeline orchestrator for AI Short Factory.

This module orchestrates the complete workflow:
1. Story & scene generation (llama-server)
2. Image generation per scene (ComfyUI + SDXL)
3. Video generation per scene (WAN2.2 I2V)
4. Final video assembly (ffmpeg concat)
"""
import json
import time
import uuid
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .llama_client import LlamaStoryClient
from .comfy_client import ComfyUIClient
from .wan2_client import WAN2Client, generate_static_video_ffmpeg
from src.common.logger import setup_logger
from src.common.config import Config

logger = setup_logger(__name__)


# Global state for tracking pipeline progress
_pipeline_states: Dict[str, Dict[str, Any]] = {}


class PipelineStatus:
    """Pipeline status constants."""
    PENDING = "pending"
    GENERATING_STORY = "generating_story"
    GENERATING_IMAGES = "generating_images"
    GENERATING_VIDEOS = "generating_videos"
    CONCATENATING = "concatenating"
    DONE = "done"
    ERROR = "error"


def generate_short(
    theme: str,
    style: str = "cinematic",
    scene_count: int = 4,
    title_hint: Optional[str] = None,
    progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Generate a complete AI short video (fully automatic pipeline).

    This function orchestrates the entire workflow:
    1. Generate story breakdown via llama-server
    2. Generate vertical images for each scene via ComfyUI + SDXL
    3. Generate video clips for each scene via WAN2.2 I2V
    4. Concatenate all clips into final vertical video

    Args:
        theme: Theme/concept for the short (e.g., "space adventure")
        style: Visual style (e.g., "cinematic", "anime", "watercolor")
        scene_count: Number of scenes (default: 4)
        title_hint: Optional title hint
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with:
        {
            "short_id": str,
            "title": str,
            "synopsis": str,
            "scenes": [
                {
                    "id": int,
                    "image_path": str,
                    "video_path": str,
                    "prompt": str
                },
                ...
            ],
            "final_video_path": str,
            "duration_sec": float,
            "status": str
        }
    """
    # Generate unique short ID
    short_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    logger.info("=" * 80)
    logger.info(f"Starting AI Short Generation Pipeline: {short_id}")
    logger.info(f"  Theme: {theme}")
    logger.info(f"  Style: {style}")
    logger.info(f"  Scene count: {scene_count}")
    logger.info("=" * 80)

    # Initialize pipeline state
    state = {
        "short_id": short_id,
        "status": PipelineStatus.PENDING,
        "progress": 0,
        "current_step": "",
        "error": None,
        "title": "",
        "synopsis": "",
        "scenes": [],
        "final_video_path": None,
    }
    _pipeline_states[short_id] = state

    def update_state(status: str, progress: int, current_step: str):
        """Update pipeline state and call progress callback."""
        state["status"] = status
        state["progress"] = progress
        state["current_step"] = current_step
        logger.info(f"[{progress}%] {current_step}")
        if progress_callback:
            progress_callback(short_id, state.copy())

    try:
        # Setup paths
        project_root = Config.ROOT_DIR
        output_dir = project_root / "output"
        images_dir = output_dir / "images" / short_id
        videos_dir = output_dir / "video_segments" / short_id
        final_dir = output_dir / "final" / short_id

        images_dir.mkdir(parents=True, exist_ok=True)
        videos_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)

        # ====================================================================
        # Step 1: Generate story breakdown
        # ====================================================================
        update_state(PipelineStatus.GENERATING_STORY, 10, "Generating story & scene breakdown...")

        llama_client = LlamaStoryClient()
        story_data = llama_client.generate_story_breakdown(
            theme=theme,
            style=style,
            scene_count=scene_count,
            title_hint=title_hint,
        )

        state["title"] = story_data["title"]
        state["synopsis"] = story_data["synopsis"]

        logger.info(f"✓ Story generated: '{story_data['title']}'")
        logger.info(f"  Scenes: {len(story_data['scenes'])}")

        # ====================================================================
        # Step 2: Generate images for each scene
        # ====================================================================
        update_state(PipelineStatus.GENERATING_IMAGES, 20, "Generating images...")

        comfy_client = ComfyUIClient()

        for i, scene in enumerate(story_data["scenes"], 1):
            scene_id = scene["id"]
            image_prompt = scene["image_prompt"]

            scene_info = {
                "id": scene_id,
                "name": scene.get("name", f"Scene {scene_id}"),
                "image_prompt": image_prompt,
                "video_prompt": scene.get("video_prompt", ""),
                "duration_sec": scene.get("duration_sec", 2.5),
                "image_path": None,
                "video_path": None,
            }

            # Generate image
            update_state(
                PipelineStatus.GENERATING_IMAGES,
                20 + int(30 * i / len(story_data["scenes"])),
                f"Generating image {i}/{len(story_data['scenes'])}: {scene_info['name']}..."
            )

            image_path = images_dir / f"scene_{scene_id:03d}.png"

            try:
                metadata = comfy_client.generate_vertical_image(
                    prompt=image_prompt,
                    out_path=image_path,
                    steps_base=25,
                    steps_refiner=15,
                    cfg=7.0,
                )
                scene_info["image_path"] = str(image_path.relative_to(project_root))
                logger.info(f"✓ Image {i}/{len(story_data['scenes'])} generated: {image_path.name}")

            except Exception as e:
                logger.error(f"Failed to generate image for scene {scene_id}: {e}")
                scene_info["image_path"] = None
                # Continue with other scenes

            state["scenes"].append(scene_info)

        # ====================================================================
        # Step 3: Generate videos for each scene
        # ====================================================================
        update_state(PipelineStatus.GENERATING_VIDEOS, 50, "Generating videos...")

        wan2_client = WAN2Client()
        wan2_available = wan2_client.is_available()

        if not wan2_available:
            logger.warning("WAN2.2 not available, using ffmpeg fallback for video generation")

        scene_video_paths = []

        for i, scene_info in enumerate(state["scenes"], 1):
            scene_id = scene_info["id"]
            image_path = Path(project_root / scene_info["image_path"]) if scene_info["image_path"] else None

            if image_path is None or not image_path.exists():
                logger.warning(f"Image not found for scene {scene_id}, skipping video generation")
                continue

            video_path = videos_dir / f"scene_{scene_id:03d}.mp4"

            update_state(
                PipelineStatus.GENERATING_VIDEOS,
                50 + int(30 * i / len(state["scenes"])),
                f"Generating video {i}/{len(state['scenes'])}: {scene_info['name']}..."
            )

            try:
                if wan2_available:
                    # Use WAN2.2 for I2V
                    wan2_client.generate_scene_video(
                        image_path=image_path,
                        prompt=scene_info["video_prompt"],
                        out_path=video_path,
                        duration_sec=scene_info["duration_sec"],
                        fps=24,
                        motion_strength=0.7,
                        num_inference_steps=50,
                        guidance_scale=7.5,
                    )
                else:
                    # Fallback to ffmpeg static video
                    generate_static_video_ffmpeg(
                        image_path=image_path,
                        out_path=video_path,
                        duration_sec=scene_info["duration_sec"],
                        fps=24,
                    )

                scene_info["video_path"] = str(video_path.relative_to(project_root))
                scene_video_paths.append(video_path)
                logger.info(f"✓ Video {i}/{len(state['scenes'])} generated: {video_path.name}")

            except Exception as e:
                logger.error(f"Failed to generate video for scene {scene_id}: {e}")
                scene_info["video_path"] = None
                # Continue with other scenes

        # ====================================================================
        # Step 4: Concatenate all scene videos
        # ====================================================================
        update_state(PipelineStatus.CONCATENATING, 85, "Concatenating final video...")

        if not scene_video_paths:
            raise RuntimeError("No scene videos were generated successfully")

        final_video_path = final_dir / "short_final.mp4"

        concat_vertical_scenes(
            scene_paths=scene_video_paths,
            out_path=final_video_path,
        )

        state["final_video_path"] = str(final_video_path.relative_to(project_root))

        # Calculate total duration
        total_duration = sum(s["duration_sec"] for s in state["scenes"] if s.get("video_path"))

        logger.info(f"✓ Final video generated: {final_video_path}")
        logger.info(f"  Duration: {total_duration:.1f}s")

        # ====================================================================
        # Done
        # ====================================================================
        update_state(PipelineStatus.DONE, 100, "Complete!")

        logger.info("=" * 80)
        logger.info(f"AI Short Generation Pipeline Completed: {short_id}")
        logger.info(f"  Title: {state['title']}")
        logger.info(f"  Scenes: {len(state['scenes'])}")
        logger.info(f"  Duration: {total_duration:.1f}s")
        logger.info(f"  Final video: {final_video_path}")
        logger.info("=" * 80)

        return {
            "short_id": short_id,
            "title": state["title"],
            "synopsis": state["synopsis"],
            "scenes": state["scenes"],
            "final_video_path": state["final_video_path"],
            "duration_sec": total_duration,
            "status": PipelineStatus.DONE,
        }

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        state["status"] = PipelineStatus.ERROR
        state["error"] = str(e)
        if progress_callback:
            progress_callback(short_id, state.copy())
        raise


def concat_vertical_scenes(
    scene_paths: List[Path],
    out_path: Path,
    audio_path: Optional[Path] = None,
) -> None:
    """Concatenate multiple vertical video scenes into one continuous clip.

    Args:
        scene_paths: List of scene video paths (MP4)
        out_path: Output video path
        audio_path: Optional background audio/music file
    """
    logger.info(f"Concatenating {len(scene_paths)} scenes into: {out_path.name}")

    # Create a temporary concat file list
    concat_file = out_path.parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for scene_path in scene_paths:
            # ffmpeg concat demuxer format
            f.write(f"file '{scene_path.absolute()}'\n")

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
    ]

    # Add audio if provided
    if audio_path and audio_path.exists():
        cmd.extend([
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",  # Match shortest stream (audio or video)
        ])
    else:
        cmd.extend([
            "-c", "copy",  # Stream copy (no re-encoding)
        ])

    cmd.append(str(out_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        )
        logger.info(f"✓ Concatenated video created: {out_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg concat failed: {e.stderr}")
        raise RuntimeError(f"Video concatenation failed: {e.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg concat timed out")
        raise RuntimeError("Video concatenation timed out")

    finally:
        # Clean up concat file
        if concat_file.exists():
            concat_file.unlink()


def get_pipeline_status(short_id: str) -> Optional[Dict[str, Any]]:
    """Get the current status of a pipeline.

    Args:
        short_id: Short ID

    Returns:
        Status dictionary or None if not found
    """
    return _pipeline_states.get(short_id)


def check_engines_health() -> Dict[str, bool]:
    """Check the health of all backend engines.

    Returns:
        Dictionary with engine health status:
        {
            "llama_server": bool,
            "comfyui": bool,
            "wan22": bool,
            "overall": bool
        }
    """
    logger.info("Checking engine health...")

    health = {
        "llama_server": False,
        "comfyui": False,
        "wan22": False,
        "overall": False,
    }

    try:
        llama_client = LlamaStoryClient()
        health["llama_server"] = llama_client.is_healthy()
    except Exception as e:
        logger.warning(f"llama-server health check failed: {e}")

    try:
        comfy_client = ComfyUIClient()
        health["comfyui"] = comfy_client.is_healthy()
    except Exception as e:
        logger.warning(f"ComfyUI health check failed: {e}")

    try:
        wan2_client = WAN2Client()
        health["wan22"] = wan2_client.is_available()
    except Exception as e:
        logger.warning(f"WAN2.2 health check failed: {e}")

    # Overall health: at minimum llama-server and ComfyUI must be healthy
    health["overall"] = health["llama_server"] and health["comfyui"]

    logger.info(f"Engine health: {health}")
    return health
