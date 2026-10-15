"""Tests for campusflow/notes.py — the structured follow-up notes feature.

Covers §12.8 of docs/design-decisions.md.
Written test-first, against the frozen §12 contract.
"""

import unittest

from campusflow.notes import add_note, get_ticket_notes, next_note_id


def make_ticket(ticket_id="T001", status="open"):
    """Minimal valid ticket for note tests. Matches the §2 schema + §12 fields."""
    return {
        "id": ticket_id,
        "title": "Wi-Fi down",
        "category": "Network",
        "urgency": "high",
        "affected_users": 12,
        "priority": "critical",
        "status": status,
        "assigned_to": None,
        "notes": [],
        "was_reopened": False,
    }


class NextNoteIdTests(unittest.TestCase):

    def test_empty_notes_returns_n001(self):
        ticket = make_ticket()
        self.assertEqual(next_note_id(ticket), "N001")

    def test_one_note_returns_n002(self):
        ticket = make_ticket()
        ticket["notes"] = [{"note_id": "N001", "author": "A", "message": "hello there"}]
        self.assertEqual(next_note_id(ticket), "N002")

    def test_gap_in_note_ids_uses_max_plus_one(self):
        ticket = make_ticket()
        ticket["notes"] = [
            {"note_id": "N001", "author": "A", "message": "first one"},
            {"note_id": "N003", "author": "B", "message": "third one"},
        ]
        self.assertEqual(next_note_id(ticket), "N004")


class AddNoteTests(unittest.TestCase):

    def test_valid_note_on_open_ticket(self):
        tickets = [make_ticket()]
        ok, note = add_note(tickets, "T001", "Mentor A", "Wi-Fi router reboot attempted")
        self.assertTrue(ok)
        self.assertEqual(note["note_id"], "N001")
        self.assertEqual(note["author"], "Mentor A")
        self.assertEqual(note["message"], "Wi-Fi router reboot attempted")
        self.assertEqual(len(tickets[0]["notes"]), 1)

    def test_valid_note_on_in_progress_ticket(self):
        tickets = [make_ticket(status="in_progress")]
        ok, note = add_note(tickets, "T001", "Mentor A", "Investigating switch ports")
        self.assertTrue(ok)
        self.assertEqual(note["note_id"], "N001")

    def test_second_note_gets_n002(self):
        tickets = [make_ticket()]
        add_note(tickets, "T001", "Mentor A", "Wi-Fi router reboot attempted")
        ok, note = add_note(tickets, "T001", "Mentor B", "Investigating switch ports")
        self.assertTrue(ok)
        self.assertEqual(note["note_id"], "N002")

    def test_note_on_resolved_ticket_rejected(self):
        tickets = [make_ticket(status="resolved")]
        ok, msg = add_note(tickets, "T001", "Mentor A", "Trying anyway here")
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)
        self.assertEqual(len(tickets[0]["notes"]), 0)

    def test_unknown_ticket_id_rejected(self):
        tickets = [make_ticket()]
        ok, msg = add_note(tickets, "T999", "Mentor A", "Wi-Fi router reboot attempted")
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)
        self.assertEqual(len(tickets[0]["notes"]), 0)

    def test_blank_author_rejected(self):
        tickets = [make_ticket()]
        ok, msg = add_note(tickets, "T001", "   ", "Wi-Fi router reboot attempted")
        self.assertFalse(ok)
        self.assertEqual(len(tickets[0]["notes"]), 0)

    def test_message_too_short_rejected(self):
        tickets = [make_ticket()]
        ok, msg = add_note(tickets, "T001", "Mentor A", "abc")
        self.assertFalse(ok)
        self.assertEqual(len(tickets[0]["notes"]), 0)

    def test_message_too_long_rejected(self):
        tickets = [make_ticket()]
        long_message = "x" * 301
        ok, msg = add_note(tickets, "T001", "Mentor A", long_message)
        self.assertFalse(ok)
        self.assertEqual(len(tickets[0]["notes"]), 0)

    def test_failed_attempt_does_not_consume_note_id(self):
        tickets = [make_ticket()]
        # Fail one attempt — author blank
        add_note(tickets, "T001", "   ", "Wi-Fi router reboot attempted")
        # Succeed on the next
        ok, note = add_note(tickets, "T001", "Mentor A", "Wi-Fi router reboot attempted")
        self.assertTrue(ok)
        self.assertEqual(note["note_id"], "N001")


class GetTicketNotesTests(unittest.TestCase):

    def test_ticket_with_no_notes_returns_empty_list(self):
        tickets = [make_ticket()]
        ok, notes = get_ticket_notes(tickets, "T001")
        self.assertTrue(ok)
        self.assertEqual(notes, [])

    def test_ticket_with_notes_returns_them(self):
        tickets = [make_ticket()]
        add_note(tickets, "T001", "A", "hello there world")
        add_note(tickets, "T001", "B", "second message here")
        ok, notes = get_ticket_notes(tickets, "T001")
        self.assertTrue(ok)
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0]["note_id"], "N001")
        self.assertEqual(notes[1]["note_id"], "N002")

    def test_unknown_ticket_returns_false(self):
        tickets = [make_ticket()]
        ok, msg = get_ticket_notes(tickets, "T999")
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    def test_notes_are_returned_sorted_by_numeric_note_id(self):
        # §12.4 — get_ticket_notes returns notes in numeric note_id order.
        # A hand-edited file can have them out of order; the API must not.
        tickets = [make_ticket()]
        tickets[0]["notes"] = [
            {"note_id": "N003", "author": "C", "message": "third message here"},
            {"note_id": "N001", "author": "A", "message": "first message here"},
            {"note_id": "N002", "author": "B", "message": "second message here"},
        ]
        ok, notes = get_ticket_notes(tickets, "T001")
        self.assertTrue(ok)
        self.assertEqual(
            [n["note_id"] for n in notes],
            ["N001", "N002", "N003"],
        )

    def test_notes_sorted_numerically_not_lexicographically(self):
        # N10 sorts after N9, not after N1. Numeric comparison required.
        tickets = [make_ticket()]
        tickets[0]["notes"] = [
            {"note_id": "N010", "author": "Ten", "message": "tenth message here"},
            {"note_id": "N002", "author": "Two", "message": "second message here"},
            {"note_id": "N001", "author": "One", "message": "first message here"},
        ]
        ok, notes = get_ticket_notes(tickets, "T001")
        self.assertTrue(ok)
        self.assertEqual(
            [n["note_id"] for n in notes],
            ["N001", "N002", "N010"],
        )


if __name__ == "__main__":
    unittest.main()