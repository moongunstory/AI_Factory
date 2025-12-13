"""작업 큐 관련 데이터 모델"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoJob(BaseModel):
    """영상 생성 작업"""
    job_id: str
    story: str
    status: JobStatus = JobStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class JobResult(BaseModel):
    """작업 결과"""
    expanded_story: Optional[str] = None
    storyboard: Optional[str] = None
    prompts: Optional[str] = None
