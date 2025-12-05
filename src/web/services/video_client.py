from __future__ import annotations
import json
import uuid
import time
from pathlib import Path
from typing import Any, Dict

import requests

from src.common.config import Config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ComfyUIVideoClient:
    """SVD (Stable Video Diffusion) video generator."""

    # Camera prompt to motion_bucket_id mapping
    CAMERA_TO_MOTION = {
        "static": 50,
        "forward": 127,
        "orbit": 180,
        "cinematic": 100,
    }

    def __init__(
        self,
        server_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.server_url = (server_url or Config.COMFYUI_URL).rstrip("/")
        self.timeout = timeout or Config.COMFYUI_TIMEOUT

    def generate_video(
        self,
        image_path: Path,
        output_path: Path,
        duration_sec: float = 2.5,
        camera_prompt: str = "cinematic",
        fps: int = 24,
    ) -> Dict[str, Any]:

        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate frames from duration and fps
        num_frames = int(duration_sec * fps)

        # Map camera_prompt to motion_bucket_id
        motion_bucket_id = self.CAMERA_TO_MOTION.get(camera_prompt, 127)

        prompt = self.build_svd_prompt(
            image_path=image_path,
            output_path=output_path,
            num_frames=num_frames,
            fps=fps,
            motion_bucket_id=motion_bucket_id,
        )

        prompt_id = self._queue_prompt(prompt)
        logger.info(f"Queued SVD prompt: {prompt_id} (frames={num_frames}, fps={fps}, motion={motion_bucket_id})")

        if not self._wait_for_completion(prompt_id, timeout=self.timeout):
            raise RuntimeError(f"Video generation timed out after {self.timeout}s")

        return {
            "prompt_id": prompt_id,
            "video_path": str(output_path),
        }

    def build_svd_prompt(
        self,
        image_path: Path,
        output_path: Path,
        num_frames: int,
        fps: int,
        motion_bucket_id: int,
    ) -> Dict[str, Any]:
        """Build SVD workflow prompt."""

        # SVD workflow nodes
        return {
            "prompt": {
                "1": {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": str(image_path.name),
                        "upload": "image",
                    },
                },
                "2": {
                    "class_type": "SVD_img2vid_Conditioning",
                    "inputs": {
                        "width": 1024,
                        "height": 576,
                        "video_frames": num_frames,
                        "motion_bucket_id": motion_bucket_id,
                        "fps": fps,
                        "augmentation_level": 0.0,
                        "clip_vision": ["3", 0],
                        "init_image": ["1", 0],
                        "vae": ["4", 0],
                    },
                },
                "3": {
                    "class_type": "CLIPVisionLoader",
                    "inputs": {
                        "clip_name": "SD15/model.safetensors",
                    },
                },
                "4": {
                    "class_type": "VAELoader",
                    "inputs": {
                        "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors",
                    },
                },
                "5": {
                    "class_type": "VideoLinearCFGGuidance",
                    "inputs": {
                        "min_cfg": 1.0,
                        "conditioning": ["2", 0],
                    },
                },
                "6": {
                    "class_type": "KSamplerSelect",
                    "inputs": {
                        "sampler_name": "euler",
                    },
                },
                "7": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": 42,
                        "steps": 20,
                        "cfg": 2.5,
                        "sampler_name": "euler",
                        "scheduler": "karras",
                        "denoise": 1.0,
                        "model": ["8", 0],
                        "positive": ["5", 0],
                        "negative": ["2", 1],
                        "latent_image": ["2", 2],
                    },
                },
                "8": {
                    "class_type": "ImageOnlyCheckpointLoader",
                    "inputs": {
                        "ckpt_name": "svd_xt.safetensors",
                    },
                },
                "9": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["7", 0],
                        "vae": ["4", 0],
                    },
                },
                "10": {
                    "class_type": "VHS_VideoCombine",
                    "inputs": {
                        "frame_rate": fps,
                        "format": "video/h264-mp4",
                        "filename_prefix": str(output_path.with_suffix("").name),
                        "images": ["9", 0],
                    },
                },
            }
        }

    def _queue_prompt(self, prompt: Dict[str, Any]) -> str:
        prompt_id = str(uuid.uuid4())
        payload = {"prompt": prompt, "client_id": prompt_id}
        res = requests.post(f"{self.server_url}/prompt", json=payload, timeout=20)
        res.raise_for_status()
        result = res.json()
        return result.get("prompt_id", prompt_id)

    def _wait_for_completion(self, prompt_id: str, timeout: int) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                res = requests.get(
                    f"{self.server_url}/history/{prompt_id}", timeout=8
                )
                if res.status_code == 200:
                    hist = res.json().get(prompt_id, {})
                    if hist.get("status", {}).get("completed"):
                        return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def is_healthy(self) -> bool:
        try:
            r = requests.get(f"{self.server_url}/system_stats", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
