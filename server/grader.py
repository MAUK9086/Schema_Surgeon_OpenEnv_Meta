"""
grader.py
---------
Scoring logic for Schema Surgeon.
Validates each document against a JSON Schema and computes pass ratio.
Exports calculate_score().
"""

from typing import Any, Dict, List

import jsonschema

MIN_SCORE: float = 0.001
MAX_SCORE: float = 0.999


def calculate_score(collection: List[Dict[str, Any]], schema: Dict[str, Any]) -> float:
    """
    Compute the fraction of documents that pass JSON Schema validation.

    Args:
        collection: Current list of documents.
        schema: Target JSON Schema.

    Returns:
        Fraction of valid documents in [0.0, 1.0].
    """
    if not collection or not isinstance(collection, list):
        return MIN_SCORE

    if not schema or not isinstance(schema, dict):
        return MIN_SCORE

    valid_count = 0
    evaluated_count = 0

    for doc in collection:
        if not isinstance(doc, dict):
            continue

        evaluated_count += 1
        try:
            jsonschema.validate(instance=doc, schema=schema)
            valid_count += 1
        except (jsonschema.ValidationError, jsonschema.SchemaError, TypeError, ValueError):
            continue

    if evaluated_count == 0:
        return MIN_SCORE

    raw_score = round(valid_count / evaluated_count, 6)
    return max(MIN_SCORE, min(MAX_SCORE, raw_score))
