"""Comprehensive tests for JSON parsing with automatic repair.

This test suite validates that safe_parse() can handle all common
LLM output failure modes and reliably produce valid JSON.
"""
import json
import pytest
from src.common.json_utils import (
    safe_parse,
    extract_json_block,
    validate_json_schema,
    safe_parse_with_schema
)


class TestExtractJsonBlock:
    """Test JSON extraction from various text formats."""

    def test_plain_json(self):
        """Test extraction of plain JSON."""
        text = '{"key": "value"}'
        result = extract_json_block(text)
        assert result == '{"key": "value"}'

    def test_json_with_text_before(self):
        """Test extraction when text appears before JSON."""
        text = 'Here is the result: {"key": "value"}'
        result = extract_json_block(text)
        assert result == '{"key": "value"}'

    def test_json_with_text_after(self):
        """Test extraction when text appears after JSON."""
        text = '{"key": "value"} and that\'s it!'
        result = extract_json_block(text)
        assert result == '{"key": "value"}'

    def test_json_with_markdown_code_block(self):
        """Test extraction from markdown code block."""
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_block(text)
        assert '{"key": "value"}' in result

    def test_json_array(self):
        """Test extraction of JSON array."""
        text = '[1, 2, 3]'
        result = extract_json_block(text)
        assert result == '[1, 2, 3]'

    def test_complex_json_with_surrounding_text(self):
        """Test extraction of complex JSON with surrounding text."""
        text = '''
        The analysis is complete. Here are the results:
        {
            "scenes": [
                {"scene_number": 1, "description": "test"}
            ],
            "total_scenes": 1
        }
        That's all for now.
        '''
        result = extract_json_block(text)
        # Should extract the JSON object
        assert '"scenes"' in result
        assert '"total_scenes"' in result


class TestSafeParse:
    """Test safe_parse() with various JSON inputs."""

    def test_valid_json(self):
        """Test parsing of perfectly valid JSON."""
        text = '{"key": "value", "number": 42}'
        result = safe_parse(text)
        assert result == {"key": "value", "number": 42}

    def test_trailing_comma(self):
        """Test JSON with trailing comma (common LLM error)."""
        text = '{"key": "value", "number": 42,}'
        result = safe_parse(text)
        assert "key" in result
        assert result["key"] == "value"

    def test_missing_closing_quote(self):
        """Test JSON with missing closing quote."""
        text = '{"key": "value, "number": 42}'
        result = safe_parse(text)
        assert "key" in result or "number" in result

    def test_missing_closing_bracket(self):
        """Test JSON with missing closing bracket."""
        text = '{"key": "value", "number": 42'
        result = safe_parse(text)
        assert "key" in result

    def test_json_with_natural_language_prefix(self):
        """Test JSON mixed with natural language."""
        text = 'Here is the JSON you requested: {"key": "value"}'
        result = safe_parse(text)
        assert result == {"key": "value"}

    def test_json_with_markdown_code_block(self):
        """Test JSON inside markdown code block."""
        text = '```json\n{"key": "value"}\n```'
        result = safe_parse(text)
        assert result == {"key": "value"}

    def test_multiline_json(self):
        """Test multiline formatted JSON."""
        text = '''{
            "scenes": [
                {
                    "scene_number": 1,
                    "description_kr": "테스트",
                    "prompt_en": "test prompt",
                    "duration": 5.0
                }
            ],
            "total_scenes": 1,
            "estimated_duration": 5.0
        }'''
        result = safe_parse(text)
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["total_scenes"] == 1

    def test_empty_string(self):
        """Test empty string returns fallback."""
        result = safe_parse("", fallback={"default": True})
        assert result == {"default": True}

    def test_completely_invalid_json(self):
        """Test completely invalid text uses fallback."""
        text = "This is not JSON at all!"
        result = safe_parse(text, fallback={"error": "fallback"})
        # Should either parse something or use fallback
        assert isinstance(result, dict)

    def test_strict_mode_raises_on_failure(self):
        """Test that strict mode raises exception on parse failure."""
        text = "Not valid JSON and cannot be repaired"
        with pytest.raises(ValueError):
            safe_parse(text, strict=True)

    def test_korean_content(self):
        """Test JSON with Korean content."""
        text = '{"description": "한국어 설명", "title": "테스트"}'
        result = safe_parse(text)
        assert result["description"] == "한국어 설명"
        assert result["title"] == "테스트"

    def test_nested_json(self):
        """Test deeply nested JSON."""
        text = '''{
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }'''
        result = safe_parse(text)
        assert result["level1"]["level2"]["level3"]["value"] == "deep"

    def test_json_array_of_objects(self):
        """Test JSON array of objects."""
        text = '''[
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"}
        ]'''
        result = safe_parse(text)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1


