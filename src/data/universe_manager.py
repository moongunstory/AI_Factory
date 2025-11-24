"""Universe (세계관) 관리 모듈."""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class UniverseManager:
    """세계관 생성, 조회, 수정, 삭제 관리."""

    def __init__(self, data_root: str = "data/universes"):
        """Initialize UniverseManager.

        Args:
            data_root: Root directory for universe data
        """
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"UniverseManager initialized with root: {self.data_root}")

    def create_universe(
        self,
        universe_id: str,
        name: str,
        genre: str,
        background: str,
        rules: Dict[str, Any],
        style_lock: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new universe.

        Args:
            universe_id: Unique ID for the universe
            name: Display name
            genre: Genre (e.g., "dark_fantasy", "sci_fi")
            background: Background description
            rules: World rules (magic system, etc.)
            style_lock: Optional style lock settings

        Returns:
            Created universe data
        """
        universe_path = self.data_root / universe_id

        if universe_path.exists():
            raise ValueError(f"Universe '{universe_id}' already exists")

        # Create directory structure
        universe_path.mkdir(parents=True, exist_ok=True)
        (universe_path / "characters" / "named").mkdir(parents=True, exist_ok=True)
        (universe_path / "characters" / "classes").mkdir(parents=True, exist_ok=True)
        (universe_path / "series").mkdir(parents=True, exist_ok=True)
        (universe_path / "episodes").mkdir(parents=True, exist_ok=True)

        # Create universe metadata
        universe_data = {
            "id": universe_id,
            "name": name,
            "genre": genre,
            "background": background,
            "rules": rules,
            "style_lock": style_lock or {
                "theme": genre,
                "locked": False
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_episodes": 0,
            "total_characters": 0,
            "locations": [],
            "items": [],
            "factions": []
        }

        # Save universe.json
        universe_file = universe_path / "universe.json"
        with open(universe_file, 'w', encoding='utf-8') as f:
            json.dump(universe_data, f, ensure_ascii=False, indent=2)

        # Create empty timeline
        timeline_data = {
            "universe_id": universe_id,
            "events": []
        }
        timeline_file = universe_path / "timeline.json"
        with open(timeline_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Created universe: {name} ({universe_id})")
        return universe_data

    def get_universe(self, universe_id: str) -> Optional[Dict[str, Any]]:
        """Get universe by ID.

        Args:
            universe_id: Universe ID

        Returns:
            Universe data or None if not found
        """
        universe_file = self.data_root / universe_id / "universe.json"

        if not universe_file.exists():
            logger.warning(f"Universe not found: {universe_id}")
            return None

        with open(universe_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_universes(self) -> List[Dict[str, Any]]:
        """List all universes.

        Returns:
            List of universe metadata
        """
        universes = []

        for universe_dir in self.data_root.iterdir():
            if universe_dir.is_dir():
                universe_file = universe_dir / "universe.json"
                if universe_file.exists():
                    with open(universe_file, 'r', encoding='utf-8') as f:
                        universes.append(json.load(f))

        # Sort by updated_at (most recent first)
        universes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return universes

    def update_universe(
        self,
        universe_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update universe data.

        Args:
            universe_id: Universe ID
            updates: Fields to update

        Returns:
            Updated universe data
        """
        universe_data = self.get_universe(universe_id)

        if not universe_data:
            raise ValueError(f"Universe not found: {universe_id}")

        # Update fields
        for key, value in updates.items():
            if key not in ['id', 'created_at']:  # Protect immutable fields
                universe_data[key] = value

        universe_data['updated_at'] = datetime.now().isoformat()

        # Save
        universe_file = self.data_root / universe_id / "universe.json"
        with open(universe_file, 'w', encoding='utf-8') as f:
            json.dump(universe_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Updated universe: {universe_id}")
        return universe_data

    def delete_universe(self, universe_id: str) -> bool:
        """Delete a universe (dangerous!).

        Args:
            universe_id: Universe ID

        Returns:
            True if deleted successfully
        """
        universe_path = self.data_root / universe_id

        if not universe_path.exists():
            logger.warning(f"Universe not found: {universe_id}")
            return False

        # Delete directory recursively
        import shutil
        shutil.rmtree(universe_path)

        logger.warning(f"Deleted universe: {universe_id}")
        return True

    def get_universe_summary(self, universe_id: str) -> Dict[str, Any]:
        """Get universe summary with statistics.

        Args:
            universe_id: Universe ID

        Returns:
            Universe summary
        """
        universe_data = self.get_universe(universe_id)

        if not universe_data:
            raise ValueError(f"Universe not found: {universe_id}")

        universe_path = self.data_root / universe_id

        # Count characters
        named_chars = len(list((universe_path / "characters" / "named").glob("*.json")))
        class_chars = len(list((universe_path / "characters" / "classes").glob("*.json")))

        # Count episodes
        episodes = len(list((universe_path / "episodes").glob("*.json")))

        # Count timeline events
        timeline_file = universe_path / "timeline.json"
        timeline_events = 0
        if timeline_file.exists():
            with open(timeline_file, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                timeline_events = len(timeline_data.get('events', []))

        return {
            **universe_data,
            "stats": {
                "named_characters": named_chars,
                "class_characters": class_chars,
                "total_characters": named_chars + class_chars,
                "total_episodes": episodes,
                "timeline_events": timeline_events
            }
        }

    def set_style_lock(
        self,
        universe_id: str,
        theme: str,
        locked: bool = True
    ) -> Dict[str, Any]:
        """Set or update style lock for universe.

        Args:
            universe_id: Universe ID
            theme: Visual theme
            locked: Whether to lock the style

        Returns:
            Updated universe data
        """
        return self.update_universe(universe_id, {
            "style_lock": {
                "theme": theme,
                "locked": locked
            }
        })

    def add_location(self, universe_id: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new location to the universe.

        Args:
            universe_id: Universe ID
            location: Location data

        Returns:
            Updated universe data
        """
        universe_data = self.get_universe(universe_id)

        if not universe_data:
            raise ValueError(f"Universe not found: {universe_id}")

        if "locations" not in universe_data:
            universe_data["locations"] = []

        universe_data["locations"].append(location)

        return self.update_universe(universe_id, {"locations": universe_data["locations"]})

    def add_item(self, universe_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new item/artifact to the universe.

        Args:
            universe_id: Universe ID
            item: Item data

        Returns:
            Updated universe data
        """
        universe_data = self.get_universe(universe_id)

        if not universe_data:
            raise ValueError(f"Universe not found: {universe_id}")

        if "items" not in universe_data:
            universe_data["items"] = []

        universe_data["items"].append(item)

        return self.update_universe(universe_id, {"items": universe_data["items"]})
