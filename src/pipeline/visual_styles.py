"""Visual style definitions for different themes."""
from typing import Dict, Any


class VisualStyleDefinitions:
    """Define global visual styles for different themes."""

    STYLES = {
        "dark_fantasy": {
            "name": "다크 판타지",
            "color_palette": "deep purples, blood reds, shadowy blacks, dim golden accents",
            "lighting": "volumetric god rays, dramatic rim lighting, low-key lighting, atmospheric fog",
            "camera": "cinematic 35mm, dramatic low angles, dutch angles for tension",
            "texture": "dark painterly style, high contrast, deep shadows, gothic aesthetic",
            "atmosphere": "ominous, mysterious, epic, foreboding",
            "consistency_tags": "consistent dark fantasy style, unified color grading, cohesive gothic atmosphere",
            "quality_tags": "masterpiece, best quality, ultra detailed, 8k, photorealistic, cinematic composition"
        },
        "anime": {
            "name": "애니메이션",
            "color_palette": "vibrant saturated colors, cel-shaded, bold outlines",
            "lighting": "anime-style lighting, dramatic highlights, soft shadows, backlit characters",
            "camera": "dynamic anime angles, dutch tilts, close-up reactions, wide establishing shots",
            "texture": "clean anime art style, sharp lines, flat colors with gradients, Studio Ghibli quality",
            "atmosphere": "expressive, dynamic, emotional, stylized",
            "consistency_tags": "consistent anime style, uniform character design, same animation quality",
            "quality_tags": "highly detailed anime art, professional animation quality, trending on pixiv, 4k anime"
        },
        "disney": {
            "name": "디즈니",
            "color_palette": "warm vibrant colors, magical glowing elements, rich saturated tones",
            "lighting": "soft diffused lighting, magical sparkles, warm golden hour, enchanting glow",
            "camera": "classic Disney cinematography, medium shots, gentle camera movements",
            "texture": "Disney 3D animation style, smooth polished surfaces, detailed textures, Pixar quality",
            "atmosphere": "whimsical, heartwarming, magical, family-friendly",
            "consistency_tags": "consistent Disney animation style, uniform character models, cohesive magical world",
            "quality_tags": "Disney animation quality, Pixar rendering, highly detailed 3D, 8k resolution"
        },
        "cinematic_realism": {
            "name": "영화적 사실주의",
            "color_palette": "natural color grading, subtle color correction, realistic tones",
            "lighting": "natural lighting, practical light sources, soft ambient occlusion, realistic shadows",
            "camera": "35mm film, shallow depth of field, professional cinematography, stabilized shots",
            "texture": "photorealistic, film grain, detailed textures, real-world materials",
            "atmosphere": "grounded, authentic, cinematic, professional",
            "consistency_tags": "consistent cinematic look, unified color grading, same film stock aesthetic",
            "quality_tags": "8k uhd, photorealistic, cinema quality, ultra detailed, professional photography"
        },
        "game_cinematic": {
            "name": "게임 시네마틱",
            "color_palette": "stylized game colors, enhanced saturation, fantasy-realism blend",
            "lighting": "dramatic game lighting, enhanced contrast, volumetric effects, god rays",
            "camera": "game engine cinematography, dynamic angles, action camera movements",
            "texture": "Unreal Engine 5 quality, detailed PBR materials, ray-traced reflections",
            "atmosphere": "epic, heroic, action-packed, immersive",
            "consistency_tags": "consistent game cinematic style, unified rendering quality, cohesive game aesthetic",
            "quality_tags": "Unreal Engine 5, ray tracing, 8k game graphics, AAA quality, highly detailed"
        },
        "cyber_fantasy": {
            "name": "사이버 판타지",
            "color_palette": "neon blues, electric purples, hot pinks, deep blacks, glowing accents",
            "lighting": "neon lighting, holographic projections, volumetric fog, backlit neon signs",
            "camera": "wide-angle cyberpunk shots, dutch angles, rain-soaked reflections",
            "texture": "cyberpunk aesthetic, holographic effects, glitch art elements, futuristic materials",
            "atmosphere": "futuristic, dystopian, high-tech, mysterious",
            "consistency_tags": "consistent cyberpunk style, unified neon aesthetic, cohesive futuristic world",
            "quality_tags": "cyberpunk 2077 style, blade runner aesthetic, 8k, highly detailed, ray traced"
        },
        "horror": {
            "name": "호러",
            "color_palette": "desaturated colors, sickly greens, deep shadows, blood red accents",
            "lighting": "harsh shadows, flickering lights, silhouette lighting, unsettling contrasts",
            "camera": "handheld shaky cam, tight claustrophobic framing, sudden perspective shifts",
            "texture": "gritty, grimy textures, organic horror, disturbing details",
            "atmosphere": "terrifying, unsettling, tense, nightmarish",
            "consistency_tags": "consistent horror atmosphere, unified terror aesthetic, cohesive nightmare world",
            "quality_tags": "horror movie quality, highly detailed, psychological horror, 4k cinematic"
        },
        "fantasy_adventure": {
            "name": "판타지 어드벤처",
            "color_palette": "rich earth tones, magical blues, golden sunlight, mystical purples",
            "lighting": "magical lighting effects, soft natural light, enchanted glows, epic sunsets",
            "camera": "epic wide shots, hero angles, sweeping camera movements",
            "texture": "high fantasy art style, detailed environments, magical effects, epic scale",
            "atmosphere": "adventurous, magical, epic, wonder-filled",
            "consistency_tags": "consistent fantasy world, unified magical aesthetic, cohesive adventure tone",
            "quality_tags": "epic fantasy art, Lord of the Rings quality, 8k, highly detailed, cinematic"
        },
        "sci_fi": {
            "name": "공상과학",
            "color_palette": "cool blues, sterile whites, metallic silvers, holographic elements",
            "lighting": "clean sci-fi lighting, LED strips, holographic displays, clinical bright lights",
            "camera": "sleek sci-fi cinematography, smooth camera movements, futuristic angles",
            "texture": "clean sci-fi materials, advanced technology surfaces, holographic interfaces",
            "atmosphere": "futuristic, advanced, clean, technological",
            "consistency_tags": "consistent sci-fi aesthetic, unified technology design, cohesive future world",
            "quality_tags": "high-end sci-fi, Star Trek quality, 8k, photorealistic, advanced CGI"
        },
        "retro_synthwave": {
            "name": "레트로 신스웨이브",
            "color_palette": "hot pink, electric blue, purple gradients, orange sunsets, neon grid",
            "lighting": "80s neon lighting, sunset gradients, grid floor reflections, retro glow",
            "camera": "80s music video style, steady tracking shots, retro effects",
            "texture": "vaporwave aesthetic, retro-futuristic, grid patterns, chrome reflections",
            "atmosphere": "nostalgic, dreamy, retro-futuristic, energetic",
            "consistency_tags": "consistent synthwave style, unified 80s aesthetic, cohesive retro theme",
            "quality_tags": "synthwave art, 80s aesthetic, vaporwave quality, 4k, highly stylized"
        }
    }

    @classmethod
    def get_style(cls, theme: str) -> Dict[str, Any]:
        """Get visual style definition for a theme.

        Args:
            theme: Theme name (e.g., 'dark_fantasy', 'anime')

        Returns:
            Dictionary with style parameters
        """
        if theme not in cls.STYLES:
            # Default to cinematic_realism if theme not found
            return cls.STYLES["cinematic_realism"]
        return cls.STYLES[theme]

    @classmethod
    def get_global_style_prompt(cls, theme: str) -> str:
        """Generate global style prompt string for Stable Diffusion.

        Args:
            theme: Theme name

        Returns:
            Formatted style prompt string
        """
        style = cls.get_style(theme)

        return (
            f"{style['color_palette']}, "
            f"{style['lighting']}, "
            f"{style['camera']}, "
            f"{style['texture']}, "
            f"{style['atmosphere']} atmosphere, "
            f"{style['consistency_tags']}, "
            f"{style['quality_tags']}"
        )

    @classmethod
    def list_themes(cls) -> list:
        """List all available themes.

        Returns:
            List of theme names
        """
        return list(cls.STYLES.keys())

    @classmethod
    def get_theme_info(cls, theme: str) -> str:
        """Get human-readable theme information.

        Args:
            theme: Theme name

        Returns:
            Formatted theme description
        """
        if theme not in cls.STYLES:
            return f"Theme '{theme}' not found. Available themes: {', '.join(cls.list_themes())}"

        style = cls.STYLES[theme]
        return f"{style['name']} - {style['atmosphere']}"
