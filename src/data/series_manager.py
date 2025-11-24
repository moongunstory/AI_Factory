"""Series/Episode 관리 모듈."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class SeriesManager:
    """시리즈와 에피소드 관리."""

    def __init__(self, data_root: str = "data/universes"):
        """Initialize SeriesManager.

        Args:
            data_root: Root directory for universe data
        """
        self.data_root = Path(data_root)
        logger.info("SeriesManager initialized")

    def create_series(
        self,
        universe_id: str,
        series_id: str,
        name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Create a new series within a universe.

        Args:
            universe_id: Universe ID
            series_id: Unique series ID
            name: Series name
            description: Series description

        Returns:
            Created series data
        """
        universe_path = self.data_root / universe_id

        if not universe_path.exists():
            raise ValueError(f"Universe not found: {universe_id}")

        series_path = universe_path / "series"
        series_path.mkdir(parents=True, exist_ok=True)

        series_file = series_path / f"{series_id}.json"

        if series_file.exists():
            raise ValueError(f"Series '{series_id}' already exists")

        series_data = {
            "id": series_id,
            "universe_id": universe_id,
            "name": name,
            "description": description,
            "episodes": [],
            "status": "ongoing",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        with open(series_file, 'w', encoding='utf-8') as f:
            json.dump(series_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Created series: {name} ({series_id})")
        return series_data

    def get_series(self, universe_id: str, series_id: str) -> Optional[Dict[str, Any]]:
        """Get series by ID.

        Args:
            universe_id: Universe ID
            series_id: Series ID

        Returns:
            Series data or None
        """
        series_file = self.data_root / universe_id / "series" / f"{series_id}.json"

        if not series_file.exists():
            logger.warning(f"Series not found: {series_id}")
            return None

        with open(series_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_series(self, universe_id: str) -> List[Dict[str, Any]]:
        """List all series in a universe.

        Args:
            universe_id: Universe ID

        Returns:
            List of series
        """
        series_path = self.data_root / universe_id / "series"

        if not series_path.exists():
            return []

        series_list = []
        for series_file in series_path.glob("*.json"):
            with open(series_file, 'r', encoding='utf-8') as f:
                series_list.append(json.load(f))

        # Sort by created_at
        series_list.sort(key=lambda x: x.get('created_at', ''))
        return series_list

    def update_series(
        self,
        universe_id: str,
        series_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update series data.

        Args:
            universe_id: Universe ID
            series_id: Series ID
            updates: Fields to update

        Returns:
            Updated series data
        """
        series_data = self.get_series(universe_id, series_id)

        if not series_data:
            raise ValueError(f"Series not found: {series_id}")

        for key, value in updates.items():
            if key not in ['id', 'universe_id', 'created_at']:
                series_data[key] = value

        series_data['updated_at'] = datetime.now().isoformat()

        series_file = self.data_root / universe_id / "series" / f"{series_id}.json"
        with open(series_file, 'w', encoding='utf-8') as f:
            json.dump(series_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Updated series: {series_id}")
        return series_data

    def create_episode(
        self,
        universe_id: str,
        series_id: str,
        episode_number: int,
        title: str,
        story: str,
        expanded_story: str,
        story_beats: Dict[str, Any],
        character_sheets: Dict[str, Any],
        scenes: List[Dict[str, Any]],
        theme: str,
        character_ids: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new episode.

        Args:
            universe_id: Universe ID
            series_id: Series ID
            episode_number: Episode number
            title: Episode title
            story: Original story idea
            expanded_story: Expanded story
            story_beats: Story beats
            character_sheets: Character sheets
            scenes: Generated scenes
            theme: Visual theme
            character_ids: List of character IDs appearing
            metadata: Additional metadata

        Returns:
            Created episode data
        """
        universe_path = self.data_root / universe_id

        if not universe_path.exists():
            raise ValueError(f"Universe not found: {universe_id}")

        episodes_path = universe_path / "episodes"
        episodes_path.mkdir(parents=True, exist_ok=True)

        episode_id = f"ep{episode_number:03d}"
        episode_file = episodes_path / f"{episode_id}.json"

        if episode_file.exists():
            raise ValueError(f"Episode {episode_number} already exists")

        episode_data = {
            "id": episode_id,
            "universe_id": universe_id,
            "series_id": series_id,
            "episode_number": episode_number,
            "title": title,
            "story": story,
            "expanded_story": expanded_story,
            "story_beats": story_beats,
            "character_sheets": character_sheets,
            "scenes": scenes,
            "theme": theme,
            "character_ids": character_ids or [],
            "total_scenes": len(scenes),
            "total_duration": sum(scene.get('duration', 0) for scene in scenes),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        with open(episode_file, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

        # Update series episode list
        series_data = self.get_series(universe_id, series_id)
        if series_data:
            if episode_id not in series_data.get('episodes', []):
                series_data['episodes'].append(episode_id)
                self.update_series(universe_id, series_id, {'episodes': series_data['episodes']})

        logger.info(f"Created episode: {episode_number} - {title}")
        return episode_data

    def get_episode(
        self,
        universe_id: str,
        episode_number: int
    ) -> Optional[Dict[str, Any]]:
        """Get episode by number.

        Args:
            universe_id: Universe ID
            episode_number: Episode number

        Returns:
            Episode data or None
        """
        episode_id = f"ep{episode_number:03d}"
        episode_file = self.data_root / universe_id / "episodes" / f"{episode_id}.json"

        if not episode_file.exists():
            logger.warning(f"Episode not found: {episode_number}")
            return None

        with open(episode_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_latest_episode(self, universe_id: str, series_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest episode in a series.

        Args:
            universe_id: Universe ID
            series_id: Series ID

        Returns:
            Latest episode data or None
        """
        series_data = self.get_series(universe_id, series_id)

        if not series_data or not series_data.get('episodes'):
            return None

        # Get the last episode ID
        last_episode_id = series_data['episodes'][-1]
        episode_file = self.data_root / universe_id / "episodes" / f"{last_episode_id}.json"

        if not episode_file.exists():
            return None

        with open(episode_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_episodes(
        self,
        universe_id: str,
        series_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all episodes in a universe or series.

        Args:
            universe_id: Universe ID
            series_id: Optional series ID to filter

        Returns:
            List of episodes
        """
        episodes_path = self.data_root / universe_id / "episodes"

        if not episodes_path.exists():
            return []

        episodes = []
        for episode_file in episodes_path.glob("*.json"):
            with open(episode_file, 'r', encoding='utf-8') as f:
                episode = json.load(f)
                if series_id is None or episode.get('series_id') == series_id:
                    episodes.append(episode)

        # Sort by episode number
        episodes.sort(key=lambda x: x.get('episode_number', 0))
        return episodes

    def get_next_episode_number(self, universe_id: str, series_id: str) -> int:
        """Get the next episode number for a series.

        Args:
            universe_id: Universe ID
            series_id: Series ID

        Returns:
            Next episode number
        """
        episodes = self.list_episodes(universe_id, series_id)

        if not episodes:
            return 1

        return max(ep.get('episode_number', 0) for ep in episodes) + 1

    def get_episode_summary(
        self,
        universe_id: str,
        episode_number: int
    ) -> str:
        """Get a brief summary of an episode.

        Args:
            universe_id: Universe ID
            episode_number: Episode number

        Returns:
            Episode summary
        """
        episode = self.get_episode(universe_id, episode_number)

        if not episode:
            return ""

        title = episode.get('title', '')
        story = episode.get('expanded_story', episode.get('story', ''))

        # Get first 200 characters as summary
        summary = story[:200] + "..." if len(story) > 200 else story

        return f"{title}: {summary}"

    def update_episode(
        self,
        universe_id: str,
        episode_number: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update episode data.

        Args:
            universe_id: Universe ID
            episode_number: Episode number
            updates: Fields to update

        Returns:
            Updated episode data
        """
        episode_data = self.get_episode(universe_id, episode_number)

        if not episode_data:
            raise ValueError(f"Episode not found: {episode_number}")

        for key, value in updates.items():
            if key not in ['id', 'universe_id', 'series_id', 'episode_number', 'created_at']:
                episode_data[key] = value

        episode_data['updated_at'] = datetime.now().isoformat()

        episode_id = f"ep{episode_number:03d}"
        episode_file = self.data_root / universe_id / "episodes" / f"{episode_id}.json"

        with open(episode_file, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Updated episode: {episode_number}")
        return episode_data
