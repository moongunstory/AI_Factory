"""Camera Layer - Assigns specific camera techniques for each scene.

This layer determines:
- Shot type (EWS, WS, MS, CU, etc.)
- Camera angle (low, high, dutch, etc.)
- Lens focal length (24mm, 35mm, 50mm, etc.)
- Camera movement (static, pan, dolly, etc.)

Ensures variety across scenes while respecting Film Layer recommendations.
"""
from typing import Dict, Any, List, Optional
import random
from ..common.logger import setup_logger

logger = setup_logger(__name__)


# ====================================================================
# Camera Specification Pools
# ====================================================================

# Shot Types (distance from subject)
SHOT_TYPES = {
    "EWS": "extreme wide shot",
    "WS": "wide shot",
    "MWS": "medium wide shot",
    "MS": "medium shot",
    "MCU": "medium close-up",
    "CU": "close-up",
    "ECU": "extreme close-up",
}

# Camera Angles (vertical position)
CAMERA_ANGLES = {
    "extreme-low": "extreme low angle, looking up dramatically",
    "low": "low angle, looking up",
    "eye-level": "eye level angle",
    "high": "high angle, looking down",
    "overhead": "overhead angle, bird's eye view",
    "dutch": "dutch angle, tilted horizon",
    "worm": "worm's eye view, ground level",
}

# Lens Focal Lengths (perspective characteristics)
LENS_FOCAL_LENGTHS = {
    "14mm": "ultra-wide 14mm lens, distorted perspective",
    "24mm": "wide-angle 24mm lens",
    "35mm": "35mm lens, natural perspective",
    "50mm": "50mm lens, standard perspective",
    "85mm": "85mm lens, portrait perspective",
    "100mm": "100mm lens, compressed perspective",
    "135mm": "telephoto 135mm lens, shallow depth",
}

# Camera Movements
CAMERA_MOVEMENTS = {
    "static": "static camera, locked-off shot",
    "slow-pan": "slow pan, gentle horizontal movement",
    "fast-pan": "fast pan, quick horizontal sweep",
    "tilt-up": "tilt up, vertical camera movement upward",
    "tilt-down": "tilt down, vertical camera movement downward",
    "dolly-in": "dolly in, smooth push toward subject",
    "dolly-out": "dolly out, smooth pull away from subject",
    "tracking": "tracking shot, following subject movement",
    "crane-up": "crane up, rising camera movement",
    "crane-down": "crane down, descending camera movement",
    "orbit": "orbit shot, circular movement around subject",
    "handheld": "handheld camera, natural shake and movement",
    "steadicam": "steadicam shot, smooth floating movement",
    "whip-pan": "whip pan, extremely fast directional change",
    "zoom-in": "zoom in, focal length increase",
    "zoom-out": "zoom out, focal length decrease",
}


