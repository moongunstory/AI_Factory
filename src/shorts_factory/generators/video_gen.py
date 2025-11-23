"""
비디오 생성 모듈

생성된 이미지들을 비디오로 합성합니다.

FFmpeg를 사용하여:
- 이미지 시퀀스를 비디오로 변환
- 트랜지션 효과 적용
- 오디오 트랙 추가 (선택사항)
- 최종 비디오 인코딩

현재는 스텁 구현이며, 실제 생성 로직은 추후 구현 예정입니다.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from config.config import (
    FFMPEG_PATH,
    VIDEOS_DIR,
    DEFAULT_VIDEO_FPS,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_AUDIO_CODEC,
    DEFAULT_VIDEO_BITRATE,
)
from src.shorts_factory.core.schemas import (
    GeneratedImage,
    GeneratedVideo,
    ScenePlanPackage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 비디오 생성기 클래스
# ============================================================================


class VideoGenerator:
    """
    비디오 생성기

    이미지들을 비디오로 합성하고 트랜지션, 음악 등을 추가합니다.

    지원 예정:
    - FFmpeg를 통한 이미지 시퀀스 → 비디오 변환
    - 트랜지션 효과 (크로스페이드, 디졸브 등)
    - 오디오 트랙 추가
    - 자막/캡션 오버레이
    - 최종 인코딩 (H.264, H.265)
    """

    def __init__(
        self,
        ffmpeg_path: str = FFMPEG_PATH,
        output_dir: Path = VIDEOS_DIR,
        fps: int = DEFAULT_VIDEO_FPS,
        video_codec: str = DEFAULT_VIDEO_CODEC,
        bitrate: str = DEFAULT_VIDEO_BITRATE,
    ):
        """
        Args:
            ffmpeg_path: FFmpeg 실행 파일 경로
            output_dir: 출력 비디오 디렉토리
            fps: 프레임레이트 (기본 24fps)
            video_codec: 비디오 코덱 (기본 libx264)
            bitrate: 비트레이트 (기본 5M)
        """
        self.ffmpeg_path = ffmpeg_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.video_codec = video_codec
        self.bitrate = bitrate

        logger.info(f"비디오 생성기 초기화: {fps}fps, {video_codec}, {bitrate}")

    def test_ffmpeg(self) -> bool:
        """
        FFmpeg 설치 및 실행 가능 여부 확인

        Returns:
            FFmpeg 사용 가능 여부
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                logger.info(f"FFmpeg 확인: {version_line}")
                return True
            return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"FFmpeg 실행 실패: {e}")
            return False

    def generate_video(
        self,
        images: list[GeneratedImage],
        scene_plan: ScenePlanPackage,
        output_filename: str = "output.mp4",
        audio_path: Optional[Path] = None,
        add_transitions: bool = True,
    ) -> GeneratedVideo:
        """
        이미지 목록으로부터 비디오 생성

        Args:
            images: 생성된 이미지 목록 (순서대로)
            scene_plan: 씬 계획 (각 샷의 duration 정보 포함)
            output_filename: 출력 파일명
            audio_path: 오디오 파일 경로 (선택사항)
            add_transitions: 트랜지션 효과 추가 여부

        Returns:
            GeneratedVideo 객체

        TODO:
            - FFmpeg를 통한 실제 비디오 합성 구현
            - 트랜지션 효과 구현 (crossfade filter 등)
            - 오디오 트랙 믹싱 구현
            - 자막 오버레이 구현
        """
        start_time = time.time()

        output_path = self.output_dir / output_filename
        logger.info(f"비디오 생성 시작: {output_filename}")
        logger.info(f"  입력 이미지: {len(images)}개")
        logger.info(f"  트랜지션: {'활성화' if add_transitions else '비활성화'}")
        if audio_path:
            logger.info(f"  오디오: {audio_path}")

        # TODO: 실제 구현 (현재는 스텁)
        # 실제 구현 시:
        #   1. 이미지 경로 목록 생성
        #   2. scene_plan에서 각 샷의 duration 추출
        #   3. FFmpeg 명령어 구성
        #   4. 트랜지션 효과가 필요하면 complex filter 사용
        #   5. 오디오가 있으면 믹싱
        #   6. 최종 비디오 인코딩

        logger.warning("⚠️  비디오 생성 기능 미구현 - 스텁 반환")

        # 예상 총 duration 계산
        total_duration = sum(
            shot.duration_seconds
            for scene in scene_plan.scenes
            for shot in scene.shots
        )

        # 스텁: 더미 데이터 반환
        generated_video = GeneratedVideo(
            video_path=str(output_path),
            duration_seconds=total_duration,
            resolution=f"720x1280",
            fps=self.fps,
            filesize_mb=0.0,  # 실제로 생성되지 않음
            shot_count=len(images),
            generation_time_seconds=time.time() - start_time,
        )

        logger.info(f"비디오 생성 완료 (스텁): {output_filename}")
        return generated_video

        # TODO: 실제 FFmpeg 구현 예시
        # self._create_video_with_ffmpeg(
        #     images=images,
        #     durations=[각 샷의 duration],
        #     output_path=output_path,
        #     audio_path=audio_path,
        #     add_transitions=add_transitions
        # )

    def _create_video_with_ffmpeg(
        self,
        images: list[GeneratedImage],
        durations: list[float],
        output_path: Path,
        audio_path: Optional[Path] = None,
        add_transitions: bool = True,
    ) -> None:
        """
        FFmpeg를 사용한 실제 비디오 생성

        TODO: 실제 구현
        """
        # 임시 파일 목록 생성
        # concat_file = self._create_concat_file(images, durations)

        # FFmpeg 명령어 구성
        # if add_transitions:
        #     # complex filter로 크로스페이드 적용
        #     filter_complex = self._build_transition_filter(images, durations)
        #     cmd = [
        #         self.ffmpeg_path,
        #         "-f", "concat",
        #         "-safe", "0",
        #         "-i", str(concat_file),
        #         "-filter_complex", filter_complex,
        #         "-c:v", self.video_codec,
        #         "-b:v", self.bitrate,
        #         "-pix_fmt", "yuv420p",
        #         str(output_path)
        #     ]
        # else:
        #     # 단순 concat
        #     cmd = [
        #         self.ffmpeg_path,
        #         "-f", "concat",
        #         "-safe", "0",
        #         "-i", str(concat_file),
        #         "-c:v", self.video_codec,
        #         "-b:v", self.bitrate,
        #         "-pix_fmt", "yuv420p",
        #         str(output_path)
        #     ]
        #
        # # 오디오 추가
        # if audio_path:
        #     cmd.extend(["-i", str(audio_path), "-c:a", DEFAULT_AUDIO_CODEC])
        #
        # # 실행
        # subprocess.run(cmd, check=True)

        raise NotImplementedError("FFmpeg 비디오 생성 미구현")

    def _build_transition_filter(
        self,
        images: list[GeneratedImage],
        durations: list[float],
        transition_duration: float = 0.5
    ) -> str:
        """
        FFmpeg complex filter 문자열 생성 (크로스페이드 트랜지션)

        TODO: 실제 구현
        """
        # Example: "[0][1]xfade=transition=fade:duration=0.5:offset=2[v01];"
        #          "[v01][2]xfade=transition=fade:duration=0.5:offset=4[v02];"
        raise NotImplementedError("트랜지션 필터 빌드 미구현")

    def add_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        기존 비디오에 오디오 트랙 추가

        Args:
            video_path: 입력 비디오 경로
            audio_path: 오디오 파일 경로
            output_path: 출력 경로 (None이면 자동 생성)

        Returns:
            출력 비디오 경로

        TODO: 실제 구현
        """
        if output_path is None:
            stem = video_path.stem
            output_path = video_path.parent / f"{stem}_with_audio.mp4"

        logger.info(f"오디오 추가: {video_path.name} + {audio_path.name}")

        # TODO: FFmpeg 명령어
        # ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac output.mp4

        raise NotImplementedError("오디오 추가 기능 미구현")

    def add_subtitles(
        self,
        video_path: Path,
        subtitle_text: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        비디오에 자막 추가

        Args:
            video_path: 입력 비디오 경로
            subtitle_text: 자막 텍스트
            output_path: 출력 경로

        Returns:
            출력 비디오 경로

        TODO: 실제 구현
        """
        logger.warning("⚠️  자막 추가 기능 미구현")
        raise NotImplementedError("자막 추가 기능 미구현")


# ============================================================================
# 편의 함수
# ============================================================================


def create_video_from_images(
    images: list[GeneratedImage],
    scene_plan: ScenePlanPackage,
    output_filename: str = "short_video.mp4",
    audio_path: Optional[Path] = None,
) -> GeneratedVideo:
    """
    이미지로부터 비디오 생성 (함수형 인터페이스)

    Args:
        images: 생성된 이미지 목록
        scene_plan: 씬 계획
        output_filename: 출력 파일명
        audio_path: 오디오 파일 (선택사항)

    Returns:
        GeneratedVideo 객체
    """
    generator = VideoGenerator()

    if not generator.test_ffmpeg():
        logger.warning("FFmpeg를 찾을 수 없습니다 - 비디오 생성 실패할 수 있음")

    return generator.generate_video(
        images=images,
        scene_plan=scene_plan,
        output_filename=output_filename,
        audio_path=audio_path,
    )
