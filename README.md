# 🎬 AI Short Factory

간단한 스토리 아이디어를 20-25개 장면의 고품질 Stable Diffusion 프롬프트 시퀀스로 자동 변환하는 도구

## 📖 개요

AI Short Factory는 간단한 이야기 아이디어를 받아서:
1. **이야기 확장**: 50-70초 분량의 완성된 쇼츠 스토리로 확장
2. **스토리 비트 분석**: 10-15개의 주요 서사 포인트 추출
3. **캐릭터 시트 생성**: 2-4명의 주요 캐릭터에 대한 상세한 외형/의상 디자인
4. **글로벌 비주얼 스타일 적용**: 10가지 테마 중 선택 (다크 판타지, 애니메이션, 디즈니 등)
5. **20-25개 장면 생성**: 자동 지속시간 추론으로 영화적 장면 시퀀스 생성
6. **고품질 프롬프트**: 7단계 구조화된 Stable Diffusion 프롬프트
7. **시각적 일관성**: 캐릭터와 스타일의 완벽한 일관성 유지

## ✨ 주요 기능

### 🎯 고급 장면 생성
- **20-25개 장면**: 완전한 영화적 시퀀스 (기존 8-15개에서 대폭 확장)
- **자동 지속시간 추론**: 액션(2-3초), 감정(4-5초), 클라이맥스(5-6초)
- **스토리 비트 시스템**: 10-15개 주요 서사 포인트 자동 추출

### 🎨 비주얼 스타일 시스템
- **10가지 테마**: dark_fantasy, anime, disney, cinematic_realism, game_cinematic, cyber_fantasy, horror, fantasy_adventure, sci_fi, retro_synthwave
- **글로벌 스타일 일관성**: 색상, 조명, 카메라, 텍스처, 분위기 통일
- **테마별 프리셋**: 각 테마마다 최적화된 비주얼 파라미터

### 👥 캐릭터 일관성
- **글로벌 캐릭터 시트**: 외형, 의상, 장비, 성격적 특징 상세 정의
- **일관성 태그**: Stable Diffusion용 캐릭터 일관성 보장 태그
- **자동 적용**: 모든 장면에 캐릭터 디자인 자동 반영

### 🎬 7단계 프롬프트 구조
1. Subject: 캐릭터 + 액션
2. Environment: 배경/환경
3. Cinematic Motion: 역동적 움직임/액션
4. Lighting: 조명 효과
5. Camera: 카메라 앵글/구도
6. Style Details: 스타일 디테일
7. Global Visual Style: 글로벌 스타일 자동 추가

### 🚀 기술적 특징
- 🤖 **로컬 LLM 사용**: llama-server 기반 HTTP API (10-50배 빠른 성능)
- 🔧 **JSON 신뢰성**: 2단계 방어 시스템 (~100% JSON 파싱 성공률)
- 🌐 **웹 UI**: Flask + Streamlit 인터페이스
- 🔄 **재생성 기능**: 원하는 장면만 선택적으로 재생성 가능
- 🇰🇷 **한국어 지원**: 전체 프로세스 한국어 지원

## 📁 프로젝트 구조

```
AI_Short_Factory/
├── run.sh                                    # 실행 스크립트
├── requirements.txt                          # Python 의존성
├── src/
│   ├── __main__.py                          # CLI 진입점
│   ├── app.py                               # Streamlit 웹 UI
│   ├── pipeline/
│   │   ├── story_expander.py                # 이야기 확장 모듈
│   │   ├── prompt_generator.py              # 기본 프롬프트 생성 모듈
│   │   ├── advanced_scene_generator.py      # 🆕 고급 장면 생성 모듈
│   │   ├── visual_styles.py                 # 🆕 테마별 비주얼 스타일 정의
│   │   ├── scene_formatter.py               # 🆕 출력 포맷터
│   │   └── translator.py                    # 번역 모듈
│   ├── generators/
│   │   └── llm.py                          # LLM 클라이언트 (llama-server HTTP API)
│   ├── common/
│   │   ├── config.py                       # 설정
│   │   ├── logger.py                       # 로깅
│   │   ├── json_utils.py                   # JSON 자동 복구
│   │   └── tests/
│   │       └── test_json_parsing.py        # JSON 신뢰성 테스트
│   └── web/
│       ├── app.py                          # Flask 웹 서버
│       └── templates/                      # HTML 템플릿
├── scripts/
│   └── llama_server_manager.sh             # llama-server 관리 스크립트
├── models/                                  # GGUF 모델 파일 위치
└── output/                                  # 생성된 결과물 저장
    ├── prompts/                            # 장면 프롬프트 JSON/텍스트
    └── logs/                               # 로그 파일
```

