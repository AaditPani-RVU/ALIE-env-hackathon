import random
from typing import Tuple, Optional
from .models import StudentState

class StudentSimulator:
    def __init__(self, initial_state: StudentState):
        self.state = initial_state
        self.history_correctness = []
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.hints_used = 0

    def step(self, action_type: str, concept_id: str, intensity: float, duration: int) -> Tuple[int, float, float]:
        is_correct = 0
        response_time = random.uniform(2.0, 5.0)
        engagement_impact = 0.0
        
        if concept_id not in self.state.knowledge_levels:
            self.state.knowledge_levels[concept_id] = 0.0

        current_knowledge = self.state.knowledge_levels[concept_id]
        effective_knowledge = max(0.0, current_knowledge - (self.state.fatigue * 0.2))
        
        # Persona modifiers
        conf_multiplier = 1.0 if self.state.persona != "guesser" else 1.5
        anxiety_factor = 2.0 if self.state.persona == "anxious_perfectionist" else 1.0

        if action_type in ["ask_easy", "ask_medium", "ask_hard"]:
            difficulty_map = {"ask_easy": 0.2, "ask_medium": 0.5, "ask_hard": 0.8}
            diff = difficulty_map[action_type]
            
            prob_correct = min(0.95, max(0.05, effective_knowledge - diff + (self.state.confidence * 0.2 * conf_multiplier)))
            
            if "core_confusion" in self.state.misconceptions and diff > 0.4:
                prob_correct *= 0.6
                
            is_correct = 1 if random.random() < prob_correct else 0
            
            if self.state.persona == "guesser":
                response_time = random.uniform(0.5, 2.0)
            
            if is_correct:
                if self.state.persona != "guesser":
                    response_time = max(1.0, 5.0 * diff - self.state.confidence * 2.0)
                self.consecutive_successes += 1
                self.consecutive_failures = 0
                
                learning_gain = self.state.learning_rate * (1.0 - current_knowledge) * (0.05 if diff > 0.3 else 0.01)
                self.state.knowledge_levels[concept_id] = min(1.0, current_knowledge + learning_gain)
                self.state.confidence = min(1.0, self.state.confidence + 0.05)
                
                if action_type == "ask_easy" and current_knowledge > 0.6:
                    engagement_impact -= 0.1
                    self.state.fatigue = min(1.0, self.state.fatigue + 0.02)
            else:
                if self.state.persona != "guesser":
                    response_time = random.uniform(5.0, 15.0)
                self.consecutive_failures += 1
                self.consecutive_successes = 0
                
                if diff > current_knowledge + 0.3:
                    self.state.confidence = max(0.0, self.state.confidence - (0.1 * anxiety_factor))
                    engagement_impact -= 0.15 * anxiety_factor
                    self.state.fatigue = min(1.0, self.state.fatigue + 0.1)
                else:
                    self.state.confidence = max(0.0, self.state.confidence - (0.05 * anxiety_factor))
                
                if self.consecutive_failures >= 3 and "core_confusion" not in self.state.misconceptions:
                    if self.state.persona != "guesser": 
                        self.state.misconceptions.append("core_confusion")

        elif action_type == "give_hint":
            self.hints_used += 1
            response_time = random.uniform(1.0, 3.0)
            self.state.confidence = min(1.0, self.state.confidence + (0.1 * intensity))
            engagement_impact += 0.05
            is_correct = -1
            
            self.state.knowledge_levels[concept_id] = min(1.0, current_knowledge + (0.02 * intensity))
            if self.hints_used > 3:
                self.state.learning_rate = max(0.0, self.state.learning_rate - (0.05 * intensity))

        elif action_type == "review_concept":
            response_time = random.uniform(10.0, 20.0) * duration
            engagement_impact += 0.05
            self.state.knowledge_levels[concept_id] = min(1.0, current_knowledge + (0.05 * duration))
            self.state.fatigue = max(0.0, self.state.fatigue - 0.05)
            is_correct = -1
            
            if "core_confusion" in self.state.misconceptions:
                if random.random() > 0.5:
                    self.state.misconceptions.remove("core_confusion")
            
            if duration > 3 and self.state.persona == "anxious_perfectionist":
                 self.state.fatigue = min(1.0, self.state.fatigue + 0.1)

        elif action_type == "advance_topic":
            response_time = random.uniform(2.0, 5.0)
            if current_knowledge < 0.7:
                self.state.confidence = max(0.0, self.state.confidence - (0.2 * anxiety_factor))
                engagement_impact -= 0.2 * anxiety_factor
            else:
                engagement_impact += 0.1
            is_correct = -1

        self.state.fatigue = min(1.0, self.state.fatigue + 0.02)
        
        if is_correct != -1:
            self.history_correctness.append(is_correct)
            if len(self.history_correctness) > 5:
                self.history_correctness.pop(0)

        return is_correct, response_time, engagement_impact

    def get_recent_answers(self) -> list:
        return self.history_correctness

    def get_trend(self) -> str:
        if len(self.history_correctness) < 3:
            return "stable"
        recent = self.history_correctness[-3:]
        if sum(recent) == 3:
            return "improving"
        elif sum(recent) == 0:
            return "declining"
        elif sum(recent) == 1 and recent[-1] == 0:
            return "declining"
        elif sum(recent) == 2 and recent[-1] == 1:
            return "improving"
        else:
            return "unstable"