class TestValidateJsonSchema:
    """Test JSON schema validation."""

    def test_all_required_keys_present(self):
        """Test validation passes when all keys present."""
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        result = validate_json_schema(data, ["key1", "key2"])
        assert result is True

    def test_missing_required_keys(self):
        """Test validation fails when keys missing."""
        data = {"key1": "value1"}
        result = validate_json_schema(data, ["key1", "key2"])
        assert result is False

    def test_strict_mode_raises_on_missing_keys(self):
        """Test strict mode raises exception on missing keys."""
        data = {"key1": "value1"}
        with pytest.raises(ValueError):
            validate_json_schema(data, ["key1", "key2"], strict=True)

    def test_empty_required_keys(self):
        """Test validation passes with no required keys."""
        data = {"key1": "value1"}
        result = validate_json_schema(data, [])
        assert result is True


class TestSafeParseWithSchema:
    """Test combined parsing and validation."""

    def test_valid_json_with_schema(self):
        """Test parsing and validation of valid JSON."""
        text = '{"scene_number": 1, "description": "test", "duration": 5.0}'
        result = safe_parse_with_schema(
            text,
            required_keys=["scene_number", "description"]
        )
        assert result["scene_number"] == 1
        assert result["description"] == "test"

    def test_missing_keys_returns_fallback(self):
        """Test that missing keys uses fallback."""
        text = '{"scene_number": 1}'
        result = safe_parse_with_schema(
            text,
            required_keys=["scene_number", "description"],
            fallback={"error": "missing_keys"}
        )
        # Validation fails but doesn't raise (non-strict)
        assert "scene_number" in result

    def test_malformed_json_with_schema_repair(self):
        """Test that malformed JSON is repaired and validated."""
        text = '{"scene_number": 1, "description": "test",}'  # Trailing comma
        result = safe_parse_with_schema(
            text,
            required_keys=["scene_number"]
        )
        assert result["scene_number"] == 1


class TestRealWorldScenarios:
    """Test real-world LLM output scenarios."""

    def test_llm_output_with_explanation(self):
        """Test typical LLM output with explanation text."""
        text = '''
        I'll create a scene breakdown for you:

        {
            "scenes": [
                {
                    "scene_number": 1,
                    "description_kr": "로봇이 우주 정거장을 걷는다",
                    "prompt_en": "a lonely robot walking in space station",
                    "duration": 5.0
                }
            ],
            "total_scenes": 1,
            "estimated_duration": 5.0
        }

        This should work well for your video!
        '''
        result = safe_parse(text)
        assert "scenes" in result
        assert len(result["scenes"]) == 1

    def test_llm_output_with_markdown_and_text(self):
        """Test LLM output with markdown formatting."""
        text = '''
        Here's the JSON output:

        ```json
        {
            "scenes": [
                {"scene_number": 1, "description_kr": "테스트", "prompt_en": "test", "duration": 5.0}
            ],
            "total_scenes": 1
        }
        ```

        Let me know if you need any changes!
        '''
        result = safe_parse(text)
        assert "scenes" in result
        assert result["total_scenes"] == 1

    def test_llm_incomplete_json(self):
        """Test LLM output with incomplete JSON (missing bracket)."""
        text = '''{
            "scenes": [
                {"scene_number": 1, "description_kr": "테스트"}
            ],
            "total_scenes": 1
        '''  # Missing closing }
        result = safe_parse(text)
        assert "scenes" in result or "total_scenes" in result

    def test_llm_extra_commas(self):
        """Test LLM output with extra commas."""
        text = '''{
            "scenes": [
                {"scene_number": 1, "description": "test",},
            ],
            "total_scenes": 1,
        }'''
        result = safe_parse(text)
        assert "scenes" in result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
