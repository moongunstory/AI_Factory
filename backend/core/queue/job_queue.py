"""파일 기반 작업 큐 관리자"""
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import VideoJob, JobStatus, JobResult


class JobQueue:
    """파일 시스템 기반 작업 큐"""

    def __init__(self, queue_dir: str = "queue", results_dir: str = "results"):
        self.queue_dir = Path(queue_dir)
        self.results_dir = Path(results_dir)

        # 디렉토리 생성
        for subdir in ["pending", "processing", "completed", "failed"]:
            (self.queue_dir / subdir).mkdir(parents=True, exist_ok=True)

        self.results_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, story: str) -> str:
        """새 작업 생성"""
        job_id = str(uuid.uuid4())

        job = VideoJob(
            job_id=job_id,
            story=story,
            status=JobStatus.PENDING
        )

        job_file = self.queue_dir / "pending" / f"{job_id}.json"
        job_file.write_text(job.model_dump_json(indent=2), encoding="utf-8")

        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        """작업 조회"""
        # 모든 상태 디렉토리 검색
        for status in ["pending", "processing", "completed", "failed"]:
            job_file = self.queue_dir / status / f"{job_id}.json"
            if job_file.exists():
                job_data = json.loads(job_file.read_text(encoding="utf-8"))

                # 결과가 있으면 로드
                result_file = self.results_dir / job_id / "result.json"
                if result_file.exists():
                    job_data["result"] = json.loads(result_file.read_text(encoding="utf-8"))

                return job_data

        return None

    def list_jobs(self, limit: int = 50) -> List[Dict]:
        """최근 작업 목록"""
        jobs = []

        for status in ["pending", "processing", "completed", "failed"]:
            status_dir = self.queue_dir / status
            if not status_dir.exists():
                continue

            for job_file in status_dir.glob("*.json"):
                try:
                    job_data = json.loads(job_file.read_text(encoding="utf-8"))
                    jobs.append(job_data)
                except Exception:
                    continue

        # 최신순 정렬
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]

    def get_stats(self) -> Dict[str, int]:
        """작업 통계"""
        stats = {}

        for status in ["pending", "processing", "completed", "failed"]:
            status_dir = self.queue_dir / status
            if status_dir.exists():
                stats[status] = len(list(status_dir.glob("*.json")))
            else:
                stats[status] = 0

        return stats
