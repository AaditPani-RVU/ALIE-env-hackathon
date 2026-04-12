from __future__ import annotations

from typing import Any, Mapping

MIN_SCORE = 0.001
MAX_SCORE = 0.999


def _strict(score: float) -> float:
    if score <= 0:
        return 0.05
    if score >= 1:
        return 0.99
    return float(score)


def _extract_knowledge_levels(state: Any) -> dict[str, float]:
    if state is None:
        return {}

    if hasattr(state, "knowledge_levels"):
        knowledge = getattr(state, "knowledge_levels")
        if isinstance(knowledge, Mapping):
            return {str(k): float(v) for k, v in knowledge.items()}

    if isinstance(state, Mapping):
        if "knowledge_levels" in state and isinstance(state["knowledge_levels"], Mapping):
            return {str(k): float(v) for k, v in state["knowledge_levels"].items()}
        if "student_state" in state:
            return _extract_knowledge_levels(state["student_state"])

    return {}


def _extract_fatigue(state: Any) -> float:
    if state is None:
        return 0.0

    if hasattr(state, "fatigue"):
        return float(getattr(state, "fatigue"))

    if isinstance(state, Mapping):
        if "fatigue" in state:
            return float(state["fatigue"])
        if "student_state" in state:
            return _extract_fatigue(state["student_state"])

    return 0.0


def _extract_misconceptions(state: Any) -> list[Any]:
    if state is None:
        return []

    if hasattr(state, "misconceptions"):
        misconceptions = getattr(state, "misconceptions")
        return list(misconceptions) if misconceptions is not None else []

    if isinstance(state, Mapping):
        if "misconceptions" in state:
            misconceptions = state["misconceptions"]
            return list(misconceptions) if misconceptions is not None else []
        if "student_state" in state:
            return _extract_misconceptions(state["student_state"])

    return []


def _extract_steps_taken(steps_taken: Any = None, **kwargs: Any) -> int:
    for value in (
        steps_taken,
        kwargs.get("steps"),
        kwargs.get("step_count"),
        kwargs.get("num_steps"),
        kwargs.get("steps_taken"),
    ):
        if value is not None:
            return max(0, int(value))
    return 0


def grade_episode(final_state: Any = None, steps_taken: Any = None, **kwargs: Any) -> float:
    """Return a strictly bounded score in (0, 1) for OpenEnv validation.

    The hackathon validator may call the grader with slightly different payload
    shapes, so this function accepts either a StudentState-like object or a raw
    mapping that contains `student_state`.
    """

    state = final_state or kwargs.get("state") or kwargs.get("student_state") or kwargs.get("final_state")
    knowledge_levels = _extract_knowledge_levels(state)
    avg_knowledge = sum(knowledge_levels.values()) / max(1, len(knowledge_levels))
    knowledge_score = min(1.0, max(0.0, avg_knowledge))

    step_count = _extract_steps_taken(steps_taken, **kwargs)
    efficiency = max(0.0, 1.0 - (step_count / 40.0))

    fatigue = max(0.0, min(1.0, _extract_fatigue(state)))
    safety = 1.0 - fatigue

    misconception_penalty = 0.2 * len(_extract_misconceptions(state))
    final_score = (knowledge_score * 0.6) + (efficiency * 0.2) + (safety * 0.2) - misconception_penalty
    return _strict(float(final_score))


def grade_easy(state: Any = None) -> float:
    try:
        return _strict(grade_episode(final_state=state, steps_taken=0))
    except Exception:
        return 0.05


def grade_medium(state: Any = None) -> float:
    try:
        return _strict(grade_episode(final_state=state, steps_taken=0))
    except Exception:
        return 0.05


def grade_hard(state: Any = None) -> float:
    try:
        return _strict(grade_episode(final_state=state, steps_taken=0))
    except Exception:
        return 0.05


def grade_state(state: Any = None) -> float:
    try:
        return _strict(grade_medium(state))
    except Exception:
        return 0.05
