from __future__ import annotations
import uuid
import time
from pathlib import Path
from typing import Any, Dict

import requests

from src.common.config import Config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ComfyUIVideoClient:
    """Stable Video Diffusion (SVD) video generator via ComfyUI."""

    # 카메라 프롬프트 → motion_bucket_id 매핑 (원할 때 나중에 튜닝)
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
        """
        하나의 이미지에서 SVD로 짧은 mp4 클립 생성.
        duration_sec, fps → 프레임 수로 변환해서 SVD에 넘김.
        """

        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 최소 프레임 수는 너무 짧지 않도록 8 프레임 이상으로 보정
        num_frames = max(8, int(duration_sec * fps))

        motion_bucket_id = self.CAMERA_TO_MOTION.get(camera_prompt, 127)

        # ComfyUI용 prompt 그래프 생성
        prompt_graph = self.build_svd_prompt(
            image_path=image_path,
            output_path=output_path,
            num_frames=num_frames,
            fps=fps,
            motion_bucket_id=motion_bucket_id,
        )

        # ComfyUI API는 {"prompt": {...}, "client_id": "..."} 형식을 기대함
        prompt_id = self._queue_prompt(prompt_graph)
        logger.info(
            f"[ComfyUI] Queued SVD prompt: {prompt_id} "
            f"(frames={num_frames}, fps={fps}, motion={motion_bucket_id})"
        )

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
        """
        Stable Video Diffusion workflow
        VIDEO_USE_UPSCALE=true -> low-res generation + upscale

        IMPORTANT: This workflow uses SVD_img2vid_Conditioning which outputs
        video-compatible conditioning tensors. The KSampler must be able to
        handle video latents (may be 5D: batch, time, channels, height, width).
        """

        # Copy image to ComfyUI input folder
        import shutil
        comfyui_input = Path("C:/Users/moong/Desktop/Project/AI_shorts_factory/engine/comfyui/input")
        comfyui_input.mkdir(exist_ok=True)

        target_image = comfyui_input / image_path.name
        shutil.copy2(image_path, target_image)

        image_name = image_path.name
        out_prefix = output_path.with_suffix("").name

        # Resolution settings: use low-res for upscale strategy
        if Config.VIDEO_USE_UPSCALE:
            base_width = Config.VIDEO_BASE_WIDTH
            base_height = Config.VIDEO_BASE_HEIGHT
            target_width = Config.VIDEO_TARGET_WIDTH
            target_height = Config.VIDEO_TARGET_HEIGHT
            use_upscale = True
            logger.info(f"Using low-res + upscale strategy: {base_width}x{base_height} → {target_width}x{target_height}")
        else:
            base_width = Config.VIDEO_TARGET_WIDTH
            base_height = Config.VIDEO_TARGET_HEIGHT
            use_upscale = False
            logger.info(f"Using direct generation: {base_width}x{base_height}")

        # Build SVD workflow
        # Note: SVD_img2vid_Conditioning outputs video-compatible tensors
        # Some ComfyUI versions require VideoLinearCFGGuidance between model and sampler
        workflow = {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image_name,
                },
            },
            "2": {
                "class_type": "SVD_img2vid_Conditioning",
                "inputs": {
                    "width": base_width,
                    "height": base_height,
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
                    "clip_name": "model.safetensors",
                },
            },
            "4": {
                "class_type": "VAELoader",
                "inputs": {
                    "vae_name": "wan2.2_vae.safetensors",
                },
            },
            "5": {
                "class_type": "ImageOnlyCheckpointLoader",
                "inputs": {
                    "ckpt_name": "svd.safetensors",
                },
            },
            # Try using VideoLinearCFGGuidance to handle video tensors properly
            # This node adapts the model to work with video conditioning
            "5a": {
                "class_type": "VideoLinearCFGGuidance",
                "inputs": {
                    "model": ["5", 0],
                    "min_cfg": 1.0,
                },
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 2.5,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["5a", 0],  # Use guided model instead of raw model
                    "positive": ["2", 0],
                    "negative": ["2", 1],
                    "latent_image": ["2", 2],
                },
            },
        }

        logger.debug(f"SVD workflow nodes: LoadImage → SVD_Conditioning → VideoLinearCFGGuidance → KSampler")

        if use_upscale:
            # 저해상도 + 업스케일 워크플로우
            upscale_factor = target_width / base_width

            workflow.update({
                "7": {
                    "class_type": "LatentUpscaleBy",
                    "inputs": {
                        "samples": ["6", 0],
                        "scale_by": upscale_factor,
                        "upscale_method": "bicubic",  # bicubic, nearest, bilinear, bislerp
                    },
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["7", 0],
                        "vae": ["4", 0],
                    },
                },
                "9": {
                    "class_type": "VHS_VideoCombine",
                    "inputs": {
                        "frame_rate": fps,
                        "loop_count": 0,
                        "filename_prefix": out_prefix,
                        "format": "video/h264-mp4",
                        "pingpong": False,
                        "save_output": True,
                        "images": ["8", 0],
                    },
                },
            })
        else:
            # 기본 워크플로우 (업스케일 없음)
            workflow.update({
                "7": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["6", 0],
                        "vae": ["4", 0],
                    },
                },
                "8": {
                    "class_type": "VHS_VideoCombine",
                    "inputs": {
                        "frame_rate": fps,
                        "loop_count": 0,
                        "filename_prefix": out_prefix,
                        "format": "video/h264-mp4",
                        "pingpong": False,
                        "save_output": True,
                        "images": ["7", 0],
                    },
                },
            })

        return workflow

    def _queue_prompt(self, prompt_graph: Dict[str, Any]) -> str:
        """
        Queue prompt to ComfyUI /prompt endpoint.
        prompt_graph: Node ID → Node definition dict from build_svd_prompt.

        Raises:
            RuntimeError: If ComfyUI rejects the workflow (e.g., missing custom nodes)
        """
        client_id = str(uuid.uuid4())
        payload = {
            "prompt": prompt_graph,
            "client_id": client_id,
        }

        res = requests.post(
            f"{self.server_url}/prompt",
            json=payload,
            timeout=20,
        )

        # Check for HTTP errors
        try:
            res.raise_for_status()
        except Exception:
            error_body = res.text
            logger.error(
                "ComfyUI /prompt HTTP error: %s\nBody: %s",
                res.status_code,
                error_body,
            )

            # Provide helpful diagnostics for common errors
            if "VideoLinearCFGGuidance" in error_body:
                raise RuntimeError(
                    "ComfyUI missing 'VideoLinearCFGGuidance' custom node. "
                    "This is required for SVD video generation. "
                    "Please install ComfyUI custom nodes for Stable Video Diffusion. "
                    f"Original error: {error_body}"
                )
            elif "SVD_img2vid_Conditioning" in error_body:
                raise RuntimeError(
                    "ComfyUI missing 'SVD_img2vid_Conditioning' node. "
                    "Please install ComfyUI SVD custom nodes. "
                    f"Original error: {error_body}"
                )
            elif "dimension" in error_body.lower() or "tensor" in error_body.lower():
                raise RuntimeError(
                    "ComfyUI tensor dimension mismatch. "
                    "This usually means your ComfyUI/SVD version is incompatible. "
                    f"Original error: {error_body}"
                )
            else:
                raise RuntimeError(f"ComfyUI workflow validation failed: {error_body}")

        result = res.json()

        # Check if ComfyUI returned an error in the JSON response
        if "error" in result:
            error_msg = result["error"]
            logger.error(f"ComfyUI workflow error: {error_msg}")
            raise RuntimeError(f"ComfyUI workflow error: {error_msg}")

        # Return prompt_id (use client_id as fallback)
        return result.get("prompt_id", client_id)

    def _wait_for_completion(self, prompt_id: str, timeout: int) -> bool:
        """
        /history/{prompt_id} 폴링해서 완료 여부 확인.
        timeout=0이면 무제한 대기.
        """
        start = time.time()
        while True:
            # timeout이 0이 아니면 체크
            if timeout > 0 and (time.time() - start >= timeout):
                return False

            try:
                res = requests.get(
                    f"{self.server_url}/history/{prompt_id}",
                    timeout=8,
                )
                if res.status_code == 200:
                    hist = res.json().get(prompt_id, {})
                    if hist.get("status", {}).get("completed"):
                        return True
            except Exception:
                # 네트워크 잠깐 끊겨도 다시 시도
                pass
            time.sleep(2)

    def is_healthy(self) -> bool:
        try:
            r = requests.get(f"{self.server_url}/system_stats", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
