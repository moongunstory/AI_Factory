"""Flask web UI for AI Short Factory."""
import os
import sys
import atexit
import signal
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.pipeline.advanced_scene_generator import AdvancedSceneGenerator
from src.pipeline.visual_styles import VisualStyleDefinitions
from src.pipeline.translator import Translator
from src.common.logger import setup_logger
from src.common.json_utils import safe_parse

logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False  # Support Korean characters

# Initialize AI components (singleton)
components = None

def get_components():
    """Initialize and cache AI components."""
    global components
    if components is None:
        logger.info("Initializing AI components...")
        components = {
            'expander': StoryExpander(),
            'generator': PromptGenerator(),
            'advanced_generator': AdvancedSceneGenerator(),
            'translator': Translator()
        }
    return components


def cleanup_on_shutdown():
    """Clean up resources when server shuts down.

    This function:
    - Clears all active sessions
    - Logs shutdown information
    - Performs graceful cleanup
    """
    logger.info("Server shutting down - cleaning up resources...")

    try:
        # Clear all Flask session data
        with app.app_context():
            # Note: Flask sessions are client-side by default,
            # so we just log the cleanup
            logger.info("Session data will be cleared on client side")

        # Clean up AI components
        global components
        if components is not None:
            logger.info("Cleaning up AI components...")
            # LlamaClient sessions will be closed via __del__
            components = None

        logger.info("✓ Cleanup completed successfully")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals (SIGINT, SIGTERM)."""
    logger.info(f"Received signal {signum} - initiating graceful shutdown...")
    cleanup_on_shutdown()
    sys.exit(0)


# Register cleanup handlers
atexit.register(cleanup_on_shutdown)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/expand-story', methods=['POST'])
def expand_story():
    """Expand a simple story idea into a full story."""
    try:
        data = request.get_json()
        simple_idea = data.get('simple_idea', '').strip()

        if not simple_idea:
            return jsonify({'error': '이야기 아이디어를 입력해주세요'}), 400

        logger.info(f"Expanding story: {simple_idea[:50]}...")

        comp = get_components()
        expanded = comp['expander'].expand(simple_idea)

        # Store in session
        session['expanded_story'] = expanded
        session['simple_idea'] = simple_idea

        return jsonify({
            'success': True,
            'expanded_story': expanded
        })

    except Exception as e:
        logger.error(f"Story expansion failed: {e}")
        return jsonify({'error': f'이야기 확장 실패: {str(e)}'}), 500


@app.route('/api/generate-prompts', methods=['POST'])
def generate_prompts():
    """Generate scene prompts from expanded story using advanced scene generator."""
    try:
        data = request.get_json()
        expanded_story = data.get('expanded_story', '').strip()

        if not expanded_story:
            return jsonify({'error': '확장된 이야기가 없습니다'}), 400

        logger.info("Generating advanced scene prompts (20-25 scenes)...")

        comp = get_components()
        advanced_gen = comp['advanced_generator']
        translator = comp['translator']

        # Step 1: Generate story beats
        logger.info("Step 1: Generating story beats...")
        story_beats = advanced_gen.generate_story_beats(expanded_story, temperature=0.7)

        # Step 2: Generate character sheets
        logger.info("Step 2: Generating character sheets...")
        character_sheets = advanced_gen.generate_character_sheet(
            expanded_story,
            story_beats,
            theme="cinematic_realism",
            temperature=0.6
        )

        # Step 3: Generate 20-25 scenes
        logger.info("Step 3: Generating 20-25 scenes...")
        scenes_result = advanced_gen.generate_scenes(
            expanded_story,
            story_beats,
            character_sheets,
            theme="cinematic_realism",
            target_duration=60.0,
            temperature=0.7
        )

        # Format scenes for frontend compatibility
        scenes = scenes_result.get('scenes', [])
        for scene in scenes:
            # Add description_kr (Korean description) for frontend compatibility
            scene['description_kr'] = scene.get('description', '')

            # Translate English prompt to Korean
            prompt_en = scene.get('prompt_en', '')
            if prompt_en:
                scene['prompt_kr'] = translator.translate(prompt_en)
            else:
                scene['prompt_kr'] = ''

        # Prepare final prompts data
        prompts_data = {
            'scenes': scenes,
            'total_scenes': len(scenes),
            'estimated_duration': scenes_result.get('total_duration', 0)
        }

        # Store in session for regeneration
        session['prompts_data'] = prompts_data
        session['story_beats'] = story_beats
        session['character_sheets'] = character_sheets

        logger.info(f"Generated {len(scenes)} scenes successfully")

        return jsonify({
            'success': True,
            'prompts_data': prompts_data
        })

    except Exception as e:
        logger.error(f"Prompt generation failed: {e}")
        return jsonify({'error': f'프롬프트 생성 실패: {str(e)}'}), 500


@app.route('/api/regenerate-scene', methods=['POST'])
def regenerate_scene():
    """Regenerate a specific scene."""
    try:
        data = request.get_json()
        scene_number = data.get('scene_number')
        scene_description = data.get('scene_description', '')

        if scene_number is None:
            return jsonify({'error': '장면 번호가 필요합니다'}), 400

        logger.info(f"Regenerating scene {scene_number}...")

        comp = get_components()
        generator = comp['generator']
        translator = comp['translator']

        # Regenerate this scene
        new_scene = generator.regenerate_scene(
            scene_number=scene_number,
            scene_description=scene_description
        )

        # Translate
        prompt_en = new_scene.get('prompt_en', '')
        if prompt_en:
            new_scene['prompt_kr'] = translator.translate(prompt_en)
        else:
            new_scene['prompt_kr'] = ''

        return jsonify({
            'success': True,
            'scene': new_scene
        })

    except Exception as e:
        logger.error(f"Scene regeneration failed: {e}")
        return jsonify({'error': f'장면 재생성 실패: {str(e)}'}), 500


@app.route('/api/regenerate-scenes', methods=['POST'])
def regenerate_scenes():
    """Regenerate multiple selected scenes using advanced scene generator."""
    try:
        data = request.get_json()
        scenes_to_regenerate = data.get('scenes', [])

        if not scenes_to_regenerate:
            return jsonify({'error': '재생성할 장면이 없습니다'}), 400

        logger.info(f"Regenerating {len(scenes_to_regenerate)} scenes with advanced generator...")

        comp = get_components()
        advanced_gen = comp['advanced_generator']
        translator = comp['translator']

        # Get character sheets and global style from session
        character_sheets = session.get('character_sheets', {'characters': []})
        theme = "cinematic_realism"
        global_style = VisualStyleDefinitions.get_global_style_prompt(theme)

        regenerated_scenes = []

        for scene_info in scenes_to_regenerate:
            scene_number = scene_info.get('scene_number')
            scene_description = scene_info.get('scene_description', '')

            # Regenerate this scene with advanced generator
            new_scene = advanced_gen.regenerate_scene(
                scene_number=scene_number,
                scene_description=scene_description,
                character_sheets=character_sheets,
                global_style=global_style,
                temperature=0.7
            )

            # Add description_kr for frontend compatibility
            new_scene['description_kr'] = new_scene.get('description', scene_description)

            # Translate English prompt to Korean
            prompt_en = new_scene.get('prompt_en', '')
            if prompt_en:
                new_scene['prompt_kr'] = translator.translate(prompt_en)
            else:
                new_scene['prompt_kr'] = ''

            regenerated_scenes.append(new_scene)

        return jsonify({
            'success': True,
            'scenes': regenerated_scenes
        })

    except Exception as e:
        logger.error(f"Scenes regeneration failed: {e}")
        return jsonify({'error': f'장면 재생성 실패: {str(e)}'}), 500


if __name__ == '__main__':
    # Development server with threading enabled for better concurrency
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True,  # 동시 요청 처리 가능
        use_reloader=False  # llama-server와의 충돌 방지
    )
