# Adaptive Learning Intervention Environment (ALIE)

ALIE is a simulated OpenEnv environment where an AI teaching agent interacts with a synthetic student. The synthetic student maintains **hidden, non-deterministic internal state** (knowledge, confidence, fatigue, misconceptions), which evolve smoothly over time depending on the sequence of teaching interventions applied by the agent.

## Environment Mechanics

### Observation Space
The agent receives a masked view (`Observation`) of the student:
- `recent_answers`: Binary correct/incorrect history
- `response_time`: Seconds taken to respond
- `engagement_score`: Visual engagement index (0.0 to 1.0)
- `current_difficulty`: Difficulty targeted
- `recent_trend`: improving / declining / unstable / stable
- `step_number`

**The exact internal knowledge, fatigue, and confidence are intentionally hidden.**

### Action Space (`Action`)
The agent chooses pedagogical interventions:
- `ask_easy`, `ask_medium`, `ask_hard`: Drill concepts
- `give_hint`: Prevent frustration, but over-reliance penalizes long-term capability
- `review_concept`: Spend time removing misconceptions while restoring slight fatigue
- `advance_topic`: Move forward (very heavily penalized if done before standard knowledge thresholds are reached)

### Reward Function
Calculated at every step (dense signal):
- Correct answers and knowledge breakthroughs increase reward heavily.
- Sustained high engagement adds passive reward.
- Heavy fatigue, guessing incorrectly frequently, and hints abuse penalize the agent.
- Dropping out prematurely or advancing without mastery yield massive negative rewards.

## Setup & Running

Build the container image:
```bash
docker build -t alie-env .
```

Run the API:
```bash
docker run -p 7860:7860 alie-env
```

Or run via Python:
```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## OpenEnv Validation
This repository acts as an officially compliant OpenEnv simulation.
To validate compliance with the OpenEnv specification locally:
```bash
pip install openenv
openenv validate .
```

## Baseline Evaluation
Execute the baseline script ensuring OpenAI API endpoints format properly:
```bash
export API_BASE_URL="api.openai.com/v1"
export MODEL_NAME="gpt-4"
export HF_TOKEN="your_hf_token_if_needed"
python inference.py
```
