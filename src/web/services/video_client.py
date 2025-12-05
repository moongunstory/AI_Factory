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
    """Direct WAN2.2-style video prompt builder & submitter."""

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

        prompt = self.build_wan22_prompt(
            image_path=image_path,
            output_path=output_path,
            duration_sec=duration_sec,
            fps=fps,
            camera_prompt=camera_prompt,
        )

        prompt_id = self._queue_prompt(prompt)
        logger.info(f"Queued WAN2.2 prompt: {prompt_id}")

        if not self._wait_for_completion(prompt_id, timeout=self.timeout):
            raise RuntimeError(f"Video generation timed out after {self.timeout}s")

        return {
            "prompt_id": prompt_id,
            "video_path": str(output_path),
        }

    def build_wan22_prompt(
        self,
        image_path: Path,
        output_path: Path,
        duration_sec: float,
        fps: int,
        camera_prompt: str,
    ) -> Dict[str, Any]:

        """🔥 Minimal & stable WAN2.2 recipe. No template required."""

        node_id = "1"

        # ComfyUI standard execution format
        return {
            "prompt": {
                node_id: {
                    "class_type": "WAN2.2_I2V",
                    "inputs": {
                        "image": str(image_path),
                        "camera_prompt": camera_prompt,
                        "fps": fps,
                        "seconds": duration_sec,
                        "output_path": str(output_path.with_suffix("")),
                    },
                }
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
