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
        Stable Video Diffusion 기본 워크플로우
        """
        
        # 이미지를 ComfyUI input 폴더로 복사
        import shutil
        comfyui_input = Path("C:/Users/moong/Desktop/Project/AI_shorts_factory/engine/comfyui/input")
        comfyui_input.mkdir(exist_ok=True)
        
        target_image = comfyui_input / image_path.name
        shutil.copy2(image_path, target_image)
        
        image_name = image_path.name
        out_prefix = output_path.with_suffix("").name

        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": image_name,
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
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 2.5,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["5", 0],          # ✅ Node 5 (ImageOnlyCheckpointLoader)
                    "positive": ["2", 0],       # ✅ Node 2의 positive 출력
                    "negative": ["2", 1],       # ✅ Node 2의 negative 출력
                    "latent_image": ["2", 2],   # ✅ Node 2의 latent 출력
                },
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],        # ✅ Node 6 (KSampler) 출력
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
                    "images": ["7", 0],         # ✅ Node 7 (VAEDecode) 출력
                },
            },
        }

    def _queue_prompt(self, prompt_graph: Dict[str, Any]) -> str:
        """
        ComfyUI /prompt 호출.
        prompt_graph: 위 build_svd_prompt가 반환한 '노드ID → 노드 정의' dict.
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

        # 여기서 400/500 같은 HTTP 에러가 나면 그대로 raise 해서 위에서 잡음
        try:
            res.raise_for_status()
        except Exception:
            logger.error(
                "ComfyUI /prompt HTTP error: %s\nBody: %s",
                res.status_code,
                res.text,
            )
            raise

        result = res.json()
        # ComfyUI가 돌려주는 prompt_id 사용 (없으면 client_id 그대로)
        return result.get("prompt_id", client_id)

    def _wait_for_completion(self, prompt_id: str, timeout: int) -> bool:
        """
        /history/{prompt_id} 폴링해서 완료 여부 확인.
        """
        start = time.time()
        while time.time() - start < timeout:
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
        return False

    def is_healthy(self) -> bool:
        try:
            r = requests.get(f"{self.server_url}/system_stats", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
