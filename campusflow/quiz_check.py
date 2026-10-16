"""Run the Engineering Understanding Check."""

from campusflow.quiz import QUESTIONS


def get_answer():
    """Accept only A, B, C, or D."""
    while True:
        answer = input("Your answer (A/B/C/D): ").strip().upper()

        if answer in ("A", "B", "C", "D"):
            return answer

        print("Invalid choice. Please enter A, B, C, or D.")


def run_quiz():
    """Ask all questions, calculate the score, and collect explanations."""
    score = 0
    explanations = []

    print("\n=== Engineering Understanding Check ===")

    for number, question in enumerate(QUESTIONS, start=1):
        print(f"\nQ{number}. {question['question']}")

        for letter, option in question["options"].items():
            print(f"  {letter}. {option}")

        answer = get_answer()

        # Record the learner's first submitted answer.
        if answer == question["answer"]:
            score += 1
            print("Correct!")
        else:
            print(f"Not quite. The correct answer is {question['answer']}.")

        # Collect explanations for the first two questions.
        if number <= 2:
            explanation = input(
                f"Briefly explain why you chose {answer}: "
            ).strip()

            while not explanation:
                print("Please provide a short explanation.")
                explanation = input("Your explanation: ").strip()

            explanations.append({
                "question": number,
                "answer": answer,
                "explanation": explanation,
            })

    print("\n=== Quiz Results ===")
    print(f"Final score: {score}/6")

    print("\nYour explanations:")
    for item in explanations:
        print(f"Q{item['question']} ({item['answer']}): {item['explanation']}")

    return score