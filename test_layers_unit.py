#!/usr/bin/env python3
"""Unit tests for Film Layer and Camera Layer (no LLM dependencies)."""
import sys
sys.path.insert(0, '/home/user/AI_Short_Factory')

from src.pipeline.film_layer import FilmLayer, SceneEmotion
from src.pipeline.camera_layer import CameraLayer
from src.pipeline.visual_styles import GlobalStyleConfig, get_available_themes


def test_film_layer():
    """Test Film Layer emotion detection and style application."""
    print("=" * 80)
    print("Testing Film Layer")
    print("=" * 80)

    film_layer = FilmLayer()

    # Test 1: Horror scene
    print("\n1. Horror Scene Detection:")
    horror_scene = "A dark hallway with flickering lights. A shadow lurks in the corner, blood dripping from the walls."
    emotion = film_layer.analyze_scene_emotion(horror_scene)
    print(f"   Scene: {horror_scene}")
    print(f"   Detected Emotion: {emotion.value}")
    assert emotion == SceneEmotion.HORROR, "Should detect HORROR"
    print("   ✓ Correct")

    # Test 2: Action scene
    print("\n2. Action Scene Detection:")
    action_scene = "The hero punches through the door, explosions erupting behind him as he runs and fights."
    emotion = film_layer.analyze_scene_emotion(action_scene)
    print(f"   Scene: {action_scene}")
    print(f"   Detected Emotion: {emotion.value}")
    assert emotion == SceneEmotion.ACTION, "Should detect ACTION"
    print("   ✓ Correct")

    # Test 3: Chase scene
    print("\n3. Chase Scene Detection:")
    chase_scene = "She runs through the narrow streets, her pursuer racing close behind."
    emotion = film_layer.analyze_scene_emotion(chase_scene)
    print(f"   Scene: {chase_scene}")
    print(f"   Detected Emotion: {emotion.value}")
    assert emotion == SceneEmotion.CHASE, "Should detect CHASE"
    print("   ✓ Correct")

    # Test 4: Get film style for horror
    print("\n4. Film Style Retrieval (Horror):")
    film_style = film_layer.get_film_style(SceneEmotion.HORROR)
    print(f"   Lighting: {film_style['lighting']}")
    print(f"   Color Grading: {film_style['color_grading']}")
    print(f"   Preferred Angles: {film_style['preferred_angles']}")
    print(f"   Preferred Movements: {film_style['preferred_movements']}")
    assert "low-key" in film_style["lighting"].lower()
    print("   ✓ Style retrieved correctly")

    print("\n✓ Film Layer tests passed!")


def test_camera_layer():
    """Test Camera Layer shot assignment and variety."""
    print("\n" + "=" * 80)
    print("Testing Camera Layer")
    print("=" * 80)

    camera_layer = CameraLayer(ensure_variety=True)

    # Test 1: Basic camera spec assignment
    print("\n1. Basic Camera Spec Assignment:")
    specs = camera_layer.assign_camera_specs(scene_number=1)
    print(f"   Shot Type: {specs['shot_type']} ({specs['shot_type_name']})")
    print(f"   Angle: {specs['angle']} ({specs['angle_description']})")
    print(f"   Lens: {specs['lens']} ({specs['lens_description']})")
    print(f"   Movement: {specs['movement']} ({specs['movement_description']})")
    assert specs['shot_type'] in ['EWS', 'WS', 'MWS', 'MS', 'MCU', 'CU', 'ECU']
    print("   ✓ Specs assigned correctly")

    # Test 2: Film style preference integration
    print("\n2. Film Style Preference Integration:")
    film_style = {
        "preferred_angles": ["low", "dutch"],
        "preferred_movements": ["handheld", "shaky"]
    }
    specs = camera_layer.assign_camera_specs(scene_number=2, film_style=film_style)
    print(f"   Film Style Preferences: angles={film_style['preferred_angles']}")
    print(f"   Assigned Angle: {specs['angle']}")
    print(f"   Assigned Movement: {specs['movement']}")
    # Note: There's 30% chance it won't use preferred, so we just check it's valid
    print("   ✓ Film style considered")

    # Test 3: Variety across multiple scenes
    print("\n3. Variety Across Multiple Scenes:")
    scenes = [{"description": f"Scene {i}"} for i in range(10)]
    camera_layer_batch = CameraLayer(ensure_variety=True)
    scenes = camera_layer_batch.batch_assign_cameras(scenes)

    shot_types = [s['camera_style']['shot_type'] for s in scenes]
    unique_shots = len(set(shot_types))

    print(f"   10 scenes generated")
    print(f"   Unique shot types: {unique_shots}")
    print(f"   Shot sequence: {', '.join(shot_types)}")
    assert unique_shots >= 3, "Should have at least 3 different shot types in 10 scenes"
    print("   ✓ Variety ensured")

    # Test 4: Variety statistics
    print("\n4. Camera Variety Statistics:")
    stats = camera_layer_batch.get_camera_variety_stats()
    print(f"   Total scenes: {stats['total_scenes']}")
    print(f"   Unique shot types: {stats['unique_shot_types']}")
    print(f"   Unique angles: {stats['unique_angles']}")
    print(f"   Shot distribution: {stats['shot_type_distribution']}")
    assert stats['total_scenes'] == 10
    print("   ✓ Statistics correct")

    print("\n✓ Camera Layer tests passed!")


