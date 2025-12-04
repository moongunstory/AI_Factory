"""Flask web UI for AI Short Factory."""
import os
import sys
import atexit
import signal
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.story_expander import StoryExpander
from src.pipeline.prompt_generator import PromptGenerator
from src.pipeline.character_extractor import CharacterExtractor
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
from src.web.services.video_client import ComfyUIVideoClient
from src.common.config import Config

logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False

# Ensure base output structure exists
Config.ensure_output_dirs()

# Initialize AI components (singleton)
components = None


class ProjectStorage:
    """Utility for project-scoped persistence following the new autosave rules."""

    BASE_DIRS = {
        'oneshot': Config.ONESHOT_DIR,
        'series': Config.SERIES_DIR,
        'meme': Config.MEME_DIR,
    }

    @classmethod
    def _sanitize_title(cls, title: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9가-힣_-]+", "_", title or "")
        cleaned = cleaned.strip("_")
        return cleaned or "project"

    @classmethod
    def _get_base_dir(cls, mode: str):
        return cls.BASE_DIRS.get(mode, Config.ONESHOT_DIR)

    @classmethod
    def _find_existing_project_dir(cls, project_id: str) -> tuple[Path | None, str | None]:
        for mode_name, base_dir in cls.BASE_DIRS.items():
            candidate = base_dir / project_id
            if candidate.exists():
                return candidate, mode_name
        return None, None

    @classmethod
    def get_project_dir(
        cls,
        mode: str | None = None,
        project_id: str | None = None,
        title: str | None = None,
    ) -> tuple[Path, str, str]:
        """Resolve or create a project directory and return (path, project_id, mode)."""

        resolved_mode = mode or 'oneshot'
        resolved_project_id = project_id

        existing_dir = None
        existing_mode = None
        if project_id:
            existing_dir, existing_mode = cls._find_existing_project_dir(project_id)
            if existing_dir:
                resolved_mode = existing_mode or resolved_mode
                resolved_project_id = project_id

        if not existing_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = cls._sanitize_title(title or 'project')
            resolved_project_id = project_id or f"{timestamp}_{safe_title}"
            existing_dir = cls._get_base_dir(resolved_mode) / resolved_project_id

        existing_dir.mkdir(parents=True, exist_ok=True)
        for child in ("story", "prompts", "images", "video", "audio"):
            (existing_dir / child).mkdir(parents=True, exist_ok=True)
        return existing_dir, resolved_project_id, resolved_mode

    @classmethod
    def _write_json(cls, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def write_metadata(
        cls,
        mode: str,
        project_id: str,
        project_title: str | None = None,
        created_at: str | None = None,
        current_step: int | None = None,
        **kwargs,
    ) -> dict:
        project_dir, resolved_id, resolved_mode = cls.get_project_dir(mode, project_id, project_title)
        metadata_path = project_dir / 'metadata.json'
        existing = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = {}

        merged = {
            **existing,
            'project_id': resolved_id,
            'project_title': project_title or existing.get('project_title') or kwargs.get('simple_idea') or 'Untitled',
            'mode': resolved_mode,
            'created_at': created_at or existing.get('created_at') or datetime.now().strftime('%Y%m%d_%H%M%S'),
        }

        if current_step is not None:
            merged['current_step'] = max(current_step, existing.get('current_step', 0))

        merged.update(kwargs)

        paths = merged.get('paths', {})
        paths.setdefault('story', str((project_dir / 'story' / 'story.json').relative_to(project_root)))
        paths.setdefault('prompts', str((project_dir / 'prompts' / 'prompts.json').relative_to(project_root)))
        paths.setdefault('images', str((project_dir / 'images').relative_to(project_root)))
        paths.setdefault('video', str((project_dir / 'video' / 'final.mp4').relative_to(project_root)))
        paths.setdefault('audio', str((project_dir / 'audio').relative_to(project_root)))
        merged['paths'] = paths

        cls._write_json(metadata_path, merged)
        return merged

    @classmethod
    def save_story(cls, story_payload: dict, mode: str = 'oneshot', project_id: str | None = None) -> dict:
        project_dir, resolved_id, resolved_mode = cls.get_project_dir(
            mode, project_id, story_payload.get('project_title')
        )
        story_path = project_dir / 'story' / 'story.json'
        cls._write_json(story_path, story_payload)
        return cls.write_metadata(
            mode=resolved_mode,
            project_id=resolved_id,
            project_title=story_payload.get('project_title'),
            current_step=1,
            simple_idea=story_payload.get('simple_idea'),
        )

    @classmethod
    def save_prompts(
        cls,
        prompts_payload: dict,
        mode: str = 'oneshot',
        project_id: str | None = None,
        project_title: str | None = None,
    ) -> dict:
        project_dir, resolved_id, resolved_mode = cls.get_project_dir(mode, project_id, project_title)
        prompts_path = project_dir / 'prompts' / 'prompts.json'
        cls._write_json(prompts_path, prompts_payload)
        return cls.write_metadata(
            mode=resolved_mode,
            project_id=resolved_id,
            project_title=project_title,
            current_step=2,
            theme=prompts_payload.get('theme'),
        )

    @classmethod
    def save_images_manifest(
        cls,
        images_payload: list,
        mode: str = 'oneshot',
        project_id: str | None = None,
        project_title: str | None = None,
    ) -> dict:
        project_dir, resolved_id, resolved_mode = cls.get_project_dir(mode, project_id, project_title)
        manifest_path = project_dir / 'images' / 'manifest.json'
        cls._write_json(manifest_path, {'images': images_payload})
        return cls.write_metadata(
            mode=resolved_mode,
            project_id=resolved_id,
            project_title=project_title,
            current_step=3,
        )

    @classmethod
    def save_video_info(
        cls,
        final_path: Path,
        mode: str = 'oneshot',
        project_id: str | None = None,
        project_title: str | None = None,
        duration: float | None = None,
        resolution: str | None = None,
    ) -> dict:
        return cls.write_metadata(
            mode=mode,
            project_id=project_id,
            project_title=project_title,
            current_step=5,
            final_video={
                'path': str(final_path.relative_to(project_root)),
                'duration': duration,
                'resolution': resolution,
            },
        )

    @classmethod
    def list_projects(cls, mode_filter: str | None = None) -> list[dict]:
        projects = []
        mode_dirs = [
            ('oneshot', Config.ONESHOT_DIR),
            ('series', Config.SERIES_DIR),
            ('meme', Config.MEME_DIR),
        ]

        for mode_name, base_dir in mode_dirs:
            if mode_filter and mode_filter != mode_name:
                continue
            if not base_dir.exists():
                continue
            for project_dir in base_dir.iterdir():
                metadata_path = project_dir / 'metadata.json'
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            metadata['mode'] = metadata.get('mode') or mode_name
                            projects.append(metadata)
                    except Exception as exc:
                        logger.warning(f"Failed to read metadata for {project_dir.name}: {exc}")

        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return projects

    @classmethod
    def load_project(cls, mode: str | None, project_id: str) -> dict:
        project_dir, resolved_mode = None, mode

        if not mode:
            project_dir, resolved_mode = cls._find_existing_project_dir(project_id)
        else:
            project_dir = cls._get_base_dir(mode) / project_id
            if not project_dir.exists():
                project_dir = None

        if not project_dir or not project_dir.exists():
            raise FileNotFoundError("project not found")

        metadata_path = project_dir / 'metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError("metadata.json not found")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        story_data = None
        story_path = project_dir / 'story' / 'story.json'
        if story_path.exists():
            with open(story_path, 'r', encoding='utf-8') as f:
                story_data = json.load(f)

        prompts_data = None
        prompts_path = project_dir / 'prompts' / 'prompts.json'
        if prompts_path.exists():
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)

        images = []
        videos = []
        manifest_path = project_dir / 'images' / 'manifest.json'
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    images = manifest.get('images', [])
            except Exception:
                images = []

        video_manifest_path = project_dir / 'video' / 'manifest.json'
        if video_manifest_path.exists():
            try:
                with open(video_manifest_path, 'r', encoding='utf-8') as f:
                    video_manifest = json.load(f)
                    videos = video_manifest.get('videos', [])
            except Exception:
                videos = []

        final_video = metadata.get('final_video')

        return {
            'metadata': {**metadata, 'mode': resolved_mode or metadata.get('mode')},
            'story': story_data,
            'prompts': prompts_data,
            'images': images,
            'videos': videos,
            'final_video': final_video,
        }

    @classmethod
    def delete_project(cls, mode: str, project_id: str) -> None:
        project_dir = cls._get_base_dir(mode) / project_id
        if project_dir.exists():
            import shutil

            shutil.rmtree(project_dir, ignore_errors=True)

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
            'character_extractor': CharacterExtractor(),
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
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')

        if not simple_idea:
            return jsonify({'error': 'Please enter a story idea'}), 400

        logger.info(f"User input: {simple_idea[:50]}...")

        comp = get_components()

        # Expand story (in English)
        expanded = comp['expander'].expand(simple_idea)
        logger.info(f"Expanded story: {expanded[:100]}...")

        metadata = ProjectStorage.save_story(
            {
                'simple_idea': simple_idea,
                'expanded_story': expanded,
                'project_title': simple_idea,
            },
            mode=mode,
            project_id=project_id,
        )

        return jsonify({
            'success': True,
            'expanded_story': expanded,
            'project_id': metadata.get('project_id'),
            'metadata': metadata,
        })

    except Exception as e:
        logger.error(f"Story expansion failed: {e}")
        return jsonify({'error': f'Story expansion failed: {str(e)}'}), 500


