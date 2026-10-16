"""Tests for the Engineering Understanding Check."""

from campusflow.quiz import QUESTIONS
from campusflow.quiz_check import get_answer


def test_question_bank_contains_six_questions():
    """The assessment must contain exactly six questions."""
    assert len(QUESTIONS) == 6


def test_each_question_has_four_options_and_an_answer():
    """Every question must have valid options and a correct answer."""
    for question in QUESTIONS:
        assert set(question["options"]) == {"A", "B", "C", "D"}
        assert question["answer"] in question["options"]


def test_get_answer_accepts_lowercase(monkeypatch):
    """Lowercase answers should be accepted."""
    monkeypatch.setattr("builtins.input", lambda _: "b")

    assert get_answer() == "B"


def test_get_answer_retries_invalid_input(monkeypatch):
    """Invalid choices should be rejected before accepting a valid choice."""
    answers = iter(["X", "B"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert get_answer() == "B"