"""Tests for campusflow/quiz.py and campusflow/quiz_check.py.

Replaces the earlier pytest-style file. unittest.TestCase only, per the
project rule; run with:

    python3 -m unittest discover -s tests -v
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from campusflow.quiz import QUESTIONS
from campusflow.quiz_check import get_answer, run_quiz


# The answer key from the assessment guide: Q1=B, Q2=C, Q3=B, Q4=C, Q5=C, Q6=B.
ANSWER_KEY = ["B", "C", "B", "C", "C", "B"]


def scripted_input(answers, explanation="Adequate explanation."):
    """Return a side_effect for builtins.input that can never run dry.

    Dispatches on the prompt, not on a raw call index, because run_quiz
    interleaves the two kinds of input: each question consumes one answer,
    and questions 1 and 2 each consume an explanation immediately after
    their answer. An index-based script that assumed six answers followed
    by two explanations would hand explanation text to get_answer(), which
    would reject it and loop forever on an exhausted mock.

    Answer prompts get the next queued letter, falling back to a valid
    "A" if the queue runs out, so get_answer() always returns. Every other
    prompt — an explanation, or a retry after a blank one — gets a
    non-blank string, so the blank-explanation retry loop exits first pass.
    """
    remaining = list(answers)

    def fake_input(prompt=""):
        if "Your answer" in prompt:
            return remaining.pop(0) if remaining else "A"
        return explanation

    return fake_input


class QuizBankTests(unittest.TestCase):

    def test_question_bank_contains_six_questions(self):
        self.assertEqual(len(QUESTIONS), 6)

    def test_each_question_has_four_options_and_an_answer(self):
        for number, question in enumerate(QUESTIONS, start=1):
            with self.subTest(question=number):
                self.assertEqual(
                    set(question["options"].keys()), {"A", "B", "C", "D"})
                self.assertIn(question["answer"], question["options"])

    def test_answer_key_matches_the_guide(self):
        actual = [question["answer"] for question in QUESTIONS]
        self.assertEqual(actual, ANSWER_KEY)


class GetAnswerTests(unittest.TestCase):

    def test_accepts_lowercase(self):
        with patch("builtins.input", return_value="b"):
            self.assertEqual(get_answer(), "B")

    def test_accepts_uppercase(self):
        with patch("builtins.input", return_value="d"):
            self.assertEqual(get_answer(), "D")

    # Exactly two inputs are consumed here, so exactly two are supplied.
    # If get_answer() asked for a third, StopIteration would surface as a
    # test error rather than an endless loop — which is the point.
    def test_retries_on_invalid_input(self):
        with patch("builtins.input", side_effect=iter(["X", "B"])):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(get_answer(), "B")

    def test_retries_multiple_times(self):
        with patch("builtins.input", side_effect=iter(["", "5", "c"])):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(get_answer(), "C")


class RunQuizTests(unittest.TestCase):

    def _run_quietly(self, answers):
        """Run run_quiz on scripted input, discarding its printing."""
        with patch("builtins.input", side_effect=scripted_input(answers)):
            with redirect_stdout(io.StringIO()):
                return run_quiz()

    def test_all_correct_scores_six(self):
        self.assertEqual(self._run_quietly(ANSWER_KEY), 6)

    # "A" is never the correct answer for any question, so every answer is wrong.
    def test_all_wrong_scores_zero(self):
        self.assertEqual(self._run_quietly(["A"] * 6), 0)

    def test_score_is_an_int_between_zero_and_six(self):
        score = self._run_quietly(ANSWER_KEY)
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 6)


if __name__ == "__main__":
    unittest.main()
