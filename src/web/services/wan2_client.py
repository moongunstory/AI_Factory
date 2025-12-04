"""Deprecated WAN2.2 client placeholder.

WAN2.2 direct Python integration is not supported. Use
``ComfyUIVideoClient`` from ``video_client.py`` instead.
"""
from __future__ import annotations

from pathlib import Path
import subprocess

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class WAN2Client:  # pragma: no cover - legacy shim
    """Legacy shim that blocks direct WAN2.2 usage."""

    def __init__(self, *_args, **_kwargs):
        raise RuntimeError(
            "WAN2.2 direct API is disabled. Use ComfyUIVideoClient for video generation."
        )


def generate_static_video_ffmpeg(image_path: Path, out_path: Path, duration_sec: float = 2.5, fps: int = 24) -> None:
    """Create a static video from an image using ffmpeg (fallback utility)."""

    logger.info(
        "Generating static video fallback: %s -> %s (%.2fs @ %sfps)",
        image_path,
        out_path,
        duration_sec,
        fps,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-c:v",
        "libx264",
        "-t",
        str(duration_sec),
        "-vf",
        f"fps={fps}",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
