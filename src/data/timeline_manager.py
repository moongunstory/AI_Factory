"""Timeline and consistency checker module."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..common.logger import setup_logger

logger = setup_logger(__name__)


class TimelineManager:
    """타임라인 이벤트 관리 및 일관성 체크."""

    def __init__(self, data_root: str = "data/universes"):
        """Initialize TimelineManager.

        Args:
            data_root: Root directory for universe data
        """
        self.data_root = Path(data_root)
        logger.info("TimelineManager initialized")

    def add_event(
        self,
        universe_id: str,
        episode_id: str,
        title: str,
        description: str,
        affected_characters: List[str] = None,
        new_locations: List[str] = None,
        new_items: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a new timeline event.

        Args:
            universe_id: Universe ID
            episode_id: Episode ID where event occurred
            title: Event title
            description: Event description
            affected_characters: Character IDs affected by this event
            new_locations: New locations introduced
            new_items: New items introduced
            metadata: Additional metadata

        Returns:
            Created event data
        """
        timeline = self._load_timeline(universe_id)

        # Generate event ID
        event_id = f"evt_{len(timeline['events']) + 1:03d}"

        event_data = {
            "id": event_id,
            "episode_id": episode_id,
            "title": title,
            "description": description,
            "affected_characters": affected_characters or [],
            "new_locations": new_locations or [],
            "new_items": new_items or [],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        timeline['events'].append(event_data)

        self._save_timeline(universe_id, timeline)

        logger.info(f"Added timeline event: {title} ({event_id})")
        return event_data

    def get_timeline(self, universe_id: str) -> List[Dict[str, Any]]:
        """Get all timeline events.

        Args:
            universe_id: Universe ID

        Returns:
            List of events
        """
        timeline = self._load_timeline(universe_id)
        return timeline.get('events', [])

    def get_events_by_episode(
        self,
        universe_id: str,
        episode_id: str
    ) -> List[Dict[str, Any]]:
        """Get all events from a specific episode.

        Args:
            universe_id: Universe ID
            episode_id: Episode ID

        Returns:
            List of events
        """
        timeline = self._load_timeline(universe_id)
        return [
            event for event in timeline['events']
            if event.get('episode_id') == episode_id
        ]

    def check_character_consistency(
        self,
        universe_id: str,
        character_id: str,
        proposed_state: str,
        proposed_episode: int
    ) -> Tuple[bool, List[str]]:
        """Check if a character's proposed state is consistent with timeline.

        Args:
            universe_id: Universe ID
            character_id: Character ID
            proposed_state: Proposed character state
            proposed_episode: Episode number being created

        Returns:
            (is_consistent, list_of_warnings)
        """
        warnings = []

        # Load character data
        from .character_manager import CharacterManager
        char_mgr = CharacterManager(str(self.data_root))
        character = char_mgr.get_character(universe_id, character_id)

        if not character:
            warnings.append(f"Character '{character_id}' not found")
            return False, warnings

        # Check current state
        current_state = character.get('current_state', 'normal')

        # Check if character is dead
        if current_state == 'dead' and proposed_state != 'dead':
            warnings.append(
                f"Consistency Error: Character '{character.get('name')}' "
                f"is marked as dead but appears alive in episode {proposed_episode}"
            )
            return False, warnings

        # Check timeline for death events
        timeline = self._load_timeline(universe_id)
        for event in timeline['events']:
            if character_id in event.get('affected_characters', []):
                if 'death' in event.get('description', '').lower():
                    # Extract episode number from event
                    event_ep_id = event.get('episode_id', '')
                    if event_ep_id:
                        event_ep_num = int(event_ep_id.replace('ep', ''))
                        if event_ep_num < proposed_episode:
                            warnings.append(
                                f"Consistency Error: Character '{character.get('name')}' "
                                f"died in episode {event_ep_num} but appears in episode {proposed_episode}"
                            )
                            return False, warnings

        return True, warnings

    def check_location_consistency(
        self,
        universe_id: str,
        location_name: str,
        proposed_state: str,
        proposed_episode: int
    ) -> Tuple[bool, List[str]]:
        """Check if a location's proposed state is consistent.

        Args:
            universe_id: Universe ID
            location_name: Location name
            proposed_state: Proposed state (e.g., "destroyed", "normal")
            proposed_episode: Episode number being created

        Returns:
            (is_consistent, list_of_warnings)
        """
        warnings = []

        timeline = self._load_timeline(universe_id)

        for event in timeline['events']:
            # Check if location was destroyed
            if location_name in event.get('description', ''):
                if 'destroyed' in event.get('description', '').lower() or \
                   'ruin' in event.get('description', '').lower():
                    event_ep_id = event.get('episode_id', '')
                    if event_ep_id:
                        event_ep_num = int(event_ep_id.replace('ep', ''))
                        if event_ep_num < proposed_episode and proposed_state == 'normal':
                            warnings.append(
                                f"Consistency Warning: Location '{location_name}' "
                                f"was destroyed in episode {event_ep_num} but appears "
                                f"normal in episode {proposed_episode}"
                            )
                            return False, warnings

        return True, warnings

    def check_story_consistency(
        self,
        universe_id: str,
        proposed_story: str,
        proposed_episode: int,
        character_ids: List[str]
    ) -> Dict[str, Any]:
        """Comprehensive consistency check for a proposed story.

        Args:
            universe_id: Universe ID
            proposed_story: Proposed story text
            proposed_episode: Episode number being created
            character_ids: Characters appearing in the story

        Returns:
            Consistency check results
        """
        results = {
            "is_consistent": True,
            "errors": [],
            "warnings": [],
            "info": []
        }

        # Check each character
        for char_id in character_ids:
            is_consistent, warnings = self.check_character_consistency(
                universe_id,
                char_id,
                "normal",  # Default assumption
                proposed_episode
            )

            if not is_consistent:
                results["is_consistent"] = False
                results["errors"].extend(warnings)
            elif warnings:
                results["warnings"].extend(warnings)

        # Check for timeline conflicts
        timeline = self._load_timeline(universe_id)
        prev_events = [
            event for event in timeline['events']
            if int(event.get('episode_id', 'ep000').replace('ep', '')) < proposed_episode
        ]

        # Log info about previous events
        if prev_events:
            results["info"].append(
                f"This episode follows {len(prev_events)} previous events"
            )

        return results

    def _load_timeline(self, universe_id: str) -> Dict[str, Any]:
        """Load timeline from file.

        Args:
            universe_id: Universe ID

        Returns:
            Timeline data
        """
        timeline_file = self.data_root / universe_id / "timeline.json"

        if not timeline_file.exists():
            # Create empty timeline
            timeline_data = {
                "universe_id": universe_id,
                "events": []
            }
            timeline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(timeline_file, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, ensure_ascii=False, indent=2)
            return timeline_data

        with open(timeline_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_timeline(self, universe_id: str, timeline_data: Dict[str, Any]):
        """Save timeline to file.

        Args:
            universe_id: Universe ID
            timeline_data: Timeline data to save
        """
        timeline_file = self.data_root / universe_id / "timeline.json"
        timeline_file.parent.mkdir(parents=True, exist_ok=True)

        with open(timeline_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    def get_timeline_summary(self, universe_id: str) -> str:
        """Get a text summary of the entire timeline.

        Args:
            universe_id: Universe ID

        Returns:
            Timeline summary text
        """
        timeline = self._load_timeline(universe_id)
        events = timeline.get('events', [])

        if not events:
            return "No events in timeline yet."

        summary_lines = [f"Timeline Summary ({len(events)} events):"]

        for event in events:
            episode_id = event.get('episode_id', 'unknown')
            title = event.get('title', 'Untitled')
            description = event.get('description', '')[:100]
            summary_lines.append(f"- [{episode_id}] {title}: {description}...")

        return "\n".join(summary_lines)
