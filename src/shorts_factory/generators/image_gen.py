"""
이미지 생성 모듈

Stable Diffusion, DALL-E, ComfyUI 등과 연동하여
프롬프트로부터 실제 이미지를 생성합니다.

현재는 스텁 구현이며, 실제 생성 로직은 추후 구현 예정입니다.
"""

import logging
import time
from pathlib import Path
from typing import Optional

import requests
from requests.exceptions import RequestException

from config.config import (
    IMAGE_GEN_API_URL,
    IMAGES_DIR,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
)
from src.shorts_factory.core.schemas import ShotPrompt, GeneratedImage

logger = logging.getLogger(__name__)


# ============================================================================
# 이미지 생성기 클래스
# ============================================================================


class ImageGenerator:
    """
    이미지 생성기

    Stable Diffusion WebUI API 또는 ComfyUI와 통신하여 이미지 생성

    지원 예정:
    - Automatic1111 WebUI API
    - ComfyUI API
    - Stable Diffusion Python API
    - DALL-E API (OpenAI)
    """

    def __init__(
        self,
        api_url: str = IMAGE_GEN_API_URL,
        output_dir: Path = IMAGES_DIR,
        backend: str = "automatic1111"  # "automatic1111", "comfyui", "dalle"
    ):
        """
        Args:
            api_url: 이미지 생성 API URL
            output_dir: 생성된 이미지 저장 디렉토리
            backend: 사용할 백엔드 ("automatic1111", "comfyui", "dalle")
        """
        self.api_url = api_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backend = backend

        logger.info(f"이미지 생성기 초기화: {backend} @ {api_url}")

    def test_connection(self) -> bool:
        """
        API 서버 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            if self.backend == "automatic1111":
                # Automatic1111 WebUI의 health check 엔드포인트
                response = requests.get(
                    f"{self.api_url}/sdapi/v1/options",
                    timeout=5
                )
                return response.status_code == 200

            elif self.backend == "comfyui":
                # ComfyUI의 health check
                response = requests.get(
                    f"{self.api_url}/system_stats",
                    timeout=5
                )
                return response.status_code == 200

            else:
                logger.warning(f"백엔드 '{self.backend}'의 연결 테스트 미구현")
                return False

        except RequestException as e:
            logger.error(f"이미지 생성 서버 연결 실패: {e}")
            return False

    def generate_image(
        self,
        shot_prompt: ShotPrompt,
        save_path: Optional[Path] = None
    ) -> GeneratedImage:
        """
        단일 샷에 대한 이미지 생성

        Args:
            shot_prompt: 샷 프롬프트 (positive/negative 포함)
            save_path: 저장 경로 (None이면 자동 생성)

        Returns:
            GeneratedImage 객체

        TODO:
            - 실제 Stable Diffusion API 호출 구현
            - 이미지 저장 로직 구현
            - 에러 핸들링 강화
        """
        start_time = time.time()

        if save_path is None:
            save_path = self.output_dir / f"{shot_prompt.shot_id}.png"

        logger.info(f"이미지 생성 시작: {shot_prompt.shot_id}")
        logger.debug(f"  Positive: {shot_prompt.positive_prompt[:100]}...")
        logger.debug(f"  Params: {shot_prompt.generation_params}")

        # TODO: 실제 구현 (현재는 스텁)
        # 실제 구현 시:
        #   1. shot_prompt.generation_params에서 파라미터 추출
        #   2. API 엔드포인트에 POST 요청
        #   3. 생성된 이미지 다운로드
        #   4. save_path에 저장

        if self.backend == "automatic1111":
            generated_image = self._generate_automatic1111(shot_prompt, save_path)
        elif self.backend == "comfyui":
            generated_image = self._generate_comfyui(shot_prompt, save_path)
        else:
            raise NotImplementedError(f"백엔드 '{self.backend}' 미구현")

        generation_time = time.time() - start_time
        logger.info(f"이미지 생성 완료: {shot_prompt.shot_id} ({generation_time:.2f}초)")

        return generated_image

    def _generate_automatic1111(
        self,
        shot_prompt: ShotPrompt,
        save_path: Path
    ) -> GeneratedImage:
        """
        Automatic1111 WebUI API를 통한 이미지 생성

        TODO: 실제 구현
        """
        logger.warning("⚠️  Automatic1111 백엔드 미구현 - 스텁 반환")

        # 스텁: 더미 데이터 반환
        return GeneratedImage(
            shot_id=shot_prompt.shot_id,
            image_path=str(save_path),
            thumbnail_path=None,
            generation_time_seconds=2.5,  # 더미 값
            seed_used=shot_prompt.generation_params.seed,
            metadata={
                "backend": "automatic1111 (stub)",
                "positive_prompt": shot_prompt.positive_prompt[:50] + "...",
                "width": shot_prompt.generation_params.width,
                "height": shot_prompt.generation_params.height,
            }
        )

        # TODO: 실제 구현 예시
        # payload = {
        #     "prompt": shot_prompt.positive_prompt,
        #     "negative_prompt": shot_prompt.negative_prompt,
        #     "width": shot_prompt.generation_params.width,
        #     "height": shot_prompt.generation_params.height,
        #     "steps": shot_prompt.generation_params.steps,
        #     "cfg_scale": shot_prompt.generation_params.cfg_scale,
        #     "sampler_name": shot_prompt.generation_params.sampler,
        #     "seed": shot_prompt.generation_params.seed or -1,
        # }
        #
        # response = requests.post(
        #     f"{self.api_url}/sdapi/v1/txt2img",
        #     json=payload
        # )
        # response.raise_for_status()
        # image_data = response.json()
        #
        # # base64 이미지 디코드 및 저장
        # import base64
        # image_bytes = base64.b64decode(image_data["images"][0])
        # save_path.write_bytes(image_bytes)

    def _generate_comfyui(
        self,
        shot_prompt: ShotPrompt,
        save_path: Path
    ) -> GeneratedImage:
        """
        ComfyUI API를 통한 이미지 생성

        TODO: 실제 구현
        """
        logger.warning("⚠️  ComfyUI 백엔드 미구현 - 스텁 반환")

        return GeneratedImage(
            shot_id=shot_prompt.shot_id,
            image_path=str(save_path),
            thumbnail_path=None,
            generation_time_seconds=2.5,
            seed_used=shot_prompt.generation_params.seed,
            metadata={"backend": "comfyui (stub)"}
        )

    def generate_batch(
        self,
        shot_prompts: list[ShotPrompt]
    ) -> list[GeneratedImage]:
        """
        배치 생성: 여러 샷 동시 처리

        Args:
            shot_prompts: 샷 프롬프트 목록

        Returns:
            생성된 이미지 목록
        """
        logger.info(f"배치 이미지 생성 시작: {len(shot_prompts)}개 샷")

        generated_images = []
        for i, shot_prompt in enumerate(shot_prompts, 1):
            logger.info(f"진행: {i}/{len(shot_prompts)}")
            image = self.generate_image(shot_prompt)
            generated_images.append(image)

        logger.info(f"배치 생성 완료: {len(generated_images)}개 이미지")
        return generated_images


# ============================================================================
# 편의 함수
# ============================================================================


def generate_images_from_prompts(
    shot_prompts: list[ShotPrompt],
    backend: str = "automatic1111",
    api_url: str = IMAGE_GEN_API_URL
) -> list[GeneratedImage]:
    """
    프롬프트 목록으로부터 이미지 생성 (함수형 인터페이스)

    Args:
        shot_prompts: 샷 프롬프트 목록
        backend: 사용할 백엔드
        api_url: API URL

    Returns:
        생성된 이미지 목록
    """
    generator = ImageGenerator(api_url=api_url, backend=backend)

    if not generator.test_connection():
        logger.warning("이미지 생성 서버 연결 실패 - 계속 진행하지만 실패할 수 있음")

    return generator.generate_batch(shot_prompts)
