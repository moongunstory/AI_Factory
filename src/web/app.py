"""Flask web UI for AI Short Factory."""
import os
import sys
import atexit
import signal
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.pipeline.advanced_scene_generator import AdvancedSceneGenerator
from src.pipeline.visual_styles import VisualStyleDefinitions
from src.pipeline.next_episode_suggester import NextEpisodeSuggester
from src.data.universe_manager import UniverseManager
from src.data.character_manager import CharacterManager
from src.data.series_manager import SeriesManager
from src.data.timeline_manager import TimelineManager
from src.common.logger import setup_logger
from src.common.json_utils import safe_parse

# Import AI Short Factory pipeline services
from src.web.services.pipeline import (
    generate_short,
    get_pipeline_status,
    check_engines_health,
    PipelineStatus,
)
from src.web.services.comfy_client import ComfyUIClient
from src.common.config import Config

logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False

# Initialize AI components (singleton)
components = None

def get_components():
    """Initialize and cache AI components."""
    global components
    if components is None:
        logger.info("Initializing AI components...")
        # Get absolute path to data directory
        data_root = str(project_root / "data" / "universes")

        components = {
            'expander': StoryExpander(),
            'generator': PromptGenerator(),
            'advanced_generator': AdvancedSceneGenerator(),
            'suggester': NextEpisodeSuggester(),
            'universe_mgr': UniverseManager(data_root),
            'character_mgr': CharacterManager(data_root),
            'series_mgr': SeriesManager(data_root),
            'timeline_mgr': TimelineManager(data_root)
        }
    return components


def cleanup_on_shutdown():
    """Clean up resources when server shuts down (single-user simplified)."""
    logger.info("Shutting down...")
    try:
        # Clean up AI components
        global components
        if components is not None:
            components = None
        logger.info("Cleanup done")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals (simplified for single-user)."""
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


@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve generated output files (images, videos)."""
    output_dir = project_root / "output"
    return send_from_directory(output_dir, filename)


@app.route('/api/expand-story', methods=['POST'])
def expand_story():
    """Expand a simple story idea into a full story (English only)."""
    try:
        data = request.get_json()
        simple_idea = data.get('simple_idea', '').strip()

        if not simple_idea:
            return jsonify({'error': 'Please enter a story idea'}), 400

        logger.info(f"User input: {simple_idea[:50]}...")

        comp = get_components()

        # Expand story (in English)
        expanded = comp['expander'].expand(simple_idea)
        logger.info(f"Expanded story: {expanded[:100]}...")

        # Store in session
        session['expanded_story'] = expanded
        session['simple_idea'] = simple_idea

        return jsonify({
            'success': True,
            'expanded_story': expanded
        })

    except Exception as e:
        logger.error(f"Story expansion failed: {e}")
        return jsonify({'error': f'Story expansion failed: {str(e)}'}), 500


