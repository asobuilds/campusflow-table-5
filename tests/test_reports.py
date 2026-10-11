"""Tests for campusflow.reports — F5 WORK QUEUE.

Covers the acceptance criteria of Issue #4. Contract: docs/design-decisions.md §7.

Run with: python -m unittest discover -s tests -v
"""

import copy
import unittest

from campusflow.reports import work_queue


def make_ticket(ticket_id, priority="low", status="open", **overrides):
    """Build a well-formed ticket dict for a test fixture.

    Fixtures are built directly rather than through create_ticket, so every value
    here is the test's own responsibility. All values used are legal ones, which
    keeps work_queue's "priority is already valid" assumption intact.
    """
    ticket = {
        "id": ticket_id,
        "title": f"Ticket {ticket_id}",
        "category": "Network",
        "urgency": "low",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": None,
    }
    ticket.update(overrides)
    return ticket


class WorkQueueTests(unittest.TestCase):

    # --- ordering ---------------------------------------------------------

    def test_orders_by_priority_critical_first(self):
        """All four priorities present, given out of order."""
        tickets = [
            make_ticket("T001", "low"),
            make_ticket("T002", "medium"),
            make_ticket("T003", "critical"),
            make_ticket("T004", "high"),
        ]

        result = work_queue(tickets)

        self.assertEqual(
            [t["id"] for t in result],
            ["T003", "T004", "T002", "T001"],
        )

    def test_tie_break_is_numeric_not_lexicographic(self):
        """T999 must sort before T1000, whichever order the two arrive in.

        T999/T1000 is the pair that crosses an ID width boundary, so string
        comparison inverts it ('9' > '1' at index 1). It is also the pair where
        arrival order decides the outcome under a stability-only sort.

        The two assertions catch two different bugs:
          - in_id_order catches a key that compares IDs as strings.
          - in_reverse_order catches a key with no tie-break at all (priority
            only, leaning on sort stability). That version returns T1000 first
            here, so a queue's order would depend on the order of the file.
        """
        in_id_order = [make_ticket("T999", "critical"), make_ticket("T1000", "critical")]
        in_reverse_order = [make_ticket("T1000", "critical"), make_ticket("T999", "critical")]

        self.assertEqual([t["id"] for t in work_queue(in_id_order)], ["T999", "T1000"])
        self.assertEqual([t["id"] for t in work_queue(in_reverse_order)], ["T999", "T1000"])

    def test_tie_break_within_same_id_width(self):
        """A guard case, not a failing case.

        This pair orders the same way under lexicographic and numeric comparison,
        so it cannot detect the bug the test above detects. It is kept so that the
        obvious behaviour stays pinned once the numeric key is in place.
        """
        tickets = [make_ticket("T010", "high"), make_ticket("T002", "high")]

        self.assertEqual([t["id"] for t in work_queue(tickets)], ["T002", "T010"])

    # --- filtering --------------------------------------------------------

    def test_excludes_resolved_tickets(self):
        tickets = [
            make_ticket("T001", "critical", status="open"),
            make_ticket("T002", "high", status="in_progress"),
            make_ticket("T003", "critical", status="resolved"),
        ]

        result = work_queue(tickets)

        self.assertEqual([t["id"] for t in result], ["T001", "T002"])

    def test_all_resolved_returns_empty_list(self):
        tickets = [
            make_ticket("T001", "critical", status="resolved"),
            make_ticket("T002", "low", status="resolved"),
        ]

        self.assertEqual(work_queue(tickets), [])

    # --- empty / boundary -------------------------------------------------

    def test_empty_input_returns_empty_list(self):
        """Must not raise. The F6 report has the same requirement."""
        self.assertEqual(work_queue([]), [])

    # --- read-only projection --------------------------------------------

    def test_input_list_is_not_mutated(self):
        tickets = [
            make_ticket("T002", "low"),
            make_ticket("T001", "critical"),
        ]
        before = copy.deepcopy(tickets)

        result = work_queue(tickets)

        self.assertEqual(
            tickets, before,
            "work_queue must not reorder or modify the input list",
        )
        self.assertIsNot(
            result, tickets,
            "work_queue must return a new list, not the input list itself",
        )


class InputFixtureTests(unittest.TestCase):
    """Sanity checks on the fixtures themselves.

    If make_ticket ever produced a ticket missing a required field, every test
    above would be testing something invalid. These pin the fixture shape.
    """

    def test_fixture_has_every_required_field(self):
        expected = {
            "id", "title", "category", "urgency",
            "affected_users", "priority", "status", "assigned_to",
        }
        self.assertEqual(set(make_ticket("T001").keys()), expected)

    def test_overrides_are_applied(self):
        ticket = make_ticket("T007", "critical", status="in_progress")
        self.assertEqual(ticket["id"], "T007")
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
