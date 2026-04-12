from __future__ import annotations

from typing import Any

from grader import grade_episode
from configs.tasks import get_initial_state

MIN_SCORE = 0.001
MAX_SCORE = 0.999


def _normalize_score(score: Any) -> float:
    return max(MIN_SCORE, min(MAX_SCORE, float(score)))


def _result(task_id: str, score: Any) -> dict[str, Any]:
    normalized = _normalize_score(score)
    return {
        "task_id": task_id,
        "score": normalized,
        "passed": normalized >= 0.5,
        "breakdown": {
            "normalized_score": normalized,
        },
    }


def grade_easy(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> dict[str, Any]:
    if final_state is None and not kwargs:
        return _result("easy", grade_episode(get_initial_state("easy"), 0))
    return _result("easy", grade_episode(final_state, steps_taken, **kwargs))


def grade_medium(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> dict[str, Any]:
    if final_state is None and not kwargs:
        return _result("medium", grade_episode(get_initial_state("medium"), 0))
    return _result("medium", grade_episode(final_state, steps_taken, **kwargs))


def grade_hard(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> dict[str, Any]:
    if final_state is None and not kwargs:
        return _result("hard", grade_episode(get_initial_state("hard"), 0))
    return _result("hard", grade_episode(final_state, steps_taken, **kwargs))


def get_score(result: Any) -> float:
    if isinstance(result, dict):
        return _normalize_score(result.get("score", 0.001))
    return _normalize_score(result)


def grade_task(task_id: str, final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> dict[str, Any]:
    grader_fn = GRADERS.get(task_id)
    if grader_fn is None:
        raise ValueError(f"Unknown task: {task_id}")
    return grader_fn(final_state, steps_taken, **kwargs)


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

TASK_GRADER_PAIRS = [(task_id, f"graders:{grader.__name__}") for task_id, grader in GRADERS.items()]
