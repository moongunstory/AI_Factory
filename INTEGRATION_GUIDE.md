# AI Short Factory - ComfyUI & WAN2.2 Integration Guide

## Architecture Overview

This integration adds **automatic vertical short video generation** to AI Short Factory, combining:

1. **llama-server** (llama.cpp) - Story & scene generation
2. **ComfyUI + SDXL** - Vertical image generation (1080×1920)
3. **WAN2.2** - Image-to-video (I2V) generation
4. **FFmpeg** - Video assembly & concatenation

### Pipeline Flow

```
User Input (Theme + Style)
    ↓
[1] llama-server → Story Breakdown
    ↓
    {
      "title": "...",
      "synopsis": "...",
      "scenes": [
        {
          "id": 1,
          "name": "...",
          "image_prompt": "...",  # For SDXL
          "video_prompt": "...",  # For WAN2.2
          "duration_sec": 2.5
        },
        ...
      ]
    }
    ↓
[2] ComfyUI (SDXL) → Generate vertical images per scene
    ↓
    output/images/{short_id}/scene_001.png
    output/images/{short_id}/scene_002.png
    ...
    ↓
[3] WAN2.2 (I2V) → Generate video clips per scene
    ↓
    output/video_segments/{short_id}/scene_001.mp4
    output/video_segments/{short_id}/scene_002.mp4
    ...
    ↓
[4] FFmpeg → Concatenate clips
    ↓
    output/final/{short_id}/short_final.mp4
```

---

## File Structure

### New Files Created

```
AI_shorts_factory/
├── src/
│   └── web/
│       └── services/              # NEW: Backend service modules
│           ├── __init__.py
│           ├── llama_client.py    # Wrapper for llama-server
│           ├── comfy_client.py    # ComfyUI HTTP client
│           ├── wan2_client.py     # WAN2.2 I2V client
│           └── pipeline.py        # Full orchestration
├── output/                        # NEW: Generated outputs
│   ├── images/
│   │   └── {short_id}/
│   │       ├── scene_001.png
│   │       └── scene_001.json     # Metadata
│   ├── video_segments/
│   │   └── {short_id}/
│   │       └── scene_001.mp4
│   └── final/
│       └── {short_id}/
│           └── short_final.mp4
└── INTEGRATION_GUIDE.md           # This file
```

### Modified Files

- `src/web/app.py` - Added 3 new API endpoints
- `src/web/templates/index.html` - Added Auto Short Generator tab
- `src/web/static/js/main.js` - Added UI logic for auto generation
- `requirements.txt` - Added Pillow, torch

---

## Setup Instructions

### Prerequisites

Ensure you have:
- **Python 3.11** (as per your environment)
- **Windows 11** with **RTX 5060 Ti** (16GB VRAM)
- **Git** installed

### Step 1: Install Python Dependencies

Navigate to your project root:

```bash
cd C:\Users\moong\Desktop\Project\AI_shorts_factory
```

Activate the main virtual environment:

```bash
.\engine\comfyui\venv\Scripts\activate
```

Install/update dependencies:

```bash
pip install -r requirements.txt
```

For PyTorch with CUDA 12.1 support:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 2: Install FFmpeg

Download FFmpeg for Windows:
- https://www.gyan.dev/ffmpeg/builds/

Extract and add `ffmpeg.exe` to your system PATH, or place it in:
```
C:\Users\moong\Desktop\Project\AI_shorts_factory\bin\ffmpeg.exe
```

Verify installation:

```bash
ffmpeg -version
```

### Step 3: Set Up ComfyUI

Ensure ComfyUI is installed at:

```
engine/comfyui/
```

Download SDXL models and place them in:

```
models/image/sdxl/
  ├── sdxl_base_1.0.safetensors
  └── sdxl_refiner_1.0.safetensors
```

You can download from:
- https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0

### Step 4: Set Up WAN2.2 (Optional)

Clone WAN2.2 repository into `engine/wan2.2/`:

```bash
cd engine
git clone https://github.com/microsoft/WAN2.2 wan2.2
cd wan2.2
```

Install WAN2.2 dependencies:

```bash
pip install -r requirements.txt
```

Download WAN2.2 I2V model and place it in:

```
models/video/wan2.2/
  └── Wan2.2-I2V-5B.safetensors
```

**Note:** If WAN2.2 is not available, the pipeline will fall back to using ffmpeg for simple zoom/pan effects.

### Step 5: Verify Repository Structure

Ensure your folder structure matches:

