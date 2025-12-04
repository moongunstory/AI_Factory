"""Streamlit web UI for AI Short Factory."""
import streamlit as st
from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.common.logger import setup_logger

logger = setup_logger(__name__)

# Page config
st.set_page_config(
    page_title="AI Short Factory",
    page_icon="🎬",
    layout="wide"
)

# Initialize components (cached)
@st.cache_resource
def get_components():
    """Initialize and cache AI components."""
    return {
        'expander': StoryExpander(),
        'generator': PromptGenerator()
    }

# Initialize session state
if 'expanded_story' not in st.session_state:
    st.session_state.expanded_story = None

if 'prompts_data' not in st.session_state:
    st.session_state.prompts_data = None

if 'selected_scenes' not in st.session_state:
    st.session_state.selected_scenes = set()

# Header
st.title("🎬 AI Short Factory")
st.markdown("### Turn a simple idea into cinematic prompts")
st.markdown("---")

# Get components
components = get_components()

# Step 1: Story Input
st.header("1️⃣ Enter your story idea")
simple_idea = st.text_area(
    "Write a simple story idea:",
    placeholder="e.g., A robot wakes up on a space station and searches for humanity's last message",
    height=100
)

col1, col2 = st.columns([1, 5])
with col1:
    expand_button = st.button("🚀 Expand story", type="primary", disabled=not simple_idea)

# Step 2: Expanded Story Display
if st.session_state.expanded_story:
    st.header("2️⃣ Expanded story")

    st.markdown("#### 📖 Generated story")
    st.info(st.session_state.expanded_story)

    col1, col2 = st.columns([1, 1])
    with col1:
        confirm_button = st.button("✅ Confirm (generate prompts)", type="primary")
    with col2:
        retry_story_button = st.button("🔄 Retry (generate again)")

# Step 3: Prompts Display
if st.session_state.prompts_data:
    st.header("3️⃣ Generated scene prompts")

    scenes = st.session_state.prompts_data.get('scenes', [])
    total_scenes = len(scenes)

    st.markdown(f"**Total scenes: {total_scenes}** | Estimated length: {st.session_state.prompts_data.get('estimated_duration', 0):.1f}s")
    st.markdown("---")

    # Display each scene
    for scene in scenes:
        scene_num = scene.get('scene_number', 0)

        with st.expander(f"🎬 Scene {scene_num} ({scene.get('duration', 0)}s)", expanded=True):
            # Scene description
            st.markdown(f"**Description:** {scene.get('description', 'N/A')}")

            # Prompts in columns
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📝 English prompt (Stable Diffusion)**")
                st.code(scene.get('prompt_en', 'N/A'), language=None)

            # Checkbox for regeneration
            is_selected = st.checkbox(
                f"Select this scene for regeneration",
                key=f"select_{scene_num}",
                value=scene_num in st.session_state.selected_scenes
            )

            if is_selected:
                st.session_state.selected_scenes.add(scene_num)
            else:
                st.session_state.selected_scenes.discard(scene_num)

    # Regenerate button
    st.markdown("---")
    if st.session_state.selected_scenes:
        selected_count = len(st.session_state.selected_scenes)
        regenerate_button = st.button(
            f"🔄 Regenerate {selected_count} selected scenes",
            type="secondary"
        )
    else:
        st.info("💡 Select scenes with the checkbox to regenerate them.")

# Event Handlers

# Expand story
if expand_button:
    with st.spinner("Expanding story... 🤖"):
        try:
            expanded = components['expander'].expand(simple_idea)
            st.session_state.expanded_story = expanded
            st.session_state.prompts_data = None  # Reset prompts
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Story expansion failed: {e}")
            logger.error(f"Story expansion failed: {e}")

# Retry story expansion
if 'retry_story_button' in locals() and retry_story_button:
    with st.spinner("Regenerating story... 🤖"):
        try:
            expanded = components['expander'].expand(simple_idea)
            st.session_state.expanded_story = expanded
            st.session_state.prompts_data = None
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Story regeneration failed: {e}")
            logger.error(f"Story retry failed: {e}")

# Confirm and generate prompts
if 'confirm_button' in locals() and confirm_button:
    with st.spinner("Generating scene prompts... 🎨"):
        try:
            # Generate prompts (English only)
            prompts_data = components['generator'].generate(st.session_state.expanded_story)

            st.session_state.prompts_data = prompts_data
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Prompt generation failed: {e}")
            logger.error(f"Prompt generation failed: {e}")

# Regenerate selected scenes
if 'regenerate_button' in locals() and regenerate_button:
    with st.spinner(f"Regenerating {len(st.session_state.selected_scenes)} scenes... 🔄"):
        try:
            prompts_data = st.session_state.prompts_data
            generator = components['generator']

            for scene in prompts_data.get('scenes', []):
                scene_num = scene.get('scene_number')

                if scene_num in st.session_state.selected_scenes:
                    # Regenerate this scene
                    logger.info(f"Regenerating scene {scene_num}")

                    new_scene = generator.regenerate_scene(
                        scene_number=scene_num,
                        scene_description=scene.get('description', '')
                    )

                    # Update the scene (English only)
                    scene['prompt_en'] = new_scene.get('prompt_en', '')
                    scene['description'] = new_scene.get('description', '')
                    scene['duration'] = new_scene.get('duration', scene.get('duration', 5.0))

            st.session_state.selected_scenes = set()
            st.rerun()

        except Exception as e:
            st.error(f"❌ Scene regeneration failed: {e}")
            logger.error(f"Scene regeneration failed: {e}")

# Footer
st.markdown("---")
st.caption("🎬 AI Short Factory - Powered by Local LLM (llama.cpp)")
