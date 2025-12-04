# Prompt Generation Pipeline Architecture

## 개요

이 문서는 AI Short Factory의 프롬프트 생성 파이프라인 아키텍처를 설명합니다.
이 시스템은 로컬 8B LLM의 한계를 극복하기 위해 멀티 스텝 접근 방식을 사용합니다.

## 주요 설계 원칙

### 1. 자연스러운 장면 수 결정
- ❌ **과거**: "최소 15~30개의 장면을 생성하라"와 같이 장면 수를 강제
- ✅ **현재**: 스토리의 주요 사건 수에 따라 자연스럽게 결정
- 장면 수는 스토리 내용에 기반하며, 억지로 padding하거나 중요 사건을 생략하지 않음

### 2. 멀티 스텝 파이프라인
긴 스토리를 한 번에 처리하면 로컬 8B 모델이 JSON을 생성하다 중단되거나 깨진 출력을 생성합니다.
이를 해결하기 위해 작업을 분리했습니다:

```
Story → Beats → Scenes → Prompts
```

#### Step A: 스토리를 플롯 비트로 요약
- **함수**: `_summarize_story_to_beats(expanded_story: str) -> List[str]`
- **목적**: 긴 스토리를 8-20개의 핵심 사건(plot beats)으로 압축
- **출력**: 영어 문장 목록
- **예시**:
  ```
  1) 20 contestants gather at the wasteland arena
  2) The gates close and the game begins
  3) Sarah sprints to the factory district for cover
  ...
  ```

#### Step B: Beats를 Scene JSON으로 변환
- **함수**: `generate(expanded_story: str) -> Dict[str, Any]`
- **입력**: Step A에서 생성된 plot beats
- **처리**: 각 beat 또는 인접한 beat 그룹을 하나의 시각적 장면으로 변환
- **출력**: Stable Diffusion 프롬프트를 포함한 구조화된 JSON

## 파일 구조

```
src/
├── pipeline/
│   ├── prompt_generator.py          # 메인 프롬프트 생성 로직
│   └── tests/
│       └── test_prompt_generator_e2e.py  # 엔드-투-엔드 테스트
├── generators/
│   └── llm.py                       # LlamaClient (HTTP API 통신)
└── common/
    └── json_utils.py                # JSON 파싱 및 자동 복구
```

## PromptGenerator 클래스

### 주요 메서드

#### `generate(expanded_story: str, temperature: float = 0.7) -> Dict[str, Any]`
메인 진입점. 전체 멀티 스텝 파이프라인을 실행합니다.

**흐름**:
1. `_summarize_story_to_beats()` 호출하여 스토리를 beats로 요약
2. Beats를 기반으로 LLM에게 scene 생성 요청
3. `_validate_and_normalize_result()` 호출하여 결과 검증 및 정규화

