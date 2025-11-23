#!/usr/bin/env python3
"""
AI Shorts Factory - Gradio 웹 UI

사용자가 간단한 이야기를 입력하면:
  1. AI가 시나리오를 확장하여 보여줌
  2. 사용자는 시나리오를 수정하거나 컨펌
  3. 컨펌하면 씬별 프롬프트 자동 생성 (한국어/영어)
  4. 각 프롬프트는 개별 재생성 가능
"""

import gradio as gr
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.shorts_factory.core.pipeline import (
    generate_story_outline,
    generate_scene_plan,
    generate_prompts,
)
from src.shorts_factory.core.llm_client import chat_completion
from src.shorts_factory.core.schemas import (
    StoryOutline,
    ScenePlanPackage,
    PromptPackage,
    ShotPrompt,
)


# 전역 상태 저장
class AppState:
    def __init__(self):
        self.outline: StoryOutline | None = None
        self.scene_plan: ScenePlanPackage | None = None
        self.prompts: PromptPackage | None = None


state = AppState()


def generate_scenario_from_idea(
    story_idea: str,
    duration: int,
    genre: str,
    tone: str
) -> str:
    """
    간단한 이야기에서 시나리오 생성

    Args:
        story_idea: 사용자가 입력한 간단한 이야기
        duration: 목표 영상 길이 (초)
        genre: 장르
        tone: 톤

    Returns:
        생성된 시나리오 (마크다운 형식)
    """
    try:
        # 스토리 아웃라인 생성
        state.outline = generate_story_outline(
            logline=story_idea,
            target_duration_seconds=duration,
            tone=tone,
            genre=genre,
        )

        # 시나리오를 읽기 쉬운 마크다운으로 변환
        scenario_md = f"""# 시나리오: {state.outline.logline}

## 메타데이터
- **길이**: {state.outline.metadata.estimated_duration_seconds}초
- **장르**: {state.outline.metadata.genre}
- **톤**: {state.outline.metadata.tone}
- **플랫폼**: {', '.join(state.outline.metadata.target_platforms)}

## 스토리 비트

"""
        for i, beat in enumerate(state.outline.beats, 1):
            scenario_md += f"""### {i}. {beat.title}
**기능**: {beat.story_function}
**감정**: {beat.emotional_tone}
**내용**: {beat.summary}

"""

        return scenario_md

    except Exception as e:
        return f"❌ 에러 발생: {str(e)}\n\n서버가 실행 중인지 확인하세요."


def confirm_scenario_and_generate_prompts(
    scenario_text: str,
    duration: int,
    genre: str,
    tone: str
) -> tuple[str, str]:
    """
    시나리오를 컨펌하고 씬별 프롬프트 생성

    Returns:
        (씬 정보, 프롬프트 테이블 HTML)
    """
    try:
        if state.outline is None:
            return "❌ 먼저 시나리오를 생성하세요.", ""

        # 씬 플랜 생성
        state.scene_plan = generate_scene_plan(state.outline)

        # 프롬프트 생성
        state.prompts = generate_prompts(state.scene_plan)

        # 씬 정보 생성
        scene_info = f"""## 생성된 씬 정보

총 씬 개수: {len(state.scene_plan.scenes)}개
총 샷 개수: {sum(len(scene.shots) for scene in state.scene_plan.scenes)}개

"""

        for i, scene in enumerate(state.scene_plan.scenes, 1):
            scene_info += f"""### 씬 {i}: {scene.scene_purpose}
- **장소**: {scene.location_description}
- **감정**: {scene.emotional_tone}
- **샷 개수**: {len(scene.shots)}개
- **총 길이**: {sum(shot.duration_seconds for shot in scene.shots):.1f}초

"""

        # 프롬프트 테이블 생성
        prompts_html = generate_prompts_table()

        return scene_info, prompts_html

    except Exception as e:
        return f"❌ 에러 발생: {str(e)}", ""