@app.route('/api/generate-prompts', methods=['POST'])
def generate_prompts():
    """Generate scene prompts from expanded story using PromptGenerator (English only)."""
    try:
        data = request.get_json()
        expanded_story = data.get('expanded_story', '').strip()
        theme = data.get('theme', 'cinematic_realism').strip()
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')

        if not expanded_story:
            return jsonify({'error': 'No expanded story provided'}), 400

        if not expanded_story and project_id:
            try:
                loaded = ProjectStorage.load_project(mode, project_id)
                expanded_story = loaded.get('story', {}).get('expanded_story', '')
            except FileNotFoundError:
                pass

        if not expanded_story:
            return jsonify({'error': 'No story available'}), 400

        logger.info(f"Generating scene prompts with theme: {theme}...")
        logger.info(f"Using story: {expanded_story[:100]}...")

        comp = get_components()
        generator = comp['generator']  # Use PromptGenerator (multi-step pipeline)
        character_extractor = comp['character_extractor']  # CharacterExtractor

        # Generate scenes using the stable multi-step pipeline
        logger.info("Generating scenes using multi-step pipeline...")
        scenes_result = generator.generate(expanded_story, temperature=0.7)

        # Extract scenes
        scenes = scenes_result.get('scenes', [])

        # Extract characters from the story
        logger.info("Extracting characters from story...")
        character_sheets = character_extractor.extract(expanded_story, temperature=0.5)

        # Prepare final prompts data
        prompts_data = {
            'scenes': scenes,
            'total_scenes': scenes_result.get('total_scenes', len(scenes)),
            'estimated_duration': scenes_result.get('estimated_duration', 0)
        }

        story_metadata = ProjectStorage.save_story(
            {
                'simple_idea': data.get('simple_idea') or '',
                'expanded_story': expanded_story,
                'character_sheets': character_sheets,
                'project_title': data.get('project_title') or expanded_story[:20] or 'Untitled',
            },
            mode=mode,
            project_id=project_id,
        )
        prompts_metadata = ProjectStorage.save_prompts(
            {
                'scenes': scenes,
                'total_scenes': scenes_result.get('total_scenes', len(scenes)),
                'estimated_duration': scenes_result.get('estimated_duration', 0),
                'theme': theme,
            },
            mode=mode,
            project_id=story_metadata.get('project_id'),
            project_title=story_metadata.get('project_title'),
        )

        logger.info(f"Generated {len(scenes)} scenes successfully")
        logger.info(f"Extracted {len(character_sheets.get('characters', []))} characters")

        return jsonify({
            'success': True,
            'prompts_data': prompts_data,
            'story_beats': [],  # Empty for backwards compatibility
            'character_sheets': character_sheets,
            'project_id': prompts_metadata.get('project_id'),
            'metadata': prompts_metadata,
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
    """Regenerate multiple selected scenes using PromptGenerator (English only)."""
    try:
        data = request.get_json()
        scenes_to_regenerate = data.get('scenes', [])
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')
        theme = data.get('theme', 'cinematic_realism')

        if not scenes_to_regenerate:
            return jsonify({'error': 'No scenes to regenerate'}), 400

        logger.info(f"Regenerating {len(scenes_to_regenerate)} scenes...")

        comp = get_components()
        generator = comp['generator']  # Use PromptGenerator

        regenerated_scenes = []

        for scene_info in scenes_to_regenerate:
            scene_number = scene_info.get('scene_number')
            scene_description = scene_info.get('scene_description', '')

            # Regenerate this scene with PromptGenerator
            new_scene = generator.regenerate_scene(
                scene_number=scene_number,
                scene_description=scene_description,
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
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')

        if not prompts_data:
            try:
                loaded = ProjectStorage.load_project(mode, project_id)
                prompts_data = loaded.get('prompts')
            except Exception:
                prompts_data = None

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

        project_dir, resolved_id, resolved_mode = ProjectStorage.get_project_dir(
            mode, project_id
        )
        images_dir = project_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        generated_images = []

        for i, scene in enumerate(scenes, 1):
            scene_number = scene.get('scene_number', i)
            prompt = scene.get('prompt_en', '')

            if not prompt:
                logger.warning(f"Scene {scene_number} has no prompt, skipping")
                continue

            logger.info(f"Generating image {i}/{len(scenes)}: Scene {scene_number}...")

            image_path = images_dir / f"{scene_number:03d}.png"

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

        metadata = ProjectStorage.save_images_manifest(
            generated_images,
            mode=resolved_mode,
            project_id=resolved_id,
        )

        logger.info(f"Generated {len([img for img in generated_images if img['image_path']])} images successfully")

        return jsonify({
            'success': True,
            'images': generated_images,
            'project_id': resolved_id,
            'metadata': metadata,
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

        project_dir, resolved_id, resolved_mode = ProjectStorage.get_project_dir(
            mode, project_id
        )
        images_dir = project_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        regenerated_images = []

        for scene_info in scenes_to_regenerate:
            scene_number = scene_info.get('scene_number')
            prompt = scene_info.get('prompt', '')

            if not prompt:
                logger.warning(f"Scene {scene_number} has no prompt, skipping")
                continue

            logger.info(f"Regenerating image for scene {scene_number}...")

            image_path = images_dir / f"{scene_number:03d}.png"

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

        metadata = ProjectStorage.save_images_manifest(
            regenerated_images,
            mode=resolved_mode,
            project_id=resolved_id,
        )

        return jsonify({
            'success': True,
            'images': regenerated_images,
            'project_id': resolved_id,
            'metadata': metadata,
        })

    except Exception as e:
        logger.error(f"Image regeneration failed: {e}")
        return jsonify({'error': f'Image regeneration failed: {str(e)}'}), 500


# ============================================================================
# Video Generation APIs (ComfyUI WAN2.2 workflow)
# ============================================================================

@app.route('/api/generate-videos', methods=['POST'])
def generate_videos():
    """Generate videos from images using ComfyUI WAN2.2 workflow."""
    try:
        data = request.get_json()
        video_requests = data.get('videos', [])
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')
        options = data.get('options', {})

        if not video_requests:
            return jsonify({'error': 'No videos to generate'}), 400

        logger.info(f"Generating videos for {len(video_requests)} scenes via ComfyUI...")

        # Initialize ComfyUI workflow client
        video_client = ComfyUIVideoClient()

        # Create output directory
        project_dir, resolved_id, resolved_mode = ProjectStorage.get_project_dir(mode, project_id)
        videos_dir = project_dir / 'video'
        videos_dir.mkdir(parents=True, exist_ok=True)

        generated_videos = []

        default_duration = float(options.get('duration', 2.5) or 2.5)
        default_camera = options.get('camera') or 'cinematic movement'
        default_fps = int(options.get('fps', 24) or 24)

        for i, video_req in enumerate(video_requests, 1):
            scene_number = video_req.get('scene_number')
            image_path = project_root / video_req.get('image_path')
            video_prompt = video_req.get('video_prompt', default_camera)
            duration = float(video_req.get('duration', default_duration) or default_duration)
            fps = int(video_req.get('fps', default_fps) or default_fps)

            if not image_path.exists():
                logger.warning(f"Image not found for scene {scene_number}: {image_path}")
                generated_videos.append({
                    'scene_number': scene_number,
                    'video_path': None,
                    'video_prompt': video_prompt,
                    'duration': duration,
                    'error': f'Image not found: {image_path}'
                })
                continue

            logger.info(f"Generating video {i}/{len(video_requests)}: Scene {scene_number}...")

            video_path = videos_dir / f"scene_{scene_number:03d}.mp4"

            try:
                video_client.generate_video(
                    image_path=image_path,
                    output_path=video_path,
                    duration_sec=duration,
                    fps=fps,
                    camera_prompt=video_prompt,
                )

                # Store relative path for frontend
                relative_path = str(video_path.relative_to(project_root))

                generated_videos.append({
                    'scene_number': scene_number,
                    'video_path': relative_path,
                    'video_prompt': video_prompt,
                    'duration': duration,
                    'fps': fps
                })

                logger.info(f"✓ Video {i}/{len(video_requests)} generated: {video_path.name}")

            except Exception as e:
                logger.error(f"Failed to generate video for scene {scene_number}: {e}")
                generated_videos.append({
                    'scene_number': scene_number,
                    'video_path': None,
                    'video_prompt': video_prompt,
                    'duration': duration,
                    'error': str(e)
                })

        # Persist manifest for resume support
        manifest_path = videos_dir / 'manifest.json'
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as manifest_file:
            json.dump({'videos': generated_videos}, manifest_file, ensure_ascii=False, indent=2)

        try:
            ProjectStorage.write_metadata(
                mode=resolved_mode,
                project_id=resolved_id,
                project_title=(ProjectStorage.load_project(resolved_mode, resolved_id).get('metadata', {}).get('project_title')),
                current_step=4,
            )
        except Exception:
            logger.warning("Failed to update metadata after video generation", exc_info=True)

        success_count = len([v for v in generated_videos if v['video_path']])
        logger.info(f"Generated {success_count}/{len(video_requests)} videos successfully")

        return jsonify({
            'success': True,
            'videos': generated_videos,
            'project_id': resolved_id,
        })

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return jsonify({'error': f'Video generation failed: {str(e)}'}), 500


@app.route('/api/assemble-final-video', methods=['POST'])
def assemble_final_video():
    """Assemble final video with BGM and subtitles."""
    try:
        data = request.get_json()
        videos = data.get('videos', [])
        options = data.get('options', {})
        mode = data.get('mode') or 'oneshot'
        project_id = data.get('project_id')

        if not videos:
            return jsonify({'error': 'No videos to assemble'}), 400

        logger.info(f"Assembling final video from {len(videos)} segments...")
        logger.info(f"Options: {options}")

        # Filter valid videos
        valid_videos = [v for v in videos if v.get('video_path')]
        if not valid_videos:
            return jsonify({'error': 'No valid video segments found'}), 400

        project_dir, resolved_id, resolved_mode = ProjectStorage.get_project_dir(mode, project_id)
        final_dir = project_dir / 'video'
        final_dir.mkdir(parents=True, exist_ok=True)

        # Prepare video paths
        video_paths = [project_root / v['video_path'] for v in valid_videos]

        # Generate output path
        final_video_path = final_dir / "final.mp4"

        # Use ffmpeg to concatenate videos
        import subprocess
        import tempfile

        # Create concat file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as concat_file:
            for video_path in video_paths:
                # Use absolute paths and escape single quotes
                abs_path = str(video_path.absolute()).replace("'", "'\\''")
                concat_file.write(f"file '{abs_path}'\n")
            concat_file_path = concat_file.name

        try:
            # Concatenate videos
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file_path,
                '-c', 'copy',
                '-y',
                str(final_video_path)
            ]

            logger.info(f"Running ffmpeg concat: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"ffmpeg concat failed: {result.stderr}")
                raise RuntimeError(f"Video concatenation failed: {result.stderr}")

            logger.info(f"✓ Videos concatenated successfully: {final_video_path}")

            # TODO: Add BGM if requested
            if options.get('add_bgm', False):
                logger.info("BGM addition requested (not yet implemented)")
                # Future: Add BGM using ffmpeg audio overlay

            # TODO: Add subtitles if requested
            if options.get('add_subtitles', False):
                logger.info("Subtitle addition requested (not yet implemented)")
                # Future: Generate subtitles using story text and add with ffmpeg

            # Calculate total duration
            total_duration = sum(v.get('duration', 2.5) for v in valid_videos)

            # Get video info
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(final_video_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            resolution = probe_result.stdout.strip() if probe_result.returncode == 0 else '768x1365'

            # Store relative path for frontend
            relative_path = str(final_video_path.relative_to(project_root))

            metadata = ProjectStorage.save_video_info(
                final_path=final_video_path,
                duration=total_duration,
                resolution=resolution,
                mode=resolved_mode,
                project_id=resolved_id,
                project_title=options.get('project_title'),
            )
            logger.info(f"Final video assembly complete: {relative_path}")

            return jsonify({
                'success': True,
                'final_video_path': relative_path,
                'duration': total_duration,
                'resolution': resolution,
                'metadata': metadata,
                'project_id': resolved_id,
            })

        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(concat_file_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Final video assembly failed: {e}")
        return jsonify({'error': f'Final video assembly failed: {str(e)}'}), 500


# ============================================================================
# Project Save/Load APIs
# ============================================================================

@app.route('/api/load-project', methods=['POST'])
def load_project():
    """Load a saved project using metadata.json."""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        mode = data.get('mode')

        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400

        loaded = ProjectStorage.load_project(mode, project_id)
        logger.info(f"Project loaded: {project_id}")

        return jsonify({
            'success': True,
            'project': loaded
        })

    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        logger.error(f"Project load failed: {e}")
        return jsonify({'error': f'Project load failed: {str(e)}'}), 500


@app.route('/api/list-projects', methods=['GET'])
def list_projects():
    """List all saved projects using metadata.json in the new directory structure."""
    try:
        mode_filter = request.args.get('mode')
        projects = ProjectStorage.list_projects(mode_filter)

        return jsonify({
            'success': True,
            'projects': projects
        })

    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return jsonify({'error': f'Failed to list projects: {str(e)}'}), 500


@app.route('/api/delete-project', methods=['POST'])
def delete_project():
    """Delete a project folder immediately."""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        mode = data.get('mode', 'oneshot')

        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400

        ProjectStorage.delete_project(mode, project_id)
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return jsonify({'error': f'Failed to delete project: {str(e)}'}), 500


@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    """Delete a single output file within the project output directory."""
    try:
        data = request.get_json()
        rel_path = data.get('path')

        if not rel_path:
            return jsonify({'error': 'Path is required'}), 400

        target_path = (project_root / rel_path).resolve()
        base_output = Config.OUTPUT_DIR.resolve()

        if base_output not in target_path.parents and target_path != base_output:
            return jsonify({'error': 'Only files inside the output directory can be deleted'}), 400

        if not target_path.exists():
            return jsonify({'error': 'File not found'}), 404

        if target_path.is_dir():
            return jsonify({'error': 'Directory deletion is not allowed via this endpoint'}), 400

        target_path.unlink()
        logger.info(f"Deleted file: {target_path}")
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


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
    """Check health of all backend engines (llama-server, ComfyUI)."""
    try:
        health = check_engines_health()

        return jsonify({
            'success': True,
            'ok': health['overall'],
            'engines': {
                'llama_server': health['llama_server'],
                'comfyui': health['comfyui']
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
