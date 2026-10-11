"""Read-only reporting over the ticket store.

Everything in this module is a query: it reads the ticket list and returns a new
object. Nothing here mutates a ticket or reorders the caller's list.

See docs/design-decisions.md §3 (deliberate exception to the (ok, payload) shape)
and Issue #4 / Issue #5.
"""

# Lower rank sorts first. critical is most urgent, so it gets the lowest number.
RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Whitelist, not "anything that isn't resolved": a status added later stays out
# of the queue until someone decides it belongs there.
OUTSTANDING = ("open", "in_progress")


def work_queue(tickets):
    """Return the outstanding tickets, most urgent first.

    Ordering: priority (critical, high, medium, low), ties broken by the numeric
    value of the ticket ID, so T999 precedes T1000.

    tickets is assumed to be already validated by load_tickets. An unrecognised
    priority is a broken invariant, not user input, so it raises KeyError here
    rather than being quietly ranked last.

    Returns a new list. The input list is not modified.
    """
    outstanding = [t for t in tickets if t["status"] in OUTSTANDING]
    return sorted(outstanding, key=lambda t: (RANK[t["priority"]], int(t["id"][1:])))
