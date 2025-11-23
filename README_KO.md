# 🎬 AI Shorts Factory

**간단한 스토리 한 줄로 → 완성된 숏폼 비디오까지!**

AI를 활용하여 TikTok, Instagram Reels, YouTube Shorts용 세로형 비디오를 자동 생성하는 파이프라인입니다.

## ✨ 특징

- 📝 **스토리 확장**: 간단한 아이디어를 상세한 스토리로 확장
- 🎬 **장면 계획**: 씬과 샷 분할, 카메라 워크 자동 계획
- 🎨 **시각적 속성**: 명도, 채도, 그림체, 색보정 등 세밀한 시각적 제어
- 🖼️ **이미지 생성**: Stable Diffusion 연동 (준비 완료)
- 🎥 **비디오 합성**: FFmpeg 기반 영상 합성 (준비 완료)
- 🔒 **로컬 우선**: 모든 처리를 로컬에서 실행 (외부 API 불필요)

## 🎯 최종 목표

```
입력 창에 간단한 이야기
    ↓
LLM이 스토리 확장
    ↓
필요한 장면 계산
    ↓
각 장면당 프롬프트 작성 (몇 초, 명도, 채도, 그림체 등)
    ↓
이미지 생성 ← [현재 여기까지 완료!]
    ↓
영상 합성
    ↓
완성된 숏폼 비디오 🎉
```

## 📂 프로젝트 구조

```
AI_Short_Factory/
├── models/                          # Llama 모델 (사용자가 다운로드)
│   └── llama-3.1-8b-instruct/
│       └── Llama3.1-8B-Instruct/
├── config/                          # 설정 파일
│   └── config.py
├── src/shorts_factory/              # 메인 패키지
│   ├── core/                        # 핵심 파이프라인
│   │   ├── llm_client.py           # LLM 통신
│   │   ├── pipeline.py             # 3단계 파이프라인
│   │   └── schemas.py              # 데이터 스키마
│   ├── generators/                  # 생성기 모듈
│   │   ├── image_gen.py            # 이미지 생성
│   │   └── video_gen.py            # 비디오 합성
│   └── utils/                       # 유틸리티
│       └── helpers.py
├── data/                            # 생성된 데이터
│   ├── outputs/                     # JSON 결과
│   ├── images/                      # 생성된 이미지
│   └── videos/                      # 최종 비디오
├── main.py                          # 메인 실행 파일
├── requirements-new.txt             # Python 의존성
└── README_KO.md                     # 이 파일
```

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# Python 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements-new.txt
```

### 2단계: Llama 모델 준비

이미 다운로드하신 모델이 있습니다:
```
models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct/
```

### 3단계: LLM 서버 시작

로컬 Llama 서버를 실행하세요 (예: llama.cpp):

```bash
# llama.cpp 서버 시작
llama-server \
  --model models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct \
  --port 8000 \
  --ctx-size 4096 \
  --n-gpu-layers 35
```

또는 vLLM:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model models/llama-3.1-8b-instruct/Llama3.1-8B-Instruct \
  --port 8000
```

### 4단계: 파이프라인 실행!

**명령줄 모드:**
```bash
python main.py \
  --logline "기사가 용을 물리치고 공주를 구한다" \
  --duration 60 \
  --genre fantasy \
  --tone epic
```

**대화형 모드:**
```bash
python main.py --interactive
```

## 📖 사용 예제

### 기본 사용법 (프롬프트 생성까지)

```bash
python main.py \
  --logline "요리사의 요리가 살아난다" \
  --duration 45 \
  --genre comedy \
  --tone whimsical \
  --output cooking_short
```

결과:
- ✅ 스토리 아웃라인 (5-20개 비트)
- ✅ 씬 & 샷 계획 (3-12개 씬, 8-40개 샷)
- ✅ 각 샷의 세부 속성:
  - 그림체 (`art_style`)
  - 명도 (`brightness`)
  - 채도 (`saturation`)
  - 대비 (`contrast`)
  - 색보정 (`color_grading`)
  - 조명 방향 (`lighting_direction`)
- ✅ 텍스트-이미지 프롬프트 (Stable Diffusion 준비 완료)

### 이미지 생성 포함 (선택사항)

```bash
python main.py \
  --logline "로봇이 감정을 발견한다" \
  --duration 30 \
  --genre sci-fi \
  --generate-images
```

**필요사항**: Stable Diffusion WebUI 또는 ComfyUI가 `localhost:7860`에서 실행 중이어야 함

### 전체 파이프라인 (영상까지)

```bash
python main.py \
  --logline "해커가 기업 AI에 침투한다" \
  --duration 90 \
  --genre cyberpunk \
  --generate-images \
  --generate-video
```

**필요사항**:
- Stable Diffusion WebUI
- FFmpeg 설치

## 🎨 시각적 속성 제어

각 샷마다 다음 속성들이 자동으로 설정됩니다:

