import unittest

from campusflow.search import search_tickets, filter_tickets


class TestSearchTickets(unittest.TestCase):

    def setUp(self):
        # Use fresh sample tickets for each test.
        self.tickets = [
            {
                "id": "T001",
                "title": "Broken lab projector",
                "category": "Hardware",
                "urgency": "high",
                "priority": "critical",
                "status": "open",
                "assigned_to": "Agene",
            },
            {
                "id": "T002",
                "title": "Wi-Fi connection failure",
                "category": "Network",
                "urgency": "medium",
                "priority": "medium",
                "status": "in_progress",
                "assigned_to": None,
            },
            {
                "id": "T003",
                "title": "Install Python software",
                "category": "Software",
                "urgency": "low",
                "priority": "low",
                "status": "resolved",
                "assigned_to": "Eyung",
            },
        ]

    def test_search_by_partial_title(self):
        results = search_tickets(self.tickets, "projector")

        self.assertEqual([ticket["id"] for ticket in results], ["T001"])

    def test_search_is_case_insensitive(self):
        results = search_tickets(self.tickets, "NETWORK")

        self.assertEqual([ticket["id"] for ticket in results], ["T002"])

    def test_search_by_ticket_id(self):
        results = search_tickets(self.tickets, "T002")

        self.assertEqual([ticket["id"] for ticket in results], ["T002"])

    def test_search_by_assignee(self):
        results = search_tickets(self.tickets, "eyung")

        self.assertEqual([ticket["id"] for ticket in results], ["T003"])

    def test_empty_query_returns_no_results(self):
        self.assertEqual(search_tickets(self.tickets, ""), [])
        self.assertEqual(search_tickets(self.tickets, "   "), [])

    def test_no_matches_returns_empty_list(self):
        self.assertEqual(search_tickets(self.tickets, "printer"), [])

    def test_search_does_not_modify_original_list(self):
        original = self.tickets.copy()

        search_tickets(self.tickets, "projector")

        self.assertEqual(self.tickets, original)


class TestFilterTickets(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            {
                "id": "T001",
                "title": "Broken lab projector",
                "category": "Hardware",
                "priority": "critical",
                "status": "open",
            },
            {
                "id": "T002",
                "title": "Wi-Fi connection failure",
                "category": "Network",
                "priority": "medium",
                "status": "in_progress",
            },
            {
                "id": "T003",
                "title": "Install Python software",
                "category": "Software",
                "priority": "low",
                "status": "resolved",
            },
        ]

    def test_filter_by_status(self):
        results = filter_tickets(self.tickets, status="open")

        self.assertEqual([ticket["id"] for ticket in results], ["T001"])

    def test_filter_by_priority(self):
        results = filter_tickets(self.tickets, priority="CRITICAL")

        self.assertEqual([ticket["id"] for ticket in results], ["T001"])

    def test_filter_by_category(self):
        results = filter_tickets(self.tickets, category="network")

        self.assertEqual([ticket["id"] for ticket in results], ["T002"])

    def test_combine_multiple_filters(self):
        results = filter_tickets(
            self.tickets,
            status="open",
            priority="critical",
            category="hardware",
        )

        self.assertEqual([ticket["id"] for ticket in results], ["T001"])

    def test_non_matching_filters_return_empty_list(self):
        results = filter_tickets(
            self.tickets,
            status="open",
            priority="low",
        )

        self.assertEqual(results, [])

    def test_no_filters_returns_all_tickets(self):
        results = filter_tickets(self.tickets)

        self.assertEqual(results, self.tickets)
        self.assertIsNot(results, self.tickets)

    def test_filter_does_not_modify_original_list(self):
        original = self.tickets.copy()

        filter_tickets(self.tickets, status="resolved")

        self.assertEqual(self.tickets, original)

    def test_non_string_filter_returns_empty_list(self):
        # Invalid filter values should not crash the application.
        self.assertEqual(
            filter_tickets(self.tickets, status=123),
            [],
        )
        self.assertEqual(
            filter_tickets(self.tickets, priority=["critical"]),
            [],
        )

    def test_none_filters_are_ignored(self):
        # None means the caller has not supplied that filter.
        results = filter_tickets(self.tickets, status=None)

        self.assertEqual(results, self.tickets)
        self.assertIsNot(results, self.tickets)


if __name__ == "__main__":
    unittest.main()