**반환값**:
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "summary": "Brief scene summary",
      "description": "Detailed scene description",
      "prompt_en": "Stable Diffusion prompt",
      "duration": 3.5,
      "characters": [  // 선택적
        {
          "id": "sarah",
          "role": "protagonist",
          "description": "visual description"
        }
      ]
    }
  ],
  "total_scenes": 18,
  "estimated_duration": 64.0
}
```

#### `_summarize_story_to_beats(expanded_story: str) -> List[str]`
스토리를 8-20개의 플롯 비트로 요약합니다.

**특징**:
- 낮은 temperature (0.5) 사용으로 일관성 유지
- 번호/불릿 제거하여 깔끔한 텍스트 리스트 생성
- 최소 1개 beat 보장 (없으면 RuntimeError)

#### `_validate_and_normalize_result(result: Dict[str, Any]) -> Dict[str, Any]`
LLM 출력을 검증하고 정규화합니다.

**검증 로직**:
1. ✅ `scenes` 리스트가 존재하고 비어있지 않은지 확인
2. ✅ 각 scene에 필수 필드 검사: `scene_number`, `prompt_en`, `duration`
3. ✅ 누락된 필드가 있는 scene은 경고 로그 남기고 필터링
4. ✅ 최소 2개 이상의 유효한 scene 필요 (미달 시 RuntimeError)
5. ✅ `scene_number`로 정렬하여 안정적인 순서 보장
6. ✅ 모든 `duration`을 합산하여 `estimated_duration` 재계산

**왜 중요한가?**:
- LLM이 `estimated_duration`을 잘못 계산하거나 누락할 수 있음
- 일부 scene에 필드가 빠질 수 있음
- UI에 "undefined", "2s" 같은 잘못된 값이 전달되는 것을 방지

## SYSTEM_PROMPT 설계

### 장면 수 정책 (prompt_generator.py:23-26)
```
Scene design principles:
- Determine the number of scenes naturally from the major events in the plot beats.
- Each scene should capture one clear visual event (danger, discovery, battle, decision, dialogue, twist, etc.).
- Do not pad scenes or force a fixed count. Do not remove important events to hit a target number.
- For long battle-royale/action stories, it is common (but not mandatory) for 15-30+ scenes to appear naturally.
```

### Duration 가이드라인 (prompt_generator.py:28-31)
```
Duration guidelines:
- Typical scene duration: 2.0-4.0 seconds.
- Key turning points (game start, climactic fight, final victory, etc.): up to 4.0-6.0 seconds.
- Estimated total duration should roughly fall within 45-75 seconds, based on the sum of all scene durations (guideline, not a hard limit).
```

### JSON 출력 강제 (prompt_generator.py:34-79)
LLM이 설명 텍스트 없이 순수 JSON만 출력하도록 명확한 지시사항 제공:
- ✅ DO: `{"scenes":[...],"total_scenes":18,"estimated_duration":64.0}`
- ❌ DON'T: "Here is the result: {...}", "```json\n{...}\n```"

## JSON 복구 메커니즘

### 2-Layer Approach

#### Layer 1: LlamaClient.generate_json()
`src/generators/llm.py:187-254`

1. System prompt에 JSON 강제 지시사항 추가
2. LLM 출력 받기
3. `safe_parse()`로 자동 복구 시도

#### Layer 2: json_utils.safe_parse()
`src/common/json_utils.py:65-151`

**복구 단계**:
1. 표준 `json.loads()` 시도 (빠른 경로)
2. 실패 시 `extract_json_block()`으로 JSON 부분만 추출
   - Markdown 코드 블록 제거
   - 주변 설명 텍스트 제거
   - 첫 `{`부터 마지막 `}`까지 추출
3. `json_repair.repair_json()`으로 깨진 JSON 복구
   - Trailing comma 제거
   - 닫히지 않은 bracket 보완
   - 잘못된 escape 수정
4. 여전히 실패 시:
   - `strict=True`: RuntimeError 발생
   - `strict=False`: fallback 값 반환 (기본: `{}`)

## 프론트엔드 계약 (UI Integration)

### 필수 필드
프론트엔드는 다음 필드들에 의존하고 있으므로 **절대 제거하거나 타입 변경 불가**:

```typescript
interface ScenePromptResult {
  scenes: Scene[];           // 장면 배열
  total_scenes: number;      // 총 장면 수
  estimated_duration: number; // 예상 길이 (초)
}

interface Scene {
  scene_number: number;      // 장면 번호
  prompt_en: string;         // Stable Diffusion 프롬프트
  duration: number;          // 장면 길이 (초)

  // 선택적 필드 (있으면 사용, 없어도 무방)
  summary?: string;          // 짧은 요약
  description?: string;      // 상세 설명
  characters?: Character[];  // 캐릭터 정보
}

interface Character {
  id: string;                // 캐릭터 ID
  role: string;              // 역할
  description: string;       // 외형 묘사
}
```

### 편의 함수
`generate_prompts(expanded_story: str) -> Dict[str, Any]`
- 원-라인 호출을 위한 편의 함수
- 내부적으로 `PromptGenerator()` 인스턴스 생성 및 `generate()` 호출

## 에러 처리 전략

### 명확한 에러 vs 조용한 Fallback

**이전 문제**:
- `safe_parse()`가 조용히 빈 scene 생성 → UI에 undefined 표시
- 디버깅이 어려움

**현재 해결책**:
- PromptGenerator가 명확하게 에러 발생 (RuntimeError)
- 로그에 경고 및 에러 메시지 명확히 기록
- 문제를 숨기지 않고 드러내어 근본 원인 해결 유도

### 에러 시나리오

1. **LLM이 scenes를 반환하지 않음**
   ```python
   raise RuntimeError("LLM did not return any scenes")
   ```

2. **유효한 scene이 2개 미만**
   ```python
   raise RuntimeError("LLM returned fewer than 2 valid scenes")
   ```

3. **필수 필드 누락**
   ```python
   logger.warning("Skipping scene due to missing fields: scene_number, prompt_en")
   # Scene 필터링, 나머지 scene이 충분하면 계속 진행
   ```

4. **JSON 파싱 완전 실패** (strict=True 시)
   ```python
   raise RuntimeError("Failed to parse JSON from LLM output even after repair")
   ```

## 테스트

### 엔드-투-엔드 테스트
`src/pipeline/tests/test_prompt_generator_e2e.py`

**테스트 케이스**:
1. ✅ **배틀로얄 스토리 전체 파이프라인**
   - 장면 수가 자연스럽게 생성되는지 (15-30개 예상)
   - 모든 필수 필드가 존재하는지
   - undefined, "2s" 같은 잘못된 값이 없는지
   - total_scenes == len(scenes)
   - estimated_duration ≈ sum(scene.duration)

2. ✅ **Beats 요약 테스트**
   - 8-20개의 plot beats 생성 확인
   - 각 beat가 비어있지 않은지 확인

3. ✅ **Duration 자동 계산 테스트**
   - LLM이 잘못된 estimated_duration을 제공해도 재계산 확인

4. ✅ **Scene 검증 테스트**
   - 빈 scenes 리스트 거부
   - 필수 필드 누락 scene 필터링
   - 최소 2개 scene 미달 시 에러

### 테스트 실행
```bash
# pytest 사용 (설치되어 있는 경우)
pytest src/pipeline/tests/test_prompt_generator_e2e.py -v -s