def generate_prompts_table() -> str:
    """프롬프트 테이블 HTML 생성"""
    if state.prompts is None:
        return "<p>프롬프트가 없습니다.</p>"

    html = """
    <style>
        .prompt-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .prompt-table th {
            background-color: #4a5568;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        .prompt-table td {
            padding: 10px;
            border: 1px solid #e2e8f0;
            vertical-align: top;
        }
        .prompt-table tr:nth-child(even) {
            background-color: #f7fafc;
        }
        .prompt-box {
            background: #edf2f7;
            padding: 8px;
            border-radius: 4px;
            margin: 4px 0;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
        }
        .visual-attrs {
            font-size: 0.9em;
            color: #4a5568;
        }
        .regen-btn {
            background: #4299e1;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }
        .regen-btn:hover {
            background: #3182ce;
        }
    </style>

    <table class="prompt-table">
        <thead>
            <tr>
                <th style="width: 5%;">선택</th>
                <th style="width: 8%;">샷 ID</th>
                <th style="width: 35%;">영어 프롬프트</th>
                <th style="width: 35%;">한국어 프롬프트</th>
                <th style="width: 12%;">시각 속성</th>
                <th style="width: 5%;">길이</th>
            </tr>
        </thead>
        <tbody>
    """

    for i, shot in enumerate(state.prompts.shots):
        # 한국어 번역 (간단히 프롬프트를 한국어로 설명)
        korean_prompt = translate_prompt_to_korean(shot)

        # 시각 속성
        visual_attrs = shot.visual_attributes
        visual_str = f"""
명도: {visual_attrs.get('brightness', 'N/A')}
채도: {visual_attrs.get('saturation', 'N/A')}
대비: {visual_attrs.get('contrast', 'N/A')}
        """.strip()

        html += f"""
            <tr>
                <td style="text-align: center;">
                    <input type="checkbox" id="shot_{i}" name="shot_select" value="{shot.shot_id}">
                </td>
                <td><strong>{shot.shot_id}</strong></td>
                <td>
                    <div class="prompt-box">{shot.positive_prompt[:200]}...</div>
                    <details>
                        <summary>전체 보기</summary>
                        <div class="prompt-box">{shot.positive_prompt}</div>
                    </details>
                </td>
                <td>
                    <div class="prompt-box">{korean_prompt[:200]}...</div>
                    <details>
                        <summary>전체 보기</summary>
                        <div class="prompt-box">{korean_prompt}</div>
                    </details>
                </td>
                <td class="visual-attrs">{visual_str}</td>
                <td>{shot.duration_seconds:.1f}초</td>
            </tr>
        """

    html += """
        </tbody>
    </table>

    <div style="margin-top: 20px;">
        <button class="regen-btn" onclick="regenerateSelected()">선택한 프롬프트 재생성</button>
    </div>

    <script>
        function regenerateSelected() {
            const selected = Array.from(document.querySelectorAll('input[name="shot_select"]:checked'))
                .map(cb => cb.value);

            if (selected.length === 0) {
                alert('재생성할 프롬프트를 선택하세요.');
                return;
            }

            alert('선택한 프롬프트 재생성: ' + selected.join(', '));
            // TODO: Gradio 백엔드와 연동
        }
    </script>
    """

    return html


def translate_prompt_to_korean(shot: ShotPrompt) -> str:
    """
    영어 프롬프트를 한국어로 번역/설명
    (간단한 버전 - 실제로는 LLM으로 번역할 수 있음)
    """
    try:
        # LLM을 사용한 번역 (간단한 프롬프트)
        system_prompt = "You are a translator. Translate the following image generation prompt to Korean."
        user_prompt = f"""Translate this image generation prompt to Korean:

{shot.positive_prompt}

Korean translation:"""

        response = chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=500,
            base_url="http://localhost:8080/v1"
        )

        return response.strip()
    except:
        # 번역 실패 시 기본 설명
        return f"[샷 {shot.shot_id}] {shot.duration_seconds}초 분량의 영상"


def regenerate_selected_prompts(selected_shot_ids: List[str]) -> str:
    """선택한 프롬프트들을 재생성"""
    if state.scene_plan is None:
        return "❌ 먼저 씬을 생성하세요."

    try:
        # 선택한 샷들만 재생성
        for shot_id in selected_shot_ids:
            # TODO: 개별 샷 프롬프트 재생성 로직
            pass

        # 테이블 다시 생성
        return generate_prompts_table()
    except Exception as e:
        return f"❌ 에러 발생: {str(e)}"


