from typing import Dict, Any
from env.models import StudentState

def get_initial_state(task_name: str) -> StudentState:
    if task_name == "easy":
        return StudentState(
            knowledge_levels={"concept_A": 0.1, "concept_B": 0.0},
            confidence=0.5,
            fatigue=0.0,
            learning_rate=0.8,
            misconceptions=[],
            persona="standard"
        )
    elif task_name == "medium":
        return StudentState(
            knowledge_levels={"concept_A": 0.3, "concept_B": 0.1},
            confidence=0.4,
            fatigue=0.2,
            learning_rate=0.5,
            misconceptions=[],
            persona="guesser"
        )
    elif task_name == "hard":
        return StudentState(
            knowledge_levels={"concept_A": 0.2, "concept_B": 0.1},
            confidence=0.3,
            fatigue=0.4,
            learning_rate=0.3,
            misconceptions=["core_confusion"],
            persona="anxious_perfectionist"
        )
    else:
        return StudentState(
            knowledge_levels={"concept_A": 0.1},
            confidence=0.5,
            fatigue=0.0,
            learning_rate=0.5,
            misconceptions=[],
            persona="standard"
        )

def grade_episode(final_state: StudentState, steps_taken: int) -> float:
    # Average knowledge across all concepts
    avg_knowledge = sum(final_state.knowledge_levels.values()) / max(1, len(final_state.knowledge_levels))
    knowledge_score = min(1.0, avg_knowledge)
    efficiency = max(0.0, 1.0 - (steps_taken / 40.0))
    safety = max(0.0, 1.0 - final_state.fatigue)
    misconception_penalty = 0.2 * len(final_state.misconceptions)
    final_score = (knowledge_score * 0.6) + (efficiency * 0.2) + (safety * 0.2) - misconception_penalty
    return max(0.0, min(1.0, final_score))