class CameraLayer:
    """Assigns camera specifications to scenes with variety and consistency."""

    def __init__(self, ensure_variety: bool = True):
        """Initialize the Camera Layer.

        Args:
            ensure_variety: If True, avoids repeating same specs in consecutive scenes
        """
        self.ensure_variety = ensure_variety
        self.previous_shot_type: Optional[str] = None
        self.previous_angle: Optional[str] = None
        self.shot_type_history: List[str] = []
        self.angle_history: List[str] = []

        logger.info("CameraLayer initialized")

    def assign_camera_specs(
        self,
        scene_number: int,
        film_style: Optional[Dict[str, Any]] = None,
        force_shot_type: Optional[str] = None,
        force_angle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign camera specifications for a single scene.

        Args:
            scene_number: Scene number (for seeding variety)
            film_style: Optional film style dict with preferred_angles/movements
            force_shot_type: Optional forced shot type
            force_angle: Optional forced angle

        Returns:
            Dictionary with camera specifications:
            {
                "shot_type": str,
                "shot_type_name": str,
                "angle": str,
                "angle_description": str,
                "lens": str,
                "lens_description": str,
                "movement": str,
                "movement_description": str,
            }
        """
        # 1. Determine shot type
        if force_shot_type:
            shot_type = force_shot_type
        else:
            shot_type = self._select_shot_type(scene_number)

        # 2. Determine camera angle (considering film style preferences)
        if force_angle:
            angle = force_angle
        else:
            preferred_angles = None
            if film_style and "preferred_angles" in film_style:
                preferred_angles = film_style["preferred_angles"]
            angle = self._select_angle(scene_number, preferred_angles)

        # 3. Determine lens (based on shot type)
        lens = self._select_lens(shot_type, scene_number)

        # 4. Determine movement (considering film style preferences)
        preferred_movements = None
        if film_style and "preferred_movements" in film_style:
            preferred_movements = film_style["preferred_movements"]
        movement = self._select_movement(scene_number, preferred_movements)

        camera_specs = {
            "shot_type": shot_type,
            "shot_type_name": SHOT_TYPES.get(shot_type, shot_type),
            "angle": angle,
            "angle_description": CAMERA_ANGLES.get(angle, angle),
            "lens": lens,
            "lens_description": LENS_FOCAL_LENGTHS.get(lens, lens),
            "movement": movement,
            "movement_description": CAMERA_MOVEMENTS.get(movement, movement),
        }

        # Update history for variety tracking
        self.previous_shot_type = shot_type
        self.previous_angle = angle
        self.shot_type_history.append(shot_type)
        self.angle_history.append(angle)

        logger.debug(
            f"Scene {scene_number}: {shot_type} {angle} {lens} {movement}"
        )

        return camera_specs

    def _select_shot_type(self, scene_number: int) -> str:
        """Select shot type with variety consideration.

        Args:
            scene_number: Current scene number

        Returns:
            Shot type key (e.g., "WS", "MS", "CU")
        """
        available_types = list(SHOT_TYPES.keys())

        # Remove previous shot type to ensure variety
        if self.ensure_variety and self.previous_shot_type in available_types:
            if len(available_types) > 1:
                available_types.remove(self.previous_shot_type)

        # Avoid 3+ consecutive similar types
        if self.ensure_variety and len(self.shot_type_history) >= 2:
            recent_types = self.shot_type_history[-2:]
            if len(set(recent_types)) == 1:  # Last 2 were same
                if recent_types[0] in available_types and len(available_types) > 1:
                    available_types.remove(recent_types[0])

        # Use scene number as seed for deterministic but varied selection
        random.seed(scene_number * 73)
        selected = random.choice(available_types)

        return selected

    def _select_angle(
        self,
        scene_number: int,
        preferred_angles: Optional[List[str]] = None
    ) -> str:
        """Select camera angle with film style preferences.

        Args:
            scene_number: Current scene number
            preferred_angles: Optional list of preferred angles from film style

        Returns:
            Angle key (e.g., "low", "high", "dutch")
        """
        available_angles = list(CAMERA_ANGLES.keys())

        # If film style specifies preferred angles, use those 70% of the time
        if preferred_angles:
            # Filter to valid angles only
            valid_preferred = [a for a in preferred_angles if a in available_angles]
            if valid_preferred:
                random.seed(scene_number * 89)
                if random.random() < 0.7:  # 70% use preferred
                    available_angles = valid_preferred

        # Remove previous angle for variety
        if self.ensure_variety and self.previous_angle in available_angles:
            if len(available_angles) > 1:
                available_angles.remove(self.previous_angle)

        random.seed(scene_number * 101)
        selected = random.choice(available_angles)

        return selected

    def _select_lens(self, shot_type: str, scene_number: int) -> str:
        """Select lens based on shot type.

        Wide shots → wider lenses
        Close-ups → longer lenses

        Args:
            shot_type: Shot type key
            scene_number: Scene number for variety

        Returns:
            Lens key (e.g., "35mm", "50mm")
        """
        # Map shot types to appropriate lens ranges
        lens_mapping = {
            "EWS": ["14mm", "24mm"],
            "WS": ["24mm", "35mm"],
            "MWS": ["35mm", "50mm"],
            "MS": ["50mm", "85mm"],
            "MCU": ["85mm", "100mm"],
            "CU": ["85mm", "100mm", "135mm"],
            "ECU": ["100mm", "135mm"],
        }

        appropriate_lenses = lens_mapping.get(shot_type, ["50mm"])

        random.seed(scene_number * 113)
        selected = random.choice(appropriate_lenses)

        return selected

    def _select_movement(
        self,
        scene_number: int,
        preferred_movements: Optional[List[str]] = None
    ) -> str:
        """Select camera movement with film style preferences.

        Args:
            scene_number: Current scene number
            preferred_movements: Optional list of preferred movements from film style

        Returns:
            Movement key (e.g., "static", "dolly-in", "tracking")
        """
        available_movements = list(CAMERA_MOVEMENTS.keys())

        # If film style specifies preferred movements, use those 70% of the time
        if preferred_movements:
            # Normalize movement names (handle variations)
            valid_preferred = []
            for pm in preferred_movements:
                # Try exact match first
                if pm in available_movements:
                    valid_preferred.append(pm)
                # Try to find similar movements
                elif "static" in pm.lower():
                    valid_preferred.append("static")
                elif "pan" in pm.lower():
                    valid_preferred.extend(["slow-pan", "fast-pan"])
                elif "dolly" in pm.lower() or "push" in pm.lower():
                    valid_preferred.extend(["dolly-in", "dolly-out"])
                elif "track" in pm.lower():
                    valid_preferred.append("tracking")
                elif "crane" in pm.lower():
                    valid_preferred.extend(["crane-up", "crane-down"])
                elif "handheld" in pm.lower() or "shaky" in pm.lower():
                    valid_preferred.append("handheld")

            if valid_preferred:
                random.seed(scene_number * 127)
                if random.random() < 0.7:  # 70% use preferred
                    available_movements = list(set(valid_preferred))

        random.seed(scene_number * 139)
        selected = random.choice(available_movements)

        return selected

    def batch_assign_cameras(
        self,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assign camera specs to multiple scenes.

        Args:
            scenes: List of scene dicts (should have 'film_style' if available)

        Returns:
            Scenes with added 'camera_style' key
        """
        logger.info(f"Assigning camera specs for {len(scenes)} scenes")

        # Reset history for new batch
        self.previous_shot_type = None
        self.previous_angle = None
        self.shot_type_history = []
        self.angle_history = []

        for i, scene in enumerate(scenes, 1):
            film_style = scene.get("film_style")
            camera_specs = self.assign_camera_specs(i, film_style)
            scene["camera_style"] = camera_specs

        logger.info("Camera layer assignment complete for all scenes")
        return scenes

    def get_camera_variety_stats(self) -> Dict[str, Any]:
        """Get statistics about camera variety in processed scenes.

        Returns:
            Dictionary with variety statistics
        """
        if not self.shot_type_history:
            return {"message": "No scenes processed yet"}

        return {
            "total_scenes": len(self.shot_type_history),
            "unique_shot_types": len(set(self.shot_type_history)),
            "unique_angles": len(set(self.angle_history)),
            "shot_type_distribution": {
                st: self.shot_type_history.count(st)
                for st in set(self.shot_type_history)
            },
            "angle_distribution": {
                ang: self.angle_history.count(ang)
                for ang in set(self.angle_history)
            },
        }
