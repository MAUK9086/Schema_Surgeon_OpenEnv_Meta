"""
models.py
---------
Pydantic models for Schema Surgeon.
Defines action, observation, and reward payloads shared by server and client.
Exports SchemaAction, SchemaObservation, and SchemaReward.
"""

from typing import Any, Dict, List

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field


class SchemaAction(Action):
    """
    Represents one action sent by an agent.

    Args:
        action_type: Action name to execute.
        params: Action-specific parameter dictionary.

    Returns:
        None.
    """

    action_type: str = Field(..., description="Action name to dispatch")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class SchemaObservation(Observation):
    """
    Represents the current environment observation.

    Args:
        sample_docs: First 10 documents from the collection.
        global_keys: Global key presence ratios across the collection.
        target_schema: Target JSON schema for current task.
        step_count: Current step count.
        max_steps: Maximum allowed steps.
        current_score: Fraction of valid documents.
        last_action_status: Status text from last action.

    Returns:
        None.
    """

    sample_docs: List[Dict[str, Any]] = Field(default_factory=list)
    global_keys: Dict[str, float] = Field(default_factory=dict)
    target_schema: Dict[str, Any] = Field(default_factory=dict)
    step_count: int = Field(default=0)
    max_steps: int = Field(default=30)
    current_score: float = Field(default=0.0)
    last_action_status: str = Field(default="reset")


class SchemaReward(BaseModel):
    """
    Reward summary model for logging and diagnostics.

    Args:
        value: Step reward value.
        score: Current global score.

    Returns:
        None.
    """

    value: float
    score: float
