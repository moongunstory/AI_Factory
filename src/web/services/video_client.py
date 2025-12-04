"""ComfyUI workflow-based video generation helper.

This module sends WAN2.2-style image-to-video requests to ComfyUI using
the bundled workflow template. The template is loaded from
``engine/comfyui/venv/Lib/site-packages/comfyui_workflow_templates_media_video/templates/video_wan2_2_14B_i2v.json``
and patched with runtime parameters before being submitted via the
ComfyUI REST API.
"""
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
    """Submit WAN2.2 image-to-video workflows to ComfyUI via REST."""

    def __init__(
        self,
        server_url: str | None = None,
        workflow_template: Path | None = None,
        timeout: int | None = None,
    ) -> None:
        self.server_url = (server_url or Config.COMFYUI_URL).rstrip("/")
        self.workflow_template = workflow_template or Config.WAN22_WORKFLOW_TEMPLATE
        self.timeout = timeout or Config.COMFYUI_TIMEOUT

    def generate_video(
        self,
        image_path: Path,
        output_path: Path,
        duration_sec: float = 2.5,
        camera_prompt: str = "cinematic movement",
        fps: int = 24,
    ) -> Dict[str, Any]:
        """Generate a video clip from an image using the WAN2.2 workflow template."""

        if not self.workflow_template.exists():
            raise FileNotFoundError(
                f"Workflow template not found: {self.workflow_template}. "
                "Install comfyui_workflow_templates_media_video or adjust the path."
            )

        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        workflow = self._load_template()
        workflow = self._prepare_workflow(
            workflow,
            image_path=image_path,
            output_path=output_path,
            duration_sec=duration_sec,
            camera_prompt=camera_prompt,
            fps=fps,
        )

        prompt_id = self._queue_prompt(workflow)
        logger.info(f"Queued ComfyUI WAN2.2 workflow: {prompt_id}")

        completed = self._wait_for_completion(prompt_id, timeout=self.timeout)
        if not completed:
            raise RuntimeError(f"Video generation timed out after {self.timeout}s")

        logger.info(f"✓ Video generated at {output_path}")
        return {
            "prompt_id": prompt_id,
            "video_path": str(output_path),
            "fps": fps,
            "duration_sec": duration_sec,
            "camera_prompt": camera_prompt,
        }

    def _load_template(self) -> Dict[str, Any]:
        with open(self.workflow_template, "r", encoding="utf-8") as f:
            return json.load(f)

    def _prepare_workflow(
        self,
        workflow: Dict[str, Any],
        image_path: Path,
        output_path: Path,
        duration_sec: float,
        camera_prompt: str,
        fps: int,
    ) -> Dict[str, Any]:
        """Inject runtime parameters into the workflow template."""

        replacements = {
            "{image_path}": str(image_path),
            "{output_path}": str(output_path.with_suffix("")),
            "{output_dir}": str(output_path.parent),
            "{camera_prompt}": camera_prompt,
        }

        workflow = self._replace_placeholders(workflow, replacements)

        for node in workflow.get("nodes", []):
            inputs = node.get("inputs", {})

            for key in ("image", "image_path", "input_image", "init_image", "bg_image"):
                if key in inputs:
                    inputs[key] = str(image_path)

            if "filename_prefix" in inputs:
                inputs["filename_prefix"] = str(output_path.with_suffix(""))
            if "output_path" in inputs:
                inputs["output_path"] = str(output_path.parent)
            if "output_dir" in inputs:
                inputs["output_dir"] = str(output_path.parent)

            for fps_key in ("fps", "frame_rate", "video_frame_rate"):
                if fps_key in inputs:
                    inputs[fps_key] = fps

            for length_key in ("seconds", "duration", "length_sec", "video_length"):
                if length_key in inputs:
                    inputs[length_key] = duration_sec

            for camera_key in ("camera", "camera_prompt", "camera_motion"):
                if camera_key in inputs:
                    inputs[camera_key] = camera_prompt

        return workflow

    def _replace_placeholders(self, obj: Any, replacements: Dict[str, str]) -> Any:
        if isinstance(obj, dict):
            return {k: self._replace_placeholders(v, replacements) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_placeholders(v, replacements) for v in obj]
        if isinstance(obj, str):
            for token, value in replacements.items():
                obj = obj.replace(token, value)
            return obj
        return obj

    def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        prompt_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": prompt_id}
        response = requests.post(f"{self.server_url}/prompt", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("prompt_id", prompt_id)

    def _wait_for_completion(self, prompt_id: str, timeout: int) -> bool:
        start_time = time.time()
        while True:
            if (time.time() - start_time) > timeout:
                return False
            try:
                response = requests.get(
                    f"{self.server_url}/history/{prompt_id}",
                    timeout=10,
                )
                response.raise_for_status()
                history = response.json()
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("completed"):
                        return True
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Status check failed for {prompt_id}: {exc}")
            time.sleep(2)

    def is_healthy(self) -> bool:
        try:
            response = requests.get(f"{self.server_url}/system_stats", timeout=5)
            return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

