# backend/core/domain/models.py
from typing import List, Optional
from pydantic import BaseModel, Field

class Scene(BaseModel):
    """
    A single visual unit (shot) in the video.
    """
    id: int
    visual_description: str = Field(..., description="Concrete visual description of the scene")
    camera: str = Field(..., description="Camera angle, movement, or lens type")
    lighting: str = Field(..., description="Lighting conditions")
    action: str = Field(..., description="Main subject motion or action")
    mood: str = Field(..., description="Emotional tone")
    estimated_duration: int = Field(4, description="Duration in seconds (default 4s for SVD)")
    img_path: Optional[str] = None
    vid_path: Optional[str] = None

class Story(BaseModel):
    """
    The expanded narrative structure.
    """
    title: str
    topic: str
    full_text: str
    style_guide: Optional[str] = None  # Consistent style instructions (e.g. "Cyberpunk, Neon")

class VideoJob(BaseModel):
    """
    Represents a full generation task.
    """
    id: str
    created_at: float
    status: str = "pending"  # pending, processing, completed, failed
    topic: str
    story: Optional[Story] = None
    scenes: List[Scene] = []
    video_paths: List[str] = []
    final_video_path: Optional[str] = None
