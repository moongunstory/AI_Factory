"""워커 메인 루프 - 파일 기반 작업 큐 감시"""
import time
import json
from pathlib import Path

from worker.processor import VideoWorkflowProcessor


def main():
    """워커 메인 루프 (동기 실행)"""
    print("\n" + "="*60)
    print("🚀 AI Factory Worker Started")
    print("="*60)
    print("브라우저 자동화 워커가 시작되었습니다.")
    print("작업 큐를 감시합니다: queue/pending/")
    print("Ctrl+C로 종료할 수 있습니다.")
    print("="*60 + "\n")

    processor = VideoWorkflowProcessor()

    queue_dir = Path("queue")
    pending_dir = queue_dir / "pending"
    processing_dir = queue_dir / "processing"

    # 디렉토리 확인
    pending_dir.mkdir(parents=True, exist_ok=True)
    processing_dir.mkdir(parents=True, exist_ok=True)

    try:
        while True:
            # pending 디렉토리 감시
            job_files = list(pending_dir.glob("*.json"))

            if job_files:
                print(f"📥 새 작업 발견: {len(job_files)}개")

                for job_file in job_files:
                    print(f"\n처리 중: {job_file.name}")

                    try:
                        # processing으로 이동
                        processing_file = processing_dir / job_file.name
                        job_file.rename(processing_file)

                        # 작업 데이터 로드
                        job_data = json.loads(processing_file.read_text(encoding="utf-8"))

                        # 작업 처리
                        processor.process_job(job_data)

                    except Exception as e:
                        print(f"❌ 작업 처리 중 오류: {e}")
                        # 오류 발생 시에도 계속 진행
                        continue

            # 1초 대기 (폴링 간격)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("⏹️  Worker 종료 중...")
        print("="*60)
        processor.cleanup()
        print("✅ Worker 종료 완료\n")

    except Exception as e:
        print(f"\n❌ Worker 오류: {e}")
        processor.cleanup()


if __name__ == "__main__":
    main()
