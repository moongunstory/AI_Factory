"""Pipeline module for AI Short Factory.

This module provides a multi-layer pipeline for generating cinematic prompts:
- Story Layer: Story expansion and beat extraction
- Film Layer: Cinematic grammar and emotional analysis
- Camera Layer: Technical camera specifications
- Prompt Layer: Final prompt generation

Main components:
- StoryExpander: Expands simple ideas into detailed stories
- PromptGenerator: Multi-layer prompt generation (Film + Camera)
- FilmLayer: Analyzes scene emotions and applies cinematic grammar
- CameraLayer: Assigns camera specs (shots, angles, lenses, movements)
- GlobalStyleConfig: Project-wide visual style configuration
"""

from .story_expander import StoryExpander, expand_story
from .prompt_generator import PromptGenerator, generate_prompts
from .film_layer import FilmLayer, SceneEmotion
from .camera_layer import CameraLayer
from .visual_styles import (
    VisualStyleDefinitions,
    GlobalStyleConfig,
    create_global_config,
    get_available_themes,
)

__all__ = [
    # Story expansion
    "StoryExpander",
    "expand_story",
    # Prompt generation
    "PromptGenerator",
    "generate_prompts",
    # Multi-layer system
    "FilmLayer",
    "SceneEmotion",
    "CameraLayer",
    # Global styling
    "VisualStyleDefinitions",
    "GlobalStyleConfig",
    "create_global_config",
    "get_available_themes",
]
