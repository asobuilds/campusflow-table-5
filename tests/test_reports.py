"""Tests for campusflow.reports — F5 WORK QUEUE and F6 REPORTS.

Covers the acceptance criteria of Issue #4 (queue) and Issue #5 (report).
Contract: docs/design-decisions.md §3.

Run with: python -m unittest discover -s tests -v
"""

import copy
import unittest

from campusflow.reports import build_report, work_queue


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
        "was_reopened": False,
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
            "was_reopened",
        }
        self.assertEqual(set(make_ticket("T001").keys()), expected)

    def test_overrides_are_applied(self):
        ticket = make_ticket("T007", "critical", status="in_progress")
        self.assertEqual(ticket["id"], "T007")
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "in_progress")


class BuildReportTests(unittest.TestCase):
    """F6 — build_report. Issue #5.

    The key behaviour is that the report's *shape* does not depend on the data:
    every known status and priority is always present, so an empty store reports
    zeroes and a caller never needs .get(key, 0).
    """

    def test_empty_store_reports_zeroes_for_every_key(self):
        report = build_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(
            report["by_status"],
            {"open": 0, "in_progress": 0, "resolved": 0},
        )
        self.assertEqual(
            report["by_priority"],
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        )

    def test_counts_by_status(self):
        tickets = [
            make_ticket("T001", status="open"),
            make_ticket("T002", status="open"),
            make_ticket("T003", status="in_progress"),
            make_ticket("T004", status="resolved"),
        ]

        self.assertEqual(
            build_report(tickets)["by_status"],
            {"open": 2, "in_progress": 1, "resolved": 1},
        )

    def test_counts_by_priority(self):
        tickets = [
            make_ticket("T001", "critical"),
            make_ticket("T002", "high"),
            make_ticket("T003", "high"),
        ]

        self.assertEqual(
            build_report(tickets)["by_priority"],
            {"critical": 1, "high": 2, "medium": 0, "low": 0},
        )

    def test_several_tickets_in_one_status(self):
        tickets = [make_ticket(f"T{i:03d}", "low", status="open") for i in range(1, 4)]

        self.assertEqual(build_report(tickets)["by_status"]["open"], 3)

    def test_total_matches_the_number_of_tickets(self):
        tickets = [make_ticket(f"T{i:03d}", "low") for i in range(1, 6)]

        self.assertEqual(build_report(tickets)["total"], 5)

    def test_report_keys_are_exactly_the_known_values(self):
        """Hardcoded on purpose: importing the constants would make this assert
        that the constants equal themselves."""
        report = build_report([])

        self.assertEqual(set(report["by_status"]), {"open", "in_progress", "resolved"})
        self.assertEqual(set(report["by_priority"]), {"critical", "high", "medium", "low"})

    def test_shape_does_not_change_with_the_data(self):
        empty = build_report([])
        populated = build_report([make_ticket("T001", "critical", status="resolved")])

        self.assertEqual(set(empty), set(populated))
        self.assertEqual(set(empty["by_status"]), set(populated["by_status"]))
        self.assertEqual(set(empty["by_priority"]), set(populated["by_priority"]))

    def test_status_and_priority_are_counted_independently(self):
        """Resolved tickets are counted here — unlike in work_queue, the report
        covers the whole store, not just outstanding work."""
        tickets = [
            make_ticket("T001", "critical", status="resolved"),
            make_ticket("T002", "low", status="resolved"),
        ]

        report = build_report(tickets)

        self.assertEqual(report["by_status"]["resolved"], 2)
        self.assertEqual(report["by_priority"]["critical"], 1)
        self.assertEqual(report["by_priority"]["low"], 1)

    def test_input_is_not_mutated(self):
        tickets = [
            make_ticket("T001", "critical"),
            make_ticket("T002", "low", status="resolved"),
        ]
        before = copy.deepcopy(tickets)

        build_report(tickets)

        self.assertEqual(tickets, before, "build_report must not modify the input")

    def test_calls_do_not_share_state(self):
        """If build_report ever returned a module-level template dict, counts
        would accumulate across calls. Invisible until the second call."""
        first = build_report([make_ticket("T001", "high", status="open")])
        second = build_report([make_ticket("T002", "high", status="open")])

        self.assertEqual(first["by_priority"]["high"], 1)
        self.assertEqual(second["by_priority"]["high"], 1)
        self.assertIsNot(first["by_status"], second["by_status"])
        self.assertIsNot(first["by_priority"], second["by_priority"])

