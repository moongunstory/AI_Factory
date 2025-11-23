"""
Data schemas for the Shorts LLM pipeline.

Defines all Pydantic models for structured data through the 3-stage pipeline:
- Stage 1: Story Outline (beats)
- Stage 2: Scene & Shot Planning
- Stage 3: Final Prompts for generation
"""

from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Stage 1: Story Outline Schemas
# ============================================================================


class StoryBeat(BaseModel):
    """
    A single narrative beat in the story structure.

    Attributes:
        id: Unique identifier for this beat (e.g., "beat_001")
        title: Short, descriptive title for the beat
        summary: Concrete, visual description of what happens
        story_function: The narrative role this beat plays
        emotional_tone: The dominant emotion or mood
    """
    id: str = Field(..., description="Unique beat identifier")
    title: str = Field(..., description="Beat title")
    summary: str = Field(..., description="Visual description of the beat")
    story_function: Literal["hook", "setup", "rising_action", "climax", "resolution"] = Field(
        ..., description="Narrative function"
    )
    emotional_tone: str = Field(..., description="Emotional mood")


class StoryMetadata(BaseModel):
    """
    Metadata about the story and its production constraints.

    Attributes:
        estimated_duration_seconds: Total duration estimate
        target_platforms: Intended distribution platforms
        tone: Overall narrative tone
        genre: Story genre classification
    """
    estimated_duration_seconds: int = Field(..., ge=15, le=300)
    target_platforms: list[str] = Field(
        default_factory=lambda: ["TikTok", "Instagram Reels", "YouTube Shorts"]
    )
    tone: str = Field(..., description="Overall tone (e.g., 'epic', 'comedic')")
    genre: str = Field(..., description="Genre (e.g., 'fantasy', 'sci-fi')")


class StoryOutline(BaseModel):
    """
    Complete story outline with beats and metadata.

    This is the output of Stage 1 (Story Expansion).
    """
    logline: str = Field(..., description="Original story logline")
    metadata: StoryMetadata
    beats: list[StoryBeat] = Field(..., min_length=5, max_length=20)


# ============================================================================
# Stage 2: Scene & Shot Planning Schemas
# ============================================================================


class ShotPlan(BaseModel):
    """
    Detailed plan for a single camera shot.

    Attributes:
        shot_id: Unique identifier (e.g., "shot_001")
        shot_type: Camera framing (e.g., "close-up", "wide", "medium")
        camera_movement: Movement type (e.g., "static", "pan", "dolly")
        duration_seconds: Shot duration in seconds
        action_description: What happens during this shot
        focus_subject: Primary subject of the shot
        emotional_tone: Emotional mood for this shot
        transition_in: How this shot begins (e.g., "cut", "fade in")
        transition_out: How this shot ends (e.g., "cut", "fade out")
        notes_for_prompt: Additional notes for prompt engineering
    """
    shot_id: str = Field(..., description="Unique shot identifier")
    shot_type: str = Field(..., description="Camera framing type")
    camera_movement: str = Field(..., description="Camera movement")
    duration_seconds: float = Field(..., ge=0.8, le=4.0)
    action_description: str = Field(..., description="Shot action")
    focus_subject: str = Field(..., description="Primary subject")
    emotional_tone: str = Field(..., description="Shot mood")
    transition_in: str = Field(..., description="Transition in")
    transition_out: str = Field(..., description="Transition out")
    notes_for_prompt: str | None = Field(None, description="Prompt engineering notes")


class ScenePlan(BaseModel):
    """
    A scene composed of multiple shots.

    Attributes:
        scene_id: Unique identifier (e.g., "scene_001")
        related_beats: List of beat IDs this scene covers
        scene_purpose: Narrative purpose of the scene
        location_description: Where the scene takes place
        emotional_tone: Overall scene mood
        shots: List of shot plans in this scene
    """
    scene_id: str = Field(..., description="Unique scene identifier")
    related_beats: list[str] = Field(..., description="Related beat IDs")
    scene_purpose: str = Field(..., description="Narrative purpose")
    location_description: str = Field(..., description="Scene location")
    emotional_tone: str = Field(..., description="Scene mood")
    shots: list[ShotPlan] = Field(..., min_length=1)


class ScenePlanPackage(BaseModel):
    """
    Complete scene and shot plan for the entire story.

    This is the output of Stage 2 (Shot Planning).
    """
    logline: str = Field(..., description="Original story logline")
    metadata: StoryMetadata
    scenes: list[ScenePlan] = Field(..., min_length=3, max_length=12)


# ============================================================================
# Stage 3: Prompt Engineering Schemas
# ============================================================================


class GlobalStyle(BaseModel):
    """
    Global visual style applied across all shots.

    Attributes:
        visual_style: Overall aesthetic (e.g., "cinematic realism", "anime")
        color_palette: Color scheme description
        lighting_style: Lighting approach
        camera_lens: Virtual lens characteristics
        frame_format: Aspect ratio (typically "9:16" for vertical video)
        frame_rate_hint: Target frame rate description
    """
    visual_style: str = Field(..., description="Overall visual aesthetic")
    color_palette: str = Field(..., description="Color scheme")
    lighting_style: str = Field(..., description="Lighting approach")
    camera_lens: str = Field(..., description="Lens characteristics")
    frame_format: str = Field(default="9:16", description="Aspect ratio")
    frame_rate_hint: str = Field(default="24fps cinematic", description="Frame rate")


class ShotPrompt(BaseModel):
    """
    Final text-to-image/video prompt for a single shot.

    Attributes:
        shot_id: References the shot from Stage 2
        scene_id: References the scene from Stage 2
        positive_prompt: Detailed positive prompt (25-80 words)
        negative_prompt: Negative prompt (artifacts to avoid)
        duration_seconds: Shot duration
        seed_hint: Optional random seed suggestion
        strength_tags: List of emphasis tags (e.g., ["character_consistency"])
    """
    shot_id: str = Field(..., description="Shot identifier")
    scene_id: str = Field(..., description="Scene identifier")
    positive_prompt: str = Field(
        ...,
        description="Detailed positive prompt for generation",
        min_length=25
    )
    negative_prompt: str = Field(
        ...,
        description="Negative prompt (artifacts to avoid)"
    )
    duration_seconds: float = Field(..., ge=0.8, le=4.0)
    seed_hint: str | None = Field(None, description="Random seed suggestion")
    strength_tags: list[str] = Field(
        default_factory=list,
        description="Emphasis tags for generation"
    )


class PromptPackage(BaseModel):
    """
    Complete prompt package ready for text-to-image/video generation.

    This is the output of Stage 3 (Prompt Engineering).
    """
    logline: str = Field(..., description="Original story logline")
    global_style: GlobalStyle
    shots: list[ShotPrompt] = Field(..., min_length=8, max_length=40)


# ============================================================================
# Final Pipeline Result
# ============================================================================


class ShortsGenerationResult(BaseModel):
    """
    Complete result from the 3-stage pipeline.

    Contains all intermediate and final outputs:
    - Stage 1: Story outline
    - Stage 2: Scene and shot plan
    - Stage 3: Final prompts

    This object is fully serializable to JSON for storage or API responses.
    """
    outline: StoryOutline
    scene_plan: ScenePlanPackage
    prompts: PromptPackage

    def to_json_file(self, filepath: str) -> None:
        """Save the complete result to a JSON file."""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json_file(cls, filepath: str) -> "ShortsGenerationResult":
        """Load a result from a JSON file."""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
