TASKS = [
    {
        "id": "easy",
        "config": {"task": "easy"},
        "grader": {"module": "grader", "function": "grade_easy"},
    },
    {
        "id": "medium",
        "config": {"task": "medium"},
        "grader": {"module": "grader", "function": "grade_medium"},
    },
    {
        "id": "hard",
        "config": {"task": "hard"},
        "grader": {"module": "grader", "function": "grade_hard"},
    },
]

TASK_ID_TO_INDEX = {task["id"]: index for index, task in enumerate(TASKS)}
TASK_GRADER_PAIRS = [(task["id"], f"{task['grader']['module']}:{task['grader']['function']}") for task in TASKS]
