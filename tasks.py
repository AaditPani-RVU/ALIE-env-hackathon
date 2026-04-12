TASKS = [
    {
        "id": "easy",
        "task_id": "easy",
        "name": "easy",
        "difficulty": "easy",
        "description": "Student with high initial engagement and predictable learning capability.",
        "grader": "grader:grade_episode",
        "graders": ["grader:grade_episode"],
        "python_module_path": "grader.py",
        "grader_function": "grade_episode",
        "reset_params": {"task_name": "easy"},
        "reward_range": [0.001, 0.999],
    },
    {
        "id": "medium",
        "task_id": "medium",
        "name": "medium",
        "difficulty": "medium",
        "description": "Average student with occasional confusion and lower resilience.",
        "grader": "grader:grade_episode",
        "graders": ["grader:grade_episode"],
        "python_module_path": "grader.py",
        "grader_function": "grade_episode",
        "reset_params": {"task_name": "medium"},
        "reward_range": [0.001, 0.999],
    },
    {
        "id": "hard",
        "task_id": "hard",
        "name": "hard",
        "difficulty": "hard",
        "description": "Student with severe misconceptions, high fatigue potential, and nonlinear learning curves.",
        "grader": "grader:grade_episode",
        "graders": ["grader:grade_episode"],
        "python_module_path": "grader.py",
        "grader_function": "grade_episode",
        "reset_params": {"task_name": "hard"},
        "reward_range": [0.001, 0.999],
    },
]

TASK_ID_TO_INDEX = {task["id"]: index for index, task in enumerate(TASKS)}
TASK_GRADER_PAIRS = [(task["id"], task["grader"]) for task in TASKS]
