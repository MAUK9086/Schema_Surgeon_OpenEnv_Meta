"""
inference.py
------------
Baseline LLM inference script for Schema Surgeon.
Runs all tasks sequentially through SchemaSurgeonEnv and emits required logs.
"""

import asyncio
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from client import SchemaSurgeonEnv
from models import SchemaAction

API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN: str = os.environ.get("HF_TOKEN", "")
ENV_BASE_URL: str = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

TEMPERATURE: float = 0.0
MAX_TOKENS: int = 512
MAX_STEPS: int = 30
SUCCESS_THRESHOLD: float = 0.95
TASKS: List[str] = ["task1", "task2", "task3"]
MAX_API_RETRIES: int = 3
INITIAL_BACKOFF_SECONDS: float = 1.0

DEFAULT_ACTION: Dict[str, Any] = {"action_type": "terminate", "params": {}}

SYSTEM_PROMPT: str = (
    "You are a Database Migration Agent. You will receive a sample of documents, "
    "global keys, a target schema, and a current score. "
    "Return exactly one JSON action. "
    "Available actions are rename_and_merge, cast_type, flatten_field, delete_key, and terminate."
)


def log_start(task: str, env: str, model: str) -> None:
    """
    Emit required start log line.

    Args:
        task: Task identifier.
        env: Environment name.
        model: Model name.

    Returns:
        None.
    """
    print(f'[START] task="{task}" env="{env}" model="{model}"', flush=True)


def log_step(
    step: int,
    action: Dict[str, Any],
    reward: float,
    done: bool,
    error: Optional[str],
) -> None:
    """
    Emit required per-step log line.

    Args:
        step: Step number.
        action: Executed action payload.
        reward: Step reward.
        done: Episode completion flag.
        error: Optional error string.

    Returns:
        None.
    """
    action_str = json.dumps(action)
    error_str = f' error="{error}"' if error else ""
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.4f} done={done}{error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """
    Emit required end log line.

    Args:
        success: Success flag for task.
        steps: Number of steps executed.
        score: Final score.
        rewards: Reward history.

    Returns:
        None.
    """
    rewards_str = json.dumps([round(item, 4) for item in rewards])
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.4f} rewards={rewards_str}",
        flush=True,
    )


def parse_action_response(raw_text: str) -> Dict[str, Any]:
    """
    Parse LLM text into action dictionary.

    Args:
        raw_text: Raw LLM output text.

    Returns:
        Valid action dictionary or terminate fallback.
    """
    json_candidates = extract_json_candidates(raw_text)
    for candidate in json_candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict) and "action_type" in parsed and "params" in parsed:
            return parsed

    return DEFAULT_ACTION.copy()


def extract_json_candidates(raw_text: str) -> List[str]:
    """
    Extract candidate JSON object strings from arbitrary model output text.

    Args:
        raw_text: Raw LLM response which may contain markdown fences or prose.

    Returns:
        Ordered list of candidate JSON object snippets.
    """
    candidates: List[str] = []
    stripped = raw_text.strip()

    if stripped:
        candidates.append(stripped)

    fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
    for match in fence_pattern.finditer(raw_text):
        fenced_block = match.group(1).strip()
        if fenced_block:
            candidates.append(fenced_block)

    start_indices = [idx for idx, char in enumerate(raw_text) if char == "{"]
    for start_idx in start_indices:
        depth = 0
        for end_idx in range(start_idx, len(raw_text)):
            char = raw_text[end_idx]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    fragment = raw_text[start_idx : end_idx + 1].strip()
                    if fragment:
                        candidates.append(fragment)
                    break

    # Keep insertion order while deduplicating.
    unique_candidates: List[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)

    return unique_candidates


