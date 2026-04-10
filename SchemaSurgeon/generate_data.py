"""
generate_data.py
----------------
One-time dataset generator for Schema Surgeon.
Builds deterministic, realistic e-commerce user records with nested objects
and arrays, then applies task-specific schema drift patterns.
"""

import copy
import json
import random
from pathlib import Path
from typing import Any, Dict, List

from faker import Faker

SEED: int = 42
NUM_DOCS: int = 50
OUTPUT_DIR: Path = Path(__file__).resolve().parent / "server" / "data"

FAKER = Faker()
Faker.seed(SEED)
FAKER.seed_instance(SEED)

PRODUCT_NAMES: List[str] = [
    "wireless_mouse",
    "noise_canceling_headphones",
    "ergonomic_keyboard",
    "smart_watch",
    "gaming_monitor",
    "usb_c_hub",
    "portable_ssd",
    "desk_lamp",
    "webcam_hd",
    "mechanical_switches",
]
TIERS: List[str] = ["bronze", "silver", "gold", "platinum"]

def build_base_record(index: int) -> Dict[str, Any]:
    """
    Build a clean canonical e-commerce user record.

    Args:
        index: Document index used for deterministic user_id generation.

    Returns:
        Base record dictionary with nested contact_info and purchase_history.
    """
    purchases: List[Dict[str, Any]] = []
    for _ in range(random.randint(2, 4)):
        purchases.append(
            {
                "item": random.choice(PRODUCT_NAMES),
                "cost": round(random.uniform(5.0, 500.0), 2),
            }
        )

    total_spend = round(sum(entry["cost"] for entry in purchases), 2)

    return {
        "user_id": f"user_{index:03d}",
        "age": random.randint(18, 80),
        "lifetime_value": round(total_spend * random.uniform(1.05, 2.0), 2),
        "tier": random.choice(TIERS),
        "contact_info": {
            "email": FAKER.email(),
            "phone": FAKER.phone_number(),
        },
        "purchase_history": purchases,
    }


def apply_task1_drift(record: Dict[str, Any], force_pattern: int = -1) -> Dict[str, Any]:
    """
    Apply naming drift for task1.

    Args:
        record: Canonical base record.
        force_pattern: Optional deterministic variant selector.

    Returns:
        Drifted record for task1.
    """
    doc = copy.deepcopy(record)
    pattern = force_pattern if force_pattern >= 0 else random.randint(0, 2)
    if pattern == 0:
        doc["uid"] = doc.pop("user_id")
    elif pattern == 1:
        doc["u_id"] = doc.pop("user_id")
    return doc


def apply_task2_drift(record: Dict[str, Any], force_pattern: int = -1) -> Dict[str, Any]:
    """
    Apply type drift for task2 while preserving nested complexity.

    Args:
        record: Canonical base record.
        force_pattern: Optional deterministic variant selector.

    Returns:
        Drifted record for task2.
    """
    doc = copy.deepcopy(record)
    pattern = force_pattern if force_pattern >= 0 else random.randint(0, 2)
    if pattern in (0, 2):
        doc["age"] = str(doc["age"])
    if pattern in (1, 2):
        doc["lifetime_value"] = str(doc["lifetime_value"])
    return doc


def apply_task3_drift(record: Dict[str, Any], force_pattern: int = -1) -> Dict[str, Any]:
    """
    Apply combined naming, type, and structural drift for task3.

    Args:
        record: Canonical base record.
        force_pattern: Optional deterministic variant selector.

    Returns:
        Drifted record for task3.
    """
    doc = copy.deepcopy(record)
    pattern = force_pattern if force_pattern >= 0 else random.randint(0, 5)

    if pattern in (0, 1, 4):
        doc["uid"] = doc.pop("user_id")
    elif pattern in (2, 3, 5):
        doc["u_id"] = doc.pop("user_id")

    if pattern in (0, 2, 5):
        doc["age"] = str(doc["age"])
    if pattern in (1, 3, 4):
        doc["lifetime_value"] = str(doc["lifetime_value"])

    if pattern in (0, 1, 2, 3):
        doc["profile"] = {"tier": doc.pop("tier")}

    return doc


def build_golden_10(task_id: int) -> List[Dict[str, Any]]:
    """
    Build deterministic golden examples for each task.

    Args:
        task_id: Task number in [1, 2, 3].

    Returns:
        Ten representative records for the task.
    """
    golden: List[Dict[str, Any]] = []
    for idx in range(1, 11):
        base = build_base_record(idx)
        if task_id == 1:
            golden.append(apply_task1_drift(base, force_pattern=(idx - 1) % 3))
        elif task_id == 2:
            golden.append(apply_task2_drift(base, force_pattern=(idx - 1) % 3))
        else:
            golden.append(apply_task3_drift(base, force_pattern=(idx - 1) % 6))
    return golden


def generate_bulk(golden_10: List[Dict[str, Any]], task_id: int) -> List[Dict[str, Any]]:
    """
    Generate task dataset with fixed seed and deterministic mutation patterns.

    Args:
        golden_10: Curated first ten documents.
        task_id: Task index in [1, 2, 3].

    Returns:
        List of exactly 50 documents.
    """
    random.seed(SEED + task_id)
    Faker.seed(SEED + task_id)
    FAKER.seed_instance(SEED + task_id)
    docs = copy.deepcopy(golden_10)

    for idx in range(10, NUM_DOCS):
        base = build_base_record(idx)
        if task_id == 1:
            doc = apply_task1_drift(base)
        elif task_id == 2:
            doc = apply_task2_drift(base)
        else:
            doc = apply_task3_drift(base)

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
    random.seed(SEED)
    Faker.seed(SEED)
    FAKER.seed_instance(SEED)

    golden_10_task1 = build_golden_10(task_id=1)
    golden_10_task2 = build_golden_10(task_id=2)
    golden_10_task3 = build_golden_10(task_id=3)

    datasets = {
        "task1": generate_bulk(golden_10_task1, 1),
        "task2": generate_bulk(golden_10_task2, 2),
        "task3": generate_bulk(golden_10_task3, 3),
    }

    for dataset_name, dataset_data in datasets.items():
        write_dataset(dataset_name, dataset_data)


if __name__ == "__main__":
    main()