```
AI_shorts_factory/
├── run.bat
├── llama_server_manager.ps1
├── requirements.txt
├── models/
│   ├── image/
│   │   └── sdxl/
│   │       ├── sdxl_base_1.0.safetensors
│   │       └── sdxl_refiner_1.0.safetensors
│   └── video/
│       └── wan2.2/
│           └── Wan2.2-I2V-5B.safetensors
├── engine/
│   ├── comfyui/
│   │   ├── main.py
│   │   └── venv/
│   └── wan2.2/
└── src/
    └── web/
        ├── app.py
        ├── templates/
        └── services/
```

---

## Running the System

You need to run **three servers** in separate terminals:

### Terminal 1: llama-server

Start the llama-server:

```powershell
powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action start
```

Verify it's running:

```powershell
powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action status
```

Expected output:
```
✓ llama-server is running on http://127.0.0.1:8080
```

### Terminal 2: ComfyUI

Navigate to ComfyUI directory and activate venv:

```bash
cd engine\comfyui
.\venv\Scripts\activate
```

Start ComfyUI server:

```bash
python main.py --listen --port 8188
```

Expected output:
```
To see the GUI go to: http://127.0.0.1:8188
```

### Terminal 3: Flask Web UI

Activate venv and start Flask:

```bash
.\engine\comfyui\venv\Scripts\activate
python src/web/app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
```

---

## Using the Auto Short Generator

### 1. Open the Web UI

Navigate to:
```
http://127.0.0.1:5000
```

### 2. Switch to Auto Short Generator Tab

- Click the **"🚀 Auto Short Generator"** tab
- Or press **`2`** on your keyboard

### 3. Check Engine Health

Click **"🔍 Check Engines Status"** to verify:
- ✅ llama-server: Running
- ✅ ComfyUI: Running
- ⚠️ WAN2.2: Available (or fallback)

### 4. Configure Your Short

Fill in the form:

- **Theme** (required): e.g., "space adventure", "underwater mystery"
- **Visual Style**: Cinematic, Anime, Dark Fantasy, etc.
- **Scene Count**: 3-8 scenes (default: 4)
- **Title Hint** (optional): Suggest a title direction

### 5. Generate!

Click **"🚀 Generate Short (Auto)"**

The pipeline will:
1. Generate story & scene breakdown (10%)
2. Generate images per scene (20-50%)
3. Generate video clips per scene (50-85%)
4. Concatenate final video (85-100%)

### 6. View Results

Once complete, you'll see:
- **Title** & **Synopsis**
- **Scene thumbnails** (images)
- **Final vertical video** (embedded player)
- **Download link** for the MP4

---

## API Endpoints

### Health Check

**GET** `/api/health`

Response:
```json
{
  "success": true,
  "ok": true,
  "engines": {
    "llama_server": true,
    "comfyui": true,
    "wan22": false
  }
}
```

### Generate Short

**POST** `/api/shorts/generate`

Request:
```json
{
  "theme": "space adventure",
  "style": "cinematic",
  "scene_count": 4,
  "title_hint": "Lost in the Stars"
}
```

Response:
```json
{
  "success": true,
  "short_id": "20250103_143022_a7b3c9d1",
  "title": "Lost in the Stars",
  "synopsis": "A lone astronaut discovers...",
  "scenes": [
    {
      "id": 1,
      "name": "Drifting in Space",
      "image_path": "output/images/.../scene_001.png",
      "video_path": "output/video_segments/.../scene_001.mp4",
      "image_prompt": "...",
      "video_prompt": "...",
      "duration_sec": 2.5
    }
  ],
  "final_video_path": "output/final/.../short_final.mp4",
  "duration_sec": 10.0,
  "status": "done"
}
```

### Get Status

**GET** `/api/shorts/<short_id>/status`

Response:
```json
{
  "success": true,
  "short_id": "20250103_143022_a7b3c9d1",
  "status": "generating_images",
  "progress": 35,
  "current_step": "Generating image 2/4...",
  "error": null,
  "title": "Lost in the Stars",
  "scenes": [...]
}
```

---

## Testing with curl

### Health Check

```bash
curl http://127.0.0.1:5000/api/health
```

### Generate Short

```bash
curl -X POST http://127.0.0.1:5000/api/shorts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "underwater mystery",
    "style": "cinematic",
    "scene_count": 4
  }'
```

### Check Status

```bash
curl http://127.0.0.1:5000/api/shorts/20250103_143022_a7b3c9d1/status
```

---

## Code Architecture

### Service Modules

#### `src/web/services/llama_client.py`

High-level wrapper around the existing `LlamaClient` for story/scene generation.

Key method:
```python
def generate_story_breakdown(
    theme: str,
    style: str,
    scene_count: int
) -> Dict[str, Any]
```

#### `src/web/services/comfy_client.py`

ComfyUI HTTP client for SDXL image generation.

Key method:
```python
def generate_vertical_image(
    prompt: str,
    out_path: Path,
    steps_base: int = 25,
    steps_refiner: int = 15,
    cfg: float = 7.0
) -> Dict[str, Any]
```

