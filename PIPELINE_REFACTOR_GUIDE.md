# Multi-Layer Prompt Generation Pipeline

## 📋 Overview

The AI Short Factory prompt generation pipeline has been refactored from a single-layer structure to a **multi-layer architecture** for enhanced cinematic quality and shot variety.

### Before: Single Layer
```
Story Expansion → Plot Beats → LLM Generates Prompts
                               (All in one step, limited control)
```

### After: Multi-Layer
```
Story Layer    → Expands story & extracts beats
    ↓
Film Layer     → Analyzes emotion & applies cinematic grammar
    ↓
Camera Layer   → Assigns shot types, angles, lenses, movements
    ↓
Prompt Layer   → Builds enhanced prompts with all layers
```

---

## 🎯 Key Improvements

### Problem Solved
- **Before**: Scenes had uniform composition, lack of camera variety
- **After**: Each scene has unique camera work and cinematic grammar

### Benefits
1. **Automatic Scene Variety**: Different shot types, angles, and movements per scene
2. **Emotion-Driven Cinematography**: Horror → dutch angles, low-key lighting
3. **Professional Camera Work**: Proper lens choices for each shot type
4. **Global Consistency**: Theme-wide visual style with per-scene variation

---

## 🧩 Architecture

### 1. Story Layer (`story_expander.py`)
**Purpose**: Convert simple ideas into detailed stories

- Expands 1-2 sentence ideas into 300-500 word stories
- Breaks stories into plot beats (8-20 beats)
- **No changes** - existing module works well

### 2. Film Layer (`film_layer.py`) 🆕
**Purpose**: Apply cinematic grammar based on scene emotion

**Features**:
- **Emotion Detection**: Analyzes scene content for 12 emotion types
  - Horror, Tension, Action, Chase, Calm, Wonder, Sadness, Joy, Mystery, Dialogue, Discovery, Battle
- **Cinematic Grammar Rules**: Each emotion has specific:
  - Lighting style (low-key, high contrast, soft natural, etc.)
  - Color grading (desaturated horror, vibrant action, etc.)
  - Preferred camera angles (dutch for horror, low for action, etc.)
  - Preferred movements (handheld for horror, tracking for chase, etc.)

**Example**:
```python
from src.pipeline import FilmLayer, SceneEmotion

film_layer = FilmLayer()

# Analyze scene
scene = "Dark corridor with blood on walls, shadows moving"
emotion = film_layer.analyze_scene_emotion(scene)
# → SceneEmotion.HORROR

# Get cinematic grammar
style = film_layer.get_film_style(emotion)
# → {
#     "lighting": "low-key lighting, harsh shadows, flickering...",
#     "color_grading": "desaturated, sickly greens, blood red accents",
#     "preferred_angles": ["dutch", "low", "extreme-low"],
#     "preferred_movements": ["handheld", "shaky", "slow-creep"],
#     ...
#   }
```

### 3. Camera Layer (`camera_layer.py`) 🆕
**Purpose**: Assign specific camera technical specifications

**Features**:
- **Shot Types**: EWS, WS, MWS, MS, MCU, CU, ECU
- **Camera Angles**: eye-level, low, high, dutch, overhead, worm, etc.
- **Lens Focal Lengths**: 14mm to 135mm (matched to shot type)
- **Camera Movements**: static, pan, dolly, tracking, crane, handheld, etc.
- **Variety Engine**: Prevents consecutive scenes from being identical

**Example**:
```python
from src.pipeline import CameraLayer

camera_layer = CameraLayer(ensure_variety=True)

# Assign specs for scene 1
specs = camera_layer.assign_camera_specs(
    scene_number=1,
    film_style={"preferred_angles": ["low", "dutch"]}
)
# → {
#     "shot_type": "MS",
#     "shot_type_name": "medium shot",
#     "angle": "low",
#     "angle_description": "low angle, looking up",
#     "lens": "50mm",
#     "lens_description": "50mm lens, standard perspective",
#     "movement": "dolly-in",
#     "movement_description": "dolly in, smooth push toward subject"
#   }
```

### 4. Prompt Layer (Enhanced `prompt_generator.py`)
**Purpose**: Build final prompts with all layers integrated

**Enhanced Pipeline**:
1. Story → Plot Beats (existing)
2. LLM generates basic scene descriptions (existing)
3. **Film Layer** analyzes and adds cinematic grammar
4. **Camera Layer** assigns technical specs
5. **Prompt Builder** combines all layers into Stable Diffusion prompts

**Prompt Structure**:
```
[Scene Description] + [Camera Specs] + [Film Style] + [Global Theme] + [Quality Tags]
```

**Example Output**:
```
"Abandoned space station corridor with flickering lights and shadows,
medium shot, low angle looking up, 50mm lens standard perspective,
slow creep camera movement, low-key lighting harsh shadows flickering light sources,
desaturated colors sickly greens deep blacks,
tight framing off-center subjects negative space,
terrifying unsettling claustrophobic atmosphere,
consistent horror atmosphere unified terror aesthetic cohesive nightmare world,
horror movie quality highly detailed psychological horror 4k cinematic"
```

### 5. Global Style Config (`visual_styles.py` enhanced)
**Purpose**: Maintain project-wide visual consistency

**Features**:
- **10 Pre-defined Themes**: dark_fantasy, horror, anime, disney, cinematic_realism, game_cinematic, cyber_fantasy, sci_fi, retro_synthwave, fantasy_adventure
- **Custom Overrides**: color_tone, camera_base, film_texture
- **Layer Control**: Enable/disable Film and Camera layers

