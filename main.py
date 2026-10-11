"""CampusFlow — Technical Helpdesk CLI Ticket Manager.

Shared entry point for the CampusFlow application.
Per design decisions §8: each feature's menu branch is a single dispatch call.
No business logic in main.py — all operations delegate to campusflow modules.
"""

import sys

from campusflow.errors import CorruptDataError
from campusflow.reports import build_report, work_queue
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, change_status, reopen_ticket

DATA_PATH = "data/tickets.json"


def prompt(text):
    """Prompt user for input and strip surrounding whitespace."""
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def handle_create_ticket(tickets):
    """F1: Collect inputs, dispatch create_ticket, save on success."""
    print("\n--- Create Ticket ---")
    title = prompt("Title: ")
    if title is None:
        return
    category = prompt("Category (Network, Hardware, Software, Other): ")
    if category is None:
        return
    urgency = prompt("Urgency (low, medium, high): ")
    if urgency is None:
        return
    affected_users = prompt("Affected users (positive integer): ")
    if affected_users is None:
        return

    ok, payload = create_ticket(tickets, title, category, urgency, affected_users)
    if ok:
        save_tickets(tickets, DATA_PATH)
        print(
            f"Success: Ticket {payload['id']} created "
            f"[{payload['priority']} priority, {payload['status']}]."
        )
    else:
        print(f"Error: {payload}")


def handle_list_and_view(tickets):
    """F2: List all tickets and optionally view a specific ticket."""
    print("\n--- All Tickets ---")
    if not tickets:
        print("No tickets found.")
        return

    print(
        f"{'ID':<6} {'Priority':<10} {'Status':<13} "
        f"{'Assignee':<12} {'Category':<10} {'Title'}"
    )
    print("-" * 75)
    for t in tickets:
        assignee = t.get("assigned_to") or "Unassigned"
        print(
            f"{t['id']:<6} {t['priority']:<10} {t['status']:<13} "
            f"{assignee:<12} {t['category']:<10} {t['title']}"
        )

    choice = prompt("\nEnter Ticket ID to inspect details (or press Enter to return): ")
    if choice:
        ticket_id = choice.upper()
        match = next((t for t in tickets if t["id"] == ticket_id), None)
        if match:
            print(f"\nDetails for {match['id']}:")
            print(f"  Title:          {match['title']}")
            print(f"  Category:       {match['category']}")
            print(f"  Urgency:        {match['urgency']}")
            print(f"  Affected Users: {match['affected_users']}")
            print(f"  Priority:       {match['priority']}")
            print(f"  Status:         {match['status']}")
            print(f"  Assigned To:    {match.get('assigned_to') or 'Unassigned'}")
        else:
            print(f"No ticket found with ID {choice}.")


def handle_assign_ticket(tickets):
    """F3: Assign ticket to staff member, save on success."""
    print("\n--- Assign Ticket ---")
    ticket_id = prompt("Ticket ID (e.g. T001): ")
    if not ticket_id:
        return
    staff_name = prompt("Staff Name: ")
    if staff_name is None:
        return

    ok, payload = assign_ticket(tickets, ticket_id.upper(), staff_name)
    if ok:
        save_tickets(tickets, DATA_PATH)
        print(f"Success: {payload['id']} assigned to {payload['assigned_to']}.")
    else:
        print(f"Error: {payload}")


def handle_change_status(tickets):
    """F4: Change status of a ticket along legal edges."""
    print("\n--- Change Status ---")
    ticket_id = prompt("Ticket ID: ")
    if not ticket_id:
        return
    new_status = prompt("New Status (in_progress, resolved): ")
    if not new_status:
        return

    ok, payload = change_status(tickets, ticket_id.upper(), new_status)
    if ok:
        save_tickets(tickets, DATA_PATH)
        print(f"Success: {payload['id']} status updated to {payload['status']}.")
    else:
        print(f"Error: {payload}")


def handle_reopen_ticket(tickets):
    """F4: Reopen a resolved ticket."""
    print("\n--- Reopen Ticket ---")
    ticket_id = prompt("Ticket ID to reopen: ")
    if not ticket_id:
        return

    ok, payload = reopen_ticket(tickets, ticket_id.upper())
    if ok:
        save_tickets(tickets, DATA_PATH)
        print(
            f"Success: {payload['id']} reopened (status: {payload['status']}, "
            f"assigned to: {payload.get('assigned_to') or 'Unassigned'})."
        )
    else:
        print(f"Error: {payload}")


def handle_work_queue(tickets):
    """F5: Display unresolved tickets ordered by priority and numeric ID."""
    print("\n--- Work Queue (Open & In Progress) ---")
    queue = work_queue(tickets)
    if not queue:
        print("Queue is empty. No outstanding tickets!")
        return

    print(
        f"{'ID':<6} {'Priority':<10} {'Status':<13} "
        f"{'Assignee':<12} {'Title'}"
    )
    print("-" * 65)
    for t in queue:
        assignee = t.get("assigned_to") or "Unassigned"
        print(
            f"{t['id']:<6} {t['priority']:<10} {t['status']:<13} "
            f"{assignee:<12} {t['title']}"
        )


def handle_summary_report(tickets):
    """F6: Display total tickets and counts by status and priority."""
    print("\n--- System Summary Report ---")
    report = build_report(tickets)

    print(f"Total Tickets: {report['total']}\n")

    print("By Status:")
    for status, count in report["by_status"].items():
        print(f"  {status:<15}: {count}")

    print("\nBy Priority:")
    for priority, count in report["by_priority"].items():
        print(f"  {priority:<15}: {count}")


def print_menu():
    """Display the main CLI navigation menu."""
    print("\n==============================")
    print("      CampusFlow Helpdesk     ")
    print("==============================")
    print("1. Create Ticket")
    print("2. List / View Tickets")
    print("3. Assign Ticket")
    print("4. Change Ticket Status")
    print("5. Reopen Resolved Ticket")
    print("6. View Work Queue")
    print("7. Summary Report")
    print("0. Exit")


def main():
    """Main application loop."""
    print("Starting CampusFlow...")
    try:
        tickets = load_tickets(DATA_PATH)
    except CorruptDataError as exc:
        print(f"\nCRITICAL: Failed to load tickets from {DATA_PATH}!")
        print(f"Reason: {exc}")
        print("Please resolve the corrupt data file before running CampusFlow.")
        sys.exit(1)

    while True:
        print_menu()
        choice = prompt("Select an option [0-7]: ")
        if choice is None or choice == "0":
            print("\nSaving tickets and exiting. Goodbye!")
            save_tickets(tickets, DATA_PATH)
            break
        elif choice == "1":
            handle_create_ticket(tickets)
        elif choice == "2":
            handle_list_and_view(tickets)
        elif choice == "3":
            handle_assign_ticket(tickets)
        elif choice == "4":
            handle_change_status(tickets)
        elif choice == "5":
            handle_reopen_ticket(tickets)
        elif choice == "6":
            handle_work_queue(tickets)
        elif choice == "7":
            handle_summary_report(tickets)
        else:
            print("Invalid selection. Please choose an option from the menu.")


if __name__ == "__main__":
    main()