Workflow:
1. Build SDXL workflow JSON (base + refiner, vertical 1080×1920)
2. Submit via `/prompt` endpoint
3. Poll `/history/{prompt_id}` for completion
4. Download image via `/view` endpoint

#### `src/web/services/wan2_client.py`

WAN2.2 wrapper for image-to-video generation.

Key method:
```python
def generate_scene_video(
    image_path: Path,
    prompt: str,
    out_path: Path,
    duration_sec: float = 2.5,
    fps: int = 24,
    motion_strength: float = 0.7
) -> None
```

Supports two modes:
1. **Direct Python API** (if WAN2.2 is properly installed)
2. **Subprocess/CLI** (fallback via WAN2.2 inference script)

If WAN2.2 is unavailable:
- Falls back to `generate_static_video_ffmpeg()` for simple zoom/pan

#### `src/web/services/pipeline.py`

Orchestrates the full workflow.

Key function:
```python
def generate_short(
    theme: str,
    style: str,
    scene_count: int
) -> Dict[str, Any]
```

Pipeline stages:
1. **Story generation** (10% progress)
2. **Image generation** (20-50%)
3. **Video generation** (50-85%)
4. **Concatenation** (85-100%)

---

## Troubleshooting

### llama-server not responding

```bash
powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action status
```

If not running:
```bash
powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action start
```

### ComfyUI not responding

Check if ComfyUI is running on port 8188:

```bash
curl http://127.0.0.1:8188/system_stats
```

If not, restart:
```bash
cd engine\comfyui
.\venv\Scripts\activate
python main.py --listen --port 8188
```

### SDXL models not found

Ensure models are in:
```
models/image/sdxl/sdxl_base_1.0.safetensors
models/image/sdxl/sdxl_refiner_1.0.safetensors
```

Download from Hugging Face if missing.

### WAN2.2 not available

If WAN2.2 fails to load, the pipeline will automatically fall back to ffmpeg-based static video generation.

To use WAN2.2:
1. Clone repo into `engine/wan2.2`
2. Install dependencies
3. Download model weights

### GPU/CUDA issues

Verify CUDA is available:

```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Should show "RTX 5060 Ti"
```

If False, reinstall PyTorch with CUDA support:

```bash
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### FFmpeg not found

Ensure ffmpeg is in PATH:

```bash
ffmpeg -version
```

If not found, download from https://www.gyan.dev/ffmpeg/builds/ and add to PATH.

---

## Performance Notes

### Expected Generation Times (RTX 5060 Ti, 16GB VRAM)

- **Story generation**: ~10-30 seconds
- **Image generation (SDXL)**: ~30-60 seconds per scene
- **Video generation (WAN2.2)**: ~60-120 seconds per scene
- **Concatenation**: ~5-10 seconds

Total for 4-scene short: **~5-10 minutes**

### Optimization Tips

1. **Reduce scene count** for faster results (3 scenes instead of 4-8)
2. **Lower SDXL steps** (base: 20, refiner: 10 instead of 25/15)
3. **Reduce WAN2.2 steps** (30 instead of 50)
4. **Use fallback mode** (skip WAN2.2, use ffmpeg static videos)

To adjust defaults, edit:
- `src/web/services/comfy_client.py` (SDXL steps)
- `src/web/services/wan2_client.py` (WAN2.2 steps)

---

## Future Enhancements

Recommended improvements:

1. **Async/Background Jobs**
   - Move pipeline to Celery/RQ for background processing
   - Add WebSocket for real-time progress updates

2. **Audio Integration**
   - Generate background music (e.g., via MusicGen)
   - Add TTS voiceover for narration

3. **Advanced Video Effects**
   - Scene transitions (fade, dissolve)
   - Text overlays (titles, captions)
   - Color grading

4. **Batch Generation**
   - Generate multiple variants with different styles
   - A/B testing for different prompts

5. **Model Optimization**
   - Use SDXL Turbo for faster generation
   - Quantize models for lower VRAM usage

---

## Summary

You now have a fully integrated pipeline:

✅ **llama-server** for story generation
✅ **ComfyUI + SDXL** for vertical images
✅ **WAN2.2** for video animation (with ffmpeg fallback)
✅ **FFmpeg** for video assembly
✅ **Flask Web UI** for one-click generation

All controlled via a simple web interface at **http://localhost:5000**!

**Next Steps:**
1. Start all three servers (llama, ComfyUI, Flask)
2. Open the web UI
3. Navigate to Auto Short Generator tab
4. Enter a theme and click "Generate Short (Auto)"
5. Wait for the magic to happen! ✨

Enjoy creating AI-powered vertical shorts! 🎬
