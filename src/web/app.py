"""Flask web UI for AI Short Factory."""
import os
import sys
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.pipeline.translator import Translator
from src.common.logger import setup_logger

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
            'translator': Translator()
        }
    return components


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
    """Generate scene prompts from expanded story."""
    try:
        data = request.get_json()
        expanded_story = data.get('expanded_story', '').strip()

        if not expanded_story:
            return jsonify({'error': '확장된 이야기가 없습니다'}), 400

        logger.info("Generating prompts...")

        comp = get_components()

        # Generate prompts
        prompts_data = comp['generator'].generate(expanded_story)

        # Translate each prompt to Korean
        translator = comp['translator']
        for scene in prompts_data.get('scenes', []):
            prompt_en = scene.get('prompt_en', '')
            if prompt_en:
                scene['prompt_kr'] = translator.translate(prompt_en)
            else:
                scene['prompt_kr'] = ''

        # Store in session
        session['prompts_data'] = prompts_data

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
    """Regenerate multiple selected scenes."""
    try:
        data = request.get_json()
        scenes_to_regenerate = data.get('scenes', [])

        if not scenes_to_regenerate:
            return jsonify({'error': '재생성할 장면이 없습니다'}), 400

        logger.info(f"Regenerating {len(scenes_to_regenerate)} scenes...")

        comp = get_components()
        generator = comp['generator']
        translator = comp['translator']

        regenerated_scenes = []

        for scene_info in scenes_to_regenerate:
            scene_number = scene_info.get('scene_number')
            scene_description = scene_info.get('scene_description', '')

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

            regenerated_scenes.append(new_scene)

        return jsonify({
            'success': True,
            'scenes': regenerated_scenes
        })

    except Exception as e:
        logger.error(f"Scenes regeneration failed: {e}")
        return jsonify({'error': f'장면 재생성 실패: {str(e)}'}), 500


if __name__ == '__main__':
    # Development server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
