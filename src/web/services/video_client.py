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
            camera_prompt=camera_prompt
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
        motion_bucket_id: int,   # 현재는 SVD 워크플로에서 안 씀 (자리 유지용)
        camera_prompt: str,      # LLM/다중 레이어에서 만든 연출 프롬프트
    ) -> Dict[str, Any]:
        """
        Stable Video Diffusion 정식 워크플로(svd_mp4.json) 기반으로
        ComfyUI /prompt 에 바로 보낼 수 있는 그래프를 만든다.

        1) svd_mp4.json 불러오기
        2) __INPUT_IMAGE__, __CAMERA_PROMPT__, __FPS__, __OUTNAME__ 치환
        3) JSON의 nodes/links 구조를 ComfyUI API 형식으로 변환:
           {"1": {"class_type": "...", "inputs": {...}}, ...}
        """

        import json
        import shutil

        # 1) ComfyUI input 폴더로 이미지 복사
        comfyui_root = Path(
            "C:/Users/moong/Desktop/Project/AI_shorts_factory/engine/comfyui"
        )
        comfyui_input = comfyui_root / "input"
        comfyui_input.mkdir(exist_ok=True)

        target_image = comfyui_input / image_path.name
        shutil.copy2(image_path, target_image)

        image_name = image_path.name
        out_prefix = output_path.with_suffix("").name

        # 2) SVD 워크플로 JSON 로드
        workflow_path = comfyui_root / "workflows" / "svd_mp4.json"
        if not workflow_path.exists():
            raise FileNotFoundError(f"SVD workflow JSON not found: {workflow_path}")

        with workflow_path.open("r", encoding="utf-8") as f:
            workflow_json = json.load(f)

        nodes = workflow_json.get("nodes", [])
        links_list = workflow_json.get("links", [])

        # link_id → (from_id, from_slot, to_id, to_slot) 매핑 구성
        link_map = {}
        for link in links_list:
            # [link_id, from_id, from_slot, to_id, to_slot]
            if len(link) >= 5:
                link_id, from_id, from_slot, to_id, to_slot = link[:5]
                link_map[link_id] = (from_id, from_slot, to_id, to_slot)

        # 3) 플레이스홀더 치환 (노드 레벨)
        for node in nodes:
            ntype = node.get("type")

            # LoadImage: 입력 이미지 파일명 치환
            if ntype == "LoadImage":
                widgets = node.get("widgets_values", [])
                if widgets:
                    # ["__INPUT_IMAGE__", "image"] 형태
                    widgets[0] = image_name
                    node["widgets_values"] = widgets

            # CLIPTextEncode: 카메라/연출 프롬프트 치환
            elif ntype == "CLIPTextEncode":
                widgets = node.get("widgets_values", [])
                if widgets:
                    # ["__CAMERA_PROMPT__"]
                    widgets[0] = camera_prompt
                    node["widgets_values"] = widgets

            # VHS_VideoCombine: fps / 출력 파일 prefix 치환
            elif ntype == "VHS_VideoCombine":
                widgets = node.get("widgets_values", {})
                # 이 노드는 widgets_values가 dict 형태
                if isinstance(widgets, dict):
                    widgets["frame_rate"] = fps
                    widgets["filename_prefix"] = out_prefix
                    node["widgets_values"] = widgets

        # 4) ComfyUI /prompt 형식으로 변환
        prompt_graph: Dict[str, Any] = {}

        for node in nodes:
            node_id = node["id"]
            node_type = node["type"]
            node_inputs_list = node.get("inputs", [])

            # 기본 연결: links 정보를 사용해 입력 간선 구성
            inputs_dict: Dict[str, Any] = {}

            for inp in node_inputs_list:
                inp_name = inp.get("name")
                link_id = inp.get("link")
                if inp_name is None:
                    continue
                if link_id is not None and link_id in link_map:
                    from_id, from_slot, _, _ = link_map[link_id]
                    inputs_dict[inp_name] = [str(from_id), from_slot]

            # 타입별로 우리가 직접 넣어야 하는 파라미터들 override

            # LoadImage: image 파일경로 직접 지정
            if node_type == "LoadImage":
                inputs_dict = {
                    "image": image_name,
                }

            # CLIPTextEncode: text 인자로 카메라/연출 프롬프트 넣기
            elif node_type == "CLIPTextEncode":
                inputs_dict = {
                    "text": camera_prompt,
                }

            # VHS_VideoCombine: images 연결 + fps/filename_prefix 등 세팅
            elif node_type == "VHS_VideoCombine":
                # 위에서 links 기반으로 만든 images 연결 유지
                # (보통 inputs_dict["images"] 가 이미 세팅돼 있음)
                inputs_dict["frame_rate"] = fps
                inputs_dict["loop_count"] = 0
                inputs_dict["filename_prefix"] = out_prefix
                inputs_dict["format"] = "video/mp4"
                # 필요하면 나중에 crf, save_metadata 등도 여기서 조정 가능

            # 최종 노드 정의 작성
            prompt_graph[str(node_id)] = {
                "class_type": node_type,
                "inputs": inputs_dict,
            }

        logger.debug(
            f"SVD workflow (svd_mp4.json 기반) 준비 완료: "
            f"image={image_name}, fps={fps}, out_prefix={out_prefix}, "
            f"camera_prompt={camera_prompt}"
        )

        # ✅ 이제는 ComfyUI가 기대하는 형태의 그래프만 리턴
        return prompt_graph

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
