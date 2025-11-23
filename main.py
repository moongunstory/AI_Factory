#!/usr/bin/env python3
"""
AI Shorts Factory - 메인 실행 파일

유저가 스토리 아이디어를 입력하면:
  1. LLM이 스토리 확장
  2. 장면 계획 수립 (명도, 채도, 그림체 포함)
  3. 프롬프트 생성
  4. [TODO] 이미지 생성
  5. [TODO] 영상 합성

사용법:
    python main.py --logline "기사가 용을 물리치고 공주를 구한다" --duration 60 --genre fantasy

    # 또는 대화형 모드
    python main.py --interactive
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.shorts_factory.core.pipeline import generate_shorts_prompt_package
from src.shorts_factory.core.llm_client import test_connection
from src.shorts_factory.generators.image_gen import ImageGenerator
from src.shorts_factory.generators.video_gen import VideoGenerator
from src.shorts_factory.utils.helpers import (
    setup_logging,
    save_json,
    print_pipeline_summary,
)
from config.config import OUTPUT_DIR


def main():
    """메인 실행 함수"""

    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(
        description="AI Shorts Factory - 스토리에서 숏폼 비디오까지",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python main.py --logline "외계인이 지구에 도착한다" --duration 45 --genre sci-fi --tone mysterious
  python main.py --interactive
  python main.py --logline "요리사의 요리가 살아난다" --duration 30 --output my_cooking_short
        """
    )

    parser.add_argument(
        "--logline",
        type=str,
        help="스토리 아이디어 (한 문장)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="목표 영상 길이 (초, 기본값: 60)"
    )
    parser.add_argument(
        "--genre",
        type=str,
        help="장르 (예: fantasy, sci-fi, horror, comedy)"
    )
    parser.add_argument(
        "--tone",
        type=str,
        help="톤 (예: epic, mysterious, comedic, dark)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="출력 파일 이름 (확장자 제외, 기본값: 자동 생성)"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="대화형 모드로 실행"
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="이미지 생성까지 실행 (Stable Diffusion 필요)"
    )
    parser.add_argument(
        "--generate-video",
        action="store_true",
        help="비디오 생성까지 실행 (FFmpeg 필요)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 (기본값: INFO)"
    )

    args = parser.parse_args()

    # 로깅 초기화
    setup_logging(args.log_level)

    print("\n" + "=" * 80)
    print("🎬 AI SHORTS FACTORY")
    print("   스토리 → 프롬프트 → 이미지 → 비디오 자동 생성")
    print("=" * 80 + "\n")

    # LLM 서버 연결 테스트
    print("🔌 LLM 서버 연결 확인 중...")
    if not test_connection():
        print("❌ LLM 서버에 연결할 수 없습니다!")
        print("   로컬 Llama 서버가 실행 중인지 확인하세요.")
        print("   예: llama-server --model models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct --port 8000")
        sys.exit(1)
    print("✅ LLM 서버 연결 성공!\n")

    # 대화형 모드
    if args.interactive:
        run_interactive_mode()
        return

    # 로그라인 필수 확인
    if not args.logline:
        print("❌ 에러: --logline 인자가 필요합니다.")
        print("   예: python main.py --logline \"기사가 용을 물리친다\" --duration 60 --genre fantasy")
        print("   또는: python main.py --interactive")
        sys.exit(1)

    # 파이프라인 실행
    result = run_pipeline(
        logline=args.logline,
        duration=args.duration,
        genre=args.genre,
        tone=args.tone,
        generate_images=args.generate_images,
        generate_video=args.generate_video,
        output_name=args.output,
    )

    # 결과 요약 출력
    print_pipeline_summary(result)

    print("✅ 완료!")


