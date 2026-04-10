"""
SchemaSurgeon_environment.py
----------------------------
Core OpenEnv environment for Schema Surgeon.
Loads static task datasets, dispatches deterministic actions, and computes
schema-validation reward and termination logic.
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from models import SchemaAction, SchemaObservation
    from server.actions import dispatch_action
    from server.grader import calculate_score
    from server.obs import build_observation
    from server.tasks import get_task
except ModuleNotFoundError:
    from SchemaSurgeon.models import SchemaAction, SchemaObservation
    from SchemaSurgeon.server.actions import dispatch_action
    from SchemaSurgeon.server.grader import calculate_score
    from SchemaSurgeon.server.obs import build_observation
    from SchemaSurgeon.server.tasks import get_task

DEFAULT_TASK_ID: str = "task1"
DEFAULT_MAX_STEPS: int = 30
STAGNATION_LIMIT: int = 5


class SchemaSurgeonEnvironment(Environment[SchemaAction, SchemaObservation, State]):
    """
    Environment for NoSQL schema migration tasks.

    Args:
        task_id: Initial task identifier.

    Returns:
        None.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, task_id: str = DEFAULT_TASK_ID) -> None:
        """
        Initialize environment state and load the selected task dataset.

        Args:
            task_id: Task ID to initialize.

        Returns:
            None.
        """
        super().__init__()
        self.episode_id: str = str(uuid4())
        self.task_id: str = task_id
        self.task_config: Dict[str, Any] = {}
        self.target_schema: Dict[str, Any] = {}
        self.protected_keys: List[str] = []
        self.max_steps: int = DEFAULT_MAX_STEPS

        self.original_collection: List[Dict[str, Any]] = []
        self.collection: List[Dict[str, Any]] = []

        self.step_count: int = 0
        self.last_score: float = 0.0
        self.stagnation_counter: int = 0
        self.last_action_status: str = "reset"
        self.done: bool = False

        self._load_task(task_id)

    def _resolve_data_path(self, relative_path: str) -> Path:
        """
        Resolve a task data file path relative to project root.

        Args:
            relative_path: Relative path string from task registry.

        Returns:
            Absolute Path to dataset file.
        """
        project_root = Path(__file__).resolve().parents[1]
        return project_root / relative_path

    def _load_task(self, task_id: str) -> None:
        """
        Load task metadata and dataset into memory.

        Args:
            task_id: Task identifier to load.

        Returns:
            None.
        """
        self.task_id = task_id
        self.task_config = get_task(task_id)
        self.target_schema = self.task_config["target_schema"]
        self.max_steps = int(self.task_config.get("max_steps", DEFAULT_MAX_STEPS))
        self.protected_keys = list(self.target_schema.get("required", []))

        data_path = self._resolve_data_path(self.task_config["data_file"])
        with data_path.open("r", encoding="utf-8") as file_obj:
            self.original_collection = json.load(file_obj)

        self.collection = copy.deepcopy(self.original_collection)

    def _build_obs(self, reward: float, done: bool, status: str) -> SchemaObservation:
        """
        Build observation model for current state.

        Args:
            reward: Reward value for this transition.
            done: Episode termination flag.
            status: Action status string.

        Returns:
            Serialized observation model.
        """
        obs = build_observation(
            collection=self.collection,
            target_schema=self.target_schema,
            step_count=self.step_count,
            max_steps=self.max_steps,
            current_score=self.last_score,
            last_action_status=status,
        )
        obs.reward = reward
        obs.done = done
        return obs

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> SchemaObservation:
        """
        Reset environment state and optionally switch tasks.

        Args:
            seed: Unused reset seed for API compatibility.
            episode_id: Optional external episode identifier.
            **kwargs: Optional reset arguments, including task_id.

        Returns:
            Initial observation for a fresh episode.
        """
        _ = seed

        requested_task = kwargs.get("task_id")
        if isinstance(requested_task, str) and requested_task != self.task_id:
            self._load_task(requested_task)

        self.collection = copy.deepcopy(self.original_collection)
        self.step_count = 0
        self.last_score = calculate_score(self.collection, self.target_schema)
        self.stagnation_counter = 0
        self.last_action_status = "reset"
        self.done = False
        self.episode_id = episode_id or str(uuid4())

        return self._build_obs(reward=0.0, done=False, status=self.last_action_status)

    def step(
        self,
        action: SchemaAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> SchemaObservation:
        """
        Execute one action and update environment state.

        Args:
            action: Action model containing action_type and params.
            timeout_s: Unused timeout argument for API compatibility.
            **kwargs: Extra ignored keyword arguments.

        Returns:
            Observation after action execution.
        """
        _ = timeout_s
        _ = kwargs

        if self.done:
            return self._build_obs(reward=0.0, done=True, status="episode_already_done")

        self.step_count += 1

        if action.action_type == "terminate":
            self.done = True
            self.last_action_status = "success"
            return self._build_obs(reward=0.0, done=True, status=self.last_action_status)

        pre_action_collection = copy.deepcopy(self.collection)
        status = dispatch_action(
            collection=self.collection,
            action_type=action.action_type,
            params=action.params,
            protected_keys=self.protected_keys,
        )
        self.last_action_status = status

        if status.startswith("error"):
            self.collection = pre_action_collection

        new_score = calculate_score(self.collection, self.target_schema)
        delta_score = max(0.0, new_score - self.last_score)
        reward_value = round(delta_score * 10.0, 4)

        if delta_score <= 0.0:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0

        self.last_score = new_score

        if new_score >= 1.0:
            self.done = True
        elif self.stagnation_counter >= STAGNATION_LIMIT:
            self.done = True
        elif self.step_count >= self.max_steps:
            self.done = True

        return self._build_obs(
            reward=reward_value,
            done=self.done,
            status=self.last_action_status,
        )

    @property
    def state(self) -> State:
        """
        Return current state for OpenEnv state endpoint.

        Args:
            None.

        Returns:
            State model containing episode tracking data.
        """
        return State(
            episode_id=self.episode_id,
            step_count=self.step_count,
            task_id=self.task_id,
            collection_size=len(self.collection),
            last_score=self.last_score,
            stagnation_counter=self.stagnation_counter,
            done=self.done,
            last_action_status=self.last_action_status,
        )
