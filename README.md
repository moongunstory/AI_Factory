# AI Short Factory

AI 기반 쇼츠 영상 자동 생성 파이프라인

## 📁 프로젝트 구조

```
AI_Short_Factory/
├── src/                    # 파이썬 모듈
│   ├── generators/        # AI 생성 모듈
│   │   ├── llm.py        # LLM (llama.cpp)
│   │   ├── image.py      # 이미지 생성 (ComfyUI) [예정]
│   │   ├── audio.py      # 오디오 생성 [예정]
│   │   └── video.py      # 비디오 생성 (WAN2.2) [예정]
│   │
│   ├── processors/        # 후처리/편집
│   │   └── video_editor.py [예정]
│   │
│   ├── publishers/        # SNS 업로드
│   │   └── sns.py [예정]
│   │
│   ├── pipeline/          # 워크플로우
│   │   ├── story_to_prompts.py  # 스토리 → 프롬프트 변환
│   │   └── orchestrator.py [예정]
│   │
│   └── common/            # 공통 유틸
│       ├── config.py      # 설정 관리
│       └── logger.py      # 로깅
│
├── engine/                # LLM 엔진
│   └── llama.cpp/         # llama.cpp 빌드
│
├── models/                # AI 모델
│   ├── llama-3.1-8b/      # LLM 모델
│   ├── wan2/              # WAN2.2 [예정]
│   ├── comfyui/           # ComfyUI [예정]
│   └── audio/             # 오디오 모델 [예정]
│
└── output/                # 생성된 결과물
    ├── clips/             # 비디오 클립
    ├── images/            # 이미지
    ├── prompts/           # 생성된 프롬프트
    └── logs/              # 로그 파일
```

## 🚀 현재 구현된 기능

### 1. Story to Prompts (스토리 → 프롬프트 변환)

이야기를 입력하면 AI가 자동으로 쇼츠 영상용 프롬프트를 생성합니다.

**생성되는 내용:**
- 씬별 이미지 생성 프롬프트
- 나레이션 텍스트
- 배경음악 무드
- 영상 구성 메타데이터

## 📋 사전 준비

### 1. llama.cpp 설치 및 빌드

```bash
# llama.cpp 클론 및 빌드
cd engine
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release

# 빌드 확인
./bin/llama-cli --version
```

### 2. LLM 모델 다운로드

```bash
# 모델 디렉토리로 이동
cd models/llama-3.1-8b

# GGUF 모델 다운로드 (예: Hugging Face)
# 예시: llama-3.1-8b-instruct.Q4_K_M.gguf
```

**추천 모델:**
- Llama 3.1 8B Instruct (Q4_K_M 양자화)
- Mistral 7B Instruct
- Qwen 2.5 7B Instruct

### 3. Python 가상환경 설정

```bash
# 가상환경 활성화
source .venv/bin/activate

# 필요한 패키지 설치 (현재는 기본 라이브러리만 사용)
# 추후 requirements.txt 추가 예정
```

## 💻 사용법

### CLI로 사용

```bash
# 기본 사용
python -m src "용감한 기사가 산속에서 드래곤과 싸웁니다"

# 파일에서 읽기
python -m src --file story.txt

# 스타일 지정
python -m src "우주 모험 이야기" --style anime --duration 30

# 상세 로그 출력
python -m src "판타지 모험" --style cinematic --verbose
```

### Python 코드에서 사용

```python
from src import create_prompts_from_story

story = "어느 날, 작은 로봇이 버려진 도시를 발견했습니다..."

result = create_prompts_from_story(
    story=story,
    style="3d",
    duration=25.0
)

# 생성된 씬 정보
for scene in result["scenes"]:
    print(f"Scene {scene['scene_number']}: {scene['description']}")
    print(f"Image Prompt: {scene['image_prompt']}")
    print(f"Narration: {scene['narration']}")
    print()
```

## 📤 출력 예시

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "description": "Knight confronting dragon",
      "image_prompt": "Epic cinematic shot, brave knight in shining armor facing massive red dragon, misty mountain peak, dramatic lighting, fantasy art style, 4k quality",
      "duration": 4.0,
      "narration": "In the heart of the ancient mountains, a hero rises.",
      "audio_mood": "epic"
    },
    ...
  ],
  "metadata": {
    "title": "The Dragon Slayer",
    "total_duration": 20.0,
    "style": "cinematic",
    "target_platform": "shorts"
  }
}
```

결과는 `output/prompts/prompts_YYYYMMDD_HHMMSS.json`에 저장됩니다.

## 🔧 설정

`src/common/config.py`에서 설정을 변경할 수 있습니다:

```python
# LLM 파라미터
LLM_TEMPERATURE = 0.7      # 창의성 (0.0-1.0)
LLM_MAX_TOKENS = 2048      # 최대 생성 토큰
LLM_TOP_P = 0.9            # Top-p 샘플링
LLM_THREADS = 4            # CPU 스레드 수
```

환경변수로도 설정 가능:

```bash
export LLM_TEMPERATURE=0.8
export LLM_MAX_TOKENS=4096
export LLM_THREADS=8
```

## 🛣️ 로드맵

- [x] Story to Prompts 변환
- [ ] ComfyUI 이미지 생성 통합
- [ ] WAN2.2 이미지→영상 변환
- [ ] 오디오 생성 (TTS + BGM)
- [ ] 자동 영상 편집
- [ ] SNS 자동 업로드 (YouTube Shorts, TikTok, Instagram)
- [ ] Web UI 개발

## 🐛 트러블슈팅

### llama.cpp 실행 오류

```bash
# 빌드 경로 확인
ls engine/llama.cpp/build/bin/llama-cli

# 실행 권한 확인
chmod +x engine/llama.cpp/build/bin/llama-cli
```

### 모델 파일을 찾을 수 없음

```bash
# 모델 디렉토리 확인
ls models/llama-3.1-8b/*.gguf

# Config.get_model_file()은 첫 번째 .gguf 파일을 자동으로 찾습니다
```

### JSON 파싱 오류

LLM이 JSON 형식을 잘 따르지 않을 때:
- 더 큰 모델 사용 (8B → 13B)
- Temperature 낮추기 (0.7 → 0.5)
- 프롬프트에 "ONLY JSON" 강조

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 PR은 언제나 환영합니다!
