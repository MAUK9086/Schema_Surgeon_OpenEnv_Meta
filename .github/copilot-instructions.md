# Copilot Instructions — NoSQL Schema Surgeon
# OpenEnv Hackathon | Team PARADOX

## Critical: Read idea.md First
The complete specification for this project lives in `idea.md` at the project root.
Read it fully before writing any code. Every design decision is documented there.

---

## Project Context

This is an OpenEnv environment scaffolded with `openenv init SchemaSurgeon`.
The scaffold already exists. Do not recreate files that exist — edit them in place.

The OpenEnv framework uses:
- **WebSocket-based communication** (not plain HTTP POST). The `EnvClient` base class
  handles WebSocket connections automatically.
- **`Environment` base class** (server-side) from `openenv.core`
- **`EnvClient` base class** (client-side) from `openenv.core`
- **Pydantic v2 models** for Action and Observation
- **FastAPI + uvicorn** for the server

---

## Existing Scaffold File Map

These files were created by `openenv init`. Edit them, do not recreate:

| File | Role | What to do |
|---|---|---|
| `models.py` | Pydantic Action + Observation models | Replace with SchemaAction, SchemaObservation, SchemaReward |
| `client.py` | EnvClient subclass | Replace with SchemaSurgeonEnv client |
| `__init__.py` | Package exports | Update exports to match new model names |
| `openenv.yaml` | Environment manifest | Replace with full task metadata |
| `server/SchemaSurgeon_environment.py` | Environment logic | Replace with full env implementation |
| `server/app.py` | FastAPI app factory | Update to wire new environment class |
| `server/Dockerfile` | Container definition | Update port to 7860, add data files |
| `server/requirements.txt` | Docker dependencies | Update with all required packages |
| `pyproject.toml` | Package config | Update dependencies list |

New files to CREATE:

| File | Role |
|---|---|
| `server/actions.py` | All action handler functions |
| `server/grader.py` | jsonschema scoring logic |
| `server/obs.py` | Observation builder |
| `server/tasks.py` | Task registry dict |
| `server/data/task1.json` | Pre-generated static dataset (created by generate_data.py) |
| `server/data/task2.json` | Pre-generated static dataset |
| `server/data/task3.json` | Pre-generated static dataset |
| `generate_data.py` | One-time dev utility — never imported by server |
| `inference.py` | Baseline inference script at project root |
| `.github/copilot-instructions.md` | This file |

---

## OpenEnv Compliance Rules

### Server-Side Environment Class
- Must extend `Environment` from `openenv.core` (or `openenv.core.environment`)
- Must implement `reset(self) -> Observation`
- Must implement `step(self, action: Action) -> StepResult`
- Must implement `state(self) -> State`
- `StepResult` contains: `observation`, `reward` (float), `done` (bool), `info` (dict)

### Client-Side Class
- Must extend `EnvClient` from `openenv.core`
- Defines `action_type = SchemaAction`
- Defines `observation_type = SchemaObservation`
- The client is what `inference.py` imports and uses

### Models
- Use **Pydantic v2** (`BaseModel`, `model_dump()` not `.dict()`)
- `SchemaAction` must have `action_type: str` and `params: Dict[str, Any]`
- `SchemaObservation` must have all fields listed in idea.md observation space section
- All fields must be JSON-serializable

### inference.py
- Lives at project root (`SchemaSurgeon/inference.py`), NOT inside `server/`
- Imports `SchemaSurgeonEnv` from `client.py` and uses it with async context manager:
  ```python
  async with SchemaSurgeonEnv(base_url=ENV_BASE_URL) as client:
      result = await client.reset()
      result = await client.step(action)
  ```
- Reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from environment variables
- Uses OpenAI Python SDK with `base_url=API_BASE_URL, api_key=API_KEY`
- Must emit `[START]`, `[STEP]`, `[END]` log lines — exact format in idea.md
- Never hardcode API keys

---

## Code Style Rules (Non-Negotiable)

- Every file: module-level docstring describing purpose, inputs, outputs
- Every function: Google-style docstring with Args and Returns
- All function signatures: fully type-hinted (`from typing import List, Dict, Optional, Tuple, Any`)
- Max line length: 100 characters
- Constants: ALL_CAPS at module level
- Never bare `except:` — always specific: `except jsonschema.ValidationError`, `except KeyError`, etc.
- Use `copy.deepcopy()` before mutating collections in the environment class

---

## Architecture Rules

- `server/SchemaSurgeon_environment.py` — orchestrates actions, grader, obs builder
- `server/actions.py` — pure functions, no I/O, no imports from env
- `server/grader.py` — `calculate_score(collection, schema) -> float` only
- `server/obs.py` — `build_observation(...) -> SchemaObservation` only
- `server/tasks.py` — task registry dict, no logic
- `server/app.py` — FastAPI wiring only, no business logic
- `generate_data.py` — standalone script, NEVER imported by any server module

---

## What NOT To Do

- Do not add a database. All state is in-memory Python `list[dict]`.
- Do not generate data at runtime. Load only from `server/data/task*.json`.
- Do not use `random` inside any server module.
- Do not change `[START]`/`[STEP]`/`[END]` log format.
- Do not put `inference.py` inside `server/`.
- Do not use `except Exception` or bare `except:` in grader.py.
- Do not cache scores — recompute from scratch after every action.
- Do not use port 8000 in Dockerfile — use port **7860** (HF Spaces requirement).
