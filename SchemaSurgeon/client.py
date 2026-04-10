"""
client.py
---------
WebSocket client for Schema Surgeon using OpenEnv EnvClient.
Exports SchemaSurgeonEnv.
"""

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import SchemaAction, SchemaObservation
except ImportError:
    from models import SchemaAction, SchemaObservation


class SchemaSurgeonEnv(EnvClient[SchemaAction, SchemaObservation, State]):
    """
    Client for the Schema Surgeon environment.

    Args:
        None.

    Returns:
        None.
    """

    action_type = SchemaAction
    observation_type = SchemaObservation

    def _step_payload(self, action: SchemaAction) -> Dict[str, Any]:
        """
        Convert action model to step payload.

        Args:
            action: Action object to serialize.

        Returns:
            JSON-serializable payload for step messages.
        """
        return action.model_dump(exclude_none=False)

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[SchemaObservation]:
        """
        Parse server step/reset payload into a typed StepResult.

        Args:
            payload: Raw server response body.

        Returns:
            Parsed StepResult with SchemaObservation.
        """
        obs_data = payload.get("observation", {})
        observation = SchemaObservation(
            **obs_data,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> State:
        """
        Parse state payload into OpenEnv State model.

        Args:
            payload: Raw state response payload.

        Returns:
            Parsed State instance.
        """
        return State(**payload)
