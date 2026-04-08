#!/usr/bin/env python3
"""Pre-submission validation script for OpenEnv Hackathon.

Checks:
  1. openenv.yaml exists and is valid
  2. Dockerfile exists
  3. inference.py exists in root
  4. Required env vars are defined
  5. Server /reset returns 200
  6. Server /step accepts action and returns StepResult
  7. Server /state returns dict with score in 0.0–1.0
  8. All 3 tasks (easy, medium, hard) can be reset and graded
"""

import os
import sys
import json
import subprocess
import time
import signal

try:
    import yaml
except ImportError:
    print("⚠️  pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("⚠️  httpx not installed. Run: pip install httpx")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_URL = "http://localhost:7860"

passed = 0
failed = 0
warnings = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  ✅ {msg}")


def fail(msg):
    global failed
    failed += 1
    print(f"  ❌ {msg}")


def warn(msg):
    global warnings
    warnings += 1
    print(f"  ⚠️  {msg}")


# ── 1. Static file checks ───────────────────────────────────────────────────
print("\n🔍 1. Static file checks")

yaml_path = os.path.join(BASE_DIR, "openenv.yaml")
if os.path.exists(yaml_path):
    ok("openenv.yaml exists")
    with open(yaml_path) as f:
        try:
            spec = yaml.safe_load(f)
            if spec.get("env_name"):
                ok(f"openenv.yaml has env_name: {spec['env_name']}")
            else:
                fail("openenv.yaml missing 'env_name'")
            if spec.get("action_schema"):
                ok("openenv.yaml has action_schema")
            else:
                fail("openenv.yaml missing 'action_schema'")
            if spec.get("observation_schema"):
                ok("openenv.yaml has observation_schema")
            else:
                fail("openenv.yaml missing 'observation_schema'")
            tasks = spec.get("tasks", [])
            if len(tasks) >= 3:
                ok(f"openenv.yaml has {len(tasks)} tasks (>= 3 required)")
            else:
                fail(f"openenv.yaml has only {len(tasks)} tasks (need >= 3)")
        except yaml.YAMLError as e:
            fail(f"openenv.yaml is not valid YAML: {e}")
else:
    fail("openenv.yaml not found")

dockerfile_path = os.path.join(BASE_DIR, "Dockerfile")
if os.path.exists(dockerfile_path):
    ok("Dockerfile exists")
else:
    fail("Dockerfile not found")

inference_path = os.path.join(BASE_DIR, "inference.py")
if os.path.exists(inference_path):
    ok("inference.py exists in root directory")
    with open(inference_path) as f:
        content = f.read()
    if "from openai import" in content or "import openai" in content:
        ok("inference.py uses OpenAI Client")
    else:
        fail("inference.py does NOT use OpenAI Client (mandatory)")
    if "[START]" in content and "[STEP]" in content and "[END]" in content:
        ok("inference.py has [START]/[STEP]/[END] structured logging")
    else:
        fail("inference.py missing structured [START]/[STEP]/[END] logging")
else:
    fail("inference.py not found in root directory")

# ── 2. Environment variable checks ──────────────────────────────────────────
print("\n🔍 2. Environment variable checks")

for var in ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]:
    val = os.getenv(var)
    if val and val not in ("your_hf_token_here", ""):
        ok(f"{var} is set")
    else:
        warn(f"{var} is not set or has placeholder value (needed at runtime)")

# ── 3. Server endpoint checks ───────────────────────────────────────────────
print("\n🔍 3. Server endpoint checks (requires running server on port 7860)")

server_running = False
try:
    r = httpx.get(f"{ENV_URL}/", timeout=3.0)
    if r.status_code == 200:
        ok(f"GET / returns 200 (HF Space health ping)")
        server_running = True
    else:
        fail(f"GET / returned {r.status_code}")
except Exception:
    warn("Server not reachable at localhost:7860 — skipping endpoint tests")
    warn("Start server with: uvicorn server.app:app --port 7860")

if server_running:
    tasks_to_test = ["easy", "medium", "hard"]
    for task_name in tasks_to_test:
        print(f"\n  --- Task: {task_name} ---")
        try:
            r = httpx.post(f"{ENV_URL}/reset", json={"task_name": task_name}, timeout=10.0)
            if r.status_code == 200:
                ok(f"POST /reset (task={task_name}) returns 200")
                obs = r.json()
                if "step_number" in obs and "engagement_score" in obs:
                    ok("Reset response has valid Observation fields")
                else:
                    fail("Reset response missing expected Observation fields")
            else:
                fail(f"POST /reset returned {r.status_code}")
                continue
        except Exception as e:
            fail(f"POST /reset failed: {e}")
            continue

        # Step
        try:
            action = {"action_type": "ask_medium", "concept_id": "core_logic"}
            r = httpx.post(f"{ENV_URL}/step", json=action, timeout=10.0)
            if r.status_code == 200:
                ok("POST /step returns 200")
                step_data = r.json()
                if "observation" in step_data and "reward" in step_data and "done" in step_data:
                    ok("Step response has observation/reward/done")
                else:
                    fail("Step response missing expected StepResult fields")
            else:
                fail(f"POST /step returned {r.status_code}")
        except Exception as e:
            fail(f"POST /step failed: {e}")

        # State
        try:
            r = httpx.post(f"{ENV_URL}/state", timeout=10.0)
            if r.status_code == 200:
                ok("POST /state returns 200")
                state = r.json()
                score = state.get("score")
                if score is not None and 0.0 <= score <= 1.0:
                    ok(f"Score is in valid range: {score:.4f}")
                else:
                    fail(f"Score out of range or missing: {score}")
            else:
                fail(f"POST /state returned {r.status_code}")
        except Exception as e:
            fail(f"POST /state failed: {e}")

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  RESULTS:  ✅ {passed} passed  |  ❌ {failed} failed  |  ⚠️  {warnings} warnings")
print("=" * 60)

if failed > 0:
    print("\n  🚫 VALIDATION FAILED — fix the issues above before submitting.\n")
    sys.exit(1)
else:
    print("\n  🎉 ALL CHECKS PASSED — ready for submission!\n")
    sys.exit(0)
