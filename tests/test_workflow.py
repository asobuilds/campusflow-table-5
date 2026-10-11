"""Tests for campusflow.workflow — F3 (assign) and F4 (status workflow).

THIS FILE IS THE ARTIFACT OF RECORD for the transition rules.

The three legal moves were agreed between Engineer A and Engineer B, but they are
NOT written in docs/design-decisions.md — `git diff ebc6797 d62701a` is empty, so
the doc never carried them. The assertions below are the written contract. If the
doc and this file ever disagree, one of them is a bug and we settle it out loud.

Run with: python -m unittest discover -s tests -v
"""

import unittest

from campusflow.workflow import assign_ticket, change_status, reopen_ticket


def make_ticket(ticket_id, status="open", assigned_to=None, priority="medium", **overrides):
    """Build a well-formed ticket dict for a test fixture.

    Fixtures are built directly rather than through create_ticket, so every value
    here is the test's own responsibility.
    """
    ticket = {
        "id": ticket_id,
        "title": f"Ticket {ticket_id}",
        "category": "Network",
        "urgency": "low",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
    }
    ticket.update(overrides)
    return ticket


class WorkflowTestCase(unittest.TestCase):
    """Shared assertions for the (ok, payload) return contract."""

    def assertRejected(self, result):
        """Assert the (False, message) half of the contract, and return the message.

        A rejection with no message is a bug: the CLI has nothing to print.
        """
        ok, payload = result
        self.assertFalse(ok, "expected a rejection, got success")
        self.assertIsInstance(payload, str, "a rejection must carry a message string")
        self.assertTrue(payload.strip(), "the rejection message must not be empty")
        return payload


class AssignTicketTests(WorkflowTestCase):

    def test_assigns_an_open_ticket(self):
        ticket = make_ticket("T001")

        ok, _ = assign_ticket([ticket], "T001", "Agene")

        self.assertTrue(ok)
        self.assertEqual(ticket["assigned_to"], "Agene")

    def test_returns_the_same_dict_object_not_a_copy(self):
        """design-decisions §4: mutate in place, return the same dict."""
        ticket = make_ticket("T001")

        _, returned = assign_ticket([ticket], "T001", "Agene")

        self.assertIs(returned, ticket)

    def test_assign_does_not_change_status(self):
        """Being assigned is the precondition for open -> in_progress, not the
        transition itself. change_status performs the move."""
        ticket = make_ticket("T001", status="open")

        assign_ticket([ticket], "T001", "Agene")

        self.assertEqual(ticket["status"], "open")

    def test_rejects_assignment_on_a_resolved_ticket(self):
        """The agreed wording is part of the contract, so it is asserted exactly."""
        ticket = make_ticket("T001", status="resolved", assigned_to="Agene")

        message = self.assertRejected(assign_ticket([ticket], "T001", "Eyung"))

        self.assertEqual(message, "Cannot assign a resolved ticket; reopen it first.")
        self.assertEqual(ticket["assigned_to"], "Agene", "a rejected assign must not mutate")

    def test_rejects_an_unknown_ticket_id(self):
        self.assertRejected(assign_ticket([make_ticket("T001")], "T999", "Agene"))

    def test_rejects_a_blank_staff_name(self):
        for blank in ("", "   ", "\t\n"):
            with self.subTest(name=repr(blank)):
                ticket = make_ticket("T001")
                self.assertRejected(assign_ticket([ticket], "T001", blank))
                self.assertIsNone(ticket["assigned_to"])

    def test_rejects_a_non_string_staff_name(self):
        ticket = make_ticket("T001")
        self.assertRejected(assign_ticket([ticket], "T001", None))
        self.assertIsNone(ticket["assigned_to"])

    def test_strips_whitespace_from_the_staff_name(self):
        ticket = make_ticket("T001")

        assign_ticket([ticket], "T001", "  Agene  ")

        self.assertEqual(ticket["assigned_to"], "Agene")

    def test_reassignment_is_allowed_while_unresolved(self):
        ticket = make_ticket("T001", status="in_progress", assigned_to="Agene")

        ok, _ = assign_ticket([ticket], "T001", "Eyung")

        self.assertTrue(ok)
        self.assertEqual(ticket["assigned_to"], "Eyung")


