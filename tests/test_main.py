"""Tests for main.py CLI menu handlers.

Ensures that every menu handler dispatches to the underlying module,
handles success and failure correctly, and complies with §8: no business
logic in main.py.
"""

import io
import unittest
from unittest.mock import patch

from campusflow.errors import CorruptDataError
from main import (
    handle_assign_ticket,
    handle_change_status,
    handle_create_ticket,
    handle_list_and_view,
    handle_reopen_ticket,
    handle_summary_report,
    handle_work_queue,
    main,
)


class TestMainHandlers(unittest.TestCase):

    def setUp(self):
        self.tickets = []

    @patch("builtins.input", side_effect=["Broken lab projector", "Hardware", "high", "12"])
    @patch("main.save_tickets")
    def test_handle_create_ticket_success(self, mock_save, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_create_ticket(self.tickets)
            self.assertEqual(len(self.tickets), 1)
            self.assertEqual(self.tickets[0]["id"], "T001")
            self.assertEqual(self.tickets[0]["priority"], "critical")
            self.assertIn("Success: Ticket T001 created", out.getvalue())
            mock_save.assert_called_once()

    @patch("builtins.input", side_effect=["", "Hardware", "high", "12"])
    @patch("main.save_tickets")
    def test_handle_create_ticket_validation_error(self, mock_save, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_create_ticket(self.tickets)
            self.assertEqual(len(self.tickets), 0)
            self.assertIn("Error:", out.getvalue())
            mock_save.assert_not_called()

    @patch("builtins.input", side_effect=["T001", "Agene"])
    @patch("main.save_tickets")
    def test_handle_assign_ticket_success(self, mock_save, mock_input):
        self.tickets = [{"id": "T001", "status": "open", "assigned_to": None}]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_assign_ticket(self.tickets)
            self.assertEqual(self.tickets[0]["assigned_to"], "Agene")
            self.assertIn("Success: T001 assigned to Agene", out.getvalue())
            mock_save.assert_called_once()

    @patch("builtins.input", side_effect=["T999", "Agene"])
    @patch("main.save_tickets")
    def test_handle_assign_ticket_unknown_id(self, mock_save, mock_input):
        self.tickets = [{"id": "T001", "status": "open", "assigned_to": None}]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_assign_ticket(self.tickets)
            self.assertIn("Error:", out.getvalue())
            mock_save.assert_not_called()

    @patch("builtins.input", side_effect=["T001", "in_progress"])
    @patch("main.save_tickets")
    def test_handle_change_status_success(self, mock_save, mock_input):
        self.tickets = [{"id": "T001", "status": "open", "assigned_to": "Agene"}]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_change_status(self.tickets)
            self.assertEqual(self.tickets[0]["status"], "in_progress")
            self.assertIn("Success: T001 status updated to in_progress", out.getvalue())
            mock_save.assert_called_once()

    @patch("builtins.input", side_effect=["T001", "resolved"])
    @patch("main.save_tickets")
    def test_handle_change_status_invalid_transition(self, mock_save, mock_input):
        self.tickets = [{"id": "T001", "status": "open", "assigned_to": "Agene"}]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_change_status(self.tickets)
            self.assertEqual(self.tickets[0]["status"], "open")
            self.assertIn("Error:", out.getvalue())
            mock_save.assert_not_called()

    @patch("builtins.input", side_effect=["T001"])
    @patch("main.save_tickets")
    def test_handle_reopen_ticket_success(self, mock_save, mock_input):
        self.tickets = [{"id": "T001", "status": "resolved", "assigned_to": "Agene"}]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_reopen_ticket(self.tickets)
            self.assertEqual(self.tickets[0]["status"], "open")
            self.assertEqual(self.tickets[0]["assigned_to"], "Agene")
            self.assertIn("Success: T001 reopened", out.getvalue())
            mock_save.assert_called_once()

    def test_handle_work_queue_output(self):
        self.tickets = [
            {"id": "T001", "priority": "low", "status": "open", "title": "Low item"},
            {"id": "T002", "priority": "critical", "status": "open", "title": "Crit item"},
        ]
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_work_queue(self.tickets)
            text = out.getvalue()
            self.assertIn("T002", text)
            self.assertIn("critical", text)
            # T002 must appear before T001.
            self.assertLess(text.index("T002"), text.index("T001"))

    def test_handle_summary_report_output(self):
        self.tickets = [
            {
                "id": "T001",
                "priority": "high",
                "status": "open",
                "category": "Network",
                "was_reopened": False,
            },
            {
                "id": "T002",
                "priority": "low",
                "status": "resolved",
                "category": "Hardware",
                "was_reopened": False,
            },
        ]

        with patch("sys.stdout", new_callable=io.StringIO) as out:
            handle_summary_report(self.tickets)
            text = out.getvalue()

            self.assertIn("Total Tickets: 2", text)
            self.assertIn("open", text)
            self.assertIn("resolved", text)
            self.assertIn("high", text)

class TestMainAppLoop(unittest.TestCase):

    @patch("main.load_tickets", return_value=[])
    @patch("main.save_tickets")
    @patch("builtins.input", side_effect=["0"])
    def test_main_exits_cleanly(self, mock_input, mock_save, mock_load):
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            main()
            self.assertIn("Starting CampusFlow...", out.getvalue())
            self.assertIn("Saving tickets and exiting. Goodbye!", out.getvalue())
            mock_save.assert_called_once()

    @patch("main.load_tickets", side_effect=CorruptDataError("Malformed test JSON"))
    def test_main_handles_corrupt_data_and_halts(self, mock_load):
        with patch("sys.stdout", new_callable=io.StringIO) as out, self.assertRaises(SystemExit):
            main()
        self.assertIn("CRITICAL: Failed to load tickets", out.getvalue())


if __name__ == "__main__":
    unittest.main()
