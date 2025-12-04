#!/usr/bin/env python3
"""Run prompt generator end-to-end test without pytest.

이 스크립트는 pytest 없이도 테스트를 실행할 수 있도록 합니다.
"""
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.prompt_generator import PromptGenerator, generate_prompts
from src.generators.llm import LlamaClient


# 배틀로얄 테스트 스토리
BATTLE_ROYALE_STORY = """
The Last Stand: Battle Royale Chronicles

Twenty contestants stood at the edge of the desolate wasteland arena, each equipped with a basic survival kit and determination to be the last one standing. The rusted gates slammed shut behind them with a deafening clang, sealing their fate. A digital countdown appeared in the sky: 60 minutes until only one could remain.

Sarah, a former military scout, immediately sprinted toward the abandoned factory district in the north. She knew high ground and cover would be essential. Behind her, chaos erupted as desperate contestants clashed over the limited weapons scattered near the starting zone. Two fell within the first minute.

Climbing through a broken window, Sarah found a storage room with a pistol and ammunition. Through the dusty glass, she watched the killzone shrink - a deadly forcefield slowly pushing everyone toward the center. Eighteen remained.

In the southern ruins, Marcus formed an uneasy alliance with two others. They moved as a unit, overwhelming isolated targets. But trust was fragile in this game. When they found a supply cache, greed turned allies into enemies. Only Marcus walked away. Fifteen remained.

The forcefield's relentless advance forced confrontations. Sarah's military training served her well - she picked off three contestants from her factory perch before being forced to relocate. Twelve remained.

A massive explosion rocked the arena as someone triggered a trap in the eastern sector. The blast took out four contestants at once. Eight remained.

Sarah and Marcus finally met in the central plaza, circling each other like predators. Their fight was brutal and desperate. Both were wounded, but Sarah's combat experience gave her the edge. Seven remained.

The final minutes were the deadliest. The forcefield compressed the survivors into a small courtyard. Sarah found a rocket launcher in a final supply drop. She took calculated risks, using the chaos to her advantage. Six, five, four...

With only three left, Sarah faced off against two contestants who had allied. She was outgunned and outmaneuvered. A bullet grazed her shoulder. She dove behind cover, breathing hard.

The arena announced: "Five minutes remaining."

Sarah made her move. She used her last grenade to create a diversion, then flanked around through a collapsed building. One shot, one kill. Two remained.

Her final opponent was skilled and desperate. They exchanged fire across the burning courtyard. Sarah's ammunition ran low. She made a decision - charge forward instead of retreat. Surprise was her only advantage.

The final bullet found its mark. The arena fell silent except for Sarah's ragged breathing.

"Winner: Sarah. Time: 58 minutes, 43 seconds."

She collapsed to her knees as the gates opened, the last one standing in the wasteland.
"""


def test_beats_summarization():
    """Test that story summarization into beats works correctly."""
    print("\n" + "=" * 80)
    print("TEST: Beats Summarization")
    print("=" * 80)

    try:
        client = LlamaClient()
        if not client.is_server_ready():
            print("❌ SKIP: llama-server is not running")
            return False

        generator = PromptGenerator(llm_client=client)
        beats = generator._summarize_story_to_beats(BATTLE_ROYALE_STORY)

        print(f"\n✓ Story summarized into {len(beats)} plot beats")

        # Validate
        assert len(beats) >= 8, f"Should have at least 8 beats, got {len(beats)}"
        assert len(beats) <= 25, f"Should have at most 25 beats, got {len(beats)}"

        for i, beat in enumerate(beats):
            assert beat.strip(), f"Beat {i} is empty"

        print("\nSample beats:")
        for i, beat in enumerate(beats[:5]):
            print(f"  {i+1}. {beat[:80]}...")

        print("\n✓ PASSED: Beats summarization")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        traceback.print_exc()
        return False


