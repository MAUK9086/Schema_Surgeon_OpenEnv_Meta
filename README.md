---
title: Schema Surgeon OpenEnv
emoji: 💉
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
tags:
- openenv
---

# NoSQL Schema Surgeon (V5-Final)

OpenEnv Hackathon | Team PARADOX

## Why We Built This
Schema drift in NoSQL systems is not a cute data-cleaning problem. It is a production nightmare.

When Mongo or Dynamo documents drift across app versions, dashboards look fine until they do not. Feature pipelines start dropping rows quietly. Aggregations start mixing strings and numbers in the same field. Sometimes the API still returns 200 and you only find out a week later that downstream analytics is wrong.

That is the whole reason this environment exists. We wanted a deterministic benchmark where an agent has to do what an on-call data engineer does in real life: fix drifted collections without making things worse.

## What This Environment Is
Schema Surgeon is an OpenEnv environment where an agent applies global transformations to a noisy NoSQL-style collection and gets scored by JSON Schema pass ratio.

- Protocol: WebSocket (`/ws`)
- Runtime: FastAPI + uvicorn
- Port: 7860
- Dataset size: 50 documents per task

## Tasks
There are three tasks with increasing complexity.

1. Task 1 (easy): key naming normalization.
2. Task 2 (medium): type correction on required fields.
3. Task 3 (hard): naming + type + nested-structure alignment under heavy noise.

## Task 3 Is A Bit Of A Beast
Task 3 is intentionally hard. We made it that way because the easy version was getting solved too quickly and was not telling us much about real utility.

What makes Task 3 difficult:

- Ambiguous types for `age` in the same collection:
  - string values like `"25"`
  - boolean values like `true`
  - nested object values like `{"val": 25}`
- Nested conflicts for tier:
  - some docs have root `tier`
  - some have `profile.tier`
  - some have `profile` without `tier`
  - some even have both root and nested tier (conflict)
- Realistic noise fields:
  - `legacy_flags`
  - `audit` event logs

So the agent cannot just memorize one cleanup recipe and call it done.

## Action Space
The environment supports these actions:

- `rename_and_merge`
- `cast_type`
- `flatten_field`
- `delete_key`
- `terminate`

These are global operations over the collection, not per-document edits.

## Observation Space
Each step observation includes:

- sample docs (first 10 docs)
- global key presence ratios across the full collection
- target JSON schema
- step counters and status
- current score

The global key ratios are especially important for strategy. They tell the agent what is actually common across all docs, not just what it sees in the sample.

## Reward and Scoring Logic
We use dense rewards so the model gets feedback before full completion.

- Base reward: proportional to positive score delta
- `no_op` penalty: `-0.1` (helps stop looping on redundant actions)
- destructive delete penalty: `-0.5` for bad delete attempts on required fields under the configured condition
- score is clamped to `[0.001, 0.999]` for validator compliance (never exact 0.0 or 1.0)

This keeps the signal useful for RL while still passing strict evaluator checks.

## Baseline Results
Our `gpt-4o-mini` baseline starts around **0.380** on Task 1 and then shows clear incremental improvement before termination.

It is not perfect, but it does improve step-by-step in a way that is easy to inspect from logs.

## Logging Format
The script emits strict evaluator-friendly logs:

- `[START]`
- `[STEP]`
- `[END]`

`[STEP]` logs include compact action JSON, reward, done flag, and error field.

## Setup
### Local
1. Create/activate your Python environment.
2. Install dependencies.
3. Run the server on port 7860.
4. Run `inference.py` with required env vars.

### Hugging Face Spaces
Set `HF_TOKEN` as a Space Secret.

Required variables for inference:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`
- `ENV_BASE_URL`

## Deployment Notes
- Docker is configured for port 7860.
- OpenEnv manifest is configured for WebSocket protocol.
- `/health` endpoint is kept for liveness checks.

## Submission Checklist
- [ ] `openenv validate` passes
- [ ] Task data files are committed (`task1.json`, `task2.json`, `task3.json`)
- [ ] WebSocket config is present in `openenv.yaml`
- [ ] Score clamping is active (`0.001` to `0.999`)
- [ ] Dense rewards + penalties are active
- [ ] Logs emit `[START]`, `[STEP]`, `[END]`
- [ ] Docker build succeeds
- [ ] Server starts on port 7860
- [ ] `HF_TOKEN` is set as a Hugging Face Secret

If you are reading this as a judge: yes, we know this task is mean. That was intentional.
