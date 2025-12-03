"""WAN2.2 I2V (Image-to-Video) client wrapper.

This module provides a Python wrapper for WAN2.2 (World Animator Network 2.2)
to generate short vertical video clips from static images.
"""
import os
import sys
import time
import torch
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class WAN2Client:
    """Client for WAN2.2 Image-to-Video generation."""

    def __init__(
        self,
        wan2_repo_path: Optional[Path] = None,
        model_path: Optional[Path] = None,
        device: str = "cuda",
    ):
        """Initialize WAN2.2 client.

        Args:
            wan2_repo_path: Path to WAN2.2 repository (default: engine/wan2.2)
            model_path: Path to WAN2.2 model weights (default: models/video/wan2.2/Wan2.2-I2V-5B.safetensors)
            device: Device to use (cuda or cpu)
        """
        # Set default paths
        project_root = Path(__file__).parent.parent.parent.parent
        self.wan2_repo_path = wan2_repo_path or (project_root / "engine" / "wan2.2")
        self.model_path = model_path or (project_root / "models" / "video" / "wan2.2" / "Wan2.2-I2V-5B.safetensors")
        self.device = device

        logger.info(f"WAN2Client initialized")
        logger.info(f"  Repository: {self.wan2_repo_path}")
        logger.info(f"  Model: {self.model_path}")
        logger.info(f"  Device: {device}")

        # Validate paths
        if not self.wan2_repo_path.exists():
            logger.warning(f"WAN2.2 repository not found at {self.wan2_repo_path}")
        if not self.model_path.exists():
            logger.warning(f"WAN2.2 model not found at {self.model_path}")

        # Check if CUDA is available
        self.cuda_available = torch.cuda.is_available()
        if device == "cuda" and not self.cuda_available:
            logger.warning("CUDA requested but not available, falling back to CPU")
            self.device = "cpu"

        logger.info(f"CUDA available: {self.cuda_available}")

    def generate_scene_video(
        self,
        image_path: Path,
        prompt: str,
        out_path: Path,
        duration_sec: float = 2.5,
        fps: int = 24,
        motion_strength: float = 0.7,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
    ) -> None:
        """Generate a vertical video clip from a static image using WAN2.2 I2V.

        Args:
            image_path: Input image path (vertical 1080x1920)
            prompt: Text prompt for video motion/animation
            out_path: Output video path (MP4)
            duration_sec: Video duration in seconds
            fps: Frames per second
            motion_strength: Motion intensity (0.0-1.0)
            num_inference_steps: Number of diffusion steps
            guidance_scale: Guidance scale for prompt adherence
            seed: Random seed (auto-generated if None)
        """
        if seed is None:
            seed = int(time.time() * 1000) % (2**32)

        num_frames = int(duration_sec * fps)

        logger.info(f"Generating video from image: {image_path.name}")
        logger.info(f"  Prompt: {prompt[:80]}...")
        logger.info(f"  Duration: {duration_sec}s, FPS: {fps}, Frames: {num_frames}")
        logger.info(f"  Motion strength: {motion_strength}, Steps: {num_inference_steps}")

        # Create output directory
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if we can import WAN2.2 directly or need to use subprocess
        try:
            # Try direct Python import (if WAN2.2 is properly installable as a package)
            self._generate_direct(
                image_path=image_path,
                prompt=prompt,
                out_path=out_path,
                num_frames=num_frames,
                fps=fps,
                motion_strength=motion_strength,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed,
            )
        except ImportError as e:
            logger.warning(f"WAN2.2 direct import failed: {e}")
            logger.info("Falling back to subprocess/CLI approach...")
            self._generate_subprocess(
                image_path=image_path,
                prompt=prompt,
                out_path=out_path,
                num_frames=num_frames,
                fps=fps,
                motion_strength=motion_strength,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed,
            )

        logger.info(f"✓ Video saved: {out_path}")

    def _generate_direct(
        self,
        image_path: Path,
        prompt: str,
        out_path: Path,
        num_frames: int,
        fps: int,
        motion_strength: float,
        num_inference_steps: int,
        guidance_scale: float,
        seed: int,
    ) -> None:
        """Generate video using direct Python API (if WAN2.2 supports it).

        This is a placeholder for direct API integration.
        Actual implementation depends on WAN2.2's Python API structure.
        """
        # Add WAN2.2 repo to Python path
        sys.path.insert(0, str(self.wan2_repo_path))

        try:
            # Import WAN2.2 modules (structure may vary)
            # Example (adjust based on actual WAN2.2 API):
            # from wan2 import WAN2I2VPipeline
            # pipeline = WAN2I2VPipeline.from_pretrained(self.model_path, device=self.device)
            # video = pipeline(
            #     image=str(image_path),
            #     prompt=prompt,
            #     num_frames=num_frames,
            #     num_inference_steps=num_inference_steps,
            #     guidance_scale=guidance_scale,
            #     generator=torch.Generator(device=self.device).manual_seed(seed),
            # )
            # video.save(str(out_path), fps=fps)

            raise NotImplementedError(
                "WAN2.2 direct Python API not yet implemented. "
                "Please check WAN2.2 documentation for proper API usage, "
                "or use the subprocess approach."
            )

        except Exception as e:
            logger.error(f"Direct generation failed: {e}")
            raise

    def _generate_subprocess(
        self,
        image_path: Path,
        prompt: str,
        out_path: Path,
        num_frames: int,
        fps: int,
        motion_strength: float,
        num_inference_steps: int,
        guidance_scale: float,
        seed: int,
    ) -> None:
        """Generate video using subprocess/CLI (if WAN2.2 provides a CLI).

        This approach shells out to WAN2.2's inference script.
        """
        # Look for WAN2.2 inference script
        # Common names: infer.py, generate.py, i2v_inference.py, etc.
        possible_scripts = [
            self.wan2_repo_path / "infer.py",
            self.wan2_repo_path / "inference.py",
            self.wan2_repo_path / "generate.py",
            self.wan2_repo_path / "scripts" / "i2v_inference.py",
            self.wan2_repo_path / "tools" / "inference.py",
        ]

        inference_script = None
        for script in possible_scripts:
            if script.exists():
                inference_script = script
                break

        if inference_script is None:
            raise FileNotFoundError(
                f"WAN2.2 inference script not found in {self.wan2_repo_path}. "
                f"Please check the WAN2.2 repository structure and update this code."
            )

        logger.info(f"Using WAN2.2 inference script: {inference_script}")

        # Build command (adjust based on actual WAN2.2 CLI interface)
        cmd = [
            "python",
            str(inference_script),
            "--model", str(self.model_path),
            "--input", str(image_path),
            "--output", str(out_path),
            "--prompt", prompt,
            "--num_frames", str(num_frames),
            "--fps", str(fps),
            "--steps", str(num_inference_steps),
            "--guidance_scale", str(guidance_scale),
            "--seed", str(seed),
            "--device", self.device,
        ]

        # Execute
        try:
            result = subprocess.run(
                cmd,
                cwd=self.wan2_repo_path,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
                check=True,
            )

            logger.info(f"WAN2.2 inference completed successfully")
            logger.debug(f"stdout: {result.stdout}")

        except subprocess.CalledProcessError as e:
            logger.error(f"WAN2.2 inference failed with exit code {e.returncode}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise RuntimeError(f"WAN2.2 inference failed: {e.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("WAN2.2 inference timed out")
            raise RuntimeError("WAN2.2 inference timed out after 10 minutes")

    def is_available(self) -> bool:
        """Check if WAN2.2 is available and configured.

        Returns:
            True if WAN2.2 can be used, False otherwise
        """
        return self.wan2_repo_path.exists() and self.model_path.exists()

    def get_info(self) -> Dict[str, Any]:
        """Get WAN2.2 client information.

        Returns:
            Info dictionary
        """
        return {
            "repository": str(self.wan2_repo_path),
            "model": str(self.model_path),
            "device": self.device,
            "cuda_available": self.cuda_available,
            "wan2_available": self.is_available(),
        }


# ============================================================================
# Fallback: Simple ffmpeg-based video generation (if WAN2.2 not available)
# ============================================================================

def generate_static_video_ffmpeg(
    image_path: Path,
    out_path: Path,
    duration_sec: float = 2.5,
    fps: int = 24,
) -> None:
    """Generate a static video from an image using ffmpeg (fallback).

    This creates a simple video where the image is shown for the specified duration
    with a subtle zoom/pan effect.

    Args:
        image_path: Input image path
        out_path: Output video path (MP4)
        duration_sec: Video duration in seconds
        fps: Frames per second
    """
    logger.info(f"Generating static video with ffmpeg: {out_path.name}")

    # Create output directory
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build ffmpeg command with subtle zoom
    # zoompan filter: z='min(zoom+0.0015,1.5)':d=duration*fps
    # This creates a slow zoom-in effect
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-loop", "1",
        "-i", str(image_path),
        "-vf", f"zoompan=z='min(zoom+0.001,1.1)':d={int(duration_sec * fps)}:fps={fps},format=yuv420p",
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        logger.info(f"✓ Static video created: {out_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg failed: {e.stderr}")
        raise RuntimeError(f"ffmpeg video generation failed: {e.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out")
        raise RuntimeError("ffmpeg video generation timed out")
