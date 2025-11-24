"""Next episode suggestion module using AI."""
from typing import Dict, List, Any, Optional
from ..generators.llm import LlamaClient
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class NextEpisodeSuggester:
    """AI-powered next episode suggestion generator."""

    SYSTEM_PROMPT = """You are an expert story consultant specializing in episodic short-form content.

Your task is to analyze the current state of a series and suggest compelling next episode ideas.

Consider:
- Previous episode's ending and unresolved conflicts
- Character arcs and development opportunities
- World-building and lore expansion
- Emotional beats and pacing
- Viewer engagement and hooks

Generate 4-5 diverse episode ideas that follow different narrative approaches:
1. Conflict-focused (갈등 중심)
2. Character growth (캐릭터 성장)
3. Event-driven (사건 중심)
4. Relationship/Emotion (관계/감정)
5. Dark route / Alternative path (다크 루트)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL JSON OUTPUT REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. OUTPUT ONLY PURE JSON - NO OTHER TEXT
2. NO explanations, NO comments, NO markdown
3. NO text before or after the JSON object
4. START with { and END with }
5. MUST be valid, parseable JSON

Required JSON Schema:
{
  "suggestions": [
    {
      "type": "conflict",
      "title": "제목 (한국어)",
      "idea": "아이디어 설명 (한국어, 2-3문장)",
      "focus": "이 에피소드의 초점 (한국어)"
    }
  ]
}

REMEMBER: Output ONLY the JSON object. Nothing else."""

    def __init__(self, llm_client: Optional[LlamaClient] = None):
        """Initialize suggester.

        Args:
            llm_client: Optional LlamaClient instance
        """
        self.llm = llm_client or LlamaClient()
        logger.info("NextEpisodeSuggester initialized")

    def suggest_next_episodes(
        self,
        universe_summary: str,
        previous_episode_summary: str,
        character_summaries: List[str],
        timeline_summary: str,
        genre: str,
        temperature: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Generate next episode suggestions.

        Args:
            universe_summary: Universe background and rules
            previous_episode_summary: Summary of the last episode
            character_summaries: List of character summaries
            timeline_summary: Timeline events summary
            genre: Story genre
            temperature: Sampling temperature

        Returns:
            List of episode suggestions
        """
        logger.info("Generating next episode suggestions...")

        # Build context
        characters_text = "\n".join(f"- {char}" for char in character_summaries)

        user_prompt = f"""세계관:
{universe_summary}

장르: {genre}

주요 캐릭터:
{characters_text}

타임라인 요약:
{timeline_summary}

직전 에피소드 (최신화):
{previous_episode_summary}

위 정보를 바탕으로, 다음 에피소드 아이디어 4-5개를 생성하세요.
각 아이디어는 다른 서사 접근법을 사용해야 합니다:

1. 갈등 중심 전개
2. 캐릭터 성장 중심
3. 사건 중심
4. 관계/감정 중심
5. 다크 루트 / 대체 전개

각 아이디어는 흥미롭고, 이전 에피소드와 자연스럽게 연결되며, 시청자를 끌어당길 수 있어야 합니다."""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=temperature,
                max_tokens=2048
            )

            suggestions = result.get('suggestions', [])
            logger.info(f"Generated {len(suggestions)} episode suggestions")

            return suggestions

        except Exception as e:
            logger.error(f"Failed to generate episode suggestions: {e}")
            raise

    def refine_suggestion(
        self,
        original_idea: str,
        user_feedback: str,
        universe_context: str,
        temperature: float = 0.7
    ) -> str:
        """Refine a suggestion based on user feedback.

        Args:
            original_idea: Original episode idea
            user_feedback: User's feedback or modification request
            universe_context: Universe context
            temperature: Sampling temperature

        Returns:
            Refined episode idea
        """
        logger.info("Refining episode suggestion...")

        refine_system = """You are a story consultant helping refine episode ideas.

Take the original idea and user feedback, then create an improved version that incorporates the feedback while maintaining narrative coherence.

Output ONLY the refined episode idea in Korean (2-3 sentences). No JSON, no explanations."""

        user_prompt = f"""원본 아이디어:
{original_idea}

사용자 피드백:
{user_feedback}

세계관 컨텍스트:
{universe_context}

피드백을 반영하여 아이디어를 개선하세요."""

        try:
            refined = self.llm.generate(
                prompt=user_prompt,
                system_prompt=refine_system,
                temperature=temperature,
                max_tokens=512
            )

            return refined.strip()

        except Exception as e:
            logger.error(f"Failed to refine suggestion: {e}")
            raise

    def merge_suggestions(
        self,
        suggestion_ids: List[int],
        suggestions: List[Dict[str, Any]],
        universe_context: str,
        temperature: float = 0.7
    ) -> str:
        """Merge multiple suggestions into one coherent idea.

        Args:
            suggestion_ids: List of suggestion indices to merge
            suggestions: Full list of suggestions
            universe_context: Universe context
            temperature: Sampling temperature

        Returns:
            Merged episode idea
        """
        logger.info(f"Merging suggestions: {suggestion_ids}")

        selected = [suggestions[i] for i in suggestion_ids if i < len(suggestions)]

        if not selected:
            raise ValueError("No valid suggestions selected")

        merge_system = """You are a story consultant helping merge multiple episode ideas.

Take the selected ideas and combine them into a single coherent episode that incorporates the best elements of each.

Output ONLY the merged episode idea in Korean (2-3 sentences). No JSON, no explanations."""

        ideas_text = "\n\n".join(
            f"아이디어 {i+1} ({s['type']}):\n{s['idea']}"
            for i, s in enumerate(selected)
        )

        user_prompt = f"""선택된 아이디어들:

{ideas_text}

세계관 컨텍스트:
{universe_context}

이 아이디어들을 하나의 통합된 에피소드 아이디어로 합쳐주세요."""

        try:
            merged = self.llm.generate(
                prompt=user_prompt,
                system_prompt=merge_system,
                temperature=temperature,
                max_tokens=512
            )

            return merged.strip()

        except Exception as e:
            logger.error(f"Failed to merge suggestions: {e}")
            raise


def suggest_next_episodes(
    universe_summary: str,
    previous_episode_summary: str,
    character_summaries: List[str],
    timeline_summary: str,
    genre: str
) -> List[Dict[str, Any]]:
    """Convenience function for generating next episode suggestions.

    Args:
        universe_summary: Universe background
        previous_episode_summary: Last episode summary
        character_summaries: Character summaries
        timeline_summary: Timeline summary
        genre: Genre

    Returns:
        List of suggestions
    """
    suggester = NextEpisodeSuggester()
    return suggester.suggest_next_episodes(
        universe_summary,
        previous_episode_summary,
        character_summaries,
        timeline_summary,
        genre
    )
