# backend/core/engine/image.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from diffusers import AutoPipelineForText2Image

from . import config as cfg
from .utils import resolve_image_model, get_optimal_dtype


class ZImageEngine:
    """
    Z-Image Turbo 텍스트 → 이미지 엔진 래퍼

    - resolve_image_model()로 로컬/HF 경로 자동 처리
    - generate() 호출 시 이미지를 파일로 저장하고, 저장 경로(Path)를 반환
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        self.device = device or cfg.DEVICE
        self.dtype = get_optimal_dtype()

        # utils에서 모델 경로 가져오기
        resolved_model_id, cache_dir = resolve_image_model()
        self.model_id = model_id or resolved_model_id
        self.cache_dir = cache_dir

        print(f"[ZImageEngine] 모델 로드 중: {self.model_id}")
        print(f"[ZImageEngine] device={self.device}, dtype={self.dtype}")

        # 로드 옵션
        from_kwargs = {
            "torch_dtype": self.dtype,
        }
        if self.cache_dir is not None:
            from_kwargs["cache_dir"] = self.cache_dir

        # Z-Image Turbo는 AutoPipelineForText2Image로 로드 가능
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            self.model_id,
            **from_kwargs,
        )

        if self.device == "cuda":
            # GPU 사용
            self.pipe.to(self.device)
            # 필요하면 아래 옵션들 켜도 됨 (VRAM 상황 보고)
            # self.pipe.enable_model_cpu_offload()
        else:
            self.pipe.to("cpu")

    # --------------------------
    # 메인: 이미지 생성
    # --------------------------
    def generate(
        self,
        *,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        output_path: str | Path = "output/z_image.png",
    ) -> Path:
        """
        텍스트 프롬프트로 이미지 생성 후, 지정된 경로에 저장.

        Args:
            prompt: 기본 프롬프트
            negative_prompt: 네거티브 프롬프트
            width, height: 해상도 (None이면 config 기본값 사용)
            num_inference_steps: 디퓨전 스텝 수
            guidance_scale: CFG 스케일
            seed: 랜덤 시드 (None이면 랜덤)
            output_path: 저장할 파일 경로

        Returns:
            Path: 저장된 파일 경로
        """
        width = width or cfg.DEFAULT_WIDTH
        height = height or cfg.DEFAULT_HEIGHT
        steps = num_inference_steps or cfg.DEFAULT_STEPS
        guidance = (
            cfg.DEFAULT_GUIDANCE_SCALE
            if guidance_scale is None
            else guidance_scale
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"[ZImageEngine] 이미지 생성 시작")
        print(f"[ZImageEngine] prompt: {prompt}")
        print(f"[ZImageEngine] negative: {negative_prompt}")
        print(
            f"[ZImageEngine] size={width}x{height}, steps={steps}, guidance={guidance}, seed={seed}"
        )

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        )

        image = result.images[0]
        image.save(output_path)
        print(f"[ZImageEngine] 이미지 저장 완료: {output_path}")

        return output_path