# Gradio 인터페이스 구성
def create_ui():
    """Gradio UI 생성"""

    # Create the Gradio interface
    # Note: theme parameter removed for compatibility with different Gradio versions
    with gr.Blocks(title="AI Shorts Factory") as app:
        gr.Markdown("""
        # 🎬 AI Shorts Factory
        ### 간단한 아이디어에서 완성된 영상 시나리오까지

        1. 이야기를 입력하세요
        2. AI가 시나리오를 작성합니다
        3. 시나리오를 확인하고 수정하세요
        4. 컨펌하면 씬별 프롬프트가 생성됩니다
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 1️⃣ 이야기 입력")

                story_input = gr.Textbox(
                    label="이야기 아이디어",
                    placeholder="예: 요리사가 만든 음식이 살아난다",
                    lines=3,
                )

                with gr.Row():
                    duration_input = gr.Slider(
                        minimum=15,
                        maximum=300,
                        value=30,
                        step=5,
                        label="목표 길이 (초)",
                    )

                with gr.Row():
                    genre_input = gr.Textbox(
                        label="장르",
                        placeholder="예: fantasy, sci-fi, comedy",
                        value="fantasy",
                    )

                    tone_input = gr.Textbox(
                        label="톤",
                        placeholder="예: whimsical, epic, dark",
                        value="whimsical",
                    )

                generate_btn = gr.Button("✨ 시나리오 생성", variant="primary", size="lg")

        with gr.Row():
            gr.Markdown("## 2️⃣ 시나리오 확인 및 수정")

        scenario_output = gr.Markdown(
            label="생성된 시나리오",
            value="시나리오가 여기에 표시됩니다...",
        )

        with gr.Row():
            confirm_btn = gr.Button("✅ 시나리오 컨펌 및 프롬프트 생성", variant="primary", size="lg")

        with gr.Row():
            gr.Markdown("## 3️⃣ 생성된 프롬프트")

        scene_info_output = gr.Markdown(
            label="씬 정보",
            value="",
        )

        prompts_output = gr.HTML(
            label="프롬프트 목록",
            value="<p>프롬프트가 여기에 표시됩니다...</p>",
        )

        # 이벤트 핸들러
        generate_btn.click(
            fn=generate_scenario_from_idea,
            inputs=[story_input, duration_input, genre_input, tone_input],
            outputs=scenario_output,
        )

        confirm_btn.click(
            fn=confirm_scenario_and_generate_prompts,
            inputs=[scenario_output, duration_input, genre_input, tone_input],
            outputs=[scene_info_output, prompts_output],
        )

    return app


def main():
    """메인 실행"""
    import subprocess
    import time
    import sys
    import os

    print("=" * 80)
    print("🎬 AI SHORTS FACTORY - WEB UI")
    print("=" * 80)

    # LLM 서버 확인 (재시도 로직 포함)
    print("\n🔌 LLM 서버 연결 확인 중...")

    max_retries = 5
    retry_delay = 2
    server_ready = False

    for attempt in range(1, max_retries + 1):
        try:
            response = chat_completion(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'OK'",
                max_tokens=5,
                base_url="http://localhost:8080/v1"
            )
            print("✅ LLM 서버 연결 성공!")
            server_ready = True
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"⏳ 서버 연결 시도 {attempt}/{max_retries}... {retry_delay}초 후 재시도")
                time.sleep(retry_delay)
            else:
                print("❌ LLM 서버에 연결할 수 없습니다!")
                print(f"   에러: {e}")
                print("\n서버를 먼저 실행하세요:")
                print("   ./llama.cpp/build/bin/llama-server --model models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct --port 8080")

                # stdin이 tty인지 확인 (대화형 모드인지)
                if sys.stdin.isatty():
                    print("\n웹 UI를 계속 시작하시겠습니까? (서버는 나중에 시작할 수 있습니다) (Y/n): ", end="")
                    try:
                        answer = input().strip().lower()
                        if answer == 'n':
                            print("종료합니다.")
                            sys.exit(1)
                    except EOFError:
                        # EOFError 발생 시 기본값으로 진행
                        print("\n⚠️  입력을 받을 수 없습니다. 웹 UI를 시작합니다...")
                else:
                    # 비대화형 모드에서는 경고만 표시하고 계속 진행
                    print("\n⚠️  서버가 준비되지 않았지만 웹 UI를 시작합니다...")
                    print("    서버가 시작되면 새로고침하세요.")

    print("\n🌐 웹 UI 시작...")
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
