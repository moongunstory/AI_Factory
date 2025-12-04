# AI Short Factory - Backend Services Guide

## 🚀 Quick Start

**단 하나의 명령어로 모든 서비스 시작:**

```batch
run.bat
```

이 명령어는 자동으로:
- ✅ llama-server (LLM) 시작
- ✅ ComfyUI (이미지 생성) 시작
- ✅ Flask Web UI 시작
- ✅ 브라우저 자동 실행

## 📋 서비스 관리

### 모든 서비스 시작
```batch
run.bat
```

또는 수동으로:
```batch
python src/manage_server.py start all
```

### 모든 서비스 종료
```batch
stop.bat
```

또는:
```batch
python src/manage_server.py stop all
```

### 서비스 상태 확인
```batch
status.bat
```

또는:
```batch
python src/manage_server.py status
```

### 개별 서비스 관리

**llama-server만:**
```batch
python src/manage_server.py start llama
python src/manage_server.py stop llama
```

**ComfyUI만:**
```batch
python src/manage_server.py start comfyui
python src/manage_server.py stop comfyui
```

### 서비스 재시작
```batch
python src/manage_server.py restart all
python src/manage_server.py restart llama
python src/manage_server.py restart comfyui
```

### 고아 프로세스 정리
```batch
python src/manage_server.py cleanup
```

## 🌐 서비스 포트

| 서비스 | 포트 | URL |
|--------|------|-----|
| Web UI | 5000 | http://localhost:5000 |
| llama-server | 8080 | http://localhost:8080 |
| ComfyUI | 8188 | http://localhost:8188 |

## 📁 로그 파일 위치

모든 로그는 `output/logs/` 디렉토리에 저장됩니다:

```
output/logs/
├── llama_server.out.log      # llama-server 표준 출력
├── llama_server.err.log      # llama-server 에러 로그
├── comfyui_server.out.log    # ComfyUI 표준 출력
└── comfyui_server.err.log    # ComfyUI 에러 로그
```

## 🔧 문제 해결

### 서비스가 시작되지 않는 경우

1. **의존성 확인:**
   ```batch
   pip install -r requirements.txt
   ```

2. **포트 충돌 확인:**
   - 8080, 8188, 5000 포트가 사용 중인지 확인
   - 다른 프로그램이 해당 포트를 사용하고 있다면 종료

3. **고아 프로세스 정리:**
   ```batch
   python src/manage_server.py cleanup
   ```

4. **로그 확인:**
   ```batch
   type output\logs\llama_server.err.log
   type output\logs\comfyui_server.err.log
   ```

### ComfyUI가 없는 경우

ComfyUI가 `engine/comfyui/` 디렉토리에 설치되어 있어야 합니다.

**설치 방법:**
```batch
cd engine
git clone https://github.com/comfyanonymous/ComfyUI.git comfyui
cd comfyui
pip install -r requirements.txt
```

**SDXL 모델 설치:**
- `sd_xl_base_1.0.safetensors` → `engine/comfyui/models/checkpoints/`
- `sd_xl_refiner_1.0.safetensors` → `engine/comfyui/models/checkpoints/`

### llama-server가 시작되지 않는 경우

1. **모델 파일 확인:**
   ```
   models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf
   ```

2. **llama-server 실행 파일 확인:**
   ```
   engine/llama.cpp/build/bin/Release/llama-server.exe
   ```

3. **GPU 드라이버 확인:**
   - NVIDIA GPU가 있는 경우 최신 드라이버 설치
   - CUDA 툴킷 설치 권장

## 💡 사용 팁

### 백그라운드 실행
Flask Web UI는 Ctrl+C로 종료해도 **백엔드 서비스는 계속 실행됩니다.**

이렇게 하면:
- 웹 UI를 재시작해도 모델 로딩 시간이 없음
- 여러 웹 UI 인스턴스를 동시에 실행 가능 (다른 포트 사용)

### 완전 종료
모든 것을 종료하려면:
```batch
stop.bat
```

### 빠른 재시작
웹 UI만 재시작 (백엔드는 유지):
- Flask를 Ctrl+C로 종료
- `python src/web/app.py`로 재시작

전체 재시작 (모든 서비스):
```batch
python src/manage_server.py restart all
```

## 🎬 워크플로우

### 1. 처음 시작
```batch
run.bat
```
→ 모든 서비스가 자동으로 시작되고 브라우저가 열립니다.

### 2. 영상 제작
1. Web UI에서 스토리 입력
2. Step 3: 프롬프트 생성
3. Step 4: 이미지 생성 (ComfyUI 자동 사용)
4. 원하는 이미지 선택/재생성
5. 저장 및 완료

### 3. 종료
```batch
stop.bat
```
→ 모든 백엔드 서비스와 Flask가 종료됩니다.

## 📊 시스템 요구사항

### 최소 사양
- **OS**: Windows 10/11
- **RAM**: 16GB
- **GPU**: NVIDIA GPU with 8GB+ VRAM (권장)
- **Storage**: 20GB+ 여유 공간

### 권장 사양
- **RAM**: 32GB
- **GPU**: NVIDIA RTX 3060 이상 (12GB+ VRAM)
- **Storage**: SSD with 50GB+ 여유 공간

## 🔒 보안

### 로컬 전용
모든 서비스는 `127.0.0.1` (localhost)에서만 실행됩니다.
외부에서 접근할 수 없으므로 안전합니다.

### 방화벽
필요한 경우 방화벽에서 다음 포트를 허용:
- 5000 (Flask)
- 8080 (llama-server)
- 8188 (ComfyUI)

## 📚 추가 정보

- **프로젝트 홈**: [GitHub Repository]
- **문제 보고**: [GitHub Issues]
- **문서**: `docs/` 디렉토리 참조
