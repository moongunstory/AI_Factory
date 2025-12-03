"""Output formatter for scene generation results."""
from typing import Dict, Any


class SceneFormatter:
    """Format scene generation results into user-friendly output."""

    @staticmethod
    def format_complete_output(result: Dict[str, Any]) -> str:
        """Format complete scene generation result into structured text.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Formatted string with all sections
        """
        output = []

        # Header
        output.append("=" * 80)
        output.append("스토리 비디오 장면 생성 결과")
        output.append("=" * 80)
        output.append("")

        # Story Idea
        output.append("[스토리 아이디어]")
        output.append(result.get('story_idea', 'N/A'))
        output.append("")
        output.append(f"테마: {result.get('theme', 'N/A')}")
        output.append("")

        # Story Summary
        output.append("=" * 80)
        output.append("[스토리 요약]")
        output.append("=" * 80)
        # Prefer Korean (_ko) field, fallback to non-suffixed field
        output.append(result.get('story_summary_ko', result.get('story_summary', 'N/A')))
        output.append("")

        # Story Beats
        output.append("=" * 80)
        output.append("[스토리 비트]")
        output.append("=" * 80)
        for beat in result.get('story_beats', []):
            beat_num = beat.get('beat_number', '?')
            # Prefer Korean (_ko) field, fallback to non-suffixed field
            description = beat.get('description_ko', beat.get('description', 'N/A'))
            function = beat.get('narrative_function', 'N/A')
            output.append(f"{beat_num}. {description}")
            output.append(f"   기능: {function}")
            output.append("")

        # Characters
        output.append("=" * 80)
        output.append("[캐릭터]")
        output.append("=" * 80)
        for char in result.get('characters', []):
            # Prefer Korean (_ko) fields, fallback to non-suffixed fields
            name = char.get('name_ko', char.get('name', 'N/A'))
            role = char.get('role', 'N/A')
            output.append(f"● {name} ({role})")
            output.append(f"  외형: {char.get('physical_ko', char.get('physical', 'N/A'))}")
            output.append(f"  의상: {char.get('costume_ko', char.get('costume', 'N/A'))}")
            output.append(f"  장비: {char.get('equipment_ko', char.get('equipment', 'N/A'))}")
            output.append(f"  성격적 특징: {char.get('personality_visual_ko', char.get('personality_visual', 'N/A'))}")
            output.append(f"  일관성 태그: {char.get('consistency_tags', 'N/A')}")
            output.append("")

        # Global Visual Style
        output.append("=" * 80)
        output.append("[글로벌 비주얼 스타일]")
        output.append("=" * 80)
        style = result.get('global_visual_style', {})
        output.append(f"테마: {style.get('theme_name', 'N/A')}")
        output.append(f"색상 팔레트: {style.get('color_palette', 'N/A')}")
        output.append(f"조명: {style.get('lighting', 'N/A')}")
        output.append(f"카메라: {style.get('camera', 'N/A')}")
        output.append(f"텍스처: {style.get('texture', 'N/A')}")
        output.append(f"분위기: {style.get('atmosphere', 'N/A')}")
        output.append(f"일관성 태그: {style.get('consistency_tags', 'N/A')}")
        output.append(f"품질 태그: {style.get('quality_tags', 'N/A')}")
        output.append("")

        # Scenes
        output.append("=" * 80)
        output.append("[장면]")
        output.append("=" * 80)
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        output.append(f"총 장면 수: {total_scenes}")
        output.append(f"총 지속시간: {total_duration}초")
        output.append("")

        for scene in result.get('scenes', []):
            scene_num = scene.get('scene_number', '?')
            duration = scene.get('duration', 0)
            description = scene.get('description', 'N/A')
            prompt_en = scene.get('prompt_en', 'N/A')
            prompt_ko = scene.get('prompt_ko', 'N/A')

            output.append("-" * 80)
            output.append(f"Scene {scene_num}")
            output.append("-" * 80)
            output.append(f"지속시간: {duration}초")
            output.append(f"설명: {description}")
            output.append("")
            output.append("프롬프트 (영어):")
            output.append(prompt_en)
            output.append("")
            output.append("프롬프트 (한국어):")
            output.append(prompt_ko)
            output.append("")

        # Footer
        output.append("=" * 80)
        output.append("생성 완료")
        output.append("=" * 80)

        return "\n".join(output)

    @staticmethod
    def format_markdown_output(result: Dict[str, Any]) -> str:
        """Format complete scene generation result into markdown.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Formatted markdown string
        """
        output = []

        # Header
        output.append("# 스토리 비디오 장면 생성 결과")
        output.append("")

        # Story Idea
        output.append("## 스토리 아이디어")
        output.append(result.get('story_idea', 'N/A'))
        output.append("")
        output.append(f"**테마:** {result.get('theme', 'N/A')}")
        output.append("")

        # Story Summary
        output.append("## 스토리 요약")
        # Prefer Korean (_ko) field, fallback to non-suffixed field
        output.append(result.get('story_summary_ko', result.get('story_summary', 'N/A')))
        output.append("")

        # Story Beats
        output.append("## 스토리 비트")
        for beat in result.get('story_beats', []):
            beat_num = beat.get('beat_number', '?')
            # Prefer Korean (_ko) field, fallback to non-suffixed field
            description = beat.get('description_ko', beat.get('description', 'N/A'))
            function = beat.get('narrative_function', 'N/A')
            output.append(f"{beat_num}. **{description}**")
            output.append(f"   - 기능: *{function}*")

        output.append("")

        # Characters
        output.append("## 캐릭터")
        for char in result.get('characters', []):
            # Prefer Korean (_ko) fields, fallback to non-suffixed fields
            name = char.get('name_ko', char.get('name', 'N/A'))
            role = char.get('role', 'N/A')
            output.append(f"### {name} ({role})")
            output.append(f"- **외형:** {char.get('physical_ko', char.get('physical', 'N/A'))}")
            output.append(f"- **의상:** {char.get('costume_ko', char.get('costume', 'N/A'))}")
            output.append(f"- **장비:** {char.get('equipment_ko', char.get('equipment', 'N/A'))}")
            output.append(f"- **성격적 특징:** {char.get('personality_visual_ko', char.get('personality_visual', 'N/A'))}")
            output.append(f"- **일관성 태그:** {char.get('consistency_tags', 'N/A')}")
            output.append("")

        # Global Visual Style
        output.append("## 글로벌 비주얼 스타일")
        style = result.get('global_visual_style', {})
        output.append(f"- **테마:** {style.get('theme_name', 'N/A')}")
        output.append(f"- **색상 팔레트:** {style.get('color_palette', 'N/A')}")
        output.append(f"- **조명:** {style.get('lighting', 'N/A')}")
        output.append(f"- **카메라:** {style.get('camera', 'N/A')}")
        output.append(f"- **텍스처:** {style.get('texture', 'N/A')}")
        output.append(f"- **분위기:** {style.get('atmosphere', 'N/A')}")
        output.append(f"- **일관성 태그:** {style.get('consistency_tags', 'N/A')}")
        output.append(f"- **품질 태그:** {style.get('quality_tags', 'N/A')}")
        output.append("")

        # Scenes
        output.append("## 장면")
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        output.append(f"**총 장면 수:** {total_scenes}  ")
        output.append(f"**총 지속시간:** {total_duration}초")
        output.append("")

        for scene in result.get('scenes', []):
            scene_num = scene.get('scene_number', '?')
            duration = scene.get('duration', 0)
            description = scene.get('description', 'N/A')
            prompt_en = scene.get('prompt_en', 'N/A')
            prompt_ko = scene.get('prompt_ko', 'N/A')

            output.append(f"### Scene {scene_num}")
            output.append(f"- **지속시간:** {duration}초")
            output.append(f"- **설명:** {description}")
            output.append("")
            output.append("**프롬프트 (영어):**")
            output.append(f"> {prompt_en}")
            output.append("")
            output.append("**프롬프트 (한국어):**")
            output.append(f"> {prompt_ko}")
            output.append("")

        output.append("---")
        output.append("*생성 완료*")

        return "\n".join(output)

    @staticmethod
    def format_summary(result: Dict[str, Any]) -> str:
        """Format a brief summary of the results.

        Args:
            result: Complete scene generation result dictionary

        Returns:
            Brief summary string
        """
        total_scenes = result.get('total_scenes', 0)
        total_duration = result.get('total_duration', 0)
        theme = result.get('theme', 'N/A')
        num_characters = len(result.get('characters', []))
        num_beats = len(result.get('story_beats', []))

        return f"""
장면 생성 완료!
────────────────────────────────────────
테마: {theme}
스토리 비트: {num_beats}개
캐릭터: {num_characters}명
생성된 장면: {total_scenes}개
총 지속시간: {total_duration}초
────────────────────────────────────────
"""
