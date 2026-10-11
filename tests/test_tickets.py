import unittest

from campusflow.tickets import calculate_priority, create_ticket


class TestTicketCreation(unittest.TestCase):

    def test_valid_ticket_creates_t001(self):
        tickets = []
        ok, ticket = create_ticket(tickets, "Wi-Fi down", "Network", "high", 3)
        self.assertTrue(ok)
        self.assertIsInstance(ticket, dict)
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(len(tickets), 1)

    def test_second_ticket_gets_t002(self):
        tickets = []
        create_ticket(tickets, "First", "Network", "low", 1)
        ok, second = create_ticket(tickets, "Second", "Hardware", "low", 1)
        self.assertTrue(ok)
        self.assertEqual(second["id"], "T002")

    def test_gap_in_ids_uses_max_plus_one(self):
        tickets = [{"id": "T001"}, {"id": "T003"}]
        ok, ticket = create_ticket(tickets, "New", "Other", "low", 1)
        self.assertTrue(ok)
        self.assertEqual(ticket["id"], "T004")

    def test_blank_title_rejected(self):
        tickets = []
        ok, message = create_ticket(tickets, "", "Network", "low", 1)
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_affected_users_zero_rejected(self):
        tickets = []
        ok, message = create_ticket(tickets, "Valid title", "Network", "low", 0)
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_affected_users_decimal_rejected(self):
        tickets = []
        ok, message = create_ticket(tickets, "Valid title", "Network", "low", 2.5)
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_affected_users_bool_rejected(self):
        tickets = []
        # True == 1 in Python; we reject bools before ints.
        ok, message = create_ticket(tickets, "Valid title", "Network", "low", True)
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_affected_users_string_number_accepted(self):
        tickets = []
        ok, ticket = create_ticket(tickets, "Valid title", "Network", "low", "12")
        self.assertTrue(ok)
        self.assertEqual(ticket["affected_users"], 12)
        self.assertIsInstance(ticket["affected_users"], int)

    def test_urgency_case_insensitive(self):
        tickets = []
        ok, ticket = create_ticket(tickets, "Valid title", "Network", "HIGH", 1)
        self.assertTrue(ok)
        self.assertEqual(ticket["urgency"], "high")

    def test_priority_high_10_users_is_critical(self):
        self.assertEqual(calculate_priority("high", 10), "critical")

    def test_priority_high_9_users_is_high(self):
        self.assertEqual(calculate_priority("high", 9), "high")

    def test_priority_medium_small_users_is_medium(self):
        # Rule 3: urgency == "medium" fires even though 2 < 3.
        self.assertEqual(calculate_priority("medium", 2), "medium")

    def test_priority_low_small_users_is_low(self):
        self.assertEqual(calculate_priority("low", 1), "low")

    def test_priority_normalization_masked_bug(self):
        # This catches the bug where create_ticket fails to normalize
        # "High" before calculate_priority runs. If normalization is
        # skipped, calculate_priority falls through all rules to "low".
        tickets = []
        ok, ticket = create_ticket(tickets, "Valid title", "Network", "High", 2)
        self.assertTrue(ok)
        self.assertEqual(ticket["priority"], "high")

    # --- B's review (PR #9) — new tests for the two blocking fixes ---

    def test_affected_users_none_rejected(self):
        # int(None) raises TypeError, not ValueError. Both must be caught
        # so §1's contract holds: user-fixable failures return (False, msg).
        tickets = []
        ok, message = create_ticket(tickets, "Valid title", "Network", "low", None)
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_affected_users_list_rejected(self):
        # int([]) raises TypeError too. Same contract.
        tickets = []
        ok, message = create_ticket(tickets, "Valid title", "Network", "low", [])
        self.assertFalse(ok)
        self.assertIsInstance(message, str)
        self.assertEqual(len(tickets), 0)

    def test_category_with_surrounding_whitespace_accepted(self):
        # "  Network  " should normalize to "Network".
        tickets = []
        ok, ticket = create_ticket(tickets, "Valid title", "  Network  ", "low", 1)
        self.assertTrue(ok)
        self.assertEqual(ticket["category"], "Network")

    def test_urgency_with_surrounding_whitespace_accepted(self):
        tickets = []
        ok, ticket = create_ticket(tickets, "Valid title", "Network", "  HIGH  ", 1)
        self.assertTrue(ok)
        self.assertEqual(ticket["urgency"], "high")

    def test_validate_returns_two_tuple_with_nested_four_tuple(self):
        # Pins the exact return shape of validate_ticket_input.
        # If a caller assumes the wrong shape, this fails and points
        # at the bug instead of letting it surface at runtime.
        from campusflow.tickets import validate_ticket_input
        result = validate_ticket_input("Wi-Fi down", "Network", "high", 5)
        self.assertEqual(len(result), 2)
        ok, payload = result
        self.assertTrue(ok)
        self.assertEqual(len(payload), 4)
        self.assertEqual(payload, ("Wi-Fi down", "Network", "high", 5))