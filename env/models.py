from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class Observation(BaseModel):
    recent_answers: List[int] = Field(default_factory=list, description="List of correctness (1 for correct, 0 for incorrect)")
    response_time: float = Field(..., description="Simulated response time in seconds")
    engagement_score: float = Field(..., description="Current engagement level (0.0 to 1.0)")
    current_difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty of the most recent interaction")
    current_concept: str = Field(default="core_logic", description="Current node in the knowledge graph")
    recent_trend: Literal["improving", "declining", "unstable", "stable"] = Field(..., description="Trend of recent performance")
    step_number: int = Field(..., description="Current step in the episode")

class Action(BaseModel):
    action_type: Literal["ask_easy", "ask_medium", "ask_hard", "give_hint", "review_concept", "advance_topic"]
    concept_id: Optional[str] = Field(default="core_logic", description="Optional concept ID for targeted review or advancement")
    intensity: Optional[float] = Field(default=0.5, ge=0.1, le=1.0, description="Hint intensity. Higher reveals more but builds dependency")
    duration: Optional[int] = Field(default=1, ge=1, le=5, description="Review duration. Higher restores more knowledge but increases fatigue")

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)

class StudentState(BaseModel):
    knowledge_levels: Dict[str, float] = Field(default_factory=lambda: {"core_logic": 0.0}, description="Dictionary mapping concept IDs to knowledge mastery")
    confidence: float = Field(..., ge=0.0, le=1.0)
    fatigue: float = Field(..., ge=0.0, le=1.0)
    learning_rate: float = Field(..., ge=0.0, le=1.0)
    misconceptions: List[str] = Field(default_factory=list)
    persona: Literal["standard", "guesser", "anxious_perfectionist"] = Field(default="standard", description="Hidden student persona type governing transition dynamics")
