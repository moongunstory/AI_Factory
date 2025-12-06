"""Film Layer - Analyzes scene emotion/action and applies cinematic grammar rules.

This layer sits between Story Layer and Camera Layer, determining:
- Scene emotional tone (horror, action, tension, calm, etc.)
- Cinematic lighting style
- Color grading approach
- Recommended camera angles and movements
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class SceneEmotion(Enum):
    """Scene emotional/narrative types."""
    HORROR = "horror"
    TENSION = "tension"
    ACTION = "action"
    CHASE = "chase"
    CALM = "calm"
    WONDER = "wonder"
    SADNESS = "sadness"
    JOY = "joy"
    MYSTERY = "mystery"
    DIALOGUE = "dialogue"
    DISCOVERY = "discovery"
    BATTLE = "battle"


# ====================================================================
# Film Grammar Rule Table
# Maps scene emotions to cinematic techniques
# ====================================================================
FILM_GRAMMAR_RULES = {
    SceneEmotion.HORROR: {
        "lighting": "low-key lighting, harsh shadows, flickering light sources, silhouette lighting",
        "color_grading": "desaturated colors, sickly greens, deep blacks, blood red accents",
        "preferred_angles": ["dutch", "low", "extreme-low"],
        "preferred_movements": ["handheld", "shaky", "slow-creep"],
        "atmosphere": "terrifying, unsettling, claustrophobic",
        "composition": "tight framing, off-center subjects, negative space",
    },
    SceneEmotion.TENSION: {
        "lighting": "dramatic side lighting, long shadows, high contrast, chiaroscuro",
        "color_grading": "muted tones, cool blues, deep shadows",
        "preferred_angles": ["dutch", "low", "high"],
        "preferred_movements": ["slow-push-in", "static", "creeping-dolly"],
        "atmosphere": "suspenseful, ominous, anticipatory",
        "composition": "asymmetric framing, leading lines, depth",
    },
    SceneEmotion.ACTION: {
        "lighting": "high contrast, dramatic rim lighting, dynamic highlights",
        "color_grading": "saturated colors, vivid contrast, enhanced clarity",
        "preferred_angles": ["wide", "low", "dynamic-dutch"],
        "preferred_movements": ["fast-pan", "tracking", "whip-pan", "crane"],
        "atmosphere": "intense, kinetic, explosive",
        "composition": "dynamic diagonals, motion blur, wide framing",
    },
    SceneEmotion.CHASE: {
        "lighting": "motion blur friendly, high shutter speed simulation, backlit",
        "color_grading": "enhanced saturation, speed ramping color shift",
        "preferred_angles": ["tracking", "low", "wide"],
        "preferred_movements": ["fast-tracking", "handheld", "steadicam-run"],
        "atmosphere": "urgent, desperate, high-speed",
        "composition": "leading space, motion lines, perspective shift",
    },
    SceneEmotion.CALM: {
        "lighting": "soft natural light, gentle diffusion, warm tones",
        "color_grading": "natural colors, slight warmth, balanced exposure",
        "preferred_angles": ["eye-level", "slight-high"],
        "preferred_movements": ["static", "slow-pan", "gentle-drift"],
        "atmosphere": "peaceful, serene, contemplative",
        "composition": "balanced framing, rule of thirds, symmetry",
    },
    SceneEmotion.WONDER: {
        "lighting": "magical golden hour, god rays, ethereal glow, soft rim light",
        "color_grading": "warm golden tones, enhanced luminance, dreamy pastels",
        "preferred_angles": ["low", "wide", "sweeping"],
        "preferred_movements": ["crane-up", "orbit", "slow-reveal"],
        "atmosphere": "awe-inspiring, magical, epic",
        "composition": "epic scale, foreground interest, depth layers",
    },
    SceneEmotion.SADNESS: {
        "lighting": "soft overcast light, minimal contrast, gentle shadows",
        "color_grading": "desaturated, cool blues, muted grays",
        "preferred_angles": ["eye-level", "slight-high"],
        "preferred_movements": ["slow-drift", "static", "gentle-pan"],
        "atmosphere": "melancholic, somber, reflective",
        "composition": "isolation, negative space, distant subjects",
    },
    SceneEmotion.JOY: {
        "lighting": "bright natural light, soft fill, warm highlights",
        "color_grading": "vibrant colors, enhanced saturation, warm tones",
        "preferred_angles": ["eye-level", "slight-low"],
        "preferred_movements": ["dynamic-pan", "joyful-bounce", "sweeping"],
        "atmosphere": "uplifting, energetic, bright",
        "composition": "open framing, centered subjects, energetic",
    },
    SceneEmotion.MYSTERY: {
        "lighting": "fog, volumetric lighting, partial reveal, obscured sources",
        "color_grading": "cool tones, purple shadows, mystery blues",
        "preferred_angles": ["obscured", "partial-reveal", "dutch"],
        "preferred_movements": ["slow-reveal", "creeping", "investigation-track"],
        "atmosphere": "enigmatic, curious, uncertain",
        "composition": "foreground obstruction, partial framing, depth",
    },
    SceneEmotion.DIALOGUE: {
        "lighting": "natural conversational lighting, soft key light, fill light",
        "color_grading": "natural skin tones, balanced color",
        "preferred_angles": ["eye-level", "slight-over-shoulder"],
        "preferred_movements": ["static", "subtle-adjustment"],
        "atmosphere": "intimate, conversational, focused",
        "composition": "medium shots, headroom, eye-line",
    },
    SceneEmotion.DISCOVERY: {
        "lighting": "reveal lighting, dramatic unveiling, spotlight effect",
        "color_grading": "contrast shift, color pop on subject",
        "preferred_angles": ["reveal", "wide-to-close"],
        "preferred_movements": ["push-in", "reveal-pan", "crane-down"],
        "atmosphere": "revelatory, significant, impactful",
        "composition": "subject emergence, background to foreground",
    },
    SceneEmotion.BATTLE: {
        "lighting": "harsh dramatic light, smoke and particles, fire glow",
        "color_grading": "war tones, gritty saturation, dust and smoke haze",
        "preferred_angles": ["wide-chaos", "low-hero", "dynamic"],
        "preferred_movements": ["chaotic-handheld", "sweep", "impact-shake"],
        "atmosphere": "chaotic, visceral, overwhelming",
        "composition": "layers of action, depth of conflict, environmental hazards",
    },
}


# ====================================================================
# Emotion Detection Keywords
# ====================================================================
EMOTION_KEYWORDS = {
    SceneEmotion.HORROR: [
        "scream", "terror", "ghost", "monster", "fear", "frightening",
        "nightmare", "creepy", "haunted", "darkness", "evil", "sinister",
        "blood", "corpse", "death", "lurking", "shadows"
    ],
    SceneEmotion.TENSION: [
        "suspense", "waiting", "anticipation", "cautious", "careful",
        "nervous", "uneasy", "tense", "quiet", "still", "watching",
        "listening", "footsteps", "approaching"
    ],
    SceneEmotion.ACTION: [
        "fight", "punch", "kick", "attack", "strike", "combat",
        "explosion", "crash", "smash", "break", "destroy", "battle",
        "shoot", "fire", "blast", "impact"
    ],
    SceneEmotion.CHASE: [
        "chase", "run", "pursuit", "escape", "flee", "racing",
        "sprint", "dash", "rush", "hurry", "fast", "speed"
    ],
    SceneEmotion.CALM: [
        "peaceful", "calm", "quiet", "serene", "tranquil", "rest",
        "relax", "gentle", "soft", "still", "meditate", "breathe"
    ],
    SceneEmotion.WONDER: [
        "wonder", "awe", "amazing", "beautiful", "magnificent", "stunning",
        "breathtaking", "magical", "enchanted", "mesmerizing", "spectacular",
        "epic", "grand", "vast", "majestic"
    ],
    SceneEmotion.SADNESS: [
        "sad", "crying", "tears", "grief", "loss", "mourning",
        "sorrow", "despair", "lonely", "empty", "regret", "goodbye"
    ],
    SceneEmotion.JOY: [
        "happy", "joy", "laugh", "smile", "celebration", "victory",
        "triumph", "excited", "cheerful", "bright", "fun", "delight"
    ],
    SceneEmotion.MYSTERY: [
        "mystery", "unknown", "strange", "curious", "investigate",
        "clue", "secret", "hidden", "puzzle", "enigma", "cryptic"
    ],
    SceneEmotion.DIALOGUE: [
        "talk", "speak", "conversation", "discuss", "tell", "say",
        "ask", "answer", "explain", "argue", "whisper", "shout"
    ],
    SceneEmotion.DISCOVERY: [
        "discover", "find", "reveal", "uncover", "realize", "understand",
        "see", "notice", "appear", "emerge", "unveil", "expose"
    ],
    SceneEmotion.BATTLE: [
        "war", "battle", "army", "soldiers", "warriors", "clash",
        "siege", "assault", "defend", "charge", "invasion", "combat"
    ],
}


class FilmLayer:
    """Analyzes scene content and applies cinematic grammar rules."""

    def __init__(self):
        """Initialize the Film Layer."""
        logger.info("FilmLayer initialized")

    def analyze_scene_emotion(
        self,
        scene_description: str,
        beat_description: Optional[str] = None
    ) -> SceneEmotion:
        """Analyze a scene to determine its primary emotional/narrative type.

        Uses keyword matching to detect scene emotion. Combines both the
        scene description and the story beat for better accuracy.

        Args:
            scene_description: The scene's visual description
            beat_description: Optional story beat/plot point description

        Returns:
            SceneEmotion enum value
        """
        combined_text = f"{scene_description} {beat_description or ''}".lower()

        # Score each emotion type based on keyword matches
        scores: Dict[SceneEmotion, int] = {emotion: 0 for emotion in SceneEmotion}

        for emotion, keywords in EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    scores[emotion] += 1

        # Get the emotion with highest score
        if max(scores.values()) > 0:
            detected_emotion = max(scores, key=scores.get)
            logger.debug(f"Detected emotion: {detected_emotion.value} (score: {scores[detected_emotion]})")
            return detected_emotion

        # Default to CALM if no keywords matched
        logger.debug("No emotion keywords matched, defaulting to CALM")
        return SceneEmotion.CALM

    def get_film_style(
        self,
        scene_emotion: SceneEmotion
    ) -> Dict[str, Any]:
        """Get cinematic style guidelines for a scene emotion.

        Args:
            scene_emotion: The scene's emotional type

        Returns:
            Dictionary with film style parameters:
            {
                "emotion": str,
                "lighting": str,
                "color_grading": str,
                "preferred_angles": List[str],
                "preferred_movements": List[str],
                "atmosphere": str,
                "composition": str
            }
        """
        if scene_emotion not in FILM_GRAMMAR_RULES:
            logger.warning(f"No film grammar rules for {scene_emotion}, using CALM")
            scene_emotion = SceneEmotion.CALM

        style = FILM_GRAMMAR_RULES[scene_emotion].copy()
        style["emotion"] = scene_emotion.value

        return style

    def apply_film_layer(
        self,
        scene_description: str,
        beat_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete film layer analysis for a scene.

        Convenience method that combines emotion detection and style retrieval.

        Args:
            scene_description: Scene visual description
            beat_description: Optional story beat

        Returns:
            Complete film style dictionary
        """
        emotion = self.analyze_scene_emotion(scene_description, beat_description)
        film_style = self.get_film_style(emotion)

        logger.info(f"Film layer applied: {emotion.value}")
        return film_style

    def batch_analyze_scenes(
        self,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze multiple scenes and add film style to each.

        Args:
            scenes: List of scene dictionaries with 'description' or 'summary' keys

        Returns:
            Scenes list with added 'film_style' key for each scene
        """
        logger.info(f"Analyzing film styles for {len(scenes)} scenes")

        for scene in scenes:
            description = scene.get("description") or scene.get("summary", "")
            beat = scene.get("beat_description", "")

            film_style = self.apply_film_layer(description, beat)
            scene["film_style"] = film_style

        logger.info("Film layer analysis complete for all scenes")
        return scenes
