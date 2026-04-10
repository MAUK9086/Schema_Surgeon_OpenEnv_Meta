# Schema_Surgeon_OpenEnv_Meta

# OpenEnv Submission: NoSQL Schema Surgeon

## 1. Environment Description & Motivation
### Motivation
In modern agile development, NoSQL databases like MongoDB often suffer from **"Schema Drift."** As applications evolve, different versions of the same entity (e.g., a `User` object) coexist in the same collection with inconsistent keys, mismatched data types, and redundant fields. 

Manually refactoring millions of documents is error-prone and time-consuming. **The Schema Surgeon** provides a Reinforcement Learning environment designed to train agents to autonomously identify drift, normalize data structures, and validate documents against a target schema without data loss.

### Real-World Utility
This environment models a critical "Day 2" operation for Data Engineers and Backend Developers. By automating schema evolution, organizations can reduce technical debt and ensure data integrity for downstream analytics and machine learning pipelines.

---

## 2. Action and Observation Spaces

### Observation Space
The observation is a `Typed Model` containing:
* **Sample Documents:** A list of `n` documents (JSON/Dict) currently in the "working buffer."
* **Target Schema:** A blueprint (JSON Schema/Pydantic structure) that the documents must eventually match.
* **Drift Report:** A summary of inconsistencies (e.g., "Key 'user_age' exists in 40% of docs, 'age' in 60%").
* **System Status:** Remaining steps in the episode and current validation success rate.

### Action Space
The agent interacts with the environment through a set of atomic refactoring tools:
* **`rename_key(old_name, new_name)`**: Standardizes inconsistent naming conventions.
* **`cast_type(key, target_type)`**: Converts data (e.g., String "25" to Integer 25).
* **`nest_fields(keys, parent_key)`**: Moves flat keys into a sub-object (e.g., `city`, `zip` -> `address`).
* **`delete_key(key)`**: Removes deprecated or redundant fields.
* **`commit_validation()`**: Triggers the grader to evaluate the current state against the Target Schema.

---

## 3. Task Descriptions & Difficulty Levels



The environment includes three specific tasks with programmatic graders:

| Task | Difficulty | Objective | Grader Criteria |
| :--- | :--- | :--- | :--- |
| **Standardize Naming** | **Easy** | Rename fragmented keys like `u_name`, `name`, and `full_name` to a single `name` key. | Success = 1.0 if 100% of docs have the `name` key and old keys are deleted. |
| **Type Normalization** | **Medium** | Ensure all `timestamp` fields are ISO strings and `price` fields are Floats. | Success = 1.0 if all specified keys pass type-validation. Partial reward for each correctly cast doc. |
| **Structural Migration** | **Hard** | Flatten deep-nested "legacy" objects and merge duplicate records based on a unique identifier. | Success = 1.0 if the final collection matches the Target Schema depth and uniqueness constraints. |

---

## 4. Reward Function & Design
The reward function is **Dense** and **Shaped** to provide feedback throughout the episode:

* **Progress Signal:** Each action that increases the percentage of documents matching the Target Schema grants a positive reward (e.g., `+0.1` per document normalized).
* **Efficiency Bonus:** A small positive reward for completing the task in the fewest possible steps.
* **Safety Penalty:** A severe penalty (`-1.0`) and immediate termination (`done=True`) if the agent deletes a key marked as "Required" in the Target Schema before migrating its data.
* **Invalid Action Penalty:** A small negative reward (`-0.05`) for attempting to rename a key that does not exist.

---

## 5. Implementation & Spec Compliance
* **OpenEnv Spec:** The project implements the `step()`, `reset()`, and `state()` endpoints via a FastAPI wrapper as required for Hugging Face Space deployment.
* **Pydantic Models:** All Observation, Action, and Reward objects are strictly typed.
* **Containerization:** A multi-stage `Dockerfile` is provided to ensure the environment stays under the 8GB memory limit.
* **Validation:** Passes `openenv validate` with zero warnings.

---

## 6. Setup and Usage Instructions
1.  **Local Development:**
    ```bash
    pip install -r requirements.txt
    python main.py  # Starts the local OpenEnv server
    ```
2.  **Inference:**
    Ensure `OPENAI_API_KEY`, `API_BASE_URL`, and `MODEL_NAME` are set.
    ```bash
    python inference.py
    ```
3.  **Docker Build:**
    ```bash
    docker build -t openenv-schema-surgeon .
    docker run -p 8000:8000 openenv-schema-surgeon
    ```

---

## 7. Baseline Scores (Tentative)
* **Task 1 (Easy):** 0.92/1.0
* **Task 2 (Medium):** 0.75/1.0
* **Task 3 (Hard):** 0.45/1.0
*(Scores generated using GPT-4o-mini as the baseline agent)*

## 8. Comparison
While tools like Liquibase handle schema versioning, they require manual human intervention for every change. The Schema Surgeon moves beyond static scripts by providing an OpenEnv environment to evaluate and train agents capable of autonomous, reasoning-based schema evolution in high-drift NoSQL environments.
