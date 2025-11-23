# 🎬 AI Short Factory

간단한 아이디어를 1-2분 쇼츠 영상용 Stable Diffusion 프롬프트로 자동 변환하는 도구

## 📖 개요

AI Short Factory는 간단한 이야기 아이디어를 받아서:
1. **이야기 확장**: 1-2분 분량의 완성된 쇼츠 스토리로 확장
2. **장면 구성**: AI가 최적의 장면 개수를 판단하고 분할
3. **프롬프트 생성**: 각 장면마다 Stable Diffusion 이미지 생성 프롬프트 생성
4. **번역 제공**: 영어 프롬프트와 한국어 번역 동시 제공

## ✨ 주요 기능

- 🤖 **로컬 LLM 사용**: llama.cpp 기반 로컬 모델로 프라이버시 보장
- 🎨 **Stable Diffusion 프롬프트**: 고품질 이미지 생성을 위한 전문 프롬프트
- 🌐 **웹 UI**: Streamlit 기반 사용자 친화적 인터페이스
- 🔄 **재생성 기능**: 원하는 장면만 선택적으로 재생성 가능
- 🇰🇷 **한국어 지원**: 전체 프로세스 한국어 지원

## 📁 프로젝트 구조

```
AI_Short_Factory/
├── app.py                      # Streamlit 웹 UI
├── run.sh                      # 실행 스크립트
├── requirements.txt            # Python 의존성
├── src/
│   ├── pipeline/
│   │   ├── story_expander.py   # 이야기 확장 모듈
│   │   ├── prompt_generator.py # 프롬프트 생성 모듈
│   │   └── translator.py       # 번역 모듈
│   ├── generators/
│   │   └── llm.py             # LLM 클라이언트 (llama.cpp)
│   └── common/
│       ├── config.py          # 설정
│       └── logger.py          # 로깅
├── models/                    # GGUF 모델 파일 위치
└── bin/                       # llama-cli 실행 파일 위치
```

## 🚀 시작하기

### 1. 필요한 것

- Python 3.11+
- llama.cpp (llama-cli 실행 파일)
- GGUF 형식의 LLM 모델

### 2. 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# llama.cpp 빌드 (아직 없다면)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make
# llama-cli를 AI_Short_Factory/bin/ 에 복사
```

### 3. 모델 준비

GGUF 형식의 모델을 다운로드하고 `models/` 디렉토리에 배치:
```bash
mkdir -p models
# 예: Llama, Mistral, Qwen 등의 GGUF 모델 다운로드
# models/model-q4_K_M.gguf 경로에 배치
```

### 4. 실행

```bash
./run.sh
```

또는

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속

## 📝 사용 방법

### 워크플로우

1. **이야기 아이디어 입력**
   - 간단한 이야기 아이디어를 텍스트로 입력
   - 예: "우주 정거장에서 깨어난 로봇이 인류의 마지막 메시지를 찾는 이야기"

2. **이야기 확장**
   - "🚀 이야기 확장" 버튼 클릭
   - AI가 1-2분 분량의 완성된 스토리로 확장
   - 마음에 들지 않으면 "🔄 재시도" 버튼으로 다시 생성

3. **프롬프트 생성**
   - "✅ 컨펌" 버튼으로 확정
   - AI가 장면 개수를 판단하고 각 장면의 프롬프트 생성
   - 영어 원본 + 한국어 번역 동시 제공

4. **선택적 재생성**
   - 각 장면 옆 체크박스로 재생성할 장면 선택
   - "🔄 선택한 N개 장면 재생성" 버튼 클릭

## ⚙️ 설정

`src/common/config.py`에서 다음 설정 변경 가능:

- `LLM_MODEL_NAME`: 사용할 GGUF 모델 파일명
- `LLM_TEMPERATURE`: 창의성 수준 (0.0-1.0)
- `LLM_MAX_TOKENS`: 최대 생성 토큰 수
- `LLAMA_CPP_PATH`: llama-cli 실행 파일 경로

## 🎯 출력 형식

각 장면은 다음 정보를 포함:

- **장면 번호**: 순서
- **장면 설명 (한국어)**: 시각적 설명
- **Stable Diffusion 프롬프트 (영어)**: 이미지 생성용 상세 프롬프트
- **한국어 번역**: 프롬프트의 한국어 버전
- **길이**: 장면 지속 시간 (초)

### Stable Diffusion 프롬프트 예시

```
a lonely robot in abandoned space station, dark corridor,
blue emergency lights, cinematic lighting, detailed mechanical parts,
sci-fi atmosphere, digital art, highly detailed, 4k, masterpiece
```

## 🔧 트러블슈팅

### llama-cli not found
```bash
# llama.cpp를 빌드하고 bin/ 디렉토리에 복사
cd llama.cpp && make
cp llama-cli /path/to/AI_Short_Factory/bin/
```

### Model not found
```bash
# models/ 디렉토리 확인
ls models/
# GGUF 모델이 있는지 확인하고 config.py의 LLM_MODEL_NAME 업데이트
```

### Out of memory
- 더 작은 quantization 모델 사용 (Q4_K_M 대신 Q4_0)
- `LLM_MAX_TOKENS` 값 줄이기
- `LLM_THREADS` 값 조정

## 📄 라이선스

MIT License

## 🤝 기여

Issues와 Pull Requests를 환영합니다!

## 📧 문의

프로젝트 관련 문의사항은 Issues를 통해 남겨주세요.
