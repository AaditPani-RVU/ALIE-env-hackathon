from __future__ import annotations

from typing import Any

from grader import grade_episode
from configs.tasks import get_initial_state


def _normalize_score(score: Any) -> float:
    return max(0.001, min(0.999, float(score)))


def grade_easy(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> float:
    if final_state is None and not kwargs:
        return _normalize_score(grade_episode(get_initial_state("easy"), 0))
    return _normalize_score(grade_episode(final_state, steps_taken, **kwargs))


def grade_medium(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> float:
    if final_state is None and not kwargs:
        return _normalize_score(grade_episode(get_initial_state("medium"), 0))
    return _normalize_score(grade_episode(final_state, steps_taken, **kwargs))


def grade_hard(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> float:
    if final_state is None and not kwargs:
        return _normalize_score(grade_episode(get_initial_state("hard"), 0))
    return _normalize_score(grade_episode(final_state, steps_taken, **kwargs))


def grade_task(task_id: str, final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> float:
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
