# backend/core/logic/director.py
from typing import List
from ..domain.models import Story, Scene

# Placeholder for LLM Client (to be injected)
# In a real implementation, this would call OpenAI/Anthropic API
# For now, we simulate the 'Pure Function' logic structure

def expand_story_logic(topic: str, llm_client=None) -> Story:
    """
    Pure function (conceptually) to expand a topic into a rich story.
    Args:
        topic: Result of user input
        llm_client: Injected dependency for API calls
    Returns:
        Story object
    """
    # TODO: Implement actual LLM call
    # prompt = f"Write a rich, visual story based on: {topic}..."
    # response = llm_client.complete(prompt)
    
    # Mock response for prototype
    mock_text = f"This is a dramatically expanded story about {topic}. It is full of vivid details."
    return Story(title=f"The Legend of {topic}", topic=topic, full_text=mock_text)


def breakdown_scenes_logic(story: Story, llm_client=None) -> List[Scene]:
    """
    Pure function to break down a story into scenes.
    Uses 'Sequential Thinking' prompt pattern via LLM.
    """
    # TODO: Implement actual LLM call with structured output (JSON)
    # prompt = "Analyze the story. Break it into 4-second shots. Return JSON..."
    
    # Mock response
    return [
        Scene(
            id=1,
            visual_description=f"Opening shot of {story.topic}",
            camera="Wide angle, slow pan",
            lighting="Golden hour sun",
            action="Leaves blowing in the wind",
            mood="Peaceful"
        ),
        Scene(
            id=2,
            visual_description=f"Close up details of {story.topic}",
            camera="Macro lens",
            lighting="Soft studio light",
            action="Subtle movement",
            mood="Intimate"
        )
    ]

def scene_to_prompt(scene: Scene, style: str = "Cinematic") -> str:
    """
    Converts a Scene object into a stable diffusion prompt string.
    Deterministic function.
    """
    base = f"{scene.visual_description}, {scene.action}"
    tech = f"{scene.camera}, {scene.lighting}, {style}, 8k resolution, photorealistic"
    mid = f"mood: {scene.mood}"
    return f"{base}, {mid}, {tech}"
