"""State persistence manager for saving and loading pipeline state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """Manage persistent state storage for pipeline execution."""

    def __init__(self, state_dir: str = ".devussy_state"):
        """Initialize the state manager.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"StateManager initialized with dir: {self.state_dir}")

    def save_state(self, key: str, data: Any) -> None:
        """Save state data to a JSON file.

        Args:
            key: Unique identifier for this state
            data: Data to save (must be JSON-serializable)
        """
        state_file = self.state_dir / f"{key}.json"

        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved state: {key}")
        except Exception as e:
            logger.error(f"Failed to save state {key}: {e}")
            raise

    def load_state(self, key: str) -> Any:
        """Load state data from a JSON file.

        Args:
            key: Unique identifier for the state to load

        Returns:
            The loaded data, or None if not found

        Raises:
            FileNotFoundError: If the state file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        state_file = self.state_dir / f"{key}.json"

        if not state_file.exists():
            logger.warning(f"State file not found: {key}")
            return None

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded state: {key}")
            return data
        except Exception as e:
            logger.error(f"Failed to load state {key}: {e}")
            raise

    def delete_state(self, key: str) -> None:
        """Delete a state file.

        Args:
            key: Unique identifier for the state to delete
        """
        state_file = self.state_dir / f"{key}.json"

        if state_file.exists():
            state_file.unlink()
            logger.info(f"Deleted state: {key}")
        else:
            logger.warning(f"State file not found for deletion: {key}")

    def list_states(self) -> list[str]:
        """List all available state keys.

        Returns:
            List of state keys (without .json extension)
        """
        return [f.stem for f in self.state_dir.glob("*.json")]

    def clear_all_states(self) -> None:
        """Delete all state files."""
        count = 0
        for state_file in self.state_dir.glob("*.json"):
            state_file.unlink()
            count += 1
        logger.info(f"Cleared {count} state file(s)")

    def save_checkpoint(
        self,
        checkpoint_key: str,
        stage: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a workflow checkpoint with metadata.

        Args:
            checkpoint_key: Unique identifier for this checkpoint
            stage: Name of the workflow stage (e.g., 'project_design', 'devplan')
            data: The main data to checkpoint
            metadata: Optional metadata (timestamps, config, etc.)
        """
        checkpoint_data = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {},
        }

        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_key}.json"

        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Saved checkpoint: {checkpoint_key} at stage: {stage}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint_key}: {e}")
            raise

    def load_checkpoint(self, checkpoint_key: str) -> Optional[Dict[str, Any]]:
        """Load a workflow checkpoint.

        Args:
            checkpoint_key: Unique identifier for the checkpoint

        Returns:
            Checkpoint data dictionary or None if not found
        """
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_key}.json"

        if not checkpoint_file.exists():
            logger.warning(f"Checkpoint file not found: {checkpoint_key}")
            return None

        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
            stage = checkpoint_data.get("stage")
            logger.info(f"Loaded checkpoint: {checkpoint_key} from stage: {stage}")
            return checkpoint_data
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_key}: {e}")
            raise

    def list_checkpoints(self) -> List[Dict[str, str]]:
        """List all available checkpoints with metadata.

        Returns:
            List of checkpoint info dictionaries
        """
        checkpoints = []

        for checkpoint_file in self.state_dir.glob("checkpoint_*.json"):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract checkpoint key from filename
                key = checkpoint_file.stem.replace("checkpoint_", "")

                checkpoints.append(
                    {
                        "key": key,
                        "stage": data.get("stage", "unknown"),
                        "timestamp": data.get("timestamp", "unknown"),
                        "file": str(checkpoint_file),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read checkpoint file {checkpoint_file}: {e}")
                continue

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        return checkpoints

    def delete_checkpoint(self, checkpoint_key: str) -> None:
        """Delete a specific checkpoint.

        Args:
            checkpoint_key: Unique identifier for the checkpoint to delete
        """
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_key}.json"

        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Deleted checkpoint: {checkpoint_key}")
        else:
            logger.warning(f"Checkpoint file not found for deletion: {checkpoint_key}")

    def cleanup_old_checkpoints(self, keep_latest: int = 5) -> None:
        """Clean up old checkpoints, keeping only the latest N.

        Args:
            keep_latest: Number of latest checkpoints to keep per key
        """
        checkpoints = self.list_checkpoints()

        # Group by base key (without stage info)
        checkpoint_groups = {}
        for checkpoint in checkpoints:
            base_key = checkpoint["key"].split("_")[0]  # Get base key
            if base_key not in checkpoint_groups:
                checkpoint_groups[base_key] = []
            checkpoint_groups[base_key].append(checkpoint)

        deleted_count = 0
        for base_key, group in checkpoint_groups.items():
            if len(group) > keep_latest:
                # Sort by timestamp and keep only the latest N
                group.sort(key=lambda x: x["timestamp"], reverse=True)
                to_delete = group[keep_latest:]

                for checkpoint in to_delete:
                    self.delete_checkpoint(checkpoint["key"])
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old checkpoints")

    def resume_pipeline(self, checkpoint_key: str) -> Optional[Dict[str, Any]]:
        """Resume a pipeline from a specific checkpoint.

        Args:
            checkpoint_key: Unique identifier for the checkpoint to resume from

        Returns:
            The checkpoint data to resume from, or None if not found
        """
        checkpoint_data = self.load_checkpoint(checkpoint_key)

        if checkpoint_data is None:
            logger.error(f"Cannot resume: checkpoint {checkpoint_key} not found")
            return None

        stage = checkpoint_data.get("stage")
        timestamp = checkpoint_data.get("timestamp")

        logger.info(
            f"Resuming pipeline from checkpoint: {checkpoint_key} "
            f"(stage: {stage}, saved: {timestamp})"
        )

        return checkpoint_data

    def get_latest_checkpoint(
        self, stage_filter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent checkpoint, optionally filtered by stage.

        Args:
            stage_filter: Optional stage name to filter by

        Returns:
            Latest checkpoint data or None if no checkpoints found
        """
        checkpoints = self.list_checkpoints()

        if stage_filter:
            checkpoints = [cp for cp in checkpoints if cp["stage"] == stage_filter]

        if not checkpoints:
            return None

        # Get the latest checkpoint (list is already sorted by timestamp)
        latest = checkpoints[0]
        return self.load_checkpoint(latest["key"])
