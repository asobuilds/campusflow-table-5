"""Read-only reporting over the ticket store.

Everything in this module is a query: it reads the ticket list and returns a new
object. Nothing here mutates a ticket or reorders the caller's list.

See docs/design-decisions.md §3 (deliberate exception to the (ok, payload) shape)
and Issue #4 / Issue #5.
"""

# Lower rank sorts first. critical is most urgent, so it gets the lowest number.
RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Report keys, in display order. Derived from RANK so the two cannot drift —
# RANK already lists the priorities most urgent first.
PRIORITIES = tuple(RANK)

# Every status a ticket can be in. A whitelist, so a status added later is
# reported as itself rather than folded into an "other" bucket.
STATUSES = ("open", "in_progress", "resolved")

# The subset of STATUSES that still needs work. Whitelist, not "anything that
# isn't resolved": a status added later stays out of the queue until someone
# decides it belongs there.
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


def build_report(tickets):
    """Return ticket totals and breakdowns without modifying the input.

    Includes counts by status, priority, and category; unresolved and
    resolved totals; resolution percentage; and tickets ever reopened.
    Empty stores return zero counts and a 0.0 resolution percentage.
    """

    by_status = {status: 0 for status in STATUSES}
    by_priority = {priority: 0 for priority in PRIORITIES}

    categories = ("Network", "Hardware", "Software", "Other")
    by_category = {category: 0 for category in categories}

    for ticket in tickets:
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1
        by_category[ticket["category"]] += 1

    total = len(tickets)
    resolved = by_status["resolved"]
    unresolved = by_status["open"] + by_status["in_progress"]

    # Avoid division by zero when there are no tickets.
    resolution_percentage = (
        resolved / total * 100 if total else 0.0
    )

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "unresolved": unresolved,
        "resolved": resolved,
        "resolution_percentage": resolution_percentage,
        "reopened": sum(1 for ticket in tickets if ticket["was_reopened"]),
    }