@app.route('/api/generate-prompts', methods=['POST'])
def generate_prompts():
    """Generate scene prompts from expanded story using advanced scene generator (English only)."""
    try:
        data = request.get_json()
        expanded_story = data.get('expanded_story', '').strip()
        theme = data.get('theme', 'cinematic_realism').strip()

        if not expanded_story:
            return jsonify({'error': 'No expanded story provided'}), 400

        # Use story from session if available
        if not expanded_story:
            expanded_story = session.get('expanded_story', '')

        if not expanded_story:
            return jsonify({'error': 'No story available'}), 400

        logger.info(f"Generating advanced scene prompts (20-25 scenes) with theme: {theme}...")
        logger.info(f"Using story: {expanded_story[:100]}...")

        comp = get_components()
        advanced_gen = comp['advanced_generator']

        # Step 1: Generate story beats (in English)
        logger.info("Step 1: Generating story beats...")
        story_beats = advanced_gen.generate_story_beats(expanded_story, temperature=0.7)

        # Step 2: Generate character sheets (in English)
        logger.info("Step 2: Generating character sheets...")
        character_sheets = advanced_gen.generate_character_sheet(
            expanded_story,
            story_beats,
            theme=theme,
            temperature=0.6
        )

        # Step 3: Generate 20-25 scenes (in English)
        logger.info("Step 3: Generating 20-25 scenes...")
        scenes_result = advanced_gen.generate_scenes(
            expanded_story,
            story_beats,
            character_sheets,
            theme=theme,
            target_duration=60.0,
            temperature=0.7
        )

        # Format scenes for frontend (English only)
        scenes = scenes_result.get('scenes', [])

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
        session['theme'] = theme

        logger.info(f"Generated {len(scenes)} scenes successfully")

        return jsonify({
            'success': True,
            'prompts_data': prompts_data,
            'story_beats': story_beats,
            'character_sheets': character_sheets
        })

    except RuntimeError as e:
        logger.error(f"Prompt generation failed due to a runtime error: {e}")
        if "Failed to connect to llama-server" in str(e):
            error_message = (
                "AI server (llama-server) is not running. "
                "Please close this window and run 'run.bat' to start the program."
            )
            return jsonify({'error': error_message}), 500
        return jsonify({'error': f'Runtime error during prompt generation: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}")
        return jsonify({'error': f'Prompt generation failed: {str(e)}'}), 500


@app.route('/api/regenerate-scene', methods=['POST'])
def regenerate_scene():
    """Regenerate a specific scene (English only)."""
    try:
        data = request.get_json()
        scene_number = data.get('scene_number')
        scene_description = data.get('scene_description', '')

        if scene_number is None:
            return jsonify({'error': 'Scene number is required'}), 400

        logger.info(f"Regenerating scene {scene_number}...")

        comp = get_components()
        generator = comp['generator']

        # Regenerate this scene
        new_scene = generator.regenerate_scene(
            scene_number=scene_number,
            scene_description=scene_description
        )

        return jsonify({
            'success': True,
            'scene': new_scene
        })

    except Exception as e:
        logger.error(f"Scene regeneration failed: {e}")
        return jsonify({'error': f'Scene regeneration failed: {str(e)}'}), 500


@app.route('/api/regenerate-scenes', methods=['POST'])
def regenerate_scenes():
    """Regenerate multiple selected scenes using advanced scene generator (English only)."""
    try:
        data = request.get_json()
        scenes_to_regenerate = data.get('scenes', [])
        theme = data.get('theme', session.get('theme', 'cinematic_realism'))

        if not scenes_to_regenerate:
            return jsonify({'error': 'No scenes to regenerate'}), 400

        logger.info(f"Regenerating {len(scenes_to_regenerate)} scenes with theme: {theme}...")

        comp = get_components()
        advanced_gen = comp['advanced_generator']

        # Get character sheets and global style from session
        character_sheets = session.get('character_sheets', {'characters': []})
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

            regenerated_scenes.append(new_scene)

        return jsonify({
            'success': True,
            'scenes': regenerated_scenes
        })

    except Exception as e:
        logger.error(f"Scenes regeneration failed: {e}")
        return jsonify({'error': f'Scenes regeneration failed: {str(e)}'}), 500


@app.route('/api/generate-images', methods=['POST'])
def generate_images():
    """Generate images for all scenes using ComfyUI + SDXL."""
    try:
        data = request.get_json()
        prompts_data = data.get('prompts_data')

        if not prompts_data:
            prompts_data = session.get('prompts_data')

        if not prompts_data:
            return jsonify({'error': 'No prompts data available'}), 400

        scenes = prompts_data.get('scenes', [])
        if not scenes:
            return jsonify({'error': 'No scenes to generate images for'}), 400

        logger.info(f"Generating images for {len(scenes)} scenes...")

        # Initialize ComfyUI client
        comfy_client = ComfyUIClient(
            server_url=Config.COMFYUI_URL,
            model_base=Config.SDXL_BASE_MODEL,
            model_refiner=Config.SDXL_REFINER_MODEL
        )

        # Check ComfyUI health
        if not comfy_client.is_healthy():
            return jsonify({'error': 'ComfyUI server is not running. Please start ComfyUI first.'}), 500

        # Create output directory
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        images_dir = Config.IMAGES_DIR / timestamp
        images_dir.mkdir(parents=True, exist_ok=True)

        generated_images = []

        for i, scene in enumerate(scenes, 1):
            scene_number = scene.get('scene_number', i)
            prompt = scene.get('prompt_en', '')

            if not prompt:
                logger.warning(f"Scene {scene_number} has no prompt, skipping")
                continue

            logger.info(f"Generating image {i}/{len(scenes)}: Scene {scene_number}...")

            image_path = images_dir / f"scene_{scene_number:03d}.png"

            try:
                metadata = comfy_client.generate_vertical_image(
                    prompt=prompt,
                    out_path=image_path,
                    steps_base=25,
                    steps_refiner=15,
                    cfg=7.0
                )

                # Store relative path for frontend
                relative_path = str(image_path.relative_to(project_root))

                generated_images.append({
                    'scene_number': scene_number,
                    'image_path': relative_path,
                    'prompt': prompt,
                    'description': scene.get('description', ''),
                    'duration': scene.get('duration', 3.0)
                })

                logger.info(f"✓ Image {i}/{len(scenes)} generated: {image_path.name}")

            except Exception as e:
                logger.error(f"Failed to generate image for scene {scene_number}: {e}")
                generated_images.append({
                    'scene_number': scene_number,
                    'image_path': None,
                    'prompt': prompt,
                    'description': scene.get('description', ''),
                    'duration': scene.get('duration', 3.0),
                    'error': str(e)
                })

        # Store generated images in session
        session['generated_images'] = generated_images
        session['images_timestamp'] = timestamp

        logger.info(f"Generated {len([img for img in generated_images if img['image_path']])} images successfully")

        return jsonify({
            'success': True,
            'images': generated_images,
            'timestamp': timestamp
        })

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return jsonify({'error': f'Image generation failed: {str(e)}'}), 500


@app.route('/api/regenerate-images', methods=['POST'])
def regenerate_images():
    """Regenerate images for selected scenes."""
    try:
        data = request.get_json()
        scenes_to_regenerate = data.get('scenes', [])

        if not scenes_to_regenerate:
            return jsonify({'error': 'No scenes to regenerate'}), 400

        logger.info(f"Regenerating images for {len(scenes_to_regenerate)} scenes...")

        # Initialize ComfyUI client
        comfy_client = ComfyUIClient(
            server_url=Config.COMFYUI_URL,
            model_base=Config.SDXL_BASE_MODEL,
            model_refiner=Config.SDXL_REFINER_MODEL
        )

        # Check ComfyUI health
        if not comfy_client.is_healthy():
            return jsonify({'error': 'ComfyUI server is not running. Please start ComfyUI first.'}), 500

        # Get timestamp from session or create new
        timestamp = session.get('images_timestamp')
        if not timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session['images_timestamp'] = timestamp

        images_dir = Config.IMAGES_DIR / timestamp
        images_dir.mkdir(parents=True, exist_ok=True)

        regenerated_images = []

        for scene_info in scenes_to_regenerate:
            scene_number = scene_info.get('scene_number')
            prompt = scene_info.get('prompt', '')

            if not prompt:
                logger.warning(f"Scene {scene_number} has no prompt, skipping")
                continue

            logger.info(f"Regenerating image for scene {scene_number}...")

            image_path = images_dir / f"scene_{scene_number:03d}.png"

            try:
                metadata = comfy_client.generate_vertical_image(
                    prompt=prompt,
                    out_path=image_path,
                    steps_base=25,
                    steps_refiner=15,
                    cfg=7.0
                )

                # Store relative path for frontend
                relative_path = str(image_path.relative_to(project_root))

                regenerated_images.append({
                    'scene_number': scene_number,
                    'image_path': relative_path,
                    'prompt': prompt,
                    'description': scene_info.get('description', ''),
                    'duration': scene_info.get('duration', 3.0)
                })

                logger.info(f"✓ Image regenerated for scene {scene_number}")

            except Exception as e:
                logger.error(f"Failed to regenerate image for scene {scene_number}: {e}")
                regenerated_images.append({
                    'scene_number': scene_number,
                    'image_path': None,
                    'prompt': prompt,
                    'description': scene_info.get('description', ''),
                    'duration': scene_info.get('duration', 3.0),
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'images': regenerated_images
        })

    except Exception as e:
        logger.error(f"Image regeneration failed: {e}")
        return jsonify({'error': f'Image regeneration failed: {str(e)}'}), 500


# ============================================================================
# Universe Management APIs
# ============================================================================

@app.route('/api/universes', methods=['GET'])
def list_universes():
    """Get all universes."""
    try:
        comp = get_components()
        universes = comp['universe_mgr'].list_universes()

        return jsonify({
            'success': True,
            'universes': universes
        })

    except Exception as e:
        logger.error(f"Failed to list universes: {e}")
        return jsonify({'error': f'Failed to fetch universe list: {str(e)}'}), 500


@app.route('/api/universes', methods=['POST'])
def create_universe():
    """Create a new universe."""
    try:
        data = request.get_json()
        universe_id = data.get('universe_id')
        name = data.get('name')
        genre = data.get('genre')
        background = data.get('background', '')
        rules = data.get('rules', {})
        style_lock = data.get('style_lock')

        if not all([universe_id, name, genre]):
            return jsonify({'error': 'Required fields are missing'}), 400

        comp = get_components()
        universe = comp['universe_mgr'].create_universe(
            universe_id, name, genre, background, rules, style_lock
        )

        return jsonify({
            'success': True,
            'universe': universe
        })

    except Exception as e:
        logger.error(f"Failed to create universe: {e}")
        return jsonify({'error': f'Failed to create universe: {str(e)}'}), 500


@app.route('/api/universes/<universe_id>', methods=['GET'])
def get_universe(universe_id):
    """Get a specific universe."""
    try:
        comp = get_components()
        universe = comp['universe_mgr'].get_universe_summary(universe_id)

        if not universe:
            return jsonify({'error': 'Universe not found'}), 404

        return jsonify({
            'success': True,
            'universe': universe
        })

    except Exception as e:
        logger.error(f"Failed to get universe: {e}")
        return jsonify({'error': f'Failed to fetch universe: {str(e)}'}), 500


# ============================================================================
# Character Management APIs
# ============================================================================

@app.route('/api/universes/<universe_id>/characters', methods=['GET'])
def list_characters(universe_id):
    """Get all characters in a universe."""
    try:
        comp = get_components()
        character_type = request.args.get('type')  # Optional filter

        characters = comp['character_mgr'].list_characters(universe_id, character_type)

        return jsonify({
            'success': True,
            'characters': characters
        })

    except Exception as e:
        logger.error(f"Failed to list characters: {e}")
        return jsonify({'error': f'Failed to fetch character list: {str(e)}'}), 500


@app.route('/api/universes/<universe_id>/characters', methods=['POST'])
def create_character(universe_id):
    """Create a new character."""
    try:
        data = request.get_json()

        comp = get_components()
        character = comp['character_mgr'].create_character(
            universe_id=universe_id,
            character_id=data.get('character_id'),
            name=data.get('name'),
            character_type=data.get('type', 'named'),
            role=data.get('role', 'supporting'),
            physical=data.get('physical', ''),
            costume=data.get('costume', ''),
            equipment=data.get('equipment', ''),
            personality_visual=data.get('personality_visual', ''),
            consistency_tags=data.get('consistency_tags', ''),
            relationships=data.get('relationships'),
            prototype_template=data.get('prototype_template')
        )

        return jsonify({
            'success': True,
            'character': character
        })

    except Exception as e:
        logger.error(f"Failed to create character: {e}")
        return jsonify({'error': f'Failed to create character: {str(e)}'}), 500


# ============================================================================
# Series/Episode Management APIs
# ============================================================================

@app.route('/api/universes/<universe_id>/series', methods=['GET'])
def list_series(universe_id):
    """Get all series in a universe."""
    try:
        comp = get_components()
        series_list = comp['series_mgr'].list_series(universe_id)

        return jsonify({
            'success': True,
            'series': series_list
        })

    except Exception as e:
        logger.error(f"Failed to list series: {e}")
        return jsonify({'error': f'Failed to fetch series list: {str(e)}'}), 500


@app.route('/api/universes/<universe_id>/series', methods=['POST'])
def create_series(universe_id):
    """Create a new series."""
    try:
        data = request.get_json()

        comp = get_components()
        series = comp['series_mgr'].create_series(
            universe_id=universe_id,
            series_id=data.get('series_id'),
            name=data.get('name'),
            description=data.get('description', '')
        )

        return jsonify({
            'success': True,
            'series': series
        })

    except Exception as e:
        logger.error(f"Failed to create series: {e}")
        return jsonify({'error': f'Failed to create series: {str(e)}'}), 500


@app.route('/api/universes/<universe_id>/episodes', methods=['GET'])
def list_episodes(universe_id):
    """Get all episodes in a universe."""
    try:
        comp = get_components()
        series_id = request.args.get('series_id')  # Optional filter

        episodes = comp['series_mgr'].list_episodes(universe_id, series_id)

        return jsonify({
            'success': True,
            'episodes': episodes
        })

    except Exception as e:
        logger.error(f"Failed to list episodes: {e}")
        return jsonify({'error': f'Failed to fetch episode list: {str(e)}'}), 500


@app.route('/api/series/next-suggestions', methods=['POST'])
def get_next_episode_suggestions():
    """Get AI-generated next episode suggestions."""
    try:
        data = request.get_json()
        universe_id = data.get('universe_id')
        series_id = data.get('series_id')

        if not all([universe_id, series_id]):
            return jsonify({'error': 'Required fields are missing'}), 400

        comp = get_components()

        # Get universe info
        universe = comp['universe_mgr'].get_universe(universe_id)
        if not universe:
            return jsonify({'error': 'Universe not found'}), 404

        # Get latest episode
        latest_episode = comp['series_mgr'].get_latest_episode(universe_id, series_id)
        previous_summary = ""
        if latest_episode:
            previous_summary = comp['series_mgr'].get_episode_summary(
                universe_id,
                latest_episode['episode_number']
            )

        # Get characters
        characters = comp['character_mgr'].list_characters(universe_id, 'named')
        character_summaries = [
            f"{char['name']} ({char['role']}): {char['physical']}"
            for char in characters[:5]  # Top 5 characters
        ]

        # Get timeline
        timeline_summary = comp['timeline_mgr'].get_timeline_summary(universe_id)

        # Generate suggestions
        suggestions = comp['suggester'].suggest_next_episodes(
            universe_summary=universe['background'],
            previous_episode_summary=previous_summary or "First episode",
            character_summaries=character_summaries,
            timeline_summary=timeline_summary,
            genre=universe['genre']
        )

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        return jsonify({'error': f'Failed to recommend next episode: {str(e)}'}), 500


# ============================================================================
# Timeline & Consistency Check APIs
# ============================================================================

@app.route('/api/universes/<universe_id>/timeline', methods=['GET'])
def get_timeline(universe_id):
    """Get timeline events."""
    try:
        comp = get_components()
        timeline = comp['timeline_mgr'].get_timeline(universe_id)

        return jsonify({
            'success': True,
            'timeline': timeline
        })

    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        return jsonify({'error': f'Failed to fetch timeline: {str(e)}'}), 500


@app.route('/api/universes/<universe_id>/consistency-check', methods=['POST'])
def check_consistency(universe_id):
    """Check story consistency."""
    try:
        data = request.get_json()
        proposed_story = data.get('story', '')
        proposed_episode = data.get('episode_number', 1)
        character_ids = data.get('character_ids', [])

        comp = get_components()
        results = comp['timeline_mgr'].check_story_consistency(
            universe_id,
            proposed_story,
            proposed_episode,
            character_ids
        )

        return jsonify({
            'success': True,
            'consistency': results
        })

    except Exception as e:
        logger.error(f"Consistency check failed: {e}")
        return jsonify({'error': f'Consistency check failed: {str(e)}'}), 500


# ============================================================================
# AI Short Factory - Automatic Video Generation APIs
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check health of all backend engines (llama-server, ComfyUI, WAN2.2)."""
    try:
        health = check_engines_health()

        return jsonify({
            'success': True,
            'ok': health['overall'],
            'engines': {
                'llama_server': health['llama_server'],
                'comfyui': health['comfyui'],
                'wan22': health['wan22']
            }
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'ok': False,
            'error': str(e)
        }), 500


@app.route('/api/shorts/generate', methods=['POST'])
def generate_short_api():
    """Generate a complete AI short video (fully automatic pipeline).

    Request JSON:
    {
        "title_hint": "optional string",
        "theme": "string (required)",
        "style": "cinematic / anime / watercolor / etc (default: cinematic)",
        "scene_count": 4 (default)
    }

    Response JSON:
    {
        "success": true,
        "short_id": "uuid-or-timestamp",
        "title": "string",
        "synopsis": "string",
        "scenes": [
            {
                "id": 1,
                "image_path": "relative/path/to/png",
                "video_path": "relative/path/to/scene_mp4",
                "prompt": "string"
            }
        ],
        "final_video_path": "relative/path/to/short_final.mp4",
        "duration_sec": float
    }
    """
    try:
        data = request.get_json()
        theme = data.get('theme', '').strip()
        style = data.get('style', 'cinematic').strip()
        scene_count = int(data.get('scene_count', 20))
        title_hint = data.get('title_hint', '').strip() or None

        if not theme:
            return jsonify({'error': 'Theme is required'}), 400

        if scene_count < 12 or scene_count > 30:
            return jsonify({'error': 'Scene count must be between 12 and 30'}), 400

        logger.info(f"Starting short generation: theme='{theme}', style='{style}', scenes={scene_count}")

        # Run the full pipeline (synchronous - single-user environment)
        result = generate_short(
            theme=theme,
            style=style,
            scene_count=scene_count,
            title_hint=title_hint,
        )

        return jsonify({
            'success': True,
            'short_id': result['short_id'],
            'title': result['title'],
            'synopsis': result['synopsis'],
            'scenes': result['scenes'],
            'final_video_path': result['final_video_path'],
            'duration_sec': result['duration_sec'],
            'status': result['status']
        })

    except Exception as e:
        logger.error(f"Short generation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Short generation failed: {str(e)}'
        }), 500


@app.route('/api/shorts/<short_id>/status', methods=['GET'])
def get_short_status(short_id):
    """Get the status of a short video generation pipeline.

    Returns progress & status:
    - pending, generating_story, generating_images, generating_videos,
      concatenating, done, error

    Response JSON:
    {
        "success": true,
        "short_id": "string",
        "status": "string",
        "progress": 0-100,
        "current_step": "string",
        "error": "string or null",
        "title": "string",
        "synopsis": "string",
        "scenes": [...],
        "final_video_path": "string or null"
    }
    """
    try:
        state = get_pipeline_status(short_id)

        if state is None:
            return jsonify({
                'success': False,
                'error': f'Short {short_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'short_id': short_id,
            'status': state.get('status', PipelineStatus.PENDING),
            'progress': state.get('progress', 0),
            'current_step': state.get('current_step', ''),
            'error': state.get('error'),
            'title': state.get('title', ''),
            'synopsis': state.get('synopsis', ''),
            'scenes': state.get('scenes', []),
            'final_video_path': state.get('final_video_path')
        })

    except Exception as e:
        logger.error(f"Failed to get status for {short_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Single-user local environment: sequential processing
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=False,  # single user: sequential handling is sufficient
        use_reloader=False  # avoid conflicts with llama-server
    )
