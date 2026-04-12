from typing import Dict, Any, Tuple
from env.models import Observation, Action, StepResult, StudentState
from env.student_sim import StudentSimulator
from configs.tasks import get_initial_state
from grader import grade_episode

MIN_SCORE = 0.001
MAX_SCORE = 0.999

class AlieEnv:
    def __init__(self, task_name: str = "easy"):
        self.task_name = task_name
        self.max_steps = 30
        self.step_count = 0
        self.sim = None
        self.current_engagement = 1.0

    async def reset(self) -> Observation:
        self.step_count = 0
        initial_student_state = get_initial_state(self.task_name)
        self.sim = StudentSimulator(initial_student_state)
        self.current_engagement = 1.0
        
        start_concept = list(self.sim.state.knowledge_levels.keys())[0] if self.sim.state.knowledge_levels else "core_logic"
        
        return self._get_observation(
            response_time=0.0,
            current_difficulty="medium",
            current_concept=start_concept
        )

    async def step(self, action: Action) -> StepResult:
        if self.sim is None:
            raise ValueError("Environment must be reset before step.")
            
        self.step_count += 1
        
        difficulty = action.action_type if "ask" in action.action_type else "medium"
        if difficulty.startswith("ask_"):
            difficulty = difficulty.split("_")[1]
            
        concept_id = action.concept_id if action.concept_id else "core_logic"
        
        is_correct, response_time, engagement_impact = self.sim.step(
            action_type=action.action_type,
            concept_id=concept_id,
            intensity=action.intensity,
            duration=action.duration
        )
        
        self.current_engagement = max(0.0, min(1.0, self.current_engagement + engagement_impact))
        
        reward = self._compute_reward(action, is_correct, engagement_impact, concept_id)
        
        done = False
        avg_knowledge = sum(self.sim.state.knowledge_levels.values()) / max(1, len(self.sim.state.knowledge_levels))
        if self.step_count >= self.max_steps or avg_knowledge > 0.9:
            done = True
            
        obs = self._get_observation(response_time, difficulty, concept_id)
        info = {
            "is_correct": is_correct,
            "fatigue_level": self.sim.state.fatigue,
            "persona": self.sim.state.persona,
            "final_score": grade_episode(self.sim.state, self.step_count) if done else None
        }
        
        return StepResult(observation=obs, reward=reward, done=done, info=info)

    def state(self) -> Dict[str, Any]:
        if self.sim is None:
            return {"score": MIN_SCORE}
        try:
            raw_score = grade_episode(self.sim.state, self.step_count)
            score = max(MIN_SCORE, min(MAX_SCORE, float(raw_score)))
        except Exception:
            score = MIN_SCORE
        student_state_dict: Dict[str, Any] = {}
        try:
            student_state_dict = self.sim.state.model_dump() if hasattr(self.sim.state, "model_dump") else self.sim.state.dict()
        except Exception:
            pass
        return {
            "task_name": self.task_name,
            "step_count": self.step_count,
            "student_state": student_state_dict,
            "engagement": self.current_engagement,
            "score": score,
        }

    def _get_observation(self, response_time: float, current_difficulty: str, current_concept: str) -> Observation:
        return Observation(
            recent_answers=self.sim.get_recent_answers(),
            response_time=response_time,
            engagement_score=self.current_engagement,
            current_difficulty=current_difficulty,
            current_concept=current_concept,
            recent_trend=self.sim.get_trend(),
            step_number=self.step_count
        )

    def _compute_reward(self, action: Action, is_correct: int, engagement_impact: float, concept_id: str) -> float:
        import math
        raw = 0.0

        failure_penalized = False

        if is_correct == 1:
            raw += 2.0
        elif is_correct == 0:
            raw -= 1.0
            failure_penalized = True

        if engagement_impact > 0:
            raw += 0.5
        elif engagement_impact < -0.1 and not failure_penalized:
            raw -= 1.0

        if self.sim.state.fatigue > 0.8:
            raw -= 2.0

        if action.action_type == "give_hint" and self.sim.hints_used > 5:
            raw -= 1.5

        current_knowledge = self.sim.state.knowledge_levels.get(concept_id, 0.0)
        if action.action_type == "advance_topic" and current_knowledge < 0.7:
            raw -= 3.0

        if action.action_type == "review_concept":
            misconception_bonus_applied = False
            if "core_confusion" in self.sim.state.misconceptions:
                raw += 2.0
                misconception_bonus_applied = True
            if action.duration > 3:
                raw -= 0.5 if misconception_bonus_applied else 1.0

        # Normalize raw reward to strictly (0, 1) using sigmoid so the
        # OpenEnv validator never sees a reward outside the valid range.
        # sigmoid(x * 0.4): raw=-5 → 0.12, raw=0 → 0.5, raw=+5 → 0.88
        normalized = 1.0 / (1.0 + math.exp(-raw * 0.4))
        return max(0.05, min(0.95, normalized))
