from app.domain import Question


def mock_questions() -> tuple[Question, ...]:
    """Fixed vocabulary set copied into each new quiz session."""
    return (
        Question(
            question_id="q1",
            prompt="Which word means lasting for a very short time?",
            choices=("ephemeral", "permanent", "ancient", "solid"),
            correct_choice="ephemeral",
        ),
        Question(
            question_id="q2",
            prompt="Which word means well meaning and kindly?",
            choices=("hostile", "benevolent", "careless", "timid"),
            correct_choice="benevolent",
        ),
        Question(
            question_id="q3",
            prompt="Which word means showing great attention to detail?",
            choices=("meticulous", "vague", "hasty", "casual"),
            correct_choice="meticulous",
        ),
        Question(
            question_id="q4",
            prompt="Which word means open to more than one interpretation?",
            choices=("obvious", "literal", "ambiguous", "certain"),
            correct_choice="ambiguous",
        ),
        Question(
            question_id="q5",
            prompt="Which word means able to recover quickly from difficulty?",
            choices=("fragile", "rigid", "resilient", "idle"),
            correct_choice="resilient",
        ),
    )
