"""Character 관리 모듈 - Named와 Class 캐릭터 분리 관리."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from ..common.logger import setup_logger

logger = setup_logger(__name__)


CharacterType = Literal["named", "class"]
CharacterRole = Literal["protagonist", "antagonist", "supporting", "extra", "monster", "npc"]


class CharacterManager:
    """캐릭터 생성, 조회, 수정, 삭제 관리."""

    def __init__(self, data_root: str = "data/universes"):
        """Initialize CharacterManager.

        Args:
            data_root: Root directory for universe data
        """
        self.data_root = Path(data_root)
        logger.info("CharacterManager initialized")

    def create_character(
        self,
        universe_id: str,
        character_id: str,
        name: str,
        character_type: CharacterType,
        role: CharacterRole,
        physical: str,
        costume: str,
        equipment: str = "",
        personality_visual: str = "",
        consistency_tags: str = "",
        relationships: Optional[Dict[str, str]] = None,
        prototype_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new character.

        Args:
            universe_id: Universe ID
            character_id: Unique character ID
            name: Character name
            character_type: "named" or "class"
            role: Character role
            physical: Physical appearance
            costume: Costume/clothing
            equipment: Equipment/weapons
            personality_visual: Visual personality traits
            consistency_tags: Consistency tags for Stable Diffusion
            relationships: Character relationships
            prototype_template: For class characters, the prototype description

        Returns:
            Created character data
        """
        universe_path = self.data_root / universe_id

        if not universe_path.exists():
            raise ValueError(f"Universe not found: {universe_id}")

        # Determine save path based on type
        if character_type == "named":
            char_path = universe_path / "characters" / "named"
        else:
            char_path = universe_path / "characters" / "classes"

        char_path.mkdir(parents=True, exist_ok=True)
        char_file = char_path / f"{character_id}.json"

        if char_file.exists():
            raise ValueError(f"Character '{character_id}' already exists")

        # Create character data
        character_data = {
            "id": character_id,
            "name": name,
            "type": character_type,
            "role": role,
            "physical": physical,
            "costume": costume,
            "equipment": equipment,
            "personality_visual": personality_visual,
            "consistency_tags": consistency_tags,
            "relationships": relationships or {},
            "appearances": [],
            "current_state": "normal",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Add prototype template for class characters
        if character_type == "class":
            character_data["prototype_template"] = prototype_template or ""

        # Save character
        with open(char_file, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Created {character_type} character: {name} ({character_id})")
        return character_data

    def get_character(
        self,
        universe_id: str,
        character_id: str,
        character_type: Optional[CharacterType] = None
    ) -> Optional[Dict[str, Any]]:
        """Get character by ID.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            character_type: Optional character type (if known)

        Returns:
            Character data or None
        """
        universe_path = self.data_root / universe_id

        # Try both types if not specified
        types_to_try = [character_type] if character_type else ["named", "class"]

        for ctype in types_to_try:
            char_file = universe_path / "characters" / ctype / f"{character_id}.json"
            if char_file.exists():
                with open(char_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        logger.warning(f"Character not found: {character_id}")
        return None

    def list_characters(
        self,
        universe_id: str,
        character_type: Optional[CharacterType] = None
    ) -> List[Dict[str, Any]]:
        """List all characters in a universe.

        Args:
            universe_id: Universe ID
            character_type: Optional filter by type

        Returns:
            List of characters
        """
        universe_path = self.data_root / universe_id
        characters = []

        types = [character_type] if character_type else ["named", "class"]

        for ctype in types:
            char_path = universe_path / "characters" / ctype
            if char_path.exists():
                for char_file in char_path.glob("*.json"):
                    with open(char_file, 'r', encoding='utf-8') as f:
                        characters.append(json.load(f))

        # Sort by name
        characters.sort(key=lambda x: x.get('name', ''))
        return characters

    def update_character(
        self,
        universe_id: str,
        character_id: str,
        updates: Dict[str, Any],
        character_type: Optional[CharacterType] = None
    ) -> Dict[str, Any]:
        """Update character data.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            updates: Fields to update
            character_type: Optional character type

        Returns:
            Updated character data
        """
        character_data = self.get_character(universe_id, character_id, character_type)

        if not character_data:
            raise ValueError(f"Character not found: {character_id}")

        # Update fields
        for key, value in updates.items():
            if key not in ['id', 'created_at']:  # Protect immutable fields
                character_data[key] = value

        character_data['updated_at'] = datetime.now().isoformat()

        # Save
        ctype = character_data['type']
        char_file = self.data_root / universe_id / "characters" / ctype / f"{character_id}.json"
        with open(char_file, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Updated character: {character_id}")
        return character_data

    def delete_character(
        self,
        universe_id: str,
        character_id: str,
        character_type: Optional[CharacterType] = None
    ) -> bool:
        """Delete a character.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            character_type: Optional character type

        Returns:
            True if deleted successfully
        """
        character_data = self.get_character(universe_id, character_id, character_type)

        if not character_data:
            logger.warning(f"Character not found: {character_id}")
            return False

        ctype = character_data['type']
        char_file = self.data_root / universe_id / "characters" / ctype / f"{character_id}.json"
        char_file.unlink()

        logger.info(f"Deleted character: {character_id}")
        return True

    def add_appearance(
        self,
        universe_id: str,
        character_id: str,
        episode_id: str,
        character_type: Optional[CharacterType] = None
    ) -> Dict[str, Any]:
        """Add an episode appearance to character.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            episode_id: Episode ID
            character_type: Optional character type

        Returns:
            Updated character data
        """
        character_data = self.get_character(universe_id, character_id, character_type)

        if not character_data:
            raise ValueError(f"Character not found: {character_id}")

        if "appearances" not in character_data:
            character_data["appearances"] = []

        if episode_id not in character_data["appearances"]:
            character_data["appearances"].append(episode_id)

        return self.update_character(
            universe_id,
            character_id,
            {"appearances": character_data["appearances"]},
            character_type
        )

    def update_state(
        self,
        universe_id: str,
        character_id: str,
        new_state: str,
        character_type: Optional[CharacterType] = None
    ) -> Dict[str, Any]:
        """Update character state (e.g., "normal", "injured", "dead").

        Args:
            universe_id: Universe ID
            character_id: Character ID
            new_state: New state
            character_type: Optional character type

        Returns:
            Updated character data
        """
        return self.update_character(
            universe_id,
            character_id,
            {"current_state": new_state},
            character_type
        )

    def get_character_prompt_snippet(
        self,
        universe_id: str,
        character_id: str,
        character_type: Optional[CharacterType] = None
    ) -> str:
        """Generate a prompt snippet for this character.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            character_type: Optional character type

        Returns:
            Prompt snippet string
        """
        character_data = self.get_character(universe_id, character_id, character_type)

        if not character_data:
            return ""

        snippet_parts = [
            character_data.get('name', ''),
            character_data.get('physical', ''),
            character_data.get('costume', ''),
        ]

        equipment = character_data.get('equipment', '')
        if equipment:
            snippet_parts.append(equipment)

        consistency = character_data.get('consistency_tags', '')
        if consistency:
            snippet_parts.append(consistency)

        return ', '.join(filter(None, snippet_parts))

    def get_characters_by_episode(
        self,
        universe_id: str,
        episode_id: str
    ) -> List[Dict[str, Any]]:
        """Get all characters that appeared in an episode.

        Args:
            universe_id: Universe ID
            episode_id: Episode ID

        Returns:
            List of characters
        """
        all_characters = self.list_characters(universe_id)
        return [
            char for char in all_characters
            if episode_id in char.get('appearances', [])
        ]