## 🚀 시작하기

### 1. 필요한 것

- Python 3.11+
- llama.cpp (llama-server 실행 파일)
- GGUF 형식의 LLM 모델 (권장: Llama 3.1 8B Q4_K_M)

### 2. 설치

#### Python 의존성 설치
```bash
pip install -r requirements.txt
```

#### llama.cpp 빌드

**🎮 GPU 지원 (권장 - Windows/Linux)**

GPU가 있다면 CUDA를 활성화하여 빌드하세요. **10-50배 빠릅니다!**

**Windows (CUDA):**
```powershell
# Visual Studio 2022 및 CUDA Toolkit 12.x 필요
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_CUDA=ON
cmake --build build --config Release

# 빌드 완료 후 engine/llama.cpp/build/bin/Release/llama-server.exe 생성됨
```

**Linux (CUDA):**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_CUDA=ON
cmake --build build --config Release
```

**🖥️ CPU 전용 (GPU 없을 때)**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

빌드 후 `engine/llama.cpp/build/bin/` 경로에 `llama-server` 실행 파일이 생성됩니다.

### 3. 모델 준비

GGUF 형식의 모델을 다운로드하고 `models/` 디렉토리에 배치:
```bash
mkdir -p models/llama-3.1-8b
# 예: Llama 3.1 8B GGUF 모델 다운로드
# models/llama-3.1-8b/model-q4_K_M.gguf 경로에 배치
```

### 4. llama-server 실행

프로젝트를 실행하기 전에 llama-server를 먼저 시작해야 합니다.

**Windows:**
```powershell
# 서버 시작
.\scripts\llama_server_manager.ps1 start

# 상태 확인
.\scripts\llama_server_manager.ps1 status

# 서버 중지
.\scripts\llama_server_manager.ps1 stop
```

**Linux/Mac:**
```bash
# 서버 시작
./scripts/llama_server_manager.sh start

# 상태 확인
./scripts/llama_server_manager.sh status

# 서버 중지
./scripts/llama_server_manager.sh stop
```

### 5. 애플리케이션 실행

#### A. 웹 UI 실행 (권장)
```bash
./run.sh
```
브라우저에서 `http://localhost:8501` 로 자동 접속

#### B. CLI 사용
```bash
# 기본 사용
python -m src "용감한 기사가 용과 싸우는 이야기"

# 테마 지정
python -m src "우주 모험 이야기" --theme cyber_fantasy --duration 60

# 파일에서 읽기
python -m src --file story.txt --theme anime

# 마크다운 출력
python -m src "판타지 이야기" --format markdown --output result.md

# 사용 가능한 테마 목록 보기
python -m src --list-themes
```

## 📝 사용 방법

### 고급 장면 생성 워크플로우

1. **스토리 아이디어 입력**
   - 간단한 이야기 아이디어를 텍스트로 입력
   - 예: "우주 정거장에서 깨어난 로봇이 인류의 마지막 메시지를 찾는 이야기"

2. **테마 선택**
   - 10가지 비주얼 테마 중 선택:
     - `dark_fantasy`: 다크 판타지 (고딕, 신비로운)
     - `anime`: 일본 애니메이션 스타일
     - `disney`: 디즈니/픽사 3D 애니메이션
     - `cinematic_realism`: 영화적 사실주의
     - `game_cinematic`: 게임 시네마틱 (언리얼 엔진)
     - `cyber_fantasy`: 사이버펑크 판타지
     - `horror`: 공포/호러
     - `fantasy_adventure`: 판타지 어드벤처
     - `sci_fi`: 공상과학
     - `retro_synthwave`: 레트로 신스웨이브

3. **자동 파이프라인 실행**
   - ✅ 스토리 확장 (50-70초 분량)
   - ✅ 스토리 비트 추출 (10-15개)
   - ✅ 캐릭터 시트 생성 (2-4명)
   - ✅ 글로벌 비주얼 스타일 적용
   - ✅ 20-25개 장면 생성
   - ✅ 영어 프롬프트 + 한국어 번역

4. **결과물 확인**
   - 스토리 요약
   - 스토리 비트 목록
   - 캐릭터 상세 정보
   - 글로벌 비주얼 스타일 정의
   - 20-25개 장면 (각 장면당 프롬프트 + 번역)

## ⚙️ 설정

### 환경 변수로 설정 (권장)

`.env` 파일을 생성하거나 환경 변수로 설정:

