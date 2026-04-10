"""
generate_data.py
----------------
One-time dataset generator for Schema Surgeon.
Creates deterministic static task datasets in server/data and is never imported
by runtime server modules.
"""

import copy
import json
import random
from pathlib import Path
from typing import Any, Dict, List

SEED: int = 42
NUM_DOCS: int = 50
OUTPUT_DIR: Path = Path(__file__).resolve().parent / "server" / "data"

GOLDEN_10_TASK1: List[Dict[str, Any]] = [
    {"uid": "user_001", "age": 25, "price": 19.99, "version": "v1"},
    {"u_id": "user_002", "age": 30, "price": 25.0, "version": "v2"},
    {"user_id": "user_003", "age": 22, "price": 9.99, "version": "v1"},
    {"uid": "user_004", "age": 45, "price": 50.0, "version": "v1"},
    {"u_id": "user_005", "age": 19, "price": 5.5, "version": "v2"},
    {"uid": "user_006", "age": 33, "price": 12.0, "version": "v1"},
    {"user_id": "user_007", "age": 28, "price": 8.75, "version": "v2"},
    {"u_id": "user_008", "age": 55, "price": 100.0, "version": "v1"},
    {"uid": "user_009", "age": 41, "price": 60.0, "version": "v1"},
    {"u_id": "user_010", "age": 37, "price": 33.3, "version": "v2"},
]

GOLDEN_10_TASK2: List[Dict[str, Any]] = [
    {"user_id": "user_001", "age": "25", "price": "19.99", "version": "v1"},
    {"user_id": "user_002", "age": 30, "price": "25.0", "version": "v2"},
    {"user_id": "user_003", "age": "22", "price": 9.99, "version": "v1"},
    {"user_id": "user_004", "age": 45, "price": "50.0", "version": "v1"},
    {"user_id": "user_005", "age": "19", "price": 5.5, "version": "v2"},
    {"user_id": "user_006", "age": "33", "price": "12.0", "version": "v1"},
    {"user_id": "user_007", "age": 28, "price": 8.75, "version": "v2"},
    {"user_id": "user_008", "age": "55", "price": "100.0", "version": "v1"},
    {"user_id": "user_009", "age": 41, "price": "60.0", "version": "v1"},
    {"user_id": "user_010", "age": "37", "price": "33.3", "version": "v2"},
]

GOLDEN_10_TASK3: List[Dict[str, Any]] = [
    {
        "uid": "user_001",
        "age": "25",
        "price": "19.99",
        "metadata": {"version": "v1"},
    },
    {
        "u_id": "user_002",
        "age": 30,
        "price": "25.0",
        "metadata": {"version": "v2"},
    },
    {"user_id": "user_003", "age": "22", "price": 9.99, "version": "v1"},
    {
        "uid": "user_004",
        "age": 45,
        "price": "50.0",
        "metadata": {"version": "v1"},
    },
    {
        "u_id": "user_005",
        "age": "19",
        "price": 5.5,
        "metadata": {"version": "v2"},
    },
    {"uid": "user_006", "age": "33", "price": "12.0", "version": "v1"},
    {
        "user_id": "user_007",
        "age": 28,
        "price": 8.75,
        "metadata": {"version": "v2"},
    },
    {
        "u_id": "user_008",
        "age": "55",
        "price": "100.0",
        "metadata": {"version": "v1"},
    },
    {"uid": "user_009", "age": 41, "price": "60.0", "version": "v1"},
    {
        "u_id": "user_010",
        "age": "37",
        "price": "33.3",
        "metadata": {"version": "v2"},
    },
]


def generate_bulk(golden_10: List[Dict[str, Any]], task_id: int) -> List[Dict[str, Any]]:
    """
    Generate task dataset with fixed seed and deterministic mutation patterns.

    Args:
        golden_10: Curated first ten documents.
        task_id: Task index in [1, 2, 3].

    Returns:
        List of exactly 50 documents.
    """
    random.seed(SEED)
    docs = copy.deepcopy(golden_10)

    for idx in range(10, NUM_DOCS):
        uid_key = random.choice(["uid", "u_id", "user_id"])
        age_val = random.randint(18, 65)
        price_val = round(random.uniform(1.0, 200.0), 2)

        if task_id == 1:
            doc = {
                uid_key: f"user_{idx:03d}",
                "age": age_val,
                "price": price_val,
                "version": random.choice(["v1", "v2"]),
            }
        elif task_id == 2:
            doc = {
                "user_id": f"user_{idx:03d}",
                "age": str(age_val) if random.random() < 0.3 else age_val,
                "price": str(price_val) if random.random() < 0.3 else price_val,
                "version": random.choice(["v1", "v2"]),
            }
        else:
            version_val = random.choice(["v1", "v2"])
            doc = {
                uid_key: f"user_{idx:03d}",
                "age": str(age_val) if random.random() < 0.3 else age_val,
                "price": str(price_val) if random.random() < 0.3 else price_val,
            }
            if random.random() < 0.5:
                doc["metadata"] = {"version": version_val}
            else:
                doc["version"] = version_val

        docs.append(doc)

    return docs


def write_dataset(name: str, data: List[Dict[str, Any]]) -> None:
    """
    Write one dataset JSON file.

    Args:
        name: Task file prefix, such as task1.
        data: Dataset content to write.

    Returns:
        None.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.json"
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, indent=2)
    print(f"Written: {output_path} ({len(data)} docs)")


def main() -> None:
    """
    Generate all task datasets and write them under server/data.

    Args:
        None.

    Returns:
        None.
    """
    datasets = {
        "task1": generate_bulk(GOLDEN_10_TASK1, 1),
        "task2": generate_bulk(GOLDEN_10_TASK2, 2),
        "task3": generate_bulk(GOLDEN_10_TASK3, 3),
    }

    for dataset_name, dataset_data in datasets.items():
        write_dataset(dataset_name, dataset_data)


if __name__ == "__main__":
    main()