| 속성 | 옵션 | 설명 |
|------|------|------|
| `art_style` | 자유 텍스트 | 그림체 (예: "사실적 영화풍", "애니메이션", "수채화") |
| `brightness` | very_dark, dark, medium, bright, very_bright | 명도 수준 |
| `saturation` | desaturated, low, medium, high, vivid | 채도 수준 |
| `contrast` | low, medium, high, dramatic | 대비 강도 |
| `color_grading` | 자유 텍스트 | 색보정 (예: "따뜻한 오렌지톤", "차가운 청록색") |
| `lighting_direction` | front, back, side, top, bottom | 조명 방향 |
| `mood_keywords` | 배열 | 분위기 키워드 |

예시 출력:
```json
{
  "shot_id": "shot_001",
  "visual_style": {
    "art_style": "사실적 영화풍",
    "brightness": "dark",
    "saturation": "desaturated",
    "contrast": "dramatic",
    "color_grading": "틸-오렌지 영화 룩",
    "lighting_direction": "side",
    "mood_keywords": ["긴장감", "신비로운", "위협적"]
  }
}
```

## 🧪 프로그래밍 방식 사용

```python
from src.shorts_factory.core.pipeline import generate_shorts_prompt_package

# 프롬프트 생성
result = generate_shorts_prompt_package(
    logline="외계인이 지구에 도착한다",
    target_duration_seconds=60,
    tone="mysterious",
    genre="sci-fi"
)

# 결과 확인
print(f"비트: {len(result.outline.beats)}개")
print(f"씬: {len(result.scene_plan.scenes)}개")
print(f"샷: {len(result.prompts.shots)}개")

# 첫 번째 샷 프롬프트 확인
first_shot = result.prompts.shots[0]
print(f"프롬프트: {first_shot.positive_prompt}")
print(f"시각 속성: {first_shot.visual_attributes}")

# JSON 저장
result.to_json_file("my_short.json")
```

## 🔧 설정

### 환경 변수

```bash
# LLM 서버 URL (기본값: http://localhost:8000/v1)
export LOCAL_LLM_BASE_URL="http://localhost:8000/v1"

# 이미지 생성 서버 URL (기본값: http://localhost:7860)
export IMAGE_GEN_API_URL="http://localhost:7860"

# 로그 레벨
export LOG_LEVEL="DEBUG"
```

### config/config.py 수정

프로젝트 경로, 모델 경로, 기본 파라미터 등을 `config/config.py`에서 수정할 수 있습니다.

## 📊 출력 형식

### JSON 결과 구조

```json
{
  "outline": {
    "logline": "...",
    "metadata": {...},
    "beats": [...]
  },
  "scene_plan": {
    "scenes": [
      {
        "scene_id": "scene_001",
        "shots": [
          {
            "shot_id": "shot_001",
            "visual_style": {
              "art_style": "...",
              "brightness": "...",
              "saturation": "...",
              ...
            },
            ...
          }
        ]
      }
    ]
  },
  "prompts": {
    "global_style": {...},
    "shots": [
      {
        "shot_id": "shot_001",
        "positive_prompt": "...",
        "negative_prompt": "...",
        "generation_params": {...},
        "visual_attributes": {...}
      }
    ]
  }
}
```

## 🛠️ 다음 단계 (TODO)

현재 **1~4단계**까지 완료되었습니다. 다음 단계는:

### 5단계: 이미지 생성 구현
- [ ] Automatic1111 WebUI API 연동
- [ ] ComfyUI API 연동
- [ ] 배치 처리 최적화
- [ ] 이미지 품질 검증

### 6단계: 비디오 합성 구현
- [ ] FFmpeg를 통한 이미지 시퀀스 합성
- [ ] 트랜지션 효과 (크로스페이드, 디졸브)
- [ ] 오디오 트랙 추가
- [ ] 자막/캡션 오버레이

### 추가 개선사항
- [ ] 파인튜닝 지원 (도메인 특화 프롬프트)
- [ ] 멀티 에이전트 협업 (각 역할별 전문 에이전트)
- [ ] 웹 UI 추가 (Gradio 또는 Streamlit)
- [ ] 스타일 프리셋 (영화풍, 애니메이션, 다큐멘터리 등)

## 🐛 문제 해결

**"LLM 서버에 연결할 수 없습니다"**
- LLM 서버가 실행 중인지 확인
- `http://localhost:8000/v1/models`에 접속하여 확인
- `LOCAL_LLM_BASE_URL` 환경 변수 확인

**"LLM 응답이 유효한 JSON이 아닙니다"**
- Instruction-tuned 모델 사용 확인 (예: Llama-3.1-Instruct)
- Temperature 낮추기 시도: `temperature_outline=0.5`

**"이미지 생성 서버 연결 실패"**
- Stable Diffusion WebUI가 `--api` 옵션으로 실행 중인지 확인
- ComfyUI가 실행 중인지 확인

## 📄 라이선스

[라이선스 명시]

## 🤝 기여

기여는 언제나 환영합니다! 이슈를 등록하거나 PR을 보내주세요.

## 👨‍💻 제작자

AI Shorts Factory Team

---

**현재 상태**: ✅ **Stage 1-4 완료** (스토리 → 프롬프트)
**다음 단계**: 🔜 Stage 5-6 (이미지 → 비디오)
