"""작업 큐 API 라우터"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List

from backend.core.queue import JobQueue


router = APIRouter()
job_queue = JobQueue()


class CreateJobRequest(BaseModel):
    """작업 생성 요청"""
    story: str


class JobResponse(BaseModel):
    """작업 응답"""
    job_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Dict] = None


@router.post("/jobs", response_model=JobResponse, status_code=202)
def create_job(request: CreateJobRequest):
    """
    작업 생성 - 큐에 추가만 함 (비동기 처리)

    워커 프로세스가 큐를 감시하여 실제 처리를 수행합니다.
    """
    job_id = job_queue.create_job(story=request.story)

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="작업이 접수되었습니다. 워커가 처리 중입니다."
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    """작업 상태 및 결과 조회"""
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    return JobResponse(
        job_id=job_id,
        status=job["status"],
        result=job.get("result")
    )


@router.get("/jobs")
def list_jobs(limit: int = 50) -> List[Dict]:
    """전체 작업 목록 조회"""
    return job_queue.list_jobs(limit=limit)


@router.get("/stats")
def get_stats() -> Dict[str, int]:
    """작업 통계 조회"""
    return job_queue.get_stats()
