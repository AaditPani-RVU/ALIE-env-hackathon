import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# ── Mandatory environment variables ──────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize OpenAI-compatible client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

# OpenEnv API Server base URL
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

TASKS = ["easy", "medium", "hard"]


def get_action_from_llm(obs: dict, action_history: list) -> dict:
    """Use the OpenAI-compatible client to decide the next pedagogical action."""

    prompt = f"""You are an AI teaching agent acting as a pedagogical decision engine.
You must infer the student's hidden state (knowledge, confidence, fatigue) based on the observation below.

Observation:
{json.dumps(obs, indent=2)}

Your Recent Actions History:
{json.dumps(action_history[-5:] if action_history else ["No actions taken yet"], indent=2)}

Available Actions: "ask_easy", "ask_medium", "ask_hard", "give_hint", "review_concept", "advance_topic"

Your JSON output MUST include these keys:
- "action_type": One of the 6 available actions above.
- "concept_id": The knowledge graph node you are targeting (e.g. "core_logic", "concept_A").
- "intensity": FLOAT 0.1-1.0 (only meaningful for give_hint).
- "duration": INT 1-5 (only meaningful for review_concept).
- "reasoning": A detailed string explaining your thought process.

CRITICAL: Do NOT repeat the same action endlessly. If the student keeps failing despite hints, use "review_concept" to fix misconceptions.

Respond with valid JSON ONLY, no markdown formatting or codeblocks."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a pedagogical AI agent. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )
        content = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        data = json.loads(content)

        action_type = data.get("action_type", "ask_medium")
        valid_actions = ["ask_easy", "ask_medium", "ask_hard", "give_hint", "review_concept", "advance_topic"]
        if action_type not in valid_actions:
            action_type = "ask_medium"

        return {
            "action_type": action_type,
            "reasoning": data.get("reasoning", ""),
            "concept_id": data.get("concept_id", "core_logic"),
            "intensity": float(data.get("intensity", 0.5)),
            "duration": int(data.get("duration", 1)),
        }
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"action_type": "ask_medium", "concept_id": "core_logic", "intensity": 0.5, "duration": 1}


def run_task(task_name: str) -> dict:
    """Run a single task episode and return summary info."""

    start_log = {
        "task_name": task_name,
        "env_name": "ALIE",
        "model": MODEL_NAME,
        "api_base_url": API_BASE_URL,
    }
    print(f"[START] {json.dumps(start_log)}")

    # ── Reset ────────────────────────────────────────────────────────────────
    try:
        res = httpx.post(f"{ENV_URL}/reset", json={"task_name": task_name}, timeout=30.0)
        res.raise_for_status()
        obs = res.json()
    except Exception as e:
        print(f"  Error connecting to env for reset: {e}")
        result = {"task_name": task_name, "score": 0.001, "total_reward": 0.0, "steps": 0, "error": str(e)}
        print(f"[END] {json.dumps(result)}")
        return result

    done = False
    total_reward = 0.0
    action_history = []
    step_number = 0

    while not done:
        # Get action from LLM
        action = get_action_from_llm(obs, action_history)
        action_history.append(action["action_type"])

        # Step the environment
        try:
            res = httpx.post(f"{ENV_URL}/step", json=action, timeout=30.0)
            res.raise_for_status()
            step_result = res.json()
        except Exception as e:
            print(f"  Error stepping env: {e}")
            break

        obs = step_result["observation"]
        reward = step_result["reward"]
        done = step_result["done"]
        total_reward += reward
        step_number += 1

        # ── [STEP] structured log ────────────────────────────────────────
        step_log = {
            "step_number": step_number,
            "action": {
                "action_type": action["action_type"],
                "concept_id": action.get("concept_id", "core_logic"),
                "intensity": action.get("intensity", 0.5),
                "duration": action.get("duration", 1),
            },
            "observation": obs,
            "reward": reward,
            "done": done,
            "reasoning": action.get("reasoning", ""),
        }
        print(f"[STEP] {json.dumps(step_log)}")

    # ── Grab final score ─────────────────────────────────────────────────────
    final_score = None
    try:
        res = httpx.post(f"{ENV_URL}/state", timeout=10.0)
        res.raise_for_status()
        state_info = res.json()
        final_score = state_info.get("score", 0.0)
    except Exception:
        pass

    if final_score is None:
        final_score = 0.001

    final_score = max(0.001, min(0.999, float(final_score)))

    result = {
        "task_name": task_name,
        "score": round(final_score, 4),
        "total_reward": round(total_reward, 4),
        "steps": step_number,
    }
    print(f"[END] {json.dumps(result)}")
    return result


def main():
    results = []
    for task_name in TASKS:
        print(f"\n--- Running task: {task_name} ---")
        result = run_task(task_name)
        results.append(result)
        print(f"  Task '{task_name}' => reward={result.get('total_reward', 'N/A')}, "
              f"score={result.get('score', 'N/A')}, steps={result.get('steps', 'N/A')}")

    summary_log = {
        "results": results,
        "total_tasks": len(TASKS),
    }
    print(f"\n[SUMMARY] {json.dumps(summary_log)}")


if __name__ == "__main__":
    main()
