"""ChatGPT 3단계 워크플로우 실행 로직"""
from typing import Dict
from .chatgpt_client_selenium import ChatGPTClientSelenium


class ChatGPTWorkflow:
    """3단계 비디오 생성 워크플로우"""

    def __init__(self, use_system_profile: bool = True):
        self.client = ChatGPTClientSelenium(use_system_profile=use_system_profile)

    def run_three_step_workflow(
        self,
        initial_story: str,
        on_step_complete=None
    ) -> Dict[str, str]:
        """
        3단계 워크플로우 실행

        Args:
            initial_story: 초기 스토리 텍스트
            on_step_complete: 각 단계 완료 시 호출되는 콜백 (step_num, result)

        Returns:
            {"expanded_story": "...", "storyboard": "...", "prompts": "..."}
        """
        results = {}

        try:
            self.client.start_browser()

            # === Step 1: 이야기 확장 (Fable Forge) ===
            print("\n" + "="*60)
            print("📍 Step 1/3: 이야기 확장 (Fable Forge)")
            print("="*60)

            step1_prompt = self._build_step1_prompt(initial_story)

            results["expanded_story"] = self.client.send_message_and_get_response(
                step1_prompt,
                self.client.GPT_URLS["fable_forge"]
            )

            print(f"✅ Step 1 완료 (길이: {len(results['expanded_story'])}자)")

            if on_step_complete:
                on_step_complete(1, results["expanded_story"])

            # === Step 2: 스토리보드 작성 (Storyboard GPT) ===
            print("\n" + "="*60)
            print("📍 Step 2/3: 스토리보드 작성 (Storyboard GPT)")
            print("="*60)

            step2_prompt = self._build_step2_prompt(results["expanded_story"])

            results["storyboard"] = self.client.send_message_and_get_response(
                step2_prompt,
                self.client.GPT_URLS["storyboard_gpt"]
            )

            print(f"✅ Step 2 완료 (길이: {len(results['storyboard'])}자)")

            if on_step_complete:
                on_step_complete(2, results["storyboard"])

            # === Step 3: 프롬프트 생성 (Storyboard Maker) ===
            print("\n" + "="*60)
            print("📍 Step 3/3: 프롬프트 생성 (Storyboard Maker)")
            print("="*60)

            step3_prompt = self._build_step3_prompt(results["storyboard"])

            results["prompts"] = self.client.send_message_and_get_response(
                step3_prompt,
                self.client.GPT_URLS["storyboard_maker"]
            )

            print(f"✅ Step 3 완료 (길이: {len(results['prompts'])}자)")

            if on_step_complete:
                on_step_complete(3, results["prompts"])

            print("\n" + "="*60)
            print("🎉 전체 워크플로우 완료!")
            print("="*60)

            return results

        except Exception as e:
            print(f"\n❌ 워크플로우 실행 중 오류: {e}")
            raise

        finally:
            # 브라우저는 명시적으로 닫지 않음 (재사용을 위해)
            pass

    def revision_step(
        self,
        step_num: int,
        revision_text: str,
        previous_result: str
    ) -> str:
        """
        특정 단계 재시도

        Args:
            step_num: 단계 번호 (1, 2, 3)
            revision_text: 수정 요청 내용
            previous_result: 이전 결과 (컨텍스트)

        Returns:
            수정된 결과
        """
        # 단계별 GPT URL
        gpt_urls = {
            1: self.client.GPT_URLS["fable_forge"],
            2: self.client.GPT_URLS["storyboard_gpt"],
            3: self.client.GPT_URLS["storyboard_maker"],
        }

        gpt_url = gpt_urls.get(step_num)
        if not gpt_url:
            raise ValueError(f"잘못된 단계 번호: {step_num}")

        # 포맷 강제 문구
        format_enforcement = """

        [중요] 답변 양식:
        - 사담, 부연설명, 메타 코멘트 일체 제외
        - 요청된 내용만 순수하게 작성
        - 이전 답변의 스타일과 형식을 유지
        """

        print(f"\n📍 재시도 요청 (Step {step_num})")
        print(f"   수정 내용: {revision_text[:100]}...")

        revised_result = self.client.send_revision_request(
            revision_text,
            gpt_url,
            format_enforcement=format_enforcement
        )

        print(f"✅ 재시도 완료 (길이: {len(revised_result)}자)")

        return revised_result

    def close(self):
        """리소스 정리"""
        self.client.close()

    # === 프롬프트 빌더 메서드들 ===

    def _build_step1_prompt(self, initial_story: str) -> str:
        """Step 1: 이야기 확장 프롬프트"""
        return f"""다음 간단한 스토리를 기승전결이 명확한 완성도 높은 단편 이야기로 확장해주세요.

물론입니다 😊
확장할 간단한 스토리 원문을 먼저 보내주세요.

짧은 줄거리나 메모 형태여도 괜찮고,

등장인물
배경
핵심 사건
중 일부만 있어도 기승전결이 분명한 완성도 높은 단편 이야기로 자연스럽게 확장해 드릴게요.

{initial_story}

요구사항:
- 사담, 부연설명, 메타 코멘트 일체 제외
- 오직 순수한 스토리 텍스트만 작성
- 명확한 기승전결 구조 (도입 → 전개 → 클라이맥스 → 결말)
- 생동감 있는 묘사와 감정선
- 캐릭터의 동기와 갈등이 명확히 드러날 것
- 독자를 몰입시킬 수 있는 디테일과 긴장감

이걸 한 채팅에 다 넣어서 말해야지. 이야기랑 요구사항을 한 채팅에 넣고 바로 그걸 받아야 함."""

    def _build_step2_prompt(self, expanded_story: str) -> str:
        """Step 2: 스토리보드 작성 프롬프트"""
        return f"""다음 스토리를 영상 제작을 위한 상세 스토리보드로 변환해주세요.

{expanded_story}

요구사항:
- 사담, 설명, 메타 코멘트 일체 제외
- 각 씬(Scene)을 명확히 구분
- 씬마다 다음 요소 포함:
  * 씬 번호
  * 시간대/장소
  * 등장인물과 동작
  * 카메라 앵글/구도 제안
  * 핵심 감정/분위기
- 영상으로 시각화 가능한 구체적 묘사
- 씬 간 자연스러운 전환과 연결성
- 전체 러닝타임 1-3분 분량으로 최적화"""

    def _build_step3_prompt(self, storyboard: str) -> str:
        """Step 3: 프롬프트 생성 프롬프트"""
        return f"""다음 스토리보드를 바탕으로 AI 이미지 생성을 위한 최적화된 프롬프트를 제작해주세요.

{storyboard}

요구사항:
- 사담, 설명, 메타 코멘트 일체 제외
- 각 씬별로 독립적인 프롬프트 생성
- 프롬프트 구성 요소:
  * 주요 피사체와 동작 (명확하고 구체적으로)
  * 배경과 환경 묘사
  * 조명과 분위기 (lighting, mood)
  * 카메라 앵글과 구도
  * 아트 스타일/화풍 지정
  * 화질 관련 키워드 (high quality, detailed, cinematic 등)
- Stable Diffusion/Midjourney 최적화 형식
- 부정 프롬프트(Negative prompt) 별도 제공
- 영문 프롬프트로 작성
- 일관된 캐릭터/스타일 유지를 위한 키워드 포함"""


# === 사용 예제 ===
if __name__ == "__main__":
    workflow = ChatGPTWorkflow(use_system_profile=True)

    try:
        test_story = """
        어느 날, 한 소녀가 숲속에서 이상한 문을 발견한다.
        문을 열자 그곳에는 시간이 멈춘 마을이 있었다.
        """

        results = workflow.run_three_step_workflow(
            test_story,
            on_step_complete=lambda step, result: print(f"\n[콜백] Step {step} 완료\n")
        )

        print("\n" + "="*60)
        print("최종 결과:")
        print("="*60)
        print(f"1. 확장 스토리: {len(results['expanded_story'])}자")
        print(f"2. 스토리보드: {len(results['storyboard'])}자")
        print(f"3. 프롬프트: {len(results['prompts'])}자")

    finally:
        workflow.close()