# pytest 없이 실행
python run_prompt_test.py
```

**주의**: 테스트 실행 시 llama-server가 실행 중이어야 합니다.

## 캐릭터 일관성 (향후 확장)

### 현재 상태
- JSON 스키마에 `characters` 필드 포함 (선택적)
- LLM이 자동으로 캐릭터 정보 생성할 수 있음
- 프론트엔드는 아직 사용하지 않음

### 향후 계획
1. 캐릭터 카드 UI 개발
2. 각 캐릭터의 외형 일관성 유지
3. Scene 프롬프트에 캐릭터 설명 자동 주입
4. 사용자가 캐릭터 외형 직접 편집 가능

## 성능 최적화

### LLM 요청 최소화
- ❌ **과거**: 스토리 전체를 한 번에 처리 → JSON 깨짐
- ✅ **현재**: 2단계로 분리하여 각 요청의 복잡도 감소

### Token 사용량
- Beats 요약: ~1000 토큰 입력 → ~500 토큰 출력
- Scene 생성: ~500 토큰 입력 (beats) → ~2000 토큰 출력
- 총: ~3500 토큰 (기존 ~4000 토큰 대비 약간 증가하지만 안정성 크게 향상)

### 타임아웃
- Beats 요약: 기본 LLM timeout (120초)
- Scene 생성: max_tokens=2048 제한으로 무한 생성 방지

## 트러블슈팅

### 문제: 장면이 1개만 나옴
**원인**: LLM 출력이 중간에 잘려서 scenes 배열이 불완전함

**해결책**:
1. `_validate_and_normalize_result()`가 최소 2개 scene 강제
2. JSON repair로 닫히지 않은 bracket 복구 시도
3. 여전히 실패 시 명확한 에러 발생 → 로그 확인하여 근본 원인 파악

### 문제: UI에 "undefined" 표시
**원인**: Scene에 필수 필드가 누락됨

**해결책**:
1. `_validate_and_normalize_result()`가 필수 필드 체크
2. 누락된 scene은 필터링
3. 로그에 경고 메시지 출력

### 문제: duration이 "2s" (문자열)
**원인**: LLM이 숫자 대신 문자열 생성

**해결책**:
1. SYSTEM_PROMPT에 "duration": 3.5 (숫자) 형식 명시
2. 검증 단계에서 타입 체크
3. JSON repair가 자동 변환 시도

### 문제: 너무 긴 또는 짧은 총 시간
**원인**: LLM이 duration 가이드라인 무시

**해결책**:
1. SYSTEM_PROMPT에 2.0-4.0초 가이드라인 명시
2. 45-75초 범위 권장 (강제는 아님)
3. 검증 단계에서 경고 로그 출력

## 참고자료

### 관련 파일
- `src/pipeline/prompt_generator.py` - 메인 로직
- `src/generators/llm.py` - LLM 통신
- `src/common/json_utils.py` - JSON 파싱
- `run_prompt_test.py` - 테스트 실행 스크립트

### 의존성
- `requests` - HTTP 통신
- `json-repair` - JSON 자동 복구
- llama.cpp llama-server - 로컬 LLM 서버

### 설정
`src/common/config.py`에서 다음 설정 가능:
- `LLAMA_SERVER_URL` - llama-server 주소 (기본: http://127.0.0.1:8080)
- `LLM_TEMPERATURE` - Sampling temperature
- `LLM_MAX_TOKENS` - 최대 토큰 수
- `LLM_REQUEST_TIMEOUT` - 요청 타임아웃

---

**작성일**: 2025-12-04
**버전**: 1.0
**상태**: ✅ Production Ready
