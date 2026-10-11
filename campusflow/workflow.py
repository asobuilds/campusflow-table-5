"""Ticket assignment and status workflow — Engineer B (F3 assign, F4 status).

Every public function here mutates the ticket dict in place and returns
(True, that_same_dict), or returns (False, "message") when the user's request
cannot be carried out. Nothing is copied — see docs/design-decisions.md §4.

TRANSITION RULES
Only three moves are legal, and each has exactly one entry point:

    open         -> in_progress    change_status, and only if assigned
    in_progress  -> resolved       change_status
    resolved     -> open           reopen_ticket

Everything else is rejected. change_status deliberately refuses resolved -> open
and points at reopen_ticket, so there is one path per transition and the two
cannot drift apart.

These rules were agreed between both engineers but are NOT in
docs/design-decisions.md. tests/test_workflow.py is the artifact of record.

STRUCTURAL CHECKING
Tickets are assumed already validated by load_tickets, so this module trusts
"id" and "status" and looks them up directly — the same boundary rule reports.py
follows. design-decisions §1 also names workflow.py as somewhere CorruptDataError
may be raised; that guard lands once campusflow/errors.py merges in from
feat/1-ticket-creation, since it does not exist on this branch yet.
"""

STATUSES = ("open", "in_progress", "resolved")

# The moves change_status is allowed to make. resolved -> open belongs to
# reopen_ticket, so it is absent here on purpose.
LEGAL_TRANSITIONS = {
    ("open", "in_progress"),
    ("in_progress", "resolved"),
}

RESOLVED_ASSIGN_MESSAGE = "Cannot assign a resolved ticket; reopen it first."


def _find_ticket(tickets, ticket_id):
    """Return the ticket dict carrying this id, or None if there is no match."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    return None


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign an unresolved ticket to a member of staff.

    Does NOT change status. Being assigned is the precondition for
    open -> in_progress, not the transition itself.

    Returns (True, ticket) or (False, message).
    """
    ticket = _find_ticket(tickets, ticket_id)
    if ticket is None:
        return False, f"No ticket with ID {ticket_id}."

    if ticket["status"] == "resolved":
        return False, RESOLVED_ASSIGN_MESSAGE

    if not isinstance(staff_name, str) or not staff_name.strip():
        return False, "Staff name cannot be blank."

    ticket["assigned_to"] = staff_name.strip()
    return True, ticket


def change_status(tickets, ticket_id, new_status):
    """Move a ticket along one of the legal edges.

    open -> in_progress requires the ticket to be assigned first, otherwise the
    queue would contain work nobody owns.

    Returns (True, ticket) or (False, message).
    """
    ticket = _find_ticket(tickets, ticket_id)
    if ticket is None:
        return False, f"No ticket with ID {ticket_id}."

    if not isinstance(new_status, str):
        return False, "Status must be text."

    target = new_status.strip().lower()
    current = ticket["status"]

    if target not in STATUSES:
        return False, f"Unknown status '{new_status.strip()}'."

    if target == current:
        return False, f"Ticket is already {current}."

    # Checked before the general transition rule so the user gets the useful
    # pointer rather than a bare rejection.
    if current == "resolved":
        return False, "Use reopen_ticket to reopen a resolved ticket."

    if (current, target) == ("open", "in_progress") and not ticket["assigned_to"]:
        return False, "Assign the ticket before starting work."

    if (current, target) not in LEGAL_TRANSITIONS:
        return False, f"Cannot move a ticket from {current} to {target}."

    ticket["status"] = target
    return True, ticket


def reopen_ticket(tickets, ticket_id):
    """Reopen a resolved ticket: resolved -> open.

    assigned_to is deliberately left alone. Clearing it would lose who was
    working on the ticket, and the reopened ticket would then have to be
    reassigned before it could move to in_progress again.

    Returns (True, ticket) or (False, message).
    """
    ticket = _find_ticket(tickets, ticket_id)
    if ticket is None:
        return False, f"No ticket with ID {ticket_id}."

    if ticket["status"] != "resolved":
        return False, (
            f"Only resolved tickets can be reopened; "
            f"this one is {ticket['status']}."
        )

    ticket["status"] = "open"
    return True, ticket