def validate_action_dict(action_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an action dictionary using SchemaAction.

    Args:
        action_dict: Candidate action payload.

    Returns:
        Validated action dict or default terminate action.
    """
    try:
        action = SchemaAction(**action_dict)
        return action.model_dump()
    except ValidationError:
        return DEFAULT_ACTION.copy()


def get_agent_action(
    llm_client: OpenAI,
    observation: Dict[str, Any],
    history: List[str],
) -> Dict[str, Any]:
    """
    Query the LLM for the next environment action.

    Args:
        llm_client: OpenAI SDK client.
        observation: Current observation dictionary.
        history: Recent textual step history.

    Returns:
        Action dictionary for the next step.
    """
    history_text = "\n".join(history[-5:]) if history else "None"

    user_prompt = (
        f"Sample docs (first 10):\n{json.dumps(observation.get('sample_docs', []), indent=2)}\n\n"
        f"Global key presence: {json.dumps(observation.get('global_keys', {}))}\n\n"
        f"Target schema: {json.dumps(observation.get('target_schema', {}))}\n\n"
        f"Current score: {observation.get('current_score', 0.0)}\n"
        f"Step: {observation.get('step_count', 0)} / {observation.get('max_steps', MAX_STEPS)}\n"
        f"Last action status: {observation.get('last_action_status', 'reset')}\n\n"
        f"Recent history:\n{history_text}\n\n"
        "Output your next action as JSON:"
    )

    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            completion = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            raw_text = completion.choices[0].message.content or ""
            parsed_action = parse_action_response(raw_text)
            return validate_action_dict(parsed_action)
        except (APIConnectionError, APIError, APITimeoutError, RateLimitError):
            if attempt < MAX_API_RETRIES:
                backoff_seconds = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                print(
                    f"[DEBUG] LLM request failed on attempt {attempt}; retrying in "
                    f"{backoff_seconds:.1f}s",
                    flush=True,
                )
                time.sleep(backoff_seconds)
                continue
            break
        except (IndexError, KeyError, TypeError, ValueError):
            break

    return DEFAULT_ACTION.copy()


async def run_task(llm_client: OpenAI, task_id: str) -> float:
    """
    Run one full task episode.

    Args:
        llm_client: OpenAI SDK client.
        task_id: Task identifier.

    Returns:
        Final task score in [0.0, 1.0].
    """
    log_start(task=task_id, env="schema-surgeon", model=MODEL_NAME)

    async with SchemaSurgeonEnv(base_url=ENV_BASE_URL) as env_client:
        result = await env_client.reset(task_id=task_id)
        observation = result.observation.model_dump()

        history: List[str] = []
        rewards: List[float] = []
        steps_taken = 0
        final_score = float(observation.get("current_score", 0.0))

        for step_number in range(1, MAX_STEPS + 1):
            action_dict = get_agent_action(llm_client, observation, history)
            action = SchemaAction(**action_dict)

            result = await env_client.step(action)
            reward_val = float(result.reward or 0.0)
            done = bool(result.done)
            observation = result.observation.model_dump()
            final_score = float(observation.get("current_score", final_score))

            rewards.append(reward_val)
            steps_taken = step_number
            log_step(step_number, action_dict, reward_val, done, None)

            history.append(
                f"Step {step_number}: {action_dict.get('action_type')}"
                f"({action_dict.get('params')}) -> reward={reward_val:.4f} "
                f"score={final_score:.4f}"
            )

            if done:
                break

        success = final_score >= SUCCESS_THRESHOLD
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)
        return final_score


async def main() -> None:
    """
    Run all tasks sequentially and print aggregate results.

    Args:
        None.

    Returns:
        None.
    """
    if not HF_TOKEN:
        raise EnvironmentError("Set HF_TOKEN environment variable.")

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    all_scores: Dict[str, float] = {}

    for task_id in TASKS:
        print("\n" + "=" * 50, flush=True)
        print(f"Running {task_id}...", flush=True)
        score = await run_task(llm_client, task_id)
        all_scores[task_id] = score
        print(f"Final score for {task_id}: {score:.4f}", flush=True)

    print("\n" + "=" * 50, flush=True)
    print("All task scores:", json.dumps(all_scores, indent=2), flush=True)
    average_score = sum(all_scores.values()) / len(all_scores)
    print(f"Average score: {average_score:.4f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
