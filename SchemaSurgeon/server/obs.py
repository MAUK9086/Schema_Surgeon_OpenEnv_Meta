"""
obs.py
------
Observation builders for Schema Surgeon.
Builds global key prevalence and per-step observation payloads.
Exports build_global_keys() and build_observation().
"""

from typing import Any, Dict, List

try:
    from models import SchemaObservation
except ModuleNotFoundError:
    from SchemaSurgeon.models import SchemaObservation

GOLDEN_SAMPLE_SIZE: int = 10


def build_global_keys(collection: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute key presence ratio across the full collection.

    Args:
        collection: Full in-memory document collection.

    Returns:
        Mapping from key names to document presence ratio.
    """
    if not collection:
        return {}

    key_counts: Dict[str, int] = {}
    total_docs = len(collection)

    for doc in collection:
        for key in doc.keys():
            key_counts[key] = key_counts.get(key, 0) + 1

    return {key: round(count / total_docs, 4) for key, count in key_counts.items()}


def build_observation(
    collection: List[Dict[str, Any]],
    target_schema: Dict[str, Any],
    step_count: int,
    max_steps: int,
    current_score: float,
    last_action_status: str,
) -> SchemaObservation:
    """
    Build the step observation model from current environment state.

    Args:
        collection: Full in-memory document collection.
        target_schema: JSON Schema objective.
        step_count: Current episode step count.
        max_steps: Maximum steps allowed.
        current_score: Current global validation score.
        last_action_status: Status emitted by previous action.

    Returns:
        SchemaObservation for client consumption.
    """
    return SchemaObservation(
        sample_docs=collection[:GOLDEN_SAMPLE_SIZE],
        global_keys=build_global_keys(collection),
        target_schema=target_schema,
        step_count=step_count,
        max_steps=max_steps,
        current_score=current_score,
        last_action_status=last_action_status,
    )
