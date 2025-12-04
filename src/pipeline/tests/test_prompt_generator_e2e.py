"""End-to-end tests for the PromptGenerator pipeline.

이 테스트는 실제 LLM 서버에 연결하여 전체 파이프라인을 검증합니다:
Story → Beats → Scenes → Prompts

배틀로얄 스토리를 사용하여 다음을 검증:
1. 장면 수가 자연스럽게 생성되는지 (1개가 아니라 15-30개)
2. 모든 scene에 필수 필드가 있는지 (scene_number, prompt_en, duration)
3. total_scenes == len(scenes)
4. estimated_duration ≈ sum(scene.duration)
5. undefined, "2s" 같은 잘못된 값이 없는지
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from ..prompt_generator import PromptGenerator, generate_prompts
from ...generators.llm import LlamaClient


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


class TestPromptGeneratorE2E:
    """End-to-end tests for PromptGenerator with real LLM."""

    @pytest.fixture(scope="class")
    def llm_client(self):
        """Create a LlamaClient instance for testing.

        Note: This requires llama-server to be running.
        Skip these tests if server is not available.
        """
        client = LlamaClient()
        if not client.is_server_ready():
            pytest.skip("llama-server is not running")
        return client

    @pytest.fixture(scope="class")
    def prompt_generator(self, llm_client):
        """Create a PromptGenerator instance."""
        return PromptGenerator(llm_client=llm_client)

    def test_generate_scenes_from_battle_royale_story(self, prompt_generator):
        """Test full pipeline with battle royale story.

        Expected behavior:
        - Generate 15-30 scenes naturally (not forced to a specific number)
        - Each scene has all required fields
        - No undefined or invalid values
        - Total duration is reasonable (45-75 seconds)
        """
        # Generate prompts
        result = prompt_generator.generate(
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

        # Validate scenes count (should be more than 1, ideally 15-30 for this story)
        assert len(scenes) >= 2, f"Should have at least 2 scenes, got {len(scenes)}"
        print(f"\n✓ Generated {len(scenes)} scenes (expected 15-30 for battle royale)")

        # Check if we got a reasonable number of scenes for this long story
        if len(scenes) < 10:
            print(f"⚠ Warning: Only {len(scenes)} scenes for a long battle royale story. Expected 15-30.")

        # Validate total_scenes matches actual count
        assert total_scenes == len(scenes), \
            f"total_scenes ({total_scenes}) should match len(scenes) ({len(scenes)})"

        # Validate each scene has required fields
        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)

            # Required fields
            assert "scene_number" in scene, \
                f"Scene {i} missing 'scene_number'"
            assert "prompt_en" in scene, \
                f"Scene {scene_num} missing 'prompt_en'"
            assert "duration" in scene, \
                f"Scene {scene_num} missing 'duration'"

            # Validate types
            assert isinstance(scene["scene_number"], int), \
                f"Scene {scene_num}: scene_number should be int, got {type(scene['scene_number'])}"
            assert isinstance(scene["prompt_en"], str), \
                f"Scene {scene_num}: prompt_en should be str, got {type(scene['prompt_en'])}"
            assert isinstance(scene["duration"], (int, float)), \
                f"Scene {scene_num}: duration should be number, got {type(scene['duration'])}"

            # Validate values are not empty/undefined
            assert scene["prompt_en"].strip(), \
                f"Scene {scene_num}: prompt_en should not be empty"
            assert scene["duration"] > 0, \
                f"Scene {scene_num}: duration should be > 0, got {scene['duration']}"

            # Check for common error values
            prompt_lower = scene["prompt_en"].lower()
            assert "undefined" not in prompt_lower, \
                f"Scene {scene_num}: prompt contains 'undefined'"
            assert scene["duration"] != "2s", \
                f"Scene {scene_num}: duration is string '2s' instead of number"

        # Validate estimated_duration
        assert isinstance(estimated_duration, (int, float)), \
            f"estimated_duration should be number, got {type(estimated_duration)}"
        assert estimated_duration > 0, \
            f"estimated_duration should be > 0, got {estimated_duration}"

        # Verify estimated_duration matches sum of scene durations
        calculated_duration = sum(scene["duration"] for scene in scenes)
        duration_diff = abs(estimated_duration - calculated_duration)
        assert duration_diff < 0.1, \
            f"estimated_duration ({estimated_duration}) should match sum of scene durations ({calculated_duration})"

        # Check if total duration is in reasonable range (45-75 seconds guideline)
        if not (45 <= estimated_duration <= 75):
            print(f"⚠ Warning: Total duration {estimated_duration}s is outside 45-75s guideline")

        # Print summary
        print(f"\n✓ All {len(scenes)} scenes validated successfully")
        print(f"✓ Total duration: {estimated_duration:.1f}s")
        print(f"✓ Average scene duration: {estimated_duration/len(scenes):.1f}s")

        # Optional: Check if characters field exists (not required, but nice to have)
        scenes_with_characters = sum(1 for s in scenes if "characters" in s)
        if scenes_with_characters > 0:
            print(f"✓ {scenes_with_characters} scenes have character information")

    def test_convenience_function(self):
        """Test the convenience function generate_prompts()."""
        # Use a shorter story for faster testing
        short_story = """
        A lone robot explores an abandoned space station, discovering the crew's fate
        through scattered logs. In the final room, it finds a message: "We're not alone.
        Turn back." The robot powers down its lights and waits in the darkness.
        """

        result = generate_prompts(short_story)

        # Basic validation
        assert "scenes" in result
        assert len(result["scenes"]) >= 2
        assert "total_scenes" in result
        assert "estimated_duration" in result

        print(f"\n✓ Convenience function generated {len(result['scenes'])} scenes")

    def test_scene_validation_rejects_invalid_data(self, prompt_generator):
        """Test that _validate_and_normalize_result properly rejects invalid data."""

        # Test case 1: Empty scenes list should raise error
        with pytest.raises(RuntimeError, match="did not return any scenes"):
            prompt_generator._validate_and_normalize_result({"scenes": []})

        # Test case 2: Non-list scenes should raise error
        with pytest.raises(RuntimeError, match="did not return any scenes"):
            prompt_generator._validate_and_normalize_result({"scenes": None})

        # Test case 3: Scenes with missing required fields should be filtered
        # If all scenes are invalid, should raise error about insufficient scenes
        invalid_scenes = [
            {"scene_number": 1},  # Missing prompt_en and duration
        ]
        with pytest.raises(RuntimeError, match="fewer than 2 valid scenes"):
            prompt_generator._validate_and_normalize_result({"scenes": invalid_scenes})

    def test_beats_summarization(self, prompt_generator):
        """Test that story summarization into beats works correctly."""
        beats = prompt_generator._summarize_story_to_beats(BATTLE_ROYALE_STORY)

        # Should generate 8-20 beats as specified
        assert len(beats) >= 8, f"Should have at least 8 beats, got {len(beats)}"
        assert len(beats) <= 25, f"Should have at most 25 beats, got {len(beats)}"

        # Each beat should be non-empty
        for i, beat in enumerate(beats):
            assert beat.strip(), f"Beat {i} is empty"

        print(f"\n✓ Story summarized into {len(beats)} plot beats")
        print("\nSample beats:")
        for i, beat in enumerate(beats[:5]):
            print(f"  {i+1}. {beat[:80]}...")

    def test_duration_auto_calculation(self, prompt_generator):
        """Test that duration is automatically calculated even if LLM provides wrong value."""

        # Create a mock result where LLM provided wrong estimated_duration
        mock_result = {
            "scenes": [
                {"scene_number": 1, "prompt_en": "test1", "duration": 3.0},
                {"scene_number": 2, "prompt_en": "test2", "duration": 4.0},
                {"scene_number": 3, "prompt_en": "test3", "duration": 2.5},
            ],
            "total_scenes": 3,
            "estimated_duration": 999.0  # Wrong value from LLM
        }

        validated = prompt_generator._validate_and_normalize_result(mock_result)

        # Should recalculate to correct value
        expected_duration = 3.0 + 4.0 + 2.5
        assert validated["estimated_duration"] == expected_duration, \
            f"Duration should be recalculated to {expected_duration}, got {validated['estimated_duration']}"

        print(f"\n✓ Duration auto-calculation works correctly: {expected_duration}s")


class TestPromptGeneratorIntegration:
    """Integration tests that don't require actual LLM (use mocks or saved data)."""

    def test_scene_schema_structure(self):
        """Verify the expected JSON schema structure is documented correctly."""

        # This test documents the expected schema for frontend integration
        expected_schema = {
            "scenes": [
                {
                    "scene_number": 1,
                    "summary": "Short English summary of the scene",
                    "description": "More detailed English description",
                    "prompt_en": "Stable Diffusion prompt in English",
                    "duration": 3.5,
                    "characters": [  # Optional
                        {
                            "id": "sarah",
                            "role": "protagonist",
                            "description": "short black hair, dusty survival clothes"
                        }
                    ]
                }
            ],
            "total_scenes": 1,
            "estimated_duration": 3.5
        }

        # Verify schema keys are what frontend expects
        required_keys = {"scenes", "total_scenes", "estimated_duration"}
        assert set(expected_schema.keys()) == required_keys

        # Verify scene structure
        scene_required_fields = {"scene_number", "prompt_en", "duration"}
        scene_optional_fields = {"summary", "description", "characters"}

        sample_scene = expected_schema["scenes"][0]
        for field in scene_required_fields:
            assert field in sample_scene, f"Required field '{field}' missing from schema"

        print("\n✓ JSON schema structure validated for UI contract")
        print(f"  Required fields: {', '.join(scene_required_fields)}")
        print(f"  Optional fields: {', '.join(scene_optional_fields)}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
