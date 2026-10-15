"""
Structured follow-up notes for CampusFlow tickets.

Contract: docs/design-decisions.md §12 (12.1–12.6).

Pure data-in, data-out — no printing, no terminal I/O, no file access.
The only mutation is the append to ticket["notes"] inside add_note (§4).
"""


def _find_ticket(tickets, ticket_id):
    """
    Return the ticket dict in `tickets` whose "id" == ticket_id, or None
    if no ticket matches.

    Private helper. Does no validation and mutates nothing — it trusts
    the in-memory list (load_tickets enforces structure, §12.7).
    """
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    return None


def next_note_id(ticket):
    """
    Pure helper. No I/O, no mutation.

    Returns the next note ID for `ticket`, as f"N{n:03d}":
        - "N001" when the ticket has no notes yet.
        - max(existing note numbers) + 1 otherwise.

    Uses max+1 — not len+1 — mirroring create_ticket's ticket-ID rule
    (§12.5). Each ticket keeps its own sequence, so T002's first note is
    also N001. A gap in note IDs must not cause the next note to reuse
    an old ID.
    """
    if not ticket["notes"]:
        return "N001"
    highest = max(int(n["note_id"][1:]) for n in ticket["notes"])
    return f"N{highest + 1:03d}"


def add_note(tickets, ticket_id, author, message):
    """
    Append a note to the ticket whose "id" == ticket_id.

    Returns:
        (True, note_dict) on success.
        (False, "human-readable message") on the first user-fixable
            failure, checked in this order (§12.3):
            1. no ticket with that ID
            2. ticket is resolved
            3. author is not a string, or blank after .strip()
            4. message is not a string, or shorter than 5 chars
               after .strip()
            5. message longer than 300 chars after .strip()

    On any failure path nothing is mutated: tickets, the ticket, and
    ticket["notes"] are all unchanged, and no note ID is consumed. The
    next successful call uses the ID the failed call would have used
    (§12.3 ID-continuity invariant). No partial mutation.
    """
    ticket = _find_ticket(tickets, ticket_id)
    if ticket is None:
        return (False, f"No ticket with ID {ticket_id}.")

    # §12.6 — only open/in_progress tickets accept notes. The frozen status
    # set is exactly {open, in_progress, resolved} (§5), so testing for
    # "resolved" is the same as testing the allowlist.
    if ticket["status"] == "resolved":
        return (False, "Cannot add a note to a resolved ticket; reopen it first.")

    if not isinstance(author, str) or not author.strip():
        return (False, "Author cannot be blank.")

    # isinstance is checked before .strip()/len() so a non-string input
    # returns (False, msg) instead of raising AttributeError/TypeError.
    if not isinstance(message, str) or len(message.strip()) < 5:
        return (False, "Message must be at least 5 characters.")
    if len(message.strip()) > 300:
        return (False, "Message must be at most 300 characters.")

    # Every check has passed, so it is safe to mutate now. Compute the ID
    # first: a failure above must not have consumed it.
    new_id = next_note_id(ticket)
    note = {
        "note_id": new_id,
        "author": author.strip(),
        "message": message.strip(),
    }
    ticket["notes"].append(note)
    return (True, note)


def get_ticket_notes(tickets, ticket_id):
    """
    Return the notes of the ticket whose "id" == ticket_id.

    Returns:
        (True, list_of_note_dicts) — sorted by numeric note_id, so the
            order is deterministic even if a hand-edited file stored
            notes out of order. The list is a shallow copy, so the
            caller cannot mutate the ticket's internal list.
        (False, "No ticket with ID {ticket_id}.") when no ticket matches.

    The (ok, payload) shape is deliberate (§12.4): ticket_id is user-typed,
    so a mistyped ID is a real user error. Returning a bare list would make
    "no such ticket" indistinguishable from "ticket exists, no notes" —
    both would be [], and the CLI could not tell the user which applied.
    """
    ticket = _find_ticket(tickets, ticket_id)
    if ticket is None:
        return (False, f"No ticket with ID {ticket_id}.")
    # Shallow copy of the list, sorted by numeric note_id. Callers must
    # not mutate the note dicts (see §12.4). The CLI only reads.
    ordered = sorted(ticket["notes"], key=lambda n: int(n["note_id"][1:]))
    return (True, ordered)