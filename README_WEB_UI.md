# AI Shorts Factory - 웹 UI 사용 가이드

## 🎬 개요

AI Shorts Factory는 간단한 이야기 아이디어를 입력하면 AI가 자동으로 완전한 시나리오와 씬별 프롬프트를 생성하는 웹 애플리케이션입니다.

## 🚀 빠른 시작

### 1단계: LLM 서버 실행

먼저 llama-server를 실행하세요:

```bash
./llama.cpp/build/bin/llama-server \
  --model models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct \
  --port 8080
```

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:
```
main: model loaded
main: server is listening on http://127.0.0.1:8080
```

### 2단계: 웹 UI 실행

새 터미널을 열고 웹 UI를 실행하세요:

```bash
# 가상환경 활성화
source .venv/bin/activate

# 웹 UI 실행
python app.py
```

브라우저가 자동으로 열리며 `http://localhost:7860`에서 웹 UI에 접속할 수 있습니다.

## 📖 사용 방법

### 1️⃣ 이야기 입력

1. **이야기 아이디어** 입력창에 간단한 스토리를 입력하세요
   - 예: "요리사가 만든 음식이 살아난다"
   - 예: "외계인이 지구에 도착한다"
   - 예: "마법사가 시간을 되돌린다"

2. **목표 길이** 슬라이더로 영상 길이 조절 (15~300초)

3. **장르** 입력:
   - fantasy, sci-fi, horror, comedy, romance, action 등

4. **톤** 입력:
   - whimsical, epic, dark, mysterious, comedic, dramatic 등

5. **"✨ 시나리오 생성"** 버튼 클릭

### 2️⃣ 시나리오 확인 및 수정

생성된 시나리오가 표시됩니다:
- 메타데이터 (길이, 장르, 톤)
- 스토리 비트 (각 장면의 제목, 기능, 감정, 내용)

시나리오를 검토하고 만족하면 다음 단계로 진행합니다.

### 3️⃣ 프롬프트 생성

**"✅ 시나리오 컨펌 및 프롬프트 생성"** 버튼을 클릭하면:

1. **씬 정보** 표시:
   - 총 씬 개수
   - 총 샷 개수
   - 각 씬의 세부 정보

2. **프롬프트 테이블** 생성:
   - 각 샷의 영어/한국어 프롬프트
   - 시각 속성 (명도, 채도, 대비)
   - 샷 길이

### 4️⃣ 프롬프트 재생성 (선택사항)

- 각 프롬프트 옆의 체크박스를 선택
- **"선택한 프롬프트 재생성"** 버튼 클릭
- 선택한 프롬프트들이 새로 생성됩니다

## 🎨 생성되는 내용

### 스토리 아웃라인
- 5~20개의 스토리 비트
- 각 비트는 서사 기능 (hook, setup, rising_action, climax, resolution) 포함
- 감정 톤 및 시각적 설명

### 씬 플랜
- 3~12개의 씬
- 각 씬은 1개 이상의 샷으로 구성
- 총 8~40개의 샷

### 프롬프트
- 각 샷마다:
  - **영어 프롬프트**: 이미지 생성용 (Stable Diffusion, DALL-E 등)
  - **한국어 프롬프트**: 사용자가 이해하기 쉽도록 번역
  - **시각 속성**:
    - 명도 (brightness): very_dark, dark, medium, bright, very_bright
    - 채도 (saturation): desaturated, low, medium, high, vivid
    - 대비 (contrast): low, medium, high, dramatic
    - 아트 스타일, 색보정, 조명 방향
  - **생성 파라미터**: 이미지 크기, 샘플러, CFG scale 등

## 📁 출력 파일

생성된 결과는 `data/outputs/` 디렉토리에 JSON 형식으로 저장됩니다:
- 스토리 아웃라인
- 씬 플랜
- 프롬프트 패키지
- 이미지 생성 파라미터

## 🔧 설정

`config/config.py`에서 다음 설정을 변경할 수 있습니다:

- `LOCAL_LLM_BASE_URL`: LLM 서버 주소 (기본: http://localhost:8080/v1)
- `DEFAULT_TEMPERATURE`: 생성 온도 (기본: 0.7)
- `DEFAULT_MAX_TOKENS`: 최대 토큰 수 (기본: 4096)

환경 변수로도 설정 가능:
```bash
export LOCAL_LLM_BASE_URL="http://localhost:8080/v1"
export LLM_MODEL_NAME="local-llama-3.1-8b-instruct"
```

## 🐛 문제 해결

### 서버 연결 실패
```
❌ LLM 서버에 연결할 수 없습니다!
```

**해결 방법**:
1. llama-server가 실행 중인지 확인
2. 포트 8080이 열려 있는지 확인
3. `config/config.py`에서 `LOCAL_LLM_BASE_URL` 확인

### Import 에러
```
ImportError: cannot import name 'HfFolder' from 'huggingface_hub'
```

**해결 방법**:
```bash
pip install "huggingface_hub<1.0.0" --upgrade
```

### Pydantic 에러
```
PydanticSchemaGenerationError: Unable to generate pydantic-core schema
```

**해결 방법**: 이미 수정되었습니다 (`any` → `Any`)

## 📝 예제

### 판타지 스토리
```
이야기: 기사가 용을 물리치고 공주를 구한다
길이: 60초
장르: fantasy
톤: epic
```

### SF 스토리
```
이야기: 외계인이 지구에 도착한다
길이: 45초
장르: sci-fi
톤: mysterious
```

### 코미디 스토리
```
이야기: 요리사가 만든 음식이 살아난다
길이: 30초
장르: fantasy
톤: whimsical
```

## 🎯 다음 단계

생성된 프롬프트를 사용하여:
1. **이미지 생성**: Stable Diffusion, DALL-E, Midjourney 등
2. **비디오 생성**: 이미지를 FFmpeg로 합성
3. **음악/사운드 추가**: BGM 및 효과음
4. **최종 편집**: 자막, 전환 효과 등

## 💡 팁

- 더 구체적인 이야기일수록 더 좋은 결과
- 장르와 톤을 명확히 지정하면 일관성 있는 스타일
- 짧은 영상(15-60초)부터 시작하여 테스트
- 생성된 프롬프트를 직접 편집하여 미세 조정 가능

## 📧 문의

문제가 있거나 질문이 있으면 이슈를 생성하세요!