**Example**:
```python
from src.pipeline import GlobalStyleConfig

# Quick theme-based config
config = GlobalStyleConfig.from_theme("horror")

# With custom overrides
config = GlobalStyleConfig(
    theme="horror",
    color_tone="toxic yellow and green",
    film_texture="heavy grain",
    enable_film_layer=True,
    enable_camera_layer=True
)

# Use in prompt generation
global_style = config.get_global_style_dict()
result = prompt_generator.generate(
    expanded_story=story,
    global_style=global_style
)
```

---

## 🔧 Usage

### Basic Usage (All Layers Enabled)
```python
from src.pipeline import (
    StoryExpander,
    PromptGenerator,
    GlobalStyleConfig
)

# 1. Setup
config = GlobalStyleConfig.from_theme("horror")
expander = StoryExpander()
generator = PromptGenerator(
    enable_film_layer=True,
    enable_camera_layer=True
)

# 2. Expand story
story = expander.expand("A lone astronaut in abandoned station")

# 3. Generate prompts
result = generator.generate(
    expanded_story=story,
    global_style=config.get_global_style_dict()
)

# 4. Access results
for scene in result['scenes']:
    print(f"Scene {scene['scene_number']}:")
    print(f"  Emotion: {scene['film_style']['emotion']}")
    print(f"  Shot: {scene['camera_style']['shot_type']}")
    print(f"  Prompt: {scene['prompt_en']}")
```

### Legacy Mode (Film/Camera Layers Disabled)
```python
# For backward compatibility
generator = PromptGenerator(
    enable_film_layer=False,
    enable_camera_layer=False
)

# Works exactly like old version
result = generator.generate(expanded_story)
```

---

## 📊 Output Format

Each scene now includes:

```json
{
  "scene_number": 1,
  "description": "Astronaut explores dark corridor",
  "duration": 3.5,

  "film_style": {
    "emotion": "horror",
    "lighting": "low-key lighting, harsh shadows",
    "color_grading": "desaturated, sickly greens",
    "preferred_angles": ["dutch", "low"],
    "preferred_movements": ["handheld", "shaky"],
    "atmosphere": "terrifying, unsettling",
    "composition": "tight framing, off-center"
  },

  "camera_style": {
    "shot_type": "MS",
    "shot_type_name": "medium shot",
    "angle": "dutch",
    "angle_description": "dutch angle, tilted horizon",
    "lens": "50mm",
    "lens_description": "50mm lens, standard perspective",
    "movement": "handheld",
    "movement_description": "handheld camera, natural shake"
  },

  "prompt_en": "[Enhanced prompt with all layers]"
}
```

---

## 🎬 Cinematic Grammar Rules

### Emotion → Film Style Mapping

| Emotion | Lighting | Color | Angles | Movement |
|---------|----------|-------|--------|----------|
| **Horror** | Low-key, flickering | Desaturated, greens | Dutch, low | Handheld, shaky |
| **Action** | High contrast, rim | Saturated, vivid | Wide, low | Fast pan, tracking |
| **Chase** | Motion blur friendly | Enhanced saturation | Tracking, low | Fast tracking, handheld |
| **Calm** | Soft natural | Natural, warm | Eye-level | Static, slow pan |
| **Wonder** | Golden hour, god rays | Warm golden | Low, wide | Crane up, orbit |
| **Tension** | Chiaroscuro | Muted, cool blues | Dutch, high | Slow push-in |

Full rules in `src/pipeline/film_layer.py`

---

## 🧪 Testing

### Unit Tests
```bash
python3 -m py_compile src/pipeline/film_layer.py
python3 -m py_compile src/pipeline/camera_layer.py
python3 -m py_compile src/pipeline/prompt_generator.py
python3 -m py_compile src/pipeline/visual_styles.py
```

### Integration Test
```bash
python3 test_multi_layer_pipeline.py
```

---

## 📁 Files Modified/Created

### New Files
- `src/pipeline/film_layer.py` - Film Layer with emotion detection and cinematic grammar
- `src/pipeline/camera_layer.py` - Camera Layer with shot/angle/lens/movement assignment
- `test_multi_layer_pipeline.py` - Integration test script
- `test_layers_unit.py` - Unit test script
- `PIPELINE_REFACTOR_GUIDE.md` - This document

### Modified Files
- `src/pipeline/prompt_generator.py` - Integrated Film and Camera layers
- `src/pipeline/visual_styles.py` - Added GlobalStyleConfig
- `src/pipeline/__init__.py` - Export new modules

---

## 🔮 Future Enhancements

1. **LLM-Based Emotion Detection**: Use LLM for more nuanced emotion analysis
2. **Scene Transition Rules**: Smooth camera transitions between scenes
3. **Character-Aware Camera**: Adjust shots based on character positions
4. **Custom Film Grammars**: User-defined cinematic rules
5. **Shot List Export**: Generate professional shot lists for reference

---

## 📝 Notes

- **Backward Compatible**: Can disable new layers for legacy behavior
- **Deterministic Variety**: Uses scene numbers as seeds for reproducible results
- **Performance**: No additional LLM calls - rule-based processing is fast
- **Extensible**: Easy to add new emotions, shot types, or camera movements

---

## 🎯 Summary

The multi-layer architecture transforms the pipeline from:
- ❌ LLM generates everything → uniform, unpredictable
- ✅ Structured layers → varied, professional, controllable

**Result**: Every scene now has unique, emotion-appropriate cinematography while maintaining overall visual consistency.
