# backend/core/engine/video.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video

from . import config as cfg


class SvdVideoEngine:
    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        self.device = device or cfg.DEVICE
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # utils에서 모델 경로 가져오기
        from .utils import resolve_video_model
        resolved_model_id, cache_dir = resolve_video_model()
        self.model_id = model_id or resolved_model_id
        self.cache_dir = cache_dir

        print(f"[SvdVideoEngine] 모델 로드 중: {self.model_id}")
        print(f"[SvdVideoEngine] device={self.device}, dtype={self.dtype}")

        # 로드 옵션
        from_kwargs = {
            "torch_dtype": self.dtype,
            "variant": "fp16",
        }
        if self.cache_dir is not None:
            from_kwargs["cache_dir"] = self.cache_dir

        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.model_id,
            **from_kwargs,
        )

        # ⚠️ 기본적으로는 CPU offload 사용 (VRAM 부족 대비)
        if self.device == "cuda":
            self.pipe.enable_model_cpu_offload()
            if hasattr(self.pipe, "enable_attention_slicing"):
                self.pipe.enable_attention_slicing("max")

    # --------------------------
    # GPU 전용 모드 (속도 최적화)
    # --------------------------
    def enable_gpu_only(self):
        """
        CPU offload 비활성화하고 전체 모델을 GPU에 올림
        VRAM 충분할 때 속도 향상
        """
        if self.device == "cuda":
            # CPU offload 끄고 GPU로 직접 이동
            self.pipe.to(self.device)
            if hasattr(self.pipe, "enable_attention_slicing"):
                self.pipe.enable_attention_slicing("max")
            print("[SvdVideoEngine] GPU 전용 모드 활성화 (CPU offload 비활성화)")

    # --------------------------
    # 메인: 비디오 생성
    # --------------------------
    def generate(
        self,
        image_path: str | Path,
        *,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        motion_bucket_id: Optional[int] = None,
        noise_aug_strength: Optional[float] = None,
        decode_chunk_size: Optional[int] = None,
        seed: int = 0,
        output_path: str | Path = "output/svd_output.mp4",
    ) -> Path:
        """
        Stable Video Diffusion으로 비디오 생성

        Args:
            image_path: 베이스 이미지 경로
            num_frames: 생성할 프레임 수 (None이면 config 기본값)
            fps: 출력 비디오 FPS
            motion_bucket_id: 모션 강도 (클수록 더 크게 움직임)
            noise_aug_strength: 베이스 이미지에 섞을 노이즈 양
            decode_chunk_size: VAE 디코드 chunk 크기 (메모리 vs 속도)
            seed: 랜덤 시드
            output_path: 저장할 mp4 경로
        """
        image_path = Path(image_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # config에서 기본값 가져오기
        num_frames = num_frames or cfg.SVD_NUM_FRAMES
        fps = fps or cfg.SVD_FPS
        motion_bucket_id = motion_bucket_id or cfg.SVD_MOTION_BUCKET_ID
        noise_aug_strength = (
            noise_aug_strength
            if noise_aug_strength is not None
            else cfg.SVD_NOISE_AUG_STRENGTH
        )
        decode_chunk_size = (
            decode_chunk_size
            if decode_chunk_size is not None
            else cfg.SVD_DECODE_CHUNK_SIZE
        )

        print(f"[SvdVideoEngine] 입력 이미지: {image_path}")
        print(
            f"[SvdVideoEngine] frames={num_frames}, fps={fps}, "
            f"motion_bucket_id={motion_bucket_id}, noise_aug_strength={noise_aug_strength}, "
            f"decode_chunk_size={decode_chunk_size}, seed={seed}"
        )

        # 이미지 로드 & 해상도 맞추기 (9:16 세로 비율)
        image = load_image(str(image_path))
        image = image.resize((cfg.SVD_DEFAULT_WIDTH, cfg.SVD_DEFAULT_HEIGHT))

        generator = torch.Generator(device=self.device).manual_seed(seed)

        # 비디오 생성
        result = self.pipe(
            image,
            num_frames=num_frames,
            decode_chunk_size=decode_chunk_size,
            generator=generator,
            motion_bucket_id=motion_bucket_id,
            noise_aug_strength=noise_aug_strength,
        )

        frames = result.frames[0]
        export_to_video(frames, str(output_path), fps=fps)
        print(f"[SvdVideoEngine] 비디오 저장 완료: {output_path}")

        return output_path