class ExtendedReportTests(unittest.TestCase):

    def test_counts_by_category(self):
        tickets = [
            make_ticket("T001", category="Network"),
            make_ticket("T002", category="Hardware"),
            make_ticket("T003", category="Network"),
            make_ticket("T004", category="Software"),
        ]

        report = build_report(tickets)

        self.assertEqual(
            report["by_category"],
            {
                "Network": 2,
                "Hardware": 1,
                "Software": 1,
                "Other": 0,
            },
        )

    def test_counts_unresolved_tickets(self):
        tickets = [
            make_ticket("T001", status="open"),
            make_ticket("T002", status="in_progress"),
            make_ticket("T003", status="resolved"),
        ]

        report = build_report(tickets)

        self.assertEqual(report["unresolved"], 2)

    def test_counts_resolved_tickets(self):
        tickets = [
            make_ticket("T001", status="resolved"),
            make_ticket("T002", status="open"),
            make_ticket("T003", status="resolved"),
        ]

        report = build_report(tickets)

        self.assertEqual(report["resolved"], 2)

    def test_calculates_resolution_percentage(self):
        tickets = [
            make_ticket("T001", status="resolved"),
            make_ticket("T002", status="resolved"),
            make_ticket("T003", status="open"),
            make_ticket("T004", status="in_progress"),
        ]

        report = build_report(tickets)

        self.assertEqual(report["resolution_percentage"], 50.0)

    def test_empty_store_has_zero_resolution_percentage(self):
        report = build_report([])

        self.assertEqual(report["resolution_percentage"], 0.0)

    def test_counts_tickets_that_were_reopened(self):
        tickets = [
            make_ticket("T001", status="open", was_reopened=False),
            make_ticket("T002", status="open", was_reopened=True),
            make_ticket("T003", status="resolved", was_reopened=True),
            make_ticket("T004", status="in_progress", was_reopened=False),
        ]

        report = build_report(tickets)

        self.assertEqual(report["reopened"], 2)

    def test_reopened_count_is_zero_when_no_tickets_were_reopened(self):
        tickets = [
            make_ticket("T001", status="open", was_reopened=False),
            make_ticket("T002", status="resolved", was_reopened=False),
        ]

        report = build_report(tickets)

        self.assertEqual(report["reopened"], 0)

    def test_empty_store_has_zero_reopened_tickets(self):
        report = build_report([])

        self.assertEqual(report["reopened"], 0)

    def test_report_combines_all_metrics(self):
        tickets = [
            make_ticket(
                "T001",
                category="Network",
                priority="high",
                status="resolved",
                was_reopened=True,
            ),
            make_ticket(
                "T002",
                category="Hardware",
                priority="low",
                status="in_progress",
            ),
            make_ticket(
                "T003",
                category="Network",
                priority="medium",
                status="open",
            ),
        ]

        report = build_report(tickets)

        self.assertEqual(report["total"], 3)
        self.assertEqual(report["resolved"], 1)
        self.assertEqual(report["unresolved"], 2)
        self.assertAlmostEqual(report["resolution_percentage"], 100 / 3)
        self.assertEqual(report["by_category"]["Network"], 2)
        self.assertEqual(report["by_category"]["Hardware"], 1)
        self.assertEqual(report["reopened"], 1)

if __name__ == "__main__":
    unittest.main()