```bash
# GPU 설정 (기본값)
LLAMA_CTX_SIZE=4096              # 컨텍스트 크기
LLAMA_BATCH_SIZE=2048            # 배치 크기
LLAMA_N_GPU_LAYERS=-1            # GPU 레이어 수 (-1 = 모두)
LLAMA_N_PARALLEL=8               # 동시 요청 수

# LLM 파라미터
LLM_TEMPERATURE=0.7              # 창의성 (0.0-1.0)
LLM_MAX_TOKENS=2048              # 최대 생성 토큰
LLM_THREADS=4                    # CPU 스레드 수

# 서버 설정
LLAMA_SERVER_HOST=127.0.0.1
LLAMA_SERVER_PORT=8080
```

### GPU 최적화 팁

**🚀 VRAM이 충분한 경우 (12GB+):**
- `LLAMA_CTX_SIZE=8192` - 더 긴 컨텍스트
- `LLAMA_BATCH_SIZE=4096` - 더 큰 배치
- 더 큰 모델 사용 (Q6_K 또는 Q8_0)

**⚡ VRAM이 부족한 경우 (6-8GB):**
- `LLAMA_CTX_SIZE=2048`
- `LLAMA_BATCH_SIZE=1024`
- `LLAMA_N_GPU_LAYERS=20` - 일부 레이어만 GPU에
- 작은 quantization (Q4_K_M 또는 Q4_0)

**🖥️ CPU 전용 환경:**
- `LLAMA_N_GPU_LAYERS=0` - GPU 비활성화
- `LLM_THREADS=8` - CPU 스레드 증가
- `LLAMA_CTX_SIZE=1024` - 메모리 절약

### config.py 직접 수정

`src/common/config.py`에서 기본값 변경 가능

## 🎯 출력 형식

### 완전한 출력 구조

```
[스토리 요약]
전체 스토리를 한 문단으로 요약

[스토리 비트]
1. 주요 서사 포인트 1
2. 주요 서사 포인트 2
...
12. 주요 서사 포인트 12

[캐릭터]
● 전사 (주인공)
  외형: 키 큰 근육질 남성, 전투로 상처받은 얼굴, 짧은 검은 머리...
  의상: 은색 장식이 달린 어두운 가죽 갑옷...
  장비: 룬 문자가 새겨진 고대 장검...
  일관성 태그: same warrior, same armor design...

[글로벌 비주얼 스타일]
테마: 다크 판타지
색상 팔레트: deep purples, blood reds, shadowy blacks...
조명: volumetric god rays, dramatic rim lighting...
카메라: cinematic 35mm, dramatic low angles...
텍스처: dark painterly style, high contrast...

[장면]
총 장면 수: 23
총 지속시간: 62초

Scene 1
- 지속시간: 3초
- 설명: 전사가 어두운 숲의 가장자리에 서서 검을 움켜쥐고 있다
- 프롬프트 (영어): a tall muscular warrior gripping ancient rune sword,
  standing at dark forest edge, mist swirling around feet, dramatic wind,
  volumetric god rays breaking through trees, cinematic 35mm, low angle shot,
  dark painterly style, deep purples and blacks, masterpiece, 8k...
- 프롬프트 (한국어): 고대 룬 검을 움켜쥔 키 큰 근육질 전사...
```

### 7단계 프롬프트 구조 예시

```
[1. Subject] a brave warrior gripping his glowing sword
[2. Environment] standing on a cliff overlooking a dragon's lair
[3. Cinematic Motion] wind blowing his cape, sparks flying from sword
[4. Lighting] dramatic sunset backlight, volumetric fog, rim lighting
[5. Camera] wide-angle cinematic shot, low angle, epic composition
[6. Style Details] dark fantasy art style, highly detailed armor
[7. Global Style] deep purples and reds, gothic atmosphere,
                 consistent dark fantasy style, masterpiece, 8k
```

## 🔧 트러블슈팅

### llama-server not found

**Windows:**
```powershell
# llama.cpp를 CUDA로 빌드
cd llama.cpp
cmake -B build -DLLAMA_CUDA=ON
cmake --build build --config Release

# 또는 scripts/llama_server_manager.ps1에서 경로 지정
```

**Linux:**
```bash
# llama.cpp를 빌드
cd llama.cpp
cmake -B build -DLLAMA_CUDA=ON  # GPU 지원
cmake --build build --config Release

# llama-server가 PATH에 있는지 확인
which llama-server
```

### CUDA 오류 (GPU 인식 안됨)

```bash
# CUDA Toolkit 설치 확인
nvcc --version

# GPU 인식 확인
nvidia-smi

# PyTorch GPU 테스트
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

llama.cpp는 CUDA를 직접 사용하므로 PyTorch 설치는 선택사항입니다.

### Out of VRAM

GPU 메모리 부족 시:
```bash
# 환경 변수로 GPU 레이어 수 줄이기
export LLAMA_N_GPU_LAYERS=20  # 모두(-1) 대신 일부만

