"""
actions.py
----------
Deterministic, idempotent global action handlers for Schema Surgeon.
Contains pure in-memory collection transforms and a dispatcher.
Exports rename_and_merge(), cast_type(), flatten_field(), delete_key(), dispatch_action().
"""

from typing import Any, Dict, List


def rename_and_merge(collection: List[Dict[str, Any]], source: str, target: str) -> str:
    """
    Rename source key to target key across all documents.

    Args:
        collection: Mutable list of document dictionaries.
        source: Key to rename.
        target: Destination key.

    Returns:
        Status string indicating whether any document changed.
    """
    modified = 0
    for doc in collection:
        if source in doc:
            if target not in doc:
                doc[target] = doc.pop(source)
            else:
                del doc[source]
            modified += 1
    return "success" if modified > 0 else "no_op"


def cast_type(
    collection: List[Dict[str, Any]],
    key: str,
    target_type: str,
    default_value: Any = None,
) -> str:
    """
    Cast values for a key to a target primitive type across all documents.

    Args:
        collection: Mutable list of document dictionaries.
        key: Key whose values should be cast.
        target_type: One of int, float, or str.
        default_value: Fallback value when cast fails.

    Returns:
        Status string indicating success, no-op, or parameter error.
    """
    type_map = {"int": int, "float": float, "str": str}
    if target_type not in type_map:
        return f"error: unsupported target_type '{target_type}'. Use int, float, or str."

    caster = type_map[target_type]
    modified = 0

    for doc in collection:
        if key not in doc:
            continue

        original = doc[key]
        try:
            casted = caster(original)
            if casted != original or type(casted) is not type(original):
                doc[key] = casted
                modified += 1
        except (TypeError, ValueError):
            doc[key] = default_value
            modified += 1

    return "success" if modified > 0 else "no_op"


def flatten_field(collection: List[Dict[str, Any]], parent_key: str, child_key: str) -> str:
    """
    Promote a nested field from parent_key.child_key to root child_key.

    Args:
        collection: Mutable list of document dictionaries.
        parent_key: Parent nested object key.
        child_key: Child key inside nested object.

    Returns:
        Status string indicating whether any document changed.
    """
    modified = 0
    for doc in collection:
        if parent_key in doc and isinstance(doc[parent_key], dict):
            nested_obj = doc[parent_key]
            if child_key in nested_obj:
                doc[child_key] = nested_obj.pop(child_key)
                if not nested_obj:
                    del doc[parent_key]
                modified += 1
    return "success" if modified > 0 else "no_op"


def delete_key(collection: List[Dict[str, Any]], key: str, protected_keys: List[str]) -> str:
    """
    Delete a key from all documents unless it is protected.

    Args:
        collection: Mutable list of document dictionaries.
        key: Key to remove globally.
        protected_keys: Keys that cannot be deleted.

    Returns:
        Status string indicating success, no-op, or protected-key error.
    """
    if key in protected_keys:
        return (
            f"error: '{key}' is protected (required by target schema) "
            "and cannot be deleted."
        )

    modified = 0
    for doc in collection:
        if key in doc:
            del doc[key]
            modified += 1

    return "success" if modified > 0 else "no_op"


def dispatch_action(
    collection: List[Dict[str, Any]],
    action_type: str,
    params: Dict[str, Any],
    protected_keys: List[str],
) -> str:
    """
    Dispatch an action request to the corresponding handler.

    Args:
        collection: Mutable list of document dictionaries.
        action_type: Action name.
        params: Action parameter payload.
        protected_keys: Keys blocked from delete operations.

    Returns:
        Status string from handler.
    """
    if action_type == "rename_and_merge":
        source = params.get("source")
        target = params.get("target")
        if not source or not target:
            return "error: rename_and_merge requires 'source' and 'target' params."
        return rename_and_merge(collection, source, target)

    if action_type == "cast_type":
        key = params.get("key")
        target_type = params.get("target_type")
        default_value = params.get("default_value", None)
        if not key or not target_type:
            return "error: cast_type requires 'key' and 'target_type' params."
        return cast_type(collection, key, target_type, default_value)

    if action_type == "flatten_field":
        parent_key = params.get("parent_key")
        child_key = params.get("child_key")
        if not parent_key or not child_key:
            return "error: flatten_field requires 'parent_key' and 'child_key' params."
        return flatten_field(collection, parent_key, child_key)

    if action_type == "delete_key":
        key = params.get("key")
        if not key:
            return "error: delete_key requires 'key' param."
        return delete_key(collection, key, protected_keys)

    return f"error: unknown action_type '{action_type}'."
