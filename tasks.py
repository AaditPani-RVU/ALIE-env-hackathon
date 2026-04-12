TASKS = [
    {
        "id": "easy",
        "task_id": "easy",
        "name": "easy",
        "difficulty": "easy",
        "description": "Student with high initial engagement and predictable learning capability.",
        "grader": "graders:grade_easy",
        "graders": ["graders:grade_easy"],
        "python_module_path": "graders.py",
        "grader_function": "grade_easy",
        "reset_params": {"task_name": "easy"},
        "reward_range": [0.001, 0.999],
    },
    {
        "id": "medium",
        "task_id": "medium",
        "name": "medium",
        "difficulty": "medium",
        "description": "Average student with occasional confusion and lower resilience.",
        "grader": "graders:grade_medium",
        "graders": ["graders:grade_medium"],
        "python_module_path": "graders.py",
        "grader_function": "grade_medium",
        "reset_params": {"task_name": "medium"},
        "reward_range": [0.001, 0.999],
    },
    {
        "id": "hard",
        "task_id": "hard",
        "name": "hard",
        "difficulty": "hard",
        "description": "Student with severe misconceptions, high fatigue potential, and nonlinear learning curves.",
        "grader": "graders:grade_hard",
        "graders": ["graders:grade_hard"],
        "python_module_path": "graders.py",
        "grader_function": "grade_hard",
        "reset_params": {"task_name": "hard"},
        "reward_range": [0.001, 0.999],
    },
]

TASK_ID_TO_INDEX = {task["id"]: index for index, task in enumerate(TASKS)}
TASK_GRADER_PAIRS = [(task["id"], task["grader"]) for task in TASKS]
