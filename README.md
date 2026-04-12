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
**OpenEnv Hackathon | Team PARADOX**

## Why This Matters (The "Why")
Schema drift in NoSQL ecosystems (like MongoDB, DynamoDB, or Firestore) is not just some "cleanup task" for interns. It is a production nightmare that kills data quality silently. In a flexible schema environment, different application versions write different document shapes over time, maybe a dev renamed `uid` to `user_id` in one microservice but forgot the other, or a bug started saving `age` as a string instead of an int.

This isn't just annoying; it is expensive. According to **Gartner research**, poor data quality costs organizations an average of **$12.9 million per year**. A recent **2025 IBM report** found that over 25% of organizations lose more than **$5 million annually** specifically due to these discrepancies, with some reporting losses over $25 million. You can read the full breakdown of these costs here: [IBM: The True Cost of Poor Data Quality](https://www.ibm.com/think/insights/cost-of-poor-data-quality).

We built **Schema Surgeon** because manual migration scripts are prone to human error. We need agents that can act as autonomous **Database Reliability Engineers (DRE)** to observe a messy collection and apply global transformations safely without making the drift worse.

## Task Difficulty: From Easy to "Mean"
We have three tasks that get progressively harder. We intentionally made Task 3 a bit of a beast because we noticed frontier models were solving the easy stuff too fast.

1. **Task 1 (The Standardizer - Easy)**: Basic key naming drift. Agent needs to merge `uid` and `u_id` into a single `user_id` across 50 docs.
2. **Task 2 (The Type-Checker - Medium)**: Keys are fine, but types are a mess. `age` must be an integer and `price` must be a number (float).
3. **Task 3 (The Full Architect - Hard)**: This is where things get real. We introduced:
   - **Ambiguous types**: In the same collection, `age` might be a string (`"25"`), a boolean (`true`), or even a nested object (`{"val": 25}`).
   - **Nested Conflicts**: Some records use a root `tier` key, while others have it hidden in `profile.tier`.
   - **Realistic Noise**: We added 50 documents with fields like `legacy_flags` and `audit` logs to distract the agent and test its ability to focus on the target schema.

## Environment Design & Reward Shaping
We did not want a sparse reward where the agent only gets a point at the very end. That is useless for learning. Instead, we use a **Dense Reward Function**.

- **Positive Reinforcement**: The agent gets a reward proportional to the positive delta in the global score (the pass ratio of the 50 documents).
- **No-Op Penalty (-0.1)**: If an agent issues an action that changes nothing (like trying to rename a key that doesn't exist), it gets penalized. This stops infinite loops.
- **Destructive Penalty (-0.5)**: If the agent tries to delete a key that is actually required by the target schema, it takes a heavy hit. A real DRE would get fired for that, so the agent should too.
- **Safe Clamping**: Scores are strictly clamped between **0.001 and 0.999**. This ensures we never return an exact 0.0 or 1.0, satisfying the strict Phase 2 validator while still giving a clear success signal.

## Action & Observation Space
The environment uses typed Pydantic models to keep things clean.

### Action Space
- `rename_and_merge`: Consolidate two keys globally.
- `cast_type`: Convert field types (int, float, str) with a fallback default.
- `flatten_field`: Promote a nested field (like `profile.tier`) to the root.
- `delete_key`: Remove legacy noise.
- `terminate`: End the session when the schema is aligned.

### Observation Space
The agent sees the first 10 documents as a Golden Sample, but more importantly, it sees **Global Key Ratios**. This tells it exactly what percentage of the *entire* 50-doc collection contains a specific key, so it can make statistical decisions rather than just guessing based on the sample.

## Reproducibility & Baseline
This environment is deterministic. The datasets are pre-generated JSON files committed to the repo. No random seeds at runtime means your results will be the same as ours.

Our `gpt-4o-mini` baseline starts Task 1 at a score of **0.380** (meaning 19/50 docs are already clean) and shows steady progress as it merges dirty keys.

## Setup & Usage
1. **Hugging Face**: Deploy this repo as a Docker Space. Add your `HF_TOKEN` to the **Secrets** tab in Settings.
2. **Local**:

```bash
pip install -r requirements.txt
python -m server.app  # Runs on port 7860
python inference.py   # Runs the baseline agent
```

## Submission Checklist
- [x] `openenv validate` returns `[OK]`.
- [x] Dockerfile is configured for port 7860.
- [x] Task data includes the Hard Task 3 noise and conflicts.
- [x] `inference.py` uses the mandatory `[START]`, `[STEP]`, `[END]` logs with 3-decimal score precision.
- [x] All scores are clamped to `(0, 1)` range to avoid validator rejection.

If you're judging this: we know Task 3 is mean. We think that is what a real RL benchmark should look like. Good luck to the agents.
