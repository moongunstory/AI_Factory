"""Streamlit web UI for AI Short Factory."""
import streamlit as st
from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.pipeline.translator import Translator
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
        'generator': PromptGenerator(),
        'translator': Translator()
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
st.markdown("### 간단한 아이디어를 영상 프롬프트로 변환")
st.markdown("---")

# Get components
components = get_components()

# Step 1: Story Input
st.header("1️⃣ 이야기 아이디어 입력")
simple_idea = st.text_area(
    "간단한 이야기 아이디어를 입력하세요:",
    placeholder="예: 우주 정거장에서 깨어난 로봇이 인류의 마지막 메시지를 찾는 이야기",
    height=100
)

col1, col2 = st.columns([1, 5])
with col1:
    expand_button = st.button("🚀 이야기 확장", type="primary", disabled=not simple_idea)

# Step 2: Expanded Story Display
if st.session_state.expanded_story:
    st.header("2️⃣ 확장된 이야기")

    st.markdown("#### 📖 생성된 이야기")
    st.info(st.session_state.expanded_story)

    col1, col2 = st.columns([1, 1])
    with col1:
        confirm_button = st.button("✅ 컨펌 (프롬프트 생성)", type="primary")
    with col2:
        retry_story_button = st.button("🔄 재시도 (이야기 다시 생성)")

# Step 3: Prompts Display
if st.session_state.prompts_data:
    st.header("3️⃣ 생성된 장면 프롬프트")

    scenes = st.session_state.prompts_data.get('scenes', [])
    total_scenes = len(scenes)

    st.markdown(f"**총 {total_scenes}개 장면** | 예상 길이: {st.session_state.prompts_data.get('estimated_duration', 0):.1f}초")
    st.markdown("---")

    # Display each scene
    for scene in scenes:
        scene_num = scene.get('scene_number', 0)

        with st.expander(f"🎬 장면 {scene_num} ({scene.get('duration', 0)}초)", expanded=True):
            # Scene description
            st.markdown(f"**장면 설명:** {scene.get('description_kr', 'N/A')}")

            # Prompts in columns
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📝 영어 프롬프트 (Stable Diffusion)**")
                st.code(scene.get('prompt_en', 'N/A'), language=None)

            with col2:
                st.markdown("**🇰🇷 한국어 번역**")
                prompt_kr = scene.get('prompt_kr', '')
                if not prompt_kr:
                    st.caption("번역 중...")
                else:
                    st.code(prompt_kr, language=None)

            # Checkbox for regeneration
            is_selected = st.checkbox(
                f"이 장면 재생성 선택",
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
            f"🔄 선택한 {selected_count}개 장면 재생성",
            type="secondary"
        )
    else:
        st.info("💡 재생성할 장면을 선택하려면 체크박스를 체크하세요.")

# Event Handlers

# Expand story
if expand_button:
    with st.spinner("이야기를 확장하는 중... 🤖"):
        try:
            expanded = components['expander'].expand(simple_idea)
            st.session_state.expanded_story = expanded
            st.session_state.prompts_data = None  # Reset prompts
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ 이야기 확장 실패: {e}")
            logger.error(f"Story expansion failed: {e}")

# Retry story expansion
if 'retry_story_button' in locals() and retry_story_button:
    with st.spinner("이야기를 다시 생성하는 중... 🤖"):
        try:
            expanded = components['expander'].expand(simple_idea)
            st.session_state.expanded_story = expanded
            st.session_state.prompts_data = None
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ 이야기 재생성 실패: {e}")
            logger.error(f"Story retry failed: {e}")

# Confirm and generate prompts
if 'confirm_button' in locals() and confirm_button:
    with st.spinner("장면 프롬프트를 생성하는 중... 🎨"):
        try:
            # Generate prompts
            prompts_data = components['generator'].generate(st.session_state.expanded_story)

            # Translate each prompt to Korean
            translator = components['translator']
            for scene in prompts_data.get('scenes', []):
                prompt_en = scene.get('prompt_en', '')
                if prompt_en:
                    scene['prompt_kr'] = translator.translate(prompt_en)
                else:
                    scene['prompt_kr'] = ''

            st.session_state.prompts_data = prompts_data
            st.session_state.selected_scenes = set()
            st.rerun()
        except Exception as e:
            st.error(f"❌ 프롬프트 생성 실패: {e}")
            logger.error(f"Prompt generation failed: {e}")

# Regenerate selected scenes
if 'regenerate_button' in locals() and regenerate_button:
    with st.spinner(f"{len(st.session_state.selected_scenes)}개 장면을 재생성하는 중... 🔄"):
        try:
            prompts_data = st.session_state.prompts_data
            generator = components['generator']
            translator = components['translator']

            for scene in prompts_data.get('scenes', []):
                scene_num = scene.get('scene_number')

                if scene_num in st.session_state.selected_scenes:
                    # Regenerate this scene
                    logger.info(f"Regenerating scene {scene_num}")

                    new_scene = generator.regenerate_scene(
                        scene_number=scene_num,
                        scene_description=scene.get('description_kr', '')
                    )

                    # Update the scene
                    scene['prompt_en'] = new_scene.get('prompt_en', '')
                    scene['prompt_kr'] = translator.translate(scene['prompt_en'])
                    scene['description_kr'] = new_scene.get('description_kr', '')
                    scene['duration'] = new_scene.get('duration', scene.get('duration', 5.0))

            st.session_state.selected_scenes = set()
            st.rerun()

        except Exception as e:
            st.error(f"❌ 장면 재생성 실패: {e}")
            logger.error(f"Scene regeneration failed: {e}")

# Footer
st.markdown("---")
st.caption("🎬 AI Short Factory - Powered by Local LLM (llama.cpp)")
