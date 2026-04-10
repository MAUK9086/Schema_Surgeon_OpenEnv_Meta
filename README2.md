# OpenEnv Submission: NoSQL Schema Surgeon (V4 - Final Spec)

## 1. Task Logic & Dataset curation (Fixes 3A)
To ensure the agent sees all patterns without randomness, we use a **Curated Static Dataset**.
* **Implementation:** The dataset is a JSON file containing exactly 50 documents. 
* **The "Golden 10":** The first 10 documents are manually curated to contain at least one instance of every drift type (type mismatch, key naming drift, nesting drift). 
* **Determinism:** The index of these documents is fixed. The agent always sees the same "Golden 10" in the observation.

## 2. Action Mechanics & Data Cleansing (Fixes 3B, 3E)
We have refined the actions to prevent "deadlock" states where the agent cannot reach 100% success.

* **`rename_and_merge(source, target)`**: 
    * If a document has both `source` and `target`, the value in `source` is discarded (Target is the "Source of Truth").
    * This allows for 100% cleanup of legacy keys.
* **`cast_type(key, target_type, default_value=None)`**:
    * If casting fails (e.g., "N/A" -> int), the value is replaced by `default_value` (or `null` if not provided).
    * **Why:** This ensures the agent can always reach a valid schema state ($S=1.0$), even with "dirty" data.
* **`delete_key(key)`**:
    * **Strict Constraint:** The environment maintains a `protected_keys` list (derived from the Target Schema's `required` field). 
    * If an agent attempts to delete a protected key, the action returns an error message in `info` and no data is deleted.

## 3. The "Anti-Stagnation" Engine (Fixes 3D, 3H)
To prevent infinite loops and ensure the 20-minute runtime limit:
* **Stagnation Counter:** If the Global Score ($S$) does not increase for **3 consecutive steps**, the environment issues a "Stagnation Warning."
* **Auto-Termination:** If no improvement is made for **5 consecutive steps**, the episode terminates with `done=True`.
* **Step Limit:** Hard cap at 20 steps per task.

## 4. Balanced Observation (Fixes 3F)
We have "blurred" the Global Stats to ensure the agent still has to reason.
* **Instead of:** `{"uid": 0.2, "user_id": 0.8}`
* **The Agent Sees:** `{"uid": "PRESENT", "user_id": "PRESENT"}` 
* **Reasoning Requirement:** The agent knows *which* keys exist globally but must look at the "Golden 10" sample to understand the *relationship* and *types* of those keys.

---

## 5. Reward & Grader Implementation (Fixes 3C, 3G)

### Reward Scaling ($R$)
To handle different dataset sizes consistently, the reward is normalized:
$$R_t = \text{max}(0, (S_t - S_{t-1})) \times 10$$
* This ensures that a full migration always results in a total cumulative reward of $10.0$ (plus the completion bonus), regardless of whether the dataset has 20 or 200 documents.

### The Grader Script (`grader.py`)
```python
import jsonschema

def calculate_score(current_collection, target_schema):
    valid_count = 0
    for doc in current_collection:
        try:
            jsonschema.validate(instance=doc, schema=target_schema)
            valid_count += 1
        except jsonschema.ValidationError:
            continue
    return valid_count / len(current_collection)
```

---

## 6. Detailed Implementation Steps for Team PARADOX

### Step 1: Environment Setup (`env.py`)
* Use a simple Python `list` of `dicts` to hold the "Database."
* Implement the `reset()` method to reload the original "Messy" JSON file.

### Step 2: Action Implementation (`actions.py`)
* Write the logic for `rename_and_merge`. 
* **Crucial:** Use `copy.deepcopy()` on the collection at each step to ensure that if an action fails, you can roll back the state (though V4 actions are global/atomic, deepcopy is safer).

### Step 3: Observation Builder (`obs.py`)
* Extract the first 10 docs.
* Loop through the entire collection once to find all unique keys for the "Global Stats" (the "PRESENT" tags).

### Step 4: Baseline Inference (`inference.py`)
* Use a clear System Prompt:
  > "You are a Database Migration Agent. You will see 10 sample docs and a list of keys present in the DB. Your goal is to make every doc pass the provided JSON Schema using the available tools."

---

## 7. Submission Checklist (The "Win" Gate)
* [ ] **Container Size:** Keep the Docker image under 1GB.
* [ ] **Validation:** Run `openenv validate` after every major code change.
* [ ] **Logs:** Ensure `inference.py` prints `[START]`, `[STEP]`, and `[END]` exactly as specified in the hackathon rules.
* [ ] **README:** Use the V4 Motivation and Utility sections for your documentation.
