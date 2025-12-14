# ChatGPT 웹 자동화 가이드

## 📋 개요

이 프로젝트는 **Selenium + undetected-chromedriver**를 사용하여 ChatGPT 커스텀 GPT 3종을 자동으로 호출하는 파이프라인입니다.

**OpenAI 공식 API를 사용하지 않고**, 웹 브라우저 자동화 방식으로 동작합니다.

---

## 🎯 주요 기능

### 1. **3단계 비디오 생성 워크플로우**
- **Step 1**: 이야기 확장 (Fable Forge)
- **Step 2**: 스토리보드 작성 (Storyboard GPT)
- **Step 3**: 프롬프트 생성 (Storyboard Maker)

### 2. **안정적인 브라우저 자동화**
- **undetected-chromedriver** 사용으로 봇 감지 우회
- 기존 Chrome 프로필 사용 (로그인 세션 재사용)
- 다중 완료 감지 메커니즘:
  - Stop generating 버튼 상태 확인
  - 텍스트 길이 안정성 체크 (3회 연속)
  - JavaScript fallback으로 클릭 안정성 향상

### 3. **워크플로우 UI**
- **3개 노드** 플로우차트 스타일
- 각 노드마다 **진행/재시도** 버튼
- **원클릭 제작** 버튼으로 전체 워크플로우 자동 실행
- 진행 중 **초록색 외곽 + 애니메이션** 시각 효과
- **재시도 모달**로 수정 요청 입력

---

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
# Worker 의존성 설치
cd worker
pip install -r requirements.txt

# Frontend 의존성 설치
cd ../frontend
npm install
```

### 2. Chrome 프로필 설정

#### **옵션 A: 시스템 Chrome 프로필 사용 (권장)**

기존 Chrome 프로필을 사용하면 ChatGPT 로그인 세션을 재사용할 수 있습니다.

**Windows:**
```python
CHROME_USER_DATA_DIR = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
CHROME_PROFILE_NAME = "Default"  # 또는 "Profile 1" 등
```

**macOS:**
```python
CHROME_USER_DATA_DIR = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
CHROME_PROFILE_NAME = "Default"
```

**Linux:**
```python
CHROME_USER_DATA_DIR = Path.home() / ".config" / "google-chrome"
CHROME_PROFILE_NAME = "Default"
```

#### **옵션 B: 독립 자동화 프로필 사용**

```python
use_system_profile = False  # 독립 프로필 사용
```

독립 프로필 사용 시 첫 실행 때 ChatGPT 로그인이 필요합니다.

---

## 🚀 사용 방법

### 1. 워커 실행

```bash
cd worker
python main.py
```

워커가 작업 큐를 감시하며 대기합니다.

### 2. 백엔드 서버 실행

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

### 4. 워크플로우 실행

1. **스토리 입력**: 간단한 이야기 아이디어 입력
2. **원클릭 제작**: 버튼 클릭으로 3단계 자동 실행
3. **진행 상태 확인**: 각 노드의 진행 상태 실시간 확인
4. **재시도 (선택)**: 특정 단계가 마음에 안 들면 재시도 버튼 클릭

---

## 🔧 핵심 구현 패턴

### 1. **브라우저 자동화 클라이언트**

```python
from worker.automation.chatgpt_client_selenium import ChatGPTClientSelenium

client = ChatGPTClientSelenium(use_system_profile=True)
client.start_browser()

response = client.send_message_and_get_response(
    "테스트 메시지",
    client.GPT_URLS["fable_forge"]
)

print(response)
client.close()
```

### 2. **워크플로우 실행**

```python
from worker.automation.chatgpt_workflow import ChatGPTWorkflow

workflow = ChatGPTWorkflow(use_system_profile=True)

results = workflow.run_three_step_workflow(
    initial_story="어느 날, 한 소녀가 숲속에서 이상한 문을 발견한다.",
    on_step_complete=lambda step, result: print(f"Step {step} 완료!")
)

print(results["expanded_story"])
print(results["storyboard"])
print(results["prompts"])

workflow.close()
```

### 3. **재시도 기능**

```python
# 특정 단계 재시도
revised_result = workflow.revision_step(
    step_num=1,  # 1, 2, 3
    revision_text="더 극적인 전개로 바꿔주세요.",
    previous_result=results["expanded_story"]
)
```

---

## 📊 API 엔드포인트

### 작업 생성
```http
POST /api/jobs
Content-Type: application/json

{
  "story": "간단한 이야기 아이디어..."
}
```

### 작업 상태 조회
```http
GET /api/jobs/{job_id}
```

**응답 예시:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "current_step": 2,
  "step_1_result": "확장된 이야기 미리보기...",
  "step_2_result": "스토리보드 미리보기...",
  "result": null
}
```

---

## 🐛 문제 해결

### 1. "Chrome을 찾을 수 없습니다"

Chrome 실행 파일 경로를 확인하세요:
```python
# chatgpt_client_selenium.py
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Windows
# 또는
# /Applications/Google Chrome.app/Contents/MacOS/Google Chrome  # macOS
```

### 2. "로그인이 필요합니다"

- 시스템 Chrome 프로필 사용 시: 해당 프로필로 ChatGPT에 로그인되어 있는지 확인
- 독립 프로필 사용 시: 첫 실행 때 브라우저에서 수동으로 로그인

### 3. "응답을 추출할 수 없습니다"

ChatGPT UI가 변경되었을 수 있습니다. 셀렉터를 업데이트하세요:
```python
# chatgpt_client_selenium.py
# 현재 셀렉터: 'div[data-message-author-role="assistant"]'
# 필요 시 Chrome DevTools로 새 셀렉터 확인
```

### 4. "CDP 연결 실패" (기존 Playwright 사용 시)

Selenium 기반 클라이언트를 사용하면 이 문제가 해결됩니다:
```python
# processor.py에서 ChatGPTWorkflow 사용
from worker.automation.chatgpt_workflow import ChatGPTWorkflow
```

---

## 📚 참고 레포지토리

이 구현은 다음 오픈소스 프로젝트들의 패턴을 참고했습니다:

1. **SlymeGPT**: undetected-chromedriver, DOM 주입 방식
2. **unofficial-chatgpt-api**: Playwright persistent context, 폴링 기반 대기
3. **ChatGPT-unofficial-api-selenium**: 다중 완료 감지, 텍스트 안정성 체크
4. **chatgpt_selenium_automation**: Remote debugging, 간단한 selector

---

## 🔐 보안 고려사항

- `.gitignore`에 Chrome 프로필 경로 추가
- 환경변수로 민감한 정보 관리
- 공개 레포지토리에 세션 토큰 노출 주의

---

## 📝 라이센스

이 프로젝트는 학습 및 개인 용도로만 사용하세요.
ChatGPT 서비스 약관을 준수하고, 과도한 자동화는 피하세요.

---

## 🤝 기여

버그 리포트, 개선 제안 환영합니다!