# 또는 더 작은 quantization 모델 사용
# Q6_K → Q4_K_M → Q4_0 순으로 VRAM 사용량 감소
```

### llama-server 관리

**Windows:**
```powershell
# 서버 시작
.\scripts\llama_server_manager.ps1 start

# 서버 상태 확인
.\scripts\llama_server_manager.ps1 status

# 서버 중지
.\scripts\llama_server_manager.ps1 stop

# 서버 재시작
.\scripts\llama_server_manager.ps1 restart
```

**Linux:**
```bash
# 서버 시작
./scripts/llama_server_manager.sh start

# 서버 상태 확인
./scripts/llama_server_manager.sh status

# 서버 중지
./scripts/llama_server_manager.sh stop

# 서버 재시작
./scripts/llama_server_manager.sh restart
```

### Model not found
```bash
# models/ 디렉토리 확인
ls models/llama-3.1-8b/
# GGUF 모델이 있는지 확인하고 config.py 업데이트
```

### JSON 파싱 오류
- 자동 복구 시스템이 대부분의 오류 처리
- 문제가 계속되면 temperature 낮추기 (0.5-0.6)
- `src/common/tests/test_json_parsing.py`로 테스트

### Out of memory
- 더 작은 quantization 모델 사용 (Q4_K_M 대신 Q4_0 또는 Q3_K_M)
- `LLAMA_CTX_SIZE` 값 줄이기 (1024 → 512)
- `LLM_MAX_TOKENS` 값 줄이기
- 동시 요청 수 제한

### 생성 속도가 느림
- **✅ GPU 활성화 필수!** llama.cpp를 CUDA로 빌드
- `LLAMA_N_GPU_LAYERS=-1` 설정 확인 (모든 레이어를 GPU에)
- llama-server 로그 확인: GPU가 실제로 사용되는지 체크
- 더 작은 모델 사용 (8B 대신 7B 또는 3B)
- Flash Attention 활성화 (`--flash-attn` 옵션)

**GPU 사용 확인:**
```bash
# Windows
nvidia-smi  # GPU 사용률 확인

# llama-server 로그 확인
Get-Content output/logs/llama_server.log -Tail 50
```

## 🆕 새로운 기능 (v2.0)

### 고급 장면 생성 시스템
- ✨ **20-25개 장면**: 기존 8-15개에서 확장
- 🎨 **10가지 테마**: 다양한 비주얼 스타일 프리셋
- 👥 **캐릭터 일관성**: 글로벌 캐릭터 시트로 완벽한 일관성
- 📖 **스토리 비트**: 서사 구조 자동 분석
- 🎬 **7단계 프롬프트**: 전문가급 Stable Diffusion 프롬프트
- ⏱️ **자동 타이밍**: 장면 유형별 지속시간 자동 추론
- 🔄 **JSON 신뢰성**: 2단계 방어로 ~100% 파싱 성공률

### 성능 개선
- ⚡ **10-50배 빠른 속도**: llama-server HTTP API 사용
- 🎯 **정확도 향상**: 향상된 프롬프트 엔지니어링
- 💾 **메모리 효율**: 최적화된 컨텍스트 관리

## 📚 관련 문서

- [JSON 신뢰성 아키텍처](docs/JSON_RELIABILITY_ARCHITECTURE.md)
- [llama.cpp 공식 문서](https://github.com/ggerganov/llama.cpp)
- [Stable Diffusion 프롬프트 가이드](https://stable-diffusion-art.com/prompt-guide/)

## 🎓 사용 예시

### 다크 판타지 스토리
```bash
python -m src "고대 왕국의 마지막 전사가 어둠의 용을 무찌르기 위한 여정" \
  --theme dark_fantasy \
  --duration 60 \
  --format markdown
```

### 애니메이션 스타일 우주 모험
```bash
python -m src "우주 정거장에서 깨어난 소녀가 사라진 승무원들의 비밀을 찾는다" \
  --theme anime \
  --duration 65
```

### 사이버펑크 액션
```bash
python -m src "네온 도시의 해커가 거대 기업의 음모를 파헤친다" \
  --theme cyber_fantasy \
  --duration 55 \
  --output cyberpunk_story.json \
  --format json
```

## 📄 라이선스

MIT License

## 🤝 기여

Issues와 Pull Requests를 환영합니다!

## 📧 문의

프로젝트 관련 문의사항은 Issues를 통해 남겨주세요.

---

**AI Short Factory** - 당신의 스토리를 영화처럼 만들어드립니다 🎬✨
