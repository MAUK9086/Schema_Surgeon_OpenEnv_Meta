"""
tasks.py
--------
Task registry for Schema Surgeon.
Defines static task metadata, target schemas, and dataset file paths.
Exports TASKS and get_task().
"""

from typing import Any, Dict

TASKS: Dict[str, Dict[str, Any]] = {
    "task1": {
        "name": "The Standardizer",
        "difficulty": "easy",
        "data_file": "server/data/task1.json",
        "max_steps": 30,
        "description": (
            "Normalize all key naming variants (uid, u_id) to user_id. "
            "All 50 documents must contain only user_id as the identifier key."
        ),
        "target_schema": {
            "type": "object",
            "required": ["user_id"],
            "properties": {
                "user_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    "task2": {
        "name": "The Type-Checker",
        "difficulty": "medium",
        "data_file": "server/data/task2.json",
        "max_steps": 30,
        "description": (
            "Keys are already standardized. Fix type mismatches: "
            "age must be integer, price must be number (float), user_id must be string."
        ),
        "target_schema": {
            "type": "object",
            "required": ["user_id", "age", "price"],
            "properties": {
                "user_id": {"type": "string"},
                "age": {"type": "integer"},
                "price": {"type": "number"},
            },
            "additionalProperties": True,
        },
    },
    "task3": {
        "name": "The Full Architect",
        "difficulty": "hard",
        "data_file": "server/data/task3.json",
        "max_steps": 30,
        "description": (
            "Full schema alignment. Fix key naming drift, type mismatches, "
            "and nesting drift (metadata.version must be flattened to version). "
            "All 4 required fields must be present with correct types."
        ),
        "target_schema": {
            "type": "object",
            "required": ["user_id", "age", "price", "version"],
            "properties": {
                "user_id": {"type": "string"},
                "age": {"type": "integer"},
                "price": {"type": "number"},
                "version": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
}


def get_task(task_id: str) -> Dict[str, Any]:
    """
    Retrieve task configuration by ID.

    Args:
        task_id: One of task1, task2, or task3.

    Returns:
        Task configuration dictionary.
    """
    if task_id not in TASKS:
        valid_tasks = ", ".join(sorted(TASKS.keys()))
        raise KeyError(f"Unknown task_id '{task_id}'. Valid options: {valid_tasks}")
    return TASKS[task_id]
