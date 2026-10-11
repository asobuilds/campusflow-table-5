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
    """Summarise the whole ticket store: a total, and counts by status and priority.

    Every known status and priority is a key even when its count is zero, so the
    shape of the report does not change with the data. An empty store reports
    zeroes rather than an empty dict, and a caller never needs .get(key, 0).

    Counts are incremented through the whitelists above, so a ticket carrying an
    unrecognised status or priority raises KeyError instead of silently creating
    a new key for it — same rule as work_queue, for the same reason.

    tickets is assumed to be already validated by load_tickets.

    Returns a new dict. The input list is not modified, and nothing is shared
    between calls.
    """
    by_status = {status: 0 for status in STATUSES}
    by_priority = {priority: 0 for priority in PRIORITIES}

    for ticket in tickets:
        by_status[ticket["status"]] += 1
        by_priority[ticket["priority"]] += 1

    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
    }