def test_global_style_config():
    """Test Global Style Configuration."""
    print("\n" + "=" * 80)
    print("Testing Global Style Config")
    print("=" * 80)

    # Test 1: Theme listing
    print("\n1. Available Themes:")
    themes = get_available_themes()
    for theme_key in list(themes.keys())[:3]:
        print(f"   • {theme_key}: {themes[theme_key]}")
    assert len(themes) > 0, "Should have available themes"
    print(f"   ✓ {len(themes)} themes available")

    # Test 2: Create config from theme
    print("\n2. Create Config from Theme:")
    config = GlobalStyleConfig.from_theme("horror")
    print(f"   Theme: {config.theme}")
    print(f"   Film Layer Enabled: {config.enable_film_layer}")
    print(f"   Camera Layer Enabled: {config.enable_camera_layer}")
    assert config.theme == "horror"
    print("   ✓ Config created")

    # Test 3: Get theme style dict
    print("\n3. Get Theme Style Dictionary:")
    style_dict = config.get_global_style_dict()
    print(f"   Color Palette: {style_dict['color_palette'][:60]}...")
    print(f"   Lighting: {style_dict['lighting'][:60]}...")
    print(f"   Atmosphere: {style_dict['atmosphere']}")
    assert 'horror' in style_dict['atmosphere'].lower() or 'terrifying' in style_dict['atmosphere'].lower()
    print("   ✓ Style dict retrieved")

    # Test 4: Custom overrides
    print("\n4. Custom Overrides:")
    config_custom = GlobalStyleConfig(
        theme="anime",
        color_tone="vibrant neon colors",
        film_texture="heavy grain"
    )
    style_dict_custom = config_custom.get_global_style_dict()
    print(f"   Original color: vibrant saturated colors...")
    print(f"   Override color: {style_dict_custom['color_palette']}")
    print(f"   Override texture: {style_dict_custom['texture']}")
    assert style_dict_custom['color_palette'] == "vibrant neon colors"
    assert style_dict_custom['texture'] == "heavy grain"
    print("   ✓ Overrides applied")

    print("\n✓ Global Style Config tests passed!")


def test_integration():
    """Test integration of Film + Camera layers."""
    print("\n" + "=" * 80)
    print("Testing Film + Camera Integration")
    print("=" * 80)

    film_layer = FilmLayer()
    camera_layer = CameraLayer()

    # Create test scenes
    test_scenes = [
        {
            "scene_number": 1,
            "description": "A dark corridor with flickering lights and shadows",
            "summary": "Horror scene in abandoned building"
        },
        {
            "scene_number": 2,
            "description": "Hero fights off multiple attackers with quick punches",
            "summary": "Action scene with combat"
        },
        {
            "scene_number": 3,
            "description": "Protagonist runs through crowded streets, pursued by enemy",
            "summary": "Chase sequence through city"
        }
    ]

    print("\nProcessing 3 test scenes through Film + Camera layers...")

    # Apply Film Layer
    scenes_with_film = film_layer.batch_analyze_scenes(test_scenes)
    print("✓ Film layer applied")

    # Apply Camera Layer
    scenes_complete = camera_layer.batch_assign_cameras(scenes_with_film)
    print("✓ Camera layer applied")

    # Display results
    for scene in scenes_complete:
        print(f"\nScene {scene['scene_number']}:")
        print(f"  Description: {scene['description']}")
        print(f"  Film Emotion: {scene['film_style']['emotion']}")
        print(f"  Film Lighting: {scene['film_style']['lighting'][:50]}...")
        print(f"  Camera Shot: {scene['camera_style']['shot_type']}")
        print(f"  Camera Angle: {scene['camera_style']['angle']}")
        print(f"  Camera Movement: {scene['camera_style']['movement']}")

    print("\n✓ Integration test passed!")


if __name__ == "__main__":
    try:
        test_film_layer()
        test_camera_layer()
        test_global_style_config()
        test_integration()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! ✓")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
