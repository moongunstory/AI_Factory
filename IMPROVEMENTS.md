# ChatGPT Automation 개선 사항

## 문제 상황
스토리 입력 후 단편 영상 생성 버튼을 누르면 "워크플로우 실행 중 오류가 발생했습니다" 에러 발생

## 해결 방법
`chatgpt_automation.py`의 베스트 프랙티스를 참고하여 `backend/core/automation/chatgpt.py` 개선

## 주요 개선 사항

### 1. 세션 Persistence 강화
**Before:**
- 브라우저 프로파일만 사용 (`launch_persistent_context`)
- 매번 로그인 필요할 수 있음

**After:**
- Playwright의 `storage_state` API 추가 사용
- 로그인 후 세션 상태를 JSON 파일로 저장
- 다음 실행 시 자동으로 세션 복원
- 재로그인 불필요

```python
# 세션 상태 저장
await self.browser_context.storage_state(path=str(self.storage_state_path))

# 세션 상태 로드
if self.storage_state_path.exists():
    context_options["storage_state"] = str(self.storage_state_path)
```

### 2. 에러 처리 개선
**Before:**
- 일반적인 `Exception` 처리
- 불명확한 에러 메시지

**After:**
- `PlaywrightTimeoutError` 명시적 처리
- 각 단계별 명확한 에러 메시지
- 타임아웃 시에도 복구 시도

```python
try:
    await self.page.wait_for_selector(textarea_selector, timeout=5000)
except PlaywrightTimeoutError:
    # 명확한 에러 메시지와 복구 로직
    print("⚠️  ChatGPT 로그인이 필요합니다.")
```

### 3. 코드 구조 개선
**Before:**
- 하드코딩된 셀렉터
- 로그인 로직이 send_message 메서드에 섞여있음

**After:**
- 셀렉터를 static 메서드로 추상화
- `ensure_logged_in()` 메서드 분리
- Context manager 지원

```python
@staticmethod
def _prompt_textarea_selector() -> str:
    """Return a CSS selector for the chat input textarea."""
    return "#prompt-textarea"

async def __aenter__(self):
    await self.start_browser()
    return self
```

### 4. 사용자 경험 개선
**Before:**
```
Waiting for response generation...
```

**After:**
```
============================================================
=== 🎬 비디오 생성 워크플로우 시작 ===
============================================================

📖 Step 1/3: 이야기 확장 (Fable Forge)
[ChatGPTClient] 메시지 전송 중: 사이버펑크 세계에서...
[ChatGPTClient] 응답 대기 중...
[ChatGPTClient] 응답 생성 완료 감지
[ChatGPTClient] 응답 수신 완료 (길이: 1234 문자)
✅ Step 1 완료 (길이: 1234 문자)
```

## 참고 코드
- `/home/user/AI_Factory/chatgpt_automation.py` - 세션 persistence 패턴
- Playwright 공식 문서 - storage_state API

## 파일 변경
- `backend/core/automation/chatgpt.py` - 전면 개선

## 테스트 방법
1. 백엔드 서버 실행: `cd backend && uvicorn main:app --reload`
2. 프론트엔드 실행: `cd frontend && npm run dev`
3. 스토리 입력 후 "단편 영상 생성" 버튼 클릭
4. 첫 실행 시 브라우저 창에서 ChatGPT 로그인
5. 세션이 저장되어 다음 실행부터는 자동 로그인

## 기대 효과
- ✅ 세션 유지로 매번 로그인 불필요
- ✅ 더 나은 에러 메시지로 문제 해결 용이
- ✅ 타임아웃 및 네트워크 이슈에 더 강건
- ✅ UI 변경 시 셀렉터만 수정하면 되어 유지보수 용이