def run_pipeline(
    logline: str,
    duration: int | None = None,
    genre: str | None = None,
    tone: str | None = None,
    generate_images: bool = False,
    generate_video: bool = False,
    output_name: str | None = None,
):
    """
    전체 파이프라인 실행

    Args:
        logline: 스토리 아이디어
        duration: 목표 길이 (초)
        genre: 장르
        tone: 톤
        generate_images: 이미지 생성 여부
        generate_video: 비디오 생성 여부
        output_name: 출력 파일 이름

    Returns:
        ShortsGenerationResult
    """
    print(f"📝 입력:")
    print(f"   스토리: {logline}")
    if duration:
        print(f"   길이: {duration}초")
    if genre:
        print(f"   장르: {genre}")
    if tone:
        print(f"   톤: {tone}")
    print()

    # Stage 1-3: 프롬프트 생성
    print("🚀 파이프라인 실행 중...\n")

    result = generate_shorts_prompt_package(
        logline=logline,
        target_duration_seconds=duration,
        tone=tone,
        genre=genre,
    )

    # 결과 저장
    if output_name is None:
        # 로그라인에서 안전한 파일명 생성
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in logline)
        safe_name = safe_name.replace(' ', '_')[:50]
        output_name = safe_name or "output"

    output_path = OUTPUT_DIR / f"{output_name}.json"
    save_json(result, output_path)
    print(f"\n💾 결과 저장: {output_path}")

    # Stage 4: 이미지 생성 (선택사항)
    if generate_images:
        print("\n🖼️  이미지 생성 중...")
        image_gen = ImageGenerator()

        if not image_gen.test_connection():
            print("⚠️  이미지 생성 서버에 연결할 수 없습니다. 이 단계를 건너뜁니다.")
        else:
            generated_images = image_gen.generate_batch(result.prompts.shots)
            result.generated_images = generated_images
            print(f"✅ {len(generated_images)}개 이미지 생성 완료")

            # 업데이트된 결과 재저장
            save_json(result, output_path)

    # Stage 5: 비디오 생성 (선택사항)
    if generate_video:
        if not result.generated_images:
            print("\n⚠️  비디오 생성을 위해서는 먼저 이미지를 생성해야 합니다.")
            print("   --generate-images 옵션을 함께 사용하세요.")
        else:
            print("\n🎥 비디오 생성 중...")
            video_gen = VideoGenerator()

            if not video_gen.test_ffmpeg():
                print("⚠️  FFmpeg를 찾을 수 없습니다. 이 단계를 건너뜁니다.")
            else:
                generated_video = video_gen.generate_video(
                    images=result.generated_images,
                    scene_plan=result.scene_plan,
                    output_filename=f"{output_name}.mp4"
                )
                result.generated_video = generated_video
                print(f"✅ 비디오 생성 완료: {generated_video.video_path}")

                # 최종 결과 저장
                save_json(result, output_path)

    return result


def run_interactive_mode():
    """대화형 모드 실행"""
    print("🎮 대화형 모드\n")

    print("스토리 아이디어를 입력하세요 (한 문장):")
    logline = input("> ").strip()

    if not logline:
        print("❌ 스토리를 입력하지 않았습니다. 종료합니다.")
        return

    print("\n목표 영상 길이 (초, Enter=60):")
    duration_input = input("> ").strip()
    duration = int(duration_input) if duration_input else 60

    print("\n장르 (예: fantasy, sci-fi, horror, comedy, Enter=건너뛰기):")
    genre = input("> ").strip() or None

    print("\n톤 (예: epic, mysterious, comedic, dark, Enter=건너뛰기):")
    tone = input("> ").strip() or None

    print("\n이미지 생성까지 실행하시겠습니까? (y/N):")
    generate_images = input("> ").strip().lower() == 'y'

    generate_video = False
    if generate_images:
        print("\n비디오 생성까지 실행하시겠습니까? (y/N):")
        generate_video = input("> ").strip().lower() == 'y'

    print("\n출력 파일 이름 (Enter=자동 생성):")
    output_name = input("> ").strip() or None

    print()

    # 파이프라인 실행
    result = run_pipeline(
        logline=logline,
        duration=duration,
        genre=genre,
        tone=tone,
        generate_images=generate_images,
        generate_video=generate_video,
        output_name=output_name,
    )

    print_pipeline_summary(result)
    print("✅ 완료!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
