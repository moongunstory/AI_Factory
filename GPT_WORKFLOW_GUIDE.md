# GPT 웹 스크래핑 워크플로우 가이드

이 기능은 ChatGPT 커스텀 GPT들을 자동으로 사용하여 스토리를 확장하고, 스토리보드를 만들고, 프롬프트를 생성하는 3단계 워크플로우를 자동화합니다.

## 🎯 워크플로우 단계

1. **Fable Forge** - 이야기를 기승전결이 확실한 재밌는 이야기로 확장
2. **Storyboard GPT** - 확장된 이야기를 스토리보드로 변환
3. **Storyboard Maker** - 스토리보드를 이미지 생성 프롬프트로 변환

## 🔧 설치 방법

### 1. 백엔드 설정

```bash
cd backend

# Python 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (Chrome)
playwright install chromium
```

### 2. 프론트엔드 설정

```bash
cd frontend

# 패키지 설치
npm install
```

## 🚀 실행 방법

### 1. 백엔드 서버 시작

```bash
cd backend
python main.py
```

백엔드는 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 서버 시작

```bash
cd frontend
npm run dev
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## 💡 사용 방법

### 첫 실행 시 (로그인)

1. 프론트엔드에서 스토리를 입력하고 "단편 영상 생성" 버튼을 클릭
2. 자동으로 Chrome 브라우저 창이 열립니다
3. **ChatGPT에 로그인하세요** (GPT Plus 계정)
4. 로그인 후 브라우저 창을 그대로 두고 대기
5. 워크플로우가 자동으로 진행됩니다

### 이후 실행 (세션 유지)

- **브라우저를 닫지 마세요!** 브라우저를 닫으면 다음에 다시 열릴 때도 로그인 세션이 유지됩니다.
- `chrome_profile` 폴더에 세션 정보가 저장되어 **한 번만 로그인하면 됩니다**.
- 다음부터는 스토리만 입력하고 버튼을 클릭하면 자동으로 워크플로우가 실행됩니다.

## 🎬 워크플로우 진행 과정

1. 사용자가 스토리 입력 후 "단편 영상 생성" 버튼 클릭
2. 백엔드가 Playwright로 Chrome 브라우저 제어
3. Fable Forge GPT 접속 → 이야기 확장 요청 → 응답 수신
4. Storyboard GPT 접속 → 스토리보드 작성 요청 → 응답 수신
5. Storyboard Maker 접속 → 프롬프트 생성 요청 → 응답 수신
6. 모든 결과를 프론트엔드에 표시

## 📊 API 엔드포인트

### POST `/api/automation/generate-video-workflow`

**요청 바디:**
```json
{
  "story": "여기에 초기 스토리를 입력하세요"
}
```

**응답:**
```json
{
  "expanded_story": "확장된 이야기...",
  "storyboard": "스토리보드...",
  "prompts": "생성 프롬프트..."
}
```

## ⚙️ 기술 스택

- **백엔드**: FastAPI, Playwright
- **프론트엔드**: Next.js, React, Mantine UI
- **브라우저 자동화**: Playwright (Chrome)

## 🔒 보안 주의사항

- `chrome_profile` 폴더에는 로그인 세션 정보가 저장됩니다
- 이 폴더를 Git에 커밋하지 마세요 (`.gitignore`에 추가 권장)
- 개인 계정 정보가 포함되므로 공유하지 마세요

## 🐛 문제 해결

### "Input area not found" 에러
- ChatGPT에 로그인되어 있지 않습니다
- 브라우저 창이 열리면 수동으로 로그인하세요

### 브라우저가 열리지 않음
- Playwright 설치 확인: `playwright install chromium`
- Chrome이 설치되어 있는지 확인

### 워크플로우가 중간에 멈춤
- ChatGPT 응답이 너무 길 경우 대기 시간이 길어질 수 있습니다
- 브라우저 창을 확인하여 에러가 있는지 체크하세요

### 매번 로그인해야 함
- `chrome_profile` 폴더가 삭제되었거나 권한 문제일 수 있습니다
- 폴더 권한 확인: `chmod 755 chrome_profile`

## 📝 참고사항

- GPT Plus 계정이 필요합니다 (무료 계정은 커스텀 GPT 사용 불가)
- 워크플로우 실행 시간은 각 GPT의 응답 속도에 따라 2-5분 정도 소요될 수 있습니다
- 동시에 여러 요청을 보내면 충돌할 수 있으니 하나씩 순차적으로 실행하세요