def test_generate_scenes_from_battle_royale():
    """Test full pipeline with battle royale story."""
    print("\n" + "=" * 80)
    print("TEST: Generate Scenes from Battle Royale Story")
    print("=" * 80)

    try:
        client = LlamaClient()
        if not client.is_server_ready():
            print("❌ SKIP: llama-server is not running")
            return False

        generator = PromptGenerator(llm_client=client)

        print("\nGenerating prompts for battle royale story...")
        result = generator.generate(
            expanded_story=BATTLE_ROYALE_STORY,
            temperature=0.7
        )

        # Validate structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "scenes" in result, "Result must contain 'scenes'"
        assert "total_scenes" in result, "Result must contain 'total_scenes'"
        assert "estimated_duration" in result, "Result must contain 'estimated_duration'"

        scenes = result["scenes"]
        total_scenes = result["total_scenes"]
        estimated_duration = result["estimated_duration"]

        print(f"\n✓ Generated {len(scenes)} scenes")

        # Validate scenes count
        assert len(scenes) >= 2, f"Should have at least 2 scenes, got {len(scenes)}"

        if len(scenes) < 10:
            print(f"⚠ Warning: Only {len(scenes)} scenes for a long battle royale story. Expected 15-30.")

        # Validate total_scenes matches actual count
        assert total_scenes == len(scenes), \
            f"total_scenes ({total_scenes}) should match len(scenes) ({len(scenes)})"

        # Validate each scene
        errors = []
        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)

            # Required fields
            if "scene_number" not in scene:
                errors.append(f"Scene {i} missing 'scene_number'")
            if "prompt_en" not in scene:
                errors.append(f"Scene {scene_num} missing 'prompt_en'")
            if "duration" not in scene:
                errors.append(f"Scene {scene_num} missing 'duration'")

            if errors:
                continue

            # Validate types
            if not isinstance(scene["scene_number"], int):
                errors.append(f"Scene {scene_num}: scene_number should be int")
            if not isinstance(scene["prompt_en"], str):
                errors.append(f"Scene {scene_num}: prompt_en should be str")
            if not isinstance(scene["duration"], (int, float)):
                errors.append(f"Scene {scene_num}: duration should be number")

            # Validate values
            if not scene["prompt_en"].strip():
                errors.append(f"Scene {scene_num}: prompt_en is empty")
            if scene["duration"] <= 0:
                errors.append(f"Scene {scene_num}: duration should be > 0")

            # Check for common error values
            prompt_lower = scene["prompt_en"].lower()
            if "undefined" in prompt_lower:
                errors.append(f"Scene {scene_num}: prompt contains 'undefined'")
            if scene["duration"] == "2s":
                errors.append(f"Scene {scene_num}: duration is string '2s' instead of number")

        if errors:
            print("\n❌ Scene validation errors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
            return False

        # Validate estimated_duration
        assert isinstance(estimated_duration, (int, float)), \
            f"estimated_duration should be number, got {type(estimated_duration)}"
        assert estimated_duration > 0, \
            f"estimated_duration should be > 0, got {estimated_duration}"

        # Verify estimated_duration matches sum of scene durations
        calculated_duration = sum(scene["duration"] for scene in scenes)
        duration_diff = abs(estimated_duration - calculated_duration)
        assert duration_diff < 0.1, \
            f"estimated_duration ({estimated_duration}) != sum of durations ({calculated_duration})"

        # Print summary
        print(f"\n✓ All {len(scenes)} scenes validated successfully")
        print(f"✓ Total duration: {estimated_duration:.1f}s")
        print(f"✓ Average scene duration: {estimated_duration/len(scenes):.1f}s")

        # Check duration range
        if not (45 <= estimated_duration <= 75):
            print(f"⚠ Warning: Total duration {estimated_duration:.1f}s is outside 45-75s guideline")

        # Optional: Check characters field
        scenes_with_characters = sum(1 for s in scenes if "characters" in s)
        if scenes_with_characters > 0:
            print(f"✓ {scenes_with_characters} scenes have character information")

        # Show sample scenes
        print("\nSample scenes:")
        for i, scene in enumerate(scenes[:3]):
            print(f"\n  Scene {scene.get('scene_number', i+1)} ({scene.get('duration', 0)}s):")
            summary = scene.get('summary', '')
            if summary:
                print(f"    Summary: {summary[:60]}...")
            prompt = scene.get('prompt_en', '')
            print(f"    Prompt: {prompt[:80]}...")

        print("\n✓ PASSED: Scene generation from battle royale story")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        traceback.print_exc()
        return False


def test_duration_auto_calculation():
    """Test that duration is automatically calculated."""
    print("\n" + "=" * 80)
    print("TEST: Duration Auto-Calculation")
    print("=" * 80)

    try:
        client = LlamaClient()
        generator = PromptGenerator(llm_client=client)

        # Create a mock result with wrong estimated_duration
        mock_result = {
            "scenes": [
                {"scene_number": 1, "prompt_en": "test1", "duration": 3.0},
                {"scene_number": 2, "prompt_en": "test2", "duration": 4.0},
                {"scene_number": 3, "prompt_en": "test3", "duration": 2.5},
            ],
            "total_scenes": 3,
            "estimated_duration": 999.0  # Wrong value
        }

        validated = generator._validate_and_normalize_result(mock_result)

        # Should recalculate to correct value
        expected_duration = 3.0 + 4.0 + 2.5
        assert validated["estimated_duration"] == expected_duration, \
            f"Duration should be {expected_duration}, got {validated['estimated_duration']}"

        print(f"\n✓ Duration auto-calculation works: {expected_duration}s")
        print("\n✓ PASSED: Duration auto-calculation")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        traceback.print_exc()
        return False


def test_scene_validation_rejects_invalid():
    """Test that validation rejects invalid data."""
    print("\n" + "=" * 80)
    print("TEST: Scene Validation Rejects Invalid Data")
    print("=" * 80)

    try:
        client = LlamaClient()
        generator = PromptGenerator(llm_client=client)

        # Test case 1: Empty scenes list
        try:
            generator._validate_and_normalize_result({"scenes": []})
            print("❌ Should have raised error for empty scenes")
            return False
        except RuntimeError as e:
            if "did not return any scenes" in str(e):
                print("✓ Correctly rejects empty scenes list")
            else:
                raise

        # Test case 2: Non-list scenes
        try:
            generator._validate_and_normalize_result({"scenes": None})
            print("❌ Should have raised error for None scenes")
            return False
        except RuntimeError as e:
            if "did not return any scenes" in str(e):
                print("✓ Correctly rejects None scenes")
            else:
                raise

        # Test case 3: Scenes with missing fields
        try:
            invalid_scenes = [{"scene_number": 1}]  # Missing prompt_en and duration
            generator._validate_and_normalize_result({"scenes": invalid_scenes})
            print("❌ Should have raised error for invalid scenes")
            return False
        except RuntimeError as e:
            if "fewer than 2 valid scenes" in str(e):
                print("✓ Correctly filters scenes with missing fields")
            else:
                raise

        print("\n✓ PASSED: Scene validation properly rejects invalid data")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PROMPT GENERATOR END-TO-END TESTS")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("Duration Auto-Calculation", test_duration_auto_calculation()))
    results.append(("Scene Validation", test_scene_validation_rejects_invalid()))
    results.append(("Beats Summarization", test_beats_summarization()))
    results.append(("Battle Royale Scene Generation", test_generate_scenes_from_battle_royale()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
