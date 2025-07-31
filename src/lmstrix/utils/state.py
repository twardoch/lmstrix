"""State management utilities for LMStrix."""

# this_file: src/lmstrix/utils/state.py

import json
from pathlib import Path

from lmstrix.utils.logging import logger
from lmstrix.utils.paths import get_lmstudio_path


class StateManager:
    """Manages persistent state for LMStrix."""

    def __init__(self) -> None:
        """Initialize the state manager."""
        self.state_file = Path(get_lmstudio_path()) / ".lmstrix_state.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {}

    def _save_state(self) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

    def get_last_used_model(self) -> str | None:
        """Get the last used model ID."""
        return self._state.get("last_used_model")

    def set_last_used_model(self, model_id: str) -> None:
        """Set the last used model ID."""
        self._state["last_used_model"] = model_id
        self._save_state()

    def clear_last_used_model(self) -> None:
        """Clear the last used model ID."""
        if "last_used_model" in self._state:
            del self._state["last_used_model"]
            self._save_state()
