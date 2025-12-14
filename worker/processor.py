"""작업 처리 로직"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

from worker.automation.chatgpt_workflow import ChatGPTWorkflow
from backend.core.debug_logger import save_error_log


class VideoWorkflowProcessor:
    """비디오 생성 워크플로우 처리기"""

    def __init__(self, queue_dir: str = ".data/queue", results_dir: str = ".data/output"):
        self.queue_dir = Path(queue_dir)
        self.results_dir = Path(results_dir)
        self.workflow: ChatGPTWorkflow = None

    def ensure_client(self):
        """ChatGPT 워크플로우 초기화 (필요 시)"""
        if not self.workflow:
            print("[Processor] ChatGPT 워크플로우 초기화 중...")
            self.workflow = ChatGPTWorkflow(use_system_profile=True)
            self.workflow.client.start_browser()

    def process_job(self, job_data: dict):
        """작업 처리 - 3단계 ChatGPT 워크플로우"""
        job_id = job_data["job_id"]
        story = job_data["story"]

        try:
            print(f"\n{'='*60}")
            print(f"🎬 작업 처리 시작: {job_id}")
            print(f"{'='*60}\n")

            # 클라이언트 초기화
            self.ensure_client()

            # 처리 시작 시간 기록
            self._update_job_status(job_id, "processing", started_at=datetime.utcnow().isoformat())

            # 단계별 진행 상태 업데이트 콜백
            def on_step_complete(step_num: int, result: str):
                print(f"[Processor] Step {step_num} 완료 콜백")
                step_names = {1: "expanded_story", 2: "storyboard", 3: "prompts"}
                self._update_job_status(
                    job_id,
                    "processing",
                    current_step=step_num,
                    **{f"step_{step_num}_result": result[:200]}  # 미리보기용
                )

            # 3단계 워크플로우 실행 (콜백 전달)
            result = self.workflow.run_three_step_workflow(story, on_step_complete=on_step_complete)

            # 결과 저장
            self._save_result(job_id, result)

            # 완료 처리
            self._move_to_completed(job_id, success=True)

            print(f"✅ 작업 완료: {job_id}\n")

        except Exception as e:
            print(f"❌ 작업 실패: {job_id}")
            print(f"   에러: {e}\n")

            # Save detailed error log to debug directory
            context = {
                "job_id": job_id,
                "story": story,
                "endpoint": "video_workflow"
            }
            page = self.workflow.client.driver if self.workflow else None
            save_error_log(e, context=context, page=page)

            self._move_to_completed(job_id, success=False, error=str(e))

    def _update_job_status(self, job_id: str, status: str, **kwargs):
        """작업 상태 업데이트"""
        processing_file = self.queue_dir / "processing" / f"{job_id}.json"

        if processing_file.exists():
            job_data = json.loads(processing_file.read_text(encoding="utf-8"))
            job_data["status"] = status
            job_data.update(kwargs)
            processing_file.write_text(json.dumps(job_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_result(self, job_id: str, result: dict):
        """결과 저장"""
        result_dir = self.results_dir / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        # 결과 JSON 저장
        result_file = result_dir / "result.json"
        result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        # 개별 텍스트 파일로도 저장
        if "expanded_story" in result:
            (result_dir / "expanded_story.txt").write_text(result["expanded_story"], encoding="utf-8")

        if "storyboard" in result:
            (result_dir / "storyboard.txt").write_text(result["storyboard"], encoding="utf-8")

        if "prompts" in result:
            (result_dir / "prompts.txt").write_text(result["prompts"], encoding="utf-8")

        print(f"[Processor] 결과 저장 완료: {result_dir}")

    def _move_to_completed(self, job_id: str, success: bool, error: str = None):
        """작업 완료 처리"""
        processing_file = self.queue_dir / "processing" / f"{job_id}.json"

        if not processing_file.exists():
            print(f"[Processor] Warning: Processing file not found: {job_id}")
            return

        # 작업 파일 읽기
        job_data = json.loads(processing_file.read_text(encoding="utf-8"))

        # 상태 업데이트
        job_data["status"] = "completed" if success else "failed"
        job_data["completed_at"] = datetime.utcnow().isoformat()

        if error:
            job_data["error"] = error

        # 적절한 디렉토리로 이동
        target_dir = self.queue_dir / ("completed" if success else "failed")
        target_file = target_dir / f"{job_id}.json"

        target_file.write_text(json.dumps(job_data, ensure_ascii=False, indent=2), encoding="utf-8")
        processing_file.unlink()

        print(f"[Processor] 작업 이동: processing → {target_dir.name}")

    def cleanup(self):
        """리소스 정리"""
        if self.workflow:
            try:
                self.workflow.close()
            except Exception as e:
                print(f"[Processor] Warning: Failed to close workflow: {e}")