class ChangeStatusTests(WorkflowTestCase):

    def test_open_to_in_progress_when_assigned(self):
        ticket = make_ticket("T001", status="open", assigned_to="Agene")

        ok, _ = change_status([ticket], "T001", "in_progress")

        self.assertTrue(ok)
        self.assertEqual(ticket["status"], "in_progress")

    def test_open_to_in_progress_rejected_when_unassigned(self):
        ticket = make_ticket("T001", status="open", assigned_to=None)

        self.assertRejected(change_status([ticket], "T001", "in_progress"))
        self.assertEqual(ticket["status"], "open")

    def test_in_progress_to_resolved(self):
        ticket = make_ticket("T001", status="in_progress", assigned_to="Agene")

        ok, _ = change_status([ticket], "T001", "resolved")

        self.assertTrue(ok)
        self.assertEqual(ticket["status"], "resolved")

    def test_resolving_keeps_the_assignee(self):
        """Resolving does not clear assigned_to. Who did the work is worth
        keeping, and reopen must have something to preserve."""
        ticket = make_ticket("T001", status="in_progress", assigned_to="Agene")

        change_status([ticket], "T001", "resolved")

        self.assertEqual(ticket["assigned_to"], "Agene")

    def test_rejects_open_to_resolved(self):
        ticket = make_ticket("T001", status="open", assigned_to="Agene")

        self.assertRejected(change_status([ticket], "T001", "resolved"))
        self.assertEqual(ticket["status"], "open")

    def test_rejects_in_progress_to_open(self):
        ticket = make_ticket("T001", status="in_progress", assigned_to="Agene")

        self.assertRejected(change_status([ticket], "T001", "open"))
        self.assertEqual(ticket["status"], "in_progress")

    def test_rejects_a_same_state_change(self):
        for status in ("open", "in_progress", "resolved"):
            with self.subTest(status=status):
                ticket = make_ticket("T001", status=status, assigned_to="Agene")
                self.assertRejected(change_status([ticket], "T001", status))
                self.assertEqual(ticket["status"], status)

    def test_resolved_to_open_points_at_reopen_ticket(self):
        """One transition, one entry point. change_status must not be a second
        way to reopen, or the two paths can drift apart."""
        ticket = make_ticket("T001", status="resolved", assigned_to="Agene")

        message = self.assertRejected(change_status([ticket], "T001", "open"))

        self.assertIn("reopen", message.lower())
        self.assertEqual(ticket["status"], "resolved")

    def test_rejects_an_unknown_status(self):
        ticket = make_ticket("T001", status="open")

        self.assertRejected(change_status([ticket], "T001", "urgent"))
        self.assertEqual(ticket["status"], "open")

    def test_rejects_an_unknown_ticket_id(self):
        self.assertRejected(change_status([make_ticket("T001")], "T999", "resolved"))

    def test_status_is_normalised(self):
        ticket = make_ticket("T001", status="open", assigned_to="Agene")

        ok, _ = change_status([ticket], "T001", "  IN_PROGRESS  ")

        self.assertTrue(ok)
        self.assertEqual(ticket["status"], "in_progress")

    def test_returns_the_same_dict_object_not_a_copy(self):
        ticket = make_ticket("T001", status="open", assigned_to="Agene")

        _, returned = change_status([ticket], "T001", "in_progress")

        self.assertIs(returned, ticket)


class ReopenTicketTests(WorkflowTestCase):

    def test_reopens_a_resolved_ticket(self):
        ticket = make_ticket("T001", status="resolved", assigned_to="Agene")

        ok, _ = reopen_ticket([ticket], "T001")

        self.assertTrue(ok)
        self.assertEqual(ticket["status"], "open")

    def test_reopen_preserves_the_assignee(self):
        """The bug this test exists for: a naive reopen resets assigned_to to
        None and silently loses who was working on the ticket."""
        ticket = make_ticket("T001", status="resolved", assigned_to="Agene")

        reopen_ticket([ticket], "T001")

        self.assertEqual(ticket["assigned_to"], "Agene")

    def test_reopened_ticket_can_restart_without_reassigning(self):
        """End to end. If reopen had wiped the assignee, the last step would be
        rejected with 'Assign the ticket before starting work.'"""
        ticket = make_ticket("T001", status="in_progress", assigned_to="Agene")

        change_status([ticket], "T001", "resolved")
        reopen_ticket([ticket], "T001")
        ok, _ = change_status([ticket], "T001", "in_progress")

        self.assertTrue(ok, "a reopened ticket should still be assigned")
        self.assertEqual(ticket["status"], "in_progress")

    def test_rejects_reopening_a_ticket_that_is_not_resolved(self):
        for status in ("open", "in_progress"):
            with self.subTest(status=status):
                ticket = make_ticket("T001", status=status)
                self.assertRejected(reopen_ticket([ticket], "T001"))
                self.assertEqual(ticket["status"], status)

    def test_rejects_an_unknown_ticket_id(self):
        self.assertRejected(reopen_ticket([make_ticket("T001")], "T999"))

    def test_returns_the_same_dict_object_not_a_copy(self):
        ticket = make_ticket("T001", status="resolved")

        _, returned = reopen_ticket([ticket], "T001")

        self.assertIs(returned, ticket)


class WorkflowIntegrationTests(WorkflowTestCase):
    """The full life of a ticket, through every legal edge and no others."""

    def test_full_ticket_lifecycle(self):
        ticket = make_ticket("T001")
        tickets = [ticket]

        self.assertTrue(assign_ticket(tickets, "T001", "Agene")[0])
        self.assertTrue(change_status(tickets, "T001", "in_progress")[0])
        self.assertTrue(change_status(tickets, "T001", "resolved")[0])
        self.assertTrue(reopen_ticket(tickets, "T001")[0])
        self.assertTrue(change_status(tickets, "T001", "in_progress")[0])

        self.assertEqual(ticket["status"], "in_progress")
        self.assertEqual(ticket["assigned_to"], "Agene")
        self.assertIs(tickets[0], ticket, "the list must still hold the same dict")

    def test_a_ticket_that_never_moved_is_untouched_by_rejections(self):
        ticket = make_ticket("T001", status="open", assigned_to=None)

        change_status([ticket], "T001", "resolved")
        change_status([ticket], "T001", "in_progress")
        reopen_ticket([ticket], "T001")
        assign_ticket([ticket], "T001", "   ")

        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])


if __name__ == "__main__":
    unittest.main()
